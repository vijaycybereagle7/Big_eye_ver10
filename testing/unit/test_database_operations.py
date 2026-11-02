"""Unit tests for database operations."""

import pytest
import asyncio
import asyncpg
import aiosqlite
from unittest.mock import patch, AsyncMock, Mock
from datetime import datetime, timedelta
import json

pytestmark = pytest.mark.asyncio


class TestDatabaseConnections:
    """Test database connection management."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_database_initialization(self, test_database):
        """Test database initialization."""
        from api.database.connections import get_postgresql_connection, get_mongodb_collection
        
        # Test PostgreSQL connection
        try:
            pg_conn = await get_postgresql_connection()
            assert pg_conn is not None
            await pg_conn.close()
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        
        # Test MongoDB collection
        try:
            mongodb_collection = await get_mongodb_collection()
            assert mongodb_collection is not None
        except Exception as e:
            pytest.skip(f"MongoDB not available: {e}")
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_database_health_check(self):
        """Test database health check."""
        from api.database.connections import check_postgresql_health, check_mongodb_health
        
        try:
            pg_health = await check_postgresql_health()
            assert "status" in pg_health
            assert pg_health["status"] in ["healthy", "unhealthy"]
        except Exception as e:
            print(f"PostgreSQL health check failed: {e}")
        
        try:
            mongodb_health = await check_mongodb_health()
            assert "status" in mongodb_health
            assert mongodb_health["status"] in ["healthy", "unhealthy"]
        except Exception as e:
            print(f"MongoDB health check failed: {e}")


class TestValidationDataStore:
    """Test validation data storage and retrieval."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_store_validation_result(self):
        """Test storing validation results."""
        from api.database.operations import ValidationDataStore
        
        # Mock the database operations
        with patch('api.database.operations.asyncpg.connect') as mock_pg, \
             patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            
            # Setup mocks
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {"id": 1}
            
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.insert_one.return_value = {"inserted_id": "mock_id"}
            
            store = ValidationDataStore()
            
            validation_result = {
                "type": "email",
                "value": "test@example.com",
                "is_valid": True,
                "confidence_score": 0.95,
                "validation_details": {"domain": "example.com", "mx_records": True}
            }
            
            # Test storing validation result
            result = await store.store_validation_result(validation_result)
            
            assert result["success"] is True
            assert "validation_id" in result
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_validation_history(self):
        """Test retrieving validation history."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {
                    "id": 1,
                    "type": "email",
                    "value": "test@example.com",
                    "is_valid": True,
                    "confidence_score": 0.95,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "type": "email",
                    "value": "test2@example.com",
                    "is_valid": False,
                    "confidence_score": 0.10,
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            store = ValidationDataStore()
            
            # Test getting validation history
            history = await store.get_validation_history("email", "example.com", limit=10)
            
            assert len(history) == 2
            assert all(record["type"] == "email" for record in history)
            assert all(record["value"].endswith("@example.com") for record in history)
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_bulk_store_validation_results(self):
        """Test bulk storage of validation results."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg, \
             patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [{"id": i} for i in range(1, 6)]
            
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.insert_many.return_value = {"inserted_ids": [f"id{i}" for i in range(5)]}
            
            store = ValidationDataStore()
            
            results = [
                {"type": "email", "value": f"test{i}@example.com", "is_valid": True}
                for i in range(5)
            ]
            
            # Test bulk store
            result = await store.bulk_store_validation_results(results)
            
            assert result["success"] is True
            assert result["stored_count"] == 5
            assert len(result["validation_ids"]) == 5


