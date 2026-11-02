"""Integration tests for API endpoints."""

import pytest
import asyncio
import json
import time
from typing import Dict, Any
from unittest.mock import patch, AsyncMock

pytestmark = pytest.mark.asyncio


class TestValidationIntegration:
    """Integration tests for validation API."""
    
    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.redis
    async def test_complete_validation_workflow(self, authenticated_client, test_database, test_redis, sample_test_data):
        """Test complete validation workflow including database and cache."""
        email = sample_test_data["emails"]["valid"]
        
        # First request - should hit database and cache result
        response1 = await authenticated_client.post(
            "/api/v1/validate/email",
            json={"email": email}
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True
        
        # Verify validation result was stored in database
        # This would require actual database access in real implementation
        
        # Second request - should hit cache
        response2 = await authenticated_client.post(
            "/api/v1/validate/email",
            json={"email": email}
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True
        
        # Response should be similar (cached result)
        assert data1["result"]["is_valid"] == data2["result"]["is_valid"]
    
    @pytest.mark.integration
    @pytest.mark.external_api
    async def test_bulk_validation_integration(self, authenticated_client, sample_test_data):
        """Test bulk validation with external API integration."""
        with patch('api.services.validation.ValidationService._check_disposable_email') as mock_disposable, \
             patch('api.services.validation.ValidationService._check_domain_reputation') as mock_reputation:
            
            mock_disposable.return_value = {"is_disposable": False, "source": "disposable_check"}
            mock_reputation.return_value = {"reputation_score": 85, "source": "reputation_api"}
            
            bulk_data = {
                "emails": sample_test_data["emails"]["bulk_valid"][:5],
                "domains": sample_test_data["domains"]["bulk"][:3],
                "ip_addresses": sample_test_data["ips"]["bulk"][:2]
            }
            
            response = await authenticated_client.post(
                "/api/v1/validate/bulk",
                json=bulk_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["total_items"] == 10  # 5 + 3 + 2
            
            # Verify all items were processed
            assert "email_validation" in data["results"]
            assert "domain_validation" in data["results"]
            assert "ip_validation" in data["results"]
            
            assert len(data["results"]["email_validation"]) == 5
            assert len(data["results"]["domain_validation"]) == 3
            assert len(data["results"]["ip_validation"]) == 2
            
            # Verify mock calls were made
            assert mock_disposable.call_count >= 5  # At least one per email
            assert mock_reputation.call_count >= 3  # At least one per domain
    
    @pytest.mark.integration
    async def test_validation_error_handling(self, authenticated_client):
        """Test validation error handling and recovery."""
        # Test with malformed request
        response = await authenticated_client.post(
            "/api/v1/validate/email",
            json={"invalid_field": "test@example.com"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test with empty email
        response = await authenticated_client.post(
            "/api/v1/validate/email",
            json={"email": ""}
        )
        
        assert response.status_code == 200  # Should handle gracefully
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is False
    
    @pytest.mark.integration
    async def test_concurrent_validations(self, authenticated_client, sample_test_data):
        """Test concurrent validation requests."""
        emails = sample_test_data["emails"]["bulk_valid"][:20]
        
        # Create concurrent requests
        tasks = [
            authenticated_client.post(
                "/api/v1/validate/email",
                json={"email": email}
            )
            for email in emails
        ]
        
        # Execute all requests concurrently
        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Verify all requests completed successfully
        assert len(responses) == 20
        
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
        
        # Verify performance (should complete in reasonable time)
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete within 10 seconds for 20 requests


class TestReputationIntegration:
    """Integration tests for reputation API."""
    
    @pytest.mark.integration
    @pytest.mark.external_api
    async def test_reputation_comprehensive_query(self, authenticated_client, mock_external_apis, sample_test_data):
        """Test comprehensive reputation query with all data sources."""
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.reputation.ReputationService._query_multiple_sources') as mock_sources:
            # Mock comprehensive reputation data from multiple sources
            mock_sources.return_value = {
                "abuseipdb": {
                    "abuseConfidenceScore": 0,
                    "totalReports": 0,
                    "isp": "Google LLC",
                    "usageType": "Hosting Provider"
                },
                "virustotal": {
                    "detected_urls": [],
                    "reputation": 0,
                    "detected_samples": []
                },
                "greynoise": {
                    "noise": False,
                    "riot": True,
                    "classification": "benign",
                    "name": "Google Public DNS"
                },
                "otx": {
                    "pulse_info": {"count": 0},
                    "reputation": 0,
                    "sections": {"malware": {}}
                }
            }
            
            response = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "detailed": True,
                    "include_context": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            result = data["result"]
            
            assert result["value"] == ip
            assert result["value_type"] == "ip"
            assert "overall_score" in result
            assert "overall_verdict" in result
            assert "sources" in result
            assert "last_updated" in result
            
            # Verify all sources were queried
            assert "abuseipdb" in result["sources"]
            assert "virustotal" in result["sources"]
            assert "greynoise" in result["sources"]
            assert "otx" in result["sources"]
            
            # Verify mock was called
            mock_sources.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.external_api
    async def test_reputation_cache_integration(self, authenticated_client, test_redis, sample_test_data):
        """Test reputation query with caching integration."""
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.reputation.ReputationService._query_external_apis') as mock_query:
            # First call - should query external APIs
            response1 = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "use_cache": True
                }
            )
            
            assert response1.status_code == 200
            assert mock_query.call_count == 1
            
            # Second call - should use cache
            response2 = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "use_cache": True
                }
            )
            
            assert response2.status_code == 200
            # Should not query external APIs again
            assert mock_query.call_count == 1  # Still 1, not 2
    
    @pytest.mark.integration
    async def test_reputation_error_recovery(self, authenticated_client, sample_test_data):
        """Test reputation API error recovery."""
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.reputation.ReputationService._query_external_apis') as mock_query:
            # Simulate external API failures
            mock_query.side_effect = [
                {"error": "AbuseIPDB unavailable"},
                {"error": "VirusTotal unavailable"}
            ]
            
            response = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "fallback_on_error": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return partial data with error information
            assert data["success"] is True
            assert "result" in data
            assert "partial_data" in data["result"]
            assert "errors" in data["result"]


class TestThreatIntelligenceIntegration:
    """Integration tests for threat intelligence API."""
    
    @pytest.mark.integration
    @pytest.mark.external_api
    async def test_threat_intel_comprehensive_search(self, authenticated_client, sample_test_data):
        """Test comprehensive threat intelligence search."""
        with patch('api.services.threat_intelligence.ThreatIntelligenceService._search_multiple_sources') as mock_search:
            mock_search.return_value = {
                "indicators": [
                    {
                        "indicator": sample_test_data["ips"]["valid_ipv4"],
                        "type": "ip",
                        "threat_family": "Clean IP",
                        "confidence": 0.95,
                        "sources": ["greynoise", "abuseipdb"]
                    }
                ],
                "campaigns": [],
                "attribution": {},
                "total_results": 1
            }
            
            response = await authenticated_client.post(
                "/api/v1/threats/search",
                json={
                    "query": "malware",
                    "search_type": "threat_family",
                    "time_range_days": 30,
                    "include_context": True,
                    "limit": 50
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "results" in data
            assert "total_results" in data
            assert "query_time" in data
    
    @pytest.mark.integration
    async def test_threat_intel_correlation(self, authenticated_client, sample_test_data):
        """Test threat intelligence correlation functionality."""
        with patch('api.services.threat_intelligence.ThreatIntelligenceService.correlate_indicators') as mock_correlate:
            mock_correlate.return_value = {
                "correlation_score": 0.85,
                "related_indicators": [
                    {
                        "indicator": "malware-site.com",
                        "relationship": "hosted_domain",
                        "confidence": 0.92
                    }
                ],
                "campaigns": [
                    {
                        "name": "APT Campaign 2024",
                        "indicators_count": 15,
                        "first_seen": "2024-01-15T00:00:00Z"
                    }
                ]
            }
            
            response = await authenticated_client.post(
                "/api/v1/threats/correlate",
                json={
                    "indicators": [
                        sample_test_data["ips"]["valid_ipv4"],
                        sample_test_data["domains"]["valid"]
                    ],
                    "correlation_type": "infrastructure",
                    "include_campaigns": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "correlation_score" in data["result"]
            assert "related_indicators" in data["result"]
    
    @pytest.mark.integration
    async def test_threat_intel_timeline(self, authenticated_client, sample_test_data):
        """Test threat intelligence timeline functionality."""
        with patch('api.services.threat_intelligence.ThreatIntelligenceService.get_timeline') as mock_timeline:
            mock_timeline.return_value = {
                "timeline": [
                    {
                        "timestamp": "2024-10-30T10:00:00Z",
                        "event": "Indicator first seen",
                        "source": "threat_feed_1",
                        "confidence": 0.85
                    },
                    {
                        "timestamp": "2024-10-30T12:00:00Z",
                        "event": "Associated campaign detected",
                        "source": "threat_feed_2",
                        "confidence": 0.92
                    }
                ],
                "total_events": 2,
                "time_range": {
                    "start": "2024-10-30T00:00:00Z",
                    "end": "2024-10-30T23:59:59Z"
                }
            }
            
            response = await authenticated_client.post(
                "/api/v1/threats/timeline",
                json={
                    "indicator": sample_test_data["ips"]["valid_ipv4"],
                    "time_range_days": 7,
                    "include_context": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "timeline" in data["result"]
            assert "total_events" in data["result"]


class TestEndToEndWorkflows:
    """End-to-end integration tests."""
    
    @pytest.mark.integration
    async def test_complete_security_validation_workflow(self, authenticated_client, sample_test_data):
        """Test complete security validation workflow."""
        # Simulate a security analyst's workflow
        email = sample_test_data["emails"]["valid"]
        domain = sample_test_data["domains"]["valid"]
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.validation.ValidationService._check_external_apis') as mock_external, \
             patch('api.services.reputation.ReputationService._query_external_apis') as mock_reputation, \
             patch('api.services.threat_intelligence.ThreatIntelligenceService._search_sources') as mock_threat:
            
            # Setup mock responses
            mock_external.return_value = {"is_valid": True, "reputation": "good"}
            mock_reputation.return_value = {"overall_score": 85, "overall_verdict": "good"}
            mock_threat.return_value = {"threats": [], "confidence": 0.1}
            
            # Step 1: Validate email
            email_response = await authenticated_client.post(
                "/api/v1/validate/email",
                json={"email": email}
            )
            assert email_response.status_code == 200
            
            # Step 2: Validate domain
            domain_response = await authenticated_client.post(
                "/api/v1/validate/domain",
                json={"domain": domain}
            )
            assert domain_response.status_code == 200
            
            # Step 3: Check reputation
            reputation_response = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "detailed": True
                }
            )
            assert reputation_response.status_code == 200
            
            # Step 4: Get threat intelligence
            threat_response = await authenticated_client.post(
                "/api/v1/threats/query",
                json={
                    "value": ip,
                    "query_type": "ip",
                    "include_context": True
                }
            )
            assert threat_response.status_code == 200
            
            # Verify all steps completed successfully
            assert email_response.json()["success"] is True
            assert domain_response.json()["success"] is True
            assert reputation_response.json()["success"] is True
            assert threat_response.json()["success"] is True
    
    @pytest.mark.integration
    async def test_bulk_security_analysis_workflow(self, authenticated_client, sample_test_data):
        """Test bulk security analysis workflow."""
        with patch('api.services.validation.ValidationService._validate_batch') as mock_validation, \
             patch('api.services.reputation.ReputationService._bulk_query') as mock_reputation, \
             patch('api.services.threat_intelligence.ThreatIntelligenceService._bulk_search') as mock_threat:
            
            # Setup mock responses for bulk processing
            mock_validation.return_value = {"valid_count": 8, "invalid_count": 2}
            mock_reputation.return_value = {"processed": 10, "good_reputation": 7, "bad_reputation": 1}
            mock_threat.return_value = {"threats_found": 2, "clean_indicators": 8}
            
            # Create bulk analysis request
            bulk_data = {
                "indicators": {
                    "emails": sample_test_data["emails"]["bulk_valid"][:5],
                    "domains": sample_test_data["domains"]["bulk"][:3],
                    "ip_addresses": sample_test_data["ips"]["bulk"][:2]
                },
                "analysis_types": ["validation", "reputation", "threat_intelligence"],
                "detailed_report": True
            }
            
            response = await authenticated_client.post(
                "/api/v1/analysis/bulk-security",
                json=bulk_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "analysis_results" in data
            assert "summary" in data
            assert "recommendations" in data
            
            # Verify bulk operations were called
            mock_validation.assert_called_once()
            mock_reputation.assert_called_once()
            mock_threat.assert_called_once()
    
    @pytest.mark.integration
    async def test_real_time_monitoring_workflow(self, authenticated_client, sample_test_data):
        """Test real-time monitoring workflow."""
        monitoring_indicators = [
            {"value": sample_test_data["ips"]["valid_ipv4"], "type": "ip"},
            {"value": sample_test_data["domains"]["valid"], "type": "domain"},
            {"value": sample_test_data["emails"]["valid"], "type": "email"}
        ]
        
        with patch('api.services.monitoring.MonitoringService.start_monitoring') as mock_start, \
             patch('api.services.monitoring.MonitoringService.get_status') as mock_status:
            
            # Start monitoring
            start_response = await authenticated_client.post(
                "/api/v1/monitoring/start",
                json={
                    "indicators": monitoring_indicators,
                    "check_interval": 300,  # 5 minutes
                    "alert_threshold": 0.7
                }
            )
            
            assert start_response.status_code == 200
            start_data = start_response.json()
            assert start_data["success"] is True
            assert "monitoring_id" in start_data
            
            # Get monitoring status
            status_response = await authenticated_client.get(
                f"/api/v1/monitoring/status/{start_data['monitoring_id']}"
            )
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["success"] is True


class TestPerformanceIntegration:
    """Integration tests for performance and load."""
    
    @pytest.mark.integration
    async def test_api_rate_limiting_integration(self, authenticated_client, sample_test_data):
        """Test API rate limiting under load."""
        email = sample_test_data["emails"]["valid"]
        
        # Make requests to test rate limiting
        responses = []
        for i in range(105):  # Exceed rate limit
            response = await authenticated_client.post(
                "/api/v1/validate/email",
                json={"email": f"test{i}@example.com"}
            )
            responses.append(response)
        
        # Verify rate limiting was triggered
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        successful_responses = [r for r in responses if r.status_code == 200]
        
        assert len(rate_limited_responses) > 0
        assert len(successful_responses) > 0
        assert len(successful_responses) <= 100  # Default rate limit
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_sustained_load_integration(self, authenticated_client, sample_test_data, performance_monitor):
        """Test sustained load on API."""
        performance_monitor.start()
        
        email = sample_test_data["emails"]["valid"]
        
        # Run sustained load for 30 seconds
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < 30:
            tasks = [
                authenticated_client.post(
                    "/api/v1/validate/email",
                    json={"email": f"load-test-{i}@example.com"}
                )
                for i in range(10)  # 10 concurrent requests
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            successful = sum(1 for r in responses if isinstance(r, dict) and r.get("status_code") == 200)
            request_count += successful
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        performance_monitor.stop()
        stats = performance_monitor.get_stats()
        
        # Verify performance metrics
        assert request_count > 100  # Should handle at least 100 requests
        assert stats["duration"] >= 30  # Should run for at least 30 seconds
        assert stats["peak_memory_percent"] < 90  # Should not use excessive memory
        assert stats["peak_cpu_percent"] < 95  # Should not max out CPU


class TestErrorHandlingIntegration:
    """Integration tests for error handling and recovery."""
    
    @pytest.mark.integration
    async def test_database_connection_recovery(self, authenticated_client, sample_test_data):
        """Test recovery from database connection issues."""
        email = sample_test_data["emails"]["valid"]
        
        with patch('api.database.connections.get_postgresql_connection') as mock_db:
            # Simulate database connection failure
            mock_db.side_effect = [
                Exception("Connection refused"),
                Exception("Connection refused"),
                AsyncMock()  # Third attempt succeeds
            ]
            
            # Should retry and eventually succeed
            response = await authenticated_client.post(
                "/api/v1/validate/email",
                json={"email": email}
            )
            
            assert response.status_code == 200
    
    @pytest.mark.integration
    async def test_external_api_failure_handling(self, authenticated_client, sample_test_data):
        """Test handling of external API failures."""
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.reputation.ReputationService._query_external_apis') as mock_api:
            # Simulate partial external API failures
            mock_api.return_value = {
                "abuseipdb": {"error": "Service unavailable"},
                "virustotal": {"reputation": 0, "detected_urls": []},
                "greynoise": {"error": "Rate limit exceeded"},
                "otx": {"pulse_info": {"count": 0}, "reputation": 0}
            }
            
            response = await authenticated_client.post(
                "/api/v1/reputation/query",
                json={
                    "value": ip,
                    "value_type": "ip",
                    "fallback_on_error": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return partial results
            assert data["success"] is True
            assert "partial_data" in data["result"]
            assert "source_errors" in data["result"]
    
    @pytest.mark.integration
    async def test_circuit_breaker_pattern(self, authenticated_client, sample_test_data):
        """Test circuit breaker pattern for external services."""
        ip = sample_test_data["ips"]["valid_ipv4"]
        
        with patch('api.services.reputation.ReputationService._query_external_apis') as mock_api:
            # Simulate consecutive failures
            mock_api.side_effect = [
                Exception("Service down") for _ in range(5)
            ] + [
                {"overall_score": 85, "overall_verdict": "good"}  # Recovery
            ]
            
            # First few requests should fail
            responses = []
            for i in range(7):
                response = await authenticated_client.post(
                    "/api/v1/reputation/query",
                    json={"value": ip, "value_type": "ip"}
                )
                responses.append(response)
            
            # First 5 should fail or return circuit breaker response
            for i in range(5):
                assert responses[i].status_code in [500, 503]
            
            # After circuit breaker opens, should return error
            assert responses[5].status_code == 503
            assert responses[6].status_code == 503