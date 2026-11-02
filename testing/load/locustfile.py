"""Load testing configuration using Locust."""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import json
import random
import time
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestData:
    """Test data for load testing."""
    
    # Load test data from fixtures
    try:
        with open("testing/fixtures/generated/load_test_data.json", "r") as f:
            LOAD_TEST_DATA = json.load(f)
    except FileNotFoundError:
        # Fallback to generated data
        LOAD_TEST_DATA = {
            "valid_emails": [f"user{i}@example.com" for i in range(100)],
            "valid_domains": [f"domain{i}.com" for i in range(100)],
            "valid_ips": [f"192.168.1.{i}" for i in range(1, 101)],
            "valid_urls": [f"https://example{i}.com/path" for i in range(100)],
            "suspicious_domains": [f"suspicious{i}.com" for i in range(50)],
            "malicious_ips": [f"192.0.2.{i}" for i in range(1, 51)]
        }


class APITestUser(HttpUser):
    """Base API test user with common functionality."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    weight = 3  # Default weight for most users
    
    def on_start(self):
        """Initialize user on start."""
        self.api_key = "test-api-key-123"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make HTTP request with error handling."""
        try:
            with self.client.request(
                method, 
                endpoint, 
                headers=self.headers, 
                **kwargs,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                    return response
                elif response.status_code == 429:
                    response.failure("Rate limited")
                    return response
                elif response.status_code == 401:
                    response.failure("Authentication failed")
                    return response
                else:
                    response.failure(f"HTTP {response.status_code}")
                    return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None


class ValidationUser(HttpUser):
    """Load test user for validation endpoints."""
    
    wait_time = between(0.5, 2)
    weight = 5
    
    @task(10)
    def validate_email(self):
        """Test email validation endpoint."""
        email = random.choice(TestData.LOAD_TEST_DATA["valid_emails"])
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/email",
            json={"email": email}
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(8)
    def validate_domain(self):
        """Test domain validation endpoint."""
        domain = random.choice(TestData.LOAD_TEST_DATA["valid_domains"])
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/domain",
            json={"domain": domain}
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(6)
    def validate_ip(self):
        """Test IP validation endpoint."""
        ip = random.choice(TestData.LOAD_TEST_DATA["valid_ips"])
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/ip",
            json={"ip_address": ip}
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(4)
    def validate_url(self):
        """Test URL validation endpoint."""
        url = random.choice(TestData.LOAD_TEST_DATA["valid_urls"])
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/url",
            json={"url": url}
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(3)
    def bulk_validation(self):
        """Test bulk validation endpoint."""
        bulk_data = {
            "emails": random.sample(TestData.LOAD_TEST_DATA["valid_emails"], 5),
            "domains": random.sample(TestData.LOAD_TEST_DATA["valid_domains"], 3),
            "ip_addresses": random.sample(TestData.LOAD_TEST_DATA["valid_ips"], 2)
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/bulk",
            json=bulk_data
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["total_items"] == 10


class ReputationUser(HttpUser):
    """Load test user for reputation endpoints."""
    
    wait_time = between(1, 3)
    weight = 4
    
    @task(8)
    def query_ip_reputation(self):
        """Test IP reputation query."""
        ip = random.choice(TestData.LOAD_TEST_DATA["valid_ips"])
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/query",
            json={
                "value": ip,
                "value_type": "ip",
                "detailed": random.choice([True, False])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(6)
    def query_domain_reputation(self):
        """Test domain reputation query."""
        domain = random.choice(TestData.LOAD_TEST_DATA["valid_domains"])
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/query",
            json={
                "value": domain,
                "value_type": "domain",
                "detailed": random.choice([True, False])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(4)
    def bulk_reputation_query(self):
        """Test bulk reputation query."""
        bulk_data = {
            "queries": [
                {
                    "value": random.choice(TestData.LOAD_TEST_DATA["valid_ips"]),
                    "value_type": "ip"
                },
                {
                    "value": random.choice(TestData.LOAD_TEST_DATA["valid_domains"]),
                    "value_type": "domain"
                }
            ]
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/bulk",
            json=bulk_data
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "results" in data
    
    @task(2)
    def check_malicious_ip_reputation(self):
        """Test reputation check for known suspicious IP."""
        ip = random.choice(TestData.LOAD_TEST_DATA["malicious_ips"])
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/query",
            json={
                "value": ip,
                "value_type": "ip",
                "detailed": True
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            result = data["result"]
            # Malicious IP should have low reputation score
            if "overall_score" in result:
                assert result["overall_score"] <= 50


class ThreatIntelUser(HttpUser):
    """Load test user for threat intelligence endpoints."""
    
    wait_time = between(2, 5)
    weight = 3
    
    @task(6)
    def query_threat_intelligence(self):
        """Test threat intelligence query."""
        ip = random.choice(TestData.LOAD_TEST_DATA["valid_ips"])
        
        response = self.make_request(
            "POST",
            "/api/v1/threats/query",
            json={
                "value": ip,
                "query_type": "ip",
                "include_context": random.choice([True, False]),
                "time_range_days": random.choice([1, 7, 30])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
    
    @task(4)
    def search_threats(self):
        """Test threat intelligence search."""
        search_terms = ["malware", "botnet", "apt", "phishing", "spam"]
        query = random.choice(search_terms)
        
        response = self.make_request(
            "POST",
            "/api/v1/threats/search",
            json={
                "query": query,
                "search_type": random.choice(["threat_family", "campaign", "indicator"]),
                "limit": random.choice([10, 25, 50])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "results" in data
    
    @task(2)
    def correlate_indicators(self):
        """Test threat correlation."""
        indicators = [
            random.choice(TestData.LOAD_TEST_DATA["valid_ips"]),
            random.choice(TestData.LOAD_TEST_DATA["valid_domains"])
        ]
        
        response = self.make_request(
            "POST",
            "/api/v1/threats/correlate",
            json={
                "indicators": indicators,
                "correlation_type": "infrastructure",
                "include_campaigns": random.choice([True, False])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "correlation_score" in data["result"]


class MLUser(HttpUser):
    """Load test user for ML endpoints."""
    
    wait_time = between(3, 6)
    weight = 2
    
    @task(5)
    def anomaly_detection(self):
        """Test anomaly detection."""
        anomaly_data = {
            "source_ip": random.choice(TestData.LOAD_TEST_DATA["valid_ips"]),
            "dest_ip": random.choice(TestData.LOAD_TEST_DATA["valid_ips"]),
            "bytes_sent": random.randint(1000, 10000000),
            "bytes_received": random.randint(1000, 50000000),
            "duration": random.uniform(0.1, 300),
            "protocol": random.choice(["TCP", "UDP"])
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/ml/anomaly-detection",
            json=anomaly_data
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
            result = data["result"]
            assert "anomaly_score" in result
            assert "is_anomaly" in result
    
    @task(3)
    def phishing_detection(self):
        """Test phishing detection."""
        email_data = {
            "subject": random.choice([
                "Important security update",
                "Meeting reminder",
                "Account verification required",
                "Daily newsletter",
                "System maintenance notice"
            ]),
            "body": f"This is a test email body with some content. {random.choice(['urgent', 'important', 'normal'])}.",
            "sender_email": random.choice(TestData.LOAD_TEST_DATA["valid_emails"])
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/ml/phishing-detection",
            json=email_data
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data
            result = data["result"]
            assert "phishing_probability" in result
    
    @task(2)
    def domain_reputation(self):
        """Test domain reputation analysis."""
        domain_data = {
            "domain": random.choice(TestData.LOAD_TEST_DATA["valid_domains"]),
            "include_features": True,
            "historical_data": random.choice([True, False])
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/ml/domain-reputation",
            json=domain_data
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "result" in data


class AdminUser(HttpUser):
    """Load test user for admin endpoints."""
    
    wait_time = between(5, 10)
    weight = 1
    admin_api_key = "test-admin-key-456"
    
    def on_start(self):
        """Initialize admin user."""
        super().on_start()
        self.headers["X-API-Key"] = self.admin_api_key
    
    @task(3)
    def health_check(self):
        """Test admin health check."""
        response = self.make_request(
            "GET",
            "/api/v1/admin/health"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(2)
    def metrics_check(self):
        """Test admin metrics."""
        response = self.make_request(
            "GET",
            "/api/v1/admin/metrics"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "metrics" in data
    
    @task(1)
    def stats_check(self):
        """Test admin statistics."""
        response = self.make_request(
            "GET",
            "/api/v1/admin/stats"
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True


class MixedWorkloadUser(HttpUser):
    """Load test user that simulates mixed real-world workload."""
    
    wait_time = between(2, 4)
    weight = 3
    
    @task(20)
    def mixed_validation(self):
        """Mixed validation requests."""
        endpoint = random.choice([
            "/api/v1/validate/email",
            "/api/v1/validate/domain", 
            "/api/v1/validate/ip",
            "/api/v1/validate/url"
        ])
        
        if "email" in endpoint:
            data = {"email": random.choice(TestData.LOAD_TEST_DATA["valid_emails"])}
        elif "domain" in endpoint:
            data = {"domain": random.choice(TestData.LOAD_TEST_DATA["valid_domains"])}
        elif "ip" in endpoint:
            data = {"ip_address": random.choice(TestData.LOAD_TEST_DATA["valid_ips"])}
        else:
            data = {"url": random.choice(TestData.LOAD_TEST_DATA["valid_urls"])}
        
        response = self.make_request("POST", endpoint, json=data)
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(15)
    def mixed_reputation(self):
        """Mixed reputation queries."""
        value_type = random.choice(["ip", "domain"])
        if value_type == "ip":
            value = random.choice(TestData.LOAD_TEST_DATA["valid_ips"])
        else:
            value = random.choice(TestData.LOAD_TEST_DATA["valid_domains"])
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/query",
            json={
                "value": value,
                "value_type": value_type,
                "detailed": random.choice([True, False])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(10)
    def mixed_threat_intel(self):
        """Mixed threat intelligence queries."""
        query_type = random.choice(["ip", "domain", "hash"])
        if query_type == "ip":
            value = random.choice(TestData.LOAD_TEST_DATA["valid_ips"])
        elif query_type == "domain":
            value = random.choice(TestData.LOAD_TEST_DATA["valid_domains"])
        else:
            value = "abc123def456"
        
        response = self.make_request(
            "POST",
            "/api/v1/threats/query",
            json={
                "value": value,
                "query_type": query_type,
                "include_context": random.choice([True, False])
            }
        )
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(5)
    def bulk_operations(self):
        """Bulk operations mixed workload."""
        operation = random.choice(["validation", "reputation"])
        
        if operation == "validation":
            bulk_data = {
                "emails": random.sample(TestData.LOAD_TEST_DATA["valid_emails"], 3),
                "domains": random.sample(TestData.LOAD_TEST_DATA["valid_domains"], 2)
            }
            endpoint = "/api/v1/validate/bulk"
        else:
            bulk_data = {
                "queries": [
                    {
                        "value": random.choice(TestData.LOAD_TEST_DATA["valid_ips"]),
                        "value_type": "ip"
                    },
                    {
                        "value": random.choice(TestData.LOAD_TEST_DATA["valid_domains"]),
                        "value_type": "domain"
                    }
                ]
            }
            endpoint = "/api/v1/reputation/bulk"
        
        response = self.make_request("POST", endpoint, json=bulk_data)
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True


class StressTestUser(HttpUser):
    """Stress test user for high-load scenarios."""
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    weight = 1
    
    def on_start(self):
        """Initialize stress test user."""
        self.api_key = "test-api-key-123"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @task
    def rapid_validation_requests(self):
        """Rapid validation requests to test rate limiting."""
        email = random.choice(TestData.LOAD_TEST_DATA["valid_emails"])
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/email",
            json={"email": email}
        )
        
        # Don't assert on success for stress tests
        # Just measure response times and error rates
        if response:
            response.success()


# Custom events for load testing
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize load test."""
    logger.info(f"Starting load test with {environment.runner.target_user_count} users")
    
    if isinstance(environment.runner, MasterRunner):
        logger.info("Running in Master mode")
    elif isinstance(environment.runner, WorkerRunner):
        logger.info("Running in Worker mode")
    
    # Initialize test data
    logger.info("Test data initialized")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Cleanup after load test."""
    logger.info("Load test completed")
    
    # Log final statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failures: {stats.total.num_failures}")
    logger.info(f"Median response time: {stats.total.median_response_time}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95)}ms")


@events.request.add_listener
def on_request(environment, request_type, name, response_time, response_length, exception, **kwargs):
    """Track individual requests."""
    if exception:
        logger.error(f"Request failed: {name} - {exception}")
    elif response_time > 5000:  # Log slow requests
        logger.warning(f"Slow request: {name} - {response_time}ms")


# Performance benchmarking tasks
class BenchmarkUser(HttpUser):
    """User for performance benchmarking."""
    
    wait_time = between(5, 10)
    weight = 1
    
    def on_start(self):
        """Initialize benchmark user."""
        self.api_key = "test-api-key-123"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    @task(10)
    def benchmark_email_validation(self):
        """Benchmark email validation performance."""
        start_time = time.time()
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/email",
            json={"email": "benchmark@example.com"}
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        logger.info(f"Email validation benchmark: {response_time:.2f}ms")
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(8)
    def benchmark_domain_validation(self):
        """Benchmark domain validation performance."""
        start_time = time.time()
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/domain",
            json={"domain": "benchmark.com"}
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        logger.info(f"Domain validation benchmark: {response_time:.2f}ms")
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(6)
    def benchmark_reputation_query(self):
        """Benchmark reputation query performance."""
        start_time = time.time()
        
        response = self.make_request(
            "POST",
            "/api/v1/reputation/query",
            json={
                "value": "8.8.8.8",
                "value_type": "ip",
                "detailed": True
            }
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        logger.info(f"Reputation query benchmark: {response_time:.2f}ms")
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(4)
    def benchmark_threat_query(self):
        """Benchmark threat intelligence query performance."""
        start_time = time.time()
        
        response = self.make_request(
            "POST",
            "/api/v1/threats/query",
            json={
                "value": "8.8.8.8",
                "query_type": "ip",
                "include_context": False
            }
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        logger.info(f"Threat query benchmark: {response_time:.2f}ms")
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True
    
    @task(2)
    def benchmark_bulk_operations(self):
        """Benchmark bulk operation performance."""
        start_time = time.time()
        
        bulk_data = {
            "emails": TestData.LOAD_TEST_DATA["valid_emails"][:10],
            "domains": TestData.LOAD_TEST_DATA["valid_domains"][:10],
            "ip_addresses": TestData.LOAD_TEST_DATA["valid_ips"][:10]
        }
        
        response = self.make_request(
            "POST",
            "/api/v1/validate/bulk",
            json=bulk_data
        )
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        logger.info(f"Bulk validation benchmark: {response_time:.2f}ms")
        
        if response and response.status_code == 200:
            data = response.json()
            assert data["success"] is True


# Export user classes for different test scenarios
LOAD_TEST_USER_CLASSES = [
    ValidationUser,
    ReputationUser, 
    ThreatIntelUser,
    MLUser,
    AdminUser,
    MixedWorkloadUser,
    StressTestUser,
    BenchmarkUser
]


# Default test configuration
DEFAULT_HOST = "http://localhost:8000"
DEFAULT_USERS = 50
DEFAULT_SPAWN_RATE = 5
DEFAULT_DURATION = "5m"


if __name__ == "__main__":
    from locust.main import main
    
    # Run with custom configuration
    import sys
    
    # Default arguments
    host = os.getenv("LOAD_TEST_HOST", DEFAULT_HOST)
    users = int(os.getenv("LOAD_TEST_USERS", DEFAULT_USERS))
    spawn_rate = int(os.getenv("LOAD_TEST_SPAWN_RATE", DEFAULT_SPAWN_RATE))
    duration = os.getenv("LOAD_TEST_DURATION", DEFAULT_DURATION)
    
    # Override with command line arguments if provided
    if "--host" not in sys.argv:
        sys.argv.extend(["--host", host])
    if "--users" not in sys.argv:
        sys.argv.extend(["--users", str(users)])
    if "--spawn-rate" not in sys.argv:
        sys.argv.extend(["--spawn-rate", str(spawn_rate)])
    if "--run-time" not in sys.argv:
        sys.argv.extend(["--run-time", duration])
    
    main()