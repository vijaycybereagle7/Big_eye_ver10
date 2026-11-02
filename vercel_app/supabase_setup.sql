-- Supabase Database Setup for Vercel Cybersecurity API
-- Run this SQL script in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create API cache table
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,
    cached_data JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for cache expiration
CREATE INDEX idx_api_cache_expires_at ON api_cache(expires_at);

-- Create validation logs table
CREATE TABLE validation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for validation logs
CREATE INDEX idx_validation_logs_timestamp ON validation_logs(timestamp);
CREATE INDEX idx_validation_logs_endpoint ON validation_logs(endpoint);

-- Create reputation logs table
CREATE TABLE reputation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for reputation logs
CREATE INDEX idx_reputation_logs_timestamp ON reputation_logs(timestamp);
CREATE INDEX idx_reputation_logs_endpoint ON reputation_logs(endpoint);
CREATE INDEX idx_reputation_logs_value_type ON reputation_logs(value_type);

-- Create threat intelligence data table (for future use)
CREATE TABLE threat_intel (
    id BIGSERIAL PRIMARY KEY,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    threat_level TEXT NOT NULL,
    threat_indicators JSONB,
    sources JSONB,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes for threat intelligence
CREATE INDEX idx_threat_intel_value ON threat_intel(value);
CREATE INDEX idx_threat_intel_type ON threat_intel(value_type);
CREATE INDEX idx_threat_intel_level ON threat_intel(threat_level);
CREATE INDEX idx_threat_intel_last_seen ON threat_intel(last_seen);
CREATE INDEX idx_threat_intel_active ON threat_intel(is_active);

-- Create API usage statistics table
CREATE TABLE api_usage_stats (
    id BIGSERIAL PRIMARY KEY,
    api_key TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    request_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_processing_time_ms FLOAT DEFAULT 0,
    date DATE DEFAULT CURRENT_DATE,
    hour INTEGER DEFAULT EXTRACT(HOUR FROM NOW()),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for usage statistics
CREATE INDEX idx_api_usage_date_hour ON api_usage_stats(date, hour);
CREATE INDEX idx_api_usage_key ON api_usage_stats(api_key);
CREATE INDEX idx_api_usage_endpoint ON api_usage_stats(endpoint);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for api_usage_stats
CREATE TRIGGER update_api_usage_stats_updated_at
    BEFORE UPDATE ON api_usage_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
-- Add some sample malicious domains for testing
INSERT INTO threat_intel (value, value_type, threat_level, threat_indicators, sources) VALUES
('malware-example.com', 'domain', 'high', '["phishing_campaign", "malware_distribution"]', '{"virustotal": true, "abuseipdb": true}'),
('192.168.1.100', 'ip', 'medium', '["port_scan", "suspicious_activity"]', '{"internal_detection": true}'),
('http://phishing-site.com/login', 'url', 'critical', '["phishing_page", "credential_harvesting"]', '{"user_report": true, "virustotal": true}');

-- Grant permissions (adjust based on your Supabase setup)
-- These permissions assume you're using the service role key
-- For anon key access, you may need to adjust RLS policies

-- Enable Row Level Security (optional - disable for simplicity in serverless)
-- ALTER TABLE api_cache ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE validation_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE reputation_logs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE threat_intel ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE api_usage_stats ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (if RLS is enabled)
-- For service role (full access)
CREATE POLICY "Service role full access on api_cache" ON api_cache
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on validation_logs" ON validation_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on reputation_logs" ON reputation_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on threat_intel" ON threat_intel
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on api_usage_stats" ON api_usage_stats
    FOR ALL USING (auth.role() = 'service_role');

-- For anon role (read-only access to some tables)
CREATE POLICY "Anon read access on api_cache" ON api_cache
    FOR SELECT USING (auth.role() = 'anon');

CREATE POLICY "Anon read access on threat_intel" ON threat_intel
    FOR SELECT USING (auth.role() = 'anon' AND is_active = true);

-- Create function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM api_cache WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get usage statistics
CREATE OR REPLACE FUNCTION get_api_usage_stats(
    p_api_key TEXT DEFAULT NULL,
    p_start_date DATE DEFAULT NULL,
    p_end_date DATE DEFAULT NULL
)
RETURNS TABLE(
    api_key TEXT,
    endpoint TEXT,
    total_requests BIGINT,
    success_rate FLOAT,
    avg_processing_time FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.api_key,
        u.endpoint,
        SUM(u.request_count) as total_requests,
        CASE 
            WHEN SUM(u.request_count) > 0 
            THEN CAST(SUM(u.success_count) AS FLOAT) / SUM(u.request_count)
            ELSE 0.0 
        END as success_rate,
        CASE 
            WHEN SUM(u.request_count) > 0 
            THEN SUM(u.total_processing_time_ms) / SUM(u.request_count)
            ELSE 0.0 
        END as avg_processing_time
    FROM api_usage_stats u
    WHERE (p_api_key IS NULL OR u.api_key = p_api_key)
      AND (p_start_date IS NULL OR u.date >= p_start_date)
      AND (p_end_date IS NULL OR u.date <= p_end_date)
    GROUP BY u.api_key, u.endpoint
    ORDER BY u.api_key, u.endpoint;
END;
$$ LANGUAGE plpgsql;

-- Create a view for recent threats
CREATE OR REPLACE VIEW recent_threats AS
SELECT 
    id,
    value,
    value_type,
    threat_level,
    threat_indicators,
    sources,
    first_seen,
    last_seen,
    confidence_score,
    EXTRACT(EPOCH FROM (NOW() - last_seen)) / 3600 as hours_since_last_seen
FROM threat_intel
WHERE is_active = TRUE
ORDER BY last_seen DESC;

-- Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION cleanup_expired_cache() TO service_role;
GRANT EXECUTE ON FUNCTION get_api_usage_stats(TEXT, DATE, DATE) TO service_role;

-- Set up automated cleanup (requires pg_cron extension)
-- Uncomment if pg_cron is available in your Supabase plan
-- SELECT cron.schedule('cleanup-expired-cache', '0 */6 * * *', 'SELECT cleanup_expired_cache();');

-- Success message
SELECT 'Supabase database setup completed successfully!' as message;
