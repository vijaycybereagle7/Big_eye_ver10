#!/usr/bin/env python3
"""
Redis Caching Implementation for Performance Optimization
5-Level Caching Strategy Implementation

This module implements a comprehensive Redis caching system with 5 levels:
1. API Responses Cache
2. Reputation Scores Cache  
3. Blacklist Results Cache
4. ML Predictions Cache
5. Aggregated Statistics Cache
"""

import redis
import json
import pickle
import logging
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import asyncio
import aioredis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceCache:
    """
    High-performance Redis caching implementation with 5 caching levels
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", **kwargs):
        """Initialize Redis connection with optional connection pool settings"""
        self.redis_url = redis_url
        self.redis_client = redis.from_url(redis_url, **kwargs)
        self.pipeline = self.redis_client.pipeline()
        
        # Cache TTL configurations (in seconds)
        self.ttl_config = {
            'api_response': 300,           # 5 minutes
            'reputation_score': 3600,     # 1 hour
            'blacklist_result': 86400,    # 24 hours
            'ml_prediction': 1800,        # 30 minutes
            'aggregated_stats': 3600,     # 1 hour
        }
    
    def _generate_cache_key(self, prefix: str, identifier: Union[str, int]) -> str:
        """Generate cache key with prefix"""
        return f"{prefix}:{identifier}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for Redis storage"""
        if isinstance(data, (str, int, float)):
            return json.dumps(data)
        return pickle.dumps(data).hex()
    
    def _deserialize_data(self, data: str, is_pickled: bool = False) -> Any:
        """Deserialize data from Redis storage"""
        try:
            if is_pickled:
                return pickle.loads(bytes.fromhex(data))
            return json.loads(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to deserialize data: {e}")
            return None


# Level 1: API Responses Cache
class APIResponseCache:
    """Cache API responses for improved performance"""
    
    def __init__(self, cache: PerformanceCache):
        self.cache = cache
        self.prefix = "api"
    
    def set_api_response(self, endpoint: str, params: Dict, version: str, 
                        response: Any, ttl: Optional[int] = None) -> bool:
        """Cache API response with endpoint and parameters"""
        key = self._generate_api_key(endpoint, params, version)
        serialized_response = self.cache._serialize_data(response)
        ttl = ttl or self.cache.ttl_config['api_response']
        
        try:
            return self.cache.redis_client.setex(key, ttl, serialized_response)
        except redis.RedisError as e:
            logger.error(f"Failed to cache API response: {e}")
            return False
    
    def get_api_response(self, endpoint: str, params: Dict, version: str) -> Optional[Any]:
        """Retrieve cached API response"""
        key = self._generate_api_key(endpoint, params, version)
        
        try:
            cached_data = self.cache.redis_client.get(key)
            if cached_data:
                return self.cache._deserialize_data(cached_data.decode())
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to retrieve API response: {e}")
            return None
    
    def invalidate_api_cache(self, pattern: str = "*") -> int:
        """Invalidate API cache by pattern"""
        try:
            keys = self.cache.redis_client.keys(f"{self.prefix}:{pattern}")
            if keys:
                return self.cache.redis_client.delete(*keys)
            return 0
        except redis.RedisError as e:
            logger.error(f"Failed to invalidate API cache: {e}")
            return 0
    
    def _generate_api_key(self, endpoint: str, params: Dict, version: str) -> str:
        """Generate unique API cache key"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{self.prefix}:{endpoint}:{params_hash}:{version}"


# Level 2: Reputation Scores Cache
class ReputationScoreCache:
    """Cache user reputation scores"""
    
    def __init__(self, cache: PerformanceCache):
        self.cache = cache
        self.prefix = "reputation"
    
    def set_reputation_score(self, user_id: str, score: float, 
                           confidence: float, metadata: Optional[Dict] = None) -> bool:
        """Cache user reputation score with metadata"""
        key = self._generate_reputation_key(user_id)
        reputation_data = {
            'score': score,
            'confidence': confidence,
            'last_updated': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        serialized_data = self.cache._serialize_data(reputation_data)
        ttl = self.cache.ttl_config['reputation_score']
        
        try:
            return self.cache.redis_client.setex(key, ttl, serialized_data)
        except redis.RedisError as e:
            logger.error(f"Failed to cache reputation score: {e}")
            return False
    
    def get_reputation_score(self, user_id: str) -> Optional[Dict]:
        """Retrieve cached reputation score"""
        key = self._generate_reputation_key(user_id)
        
        try:
            cached_data = self.cache.redis_client.get(key)
            if cached_data:
                return self.cache._deserialize_data(cached_data.decode())
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to retrieve reputation score: {e}")
            return None
    
    def set_batch_reputation_scores(self, scores: List[Dict]) -> int:
        """Cache multiple reputation scores in batch"""
        pipeline = self.cache.redis_client.pipeline()
        success_count = 0
        
        for score_data in scores:
            user_id = score_data['user_id']
            key = self._generate_reputation_key(user_id)
            serialized_data = self.cache._serialize_data(score_data)
            ttl = self.cache.ttl_config['reputation_score']
            
            pipeline.setex(key, ttl, serialized_data)
        
        try:
            results = pipeline.execute()
            success_count = sum(1 for result in results if result)
            logger.info(f"Batch cached {success_count} reputation scores")
            return success_count
        except redis.RedisError as e:
            logger.error(f"Failed to batch cache reputation scores: {e}")
            return 0
    
    def _generate_reputation_key(self, user_id: str) -> str:
        """Generate reputation cache key"""
        return f"{self.prefix}:user:{user_id}"


# Level 3: Blacklist Results Cache
class BlacklistCache:
    """Cache blacklist check results"""
    
    def __init__(self, cache: PerformanceCache):
        self.cache = cache
        self.prefix = "blacklist"
    
    def set_blacklist_result(self, identifier_type: str, identifier: str, 
                           result: str, reason: str = "", ttl: Optional[int] = None) -> bool:
        """Cache blacklist check result"""
        key = self._generate_blacklist_key(identifier_type, identifier)
        blacklist_data = {
            'result': result,
            'reason': reason,
            'checked_at': datetime.now().isoformat(),
            'valid_until': (datetime.now() + timedelta(seconds=ttl or self.cache.ttl_config['blacklist_result'])).isoformat()
        }
        
        serialized_data = self.cache._serialize_data(blacklist_data)
        ttl = ttl or self.cache.ttl_config['blacklist_result']
        
        try:
            return self.cache.redis_client.setex(key, ttl, serialized_data)
        except redis.RedisError as e:
            logger.error(f"Failed to cache blacklist result: {e}")
            return False
    
    def get_blacklist_result(self, identifier_type: str, identifier: str) -> Optional[Dict]:
        """Retrieve cached blacklist result"""
        key = self._generate_blacklist_key(identifier_type, identifier)
        
        try:
            cached_data = self.cache.redis_client.get(key)
            if cached_data:
                return self.cache._deserialize_data(cached_data.decode())
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to retrieve blacklist result: {e}")
            return None
    
    def batch_check_blacklist(self, checks: List[Dict]) -> Dict[str, Dict]:
        """Batch check multiple identifiers against blacklist"""
        pipeline = self.cache.redis_client.pipeline()
        results = {}
        
        # Queue all gets
        for check in checks:
            identifier_type = check['type']
            identifier = check['value']
            key = self._generate_blacklist_key(identifier_type, identifier)
            pipeline.get(key)
        
        try:
            cached_results = pipeline.execute()
            
            for i, check in enumerate(checks):
                identifier_type = check['type']
                identifier = check['value']
                key = self._generate_blacklist_key(identifier_type, identifier)
                
                if cached_results[i]:
                    results[key] = self.cache._deserialize_data(cached_results[i].decode())
                else:
                    results[key] = None
                    
        except redis.RedisError as e:
            logger.error(f"Failed to batch check blacklist: {e}")
        
        return results
    
    def _generate_blacklist_key(self, identifier_type: str, identifier: str) -> str:
        """Generate blacklist cache key"""
        return f"{self.prefix}:{identifier_type}:{identifier}"


# Level 4: ML Predictions Cache
class MLPredictionCache:
    """Cache machine learning model predictions"""
    
    def __init__(self, cache: PerformanceCache):
        self.cache = cache
        self.prefix = "ml"
    
    def set_ml_prediction(self, model_name: str, feature_hash: str, 
                         prediction: Dict, ttl: Optional[int] = None) -> bool:
        """Cache ML model prediction"""
        key = self._generate_prediction_key(model_name, feature_hash)
        prediction_data = {
            'prediction': prediction,
            'model_version': prediction.get('model_version', 'unknown'),
            'confidence': prediction.get('confidence', 0.0),
            'generated_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(seconds=ttl or self.cache.ttl_config['ml_prediction'])).isoformat()
        }
        
        serialized_data = self.cache._serialize_data(prediction_data)
        ttl = ttl or self.cache.ttl_config['ml_prediction']
        
        try:
            return self.cache.redis_client.setex(key, ttl, serialized_data)
        except redis.RedisError as e:
            logger.error(f"Failed to cache ML prediction: {e}")
            return False
    
    def get_ml_prediction(self, model_name: str, feature_hash: str) -> Optional[Dict]:
        """Retrieve cached ML prediction"""
        key = self._generate_prediction_key(model_name, feature_hash)
        
        try:
            cached_data = self.cache.redis_client.get(key)
            if cached_data:
                return self.cache._deserialize_data(cached_data.decode())
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to retrieve ML prediction: {e}")
            return None
    
    def warmup_cache(self, model_name: str, features: List[Dict]) -> int:
        """Warm up cache with ML predictions for common features"""
        warmed_count = 0
        
        for features_dict in features:
            feature_hash = self._hash_features(features_dict)
            prediction = self._generate_mock_prediction(features_dict)  # Replace with actual model
            
            if self.set_ml_prediction(model_name, feature_hash, prediction):
                warmed_count += 1
        
        logger.info(f"Warmed up cache with {warmed_count} predictions for {model_name}")
        return warmed_count
    
    def _generate_prediction_key(self, model_name: str, feature_hash: str) -> str:
        """Generate ML prediction cache key"""
        return f"{self.prefix}:{model_name}:{feature_hash}"
    
    def _hash_features(self, features: Dict) -> str:
        """Generate hash for features"""
        features_str = json.dumps(features, sort_keys=True)
        return hashlib.md5(features_str.encode()).hexdigest()[:12]
    
    def _generate_mock_prediction(self, features: Dict) -> Dict:
        """Generate mock prediction (replace with actual model call)"""
        return {
            'score': 0.75,
            'confidence': 0.92,
            'model_version': 'v2.1',
            'prediction_type': 'classification',
            'features_used': list(features.keys())
        }


# Level 5: Aggregated Statistics Cache
class AggregatedStatsCache:
    """Cache aggregated analytics and statistics"""
    
    def __init__(self, cache: PerformanceCache):
        self.cache = cache
        self.prefix = "stats"
    
    def set_daily_stats(self, metric: str, date: str, stats: Dict, 
                       ttl: Optional[int] = None) -> bool:
        """Cache daily aggregated statistics"""
        key = self._generate_stats_key(metric, "daily", date)
        stats_data = {
            'stats': stats,
            'calculated_at': datetime.now().isoformat(),
            'date': date,
            'period': 'daily'
        }
        
        serialized_data = self.cache._serialize_data(stats_data)
        ttl = ttl or self.cache.ttl_config['aggregated_stats']
        
        try:
            return self.cache.redis_client.setex(key, ttl, serialized_data)
        except redis.RedisError as e:
            logger.error(f"Failed to cache daily stats: {e}")
            return False
    
    def get_daily_stats(self, metric: str, date: str) -> Optional[Dict]:
        """Retrieve cached daily statistics"""
        key = self._generate_stats_key(metric, "daily", date)
        
        try:
            cached_data = self.cache.redis_client.get(key)
            if cached_data:
                return self.cache._deserialize_data(cached_data.decode())
            return None
        except redis.RedisError as e:
            logger.error(f"Failed to retrieve daily stats: {e}")
            return None
    
    def increment_realtime_counter(self, metric: str, increment: int = 1) -> int:
        """Increment real-time counter"""
        key = f"{self.prefix}:{metric}:realtime"
        
        try:
            return self.cache.redis_client.incrby(key, increment)
        except redis.RedisError as e:
            logger.error(f"Failed to increment real-time counter: {e}")
            return 0
    
    def get_realtime_counter(self, metric: str) -> int:
        """Get real-time counter value"""
        key = f"{self.prefix}:{metric}:realtime"
        
        try:
            value = self.cache.redis_client.get(key)
            return int(value) if value else 0
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Failed to get real-time counter: {e}")
            return 0
    
    def set_complex_stats(self, stat_type: str, period: str, data: Dict) -> bool:
        """Cache complex statistical aggregations"""
        key = f"{self.prefix}:{stat_type}:{period}:complex"
        
        try:
            serialized_data = self.cache._serialize_data(data)
            return self.cache.redis_client.setex(key, self.cache.ttl_config['aggregated_stats'], serialized_data)
        except redis.RedisError as e:
            logger.error(f"Failed to cache complex stats: {e}")
            return False
    
    def _generate_stats_key(self, metric: str, period: str, identifier: str) -> str:
        """Generate statistics cache key"""
        return f"{self.prefix}:{metric}:{period}:{identifier}"


# Main caching orchestrator
class MultiLevelCache:
    """Orchestrates all 5 caching levels"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", **kwargs):
        self.redis_cache = PerformanceCache(redis_url, **kwargs)
        self.api_cache = APIResponseCache(self.redis_cache)
        self.reputation_cache = ReputationScoreCache(self.redis_cache)
        self.blacklist_cache = BlacklistCache(self.redis_cache)
        self.ml_cache = MLPredictionCache(self.redis_cache)
        self.stats_cache = AggregatedStatsCache(self.redis_cache)
    
    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        stats = {}
        
        try:
            info = self.redis_cache.redis_client.info()
            stats.update({
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0)
            })
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            total = hits + misses
            stats['hit_rate'] = round((hits / total * 100), 2) if total > 0 else 0
            
        except redis.RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
        
        return stats
    
    def clear_all_cache(self) -> bool:
        """Clear all cached data (use with caution)"""
        try:
            return bool(self.redis_cache.redis_client.flushall())
        except redis.RedisError as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def cache_warming_service(self) -> Dict[str, int]:
        """Warm up all caches with essential data"""
        results = {}
        
        # Warm up reputation cache for active users
        active_users = []  # Fetch from database
        if active_users:
            reputation_scores = [{'user_id': user['id'], 'score': 85.0, 'confidence': 0.9} 
                               for user in active_users[:100]]
            results['reputation'] = self.reputation_cache.set_batch_reputation_scores(reputation_scores)
        
        # Warm up ML cache for common patterns
        common_features = [{'feature1': 0.5, 'feature2': 1.0}]  # Fetch from analytics
        results['ml_predictions'] = self.ml_cache.warmup_cache('fraud_detector', common_features)
        
        # Warm up statistics cache
        today_stats = {'total_users': 1250, 'active_sessions': 89}
        self.stats_cache.set_daily_stats('users', datetime.now().strftime('%Y-%m-%d'), today_stats)
        results['daily_stats'] = 1
        
        return results


