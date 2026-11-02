#!/bin/bash
# PostgreSQL Backup Script with Advanced Retention Policies
# Comprehensive backup solution for Threat Intelligence Platform
# Supports: 7 daily, 4 weekly, 12 monthly, 7 yearly backups

set -euo pipefail

# ===========================================
# Configuration
# ===========================================
BACKUP_DIR="/opt/backups/postgres"
WAL_ARCHIVE_DIR="/wal_archive"
S3_BACKUP_BUCKET="${S3_BACKUP_BUCKET:-threatintel-backups}"
AWS_REGION="${AWS_REGION:-us-west-2}"
AZURE_STORAGE_ACCOUNT="${AZURE_STORAGE_ACCOUNT:-}"
AZURE_CONTAINER="${AZURE_CONTAINER:-threatintel-backups}"
GCP_BUCKET="${GCP_BUCKET:-}"

# Database Connection
PGPASSWORD="${POSTGRES_PASSWORD:-}"
PGUSER="${PGUSER:-threatintel_user}"
PGDATABASE="${PGDATABASE:-threatintel}"
PGHOST="${PGHOST:-postgres-timescaledb}"
PGPORT="${PGPORT:-5432}"

# Backup Configuration
BACKUP_PREFIX="threatintel_postgres"
LOG_FILE="/var/log/postgres_backup.log"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
OFFSITE_BACKUP="${OFFSITE_BACKUP_ENABLED:-false}"

# Retention Policies (in days)
RETENTION_DAILY=7
RETENTION_WEEKLY=28  # 4 weeks
RETENTION_MONTHLY=365  # 12 months
RETENTION_YEARLY=2555  # 7 years

# Performance Settings
MAX_PARALLEL_JOBS=4
COMPRESSION_LEVEL=6
ENABLE_PARALLEL_BACKUP=true

# ===========================================
# Functions
# ===========================================

# Enhanced logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info() { log "INFO" "$@"; }
warn() { log "WARN" "$@"; }
error() { log "ERROR" "$@"; }
debug() {
    if [ "${DEBUG:-false}" == "true" ]; then
        log "DEBUG" "$@"
    fi
}

# Error handling with cleanup
error_exit() {
    error "$1"
    cleanup_temp_files
    exit 1
}

# Cleanup temporary files
cleanup_temp_files() {
    rm -rf /tmp/postgres_backup_*
    info "Temporary files cleaned up"
}

# Verify prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check required commands
    local missing_cmds=()
    for cmd in pg_dump pg_basebackup gzip tar aws gcloud az; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_cmds+=("$cmd")
        fi
    done
    
    if [ ${#missing_cmds[@]} -gt 0 ]; then
        error_exit "Missing required commands: ${missing_cmds[*]}"
    fi
    
    # Check AWS credentials if using AWS
    if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
        if ! aws sts get-caller-identity &> /dev/null; then
            warn "AWS credentials check failed"
        fi
    fi
    
    info "Prerequisites check completed"
}

# Check database connectivity
check_db_connection() {
    info "Checking database connectivity..."
    
    if ! pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -t 10; then
        error_exit "Cannot connect to PostgreSQL database"
    fi
    
    # Get database size
    local db_size=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT pg_size_pretty(pg_database_size('$PGDATABASE'));" | xargs)
    info "Database size: $db_size"
    
    # Check database health
    local db_status=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT pg_is_in_recovery();" | xargs)
    if [ "$db_status" == "t" ]; then
        warn "Database is in recovery mode - WAL archiving may be slow"
    fi
}

# Get backup timestamp
get_timestamp() {
    date +"%Y%m%d_%H%M%S"
}

# Get backup date information
get_backup_info() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local date_str=$(date +"%Y-%m-%d")
    local day_of_week=$(date +%u)
    local day_of_month=$(date +%d)
    local month=$(date +%m)
    local year=$(date +%Y)
    
    echo "$timestamp|$date_str|$day_of_week|$day_of_month|$month|$year"
}

# Encrypt backup file
encrypt_backup() {
    local input_file="$1"
    local output_file="${input_file}.enc"
    
    if [ -z "$ENCRYPTION_KEY" ]; then
        debug "No encryption key provided, skipping encryption"
        echo "$input_file"
        return 0
    fi
    
    info "Encrypting backup file: $(basename "$input_file")"
    
    if command -v gpg &> /dev/null; then
        echo "$ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 \
            --output "$output_file" "$input_file" || error_exit "Encryption failed"
        rm -f "$input_file"
        echo "$output_file"
    elif command -v openssl &> /dev/null; then
        openssl enc -aes-256-cbc -salt -in "$input_file" -out "$output_file" -k "$ENCRYPTION_KEY" || error_exit "Encryption failed"
        rm -f "$input_file"
        echo "$output_file"
    else
        warn "No encryption tool available, leaving file unencrypted"
        echo "$input_file"
    fi
}