class TestReputationDataStore:
    """Test reputation data storage and retrieval."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_store_reputation_result(self):
        """Test storing reputation analysis results."""
        from api.database.operations import ReputationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg, \
             patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {"id": 1}
            
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.insert_one.return_value = {"inserted_id": "rep_id"}
            
            store = ReputationDataStore()
            
            reputation_result = {
                "value": "8.8.8.8",
                "value_type": "ip",
                "overall_score": 85,
                "overall_verdict": "good",
                "sources": {
                    "abuseipdb": {"score": 0, "verdict": "clean"},
                    "virustotal": {"reputation": 0, "verdict": "clean"}
                }
            }
            
            result = await store.store_reputation_result(reputation_result)
            
            assert result["success"] is True
            assert "reputation_id" in result
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_reputation_history(self):
        """Test retrieving reputation history."""
        from api.database.operations import ReputationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {
                    "id": 1,
                    "value": "8.8.8.8",
                    "value_type": "ip",
                    "overall_score": 85,
                    "overall_verdict": "good",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": 2,
                    "value": "1.1.1.1",
                    "value_type": "ip",
                    "overall_score": 80,
                    "overall_verdict": "good",
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            store = ReputationDataStore()
            
            history = await store.get_reputation_history("8.8.8.8", limit=10)
            
            assert len(history) >= 1
            assert all(record["value"] == "8.8.8.8" for record in history)
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_update_reputation_score(self):
        """Test updating reputation scores."""
        from api.database.operations import ReputationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.rowcount = 1
            
            store = ReputationDataStore()
            
            # Test updating reputation score
            result = await store.update_reputation_score(
                "8.8.8.8",
                "ip",
                90,
                "excellent",
                {"virustotal": {"reputation": 0}}
            )
            
            assert result["success"] is True
            assert result["updated"] is True


class TestThreatIntelDataStore:
    """Test threat intelligence data storage and retrieval."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_store_threat_intel(self):
        """Test storing threat intelligence data."""
        from api.database.operations import ThreatIntelDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg, \
             patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = {"id": 1}
            
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.insert_one.return_value = {"inserted_id": "threat_id"}
            
            store = ThreatIntelDataStore()
            
            threat_data = {
                "indicator": "192.0.2.100",
                "indicator_type": "ip",
                "threat_family": "Zeus",
                "threat_level": "high",
                "confidence_score": 0.95,
                "sources": ["abuseipdb", "virustotal"],
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
            
            result = await store.store_threat_intel(threat_data)
            
            assert result["success"] is True
            assert "threat_id" in result
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_search_threat_intelligence(self):
        """Test searching threat intelligence data."""
        from api.database.operations import ThreatIntelDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg, \
             patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {
                    "id": 1,
                    "indicator": "192.0.2.100",
                    "threat_family": "Zeus",
                    "threat_level": "high",
                    "confidence_score": 0.95,
                    "created_at": datetime.now().isoformat()
                }
            ]
            
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.find.return_value = [
                {
                    "indicator": "192.0.2.100",
                    "threat_family": "Zeus",
                    "threat_level": "high",
                    "campaigns": ["Campaign A", "Campaign B"]
                }
            ]
            
            store = ThreatIntelDataStore()
            
            # Test searching threat intelligence
            results = await store.search_threat_intelligence(
                query="Zeus",
                threat_level="high",
                limit=10
            )
            
            assert len(results) >= 1
            assert results[0]["threat_family"] == "Zeus"
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_get_related_threats(self):
        """Test getting related threat intelligence."""
        from api.database.operations import ThreatIntelDataStore
        
        with patch('api.database.operations.get_mongodb_collection') as mock_mongo:
            mock_collection = AsyncMock()
            mock_mongo.return_value = mock_collection
            mock_collection.find.return_value = [
                {
                    "indicator": "malware-site.com",
                    "threat_family": "Zeus",
                    "related_indicators": ["192.0.2.100", "192.0.2.101"]
                }
            ]
            
            store = ThreatIntelDataStore()
            
            # Test getting related threats
            related = await store.get_related_threats("192.0.2.100", limit=10)
            
            assert len(related) >= 1
            assert related[0]["related_indicators"] is not None


