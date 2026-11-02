"""Test configuration and utilities for the Cybersecurity Validation API."""

import pytest
import asyncio
from typing import Dict, Any
from httpx import AsyncClient, Headers
import json

# Test configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_key": "default-api-key-123",
    "admin_api_key": "admin-api-key-456",
    "timeout": 30.0
}


class APITestClient:
    """Test client for making API requests with authentication."""
    
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or TEST_CONFIG["base_url"]
        self.api_key = api_key or TEST_CONFIG["api_key"]
        self.client = None
    
    async def __aenter__(self):
        self.client = AsyncClient(base_url=self.base_url, timeout=TEST_CONFIG["timeout"])
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def _headers(self, additional_headers: Dict[str, str] = None) -> Headers:
        """Get request headers with authentication."""
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        if additional_headers:
            headers.update(additional_headers)
        return Headers(headers)
    
    async def get(self, path: str, params: Dict[str, Any] = None):
        """Make GET request."""
        headers = self._headers()
        response = await self.client.get(f"{self.base_url}{path}", headers=headers, params=params)
        return response
    
    async def post(self, path: str, data: Dict[str, Any] = None):
        """Make POST request."""
        headers = self._headers()
        json_data = json.dumps(data) if data else None
        response = await self.client.post(f"{self.base_url}{path}", headers=headers, content=json_data)
        return response
    
    async def delete(self, path: str):
        """Make DELETE request."""
        headers = self._headers()
        response = await self.client.delete(f"{self.base_url}{path}", headers=headers)
        return response


# Test data for validation
VALID_TEST_DATA = {
    "emails": {
        "valid": "user@example.com",
        "invalid": "invalid-email",
        "disposable": "user@10minutemail.com",
        "role_account": "admin@example.com"
    },
    "domains": {
        "valid": "example.com",
        "invalid": "not-a-domain",
        "parked": "example-parked-domain.com"
    },
    "ips": {
        "valid_ipv4": "8.8.8.8",
        "valid_ipv6": "2001:4860:4860::8888",
        "private": "192.168.1.1",
        "invalid": "999.999.999.999"
    },
    "urls": {
        "valid": "https://www.example.com/path?param=value",
        "invalid": "not-a-url",
        "http": "http://example.com"
    },
    "senders": {
        "valid": {
            "email": "user@example.com",
            "domain": "example.com"
        },
        "invalid": {
            "email": "user@invalid-domain",
            "domain": "invalid-domain"
        }
    }
}


# Test fixtures
@pytest.fixture
async def test_client():
    """Create test client for API testing."""
    async with APITestClient() as client:
        yield client


@pytest.fixture
async def admin_client():
    """Create admin test client for API testing."""
    async with APITestClient(api_key=TEST_CONFIG["admin_api_key"]) as client:
        yield client


# Helper functions for tests
async def validate_response(response, expected_status: int = 200):
    """Validate HTTP response."""
    assert response.status_code == expected_status
    
    if expected_status == 200:
        data = response.json()
        assert "success" in data
        assert data["success"] in [True, False]
        assert "message" in data
        assert "timestamp" in data
        return data
    else:
        # Handle error responses
        error_data = response.json()
        assert "error" in error_data
        assert "error_code" in error_data["error"]
        assert "error_message" in error_data["error"]
        return error_data


