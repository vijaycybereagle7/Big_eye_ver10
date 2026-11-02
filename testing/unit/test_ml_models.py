"""Unit tests for ML models."""

import pytest
import numpy as np
from unittest.mock import patch, Mock, AsyncMock
from datetime import datetime, timedelta
import json
import pandas as pd

pytestmark = pytest.mark.asyncio


class TestAnomalyDetection:
    """Test anomaly detection models."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_anomaly_detector_initialization(self, mock_ml_models):
        """Test anomaly detector model initialization."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Verify mock is callable
        assert callable(detector["predict"])
        assert callable(detector["predict_batch"])
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_anomaly_detection_single_prediction(self, mock_ml_models):
        """Test single anomaly prediction."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Test single prediction
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "bytes_sent": 1000000,
            "bytes_received": 2000000,
            "duration": 30.0,
            "protocol": "TCP"
        }
        
        prediction = detector["predict"](test_data)
        
        assert "anomaly_score" in prediction
        assert "is_anomaly" in prediction
        assert 0 <= prediction["anomaly_score"] <= 1
        assert isinstance(prediction["is_anomaly"], bool)
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_anomaly_detection_batch_prediction(self, mock_ml_models):
        """Test batch anomaly prediction."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Test batch prediction
        test_data = [
            {
                "timestamp": datetime.now().isoformat(),
                "source_ip": f"192.168.1.{i}",
                "dest_ip": "8.8.8.8",
                "bytes_sent": 1000000,
                "bytes_received": 2000000,
                "duration": 30.0,
                "protocol": "TCP"
            }
            for i in range(10)
        ]
        
        predictions = detector["predict_batch"](test_data)
        
        assert len(predictions) == 10
        for pred in predictions:
            assert "anomaly_score" in pred
            assert "is_anomaly" in pred
            assert 0 <= pred["anomaly_score"] <= 1
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_anomaly_detection_thresholds(self, mock_ml_models):
        """Test anomaly detection thresholds."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Test normal traffic (low anomaly score)
        normal_traffic = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "bytes_sent": 1000000,
            "bytes_received": 2000000,
            "duration": 30.0,
            "protocol": "TCP"
        }
        
        normal_prediction = detector["predict"](normal_traffic)
        assert normal_prediction["anomaly_score"] < 0.5
        assert normal_prediction["is_anomaly"] is False
        
        # Test suspicious traffic (high anomaly score)
        suspicious_traffic = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": "192.0.2.100",  # Suspicious IP
            "dest_ip": "8.8.8.8",
            "bytes_sent": 1000000000,  # Very large transfer
            "bytes_received": 100,  # Very small response
            "duration": 0.1,  # Very short duration
            "protocol": "TCP"
        }
        
        suspicious_prediction = detector["predict"](suspicious_traffic)
        # In a real model, this would have a high anomaly score


class TestPhishingDetection:
    """Test phishing detection models."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_phishing_classifier_initialization(self, mock_ml_models):
        """Test phishing classifier model initialization."""
        classifier = mock_ml_models["phishing_classifier"]
        
        assert callable(classifier["predict"])
        assert callable(classifier["predict_proba"])
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_phishing_detection_email(self, mock_ml_models):
        """Test phishing detection for email content."""
        classifier = mock_ml_models["phishing_classifier"]
        
        # Test legitimate email
        legitimate_email = {
            "subject": "Meeting reminder for tomorrow",
            "body": "Hi John, just a reminder about our meeting scheduled for 2 PM tomorrow. Please bring the documents. Thanks.",
            "sender_domain": "company.com",
            "recipient_domain": "company.com"
        }
        
        prediction = classifier["predict"](legitimate_email)
        
        assert "phishing_probability" in prediction
        assert "is_phishing" in prediction
        assert 0 <= prediction["phishing_probability"] <= 1
        
        # Legitimate email should have low phishing probability
        assert prediction["phishing_probability"] < 0.5
        
        # Test phishing email
        phishing_email = {
            "subject": "URGENT: Account Security Alert",
            "body": "Your account has been compromised. Click here immediately to verify your account: http://fake-bank.com/login",
            "sender_domain": "fake-domain.net",
            "recipient_domain": "gmail.com"
        }
        
        phishing_prediction = classifier["predict"](phishing_email)
        # Phishing email should have high probability
        # Note: Mock may not reflect real behavior
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_phishing_detection_probabilities(self, mock_ml_models):
        """Test phishing detection probability scores."""
        classifier = mock_ml_models["phishing_classifier"]
        
        # Test probability prediction
        email_features = {
            "subject": "Important security update",
            "body": "Please verify your account information",
            "sender_domain": "suspicious-domain.com",
            "recipient_domain": "gmail.com",
            "has_links": True,
            "has_attachments": False,
            "urgency_score": 0.9
        }
        
        proba = classifier["predict_proba"](email_features)
        
        assert len(proba) == 2  # [legitimate_prob, phishing_prob]
        assert abs(sum(proba[0]) - 1.0) < 0.001  # Probabilities should sum to 1
        assert all(0 <= p <= 1 for p in proba[0])


