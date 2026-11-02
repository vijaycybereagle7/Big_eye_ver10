-- =============================================
-- POSTGRESQL PARTITIONING IMPLEMENTATION
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. RANGE PARTITIONING - BY DATE
-- =============================================

-- Create partitioned table for user sessions by month
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (session_start);

-- Create monthly partitions
CREATE TABLE user_sessions_2023_01 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE user_sessions_2023_02 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');

CREATE TABLE user_sessions_2023_03 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-03-01') TO ('2023-04-01');

-- Continue pattern for all needed months...
CREATE TABLE user_sessions_2023_04 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-04-01') TO ('2023-05-01');

CREATE TABLE user_sessions_2023_05 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-05-01') TO ('2023-06-01');

CREATE TABLE user_sessions_2023_06 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-06-01') TO ('2023-07-01');

CREATE TABLE user_sessions_2023_07 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-07-01') TO ('2023-08-01');

CREATE TABLE user_sessions_2023_08 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-08-01') TO ('2023-09-01');

CREATE TABLE user_sessions_2023_09 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-09-01') TO ('2023-10-01');

CREATE TABLE user_sessions_2023_10 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-10-01') TO ('2023-11-01');

CREATE TABLE user_sessions_2023_11 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-11-01') TO ('2023-12-01');

CREATE TABLE user_sessions_2023_12 PARTITION OF user_sessions
    FOR VALUES FROM ('2023-12-01') TO ('2024-01-01');

CREATE TABLE user_sessions_default PARTITION OF user_sessions DEFAULT;

-- Create indexes on partitions
CREATE INDEX CONCURRENTLY ON user_sessions_2023_01 (user_id, session_start);
CREATE INDEX CONCURRENTLY ON user_sessions_2023_02 (user_id, session_start);
CREATE INDEX CONCURRENTLY ON user_sessions_2023_03 (user_id, session_start);
-- Continue for all partitions...

-- =============================================
-- 2. LIST PARTITIONING - BY STATUS
-- =============================================

-- Create partitioned table by user status
CREATE TABLE user_activity_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY LIST (status);

-- Create partitions by status type
CREATE TABLE user_activity_logs_active PARTITION OF user_activity_logs
    FOR VALUES IN ('active', 'active_pending');

CREATE TABLE user_activity_logs_inactive PARTITION OF user_activity_logs
    FOR VALUES IN ('inactive', 'suspended');

CREATE TABLE user_activity_logs_blocked PARTITION OF user_activity_logs
    FOR VALUES IN ('blocked', 'banned');

CREATE TABLE user_activity_logs_other PARTITION OF user_activity_logs
    FOR VALUES IN (NULL, '');

-- Create indexes on list partitions
CREATE INDEX CONCURRENTLY ON user_activity_logs_active (user_id, created_at);
CREATE INDEX CONCURRENTLY ON user_activity_logs_inactive (user_id, created_at);
CREATE INDEX CONCURRENTLY ON user_activity_logs_blocked (user_id, created_at);

-- =============================================
-- 3. HASH PARTITIONING - BY USER ID
-- =============================================

-- Create partitioned table for large user data
CREATE TABLE user_payments (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    payment_method VARCHAR(50),
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    metadata JSONB
) PARTITION BY HASH (user_id);

-- Create hash partitions (4 partitions for even distribution)
CREATE TABLE user_payments_hash_0 PARTITION OF user_payments
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);

CREATE TABLE user_payments_hash_1 PARTITION OF user_payments
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);

CREATE TABLE user_payments_hash_2 PARTITION OF user_payments
    FOR VALUES WITH (MODULUS 4, REMAINDER 2);

CREATE TABLE user_payments_hash_3 PARTITION OF user_payments
    FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Create indexes on hash partitions
CREATE INDEX CONCURRENTLY ON user_payments_hash_0 (transaction_date, status);
CREATE INDEX CONCURRENTLY ON user_payments_hash_1 (transaction_date, status);
CREATE INDEX CONCURRENTLY ON user_payments_hash_2 (transaction_date, status);
CREATE INDEX CONCURRENTLY ON user_payments_hash_3 (transaction_date, status);

-- =============================================
-- 4. COMPOSITE PARTITIONING - RANGE + LIST
-- =============================================

-- Create composite partitioned table
CREATE TABLE user_transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
) PARTITION BY RANGE (created_at);

-- Create main range partitions by month
CREATE TABLE user_transactions_2023_q1 PARTITION OF user_transactions
    FOR VALUES FROM ('2023-01-01') TO ('2023-04-01') PARTITION BY LIST (transaction_type);

-- Q1 partitions by transaction type
CREATE TABLE user_transactions_q1_purchase PARTITION OF user_transactions_2023_q1
    FOR VALUES IN ('purchase', 'buy', 'order');

CREATE TABLE user_transactions_q1_refund PARTITION OF user_transactions_2023_q1
    FOR VALUES IN ('refund', 'return', 'credit');

CREATE TABLE user_transactions_q1_other PARTITION OF user_transactions_2023_q1
    FOR VALUES IN ('subscription', 'renewal', 'upgrade', 'downgrade');

