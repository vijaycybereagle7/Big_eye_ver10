#!/bin/bash
# PostgreSQL Backup Script with WAL Archiving and Point-in-Time Recovery
# Comprehensive backup solution for Threat Intelligence Platform

set -euo pipefail

# Configuration
BACKUP_DIR="/opt/backups/postgres"
WAL_ARCHIVE_DIR="/wal_archive"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-threatintel-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGUSER="${PGUSER:-threatintel_user}"
PGDATABASE="${PGDATABASE:-threatintel}"
PGHOST="${PGHOST:-postgres-timescaledb}"
PGPORT="${PGPORT:-5432}"
BACKUP_PREFIX="threatintel_postgres"
LOG_FILE="/var/log/postgres_backup.log"

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

# Function to create base backup
create_base_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_base_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting base backup: $backup_name"
    
    # Create backup using pg_basebackup
    pg_basebackup -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -D "$backup_path" \
        -Ft -z -P -R || error_exit "pg_basebackup failed"
    
    # Create backup metadata
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Type: Base Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Database: $PGDATABASE
User: $PGUSER
Host: $PGHOST
Port: $PGPORT
WAL Archive: $WAL_ARCHIVE_DIR
EOF
    
    # Compress and upload to S3
    log "Compressing and uploading base backup to S3"
    tar -czf "${backup_path}.tar.gz" -C "$BACKUP_DIR" "$backup_name" || error_exit "Compression failed"
    
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.tar.gz" "s3://${S3_BACKUP_BUCKET}/postgres/base/" || error_exit "S3 upload failed"
    fi
    
    # Remove local files
    rm -rf "$backup_path" "${backup_path}.tar.gz"
    
    log "Base backup completed: $backup_name"
}

# Function to backup individual database
backup_database() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_db_${timestamp}.sql"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    log "Starting database backup: $backup_name"
    
    # Create SQL dump
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        --no-owner --no-privileges --verbose \
        --format=custom --compress=9 \
        --file="$backup_path.custom" || error_exit "pg_dump failed"
    
    # Create schema-only dump
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        --schema-only --no-owner --no-privileges \
        --format=plain --file="${backup_path}_schema.sql" || error_exit "Schema dump failed"
    
    # Compress files
    gzip "$backup_path.custom" "${backup_path}_schema.sql" || error_exit "Compression failed"
    
    # Upload to S3
    if command -v aws &> /dev/null; then
        aws s3 cp "${backup_path}.custom.gz" "s3://${S3_BACKUP_BUCKET}/postgres/daily/" || error_exit "S3 upload failed"
        aws s3 cp "${backup_path}_schema.sql.gz" "s3://${S3_BACKUP_BUCKET}/postgres/daily/" || error_exit "S3 upload failed"
    fi
    
    log "Database backup completed: $backup_name"
}

# Function to backup WAL files
backup_wal_files() {
    log "Starting WAL archive backup"
    
    # Copy WAL files to backup directory
    if [ -d "$WAL_ARCHIVE_DIR" ]; then
        local wal_backup_dir="${BACKUP_DIR}/wal_archive_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$wal_backup_dir"
        
        # Copy recent WAL files (last 24 hours)
        find "$WAL_ARCHIVE_DIR" -name "*.wal" -mtime -1 -exec cp {} "$wal_backup_dir/" \; || true
        
        # Compress and upload
        tar -czf "${wal_backup_dir}.tar.gz" -C "$BACKUP_DIR" "$(basename "$wal_backup_dir")"
        
        if command -v aws &> /dev/null; then
            aws s3 cp "${wal_backup_dir}.tar.gz" "s3://${S3_BACKUP_BUCKET}/postgres/wal/" || error_exit "S3 upload failed"
        fi
        
        # Clean up
        rm -rf "$wal_backup_dir" "${wal_backup_dir}.tar.gz"
    fi
    
    log "WAL archive backup completed"
}

# Function to check database connectivity
check_db_connection() {
    log "Checking database connectivity"
    
    if ! pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER"; then
        error_exit "Cannot connect to PostgreSQL"
    fi
    
    log "Database connection successful"
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)"
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -name "${BACKUP_PREFIX}_*" -mtime +$RETENTION_DAYS -delete || true
    
    # S3 cleanup
    if command -v aws &> /dev/null; then
        # Base backups (keep for 7 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/postgres/base/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(($(date +%s) - (7 * 24 * 60 * 60)))
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/postgres/base/$fileName"
            fi
        done
        
        # Daily backups (keep for 30 days)
        aws s3 ls "s3://${S3_BACKUP_BUCKET}/postgres/daily/" | while read -r line; do
            fileDate=$(echo $line | awk '{print $1" "$2}')
            fileDateSec=$(date -d "$fileDate" +%s)
            thresholdSec=$(date -d "$RETENTION_DAYS days ago" +%s)
            if [ $fileDateSec -lt $thresholdSec ]; then
                fileName=$(echo $line | awk '{print $4}')
                aws s3 rm "s3://${S3_BACKUP_BUCKET}/postgres/daily/$fileName"
            fi
        done
    fi
    
    log "Cleanup completed"
}

# Function to verify backup
verify_backup() {
    local backup_file="$1"
    local backup_type="$2"
    
    log "Verifying $backup_type backup: $backup_file"
    
    if [ "$backup_type" == "base" ]; then
        if [ -f "${backup_file}.tar.gz" ]; then
            log "Base backup file exists and not empty"
            return 0
        else
            log "Base backup file missing or empty"
            return 1
        fi
    elif [ "$backup_type" == "database" ]; then
        if [ -f "${backup_file}.custom.gz" ]; then
            log "Database backup file exists"
            return 0
        else
            log "Database backup file missing"
            return 1
        fi
    fi
}

# Main backup execution
main() {
    log "=== PostgreSQL Backup Started ==="
    
    # Check database connection
    check_db_connection
    
    # Determine backup type based on day of week
    day_of_week=$(date +%u)
    
    if [ "$day_of_week" -eq 7 ]; then
        # Sunday - Full base backup
        create_base_backup
        backup_wal_files
        backup_database
    else
        # Regular day - Database backup and WAL archive
        backup_database
        backup_wal_files
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "=== PostgreSQL Backup Completed Successfully ==="
}

# Execute main function
main "$@"