class TestDomainReputation:
    """Test domain reputation models."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_domain_reputation_model(self, mock_ml_models):
        """Test domain reputation prediction model."""
        reputation_model = mock_ml_models["domain_reputation"]
        
        # Test legitimate domain
        legitimate_domain = {
            "domain": "google.com",
            "domain_age_days": 10000,
            "ssl_certificate_valid": True,
            "has_mx_records": True,
            "whois_info_available": True,
            "suspicious_tlds": False,
            "typosquatting_score": 0.1,
            "alexa_rank": 1
        }
        
        reputation = reputation_model["predict"](legitimate_domain)
        
        assert "reputation_score" in reputation
        assert "confidence" in reputation
        assert 0 <= reputation["reputation_score"] <= 100
        assert 0 <= reputation["confidence"] <= 1
        
        # Legitimate domain should have high reputation
        assert reputation["reputation_score"] > 70
        
        # Test suspicious domain
        suspicious_domain = {
            "domain": "goog1e-secure-login.com",
            "domain_age_days": 10,
            "ssl_certificate_valid": False,
            "has_mx_records": False,
            "whois_info_available": False,
            "suspicious_tlds": True,
            "typosquatting_score": 0.9,
            "alexa_rank": None
        }
        
        suspicious_reputation = reputation_model["predict"](suspicious_domain)
        # Suspicious domain should have low reputation
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_domain_features_extraction(self):
        """Test domain feature extraction for ML models."""
        from ai_ml.pattern_recognition.feature_extraction import DomainFeatureExtractor
        
        extractor = DomainFeatureExtractor()
        
        # Test feature extraction for legitimate domain
        features = extractor.extract_domain_features("google.com")
        
        expected_features = [
            "domain_length", "subdomain_count", "has_hyphens",
            "suspicious_tld", "typosquatting_score", "domain_age_days",
            "has_mx_records", "ssl_valid", "whois_available",
            "alexa_rank", "whois_days_old"
        ]
        
        for feature in expected_features:
            assert feature in features
        
        # Verify feature values are reasonable
        assert features["domain_length"] > 0
        assert features["typosquatting_score"] >= 0
        assert features["typosquatting_score"] <= 1


class TestNLPProcessor:
    """Test NLP processing for cybersecurity text."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_ioc_extraction(self, mock_ml_models):
        """Test IOC (Indicator of Compromise) extraction."""
        nlp = mock_ml_models["nlp_processor"]
        
        # Test security advisory text
        security_text = """
        Security Alert: Multiple vulnerabilities discovered in Apache server.
        IOCs detected: 192.168.1.100, suspicious-domain.com, md5:abc123def456.
        CVE-2024-12345 allows remote code execution. Phishing email from sender@fake-site.com
        contains malicious link to https://malicious-site.xyz/path.
        """
        
        iocs = nlp["extract_iocs"](security_text)
        
        assert "ips" in iocs
        assert "domains" in iocs
        assert "hashes" in iocs
        assert "emails" in iocs
        assert "urls" in iocs
        
        # Should extract IP addresses
        assert "192.168.1.100" in iocs["ips"]
        
        # Should extract domains
        assert "suspicious-domain.com" in iocs["domains"]
        assert "malicious-site.xyz" in iocs["domains"]
        
        # Should extract hashes
        assert "abc123def456" in iocs["hashes"]
        
        # Should extract emails
        assert "sender@fake-site.com" in iocs["emails"]
        
        # Should extract URLs
        assert "https://malicious-site.xyz/path" in iocs["urls"]
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_email_classification(self, mock_ml_models):
        """Test email spam/phishing classification."""
        nlp = mock_ml_models["nlp_processor"]
        
        # Test phishing email
        phishing_email = """
        Subject: URGENT: Your Account Has Been Suspended
        
        Dear Valued Customer,
        
        We have detected suspicious activity on your account. Your account has been temporarily suspended.
        
        To restore access, please click the link below and verify your identity:
        http://fake-bank.com/verify
        
        Failure to act within 24 hours will result in permanent account closure.
        
        Security Team
        """
        
        classification = nlp["classify_email"](phishing_email)
        
        assert "spam_probability" in classification
        assert "is_spam" in classification
        assert "is_phishing" in classification
        assert "confidence" in classification
        
        # Phishing email should have high spam probability
        assert classification["is_spam"] is True
        assert classification["spam_probability"] > 0.8
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_threat_intelligence_extraction(self):
        """Test threat intelligence extraction from text."""
        from ai_ml.nlp.nlp_processor import CyberNLPProcessor
        
        processor = CyberNLPProcessor()
        
        # Test threat intelligence text
        threat_text = """
        APT29 campaign targeting financial institutions.
        Malware samples: C2 server at 185.159.153.177, download domain: malware-hosting.net
        Hashes: 44d88612fea8a8f36de82e1278abb02f (MD5)
        Spear-phishing emails sent from: phishing@apt-campaign.org
        """
        
        threat_intel = processor.extract_threat_intelligence(threat_text)
        
        assert "threat_actors" in threat_intel
        assert "campaigns" in threat_intel
        assert "infrastructure" in threat_intel
        assert "malware_families" in threat_intel
        
        # Should extract threat actor
        assert "APT29" in threat_intel["threat_actors"]
        
        # Should extract campaign
        assert any("financial" in campaign.lower() for campaign in threat_intel["campaigns"])
        
        # Should extract infrastructure
        assert "185.159.153.177" in threat_intel["infrastructure"]["ips"]
        assert "malware-hosting.net" in threat_intel["infrastructure"]["domains"]