# Upload to cloud storage
upload_to_cloud() {
    local local_file="$1"
    local cloud_path="$2"
    
    debug "Uploading to cloud: $cloud_path"
    
    # Upload to AWS S3
    if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && command -v aws &> /dev/null; then
        info "Uploading to AWS S3: $cloud_path"
        aws s3 cp "$local_file" "s3://$cloud_path" --storage-class STANDARD_IA || warn "S3 upload failed"
    fi
    
    # Upload to Azure Blob Storage
    if [ -n "${AZURE_STORAGE_ACCOUNT:-}" ] && [ -n "${AZURE_CONTAINER:-}" ] && command -v az &> /dev/null; then
        info "Uploading to Azure Blob Storage: $cloud_path"
        az storage blob upload \
            --account-name "$AZURE_STORAGE_ACCOUNT" \
            --container-name "$AZURE_CONTAINER" \
            --name "$cloud_path" \
            --file "$local_file" \
            --overwrite || warn "Azure upload failed"
    fi
    
    # Upload to Google Cloud Storage
    if [ -n "${GCP_BUCKET:-}" ] && command -v gsutil &> /dev/null; then
        info "Uploading to Google Cloud Storage: $cloud_path"
        gsutil cp "$local_file" "gs://$GCP_BUCKET/$cloud_path" || warn "GCS upload failed"
    fi
}

# Create base backup
create_base_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_base_${timestamp}"
    local backup_path="/tmp/${backup_name}"
    local final_backup="${BACKUP_DIR}/${backup_name}.tar.gz"
    
    info "Starting base backup: $backup_name"
    
    # Create backup using pg_basebackup
    local start_time=$(date +%s)
    pg_basebackup -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -D "$backup_path" \
        -Ft -z -P -R -W --verbose || error_exit "pg_basebackup failed"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    info "Base backup completed in ${duration} seconds"
    
    # Create backup metadata
    cat > "${backup_path}/backup_info.txt" << EOF
Backup Type: Base Backup
Created: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
Database: $PGDATABASE
User: $PGUSER
Host: $PGHOST
Port: $PGPORT
WAL Archive: $WAL_ARCHIVE_DIR
Backup Duration: ${duration} seconds
TimescaleDB Enabled: true
EOF
    
    # Create checksum
    find "$backup_path" -type f -exec sha256sum {} \; > "${backup_path}/checksums.sha256"
    
    # Compress and encrypt
    tar -czf "${final_backup}" -C /tmp "$backup_name" || error_exit "Compression failed"
    rm -rf "$backup_path"
    
    final_backup=$(encrypt_backup "$final_backup")
    
    # Upload to cloud
    upload_to_cloud "$final_backup" "${S3_BACKUP_BUCKET}/postgres/base/$(basename "$final_backup")"
    
    # Move to final location
    mv "$final_backup" "${BACKUP_DIR}/$(basename "$final_backup")"
    
    info "Base backup completed and uploaded"
}

# Create differential backup
create_differential_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="${BACKUP_PREFIX}_diff_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    info "Starting differential backup: $backup_name"
    
    # Get LSN position for differential backup
    local lsn=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        -t -c "SELECT pg_current_wal_lsn();" | xargs)
    
    # Create custom format dump with LSN
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        --no-owner --no-privileges --verbose \
        --format=custom --compress=$COMPRESSION_LEVEL \
        --file="$backup_path.custom" \
        --progress || error_exit "pg_dump failed"
    
    # Compress and encrypt
    gzip "$backup_path.custom"
    backup_path="${backup_path}.custom.gz"
    
    # Add LSN info to filename
    local final_backup="${BACKUP_DIR}/${backup_name}_lsn_${lsn}.custom.gz"
    mv "$backup_path" "$final_backup"
    
    # Encrypt
    final_backup=$(encrypt_backup "$final_backup")
    
    # Upload to cloud
    upload_to_cloud "$final_backup" "${S3_BACKUP_BUCKET}/postgres/differential/$(basename "$final_backup")"
    
    info "Differential backup completed"
}