# Decorator for automatic caching
def cached_api_response(ttl: int = 300):
    """Decorator to automatically cache API responses"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Implementation would extract cache key from function call
            # and check cache before executing function
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    # Initialize multi-level cache
    cache = MultiLevelCache()
    
    # Test API Response Cache
    print("Testing API Response Cache...")
    endpoint = "/users/profile"
    params = {"user_id": "123", "include": ["profile", "activity"]}
    version = "v1"
    response = {"user": {"id": "123", "name": "John Doe"}, "activity": []}
    
    # Set cache
    success = cache.api_cache.set_api_response(endpoint, params, version, response)
    print(f"API response cached: {success}")
    
    # Get cache
    cached_response = cache.api_cache.get_api_response(endpoint, params, version)
    print(f"Cached response: {cached_response}")
    
    # Test Reputation Score Cache
    print("\nTesting Reputation Score Cache...")
    reputation = cache.reputation_cache.set_reputation_score(
        user_id="123", 
        score=92.5, 
        confidence=0.95,
        metadata={"source": "credit_score", "last_check": "2023-10-30"}
    )
    print(f"Reputation cached: {reputation}")
    
    retrieved_reputation = cache.reputation_cache.get_reputation_score("123")
    print(f"Retrieved reputation: {retrieved_reputation}")
    
    # Test Blacklist Cache
    print("\nTesting Blacklist Cache...")
    blacklist_result = cache.blacklist_cache.set_blacklist_result(
        identifier_type="email",
        identifier="test@example.com",
        result="blocked",
        reason="Disposable email provider"
    )
    print(f"Blacklist cached: {blacklist_result}")
    
    retrieved_blacklist = cache.blacklist_cache.get_blacklist_result("email", "test@example.com")
    print(f"Retrieved blacklist: {retrieved_blacklist}")
    
    # Test ML Prediction Cache
    print("\nTesting ML Prediction Cache...")
    features = {"amount": 100.0, "frequency": 5, "recency": 30}
    feature_hash = cache.ml_cache._hash_features(features)
    
    ml_prediction = cache.ml_cache.set_ml_prediction(
        model_name="fraud_detector",
        feature_hash=feature_hash,
        prediction={
            "fraud_probability": 0.23,
            "confidence": 0.89,
            "model_version": "v2.1"
        }
    )
    print(f"ML prediction cached: {ml_prediction}")
    
    retrieved_prediction = cache.ml_cache.get_ml_prediction("fraud_detector", feature_hash)
    print(f"Retrieved ML prediction: {retrieved_prediction}")
    
    # Test Aggregated Stats Cache
    print("\nTesting Aggregated Stats Cache...")
    daily_stats = {
        "total_users": 1250,
        "new_signups": 45,
        "active_sessions": 89,
        "avg_session_duration": 1245.5
    }
    
    stats_cached = cache.stats_cache.set_daily_stats(
        metric="users",
        date=datetime.now().strftime('%Y-%m-%d'),
        stats=daily_stats
    )
    print(f"Daily stats cached: {stats_cached}")
    
    retrieved_stats = cache.stats_cache.get_daily_stats("users", datetime.now().strftime('%Y-%m-%d'))
    print(f"Retrieved daily stats: {retrieved_stats}")
    
    # Test real-time counters
    print("\nTesting Real-time Counters...")
    cache.stats_cache.increment_realtime_counter("active_users", 1)
    cache.stats_cache.increment_realtime_counter("current_sessions", 5)
    
    active_users = cache.stats_cache.get_realtime_counter("active_users")
    current_sessions = cache.stats_cache.get_realtime_counter("current_sessions")
    
    print(f"Active users: {active_users}")
    print(f"Current sessions: {current_sessions}")
    
    # Get cache statistics
    print("\nCache Statistics:")
    cache_stats = cache.get_cache_stats()
    for key, value in cache_stats.items():
        print(f"  {key}: {value}")
    
    # Test cache warming
    print("\nCache Warming Service:")
    warmup_results = cache.cache_warming_service()
    for cache_type, count in warmup_results.items():
        print(f"  {cache_type}: {count} items warmed")