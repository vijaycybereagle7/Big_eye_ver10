-- =============================================
-- MATERIALIZED VIEWS CREATION SCRIPTS
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. USER ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- User engagement summary materialized view
CREATE MATERIALIZED VIEW user_engagement_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.created_at as signup_date,
    u.status,
    COUNT(s.id) as total_sessions,
    COALESCE(SUM(s.session_duration), 0) as total_session_duration,
    COALESCE(AVG(s.session_duration), 0) as avg_session_duration,
    COALESCE(MAX(s.session_start), '1970-01-01') as last_activity,
    COUNT(CASE WHEN s.session_start >= NOW() - INTERVAL '30 days' THEN 1 END) as sessions_last_30_days,
    COUNT(CASE WHEN s.session_start >= NOW() - INTERVAL '7 days' THEN 1 END) as sessions_last_7_days,
    COUNT(CASE WHEN s.session_start >= NOW() - INTERVAL '1 day' THEN 1 END) as sessions_last_day,
    COUNT(p.id) as total_purchases,
    COALESCE(SUM(p.amount), 0) as total_revenue,
    COALESCE(AVG(p.amount), 0) as avg_purchase_amount,
    CASE 
        WHEN COUNT(CASE WHEN s.session_start >= NOW() - INTERVAL '30 days' THEN 1 END) = 0 THEN 'inactive'
        WHEN COUNT(CASE WHEN s.session_start >= NOW() - INTERVAL '7 days' THEN 1 END) = 0 THEN 'dormant'
        ELSE 'active'
    END as engagement_status
FROM users u
LEFT JOIN user_sessions s ON u.id = s.user_id
LEFT JOIN user_payments p ON u.id = p.user_id AND p.status = 'completed'
WHERE u.deleted_at IS NULL
GROUP BY u.id, u.email, u.first_name, u.last_name, u.created_at, u.status;

-- Create index on materialized view
CREATE UNIQUE INDEX idx_user_engagement_user_id ON user_engagement_summary(user_id);
CREATE INDEX idx_user_engagement_status ON user_engagement_summary(engagement_status);
CREATE INDEX idx_user_engagement_last_activity ON user_engagement_summary(last_activity);
CREATE INDEX idx_user_engagement_revenue ON user_engagement_summary(total_revenue DESC);

-- =============================================
-- 2. DAILY ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- Daily user activity summary
CREATE MATERIALIZED VIEW daily_user_activity AS
SELECT 
    DATE_TRUNC('day', session_start) as activity_date,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(DISTINCT CASE WHEN session_duration > 0 THEN user_id END) as engaged_users,
    COUNT(*) as total_sessions,
    COALESCE(AVG(session_duration), 0) as avg_session_duration,
    SUM(session_duration) as total_session_time,
    COUNT(CASE WHEN session_duration < 60 THEN 1 END) as short_sessions,
    COUNT(CASE WHEN session_duration > 1800 THEN 1 END) as long_sessions
FROM user_sessions
WHERE session_start >= NOW() - INTERVAL '90 days'
GROUP BY DATE_TRUNC('day', session_start)
ORDER BY activity_date;

-- Create indexes
CREATE INDEX idx_daily_activity_date ON daily_user_activity(activity_date);
CREATE INDEX idx_daily_activity_users ON daily_user_activity(active_users);
CREATE UNIQUE INDEX idx_daily_activity_date_unique ON daily_user_activity(activity_date);

-- =============================================
-- 3. REVENUE ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- Monthly revenue summary
CREATE MATERIALIZED VIEW monthly_revenue_summary AS
SELECT 
    DATE_TRUNC('month', transaction_date) as month,
    COUNT(*) as total_transactions,
    COUNT(DISTINCT user_id) as paying_users,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_transaction_amount,
    SUM(CASE WHEN status = 'refunded' THEN amount ELSE 0 END) as refunds_total,
    SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) as net_revenue,
    COUNT(CASE WHEN amount > 100 THEN 1 END) as high_value_transactions,
    COUNT(CASE WHEN payment_method = 'credit_card' THEN 1 END) as credit_card_transactions,
    COUNT(CASE WHEN payment_method = 'paypal' THEN 1 END) as paypal_transactions
