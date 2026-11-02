-- =============================================
-- DATABASE INDEXING STRATEGY
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. B-TREE INDEXES
-- =============================================
-- Primary use: Equality and range queries on data that can be sorted
-- Examples: numerical, date, and string columns

-- B-Tree Index on User ID (Common Query Pattern)
CREATE INDEX CONCURRENTLY idx_users_id 
ON users (id);

-- B-Tree Index on Email (Unique Lookup)
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email 
ON users (email);

-- B-Tree Index on Created Date (Range Query)
CREATE INDEX CONCURRENTLY idx_users_created_at 
ON users (created_at DESC);

-- Composite B-Tree Index for Complex Queries
CREATE INDEX CONCURRENTLY idx_users_status_created 
ON users (status, created_at DESC);

-- B-Tree Index with WHERE clause (Partial Index)
CREATE INDEX CONCURRENTLY idx_users_active 
ON users (email, created_at) 
WHERE status = 'active';

-- =============================================
-- 2. GIN INDEXES (GENERALIZED INVERTED INDEX)
-- =============================================
-- Primary use: Full-text search, JSONB data, arrays

-- GIN Index for Full-Text Search
CREATE INDEX CONCURRENTLY idx_users_search_gin 
ON users USING gin (to_tsvector('english', email || ' ' || COALESCE(first_name, '') || ' ' || COALESCE(last_name, '')));

-- GIN Index for JSONB Data
CREATE INDEX CONCURRENTLY idx_users_metadata_gin 
ON users USING gin (metadata);

-- GIN Index for Array Data
CREATE INDEX CONCURRENTLY idx_users_tags_gin 
ON users USING gin (tags);

-- GIN Index for JSONB with JSONPATH
CREATE INDEX CONCURRENTLY idx_users_preferences_gin 
ON users USING gin (preferences) 
WHERE preferences ? 'notification_settings';

-- =============================================
-- 3. GIST INDEXES (GENERALIZED SEARCH TREE)
-- =============================================
-- Primary use: Geometric data, full-text search with ranking

-- GiST Index for Point/Geometric Data
CREATE INDEX CONCURRENTLY idx_users_location_gist 
ON users USING gist (location);

-- GiST Index for Full-Text Search with Ranking
CREATE INDEX CONCURRENTLY idx_user_profiles_search_gist 
ON user_profiles USING gist (to_tsvector('english', bio));

-- GiST Index for Range Types
CREATE INDEX CONCURRENTLY idx_sessions_validity_gist 
ON sessions USING gist (validity_range);

-- GiST Index for Hierarchical Data (ltree extension)
CREATE INDEX CONCURRENTLY idx_categories_path_gist 
ON categories USING gist (category_path);

-- =============================================
-- 4. PARTIAL INDEXES
-- =============================================
-- Primary use: Index subset of data for better performance

-- Partial Index for Active Users Only
CREATE INDEX CONCURRENTLY idx_users_active_partial 
ON users (last_login_at) 
WHERE status = 'active' AND deleted_at IS NULL;

-- Partial Index for Verified Emails
CREATE INDEX CONCURRENTLY idx_users_verified_partial 
ON users (email_verified_at, status) 
WHERE email_verified_at IS NOT NULL;

-- Partial Index for Recent Activity
CREATE INDEX CONCURRENTLY idx_users_recent_activity 
ON users (last_activity_at) 
WHERE last_activity_at >= NOW() - INTERVAL '30 days';

-- Partial Index for Premium Users
CREATE INDEX CONCURRENTLY idx_users_premium_partial 
ON users (subscription_type, expires_at) 
WHERE subscription_type = 'premium' AND expires_at > NOW();

-- =============================================
-- 5. EXPRESSION INDEXES
-- =============================================

-- Lowercase Email Index
CREATE INDEX CONCURRENTLY idx_users_email_lower 
ON users (LOWER(email));

-- Calculated Field Index
CREATE INDEX CONCURRENTLY idx_users_full_name 
ON users ((first_name || ' ' || last_name));

-- Date Truncation Index
CREATE INDEX CONCURRENTLY idx_users_signup_month 
ON users (DATE_TRUNC('month', created_at));

-- Age Calculation Index
CREATE INDEX CONCURRENTLY idx_users_age_group 
ON users ((EXTRACT(YEAR FROM age(birth_date))));

-- =============================================
-- 6. MULTI-COLUMN INDEXES
-- =============================================

-- Optimal Multi-Column Index
CREATE INDEX CONCURRENTLY idx_users_multicolumn_optimal 
ON users (status, created_at, email);

-- Index for Complex WHERE and ORDER BY
CREATE INDEX CONCURRENTLY idx_users_query_optimization 
ON users (status, last_login_at DESC) 
WHERE status IN ('active', 'pending');

-- =============================================
-- 7. INDEX MAINTENANCE COMMANDS
-- =============================================

-- Reindex specific index
-- REINDEX INDEX CONCURRENTLY idx_users_email;

-- Update statistics for specific index
-- ANALYZE VERBOSE users;

-- Full reindex (off-peak maintenance)
-- REINDEX DATABASE CONCURRENTLY your_database_name;

-- =============================================
-- 8. INDEX USAGE MONITORING
-- =============================================

-- Query to find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename, indexname;

-- Query to find duplicate indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY schemaname, tablename;

-- =============================================
-- 9. INDEX PERFORMANCE ANALYSIS
-- =============================================

-- Check index size and usage
SELECT 
    i.schemaname,
    i.tablename,
    i.indexname,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
    s.idx_scan,
    s.idx_tup_read,
    s.idx_tup_fetch
FROM pg_indexes i
JOIN pg_stat_user_indexes s ON s.indexrelid = i.indexrelid
WHERE i.schemaname = 'public'
ORDER BY pg_relation_size(i.indexrelid) DESC;