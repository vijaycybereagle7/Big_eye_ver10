#!/bin/bash
# MongoDB Backup Script
# Comprehensive backup solution for Threat Intelligence Platform MongoDB

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups/mongodb"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-threatintel-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
MONGO_HOST="${MONGO_HOST:-mongodb}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-}"
MONGO_AUTH_DB="${MONGO_AUTH_DB:-admin}"
DATABASE_NAME="${DATABASE_NAME:-threatintel_logs}"
BACKUP_PREFIX="threatintel_mongodb"
LOG_FILE="/var/log/mongodb_backup.log"

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

# Function to check MongoDB connectivity
check_mongo_connection() {
    log "Checking MongoDB connectivity"
    
    if ! mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" --username "$MONGO_USER" \
           --password "$MONGO_PASSWORD" --authenticationDatabase "$MONGO_AUTH_DB" \
           --eval "db.adminCommand('ping')" --quiet; then
        error_exit "Cannot connect to MongoDB"
    fi
    
    log "MongoDB connection successful"
}

# Function to create full database backup
backup_database() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting MongoDB backup: $backup_name"
    
    # Create mongodump
    mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
              --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
              --authenticationDatabase "$MONGO_AUTH_DB" \
              --db "$DATABASE_NAME" \
              --out "$backup_path" || error_exit "mongodump failed"
    
    # Create backup metadata
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Type: Full Database Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Database: $DATABASE_NAME
Host: $MONGO_HOST
Port: $MONGO_PORT
User: $MONGO_USER
Auth DB: $MONGO_AUTH_DB
EOF
    
    # Get collection statistics
    mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" \
            --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
            --authenticationDatabase "$MONGO_AUTH_DB" \
            --eval "
                use $DATABASE_NAME;
                var stats = db.runCommand('dbStats');
                print('Database Statistics:');
                printjson(stats);
                
                var collections = db.getCollectionNames();
                collections.forEach(function(col) {
                    var colStats = db[col].stats();
                    print('Collection: ' + col);
                    printjson(colStats);
                });
            " > "${backup_path}/statistics.txt"
    
    # Compress backup
    log "Compressing backup"
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name" || error_exit "Compression failed"
    
    # Upload to S3
    log "Uploading backup to S3"
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/mongodb/daily/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    rm -rf "$backup_path" "${backup_path}.tar.gz"
    
    log "MongoDB backup completed: $backup_name"
}

# Function to backup oplog
backup_oplog() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_oplog_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting MongoDB oplog backup: $backup_name"
    
    # Create oplog dump (last 24 hours)
    mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
              --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
              --authenticationDatabase "$MONGO_AUTH_DB" \
              --oplog --out "$backup_path" || error_exit "mongodump (oplog) failed"
    
    # Compress backup
    log "Compressing oplog backup"
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name" || error_exit "Compression failed"
    
    # Upload to S3
    log "Uploading oplog backup to S3"
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/mongodb/oplog/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    rm -rf "$backup_path" "${backup_path}.tar.gz"
    
    log "MongoDB oplog backup completed: $backup_name"
}

# Function to backup specific collections
backup_collections() {
    local collections=("logs" "threat_intelligence" "malware_analysis" "network_events")
    
    for collection in "${collections[@]}"; do
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local backup_name="${BACKUP_PREFIX}_${collection}_${timestamp}"
        local backup_path="${BACKUP_DIR}/${backup_name}"
        
        log "Starting collection backup: $collection"
        
        # Create collection dump
        mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
                  --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                  --authenticationDatabase "$MONGO_AUTH_DB" \
                  --db "$DATABASE_NAME" \
                  --collection "$collection" \
                  --out "$backup_path" || log "Failed to backup collection: $collection"
        
        if [ -d "$backup_path/$DATABASE_NAME" ]; then
            # Compress collection backup
            tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name" || log "Compression failed: $collection"
            
            # Upload to S3
            if command -v aws &> /dev/null; then
                aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/mongodb/collections/" || log "S3 upload failed: $collection"
            fi
            
            # Remove local files
            rm -rf "$backup_path" "${backup_path}.tar.gz"
        fi
        
        log "Collection backup completed: $collection"
    done
}

# Function to create point-in-time backup
create_point_in_time_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_pit_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting point-in-time backup: $backup_name"
    
    # Get current oplog timestamp
    local oplog_timestamp=$(mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" \
                                   --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                                   --authenticationDatabase "$MONGO_AUTH_DB" \
                                   --eval "var ts = db.getSiblingDB('local').oplog.rs.find().sort({\$natural:-1}).limit(1).next().ts; printjson(ts);" \
                                   --quiet | grep -o '{.*}' | jq -r '.toString')
    
    # Create backup with specific timestamp
    mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
              --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
              --authenticationDatabase "$MONGO_AUTH_DB" \
              --db "$DATABASE_NAME" \
              --out "$backup_path" || error_exit "mongodump (PIT) failed"
    
    # Create metadata with timestamp
    cat > "${backup_path}/pitr_info.txt" << EOF
Backup Type: Point-in-Time Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Database: $DATABASE_NAME
Host: $MONGO_HOST
Oplog Timestamp: $oplog_timestamp
EOF
    
    # Compress and upload
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/mongodb/pitr/" || error_exit "S3 upload failed"
    fi
    
    # Cleanup
    rm -rf "$backup_path" "${backup_path}.tar.gz"
    
    log "Point-in-time backup completed: $backup_name"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)"
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -name "${BACKUP_PREFIX}_*" -mtime +$RETENTION_DAYS -delete || true
    
    # S3 cleanup
    if command -v aws &> /dev/null; then
        # Daily backups (keep for 30 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/mongodb/daily/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "$RETENTION_DAYS days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/mongodb/daily/$fileName"
            fi
        done
        
        # Oplog backups (keep for 7 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/mongodb/oplog/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "7 days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/mongodb/oplog/$fileName"
            fi
        done
    fi
    
    log "Cleanup completed"
}

# Function to verify backup
verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup: $backup_file"
    
    if [ -f "$backup_file" ]; then
        local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
        if [ "$file_size" -gt 0 ]; then
            log "Backup file exists and has content (size: $file_size bytes)"
            return 0
        else
            log "Backup file is empty"
            return 1
        fi
    else
        log "Backup file not found"
        return 1
    fi
}

# Main backup execution
main() {
    log "=== MongoDB Backup Started ==="
    
    # Check MongoDB connection
    check_mongo_connection
    
    # Determine backup type based on day of week and time
    day_of_week=$(date +%u)
    hour=$(date +%H)
    
    if [ "$day_of_week" -eq 7 ] && [ "$hour" -eq 2 ]; then
        # Sunday 2 AM - Full backup with oplog
        backup_database
        backup_oplog
        create_point_in_time_backup
    else
        # Regular backup
        backup_database
        backup_oplog
        backup_collections
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "=== MongoDB Backup Completed Successfully ==="
}

# Execute main function
main "$@"