FROM user_payments
WHERE transaction_date >= NOW() - INTERVAL '24 months'
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month;

-- Create indexes
CREATE UNIQUE INDEX idx_monthly_revenue_month ON monthly_revenue_summary(month);
CREATE INDEX idx_monthly_revenue_amount ON monthly_revenue_summary(net_revenue DESC);

-- =============================================
-- 4. CONTENT ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- Content performance summary
CREATE MATERIALIZED VIEW content_performance_summary AS
SELECT 
    c.id as content_id,
    c.title,
    c.content_type,
    c.published_at,
    c.author_id,
    COUNT(v.id) as total_views,
    COUNT(DISTINCT v.user_id) as unique_viewers,
    COUNT(CASE WHEN v.viewed_at >= NOW() - INTERVAL '30 days' THEN 1 END) as views_last_30_days,
    COUNT(CASE WHEN v.viewed_at >= NOW() - INTERVAL '7 days' THEN 1 END) as views_last_7_days,
    AVG(v.watch_time) as avg_watch_time,
    SUM(v.watch_time) as total_watch_time,
    COUNT(CASE WHEN v.completed = true THEN 1 END) as completions,
    COUNT(CASE WHEN v.liked = true THEN 1 END) as likes,
    COUNT(CASE WHEN v.shared = true THEN 1 END) as shares,
    COUNT(CASE WHEN v.reported = true THEN 1 END) as reports,
    ROUND(
        COUNT(CASE WHEN v.liked = true THEN 1 END) * 100.0 / NULLIF(COUNT(v.id), 0), 
        2
    ) as engagement_rate
FROM content c
LEFT JOIN user_content_views v ON c.id = v.content_id
WHERE c.deleted_at IS NULL
  AND c.published_at >= NOW() - INTERVAL '365 days'
GROUP BY c.id, c.title, c.content_type, c.published_at, c.author_id
ORDER BY total_views DESC;

-- Create indexes
CREATE INDEX idx_content_performance_id ON content_performance_summary(content_id);
CREATE INDEX idx_content_performance_views ON content_performance_summary(total_views DESC);
CREATE INDEX idx_content_performance_engagement ON content_performance_summary(engagement_rate DESC);
CREATE INDEX idx_content_performance_type ON content_performance_summary(content_type);

-- =============================================
-- 5. REAL-TIME METRICS MATERIALIZED VIEWS
-- =============================================

-- Real-time user statistics
CREATE MATERIALIZED VIEW realtime_user_stats AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as new_users,
    COUNT(CASE WHEN source = 'organic_search' THEN 1 END) as organic_users,
    COUNT(CASE WHEN source = 'paid_ads' THEN 1 END) as paid_users,
    COUNT(CASE WHEN source = 'social_media' THEN 1 END) as social_users,
    COUNT(CASE WHEN source = 'referral' THEN 1 END) as referral_users,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_users,
    COUNT(CASE WHEN email_verified_at IS NOT NULL THEN 1 END) as verified_users
FROM users
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour;

-- Create indexes
CREATE INDEX idx_realtime_stats_hour ON realtime_user_stats(hour);
CREATE UNIQUE INDEX idx_realtime_stats_hour_unique ON realtime_user_stats(hour);

-- =============================================
-- 6. GEOGRAPHIC ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- Geographic user distribution
CREATE MATERIALIZED VIEW geographic_user_distribution AS
SELECT 
    COALESCE(up.country, 'Unknown') as country,
    COALESCE(up.state_province, 'Unknown') as state_province,
    COALESCE(up.city, 'Unknown') as city,
    COUNT(*) as user_count,
    COUNT(CASE WHEN u.status = 'active' THEN 1 END) as active_users,
    COUNT(CASE WHEN u.created_at >= NOW() - INTERVAL '30 days' THEN 1 END) as new_users_30_days,
    AVG(EXTRACT(YEAR FROM AGE(u.created_at))) as avg_account_age_years,
    COUNT(CASE WHEN up.premium = true THEN 1 END) as premium_users
FROM users u
LEFT JOIN user_profiles up ON u.id = up.user_id
WHERE u.deleted_at IS NULL
  AND u.created_at >= NOW() - INTERVAL '90 days'
