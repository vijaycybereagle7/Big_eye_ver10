"""Unit tests for API endpoints."""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, Mock
from typing import Dict, Any

# Test configuration
pytestmark = pytest.mark.asyncio


class TestValidationAPI:
    """Test validation API endpoints."""
    
    @pytest.mark.unit
    async def test_email_validation_valid(self, test_client, sample_test_data):
        """Test email validation with valid email."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={"email": sample_test_data["emails"]["valid"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        result = data["result"]
        
        assert result["value"] == sample_test_data["emails"]["valid"]
        assert "is_valid" in result
        assert "confidence_score" in result
        assert "validation_details" in result
        assert result["is_valid"] is True  # Valid email should return True
    
    @pytest.mark.unit
    async def test_email_validation_invalid(self, test_client, sample_test_data):
        """Test email validation with invalid email."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={"email": sample_test_data["emails"]["invalid"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["result"]["is_valid"] is False
        assert "validation_details" in data["result"]
    
    @pytest.mark.unit
    async def test_email_validation_disposable(self, test_client, sample_test_data):
        """Test email validation with disposable email."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={"email": sample_test_data["emails"]["disposable"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        result = data["result"]
        
        # Disposable emails should be detected
        assert "is_disposable" in result
        assert "domain_age" in result
        assert "mx_records" in result
    
    @pytest.mark.unit
    async def test_domain_validation_valid(self, test_client, sample_test_data):
        """Test domain validation with valid domain."""
        response = await test_client.post(
            "/api/v1/validate/domain",
            json={"domain": sample_test_data["domains"]["valid"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["value"] == sample_test_data["domains"]["valid"]
        assert "is_valid" in data["result"]
        assert data["result"]["is_valid"] is True
    
    @pytest.mark.unit
    async def test_domain_validation_invalid(self, test_client, sample_test_data):
        """Test domain validation with invalid domain."""
        response = await test_client.post(
            "/api/v1/validate/domain",
            json={"domain": sample_test_data["domains"]["invalid"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["result"]["is_valid"] is False
        assert "validation_details" in data["result"]
    
    @pytest.mark.unit
    async def test_ip_validation_ipv4(self, test_client, sample_test_data):
        """Test IP validation with IPv4 address."""
        response = await test_client.post(
            "/api/v1/validate/ip",
            json={"ip_address": sample_test_data["ips"]["valid_ipv4"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["value"] == sample_test_data["ips"]["valid_ipv4"]
        assert data["result"]["ip_version"] == 4
        assert "is_private" in data["result"]
        assert "is_public" in data["result"]
    
    @pytest.mark.unit
    async def test_ip_validation_ipv6(self, test_client, sample_test_data):
        """Test IP validation with IPv6 address."""
        response = await test_client.post(
            "/api/v1/validate/ip",
            json={"ip_address": sample_test_data["ips"]["valid_ipv6"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["result"]["ip_version"] == 6
    
    @pytest.mark.unit
    async def test_url_validation_valid(self, test_client, sample_test_data):
        """Test URL validation with valid URL."""
        response = await test_client.post(
            "/api/v1/validate/url",
            json={"url": sample_test_data["urls"]["valid"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        assert data["result"]["value"] == sample_test_data["urls"]["valid"]
        assert "is_valid" in data["result"]
        assert "url_components" in data["result"]
    
    @pytest.mark.unit
    async def test_bulk_validation(self, test_client, sample_test_data):
        """Test bulk validation endpoint."""
        bulk_data = {
            "emails": sample_test_data["emails"]["bulk_valid"] + sample_test_data["emails"]["bulk_invalid"],
            "domains": sample_test_data["domains"]["bulk"],
            "ip_addresses": sample_test_data["ips"]["bulk"]
        }
        
        response = await test_client.post(
            "/api/v1/validate/bulk",
            json=bulk_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "total_items" in data
        assert "valid_items" in data
        assert "invalid_items" in data
        assert "results" in data
        
        # Verify that total matches sum of all items
        total_emails = len(bulk_data["emails"])
        total_domains = len(bulk_data["domains"])
        total_ips = len(bulk_data["ip_addresses"])
        expected_total = total_emails + total_domains + total_ips
        
        assert data["total_items"] == expected_total
        
        # Verify results structure
        assert "email_validation" in data["results"]
        assert "domain_validation" in data["results"]
        assert "ip_validation" in data["results"]


class TestReputationAPI:
    """Test reputation API endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.external_api
    async def test_reputation_query_ip(self, test_client, sample_test_data):
        """Test reputation query for IP address."""
        with patch('api.services.reputation.ReputationService.query_ip') as mock_query:
            # Mock the reputation service response
            mock_query.return_value = {
                "value": sample_test_data["ips"]["valid_ipv4"],
                "value_type": "ip",
                "overall_score": 85,
                "overall_verdict": "good",
                "sources": {
                    "abuseipdb": {"score": 0, "verdict": "clean"},
                    "virustotal": {"reputation": 0, "verdict": "clean"},
                    "greynoise": {"classification": "benign", "score": 0}
                },
                "last_updated": "2025-10-30T12:00:00Z"
            }
            
            response = await test_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": sample_test_data["ips"]["valid_ipv4"],
                    "value_type": "ip",
                    "detailed": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "result" in data
            result = data["result"]
            
            assert result["value"] == sample_test_data["ips"]["valid_ipv4"]
            assert result["value_type"] == "ip"
            assert "overall_score" in result
            assert "overall_verdict" in result
            assert "sources" in result
            
            # Verify mock was called
            mock_query.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.external_api
    async def test_reputation_query_domain(self, test_client, sample_test_data):
        """Test reputation query for domain."""
        with patch('api.services.reputation.ReputationService.query_domain') as mock_query:
            mock_query.return_value = {
                "value": sample_test_data["domains"]["valid"],
                "value_type": "domain",
                "overall_score": 75,
                "overall_verdict": "good",
                "sources": {
                    "virustotal": {"reputation": 25, "verdict": "clean"},
                    "otx": {"reputation": 0, "verdict": "clean"}
                }
            }
            
            response = await test_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": sample_test_data["domains"]["valid"],
                    "value_type": "domain",
                    "detailed": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["result"]["value_type"] == "domain"
            assert data["result"]["overall_score"] == 75
    
    @pytest.mark.unit
    @pytest.mark.external_api
    async def test_reputation_bulk_query(self, test_client, sample_test_data):
        """Test bulk reputation query."""
        bulk_data = {
            "queries": [
                {
                    "value": sample_test_data["ips"]["valid_ipv4"],
                    "value_type": "ip"
                },
                {
                    "value": sample_test_data["domains"]["valid"],
                    "value_type": "domain"
                }
            ]
        }
        
        with patch('api.services.reputation.ReputationService.bulk_query') as mock_bulk:
            mock_bulk.return_value = {
                "results": [
                    {
                        "value": sample_test_data["ips"]["valid_ipv4"],
                        "value_type": "ip",
                        "overall_score": 85,
                        "overall_verdict": "good"
                    },
                    {
                        "value": sample_test_data["domains"]["valid"],
                        "value_type": "domain",
                        "overall_score": 75,
                        "overall_verdict": "good"
                    }
                ],
                "total_processed": 2,
                "success_rate": 100.0
            }
            
            response = await test_client.post(
                "/api/v1/reputation/bulk",
                json=bulk_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "results" in data
            assert data["total_processed"] == 2
            assert len(data["results"]) == 2


class TestThreatIntelligenceAPI:
    """Test threat intelligence API endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.external_api
    async def test_threat_intelligence_query(self, test_client, sample_test_data):
        """Test threat intelligence query."""
        with patch('api.services.threat_intelligence.ThreatIntelligenceService.query') as mock_query:
            mock_query.return_value = {
                "indicator": sample_test_data["ips"]["valid_ipv4"],
                "indicator_type": "ip",
                "intelligence": {
                    "threat_indicators": [],
                    "campaigns": [],
                    "attribution": None,
                    "first_seen": "2025-10-01T00:00:00Z",
                    "last_seen": "2025-10-30T12:00:00Z"
                },
                "confidence_score": 75,
                "risk_level": "low",
                "recommendation": "monitor"
            }
            
            response = await test_client.post(
                "/api/v1/threats/query",
                json={
                    "value": sample_test_data["ips"]["valid_ipv4"],
                    "query_type": "ip",
                    "include_context": True,
                    "include_related": False,
                    "time_range_days": 30
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "result" in data
            result = data["result"]
            
            assert result["indicator"] == sample_test_data["ips"]["valid_ipv4"]
            assert result["indicator_type"] == "ip"
            assert "intelligence" in result
            assert "confidence_score" in result
            assert "risk_level" in result
    
    @pytest.mark.unit
    async def test_threat_intelligence_search(self, test_client):
        """Test threat intelligence search endpoint."""
        with patch('api.services.threat_intelligence.ThreatIntelligenceService.search') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "indicator": "192.0.2.100",
                        "type": "ip",
                        "threat_family": "Zeus",
                        "first_seen": "2025-10-01T00:00:00Z",
                        "last_seen": "2025-10-30T12:00:00Z"
                    }
                ],
                "total_results": 1,
                "query_time": 0.125
            }
            
            response = await test_client.post(
                "/api/v1/threats/search",
                json={
                    "query": "Zeus",
                    "search_type": "threat_family",
                    "limit": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["threat_family"] == "Zeus"


class TestAdminAPI:
    """Test admin API endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.database
    async def test_admin_health_check(self, admin_client):
        """Test admin health check endpoint."""
        response = await admin_client.get("/api/v1/admin/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "health_status" in data
        assert "components" in data
        assert "metrics" in data
    
    @pytest.mark.unit
    async def test_admin_metrics(self, admin_client):
        """Test admin metrics endpoint."""
        response = await admin_client.get("/api/v1/admin/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "metrics" in data
        assert "requests_total" in data["metrics"]
        assert "requests_per_second" in data["metrics"]
    
    @pytest.mark.unit
    async def test_admin_stats(self, admin_client):
        """Test admin statistics endpoint."""
        response = await admin_client.get("/api/v1/admin/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "validation_stats" in data
        assert "reputation_stats" in data
        assert "threat_intel_stats" in data
    
    @pytest.mark.unit
    async def test_admin_rate_limit_info(self, admin_client):
        """Test admin rate limit information endpoint."""
        response = await admin_client.get("/api/v1/admin/rate-limits")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "rate_limits" in data
        assert "api_limits" in data


class TestAPIValidation:
    """Test API input validation and error handling."""
    
    @pytest.mark.unit
    async def test_missing_required_field(self, test_client):
        """Test validation with missing required field."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={}  # Missing 'email' field
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.unit
    async def test_invalid_json(self, test_client):
        """Test validation with invalid JSON."""
        response = await test_client.post(
            "/api/v1/validate/email",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.unit
    async def test_request_too_large(self, test_client):
        """Test validation with oversized request."""
        large_email_list = ["test@example.com"] * 10000  # Very large list
        
        response = await test_client.post(
            "/api/v1/validate/bulk",
            json={"emails": large_email_list}
        )
        
        assert response.status_code == 413  # Payload Too Large
    
    @pytest.mark.unit
    async def test_invalid_value_type(self, test_client):
        """Test validation with invalid value type."""
        response = await test_client.post(
            "/api/v1/reputation/query",
            json={
                "value": "test-value",
                "value_type": "invalid_type"
            }
        )
        
        assert response.status_code == 422  # Unprocessable Entity


class TestAuthentication:
    """Test API authentication."""
    
    @pytest.mark.unit
    async def test_missing_api_key(self, http_client):
        """Test request without API key."""
        response = await http_client.post(
            "/api/v1/validate/email",
            json={"email": "test@example.com"}
        )
        
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.unit
    async def test_invalid_api_key(self, http_client):
        """Test request with invalid API key."""
        headers = {"X-API-Key": "invalid-api-key"}
        
        response = await http_client.post(
            "/api/v1/validate/email",
            json={"email": "test@example.com"},
            headers=headers
        )
        
        assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.unit
    async def test_valid_api_key(self, test_client):
        """Test request with valid API key."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={"email": "test@example.com"}
        )
        
        # Should succeed (though may fail validation)
        assert response.status_code in [200, 422]


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.unit
    async def test_rate_limit_exceeded(self, test_client, sample_test_data):
        """Test rate limiting when exceeded."""
        # Make requests until rate limit is triggered
        responses = []
        for i in range(110):  # Exceed default limit of 100
            response = await test_client.post(
                "/api/v1/validate/email",
                json={"email": f"test{i}@example.com"}
            )
            responses.append(response)
            
            if response.status_code == 429:
                break
        
        # Should have at least one rate-limited response
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
    
    @pytest.mark.unit
    async def test_rate_limit_headers(self, test_client):
        """Test rate limit headers in response."""
        response = await test_client.post(
            "/api/v1/validate/email",
            json={"email": "test@example.com"}
        )
        
        if response.status_code == 200:
            # Rate limit headers should be present
            assert "X-RateLimit-Limit" in response.headers
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers


class TestCORS:
    """Test CORS functionality."""
    
    @pytest.mark.unit
    async def test_cors_headers(self, http_client):
        """Test CORS headers in response."""
        response = await http_client.options("/api/v1/validate/email")
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
        assert "access-control-allow-methods" in [h.lower() for h in response.headers.keys()]
        assert "access-control-allow-headers" in [h.lower() for h in response.headers.keys()]
    
    @pytest.mark.unit
    async def test_preflight_request(self, http_client):
        """Test OPTIONS preflight request."""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-API-Key"
        }
        
        response = await http_client.options(
            "/api/v1/validate/email",
            headers=headers
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in [h.lower() for h in response.headers.keys()]
