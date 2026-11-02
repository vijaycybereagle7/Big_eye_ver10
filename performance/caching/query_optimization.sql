-- =============================================
-- QUERY OPTIMIZATION WITH CACHING STRATEGIES
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. OPTIMIZED QUERY PATTERNS
-- =============================================

-- Optimized User Query with Proper JOINs
EXPLAIN (ANALYZE, BUFFERS)
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    p.bio,
    p.location,
    COUNT(s.id) as session_count,
    MAX(s.created_at) as last_session
FROM users u
LEFT JOIN user_profiles p ON u.id = p.user_id
LEFT JOIN sessions s ON u.id = s.user_id AND s.created_at >= NOW() - INTERVAL '30 days'
WHERE u.status = 'active'
  AND u.created_at >= NOW() - INTERVAL '90 days'
GROUP BY u.id, u.email, u.first_name, u.last_name, p.bio, p.location
ORDER BY last_session DESC NULLS LAST
LIMIT 100;

-- Optimized Pagination Query
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM users u
WHERE u.id > $1  -- Last ID from previous page
  AND u.status = 'active'
ORDER BY u.id
LIMIT 50;

-- Optimized Aggregation Query
EXPLAIN (ANALYZE, BUFFERS)
WITH user_stats AS (
    SELECT 
        user_id,
        COUNT(*) as total_sessions,
        AVG(session_duration) as avg_duration,
        MAX(created_at) as last_activity
    FROM user_sessions
    WHERE created_at >= NOW() - INTERVAL '30 days'
      AND status = 'completed'
    GROUP BY user_id
)
SELECT 
    u.email,
    us.total_sessions,
    us.avg_duration,
    us.last_activity
FROM users u
JOIN user_stats us ON u.id = us.user_id
WHERE u.status = 'active'
ORDER BY us.total_sessions DESC;

-- =============================================
-- 2. CACHING STRATEGY FUNCTIONS
-- =============================================

-- Function to get user profile with caching
CREATE OR REPLACE FUNCTION get_user_profile_cached(user_id_param UUID)
RETURNS TABLE (
    user_id UUID,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    bio TEXT,
    location TEXT,
    created_at TIMESTAMP
) AS $$
BEGIN
    -- Cache hit - return from cache
    IF EXISTS (
        SELECT 1 FROM cache_profiles 
        WHERE user_id = user_id_param 
        AND expires_at > NOW()
    ) THEN
        RETURN QUERY
        SELECT cp.user_id, cp.email, cp.first_name, 
               cp.last_name, cp.bio, cp.location, cp.created_at
        FROM cache_profiles cp
        WHERE cp.user_id = user_id_param 
        AND cp.expires_at > NOW();
        RETURN;
    END IF;
    
    -- Cache miss - fetch from main table
    RETURN QUERY
    SELECT u.id, u.email, u.first_name, 
           u.last_name, p.bio, p.location, u.created_at
    FROM users u
    LEFT JOIN user_profiles p ON u.id = p.user_id
    WHERE u.id = user_id_param;
    
    -- Update cache
    INSERT INTO cache_profiles (user_id, email, first_name, last_name, bio, location, created_at, expires_at)
    SELECT u.id, u.email, u.first_name, u.last_name, 
           p.bio, p.location, u.created_at, NOW() + INTERVAL '1 hour'
    FROM users u
    LEFT JOIN user_profiles p ON u.id = p.user_id
    WHERE u.id = user_id_param
    ON CONFLICT (user_id) 
    DO UPDATE SET 
        email = EXCLUDED.email,
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        bio = EXCLUDED.bio,
        location = EXCLUDED.location,
        expires_at = EXCLUDED.expires_at,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to invalidate user profile cache
