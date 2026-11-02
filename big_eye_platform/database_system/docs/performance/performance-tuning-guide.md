# Performance Tuning Guide

## Table of Contents
1. [Overview](#overview)
2. [Performance Monitoring](#performance-monitoring)
3. [Database Optimization](#database-optimization)
4. [API Performance Tuning](#api-performance-tuning)
5. [Cache Optimization](#cache-optimization)
6. [Infrastructure Optimization](#infrastructure-optimization)
7. [Application Optimization](#application-optimization)
8. [Benchmarking Procedures](#benchmarking-procedures)
9. [Performance Testing](#performance-testing)
10. [Capacity Planning](#capacity-planning)
11. [Scaling Strategies](#scaling-strategies)

## Overview

This guide provides comprehensive strategies for optimizing the performance of the Cybersecurity Threat Intelligence System. It covers database tuning, API optimization, caching strategies, infrastructure improvements, and benchmarking procedures.

**Performance Goals**:
- API Response Time: < 200ms (P95), < 500ms (P99)
- Database Query Time: < 100ms (average)
- Cache Hit Rate: > 90%
- System Uptime: > 99.9%
- Throughput: 10,000+ requests/minute

## Performance Monitoring

### 1. Key Performance Indicators (KPIs)

#### 1.1 Application Metrics
```python
# Key metrics to monitor
PERFORMANCE_METRICS = {
    "api": {
        "response_time_p50": "< 100ms",
        "response_time_p95": "< 200ms", 
        "response_time_p99": "< 500ms",
        "error_rate": "< 1%",
        "throughput": "> 10000 req/min",
        "active_connections": "< 80% of max"
    },
    "database": {
        "query_time_avg": "< 50ms",
        "query_time_p95": "< 100ms",
        "connection_pool_utilization": "< 80%",
        "cache_hit_ratio": "> 95%",
        "index_usage": "> 90%"
    },
    "cache": {
        "hit_ratio": "> 90%",
        "memory_utilization": "< 80%",
        "eviction_rate": "< 5%",
        "slow_commands": "< 1/sec"
    },
    "system": {
        "cpu_utilization": "< 70%",
        "memory_utilization": "< 80%", 
        "disk_io_utilization": "< 80%",
        "network_utilization": "< 80%"
    }
}
```

#### 1.2 Monitoring Dashboard Configuration

**Grafana Dashboard: System Performance**
```json
{
  "dashboard": {
    "title": "Threat Intelligence System Performance",
    "panels": [
      {
        "title": "API Response Times",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95 Response Time"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99 Response Time"
          }
        ],
        "yAxes": [
          {
            "label": "Response Time (seconds)",
            "min": 0
          }
        ]
      },
      {
        "title": "API Throughput",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests per second"
          }
        ]
      },
      {
        "title": "Database Query Performance",
        "targets": [
          {
            "expr": "pg_stat_statements_mean_time",
            "legendFormat": "Average Query Time"
          }
        ]
      },
      {
        "title": "Cache Hit Ratio",
        "targets": [
          {
            "expr": "rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))",
            "legendFormat": "Cache Hit Ratio"
          }
        ]
      }
    ]
  }
}
```

### 2. Performance Alerting

#### 2.1 Prometheus Alert Rules
```yaml
# File: monitoring/prometheus/rules.yml
groups:
  - name: performance_alerts
    rules:
      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High API response time detected"
          description: "API response time P95 is {{ $value }}s"

      - alert: HighAPIErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High API error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: DatabaseSlowQueries
        expr: pg_stat_statements_mean_time > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "Average query time is {{ $value }}ms"

      - alert: LowCacheHitRate
        expr: rate(redis_keyspace_hits_total[5m]) / (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m])) < 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"
```

## Database Optimization

### 1. PostgreSQL Performance Tuning

#### 1.1 Configuration Optimization

**File**: `postgres/postgresql.conf`
```ini
# Memory Settings
shared_buffers = 256MB                    # 25% of total RAM
effective_cache_size = 1GB                # Estimate of OS cache size
work_mem = 4MB                            # Per operation, adjust based on queries
maintenance_work_mem = 64MB               # For VACUUM, CREATE INDEX, etc.

# Checkpoint Settings
wal_buffers = 16MB                        # WAL buffer size
checkpoint_completion_target = 0.9        # Spread checkpoints over 90% of interval
max_wal_size = 1GB                        # Maximum WAL size before checkpoint
min_wal_size = 80MB                       # Minimum WAL size to keep

# Query Planner Settings
random_page_cost = 1.1                    # SSD storage
effective_io_concurrency = 200            # Number of concurrent I/O operations
default_statistics_target = 1000          # Statistics collection target

# Connection Settings
max_connections = 200                     # Adjust based on application needs
max_prepared_transactions = 200           # For transaction pooling

# Logging Settings
log_min_duration_statement = 1000         # Log queries slower than 1 second
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# Performance Settings
shared_preload_libraries = 'pg_stat_statements'
track_activity_query_size = 2048         # Size of query text to store
```

#### 1.2 Index Optimization

**Strategic Index Creation**:
```sql
-- High-performance indexes for threat intelligence queries
-- 1. Composite index for common threat queries
CREATE INDEX CONCURRENTLY idx_threat_intel_composite_active 
ON threat_intelligence(source_id, indicator_type, is_active, created_at DESC)
WHERE is_active = true;

-- 2. Partial index for high-confidence threats
CREATE INDEX CONCURRENTLY idx_threat_intel_high_confidence 
ON threat_intelligence(confidence_score DESC, source_id)
WHERE confidence_score > 0.8;

-- 3. Expression index for efficient text search
CREATE INDEX CONCURRENTLY idx_threat_intel_search 
ON threat_intelligence USING GIN(to_tsvector('english', indicator_value || ' ' || COALESCE(notes, '')));

-- 4. Covering index for email analysis queries
CREATE INDEX CONCURRENTLY idx_email_analysis_covering 
ON email_analysis(email_domain, suspicious_score DESC, created_at DESC)
INCLUDE (email_address, risk_level);

-- 5. Hash index for exact lookups (faster than B-tree for equality)
CREATE INDEX CONCURRENTLY idx_url_hash_lookup 
ON url_analysis USING HASH(url_hash);

-- 6. Index for reputation intelligence
CREATE INDEX CONCURRENTLY idx_reputation_lookup 
ON reputation_intelligence(indicator_type, indicator_value) 
WHERE last_updated > NOW() - INTERVAL '7 days';
```

**Index Maintenance**:
```sql
-- Monthly index maintenance procedure
-- 1. Analyze index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- 2. Remove unused indexes
-- (Run analysis to identify, then drop)
-- DROP INDEX CONCURRENTLY IF EXISTS idx_unused_index;

-- 3. Reindex bloat-heavy indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as current_size,
    pg_size_pretty(pg_relation_size(indexrelid::regclass)) as expected_size,
    ROUND(
        (pg_relation_size(indexrelid::regclass)::float / 
         pg_relation_size(indexrelid)::float - 1) * 100, 2
    ) as bloat_percentage
FROM pg_stat_user_indexes
WHERE pg_relation_size(indexrelid::regclass) > 
      pg_relation_size(indexrelid) * 1.2
ORDER BY bloat_percentage DESC;

-- 4. Reindex if bloat > 20%
-- REINDEX INDEX CONCURRENTLY idx_heavily_bloated_index;
```

#### 1.3 Query Optimization

**Performance Analysis Query**:
```sql
-- Identify slow queries for optimization
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    stddev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent,
    pg_size_pretty(total_time::bigint) as total_time_pretty
FROM pg_stat_statements 
WHERE calls > 100
  AND mean_time > 100  -- Queries slower than 100ms
ORDER BY mean_time DESC 
LIMIT 20;

-- Query execution plan analysis
EXPLAIN (ANALYZE, BUFFERS, VERBOSE) 
SELECT ti.indicator_value, ti.confidence_score, ts.source_name
FROM threat_intelligence ti
JOIN threat_sources ts ON ti.source_id = ts.id
WHERE ti.indicator_type = 'ip_address'
  AND ti.confidence_score > 0.8
  AND ti.is_active = true
  AND ti.created_at > NOW() - INTERVAL '7 days'
ORDER BY ti.confidence_score DESC
LIMIT 100;
```

### 2. MongoDB Performance Optimization

#### 2.1 Configuration Tuning

**File**: `mongodb/mongod.conf`
```yaml
# Performance configuration
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2                      # 60% of available RAM
      journalCompressor: snappy
      directoryForIndexes: false
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

replication:
  replSetName: "threatintel-replica"
  oplogSizeMB: 10240                     # 10GB for heavy workloads

sharding:
  configDB: configReplSet/config1:27017,config2:27017,config3:27017

systemLog:
  verbosity: 1
  component:
    query:
      verbosity: 2

net:
  maxIncomingConnections: 1000
  wireObjectCheck: false                  # Disable for better performance

processManagement:
  fork: true
```

#### 2.2 Index Strategy

```javascript
// MongoDB index optimization script

// 1. Compound indexes for common query patterns
db.threatIntelligence.createIndex(
    {
        "sourceId": 1,
        "indicatorType": 1,
        "confidenceScore": -1,
        "isActive": 1,
        "createdAt": -1
    },
    {
        name: "compound_performance_index",
        background: true
    }
);

// 2. Text search index for notes and descriptions
db.threatIntelligence.createIndex(
    {
        "notes": "text",
        "description": "text"
    },
    {
        name: "text_search_index",
        weights: {
            "notes": 10,
            "description": 5
        },
        default_language: "english"
    }
);

// 3. Partial index for active records only
db.threatIntelligence.createIndex(
    {
        "lastSeen": -1,
        "confidenceScore": -1
    },
    {
        name: "active_records_index",
        partialFilterExpression: { "isActive": true }
    }
);

// 4. Hashed index for even distribution
db.emailAnalysis.createIndex(
    {
        "emailHash": "hashed"
    },
    {
        name: "email_hash_distribution"
    }
);

// 5. Wildcard index for dynamic queries (use carefully)
db.threatIntelligence.createIndex(
    { "$**": 1 },
    {
        name: "wildcard_all_fields",
        wildcardProjection: {
            "metadata": 1,
            "tags": 1,
            "sourceId": 1
        }
    }
);

// 6. TTL index for automatic data expiration
db.apiLogs.createIndex(
    { "createdAt": 1 },
    {
        name: "ttl_logs",
        expireAfterSeconds: 2592000  // 30 days
    }
);
```

## API Performance Tuning

### 1. FastAPI Optimization

#### 1.1 Application Configuration

**File**: `api/main.py`
```python
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cache import CacheMiddleware
import redis
import asyncio

# Performance-optimized FastAPI app
app = FastAPI(
    title="Threat Intelligence API",
    docs_url=None,  # Disable docs in production
    redoc_url=None,
    openapi_url=None,
    default_response_class=None
)

# Add performance middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Redis cache middleware
redis_client = redis.Redis(
    host='localhost', 
    port=6379, 
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True
)

@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    # Skip caching for non-GET requests or admin endpoints
    if request.method != "GET" or "/admin" in request.url.path:
        return await call_next(request)
    
    cache_key = f"api:{request.url.path}:{hash(str(request.query_params))}"
    
    # Try to get from cache
    cached_response = redis_client.get(cache_key)
    if cached_response:
        return Response(
            content=cached_response,
            media_type="application/json",
            headers={"X-Cache": "HIT"}
        )
    
    # Generate response
    response = await call_next(request)
    
    # Cache successful responses
    if response.status_code == 200:
        response_body = response.body
        redis_client.setex(cache_key, 300, response_body)  # Cache for 5 minutes
        response.headers["X-Cache"] = "MISS"
    
    return response

# Connection pooling
DATABASE_POOL_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "pool_timeout": 30
}
```

#### 1.2 Async Performance Optimization

```python
import asyncio
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import asyncpg
import motor.motor_asyncio

class OptimizedThreatService:
    def __init__(self):
        self.postgres_pool = None
        self.mongodb_client = None
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
    
    async def get_threat_intelligence_batch(
        self, 
        indicators: List[str], 
        batch_size: int = 50
    ) -> List[dict]:
        """Process multiple indicators in parallel"""
        
        # Split into batches for optimal processing
        batches = [indicators[i:i + batch_size] 
                  for i in range(0, len(indicators), batch_size)]
        
        # Process batches concurrently
        tasks = [self._process_indicator_batch(batch) 
                for batch in batches]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter results
        all_results = []
        for result in results:
            if isinstance(result, list):
                all_results.extend(result)
        
        return all_results
    
    async def _process_indicator_batch(self, indicators: List[str]) -> List[dict]:
        """Process a single batch of indicators"""
        
        # Use thread pool for CPU-intensive operations
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                self.thread_pool,
                self._get_threat_data,
                indicator
            ) for indicator in indicators
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_cached_threat_data(self, indicator: str) -> Optional[dict]:
        """Get threat data with caching"""
        
        cache_key = f"threat:{indicator}"
        
        # Try cache first
        cached = await self._async_redis_get(cache_key)
        if cached:
            return cached
        
        # Get from database if not in cache
        threat_data = await self._get_threat_data_async(indicator)
        
        # Cache for future use
        if threat_data:
            await self._async_redis_setex(
                cache_key, 
                3600,  # 1 hour TTL
                threat_data
            )
        
        return threat_data
    
    async def _get_threat_data_async(self, indicator: str) -> Optional[dict]:
        """Async database query"""
        
        async with self.postgres_pool.acquire() as conn:
            query = """
            SELECT indicator_value, confidence_score, source_name, created_at
            FROM threat_intelligence ti
            JOIN threat_sources ts ON ti.source_id = ts.id
            WHERE ti.indicator_value = $1 
              AND ti.is_active = true
            ORDER BY ti.confidence_score DESC
            LIMIT 10
            """
            
            rows = await conn.fetch(query, indicator)
            return [dict(row) for row in rows]
    
    async def _async_redis_get(self, key: str) -> Optional[dict]:
        """Async Redis get operation"""
        try:
            loop = asyncio.get_event_loop()
            value = await loop.run_in_executor(
                self.thread_pool,
                redis_client.get,
                key
            )
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def _async_redis_setex(self, key: str, ttl: int, value: dict):
        """Async Redis set with TTL"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                redis_client.setex,
                key,
                ttl,
                json.dumps(value)
            )
        except Exception:
            pass  # Log error but don't fail the request
```

### 2. Database Connection Optimization

#### 2.1 Connection Pool Management

```python
import asyncpg
import asyncio
from contextlib import asynccontextmanager

class DatabasePool:
    def __init__(self):
        self.pools = {}
        self.lock = asyncio.Lock()
    
    async def create_pool(self, database_url: str, **config):
        """Create or get existing connection pool"""
        
        async with self.lock:
            if database_url not in self.pools:
                pool = await asyncpg.create_pool(
                    database_url,
                    min_size=10,
                    max_size=50,
                    max_queries=50000,
                    max_inactive_connection_lifetime=300.0,
                    command_timeout=60,
                    server_settings={
                        'jit': 'off',  # Disable JIT for better performance
                        'application_name': 'threat-intel-api'
                    },
                    **config
                )
                self.pools[database_url] = pool
        
        return self.pools[database_url]
    
    @asynccontextmanager
    async def get_connection(self, database_url: str):
        """Get connection from pool with automatic cleanup"""
        
        pool = await self.create_pool(database_url)
        async with pool.acquire() as connection:
            # Set connection parameters
            await connection.execute("SET work_mem = '4MB'")
            await connection.execute("SET random_page_cost = '1.1'")
            yield connection
    
    async def close_all_pools(self):
        """Close all connection pools"""
        for pool in self.pools.values():
            await pool.close()

# Global pool manager
db_pool = DatabasePool()
```

### 3. Response Optimization

#### 3.1 Response Compression and Caching

```python
from fastapi import Response
from fastapi.responses import JSONResponse
import gzip
import json
from typing import Any, Dict, Optional

class OptimizedResponse:
    @staticmethod
    def create_cacheable_response(
        data: Any,
        status_code: int = 200,
        cache_ttl: int = 300,
        headers: Optional[Dict[str, str]] = None
    ) -> Response:
        """Create an optimized, cacheable response"""
        
        # Convert to JSON
        json_data = json.dumps(data, default=str)
        
        # Compress if data is large
        if len(json_data) > 1024:
            compressed_data = gzip.compress(json_data.encode())
            content = compressed_data
            headers = headers or {}
            headers["Content-Encoding"] = "gzip"
        else:
            content = json_data
        
        # Add cache headers
        headers = headers or {}
        headers.update({
            "Cache-Control": f"public, max-age={cache_ttl}",
            "ETag": f'"{hash(json_data)}"',
            "X-Cache-TTL": str(cache_ttl)
        })
        
        return Response(
            content=content,
            media_type="application/json",
            status_code=status_code,
            headers=headers
        )
    
    @staticmethod
    def create_error_response(
        error: str,
        status_code: int = 500,
        include_traceback: bool = False
    ) -> Response:
        """Create a standardized error response"""
        
        error_data = {
            "error": error,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if include_traceback:
            import traceback
            error_data["traceback"] = traceback.format_exc()
        
        return OptimizedResponse.create_cacheable_response(
            data=error_data,
            status_code=status_code,
            cache_ttl=0  # Don't cache errors
        )
```

## Cache Optimization

### 1. Redis Performance Tuning

#### 1.1 Configuration Optimization

**File**: `redis/redis.conf`
```ini
# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence optimization
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error no
rdbcompression yes
rdbchecksum yes

# Network optimization
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Performance optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# Lazy freeing
lazyfree-lazy-eviction no
lazyfree-lazy-expire no
lazyfree-lazy-server-del no
replica-lazy-flush no

# Threaded I/O
io-threads 4
io-threads-do-reads yes

# Security (minimal for internal use)
protected-mode yes
requirepass secure_redis_password
```

#### 1.2 Cache Strategy Implementation

```python
import redis
import json
import hashlib
import time
from typing import Any, Optional, Dict, Union
from functools import wraps

class OptimizedCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            password='secure_redis_password',
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=100,
            connection_pool_class=redis.ConnectionPool
        )
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'evictions': 0
        }
    
    def cache_result(
        self, 
        ttl: int = 3600,
        key_prefix: str = "cache:",
        include_params: bool = True
    ):
        """Decorator for caching function results"""
        
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(
                    func.__name__, 
                    args, 
                    kwargs, 
                    key_prefix,
                    include_params
                )
                
                # Try to get from cache
                try:
                    cached_result = await self._async_get(cache_key)
                    if cached_result is not None:
                        self.stats['hits'] += 1
                        return cached_result
                except Exception as e:
                    self.stats['errors'] += 1
                    # Continue with database query on cache error
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache the result
                try:
                    await self._async_setex(cache_key, ttl, result)
                    self.stats['misses'] += 1
                except Exception as e:
                    self.stats['errors'] += 1
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_cache_key(
                    func.__name__, 
                    args, 
                    kwargs, 
                    key_prefix,
                    include_params
                )
                
                # Try to get from cache
                try:
                    cached_result = self.redis_client.get(cache_key)
                    if cached_result:
                        self.stats['hits'] += 1
                        return json.loads(cached_result)
                except Exception as e:
                    self.stats['errors'] += 1
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Cache the result
                try:
                    self.redis_client.setex(
                        cache_key, 
                        ttl, 
                        json.dumps(result, default=str)
                    )
                    self.stats['misses'] += 1
                except Exception as e:
                    self.stats['errors'] += 1
                
                return result
            
            # Choose wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _generate_cache_key(
        self, 
        func_name: str, 
        args: tuple, 
        kwargs: dict, 
        prefix: str,
        include_params: bool
    ) -> str:
        """Generate a unique cache key"""
        
        if not include_params:
            return f"{prefix}{func_name}"
        
        # Create key components
        key_parts = [func_name]
        
        # Add positional args (limited to avoid overly long keys)
        for arg in args[:3]:  # Limit to first 3 args
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword args (limited)
        for key, value in list(kwargs.items())[:3]:  # Limit to first 3 kwargs
            if isinstance(value, (str, int, float)):
                key_parts.append(f"{key}:{value}")
            else:
                key_parts.append(f"{key}:{hashlib.md5(str(value).encode()).hexdigest()[:8]}")
        
        # Generate final key
        key_string = ":".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
        
        return f"{prefix}{func_name}:{key_hash}"
    
    async def _async_get(self, key: str) -> Optional[Any]:
        """Async get from cache"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.redis_client.get, 
            key
        )
    
    async def _async_setex(self, key: str, ttl: int, value: Any):
        """Async set with TTL"""
        loop = asyncio.get_event_loop()
        serialized_value = json.dumps(value, default=str)
        await loop.run_in_executor(
            None,
            self.redis_client.setex,
            key,
            ttl,
            serialized_value
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'memory_usage': self.redis_client.info('memory')['used_memory_human']
        }

# Global cache instance
cache = OptimizedCache()
```

### 2. Multi-Level Caching Strategy

```python
from typing import Dict, Any, Optional
import threading

class MultiLevelCache:
    """Multi-level caching: L1 (memory) -> L2 (Redis) -> L3 (Database)"""
    
    def __init__(self, redis_cache: OptimizedCache):
        self.redis_cache = redis_cache
        self.local_cache: Dict[str, tuple[Any, float]] = {}
        self.lock = threading.RLock()
        self.max_local_size = 1000
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        
        # L1: Check local memory cache
        with self.lock:
            if key in self.local_cache:
                value, expiry = self.local_cache[key]
                if time.time() < expiry:
                    return value
                else:
                    # Expired, remove from local cache
                    del self.local_cache[key]
        
        # L2: Check Redis cache
        try:
            redis_value = self.redis_cache.redis_client.get(key)
            if redis_value:
                value = json.loads(redis_value)
                
                # Store in L1 cache for faster access
                self._store_in_local_cache(key, value, 300)  # 5 min local TTL
                
                return value
        except Exception:
            pass  # Redis error, continue to database
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in multi-level cache"""
        
        # Store in Redis (L2)
        try:
            self.redis_cache.redis_client.setex(
                key, 
                ttl, 
                json.dumps(value, default=str)
            )
        except Exception:
            pass  # Redis error, still store in local cache
        
        # Store in local cache (L1)
        self._store_in_local_cache(key, value, min(ttl, 300))  # Max 5 min local TTL
    
    def _store_in_local_cache(self, key: str, value: Any, ttl: int):
        """Store in local memory cache with LRU eviction"""
        
        with self.lock:
            # If cache is full, remove oldest entry
            if len(self.local_cache) >= self.max_local_size:
                oldest_key = min(self.local_cache.keys(), 
                               key=lambda k: self.local_cache[k][1])
                del self.local_cache[oldest_key]
            
            # Store with expiry time
            expiry = time.time() + ttl
            self.local_cache[key] = (value, expiry)
    
    def invalidate(self, key: str):
        """Invalidate key from all cache levels"""
        
        # Remove from local cache
        with self.lock:
            self.local_cache.pop(key, None)
        
        # Remove from Redis
        try:
            self.redis_cache.redis_client.delete(key)
        except Exception:
            pass

# Global multi-level cache
multi_cache = MultiLevelCache(cache)
```

## Infrastructure Optimization

### 1. System-Level Tuning

#### 1.1 Kernel Parameters

**File**: `/etc/sysctl.d/99-threat-intel.conf`
```bash
# Network performance
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 128
net.ipv4.tcp_max_syn_backlog = 2048

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1

# File system
fs.file-max = 2097152
fs.nr_open = 1048576

# Security
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
```

#### 1.2 File Descriptor Limits

**File**: `/etc/security/limits.conf`
```
# Increase file descriptor limits
threat-intel soft nofile 65536
threat-intel hard nofile 65536
threat-intel soft nproc 32768
threat-intel hard nproc 32764

# PostgreSQL specific
postgres soft nofile 65536
postgres hard nofile 65536

# MongoDB specific  
mongod soft nofile 65536
mongod hard nofile 65536

# Redis specific
redis soft nofile 65536
redis hard nofile 65536
```

### 2. Docker Performance Optimization

#### 2.1 Docker Compose Configuration

**File**: `docker-compose.performance.yml`
```yaml
version: '3.8'

services:
  api:
    build: ./api
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    environment:
      - WORKERS=4
      - MAX_REQUESTS=1000
      - MAX_REQUESTS_JITTER=100
    volumes:
      - ./logs:/app/logs
    networks:
      - threat-intel
    depends_on:
      - postgres
      - mongodb
      - redis
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  postgres:
    image: postgres:15
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    command: >
      postgres 
      -c shared_buffers=1GB
      -c effective_cache_size=3GB
      -c work_mem=16MB
      -c maintenance_work_mem=256MB
      -c checkpoint_completion_target=0.9
      -c wal_buffers=32MB
      -c max_connections=200
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    command: redis-server /usr/local/etc/redis/redis.conf
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

  prometheus:
    image: prom/prometheus:latest
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=200h'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  threat-intel:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.1.0/24
```

## Benchmarking Procedures

### 1. API Benchmarking

#### 1.1 Load Testing Script

```python
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json

class APILoadTester:
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = None
    
    async def setup(self):
        """Setup HTTP session"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Threat-Intel-LoadTester/1.0'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None
    ) -> Dict[str, Any]:
        """Make a single API request"""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            start_time = time.time()
            
            async with self.session.request(
                method=method,
                url=url,
                json=data
            ) as response:
                
                end_time = time.time()
                response_time = end_time - start_time
                
                try:
                    response_data = await response.json()
                except:
                    response_data = {"text": await response.text()}
                
                return {
                    'status_code': response.status,
                    'response_time': response_time,
                    'success': 200 <= response.status < 300,
                    'data': response_data,
                    'error': None
                }
        
        except Exception as e:
            return {
                'status_code': 0,
                'response_time': time.time() - start_time,
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    async def benchmark_endpoint(
        self,
        endpoint: str,
        method: str = 'GET',
        data: Dict = None,
        concurrent_users: int = 10,
        requests_per_user: int = 100,
        ramp_up_time: int = 10
    ) -> Dict[str, Any]:
        """Benchmark an API endpoint with concurrent users"""
        
        print(f"Starting benchmark for {method} {endpoint}")
        print(f"Concurrent users: {concurrent_users}")
        print(f"Requests per user: {requests_per_user}")
        
        await self.setup()
        
        try:
            # Calculate requests per second for ramp up
            requests_total = concurrent_users * requests_per_user
            requests_per_second = requests_total / ramp_up_time if ramp_up_time > 0 else requests_total
            
            # Create user tasks
            user_tasks = []
            for user_id in range(concurrent_users):
                task = asyncio.create_task(
                    self._simulate_user(
                        endpoint=endpoint,
                        method=method,
                        data=data,
                        num_requests=requests_per_user,
                        user_delay=ramp_up_time / concurrent_users
                    )
                )
                user_tasks.append(task)
            
            # Wait for all users to complete
            start_time = time.time()
            results = await asyncio.gather(*user_tasks)
            total_time = time.time() - start_time
            
            # Aggregate results
            all_responses = []
            for user_results in results:
                all_responses.extend(user_results)
            
            # Calculate statistics
            stats = self._calculate_stats(all_responses)
            
            print(f"\nBenchmark completed in {total_time:.2f} seconds")
            print(f"Total requests: {len(all_responses)}")
            print(f"Requests per second: {len(all_responses) / total_time:.2f}")
            print(f"Success rate: {stats['success_rate']:.1%}")
            print(f"Average response time: {stats['avg_response_time']:.3f}s")
            print(f"P95 response time: {stats['p95_response_time']:.3f}s")
            print(f"P99 response time: {stats['p99_response_time']:.3f}s")
            print(f"Min response time: {stats['min_response_time']:.3f}s")
            print(f"Max response time: {stats['max_response_time']:.3f}s")
            
            return {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'requests_per_user': requests_per_user,
                'total_requests': len(all_responses),
                'total_time': total_time,
                'requests_per_second': len(all_responses) / total_time,
                'statistics': stats,
                'raw_results': all_responses
            }
        
        finally:
            await self.cleanup()
    
    async def _simulate_user(
        self,
        endpoint: str,
        method: str,
        data: Dict,
        num_requests: int,
        user_delay: float
    ) -> List[Dict[str, Any]]:
        """Simulate a single user's requests"""
        
        results = []
        
        # Ramp up delay
        await asyncio.sleep(user_delay)
        
        for i in range(num_requests):
            result = await self.make_request(method, endpoint, data)
            results.append(result)
            
            # Small delay between requests to avoid overwhelming
            if i < num_requests - 1:
                await asyncio.sleep(0.1)
        
        return results
    
    def _calculate_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance statistics"""
        
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        response_times = [r['response_time'] for r in results]
        
        return {
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(results) if results else 0,
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'median_response_time': statistics.median(response_times) if response_times else 0,
            'p95_response_time': statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else (max(response_times) if response_times else 0),
            'p99_response_time': statistics.quantiles(response_times, n=100)[98] if len(response_times) >= 100 else (max(response_times) if response_times else 0),
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'response_time_stdev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
            'status_codes': self._get_status_code_distribution(results),
            'errors': [r['error'] for r in failed_results if r['error']]
        }
    
    def _get_status_code_distribution(self, results: List[Dict[str, Any]]) -> Dict[int, int]:
        """Get distribution of status codes"""
        distribution = {}
        for result in results:
            code = result['status_code']
            distribution[code] = distribution.get(code, 0) + 1
        return distribution

# Usage example
async def run_benchmark():
    tester = APILoadTester("https://api.yourdomain.com", "your-api-key")
    
    # Benchmark health endpoint
    await tester.benchmark_endpoint(
        endpoint="/health",
        concurrent_users=50,
        requests_per_user=100,
        ramp_up_time=30
    )
    
    # Benchmark threat intelligence lookup
    await tester.benchmark_endpoint(
        endpoint="/threat-intelligence/lookup",
        method="POST",
        data={"indicator": "8.8.8.8", "type": "ip_address"},
        concurrent_users=20,
        requests_per_user=50,
        ramp_up_time=20
    )

if __name__ == "__main__":
    asyncio.run(run_benchmark())
```

### 2. Database Benchmarking

#### 2.1 PostgreSQL Benchmark Script

```python
import asyncio
import asyncpg
import time
import statistics
from typing import List, Dict, Any

class DatabaseBenchmark:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.pool = None
    
    async def setup(self):
        """Setup database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=10,
            max_size=50,
            command_timeout=60
        )
    
    async def cleanup(self):
        """Cleanup database connections"""
        if self.pool:
            await self.pool.close()
    
    async def benchmark_queries(self) -> Dict[str, Any]:
        """Run various database query benchmarks"""
        
        await self.setup()
        
        try:
            benchmarks = {
                'simple_select': self._benchmark_simple_select,
                'complex_join': self._benchmark_complex_join,
                'aggregate_query': self._benchmark_aggregate_query,
                'insert_performance': self._benchmark_inserts,
                'update_performance': self._benchmark_updates
            }
            
            results = {}
            for name, benchmark_func in benchmarks.items():
                print(f"Running {name} benchmark...")
                result = await benchmark_func()
                results[name] = result
                print(f"{name}: {result['avg_time']:.3f}ms average")
            
            return results
        
        finally:
            await self.cleanup()
    
    async def _benchmark_simple_select(self, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark simple SELECT queries"""
        
        query = "SELECT indicator_value, confidence_score FROM threat_intelligence WHERE indicator_type = $1 LIMIT 10"
        execution_times = []
        
        async with self.pool.acquire() as conn:
            for i in range(iterations):
                start_time = time.time()
                
                rows = await conn.fetch(query, 'ip_address')
                
                end_time = time.time()
                execution_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        return self._calculate_query_stats(execution_times, iterations)
    
    async def _benchmark_complex_join(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark complex JOIN queries"""
        
        query = """
        SELECT 
            ti.indicator_value,
            ti.confidence_score,
            ts.source_name,
            ri.reputation_score,
            COUNT(ti2.id) as related_threats
        FROM threat_intelligence ti
        JOIN threat_sources ts ON ti.source_id = ts.id
        LEFT JOIN reputation_intelligence ri ON ti.indicator_value = ri.indicator_value
        LEFT JOIN threat_intelligence ti2 ON ti.indicator_value = ti2.indicator_value 
            AND ti2.is_active = true
        WHERE ti.indicator_type = $1 
          AND ti.confidence_score > $2
          AND ti.is_active = true
        GROUP BY ti.id, ti.indicator_value, ti.confidence_score, ts.source_name, ri.reputation_score
        ORDER BY ti.confidence_score DESC
        LIMIT 100
        """
        
        execution_times = []
        
        async with self.pool.acquire() as conn:
            for i in range(iterations):
                start_time = time.time()
                
                rows = await conn.fetch(query, 'ip_address', 0.7)
                
                end_time = time.time()
                execution_times.append((end_time - start_time) * 1000)
        
        return self._calculate_query_stats(execution_times, iterations)
    
    async def _benchmark_aggregate_query(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark aggregate queries"""
        
        query = """
        SELECT 
            source_name,
            indicator_type,
            COUNT(*) as threat_count,
            AVG(confidence_score) as avg_confidence,
            MAX(created_at) as last_seen
        FROM threat_intelligence ti
        JOIN threat_sources ts ON ti.source_id = ts.id
        WHERE ti.created_at > NOW() - INTERVAL '30 days'
        GROUP BY source_name, indicator_type
        ORDER BY threat_count DESC
        """
        
        execution_times = []
        
        async with self.pool.acquire() as conn:
            for i in range(iterations):
                start_time = time.time()
                
                rows = await conn.fetch(query)
                
                end_time = time.time()
                execution_times.append((end_time - start_time) * 1000)
        
        return self._calculate_query_stats(execution_times, iterations)
    
    async def _benchmark_inserts(self, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark INSERT performance"""
        
        insert_query = """
        INSERT INTO threat_intelligence 
        (source_id, indicator_type, indicator_value, confidence_score, notes, is_active)
        VALUES ($1, $2, $3, $4, $5, true)
        ON CONFLICT (source_id, indicator_type, indicator_value) 
        DO UPDATE SET 
            confidence_score = EXCLUDED.confidence_score,
            notes = EXCLUDED.notes,
            updated_at = NOW()
        """
        
        execution_times = []
        
        # Get a valid source_id
        async with self.pool.acquire() as conn:
            source_row = await conn.fetchrow("SELECT id FROM threat_sources LIMIT 1")
            if not source_row:
                raise Exception("No threat sources found")
            
            source_id = source_row['id']
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(iterations):
                    start_time = time.time()
                    
                    await conn.execute(
                        insert_query,
                        source_id,
                        'ip_address',
                        f'192.168.1.{i % 255}',
                        0.5 + (i % 50) / 100,
                        f'Test threat {i}'
                    )
                    
                    end_time = time.time()
                    execution_times.append((end_time - start_time) * 1000)
        
        return self._calculate_query_stats(execution_times, iterations)
    
    async def _benchmark_updates(self, iterations: int = 500) -> Dict[str, Any]:
        """Benchmark UPDATE performance"""
        
        update_query = """
        UPDATE threat_intelligence 
        SET confidence_score = confidence_score + 0.1,
            last_seen = NOW(),
            updated_at = NOW()
        WHERE indicator_type = $1 
          AND confidence_score < $2
        """
        
        execution_times = []
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for i in range(iterations):
                    start_time = time.time()
                    
                    result = await conn.execute(
                        update_query,
                        'ip_address',
                        0.9 - (i % 10) * 0.01
                    )
                    
                    end_time = time.time()
                    execution_times.append((end_time - start_time) * 1000)
        
        return self._calculate_query_stats(execution_times, iterations)
    
    def _calculate_query_stats(
        self, 
        execution_times: List[float], 
        iterations: int
    ) -> Dict[str, Any]:
        """Calculate query performance statistics"""
        
        return {
            'iterations': iterations,
            'avg_time': statistics.mean(execution_times),
            'median_time': statistics.median(execution_times),
            'min_time': min(execution_times),
            'max_time': max(execution_times),
            'p95_time': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) >= 20 else max(execution_times),
            'p99_time': statistics.quantiles(execution_times, n=100)[98] if len(execution_times) >= 100 else max(execution_times),
            'std_dev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'total_time': sum(execution_times),
            'queries_per_second': iterations / sum(execution_times) if execution_times else 0
        }
```

## Performance Testing

### 1. Continuous Performance Testing

#### 1.1 Performance Test Suite

```python
import asyncio
import pytest
import time
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PerformanceTestResult:
    test_name: str
    target_response_time: float
    actual_response_time: float
    success: bool
    message: str

class PerformanceTestSuite:
    def __init__(self, api_base_url: str, db_connection_string: str):
        self.api_base_url = api_base_url
        self.db_connection_string = db_connection_string
        self.results: List[PerformanceTestResult] = []
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        
        print("Starting Performance Test Suite")
        print("=" * 50)
        
        # API Tests
        await self.test_api_health()
        await self.test_api_threat_lookup()
        await self.test_api_reputation_lookup()
        await self.test_api_email_analysis()
        await self.test_api_url_analysis()
        
        # Database Tests
        await self.test_db_query_performance()
        await self.test_db_connection_pool()
        await self.test_db_complex_queries()
        
        # Cache Tests
        await self.test_cache_performance()
        await self.test_cache_hit_rate()
        
        # Generate report
        return self.generate_report()
    
    async def test_api_health(self):
        """Test API health endpoint response time"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            
            async with session.get(f"{self.api_base_url}/health") as response:
                await response.json()
                
                response_time = time.time() - start_time
                
                test_result = PerformanceTestResult(
                    test_name="API Health Check",
                    target_response_time=0.1,  # 100ms
                    actual_response_time=response_time,
                    success=response_time < 0.1,
                    message=f"Response time: {response_time:.3f}s"
                )
                
                self.results.append(test_result)
                print(f"✓ API Health: {response_time:.3f}s")
    
    async def test_api_threat_lookup(self):
        """Test threat intelligence lookup performance"""
        import aiohttp
        
        test_cases = [
            {"indicator": "8.8.8.8", "type": "ip_address"},
            {"indicator": "example.com", "type": "domain"},
            {"indicator": "test@example.com", "type": "email"}
        ]
        
        async with aiohttp.ClientSession() as session:
            for test_case in test_cases:
                start_time = time.time()
                
                async with session.post(
                    f"{self.api_base_url}/threat-intelligence/lookup",
                    json=test_case
                ) as response:
                    await response.json()
                    
                    response_time = time.time() - start_time
                    
                    test_result = PerformanceTestResult(
                        test_name=f"Threat Lookup - {test_case['type']}",
                        target_response_time=0.5,  # 500ms
                        actual_response_time=response_time,
                        success=response_time < 0.5,
                        message=f"{test_case['type']}: {response_time:.3f}s"
                    )
                    
                    self.results.append(test_result)
                    print(f"✓ Threat Lookup ({test_case['type']}): {response_time:.3f}s")
    
    async def test_db_query_performance(self):
        """Test database query performance"""
        import asyncpg
        
        # Test simple query performance
        query = "SELECT COUNT(*) FROM threat_intelligence WHERE is_active = true"
        
        execution_times = []
        
        async with asyncpg.create_pool(self.db_connection_string) as pool:
            async with pool.acquire() as conn:
                for _ in range(10):
                    start_time = time.time()
                    await conn.fetchval(query)
                    execution_times.append(time.time() - start_time)
        
        avg_time = sum(execution_times) / len(execution_times)
        
        test_result = PerformanceTestResult(
            test_name="Database Simple Query",
            target_response_time=0.1,  # 100ms
            actual_response_time=avg_time,
            success=avg_time < 0.1,
            message=f"Average time: {avg_time:.3f}s"
        )
        
        self.results.append(test_result)
        print(f"✓ DB Simple Query: {avg_time:.3f}s")
    
    async def test_cache_performance(self):
        """Test cache performance"""
        import redis
        
        redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test cache write/read performance
        test_data = {"test": "data", "number": 12345, "list": list(range(100))}
        
        # Test write performance
        write_times = []
        for i in range(100):
            start_time = time.time()
            redis_client.set(f"test_key_{i}", str(test_data))
            write_times.append(time.time() - start_time)
        
        avg_write_time = sum(write_times) / len(write_times)
        
        # Test read performance
        read_times = []
        for i in range(100):
            start_time = time.time()
            redis_client.get(f"test_key_{i}")
            read_times.append(time.time() - start_time)
        
        avg_read_time = sum(read_times) / len(read_times)
        
        # Cleanup
        for i in range(100):
            redis_client.delete(f"test_key_{i}")
        
        write_result = PerformanceTestResult(
            test_name="Cache Write Performance",
            target_response_time=0.001,  # 1ms
            actual_response_time=avg_write_time,
            success=avg_write_time < 0.001,
            message=f"Average write time: {avg_write_time:.6f}s"
        )
        
        read_result = PerformanceTestResult(
            test_name="Cache Read Performance",
            target_response_time=0.001,  # 1ms
            actual_response_time=avg_read_time,
            success=avg_read_time < 0.001,
            message=f"Average read time: {avg_read_time:.6f}s"
        )
        
        self.results.extend([write_result, read_result])
        print(f"✓ Cache Write: {avg_write_time:.6f}s, Read: {avg_read_time:.6f}s")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate performance test report"""
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        avg_response_time = sum(r.actual_response_time for r in self.results) / total_tests
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'average_response_time': avg_response_time
            },
            'tests': [
                {
                    'name': r.test_name,
                    'target_time': r.target_response_time,
                    'actual_time': r.actual_response_time,
                    'success': r.success,
                    'message': r.message
                } for r in self.results
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        
        recommendations = []
        
        # Analyze failed tests
        failed_tests = [r for r in self.results if not r.success]
        
        for test in failed_tests:
            if "API" in test.test_name and test.actual_response_time > test.target_response_time * 2:
                recommendations.append(
                    f"API performance issue detected in {test.test_name}. "
                    "Consider optimizing database queries or adding caching."
                )
            
            elif "Database" in test.test_name:
                recommendations.append(
                    f"Database performance issue in {test.test_name}. "
                    "Consider adding indexes or optimizing query structure."
                )
            
            elif "Cache" in test.test_name:
                recommendations.append(
                    f"Cache performance issue in {test.test_name}. "
                    "Consider Redis configuration optimization or memory allocation."
                )
        
        return recommendations

# Usage example
async def run_performance_tests():
    tester = PerformanceTestSuite(
        api_base_url="https://api.yourdomain.com",
        db_connection_string="postgresql://user:password@localhost/threatintel"
    )
    
    report = await tester.run_all_tests()
    
    print("\n" + "=" * 50)
    print("PERFORMANCE TEST REPORT")
    print("=" * 50)
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Average Response Time: {report['summary']['average_response_time']:.3f}s")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"• {rec}")
    
    # Save report
    import json
    with open(f"performance_report_{int(time.time())}.json", "w") as f:
        json.dump(report, f, indent=2)
```

---

For operational procedures, see the [Operational Runbook](../operations/operational-runbook.md).

For troubleshooting assistance, see the [Troubleshooting Guide](../troubleshooting/troubleshooting-guide.md).

For security considerations, see the [Security Considerations](../security/security-considerations.md).
