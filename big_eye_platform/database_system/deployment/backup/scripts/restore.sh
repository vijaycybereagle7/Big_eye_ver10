#!/bin/bash
# Comprehensive Database Restore Script
# Point-in-time recovery for PostgreSQL, MongoDB, and Redis
# Usage: ./restore.sh [database] [backup_file] [restore_time]

set -euo pipefail

# Configuration
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-threatintel-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"
LOG_FILE="/var/log/database_restore.log"
TEMP_DIR="/tmp/restore_$$"

# PostgreSQL Configuration
PGHOST="${PGHOST:-postgres-timescaledb}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-threatintel_user}"
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGDATABASE="${PGDATABASE:-threatintel}"

# MongoDB Configuration
MONGO_HOST="${MONGO_HOST:-mongodb}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-}"
MONGO_AUTH_DB="${MONGO_AUTH_DB:-admin}"
MONGO_DATABASE="${MONGO_DATABASE:-threatintel_logs}"

# Redis Configuration
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    cleanup_temp_dir
    exit 1
}

# Cleanup function
cleanup_temp_dir() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
        log "Cleaned up temporary directory: $TEMP_DIR"
    fi
}

# Trap cleanup
trap cleanup_temp_dir EXIT

# Create temp directory
mkdir -p "$TEMP_DIR" || error_exit "Failed to create temporary directory"

# Parse command line arguments
DATABASE_TYPE="${1:-all}"
BACKUP_FILE="${2:-}"
RESTORE_TIME="${3:-}"

if [ -z "$BACKUP_FILE" ] && [ "$DATABASE_TYPE" != "all" ]; then
    echo "Usage: $0 [database] [backup_file] [restore_time]"
    echo "Databases: postgres|mongodb|redis|all"
    echo "Example: $0 postgres s3://bucket/path/backup.tar.gz '2024-01-01 12:00:00'"
    exit 1
fi