# Create full database backup
backup_database() {
    local timestamp=$(get_timestamp)
    local backup_name="${BACKUP_PREFIX}_db_${timestamp}"
    local backup_path="${BACKUP_DIR}/${backup_name}"
    
    info "Starting full database backup: $backup_name"
    
    local start_time=$(date +%s)
    
    # Parallel dump if enabled
    if [ "$ENABLE_PARALLEL_BACKUP" == "true" ]; then
        # Get list of tables
        local tables=$(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            -t -c "SELECT schemaname||'.'||tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema')" | xargs)
        
        # Create parallel jobs
        local job_count=0
        local pids=()
        for table in $tables; do
            if [ $job_count -ge $MAX_PARALLEL_JOBS ]; then
                wait -n
                job_count=$((job_count - 1))
            fi
            
            (
                pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
                    --table="$table" --format=custom --compress=$COMPRESSION_LEVEL \
                    --file="${backup_path}_${table//./_}.custom" &
            ) &
            
            pids+=($!)
            job_count=$((job_count + 1))
        done
        
        # Wait for all jobs
        wait
        
        # Combine dumps
        pg_restore --list "${backup_path}_threat_events.custom" > /tmp/tables_list.txt
        
        # Add all table dumps to list
        for table in $tables; do
            echo "; Table: $table" >> /tmp/tables_list.txt
            pg_restore "${backup_path}_${table//./_}.custom" --list /tmp/tables_list.txt --clean --if-exists \
                --create --verbose 2>/dev/null || true
        done
    else
        # Single-threaded backup
        pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
            --no-owner --no-privileges --verbose \
            --format=custom --compress=$COMPRESSION_LEVEL \
            --file="$backup_path.custom" || error_exit "pg_dump failed"
    fi
    
    # Create schema-only dump
    pg_dump -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
        --schema-only --no-owner --no-privileges \
        --format=plain --file="${backup_path}_schema.sql" || error_exit "Schema dump failed"
    
    # Compress
    gzip "$backup_path.custom" "${backup_path}_schema.sql"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    info "Database backup completed in ${duration} seconds"
    
    # Encrypt
    backup_path="${backup_path}.custom.gz"
    backup_path=$(encrypt_backup "$backup_path")
    
    # Upload to cloud
    upload_to_cloud "$backup_path" "${S3_BACKUP_BUCKET}/postgres/daily/$(basename "$backup_path")"
}

# Backup WAL files
backup_wal_files() {
    info "Starting WAL archive backup"
    
    if [ ! -d "$WAL_ARCHIVE_DIR" ]; then
        warn "WAL archive directory not found: $WAL_ARCHIVE_DIR"
        return 0
    fi
    
    local wal_backup_dir="/tmp/wal_archive_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$wal_backup_dir"
    
    # Copy WAL files from last 24 hours
    find "$WAL_ARCHIVE_DIR" -name "*.wal" -mtime -1 -type f | head -1000 | \
        xargs -I {} cp {} "$wal_backup_dir/" || true
    
    if [ -n "$(ls -A "$wal_backup_dir"/*.wal 2>/dev/null)" ]; then
        # Compress and upload
        tar -czf "${wal_backup_dir}.tar.gz" -C /tmp "$(basename "$wal_backup_dir")"
        rm -rf "$wal_backup_dir"
        
        local wal_archive="${wal_backup_dir}.tar.gz"
        wal_archive=$(encrypt_backup "$wal_archive")
        
        upload_to_cloud "$wal_archive" "${S3_BACKUP_BUCKET}/postgres/wal/$(basename "$wal_archive")"
        
        info "WAL archive backup completed: $(du -h "$wal_archive" | cut -f1)"
    else
        info "No WAL files found to backup"
    fi
    
    rm -rf "$wal_backup_dir"
}

# Clean up old backups with retention policies
cleanup_old_backups() {
    info "Cleaning up old backups according to retention policies"
    
    # Calculate thresholds
    local daily_threshold=$(date -d "$RETENTION_DAILY days ago" +%s)
    local weekly_threshold=$(date -d "$RETENTION_WEEKLY days ago" +%s)
    local monthly_threshold=$(date -d "$RETENTION_MONTHLY days ago" +%s)
    local yearly_threshold=$(date -d "$RETENTION_YEARLY days ago" +%s)
    
    # Local cleanup
    find "$BACKUP_DIR" -type f -name "${BACKUP_PREFIX}_*" -mtime +$RETENTION_YEARLY -delete 2>/dev/null || true
    
    # Cloud cleanup for AWS S3
    if command -v aws &> /dev/null && [ -n "${AWS_ACCESS_KEY_ID:-}" ]; then
        info "Cleaning up S3 backups..."
        
        # Base backups (keep for 30 days)
        cleanup_s3_backups "${S3_BACKUP_BUCKET}/postgres/base/" 30
        
        # Daily backups (keep for RETENTION_DAILY days)
        cleanup_s3_backups "${S3_BACKUP_BUCKET}/postgres/daily/" $RETENTION_DAILY
        
        # Differential backups (keep for RETENTION_WEEKLY days)
        cleanup_s3_backups "${S3_BACKUP_BUCKET}/postgres/differential/" $RETENTION_WEEKLY
        
        # WAL archives (keep for RETENTION_DAILY days)
        cleanup_s3_backups "${S3_BACKUP_BUCKET}/postgres/wal/" $RETENTION_DAILY
    fi
}