GROUP BY up.country, up.state_province, up.city
HAVING COUNT(*) >= 10
ORDER BY user_count DESC, country, state_province, city;

-- Create indexes
CREATE INDEX idx_geo_dist_country ON geographic_user_distribution(country);
CREATE INDEX idx_geo_dist_state ON geographic_user_distribution(state_province);
CREATE INDEX idx_geo_dist_city ON geographic_user_distribution(city);
CREATE INDEX idx_geo_dist_user_count ON geographic_user_distribution(user_count DESC);

-- =============================================
-- 7. PERFORMANCE ANALYTICS MATERIALIZED VIEWS
-- =============================================

-- System performance metrics
CREATE MATERIALIZED VIEW system_performance_metrics AS
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    service_name,
    AVG(response_time) as avg_response_time,
    MAX(response_time) as max_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time) as p95_response_time,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY response_time) as p99_response_time,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) as successful_requests,
    COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_requests,
    ROUND(
        COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as success_rate
FROM system_logs
WHERE timestamp >= NOW() - INTERVAL '24 hours'
  AND log_level != 'DEBUG'
GROUP BY DATE_TRUNC('minute', timestamp), service_name
ORDER BY minute DESC, service_name;

-- Create indexes
CREATE INDEX idx_perf_metrics_minute ON system_performance_metrics(minute);
CREATE INDEX idx_perf_metrics_service ON system_performance_metrics(service_name);
CREATE INDEX idx_perf_metrics_response_time ON system_performance_metrics(avg_response_time DESC);

-- =============================================
-- 8. COHORT ANALYSIS MATERIALIZED VIEWS
-- =============================================

-- User cohort analysis
CREATE MATERIALIZED VIEW user_cohort_analysis AS
WITH cohorts AS (
    SELECT 
        user_id,
        DATE_TRUNC('month', signup_date) as cohort_month,
        DATE_TRUNC('month', created_at) as activity_month,
        EXTRACT(YEAR FROM age(DATE_TRUNC('month', created_at), DATE_TRUNC('month', signup_date))) * 12 +
        EXTRACT(MONTH FROM age(DATE_TRUNC('month', created_at), DATE_TRUNC('month', signup_date))) as months_since_signup
    FROM user_engagement_summary
    JOIN users u ON user_id = u.id
    CROSS JOIN generate_series(
        DATE_TRUNC('month', signup_date),
        DATE_TRUNC('month', NOW()),
        INTERVAL '1 month'
    ) AS periods(activity_month)
    WHERE u.deleted_at IS NULL
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT user_id) as cohort_size
    FROM cohorts
    WHERE months_since_signup = 0
    GROUP BY cohort_month
),
cohort_activity AS (
    SELECT 
        cohort_month,
        months_since_signup,
        COUNT(DISTINCT user_id) as active_users
    FROM cohorts
    WHERE user_id IS NOT NULL
    GROUP BY cohort_month, months_since_signup
)
SELECT 
    c.cohort_month,
    c.months_since_signup,
    cs.cohort_size,
    c.active_users,
    ROUND(c.active_users * 100.0 / cs.cohort_size, 2) as retention_rate
FROM cohort_activity c
JOIN cohort_sizes cs ON c.cohort_month = cs.cohort_month
WHERE c.cohort_month >= DATE_TRUNC('month', NOW()) - INTERVAL '12 months'
ORDER BY c.cohort_month, c.months_since_signup;

-- Create indexes
CREATE INDEX idx_cohort_analysis_month ON user_cohort_analysis(cohort_month);
CREATE INDEX idx_cohort_analysis_months ON user_cohort_analysis(months_since_signup);

-- =============================================
-- 9. MATERIALIZED VIEW REFRESH FUNCTIONS
-- =============================================

-- Function to refresh user engagement summary
CREATE OR REPLACE FUNCTION refresh_user_engagement_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_engagement_summary;
    
    -- Log the refresh
    INSERT INTO maintenance_logs (operation, table_name, timestamp, status)
    VALUES ('refresh', 'user_engagement_summary', NOW(), 'success');
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO maintenance_logs (operation, table_name, timestamp, status, error_message)
        VALUES ('refresh', 'user_engagement_summary', NOW(), 'error', SQLERRM);
        RAISE;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS TABLE (view_name TEXT, refresh_time TIMESTAMP, status TEXT) AS $$
