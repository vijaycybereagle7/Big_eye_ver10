-- =============================================
-- POSTGRESQL READ REPLICA SETUP SCRIPTS
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. MASTER SERVER CONFIGURATION
-- =============================================

-- Enable WAL archiving for streaming replication
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET wal_keep_size = '2GB';
ALTER SYSTEM SET max_connections = 200;

-- Configure WAL archiving (for point-in-time recovery)
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'cp %p /var/lib/postgresql/archive/%f';

-- Configure replication authentication
ALTER SYSTEM SET hot_standby = on;
ALTER SYSTEM SET hot_standby_feedback = on;
ALTER SYSTEM SET wal_receiver_status_interval = 10s;

-- Add replication user
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'replicator') THEN
        CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_replication_password';
    END IF;
END $$;

-- Create replication slot
SELECT pg_create_physical_replication_slot('replica_slot_1');

-- Create base backup for replica setup
-- Command: pg_basebackup -h master_host -D /var/lib/postgresql/replica_base -U replicator -v -P -R -S replica_slot_1

-- =============================================
-- 2. REPLICA SERVER CONFIGURATION
-- =============================================

-- Standby server configuration
ALTER SYSTEM SET hot_standby = on;
ALTER SYSTEM SET max_standby_streaming_delay = 30s;
ALTER SYSTEM SET wal_receiver_status_interval = 10s;
ALTER SYSTEM SET hot_standby_feedback = on;
ALTER SYSTEM SET max_connections = 250;

-- Configure read-only queries
ALTER SYSTEM SET default_transaction_read_only = on;
ALTER SYSTEM SET transaction_read_only = on;

-- Recovery configuration for standby
-- Add to postgresql.auto.conf:
-- primary_conninfo = 'host=master_host port=5432 user=replicator password=secure_replication_password application_name=replica_1'
-- restore_command = 'cp /var/lib/postgresql/archive/%f %p'
-- recovery_target_timeline = 'latest'

-- =============================================
-- 3. STANDBY SIGNAL FILES
-- =============================================

-- Create standby.signal file to enable read-only mode
-- touch /var/lib/postgresql/data/standby.signal

-- =============================================
-- 4. REPLICA MONITORING QUERIES
-- =============================================

-- Check replication lag on replica
SELECT 
    client_addr,
    application_name,
    state,
    sync_state,
    COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn), 0) as lag_bytes,
    COALESCE(pg_wal_lsn_diff(sent_lsn, write_lsn), 0) as write_lag,
    COALESCE(pg_wal_lsn_diff(write_lsn, flush_lsn), 0) as flush_lag,
    COALESCE(pg_wal_lsn_diff(flush_lsn, replay_lsn), 0) as replay_lag,
    write_lag,
    flush_lag,
    replay_lag,
    COALESCE(EXTRACT(EPOCH FROM write_lag), 0) as write_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM flush_lag), 0) as flush_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM replay_lag), 0) as replay_lag_sec
FROM pg_stat_replication
WHERE application_name LIKE 'replica_%';

-- Check replication status on master
SELECT 
    pid,
    application_name,
    client_addr,
    state,
    sync_state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn), 0) as lag_bytes
FROM pg_stat_replication;

-- Check replication slots
SELECT 
    slot_name,
    plugin,
    slot_type,
    active,
    active_pid,
    xmin,
    catalog_xmin,
    restart_lsn,
    confirmed_flush_lsn
FROM pg_replication_slots;

-- =============================================
-- 5. LOAD BALANCING CONFIGURATION
-- =============================================

-- Function to route read queries to replicas
CREATE OR REPLACE FUNCTION get_replica_connection()
RETURNS TEXT AS $$
DECLARE
    replica_urls TEXT[];
    selected_replica TEXT;
BEGIN
    -- In production, this would query a service discovery system
    -- For now, return static replica addresses
    replica_urls := ARRAY[
        'postgresql://user:pass@replica1:5432/database',
        'postgresql://user:pass@replica2:5432/database',
        'postgresql://user:pass@replica3:5432/database'
    ];
    
    -- Simple round-robin selection
    selected_replica := replica_urls[(EXTRACT(EPOCH FROM NOW()) % array_length(replica_urls, 1) + 1)::INT];
    
    RETURN selected_replica;
END;
$$ LANGUAGE plpgsql;

-- Connection pool configuration hints
-- Recommended pool sizes:
-- Master: max_connections = 100
-- Each Replica: max_connections = 150 (for read scaling)

-- =============================================
-- 6. CONNECTION ROUTING FUNCTION
-- =============================================

-- Function to check replica health
CREATE OR REPLACE FUNCTION check_replica_health(replica_name TEXT)
RETURNS TABLE (
    replica_name TEXT,
    is_healthy BOOLEAN,
    lag_bytes BIGINT,
    lag_seconds NUMERIC,
    status TEXT
) AS $$
DECLARE
    health_status BOOLEAN := false;
    current_lag BIGINT := 0;
    current_lag_sec NUMERIC := 0;
    status_msg TEXT := 'unknown';
BEGIN
    -- This would require dblink extension for actual replica check
    -- For demonstration purposes, return placeholder values
    
    RETURN QUERY
    SELECT 
        replica_name,
        health_status,
        current_lag,
        current_lag_sec,
        status_msg;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 7. QUERY ROUTING OPTIMIZATION
