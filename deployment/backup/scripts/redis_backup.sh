#!/bin/bash
# Redis Backup Script
# Simple and effective Redis backup for Threat Intelligence Platform

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups/redis"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-threatintel-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
BACKUP_PREFIX="threatintel_redis"
LOG_FILE="/var/log/redis_backup.log"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR" || error_exit "Failed to create backup directory"

# Redis CLI helper function
redis_cli() {
    local cmd="$1"
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" -a "$REDIS_PASSWORD" $cmd
    else
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" $cmd
    fi
}

# Function to check Redis connectivity
check_redis_connection() {
    log "Checking Redis connectivity"
    
    if ! redis_cli ping > /dev/null 2>&1; then
        error_exit "Cannot connect to Redis"
    fi
    
    log "Redis connection successful"
}

# Function to create Redis RDB backup
backup_rdb() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_rdb_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting Redis RDB backup: $backup_name"
    
    # Create backup using SAVE command
    redis_cli BGSAVE || error_exit "Redis BGSAVE failed"
    
    # Wait for save to complete
    local save_status=""
    while [ "$save_status" != "OK" ]; do
        sleep 1
        save_status=$(redis_cli lastsave)
        log "Waiting for save to complete... (lastsave: $save_status)"
    done
    
    # Copy dump file
    local dump_file=$(redis_cli CONFIG GET dir | tail -1)/dump.rdb
    if [ -f "$dump_file" ]; then
        cp "$dump_file" "${backup_path}.rdb" || error_exit "Failed to copy RDB file"
    else
        error_exit "RDB file not found: $dump_file"
    fi
    
    # Get Redis info
    redis_cli INFO > "${backup_path}_info.txt"
    
    # Get key statistics
    redis_cli INFO keyspace > "${backup_path}_keyspace.txt"
    
    # Get database sizes
    local db_count=$(redis_cli CONFIG GET databases | tail -1)
    echo "Database Count: $db_count" > "${backup_path}_db_sizes.txt"
    for ((i=0; i<db_count; i++)); do
        local db_size=$(redis_cli DBSIZE $i 2>/dev/null || echo "0")
        echo "DB$i: $db_size keys" >> "${backup_path}_db_sizes.txt"
    done
    
    # Create metadata
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Type: Redis RDB Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Host: $REDIS_HOST
Port: $REDIS_PORT
Password: $([ -n "$REDIS_PASSWORD" ] && echo "SET" || echo "NONE")
RDB File: $(basename "${backup_path}.rdb")
EOF
    
    # Compress backup
    log "Compressing Redis backup"
    tar -czf "${backup_path}.tar.gz" \
        -C "$BACKUP_DIR" \
        "$(basename "${backup_path}.rdb")" \
        "$(basename "${backup_path}_info.txt")" \
        "$(basename "${backup_path}_keyspace.txt")" \
        "$(basename "${backup_path}_db_sizes.txt")" \
        "$(basename "${backup_path}/backup_info.txt")" || error_exit "Compression failed"
    
    # Upload to S3
    log "Uploading Redis backup to S3"
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/redis/rdb/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    rm -f "${backup_path}.tar.gz" \
          "${backup_path}.rdb" \
          "${backup_path}_info.txt" \
          "${backup_path}_keyspace.txt" \
          "${backup_path}_db_sizes.txt" \
          "${backup_path}/backup_info.txt"
    
    log "Redis RDB backup completed: $backup_name"
}

