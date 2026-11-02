-- =============================================
-- REDIS CACHING IMPLEMENTATION (5 LEVELS)
-- Performance Optimization Implementation
-- =============================================

-- =============================================
-- 1. API RESPONSES CACHE (Level 1)
-- =============================================

-- Cache API responses with TTL
-- Key pattern: api:endpoint:params:version

-- Set API response cache
-- redis-cli SET api:users:profile:123:v1 '{"user_id": 123, "data": {...}}' EX 300

-- Get API response cache
-- redis-cli GET api:users:profile:123:v1

-- Delete API response cache
-- redis-cli DEL api:users:profile:123:v1

-- Set multiple API responses
-- redis-cli MSET api:users:list:v1:page1 '[]' EX 60 api:users:list:v1:page2 '[]' EX 60

-- Cache invalidation pattern
-- redis-cli KEYS "api:users:*" | xargs redis-cli DEL

-- =============================================
-- 2. REPUTATION SCORES CACHE (Level 2)
-- =============================================

-- Cache user reputation scores
-- Key pattern: reputation:user:{user_id}

-- Set reputation score with scoring metadata
-- redis-cli HSET reputation:user:123 score 85.5 confidence 0.92 last_updated 1640995200

-- Get reputation score
-- redis-cli HGET reputation:user:123 score

-- Get all reputation data
-- redis-cli HGETALL reputation:user:123

-- Batch set reputation scores
-- redis-cli HSET reputation:user:124 score 92.1 confidence 0.96 last_updated 1640995201
-- redis-cli HSET reputation:user:125 score 78.3 confidence 0.89 last_updated 1640995202

-- Cache reputation for multiple users
-- redis-cli HMSET reputation:batch:users:124 score 92.1 confidence 0.96
-- redis-cli HMSET reputation:batch:users:125 score 78.3 confidence 0.89

-- =============================================
-- 3. BLACKLIST RESULTS CACHE (Level 3)
-- =============================================

-- Cache blacklist check results
-- Key pattern: blacklist:{type}:{identifier}

-- Set email blacklist check
-- redis-cli SET blacklist:email:test@example.com result:blocked reason:"Disposable email" TTL 86400

-- Set IP blacklist check
-- redis-cli SET blacklist:ip:192.168.1.1 result:allowed TTL 3600

-- Set phone blacklist check
-- redis-cli SET blacklist:phone:+1234567890 result:verified TTL 7200

-- Get blacklist result
-- redis-cli GET blacklist:email:test@example.com

-- Batch blacklist check
-- redis-cli MSET blacklist:email:test1@example.com result:blocked blacklist:email:test2@example.com result:allowed

-- Set blacklist status with additional data
-- redis-cli HSET blacklist:ip:192.168.1.2 result "allowed" trust_score 85 risk_level "low"

-- =============================================
-- 4. ML PREDICTIONS CACHE (Level 4)
-- =============================================

-- Cache ML model predictions
-- Key pattern: ml:{model_name}:{feature_hash}

-- Set fraud detection prediction
-- redis-cli SET ml:fraud_detector:abc123 '{"fraud_probability": 0.23, "features": {...}, "model_version": "v2.1"}' EX 1800

-- Set sentiment analysis prediction
-- redis-cli SET ml:sentiment_analyzer:def456 '{"sentiment": "positive", "confidence": 0.89, "score": 0.87}' EX 3600

-- Set user behavior prediction
-- redis-cli SET ml:behavior_predictor:ghi789 '{"churn_probability": 0.15, "ltv_prediction": 1250.50, "features": {...}}' EX 900

-- Store prediction cache with metadata
-- redis-cli HMSET ml:anomaly_detection:xyz001 prediction_type "anomaly" confidence 0.95 score 0.78 processing_time 45

-- Get ML prediction
-- redis-cli GET ml:fraud_detector:abc123

-- Batch ML predictions
-- redis-cli MSET ml:risk_scoring:user123 '{"risk_score": 65.2}' EX 1200 ml:risk_scoring:user124 '{"risk_score": 89.7}' EX 1200

-- =============================================
-- 5. AGGREGATED STATISTICS CACHE (Level 5)
-- =============================================

-- Cache aggregated analytics data
-- Key pattern: stats:{metric}:{time_period}

-- Cache daily user statistics
-- redis-cli SET stats:users:daily:2023-10-30 '{"total": 1250, "active": 980, "new": 89}' EX 3600

-- Cache hourly revenue statistics
-- redis-cli SET stats:revenue:hourly:2023103015 '{"total": 15420.50, "orders": 145, "avg_order": 106.35}' EX 900

-- Cache weekly engagement metrics
-- redis-cli SET stats:engagement:weekly:2023-w43 '{"avg_session": 1245, "bounce_rate": 0.32, "page_views": 45230}' EX 1800

-- Cache real-time counters
-- redis-cli INCR stats:active_users
-- redis-cli INCR stats:current_sessions
-- redis-cli INCRBY stats:total_revenue 156.75

-- Cache percentile data
-- redis-cli SET stats:response_time:p95:daily '{"value": 245, "unit": "ms"}' EX 1800

-- Set complex statistics
-- redis-cli HMSET stats:user_segments:daily count_premium 340 count_basic 890 count_trial 120

-- =============================================
-- CACHE INVALATION STRATEGIES
-- =============================================

-- Invalidate user-related caches
-- redis-cli DEL "reputation:user:123"
-- redis-cli DEL "api:users:profile:123:v1"
-- redis-cli SADD invalidation_queue "user:123"

-- Bulk invalidation by pattern
-- redis-cli EVAL "for _,key in ipairs(redis.call('KEYS','api:*')) do redis.call('DEL', key) end" 0

-- =============================================
-- CACHE MONITORING AND HEALTH CHECKS
-- =============================================

-- Get cache hit rate for user profiles
-- redis-cli GET cache:hits:profiles
-- redis-cli GET cache:misses:profiles

-- Monitor memory usage per cache type
-- redis-cli INFO MEMORY | grep used_memory_human

-- Get cache statistics
-- redis-cli INFO STATS | grep keyspace_hits
-- redis-cli INFO STATS | grep keyspace_misses

-- =============================================
-- REDIS SCRIPT FOR CACHE WARMING
-- =============================================

-- Lua script for warming reputation cache
-- local keys = redis.call('KEYS', 'reputation:user:*')
-- for i=1,#keys,100 do
--     local batch = {}
--     for j=i,math.min(i+99,#keys) do
--         table.insert(batch, keys[j])
--     end
--     redis.call('MGET', unpack(batch))
-- end

-- =============================================
-- ADVANCED CACHING FEATURES
-- =============================================

-- Set cache with conditional updates
-- redis-cli SETNX api:last_updated:users:profile "2023-10-30T15:30:00"

-- Implement cache locking for expensive operations
-- redis-cli SET lock:expensive:operation "locked" EX 30 NX

-- Cache with versioning
-- redis-cli SET api:users:v2:123 "new_data" EX 300
-- redis-cli DEL api:users:v1:123

-- Bloom filter for efficient cache checking
-- redis-cli BF.ADD blacklisted_emails "test@spam.com"
-- redis-cli BF.EXISTS blacklisted_emails "test@spam.com"