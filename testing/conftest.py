"""Pytest configuration and shared fixtures."""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Generator

import pytest
import pytest_asyncio
import pytest_html
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))
sys.path.insert(0, str(project_root / "ai_ml"))
sys.path.insert(0, str(project_root / "threat_intelligence"))

# Test configuration
TEST_CONFIG = {
    "test_database_url": "sqlite+aiosqlite:///./test.db",
    "test_redis_url": "redis://localhost:6379/15",
    "api_base_url": "http://localhost:8000",
    "api_key": "test-api-key-123",
    "admin_api_key": "test-admin-key-456",
    "external_api_timeout": 30.0,
    "test_timeout": 60,
    "load_test_users": 100,
    "load_test_spawn_rate": 5
}

# Environment configuration for tests
os.environ.update({
    "TESTING": "true",
    "DATABASE_URL": TEST_CONFIG["test_database_url"],
    "REDIS_URL": TEST_CONFIG["test_redis_url"],
    "API_KEY": TEST_CONFIG["api_key"],
    "ADMIN_API_KEY": TEST_CONFIG["admin_api_key"],
    "LOG_LEVEL": "WARNING"
})


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "load: mark test as a load test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )
    config.addinivalue_line(
        "markers", "external_api: mark test as requiring external API"
    )
    config.addinivalue_line(
        "markers", "ml_model: mark test as requiring ML model"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )


# Add command line options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-db",
        action="store_true",
        default=False,
        help="Run tests requiring database"
    )
    parser.addoption(
        "--run-redis",
        action="store_true",
        default=False,
        help="Run tests requiring Redis"
    )
    parser.addoption(
        "--run-external",
        action="store_true",
        default=False,
        help="Run tests requiring external APIs"
    )
    parser.addoption(
        "--run-ml",
        action="store_true",
        default=False,
        help="Run tests requiring ML models"
    )
    parser.addoption(
        "--generate-fixtures",
        action="store_true",
        default=False,
        help="Generate test fixtures"
    )