CREATE OR REPLACE FUNCTION invalidate_user_profile_cache(user_id_param UUID)
RETURNS VOID AS $$
BEGIN
    DELETE FROM cache_profiles WHERE user_id = user_id_param;
    
    -- Also invalidate in Redis (application level)
    PERFORM pg_notify('cache_invalidation', 'user_profile:' || user_id_param);
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 3. QUERY PLAN OPTIMIZATION
-- =============================================

-- Force specific join order for critical queries
CREATE OR REPLACE FUNCTION get_user_sessions_optimized(user_id_param UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE (
    session_id UUID,
    created_at TIMESTAMP,
    session_duration INTEGER,
    ip_address INET,
    user_agent TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.created_at,
        s.session_duration,
        s.ip_address,
        s.user_agent
    FROM user_sessions s
    WHERE s.user_id = user_id_param
      AND s.created_at >= NOW() - (days_back || ' days')::INTERVAL
      AND s.status = 'completed'
    ORDER BY s.created_at DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 4. BATCH PROCESSING FUNCTIONS
-- =============================================

-- Batch user processing for analytics
CREATE OR REPLACE FUNCTION process_user_batch(batch_size INTEGER DEFAULT 1000)
RETURNS TABLE (
    user_id UUID,
    email TEXT,
    total_sessions BIGINT,
    total_revenue DECIMAL,
    last_activity TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    WITH ranked_users AS (
        SELECT 
            u.id,
            u.email,
            ROW_NUMBER() OVER (ORDER BY u.created_at DESC) as rn
        FROM users u
        WHERE u.status = 'active'
          AND u.deleted_at IS NULL
    ),
    current_batch AS (
        SELECT id, email
        FROM ranked_users
        WHERE rn <= batch_size
    ),
    user_analytics AS (
        SELECT 
            cb.id,
            cb.email,
            COALESCE(s.session_count, 0) as total_sessions,
            COALESCE(o.total_revenue, 0) as total_revenue,
            s.last_activity
        FROM current_batch cb
        LEFT JOIN (
            SELECT 
                user_id,
                COUNT(*) as session_count,
                MAX(created_at) as last_activity
            FROM user_sessions
            WHERE created_at >= NOW() - INTERVAL '90 days'
            GROUP BY user_id
        ) s ON cb.id = s.user_id
        LEFT JOIN (
            SELECT 
                user_id,
                SUM(amount) as total_revenue
            FROM orders
            WHERE status = 'completed'
              AND created_at >= NOW() - INTERVAL '90 days'
            GROUP BY user_id
        ) o ON cb.id = o.user_id
    )
    SELECT 
        ua.id,
        ua.email,
        ua.total_sessions,
        ua.total_revenue,
        ua.last_activity
    FROM user_analytics ua
    ORDER BY ua.total_revenue DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 5. AUTOMATIC QUERY CLEANUP
-- =============================================

-- Function to clean up old cached data
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up expired profile cache
    DELETE FROM cache_profiles WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old session data
    DELETE FROM user_sessions 
    WHERE created_at < NOW() - INTERVAL '90 days' 
      AND status != 'active';
    
    -- Log cleanup
    INSERT INTO maintenance_logs (operation, records_affected, timestamp)
    VALUES ('cache_cleanup', deleted_count, NOW());
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-cache', '0 2 * * *', 'SELECT cleanup_expired_cache();');

-- =============================================
-- 6. QUERY PERFORMANCE MONITORING
-- =============================================

-- Create function to analyze query performance
CREATE OR REPLACE FUNCTION analyze_query_performance(query_text TEXT)
RETURNS TABLE (
    plan_node TEXT,
    plan_type TEXT,
    row_count BIGINT,
    loop_count BIGINT,
    shared_hit_blocks BIGINT,
    shared_read_blocks BIGINT,
    local_hit_blocks BIGINT,
    local_read_blocks BIGINT
) AS $$
BEGIN
    RETURN QUERY
    EXECUTE format('EXPLAIN (ANALYZE, BUFFERS, COSTS OFF) %s', query_text);
END;
$$ LANGUAGE plpgsql;