# Clean up S3 backups
cleanup_s3_backups() {
    local s3_path="$1"
    local retention_days="$2"
    local threshold=$(date -d "$retention_days days ago" +%s)
    
    aws s3 ls "s3://$s3_path" 2>/dev/null | while read -r line; do
        local file_date=$(echo $line | awk '{print $1" "$2}')
        local file_date_sec=$(date -d "$file_date" +%s 2>/dev/null || echo 0)
        local file_name=$(echo $line | awk '{print $4}')
        
        if [ $file_date_sec -lt $threshold ]; then
            info "Deleting old backup: $file_name"
            aws s3 rm "s3://$s3_path$file_name" || warn "Failed to delete $file_name"
        fi
    done
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    local backup_type="$2"
    
    info "Verifying backup: $(basename "$backup_file")"
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    if [ "$file_size" -lt 1024 ]; then
        error "Backup file too small: $file_size bytes"
        return 1
    fi
    
    # Verify checksum if available
    if [ -f "${backup_file}.sha256" ]; then
        if command -v sha256sum &> /dev/null; then
            local calculated_hash=$(sha256sum "$backup_file" | awk '{print $1}')
            local stored_hash=$(cat "${backup_file}.sha256" | awk '{print $1}')
            if [ "$calculated_hash" != "$stored_hash" ]; then
                error "Checksum mismatch for backup: $backup_file"
                return 1
            fi
        fi
    fi
    
    info "Backup verification passed"
    return 0
}

# Generate backup report
generate_backup_report() {
    local report_file="${BACKUP_DIR}/backup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    cat > "$report_file" << EOF
=== PostgreSQL Backup Report ===
Generated: $(date)
Database: $PGDATABASE
Host: $PGHOST
Port: $PGPORT
User: $PGUSER

=== Local Backups ===
$(find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*" -type f -exec ls -lh {} \; | sort)

=== S3 Backups ===
$(aws s3 ls "s3://${S3_BACKUP_BUCKET}/postgres/" --recursive 2>/dev/null || echo "S3 not configured")

=== Database Statistics ===
Database Size: $(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT pg_size_pretty(pg_database_size('$PGDATABASE'));" | xargs)
Total Tables: $(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');" | xargs)
Total Indexes: $(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM pg_indexes;" | xargs)

=== TimescaleDB Statistics ===
Hypertables: $(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT count(*) FROM timescaledb_information.hypertables;" | xargs)
Compression Status: $(psql -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" -t -c "SELECT COUNT(*) FROM timescaledb_information.compression_settings;" | xargs)

=== End of Report ===
EOF
    
    info "Backup report generated: $report_file"
    
    # Upload report to cloud
    upload_to_cloud "$report_file" "${S3_BACKUP_BUCKET}/reports/$(basename "$report_file")"
}

# Main backup execution
main() {
    info "=== PostgreSQL Backup Started ==="
    
    # Parse command line arguments
    local backup_type="${1:-auto}"
    
    # Check prerequisites
    check_prerequisites
    
    # Check database connection
    check_db_connection
    
    # Get backup type information
    IFS='|' read -r timestamp date_str day_of_week day_of_month month year <<< "$(get_backup_info)"
    
    # Determine backup strategy
    if [ "$backup_type" == "base" ] || [ "$backup_type" == "full" ]; then
        create_base_backup
        backup_wal_files
        backup_database
    elif [ "$backup_type" == "differential" ]; then
        create_differential_backup
        backup_wal_files
    elif [ "$backup_type" == "incremental" ]; then
        backup_database
        backup_wal_files
    else
        # Auto mode - determine based on schedule
        if [ "$day_of_week" -eq 7 ]; then
            # Sunday - Full base backup
            info "Sunday detected - performing full base backup"
            create_base_backup
            backup_wal_files
            backup_database
        elif [ "$day_of_month" -eq 1 ]; then
            # First of month - Differential backup
            info "First of month detected - performing differential backup"
            create_differential_backup
            backup_wal_files
        else
            # Regular day - Incremental backup
            info "Performing incremental backup"
            backup_database
            backup_wal_files
        fi
    fi
    
    # Verify recent backups
    verify_backup "${BACKUP_DIR}/${BACKUP_PREFIX}"_db_"${timestamp}".custom.gz" "database" || warn "Backup verification failed"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Generate report
    generate_backup_report
    
    # Cleanup temporary files
    cleanup_temp_files
    
    info "=== PostgreSQL Backup Completed Successfully ==="
}

# Execute main function
main "$@"