async def test_email_validation(client: APITestClient):
    """Test email validation endpoint."""
    # Test valid email
    response = await client.post("/api/v1/validate/email", {
        "email": VALID_TEST_DATA["emails"]["valid"]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert "result" in data
    result = data["result"]
    assert result["value"] == VALID_TEST_DATA["emails"]["valid"]
    assert "is_valid" in result
    assert "confidence_score" in result
    
    # Test invalid email
    response = await client.post("/api/v1/validate/email", {
        "email": VALID_TEST_DATA["emails"]["invalid"]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert data["result"]["is_valid"] is False


async def test_domain_validation(client: APITestClient):
    """Test domain validation endpoint."""
    response = await client.post("/api/v1/validate/domain", {
        "domain": VALID_TEST_DATA["domains"]["valid"]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert "result" in data
    assert data["result"]["value"] == VALID_TEST_DATA["domains"]["valid"]


async def test_ip_validation(client: APITestClient):
    """Test IP validation endpoint."""
    response = await client.post("/api/v1/validate/ip", {
        "ip_address": VALID_TEST_DATA["ips"]["valid_ipv4"]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert data["result"]["value"] == VALID_TEST_DATA["ips"]["valid_ipv4"]
    assert data["result"]["ip_version"] == 4


async def test_url_validation(client: APITestClient):
    """Test URL validation endpoint."""
    response = await client.post("/api/v1/validate/url", {
        "url": VALID_TEST_DATA["urls"]["valid"]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert data["result"]["value"] == VALID_TEST_DATA["urls"]["valid"]


async def test_bulk_validation(client: APITestClient):
    """Test bulk validation endpoint."""
    response = await client.post("/api/v1/validate/bulk", {
        "emails": [
            VALID_TEST_DATA["emails"]["valid"],
            VALID_TEST_DATA["emails"]["invalid"]
        ],
        "domains": [VALID_TEST_DATA["domains"]["valid"]],
        "ip_addresses": [VALID_TEST_DATA["ips"]["valid_ipv4"]]
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert "total_items" in data
    assert "valid_items" in data
    assert "invalid_items" in data
    assert "results" in data
    assert len(data["results"]) > 0


async def test_reputation_query(client: APITestClient):
    """Test reputation query endpoint."""
    response = await client.post("/api/v1/reputation/query", {
        "value": VALID_TEST_DATA["ips"]["valid_ipv4"],
        "value_type": "ip",
        "detailed": False
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert "result" in data
    result = data["result"]
    assert result["value"] == VALID_TEST_DATA["ips"]["valid_ipv4"]
    assert result["value_type"] == "ip"
    assert "overall_score" in result
    assert "overall_verdict" in result
    assert "sources" in result


async def test_threat_intelligence_query(client: APITestClient):
    """Test threat intelligence query endpoint."""
    response = await client.post("/api/v1/threats/query", {
        "value": VALID_TEST_DATA["ips"]["valid_ipv4"],
        "query_type": "ip",
        "include_context": True,
        "include_related": False,
        "time_range_days": 7
    })
    data = await validate_response(response, 200)
    assert data["success"] is True
    assert "result" in data
    result = data["result"]
    assert result["indicator"] == VALID_TEST_DATA["ips"]["valid_ipv4"]
    assert result["indicator_type"] == "ip"
    assert "intelligence" in result
    assert "confidence_score" in result
    assert "risk_level" in result


async def test_authentication_error():
    """Test authentication failure."""
    async with APITestClient(api_key="invalid-key") as client:
        response = await client.post("/api/v1/validate/email", {
            "email": VALID_TEST_DATA["emails"]["valid"]
        })
        assert response.status_code == 401
        error_data = await validate_response(response, 401)
        assert error_data["success"] is False
        assert "error" in error_data


async def test_rate_limiting(client: APITestClient):
    """Test rate limiting."""
    # Make multiple requests quickly to trigger rate limiting
    responses = []
    for i in range(105):  # More than the default limit of 100
        response = await client.post("/api/v1/validate/email", {
            "email": VALID_TEST_DATA["emails"]["valid"]
        })
        responses.append(response)
    
    # At least some requests should be rate limited
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0


# Performance test helpers
async def benchmark_endpoint(client: APITestClient, path: str, data: Dict[str, Any], iterations: int = 10):
    """Benchmark API endpoint performance."""
    import time
    
    times = []
    for _ in range(iterations):
        start_time = time.time()
        response = await client.post(path, data)
        end_time = time.time()
        
        assert response.status_code == 200
        times.append(end_time - start_time)
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    return {
        "average_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "iterations": iterations
    }


# Database test helpers
@pytest.fixture
async def test_database():
    """Setup test database."""
    from ..database.connections import init_databases, close_databases
    
    await init_databases()
    yield
    await close_databases()


@pytest.fixture
async def test_cache():
    """Setup test cache."""
    from ..cache.redis_cache import init_redis, check_redis_health
    
    try:
        await init_redis()
        health = await check_redis_health()
        assert health["status"] == "healthy"
        yield
    except Exception:
        pytest.skip("Redis not available for testing")


# Test markers for different test categories
pytestmark = pytest.mark.asyncio

# Mark tests that require external APIs
pytest.mark.external_api = pytest.mark.skipif(
    not all([
        pytest.config.getoption("--run-external"),
    ]), 
    reason="External API tests disabled. Use --run-external to enable."
)

# Mark tests that require database
pytest.mark.database = pytest.mark.skipif(
    not pytest.config.getoption("--run-db"),
    reason="Database tests disabled. Use --run-db to enable."
)

# Mark integration tests
pytest.mark.integration = pytest.mark.skipif(
    not pytest.config.getoption("--run-integration"),
    reason="Integration tests disabled. Use --run-integration to enable."
)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "external_api: mark test as requiring external APIs")
    config.addinivalue_line("markers", "database: mark test as requiring database")
    config.addinivalue_line("markers", "integration: mark test as integration test")


# Test configuration for pytest
def pytest_addoption(parser):
    """Add command line options for test configuration."""
    parser.addoption(
        "--run-external",
        action="store_true",
        default=False,
        help="Run tests that require external API access"
    )
    parser.addoption(
        "--run-db",
        action="store_true", 
        default=False,
        help="Run tests that require database access"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False, 
        help="Run integration tests"
    )
    parser.addoption(
        "--benchmark",
        action="store_true",
        default=False,
        help="Run performance benchmarks"
    )


# Example usage in test files
"""
# Example test file: test_validation.py
import pytest

@pytest.mark.asyncio
@pytest.mark.database
async def test_email_validation_comprehensive(test_client, test_database):
    '''Test email validation with database setup.'''
    await test_email_validation(test_client)

@pytest.mark.asyncio
@pytest.mark.external_api  
async def test_reputation_with_external_apis(test_client):
    '''Test reputation queries with external APIs.'''
    await test_reputation_query(test_client)

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_performance_benchmarks(test_client):
    '''Run performance benchmarks.'''
    if pytest.config.getoption("--benchmark"):
        result = await benchmark_endpoint(
            test_client,
            "/api/v1/validate/email",
            {"email": "user@example.com"},
            iterations=100
        )
        print(f"Average response time: {result['average_time']:.3f}s")
        assert result['average_time'] < 1.0  # Should respond within 1 second
"""

# Testing utilities
class TestDataGenerator:
    """Generate test data for validation testing."""
    
    @staticmethod
    def generate_test_emails(count: int = 10) -> list:
        """Generate test email addresses."""
        domains = ["example.com", "test.com", "demo.org", "sample.net"]
        emails = []
        
        for i in range(count):
            local_part = f"user{i}"
            domain = domains[i % len(domains)]
            emails.append(f"{local_part}@{domain}")
        
        return emails
    
    @staticmethod
    def generate_test_domains(count: int = 10) -> list:
        """Generate test domain names."""
        return [f"domain{i}.com" for i in range(count)]
    
    @staticmethod
    def generate_test_ips(count: int = 10) -> list:
        """Generate test IP addresses."""
        return [f"192.168.1.{i+1}" for i in range(count)]


# Load test configuration
def load_test_config():
    """Load test configuration from environment or defaults."""
    import os
    
    config = TEST_CONFIG.copy()
    
    # Override with environment variables if present
    config.update({
        "base_url": os.getenv("TEST_API_URL", config["base_url"]),
        "api_key": os.getenv("TEST_API_KEY", config["api_key"]),
        "admin_api_key": os.getenv("TEST_ADMIN_API_KEY", config["admin_api_key"])
    })
    
    return config


if __name__ == "__main__":
    # Run basic tests if executed directly
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])