# Skip markers for conditional tests
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip tests based on markers."""
    skip_slow = pytest.mark.skip(reason="Need --run-slow option to run")
    skip_db = pytest.mark.skip(reason="Need --run-db option to run")
    skip_redis = pytest.mark.skip(reason="Need --run-redis option to run")
    skip_external = pytest.mark.skip(reason="Need --run-external option to run")
    skip_ml = pytest.mark.skip(reason="Need --run-ml option to run")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--run-slow"):
            item.add_marker(skip_slow)
        if "database" in item.keywords and not config.getoption("--run-db"):
            item.add_marker(skip_db)
        if "redis" in item.keywords and not config.getoption("--run-redis"):
            item.add_marker(skip_redis)
        if "external_api" in item.keywords and not config.getoption("--run-external"):
            item.add_marker(skip_external)
        if "ml_model" in item.keywords and not config.getoption("--run-ml"):
            item.add_marker(skip_ml)


# Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG.copy()


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    fixed_time = datetime(2025, 10, 30, 12, 0, 0)
    
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.utcnow.return_value = fixed_time
        yield mock_dt


@pytest.fixture
def sample_test_data():
    """Provide sample test data."""
    return {
        "emails": {
            "valid": "user@example.com",
            "invalid": "invalid-email",
            "disposable": "user@10minutemail.com",
            "phishing": "security@fake-bank.com",
            "bulk_valid": ["user1@example.com", "user2@test.org", "admin@demo.net"],
            "bulk_invalid": ["not-an-email", "@invalid.com", "user@"]
        },
        "domains": {
            "valid": "example.com",
            "invalid": "not-a-domain",
            "malicious": "malware-site.xyz",
            "suspicious": "suspicious-domain.com",
            "parked": "example-parked-domain.com",
            "bulk": ["domain1.com", "domain2.org", "domain3.net"]
        },
        "ips": {
            "valid_ipv4": "8.8.8.8",
            "valid_ipv6": "2001:4860:4860::8888",
            "private": "192.168.1.1",
            "public": "1.1.1.1",
            "malicious": "192.0.2.100",
            "tor": "127.0.0.2",
            "invalid": "999.999.999.999",
            "bulk": ["1.1.1.1", "8.8.8.8", "1.0.0.1"]
        },
        "urls": {
            "valid": "https://www.example.com/path?param=value",
            "http": "http://example.com",
            "malicious": "https://malicious-site.xyz/path?download=malware.exe",
            "phishing": "http://fake-bank.com/login",
            "shortened": "https://bit.ly/2X123",
            "invalid": "not-a-url"
        },
        "hashes": {
            "md5": "098f6bcd4621d373cade4e832627b4f6",
            "sha1": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
    }


# Test data generators
@pytest.fixture
def data_generator():
    """Provide test data generator."""
    from generators.test_data_generator import TestDataGenerator
    return TestDataGenerator()


# Mock services
@pytest.fixture
def mock_external_apis():
    """Mock external API responses."""
    mock_responses = {
        "abuseipdb": {
            "8.8.8.8": {
                "success": True,
                "data": {
                    "ipAddress": "8.8.8.8",
                    "abuseConfidenceScore": 0,
                    "totalReports": 0,
                    "usageType": " Hosting Provider",
                    "isPublic": True
                }
            }
        },
        "virustotal": {
            "8.8.8.8": {
                "success": True,
                "data": {
                    "attributes": {
                        "reputation": 0,
                        "last_analysis_results": {
                            "harmless": 1,
                            "malicious": 0,
                            "suspicious": 0
                        }
                    }
                }
            }
        }
    }
    
    with patch('threat_intelligence.abuseipdb_collector.AbuseIPDBCollector.query') as mock_abuseipdb, \
         patch('threat_intelligence.virustotal_collector.VirusTotalCollector.query') as mock_vt:
        
        mock_abuseipdb.return_value = AsyncMock(return_value=mock_responses["abuseipdb"]["8.8.8.8"])
        mock_vt.return_value = AsyncMock(return_value=mock_responses["virustotal"]["8.8.8.8"])
        
        yield {
            "abuseipdb": mock_abuseipdb,
            "virustotal": mock_vt
        }


# Database fixtures
@pytest.fixture
async def test_database():
    """Setup test database."""
    from api.database.connections import init_databases, close_databases
    
    try:
        await init_databases()
        yield
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
    finally:
        await close_databases()


@pytest.fixture
async def test_redis():
    """Setup test Redis."""
    from api.cache.redis_cache import init_redis, get_redis_client, close_redis
    
    try:
        await init_redis()
        client = get_redis_client()
        yield client
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")
    finally:
        await close_redis()


# HTTP client fixtures
@pytest.fixture
async def http_client(test_config):
    """Create HTTP client for testing."""
    import httpx
    
    async with httpx.AsyncClient(
        base_url=test_config["api_base_url"],
        timeout=test_config["external_api_timeout"]
    ) as client:
        yield client


@pytest.fixture
async def authenticated_client(test_config):
    """Create authenticated HTTP client."""
    import httpx
    
    headers = {
        "X-API-Key": test_config["api_key"],
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(
        base_url=test_config["api_base_url"],
        headers=headers,
        timeout=test_config["external_api_timeout"]
    ) as client:
        yield client


# ML model fixtures
@pytest.fixture
def mock_ml_models():
    """Mock ML model predictions."""
    return {
        "anomaly_detector": {
            "predict": Mock(return_value={"anomaly_score": 0.15, "is_anomaly": False}),
            "predict_batch": Mock(return_value=[{"anomaly_score": 0.15, "is_anomaly": False}] * 10)
        },
        "phishing_classifier": {
            "predict": Mock(return_value={"phishing_probability": 0.02, "is_phishing": False}),
            "predict_proba": Mock(return_value=[[0.98, 0.02]])
        },
        "domain_reputation": {
            "predict": Mock(return_value={"reputation_score": 85, "confidence": 0.92}),
        },
        "nlp_processor": {
            "extract_iocs": Mock(return_value={
                "ips": ["192.168.1.100"],
                "domains": ["malware-site.com"],
                "hashes": ["abc123def456"]
            }),
            "classify_email": Mock(return_value={"spam_probability": 0.95, "is_spam": True})
        }
    }


# Performance testing fixtures
@pytest.fixture
def performance_monitor():
    """Monitor performance during tests."""
    import time
    import psutil
    import threading
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.peak_memory = 0
            self.peak_cpu = 0
            self.monitoring = False
            
        def start(self):
            self.start_time = time.time()
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor)
            self.monitor_thread.start()
            
        def _monitor(self):
            while self.monitoring:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                self.peak_cpu = max(self.peak_cpu, cpu_percent)
                self.peak_memory = max(self.peak_memory, memory.percent)
                time.sleep(0.1)
                
        def stop(self):
            self.monitoring = False
            if hasattr(self, 'monitor_thread'):
                self.monitor_thread.join()
                
        def get_stats(self):
            duration = time.time() - self.start_time if self.start_time else 0
            return {
                "duration": duration,
                "peak_memory_percent": self.peak_memory,
                "peak_cpu_percent": self.peak_cpu
            }
    
    monitor = PerformanceMonitor()
    yield monitor
    if monitor.monitoring:
        monitor.stop()


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Cleanup test environment after each test."""
    yield
    # Cleanup code here
    import gc
    gc.collect()


# Hook for HTML report
def pytest_html_report_title(report):
    """Customize HTML report title."""
    report.title = "Cybersecurity API - Quality Assurance Report"


def pytest_html_results_summary(prefix, summary, postfix):
    """Customize HTML report summary."""
    prefix.extend([
        "<h2>Test Summary</h2>",
        "<p>Comprehensive testing report for Cybersecurity Validation API</p>"
    ])


# Environment helpers
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment once per test session."""
    # Create test directories
    test_dirs = [
        Path("testing/fixtures/generated"),
        Path("testing/coverage/reports"),
        Path("testing/load/reports")
    ]
    
    for test_dir in test_dirs:
        test_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup after all tests
    for test_dir in test_dirs:
        if test_dir.exists():
            for file in test_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            test_dir.rmdir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])