# Function to create AOF backup
backup_aof() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_aof_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting Redis AOF backup: $backup_name"
    
    # Force rewrite AOF
    redis_cli BGREWRITEAOF || error_exit "Redis BGREWRITEAOF failed"
    
    # Wait for rewrite to complete
    local aof_rewrite_status=""
    while [ -n "$(redis_cli INFO persistence | grep aof_rewrite_in_progress | cut -d: -f2 | tr -d '\r')" ]; do
        sleep 2
        log "Waiting for AOF rewrite to complete..."
    done
    
    # Copy AOF file
    local aof_file=$(redis_cli CONFIG GET dir | tail -1)/appendonly.aof
    if [ -f "$aof_file" ]; then
        cp "$aof_file" "${backup_path}.aof" || error_exit "Failed to copy AOF file"
    else
        log "AOF file not found: $aof_file"
        return 0
    fi
    
    # Get AOF info
    redis_cli INFO persistence > "${backup_path}_persistence.txt"
    
    # Create metadata
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Type: Redis AOF Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Host: $REDIS_HOST
Port: $REDIS_PORT
AOF File: $(basename "${backup_path}.aof")
EOF
    
    # Compress backup
    log "Compressing Redis AOF backup"
    tar -czf "${backup_path}.tar.gz" \
        -C "$BACKUP_DIR" \
        "$(basename "${backup_path}.aof")" \
        "$(basename "${backup_path}_persistence.txt")" \
        "$(basename "${backup_path}/backup_info.txt")" || error_exit "Compression failed"
    
    # Upload to S3
    log "Uploading Redis AOF backup to S3"
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/redis/aof/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    rm -f "${backup_path}.tar.gz" \
          "${backup_path}.aof" \
          "${backup_path}_persistence.txt" \
          "${backup_path}/backup_info.txt"
    
    log "Redis AOF backup completed: $backup_name"
}

# Function to export all keys
backup_keys_export() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_keys_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting Redis keys export: $backup_name"
    
    # Get all keys
    redis_cli --csv keys '*' > "${backup_path}_keys.csv" 2>/dev/null || touch "${backup_path}_keys.csv"
    
    # Export key values (be careful with large datasets)
    local key_count=$(wc -l < "${backup_path}_keys.csv")
    if [ "$key_count" -lt 10000 ]; then
        log "Exporting $key_count keys"
        while IFS= read -r key; do
            key=$(echo "$key" | tr -d '"')
            redis_cli GET "$key" > "${backup_path}_${key//:/_}.txt" 2>/dev/null || true
        done < "${backup_path}_keys.csv"
    else
        log "Skipping key export due to large number of keys ($key_count)"
    fi
    
    # Create key metadata
    cat > "${backup_path}/keys_info.txt" << EOF
Key Export Summary
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Total Keys: $key_count
Host: $REDIS_HOST
Port: $REDIS_PORT
EOF
    
    # Compress backup
    log "Compressing Redis keys export"
    tar -czf "${backup_path}.tar.gz" \
        -C "$BACKUP_DIR" \
        "$(basename "${backup_path}_keys.csv")" \
        "$(basename "${backup_path}/keys_info.txt")" \
        $(find "$BACKUP_DIR" -name "${backup_path}_*.txt" ! -name "${backup_path}_keys.csv" ! -path "*/${backup_path}/keys_info.txt" -exec basename {} \; 2>/dev/null | head -100 || true) || error_exit "Compression failed"
    
    # Upload to S3
    log "Uploading Redis keys export to S3"
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/redis/keys/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    find "$BACKUP_DIR" -name "${backup_path}_*.txt" -delete
    rm -f "${backup_path}.tar.gz"
    
    log "Redis keys export completed: $backup_name"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)"
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -name "${BACKUP_PREFIX}_*" -mtime +$RETENTION_DAYS -delete || true
    
    # S3 cleanup
    if command -v aws &> /dev/null; then
        # RDB backups (keep for 7 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/redis/rdb/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "7 days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/redis/rdb/$fileName"
            fi
        done
        
        # AOF backups (keep for 7 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/redis/aof/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "7 days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/redis/aof/$fileName"
            fi
        done
        
        # Keys export (keep for 30 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/redis/keys/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "$RETENTION_DAYS days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/redis/keys/$fileName"
            fi
        done
    fi
    
    log "Cleanup completed"
}

# Function to get Redis statistics
get_redis_stats() {
    log "Redis Statistics:"
    echo "=== Redis Info ==="
    redis_cli INFO
    echo ""
    echo "=== Database Sizes ==="
    redis_cli DBSIZE
    echo ""
    echo "=== Config ==="
    redis_cli CONFIG GET "*"
}

# Main backup execution
main() {
    log "=== Redis Backup Started ==="
    
    # Check Redis connection
    check_redis_connection
    
    # Get statistics
    get_redis_stats
    
    # Determine backup type based on day of week
    day_of_week=$(date +%u)
    
    if [ "$day_of_week" -eq 7 ]; then
        # Sunday - Full backup (RDB + AOF + Keys)
        backup_rdb
        backup_aof
        backup_keys_export
    else
        # Regular day - RDB backup
        backup_rdb
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "=== Redis Backup Completed Successfully ==="
}

# Execute main function
main "$@"