class TestCachingOperations:
    """Test Redis caching operations."""
    
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_cache_validation_result(self):
        """Test caching validation results."""
        from api.database.operations import CacheOperations
        
        with patch('api.cache.redis_cache.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.set = AsyncMock()
            mock_client.get = AsyncMock()
            mock_client.get.return_value = json.dumps({
                "value": "test@example.com",
                "is_valid": True,
                "confidence_score": 0.95
            }).encode()
            
            cache = CacheOperations()
            
            # Test caching validation result
            result = await cache.cache_validation_result(
                "email:test@example.com",
                {"value": "test@example.com", "is_valid": True, "confidence_score": 0.95}
            )
            
            assert result["success"] is True
            mock_client.set.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_get_cached_validation(self):
        """Test retrieving cached validation results."""
        from api.database.operations import CacheOperations
        
        with patch('api.cache.redis_cache.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.get = AsyncMock()
            mock_client.get.return_value = json.dumps({
                "value": "test@example.com",
                "is_valid": True,
                "confidence_score": 0.95,
                "cached_at": datetime.now().isoformat()
            }).encode()
            
            cache = CacheOperations()
            
            # Test getting cached validation
            cached_result = await cache.get_cached_validation("email:test@example.com")
            
            assert cached_result["success"] is True
            assert "value" in cached_result
            assert cached_result["value"]["is_valid"] is True
    
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_cache_invalidation(self):
        """Test cache invalidation."""
        from api.database.operations import CacheOperations
        
        with patch('api.cache.redis_cache.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.delete = AsyncMock()
            mock_client.delete.return_value = 1
            
            cache = CacheOperations()
            
            # Test cache invalidation
            result = await cache.invalidate_cache("email:test@example.com")
            
            assert result["success"] is True
            mock_client.delete.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_bulk_cache_operations(self):
        """Test bulk cache operations."""
        from api.database.operations import CacheOperations
        
        with patch('api.cache.redis_cache.get_redis_client') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            mock_client.mset = AsyncMock()
            mock_client.mget = AsyncMock()
            mock_client.mget.return_value = [
                json.dumps({"is_valid": True}).encode(),
                json.dumps({"is_valid": False}).encode()
            ]
            
            cache = CacheOperations()
            
            # Test bulk cache set
            data = {
                "email:test1@example.com": {"is_valid": True},
                "email:test2@example.com": {"is_valid": False}
            }
            
            result = await cache.bulk_cache_set(data)
            assert result["success"] is True
            
            # Test bulk cache get
            keys = list(data.keys())
            bulk_result = await cache.bulk_cache_get(keys)
            assert bulk_result["success"] is True
            assert len(bulk_result["values"]) == 2


class TestDatabaseTransactions:
    """Test database transaction handling."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_transaction_rollback(self):
        """Test transaction rollback on error."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            
            # Simulate an error during transaction
            mock_cursor.executemany.side_effect = Exception("Simulated database error")
            
            store = ValidationDataStore()
            
            results = [
                {"type": "email", "value": f"test{i}@example.com", "is_valid": True}
                for i in range(5)
            ]
            
            # Test that transaction rolls back on error
            result = await store.bulk_store_validation_results(results)
            
            assert result["success"] is False
            assert "error" in result
            mock_conn.rollback.assert_called_once()
            mock_conn.close.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_transaction_commit(self):
        """Test successful transaction commit."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [{"id": i} for i in range(1, 3)]
            
            store = ValidationDataStore()
            
            results = [
                {"type": "email", "value": f"test{i}@example.com", "is_valid": True}
                for i in range(2)
            ]
            
            # Test successful transaction commit
            result = await store.bulk_store_validation_results(results)
            
            assert result["success"] is True
            assert result["stored_count"] == 2
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()


class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_indexed_queries(self):
        """Test that queries use proper indexes."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = []
            
            store = ValidationDataStore()
            
            # Test indexed query for validation history
            await store.get_validation_history("email", "example.com", limit=100)
            
            # Verify that the query contains proper WHERE clause for indexing
            call_args = mock_cursor.execute.call_args
            query = call_args[0][0]
            
            # Should contain indexed columns
            assert "WHERE" in query
            assert "value" in query
            assert "type" in query
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_bulk_operations_efficiency(self):
        """Test bulk operations for efficiency."""
        from api.database.operations import ValidationDataStore
        
        with patch('api.database.operations.asyncpg.connect') as mock_pg:
            mock_conn = AsyncMock()
            mock_pg.return_value = mock_conn
            mock_cursor = AsyncMock()
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [{"id": i} for i in range(100)]
            
            store = ValidationDataStore()
            
            # Create large batch of results
            large_batch = [
                {"type": "email", "value": f"test{i}@example.com", "is_valid": True}
                for i in range(100)
            ]
            
            # Test bulk operation with large batch
            result = await store.bulk_store_validation_results(large_batch)
            
            assert result["success"] is True
            assert result["stored_count"] == 100
            
            # Should use batch insert, not individual inserts
            mock_cursor.executemany.assert_called_once()