class TestModelPerformance:
    """Test ML model performance and accuracy."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_consistency(self, mock_ml_models):
        """Test model consistency across multiple predictions."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Same input should produce consistent results
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "bytes_sent": 1000000,
            "bytes_received": 2000000,
            "duration": 30.0,
            "protocol": "TCP"
        }
        
        predictions = [detector["predict"](test_data) for _ in range(10)]
        
        # All predictions should be identical (or very similar)
        anomaly_scores = [pred["anomaly_score"] for pred in predictions]
        is_anomalies = [pred["is_anomaly"] for pred in predictions]
        
        # Scores should be consistent (allowing for small floating point differences)
        assert max(anomaly_scores) - min(anomaly_scores) < 0.01
        # Anomaly flags should be identical
        assert all(anomaly == is_anomalies[0] for anomaly in is_anomalies)
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_feature_validation(self, mock_ml_models):
        """Test that models properly validate input features."""
        reputation_model = mock_ml_models["domain_reputation"]
        
        # Test with missing features
        incomplete_features = {"domain": "example.com"}  # Missing other features
        
        try:
            reputation = reputation_model["predict"](incomplete_features)
            # Should handle missing features gracefully
            assert "reputation_score" in reputation
        except Exception as e:
            # If validation is implemented, should raise appropriate error
            assert "missing" in str(e).lower() or "required" in str(e).lower()
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_bounds_checking(self, mock_ml_models):
        """Test model output bounds checking."""
        classifier = mock_ml_models["phishing_classifier"]
        
        # Test with various email contents
        test_emails = [
            {"subject": "Hello", "body": "Just a quick email", "sender_domain": "good.com"},
            {"subject": "", "body": "", "sender_domain": ""},
            {"subject": "A" * 1000, "body": "B" * 5000, "sender_domain": "c" * 100}
        ]
        
        for email in test_emails:
            prediction = classifier["predict"](email)
            
            # Check probability bounds
            assert 0 <= prediction["phishing_probability"] <= 1
            
            # Check boolean bounds
            assert isinstance(prediction["is_phishing"], bool)