-- =============================================
-- 5. AUTOMATED PARTITION MANAGEMENT
-- =============================================

-- Function to create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(
    table_name TEXT,
    target_date DATE
) RETURNS TEXT AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
    sql_statement TEXT;
BEGIN
    partition_name := table_name || '_' || TO_CHAR(target_date, 'YYYY_MM');
    start_date := DATE_TRUNC('month', target_date);
    end_date := start_date + INTERVAL '1 month';
    
    sql_statement := format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date, end_date
    );
    
    EXECUTE sql_statement;
    RETURN partition_name;
END;
$$ LANGUAGE plpgsql;

-- Function to drop old partitions
CREATE OR REPLACE FUNCTION drop_old_partitions(
    table_name TEXT,
    retention_months INTEGER DEFAULT 12
) RETURNS INTEGER AS $$
DECLARE
    partition_record RECORD;
    drop_count INTEGER := 0;
    cutoff_date DATE := DATE_TRUNC('month', NOW() - (retention_months || ' months')::INTERVAL);
BEGIN
    FOR partition_record IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE tablename LIKE table_name || '_%'
          AND tablename < table_name || '_' || TO_CHAR(cutoff_date, 'YYYY_MM')
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I.%I', partition_record.schemaname, partition_record.tablename);
        drop_count := drop_count + 1;
    END LOOP;
    
    RETURN drop_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 6. PARTITION MAINTENANCE JOBS
-- =============================================

-- Function to maintain partitions automatically
CREATE OR REPLACE FUNCTION maintain_partitions() RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    current_date DATE := CURRENT_DATE;
    start_month DATE;
    next_month DATE;
    i INTEGER;
BEGIN
    -- Create partitions for next 3 months
    FOR i IN 0..2 LOOP
        start_month := DATE_TRUNC('month', current_date + (i || ' months')::INTERVAL);
        next_month := start_month + INTERVAL '1 month';
        
        partition_name := 'user_sessions_' || TO_CHAR(start_month, 'YYYY_MM');
        
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF user_sessions FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_month, next_month
        );
    END LOOP;
    
    -- Drop partitions older than 24 months
    PERFORM drop_old_partitions('user_sessions', 24);
END;
$$ LANGUAGE plpgsql;

-- Schedule partition maintenance (requires pg_cron)
-- SELECT cron.schedule('maintain-partitions', '0 0 1 * *', 'SELECT maintain_partitions();');

-- =============================================
-- 7. QUERY OPTIMIZATION FOR PARTITIONED TABLES
-- =============================================

-- Optimized query with partition pruning
EXPLAIN (ANALYZE, BUFFERS)
SELECT user_id, session_start, duration
FROM user_sessions
WHERE session_start >= '2023-06-01'
  AND session_start < '2023-07-01'
  AND user_id = '123e4567-e89b-12d3-a456-426614174000'
ORDER BY session_start DESC
LIMIT 100;

-- Cross-partition query with aggregation
EXPLAIN (ANALYZE, BUFFERS)
SELECT 
    DATE_TRUNC('month', session_start) as month,
    COUNT(*) as total_sessions,
    AVG(duration) as avg_duration
FROM user_sessions
WHERE session_start >= '2023-01-01'
  AND session_start < '2023-07-01'
GROUP BY DATE_TRUNC('month', session_start)
ORDER BY month;

-- =============================================
-- 8. PARTITION STATISTICS AND MONITORING
-- =============================================

-- Function to get partition statistics
CREATE OR REPLACE FUNCTION get_partition_stats(parent_table TEXT)
RETURNS TABLE (
    partition_name TEXT,
    row_count BIGINT,
    size_bytes BIGINT,
    last_vacuum TIMESTAMP,
    last_analyze TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.relname::TEXT as partition_name,
        s.n_live_tup as row_count,
        pg_total_relation_size(c.oid) as size_bytes,
        GREATEST(last_vacuum, last_autovacuum) as last_vacuum,
        GREATEST(last_analyze, last_autoanalyze) as last_analyze
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    LEFT JOIN pg_stat_user_tables s ON s.relname = c.relname
    WHERE n.nspname = 'public'
      AND c.relname LIKE parent_table || '_%'
    ORDER BY c.relname;
END;
$$ LANGUAGE plpgsql;

-- Get statistics for user sessions partitions
SELECT * FROM get_partition_stats('user_sessions');

-- =============================================
-- 9. DATA MIGRATION TO PARTITIONS
-- =============================================

-- Move existing data to appropriate partitions
INSERT INTO user_sessions_2023_10 
SELECT * FROM user_sessions_staging 
WHERE session_start >= '2023-10-01' 
  AND session_start < '2023-11-01';

-- Verify data migration
SELECT 
    partition_name,
    COUNT(*) as row_count
FROM (
    SELECT 'user_sessions_2023_10' as partition_name, COUNT(*) as count FROM user_sessions_2023_10
    UNION ALL
    SELECT 'user_sessions_default' as partition_name, COUNT(*) as count FROM user_sessions_default
) counts
GROUP BY partition_name;