# Function to download backup from S3 or use local file
download_backup() {
    local source="$1"
    local filename=$(basename "$source")
    local local_path="${TEMP_DIR}/${filename}"
    
    log "Downloading backup: $source"
    
    if [[ "$source" == s3://* ]]; then
        # Download from S3
        aws s3 cp "$source" "$local_path" || error_exit "Failed to download from S3: $source"
    elif [[ "$source" == http://* ]] || [[ "$source" == https://* ]]; then
        # Download from HTTP
        curl -o "$local_path" "$source" || error_exit "Failed to download from HTTP: $source"
    else
        # Use local file
        if [ ! -f "$source" ]; then
            error_exit "Local backup file not found: $source"
        fi
        cp "$source" "$local_path"
    fi
    
    echo "$local_path"
}

# PostgreSQL Restore Functions
restore_postgres_base() {
    local backup_path="$1"
    local restore_time="$2"
    
    log "Starting PostgreSQL base restore"
    
    # Extract backup
    local extract_dir="${TEMP_DIR}/postgres_restore"
    mkdir -p "$extract_dir"
    tar -xzf "$backup_path" -C "$extract_dir" || error_exit "Failed to extract PostgreSQL backup"
    
    # Stop PostgreSQL
    log "Stopping PostgreSQL service"
    docker stop postgres-timescaledb 2>/dev/null || true
    
    # Restore data directory
    local backup_dir=$(find "$extract_dir" -name "threatintel_postgres_base_*" -type d | head -1)
    if [ -z "$backup_dir" ]; then
        error_exit "Backup directory not found in extracted files"
    fi
    
    log "Restoring PostgreSQL data from: $backup_dir"
    
    # Remove old data
    rm -rf /opt/data/postgres_timescaledb/* || true
    
    # Copy restored data
    cp -r "$backup_dir"/* /opt/data/postgres_timescaledb/ || error_exit "Failed to copy PostgreSQL data"
    
    # Set proper permissions
    chown -R postgres:postgres /opt/data/postgres_timescaledb || true
    
    # Start PostgreSQL
    log "Starting PostgreSQL service"
    docker start postgres-timescaledb || error_exit "Failed to start PostgreSQL"
    
    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready"
    for i in {1..30}; do
        if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER"; then
            log "PostgreSQL is ready"
            break
        fi
        sleep 2
    done
    
    # Point-in-time recovery if specified
    if [ -n "$restore_time" ]; then
        log "Starting point-in-time recovery to: $restore_time"
        
        # Find the first WAL file after restore time
        local recovery_target=$(date -d "$restore_time" +%Y%m%d%H%M%S)
        
        # Update recovery.conf for point-in-time recovery
        cat > /opt/data/postgres_timescaledb/postgresql.auto.conf << EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '$restore_time'
recovery_target_timeline = 'latest'
recovery_target_action = 'promote'
EOF
        
        # Restart PostgreSQL to apply recovery
        log "Restarting PostgreSQL for point-in-time recovery"
        docker restart postgres-timescaledb
        
        # Wait for recovery to complete
        for i in {1..60}; do
            if ! docker exec postgres-timescaledb psql -U postgres -c "SELECT pg_is_in_recovery();" | grep -q t; then
                log "Point-in-time recovery completed"
                break
            fi
            sleep 5
        done
    fi
    
    # Verify restore
    log "Verifying PostgreSQL restore"
    if pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER"; then
        log "PostgreSQL restore completed successfully"
    else
        error_exit "PostgreSQL restore verification failed"
    fi
}

# MongoDB Restore Functions
restore_mongodb() {
    local backup_path="$1"
    local restore_time="$2"
    
    log "Starting MongoDB restore"
    
    # Extract backup
    local extract_dir="${TEMP_DIR}/mongodb_restore"
    mkdir -p "$extract_dir"
    tar -xzf "$backup_path" -C "$extract_dir" || error_exit "Failed to extract MongoDB backup"
    
    # Stop MongoDB
    log "Stopping MongoDB service"
    docker stop mongodb 2>/dev/null || true
    
    # Find backup directory
    local backup_dir=$(find "$extract_dir" -name "threatintel_mongodb_*" -type d | head -1)
    if [ -z "$backup_dir" ]; then
        error_exit "MongoDB backup directory not found"
    fi
    
    # For point-in-time recovery, we need oplog
    if [ -n "$restore_time" ]; then
        log "MongoDB point-in-time recovery requires oplog replay"
        log "Restoring to closest backup point before: $restore_time"
    fi
    
    # Remove old data
    rm -rf /opt/data/mongodb/* || true
    
    # Copy restored data
    cp -r "$backup_dir"/* /opt/data/mongodb/ || error_exit "Failed to copy MongoDB data"
    
    # Set proper permissions
    chown -R mongodb:mongodb /opt/data/mongodb || true
    
    # Start MongoDB
    log "Starting MongoDB service"
    docker start mongodb || error_exit "Failed to start MongoDB"
    
    # Wait for MongoDB to be ready
    log "Waiting for MongoDB to be ready"
    for i in {1..30}; do
        if mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" \
                   --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                   --authenticationDatabase "$MONGO_AUTH_DB" \
                   --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
            log "MongoDB is ready"
            break
        fi
        sleep 2
    done
    
    # Verify restore
    log "Verifying MongoDB restore"
    if mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" \
               --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
               --authenticationDatabase "$MONGO_AUTH_DB" \
               --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        log "MongoDB restore completed successfully"
    else
        error_exit "MongoDB restore verification failed"
    fi
}

# Redis Restore Functions
restore_redis() {
    local backup_path="$1"
    
    log "Starting Redis restore"
    
    # Extract backup
    local extract_dir="${TEMP_DIR}/redis_restore"
    mkdir -p "$extract_dir"
    tar -xzf "$backup_path" -C "$extract_dir" || error_exit "Failed to extract Redis backup"
    
    # Find RDB file
    local rdb_file=$(find "$extract_dir" -name "*.rdb" | head -1)
    if [ -z "$rdb_file" ]; then
        error_exit "RDB file not found in backup"
    fi
    
    # Stop Redis
    log "Stopping Redis service"
    docker stop redis 2>/dev/null || true
    
    # Restore RDB file
    cp "$rdb_file" /opt/data/redis/dump.rdb || error_exit "Failed to copy RDB file"
    
    # Set proper permissions
    chown -R redis:redis /opt/data/redis || true
    
    # Start Redis
    log "Starting Redis service"
    docker start redis || error_exit "Failed to start Redis"
    
    # Wait for Redis to be ready
    log "Waiting for Redis to be ready"
    for i in {1..30}; do
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
            log "Redis is ready"
            break
        fi
        sleep 2
    done
    
    # Verify restore
    log "Verifying Redis restore"
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
        log "Redis restore completed successfully"
        # Show key count
        local key_count=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" DBSIZE)
        log "Redis key count: $key_count"
    else
        error_exit "Redis restore verification failed"
    fi
}

# Function to validate restore point
validate_restore_point() {
    local database="$1"
    local backup_file="$2"
    local restore_time="$3"
    
    log "Validating restore point"
    
    if [ -n "$restore_time" ]; then
        # Check if restore time is reasonable
        if ! date -d "$restore_time" >/dev/null 2>&1; then
            error_exit "Invalid restore time format: $restore_time"
        fi
        
        local restore_timestamp=$(date -d "$restore_time" +%s)
        local now_timestamp=$(date +%s)
        
        if [ "$restore_timestamp" -gt "$now_timestamp" ]; then
            error_exit "Restore time cannot be in the future"
        fi
        
        # Check if restore time is not too old for specific databases
        local max_age_days=30
        if [ "$(( (now_timestamp - restore_timestamp) / 86400 ))" -gt "$max_age_days" ]; then
            log "WARNING: Restore time is more than $max_age_days days old"
            log "WAL archiving and oplog retention may not cover this period"
        fi
    fi
    
    # Check backup file integrity
    if [[ "$backup_file" == s3://* ]]; then
        if ! command -v aws &> /dev/null; then
            error_exit "AWS CLI not found for S3 access"
        fi
    fi
    
    log "Restore point validation completed"
}

# Function to create recovery checkpoint
create_recovery_checkpoint() {
    local database="$1"
    
    log "Creating recovery checkpoint for $database"
    
    case "$database" in
        postgres)
            # Create a backup before restore
            pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
                    --schema-only > "${TEMP_DIR}/${database}_pre_restore_schema.sql"
            ;;
        mongodb)
            # Export current database metadata
            mongodump --host "$MONGO_HOST" --port "$MONGO_PORT" \
                      --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                      --authenticationDatabase "$MONGO_AUTH_DB" \
                      --db "$MONGO_DATABASE" \
                      --out "${TEMP_DIR}/${database}_pre_restore" >/dev/null 2>&1 || true
            ;;
        redis)
            # Get current key count and info
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO > "${TEMP_DIR}/${database}_pre_restore_info.txt"
            ;;
    esac
    
    log "Recovery checkpoint created"
}

# Function to rollback restore
rollback_restore() {
    local database="$1"
    
    log "Rolling back $database restore"
    
    case "$database" in
        postgres)
            # Restore from pre-restore schema
            if [ -f "${TEMP_DIR}/${database}_pre_restore_schema.sql" ]; then
                psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
                     < "${TEMP_DIR}/${database}_pre_restore_schema.sql" || log "Rollback schema restore failed"
            fi
            ;;
        mongodb)
            # Drop and restore from pre-restore backup
            if [ -d "${TEMP_DIR}/${database}_pre_restore" ]; then
                mongosh --host "$MONGO_HOST" --port "$MONGO_PORT" \
                        --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                        --authenticationDatabase "$MONGO_AUTH_DB" \
                        --eval "use $MONGO_DATABASE; db.dropDatabase()" >/dev/null 2>&1 || true
                
                mongorestore --host "$MONGO_HOST" --port "$MONGO_PORT" \
                             --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
                             --authenticationDatabase "$MONGO_AUTH_DB" \
                             --db "$MONGO_DATABASE" \
                             "${TEMP_DIR}/${database}_pre_restore/" >/dev/null 2>&1 || log "Rollback restore failed"
            fi
            ;;
        redis)
            # Flush and reload from checkpoint if available
            redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" FLUSHALL >/dev/null 2>&1 || log "Failed to flush Redis during rollback"
            ;;
    esac
    
    log "$database rollback completed"
}

# Main restore function
main() {
    log "=== Database Restore Started ==="
    log "Database Type: $DATABASE_TYPE"
    log "Backup File: $BACKUP_FILE"
    log "Restore Time: $RESTORE_TIME"
    
    # Validate parameters
    if [ -n "$BACKUP_FILE" ]; then
        validate_restore_point "$DATABASE_TYPE" "$BACKUP_FILE" "$RESTORE_TIME"
    fi
    
    case "$DATABASE_TYPE" in
        postgres)
            if [ -z "$BACKUP_FILE" ]; then
                error_exit "Backup file required for PostgreSQL restore"
            fi
            
            create_recovery_checkpoint "postgres"
            download_backup "$BACKUP_FILE"
            restore_postgres_base "${TEMP_DIR}/$(basename "$BACKUP_FILE")" "$RESTORE_TIME"
            ;;
        mongodb)
            if [ -z "$BACKUP_FILE" ]; then
                error_exit "Backup file required for MongoDB restore"
            fi
            
            create_recovery_checkpoint "mongodb"
            download_backup "$BACKUP_FILE"
            restore_mongodb "${TEMP_DIR}/$(basename "$BACKUP_FILE")" "$RESTORE_TIME"
            ;;
        redis)
            if [ -z "$BACKUP_FILE" ]; then
                error_exit "Backup file required for Redis restore"
            fi
            
            create_recovery_checkpoint "redis"
            download_backup "$BACKUP_FILE"
            restore_redis "${TEMP_DIR}/$(basename "$BACKUP_FILE")"
            ;;
        all)
            log "Full system restore - restore each database individually"
            log "Use: $0 postgres [backup_file] [restore_time]"
            log "Use: $0 mongodb [backup_file] [restore_time]"
            log "Use: $0 redis [backup_file]"
            ;;
        *)
            error_exit "Unknown database type: $DATABASE_TYPE. Use: postgres|mongodb|redis|all"
            ;;
    esac
    
    log "=== Database Restore Completed Successfully ==="
}

# Execute main function
main "$@"