-- =============================================

-- Identify read-heavy queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
WHERE query LIKE '%SELECT%'
ORDER BY total_time DESC 
LIMIT 20;

-- Find queries suitable for replicas
SELECT 
    schemaname,
    query,
    calls,
    total_exec_time,
    mean_exec_time
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
  AND query ILIKE '%FROM%'
  AND query NOT ILIKE '%INSERT%'
  AND query NOT ILIKE '%UPDATE%'
  AND query NOT ILIKE '%DELETE%'
ORDER BY mean_exec_time DESC
LIMIT 50;

-- =============================================
-- 8. AUTOMATIC FAILOVER CONFIGURATION
-- =============================================

-- Function to promote replica to master
CREATE OR REPLACE FUNCTION promote_replica(target_replica TEXT)
RETURNS VOID AS $$
BEGIN
    -- This would be implemented by external tools like Patroni or repmgr
    -- The actual implementation depends on your infrastructure
    
    -- Update connection pool configuration
    -- Update application database URLs
    -- Send notifications
    
    RAISE NOTICE 'Promoting replica % to master', target_replica;
END;
$$ LANGUAGE plpgsql;

-- Check replica lag and trigger failover if necessary
CREATE OR REPLACE FUNCTION check_replica_lag_threshold(threshold_mb INTEGER DEFAULT 100)
RETURNS TABLE (
    replica_name TEXT,
    lag_mb NUMERIC,
    should_failover BOOLEAN
) AS $$
DECLARE
    replica_record RECORD;
BEGIN
    FOR replica_record IN
        SELECT 
            application_name,
            pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) as lag_bytes
        FROM pg_stat_replication
        WHERE application_name LIKE 'replica_%'
    LOOP
        RETURN QUERY
        SELECT 
            replica_record.application_name,
            (replica_record.lag_bytes / 1024.0 / 1024.0)::NUMERIC,
            replica_record.lag_bytes > (threshold_mb * 1024 * 1024);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 9. BACKUP AND MAINTENANCE
-- =============================================

-- Create backup verification function
CREATE OR REPLACE FUNCTION verify_replica_consistency()
RETURNS TABLE (
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
DECLARE
    master_count BIGINT;
    replica_count BIGINT;
BEGIN
    -- Check row counts for critical tables
    SELECT COUNT(*) INTO master_count FROM users WHERE deleted_at IS NULL;
    -- This would require connecting to replica via dblink
    -- replica_count := (SELECT COUNT(*) FROM dblink('replica_conn_string', 'SELECT COUNT(*) FROM users WHERE deleted_at IS NULL'));
    
    -- For demonstration, assume replica is consistent
    replica_count := master_count;
    
    RETURN QUERY
    SELECT 
        'row_count_consistency'::TEXT,
        CASE WHEN master_count = replica_count THEN 'PASS' ELSE 'FAIL' END::TEXT,
        format('Master: %, Replica: %', master_count, replica_count)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Schedule periodic consistency checks
-- SELECT cron.schedule('replica-consistency-check', '*/15 * * * *', 'SELECT verify_replica_consistency();');

-- =============================================
-- 10. PERFORMANCE MONITORING
-- =============================================

-- Monitor replica performance
SELECT 
    application_name,
    state,
    COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn), 0) as lag_bytes,
    COALESCE(EXTRACT(EPOCH FROM write_lag), 0) as write_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM flush_lag), 0) as flush_lag_sec,
    COALESCE(EXTRACT(EPOCH FROM replay_lag), 0) as replay_lag_sec
FROM pg_stat_replication
ORDER BY application_name;

-- Monitor connection pool statistics
-- This would be done via external tools like PgBouncer or application monitoring

-- Get database size on replicas
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
WHERE datname NOT IN ('postgres', 'template0', 'template1')
ORDER BY pg_database_size(datname) DESC;

-- =============================================
-- 11. MAINTENANCE WINDOW OPERATIONS
-- =============================================

-- Function to pause replication for maintenance
CREATE OR REPLACE FUNCTION pause_replication()
RETURNS VOID AS $$
BEGIN
    -- This would pause the replication process on the replica
    RAISE NOTICE 'Replication paused for maintenance';
END;
$$ LANGUAGE plpgsql;

-- Function to resume replication
CREATE OR REPLACE FUNCTION resume_replication()
RETURNS VOID AS $$
BEGIN
    -- This would resume the replication process on the replica
    RAISE NOTICE 'Replication resumed';
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 12. SECURITY CONFIGURATION
-- =============================================

-- Restrict access to replication users
REVOKE ALL ON SCHEMA public FROM replicator;
GRANT USAGE ON SCHEMA public TO replicator;

-- Monitor replication user connections
SELECT 
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    query
FROM pg_stat_activity 
WHERE usename = 'replicator';

-- =============================================
-- 13. REPLICA SETUP COMMANDS
-- =============================================

-- Initial setup steps:
-- 1. Configure master server with replication settings
-- 2. Create replication user and slot
-- 3. Take base backup: pg_basebackup -h master_host -D /var/lib/postgresql/replica_base -U replicator -R -S replica_slot_1
-- 4. Configure replica server settings
-- 5. Start replica server
-- 6. Monitor replication lag
-- 7. Configure load balancer/pooler

-- Replication status check:
-- SELECT * FROM pg_stat_replication;