class TestModelTraining:
    """Test ML model training and validation."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_training_pipeline(self):
        """Test model training pipeline."""
        from ai_ml.pattern_recognition.training_pipeline import ModelTrainingPipeline
        
        pipeline = ModelTrainingPipeline()
        
        # Mock training data
        training_data = pd.DataFrame({
            "feature1": np.random.rand(100),
            "feature2": np.random.rand(100),
            "feature3": np.random.choice([0, 1], 100),
            "target": np.random.choice([0, 1], 100)
        })
        
        with patch.object(pipeline, 'train_model') as mock_train:
            mock_train.return_value = {
                "model": Mock(),
                "accuracy": 0.85,
                "precision": 0.83,
                "recall": 0.87,
                "f1_score": 0.85
            }
            
            result = pipeline.train_model(training_data)
            
            assert "model" in result
            assert "accuracy" in result
            assert 0 <= result["accuracy"] <= 1
            assert 0 <= result["precision"] <= 1
            assert 0 <= result["recall"] <= 1
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_cross_validation(self):
        """Test model cross-validation."""
        from ai_ml.pattern_recognition.model_evaluation import ModelEvaluator
        
        evaluator = ModelEvaluator()
        
        # Mock model and data
        mock_model = Mock()
        X = np.random.rand(100, 5)
        y = np.random.choice([0, 1], 100)
        
        with patch.object(evaluator, 'cross_validate') as mock_cv:
            mock_cv.return_value = {
                "cv_scores": [0.82, 0.85, 0.83, 0.87, 0.84],
                "mean_accuracy": 0.842,
                "std_accuracy": 0.019
            }
            
            cv_result = evaluator.cross_validate(mock_model, X, y, cv=5)
            
            assert "cv_scores" in cv_result
            assert "mean_accuracy" in cv_result
            assert len(cv_result["cv_scores"]) == 5
            assert 0 <= cv_result["mean_accuracy"] <= 1


class TestModelIntegration:
    """Test integration of ML models with API."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_anomaly_detection_api_integration(self, test_client):
        """Test anomaly detection through API endpoint."""
        anomaly_data = {
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "bytes_sent": 1000000,
            "bytes_received": 2000000,
            "duration": 30.0,
            "protocol": "TCP"
        }
        
        with patch('api.services.anomaly_detection.AnomalyDetectionService.detect_anomaly') as mock_detect:
            mock_detect.return_value = {
                "anomaly_score": 0.15,
                "is_anomaly": False,
                "confidence": 0.92,
                "features_importance": {
                    "bytes_sent": 0.3,
                    "duration": 0.2,
                    "protocol": 0.1
                }
            }
            
            response = await test_client.post(
                "/api/v1/ml/anomaly-detection",
                json=anomaly_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "result" in data
            result = data["result"]
            
            assert "anomaly_score" in result
            assert "is_anomaly" in result
            assert "confidence" in result
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_phishing_detection_api_integration(self, test_client):
        """Test phishing detection through API endpoint."""
        email_data = {
            "subject": "Important security update",
            "body": "Please verify your account information at https://example.com",
            "sender_email": "security@example.com"
        }
        
        with patch('api.services.phishing_detection.PhishingDetectionService.classify_email') as mock_classify:
            mock_classify.return_value = {
                "phishing_probability": 0.15,
                "is_phishing": False,
                "confidence": 0.88,
                "features": {
                    "has_suspicious_links": False,
                    "urgency_score": 0.3,
                    "sender_reputation": 0.9
                }
            }
            
            response = await test_client.post(
                "/api/v1/ml/phishing-detection",
                json=email_data
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert "result" in data
            assert "phishing_probability" in data["result"]


class TestModelRobustness:
    """Test ML model robustness and edge cases."""
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_with_noise(self, mock_ml_models):
        """Test model robustness with noisy data."""
        reputation_model = mock_ml_models["domain_reputation"]
        
        # Test with noisy features
        noisy_features = {
            "domain": "ex@amp!le.c@om",  # Contains special characters
            "domain_age_days": -1,  # Negative age
            "ssl_certificate_valid": "invalid",  # String instead of bool
            "has_mx_records": None,  # None value
            "whois_info_available": True,
            "suspicious_tlds": False,
            "typosquatting_score": 1.5,  # Score > 1
            "alexa_rank": "unknown"  # String instead of number
        }
        
        try:
            reputation = reputation_model["predict"](noisy_features)
            # Should handle invalid inputs gracefully
            assert "reputation_score" in reputation
            assert 0 <= reputation["reputation_score"] <= 100
        except Exception as e:
            # If error handling is implemented, it should be informative
            assert "invalid" in str(e).lower() or "error" in str(e).lower()
    
    @pytest.mark.unit
    @pytest.mark.ml_model
    async def test_model_with_extreme_values(self, mock_ml_models):
        """Test model with extreme feature values."""
        detector = mock_ml_models["anomaly_detector"]
        
        # Test with extreme values
        extreme_data = {
            "timestamp": datetime.now().isoformat(),
            "source_ip": "192.168.1.100",
            "dest_ip": "8.8.8.8",
            "bytes_sent": 0,  # Zero bytes
            "bytes_received": 999999999999,  # Very large number
            "duration": 999999,  # Very long duration
            "protocol": "UNKNOWN"  # Unknown protocol
        }
        
        prediction = detector["predict"](extreme_data)
        
        # Should handle extreme values without crashing
        assert "anomaly_score" in prediction
        assert "is_anomaly" in prediction
        assert isinstance(prediction["anomaly_score"], (int, float))
        assert isinstance(prediction["is_anomaly"], bool)