DECLARE
    mv_record RECORD;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    refresh_duration INTERVAL;
    status_text TEXT;
BEGIN
    FOR mv_record IN
        SELECT schemaname, matviewname
        FROM pg_matviews
        WHERE schemaname = 'public'
    LOOP
        start_time := NOW();
        
        BEGIN
            EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I.%I', 
                          mv_record.schemaname, mv_record.matviewname);
            end_time := NOW();
            refresh_duration := end_time - start_time;
            status_text := 'success';
        EXCEPTION
            WHEN OTHERS THEN
                end_time := NOW();
                refresh_duration := end_time - start_time;
                status_text := 'error';
        END;
        
        RETURN QUERY
        SELECT 
            mv_record.matviewname::TEXT,
            end_time,
            status_text;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 10. AUTOMATED REFRESH SCHEDULING
-- =============================================

-- Schedule regular refreshes (requires pg_cron)
-- SELECT cron.schedule('refresh-user-engagement', '*/15 * * * *', 'SELECT refresh_user_engagement_summary();');
-- SELECT cron.schedule('refresh-daily-analytics', '0 2 * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY daily_user_activity;');
-- SELECT cron.schedule('refresh-monthly-analytics', '0 3 1 * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_revenue_summary;');
-- SELECT cron.schedule('refresh-realtime-stats', '*/5 * * * *', 'REFRESH MATERIALIZED VIEW CONCURRENTLY realtime_user_stats;');

-- =============================================
-- 11. MATERIALIZED VIEW MONITORING
-- =============================================

-- Function to check materialized view freshness
CREATE OR REPLACE FUNCTION check_materialized_view_freshness()
RETURNS TABLE (
    view_name TEXT,
    last_refresh TIMESTAMP,
    staleness_minutes NUMERIC,
    needs_refresh BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mv.matviewname::TEXT,
        mv.last_refresh_time,
        EXTRACT(EPOCH FROM (NOW() - mv.last_refresh_time)) / 60 as staleness_minutes,
        CASE 
            WHEN mv.last_refresh_time < NOW() - INTERVAL '15 minutes' THEN true
            ELSE false
        END as needs_refresh
    FROM pg_matviews mv
    WHERE mv.schemaname = 'public'
    ORDER BY mv.last_refresh_time;
END;
$$ LANGUAGE plpgsql;

-- Check materialized view sizes
SELECT 
    n.nspname as schema_name,
    c.relname as view_name,
    pg_size_pretty(pg_total_relation_size(c.oid)) as size,
    pg_size_pretty(pg_relation_size(c.oid)) as table_size,
    pg_size_pretty(pg_total_relation_size(c.oid) - pg_relation_size(c.oid)) as indexes_size
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'm'
  AND n.nspname = 'public'
ORDER BY pg_total_relation_size(c.oid) DESC;

-- =============================================
-- 12. CLEANUP AND MAINTENANCE
-- =============================================

-- Function to clean up old materialized view data
CREATE OR REPLACE FUNCTION cleanup_old_materialized_views()
RETURNS INTEGER AS $$
DECLARE
    drop_count INTEGER := 0;
BEGIN
    -- Drop old daily aggregates (keep 90 days)
    DELETE FROM daily_user_activity 
    WHERE activity_date < NOW() - INTERVAL '90 days';
    
    -- Drop old real-time stats (keep 24 hours)
    DELETE FROM realtime_user_stats 
    WHERE hour < NOW() - INTERVAL '24 hours';
    
    -- Get drop count
    GET DIAGNOSTICS drop_count = ROW_COUNT;
    
    -- Log cleanup
    INSERT INTO maintenance_logs (operation, table_name, records_affected, timestamp, status)
    VALUES ('cleanup', 'materialized_views', drop_count, NOW(), 'success');
    
    RETURN drop_count;
END;
$$ LANGUAGE plpgsql;