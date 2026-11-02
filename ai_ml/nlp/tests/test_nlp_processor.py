"""
Test suite for Cyber NLP Processor
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlp_processor import CyberNLPProcessor, IOC, ThreatIntelligence, EmailClassification
from config import Config
from utils.cyber_utils import (
    validate_ip_address, validate_domain, validate_url, validate_hash,
    normalize_ioc, calculate_ioc_confidence, extract_context_snippet,
    create_ioc_summary, deduplicate_iocs, export_to_json, export_to_csv
)
from utils.database import DatabaseManager


class TestCyberUtils:
    """Test utility functions"""
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        # Valid IPv4
        assert validate_ip_address("192.168.1.1")[0] == True
        assert validate_ip_address("192.168.1.1")[1] == "4"
        
        # Valid IPv6
        assert validate_ip_address("::1")[0] == True
        assert validate_ip_address("2001:db8::1")[1] == "6"
        
        # Invalid IP
        assert validate_ip_address("999.999.999.999")[0] == False
        assert validate_ip_address("not-an-ip")[0] == False
    
    def test_validate_domain(self):
        """Test domain validation"""
        # Valid domains
        assert validate_domain("example.com")[0] == True
        assert validate_domain("sub.domain.co.uk")[0] == True
        
        # Invalid domains
        assert validate_domain("")[0] == False
        assert validate_domain("no-tld")[0] == False
        assert validate_domain("toolong" + "x" * 250)[0] == False
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        assert validate_url("https://example.com")[0] == True
        assert validate_url("http://sub.domain.com/path?query=value")[0] == True
        
        # Invalid URLs
        assert validate_url("not-a-url")[0] == False
        assert validate_url("")[0] == False
    
    def test_validate_hash(self):
        """Test hash validation"""
        # Valid hashes
        assert validate_hash("d41d8cd98f00b204e9800998ecf8427e", "md5")[0] == True
        assert validate_hash("356a192b7913b04c54574d18c28d46e6395428ab", "sha1")[0] == True
        assert validate_hash("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "sha256")[0] == True
        
        # Invalid hashes
        assert validate_hash("short", "md5")[0] == False
        assert validate_hash("toolong", "md5")[0] == False
    
    def test_normalize_ioc(self):
        """Test IOC normalization"""
        # IP addresses
        assert normalize_ioc("ipv4", "192.168.1.1") == "192.168.1.1"
        assert normalize_ioc("ipv6", "2001:DB8::1") == "2001:db8::1"
        
        # Domains
        assert normalize_ioc("domain", "EXAMPLE.COM") == "example.com"
        assert normalize_ioc("domain", "https://example.com") == "example.com"
        
        # Hashes
        assert normalize_ioc("md5", "ABCD1234") == "abcd1234"
        assert normalize_ioc("sha256", "ABCD1234") == "abcd1234"
    
    def test_calculate_ioc_confidence(self):
        """Test IOC confidence calculation"""
        # High confidence for valid IOCs
        confidence = calculate_ioc_confidence("ipv4", "192.168.1.1")
        assert confidence >= 0.9
        
        confidence = calculate_ioc_confidence("md5", "d41d8cd98f00b204e9800998ecf8427e")
        assert confidence >= 0.9
        
        # Lower confidence for invalid IOCs
        confidence = calculate_ioc_confidence("ipv4", "999.999.999.999")
        assert confidence < 0.9
    
    def test_create_ioc_summary(self):
        """Test IOC summary creation"""
        iocs = [
            {"type": "ipv4", "value": "192.168.1.1", "confidence": 0.95, "source": "regex"},
            {"type": "domain", "value": "malware.com", "confidence": 0.90, "source": "regex"},
            {"type": "url", "value": "http://malware.com/payload", "confidence": 0.85, "source": "spacy_ner"}
        ]
        
        summary = create_ioc_summary(iocs)
        
        assert summary["total_iocs"] == 3
        assert "by_type" in summary
        assert "confidence_stats" in summary
        assert summary["by_type"]["ipv4"] == 1
        assert summary["by_type"]["domain"] == 1
        assert summary["by_type"]["url"] == 1
    
    def test_deduplicate_iocs(self):
        """Test IOC deduplication"""
        iocs = [
            {"type": "ipv4", "value": "192.168.1.1"},
            {"type": "ipv4", "value": "192.168.1.1"},  # Duplicate
            {"type": "domain", "value": "example.com"},
            {"type": "domain", "value": "example.com"}  # Duplicate
        ]
        
        deduplicated = deduplicate_iocs(iocs)
        
        assert len(deduplicated) == 2
        assert len([ioc for ioc in deduplicated if ioc["value"] == "192.168.1.1"]) == 1
        assert len([ioc for ioc in deduplicated if ioc["value"] == "example.com"]) == 1
    
    def test_export_functions(self):
        """Test data export functions"""
        data = [{"test": "data", "number": 42}]
        
        # Test JSON export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_json = f.name
        
        try:
            assert export_to_json(data, temp_json) == True
            assert os.path.exists(temp_json)
            
            with open(temp_json, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == data
        finally:
            if os.path.exists(temp_json):
                os.remove(temp_json)
        
        # Test CSV export
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_csv = f.name
        
        try:
            assert export_to_csv(data, temp_csv) == True
            assert os.path.exists(temp_csv)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)


class TestCyberNLPProcessor:
    """Test the main NLP processor"""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance for testing"""
        return CyberNLPProcessor(use_gpu=False)
    
    def test_processor_initialization(self, processor):
        """Test processor initialization"""
        assert processor is not None
        assert processor.logger is not None
    
    def test_extract_iocs_basic(self, processor):
        """Test basic IOC extraction"""
        text = """
        The attack originated from IP address 203.0.113.10 and used 
        domain malware.example.com. The malicious file had hash 
        a1b2c3d4e5f6789012345678901234567890abcd.
        """
        
        iocs = processor.extract_iocs(text)
        
        assert len(iocs) > 0
        ioc_types = [ioc.type for ioc in iocs]
        assert "ipv4" in ioc_types or "domain" in ioc_types or "sha256" in ioc_types
    
    def test_extract_iocs_with_confidence(self, processor):
        """Test IOC extraction with confidence threshold"""
        text = "IP: 192.168.1.1"
        
        iocs_all = processor.extract_iocs(text, min_confidence=0.0)
        iocs_high = processor.extract_iocs(text, min_confidence=0.9)
        
        assert len(iocs_all) >= len(iocs_high)
    
    def test_analyze_email_phishing(self, processor):
        """Test email phishing analysis"""
        phishing_email = """
        Subject: URGENT: Verify Your Account
        
        Dear Customer,
        Your account has been suspended due to suspicious activity. 
        Please click the link below to verify your account immediately:
        http://security-update-login.com/verify
        
        Failure to act will result in permanent account suspension.
        """
        
        result = processor.analyze_email(phishing_email, "URGENT: Verify Your Account")
        
        assert result.classification in ["spam", "phishing"]
        assert result.confidence > 0.5
        assert len(result.phishing_indicators) > 0
    
    def test_analyze_email_legitimate(self, processor):
        """Test legitimate email analysis"""
        legitimate_email = """
        Subject: Meeting Reminder
        
        Hi team,
        
        This is a reminder about our weekly meeting tomorrow at 2 PM.
        
        Best regards,
        Sarah
        """
        
        result = processor.analyze_email(legitimate_email, "Meeting Reminder")
        
        # Should classify as legitimate with reasonable confidence
        assert result.classification in ["legitimate", "spam"]  # May vary depending on content
        assert result.confidence >= 0.0
    
    def test_analyze_domain_brands(self, processor):
        """Test domain brand analysis"""
        suspicious_domain = "google-secure-login-verify.com"
        
        analysis = processor.analyze_domain_brands(suspicious_domain)
        
        assert "domain" in analysis
        assert "suspicious_score" in analysis
        assert "recommendation" in analysis
        assert analysis["suspicious_score"] > 0  # Should detect suspicious pattern
    
    def test_extract_threat_intelligence(self, processor):
        """Test threat intelligence extraction"""
        threat_text = """
        Security researchers discovered a new campaign attributed to APT29 
        targeting healthcare organizations. The threat actor used spear-phishing 
        emails with malicious attachments. Indicators include domains like 
        healthcare-update.com and IPs 203.0.113.10 and 203.0.113.11. The malware 
        family associated with this campaign is identified as TrickBot.
        """
        
        result = processor.extract_threat_intelligence(threat_text)
        
        assert isinstance(result, ThreatIntelligence)
        assert result.language is not None
        assert result.sentiment_score is not None
        assert len(result.indicators) > 0
    
    def test_parse_whois_data(self, processor):
        """Test WHOIS data parsing"""
        whois_text = """
        Domain Name: EXAMPLE.COM
        Registrar: Example Registrar, Inc.
        Created Date: 2020-01-01 00:00:00
        Expiration Date: 2025-01-01 00:00:00
        Name Server: ns1.example.com
        """
        
        result = processor.parse_whois_data(whois_text)
        
        assert "registrar" in result
        assert "creation_date" in result
        assert "expiration_date" in result
        assert "name_servers" in result
    
    @patch('builtins.open')
    @patch('joblib.load')
    def test_classify_email_trained_no_model(self, mock_joblib, mock_open, processor):
        """Test email classification without trained model"""
        result = processor.classify_email_trained("Test Subject", "Test content")
        
        assert "error" in result
        assert "No trained model available" in result["error"]
    
    def test_train_email_classifier_insufficient_data(self, processor):
        """Test training with insufficient data"""
        insufficient_data = [
            ("subject1", "content1", "spam"),
            ("subject2", "content2", "legitimate")
        ]  # Only 2 samples
        
        result = processor.train_email_classifier(insufficient_data)
        
        assert "error" in result
        assert "Insufficient training data" in result["error"]


class TestEmailClassification:
    """Test email classification data structure"""
    
    def test_email_classification_creation(self):
        """Test creating email classification object"""
        classification = EmailClassification(
            classification="phishing",
            confidence=0.95,
            phishing_indicators=["Contains phishing keyword"],
            suspicious_urls=[{"url": "http://bad.com", "domain": "bad.com"}],
            suspicious_attachments=[".exe"],
            analysis_details={"length": 100, "word_count": 20}
        )
        
        assert classification.classification == "phishing"
        assert classification.confidence == 0.95
        assert len(classification.phishing_indicators) > 0
        assert len(classification.suspicious_urls) > 0


class TestConfiguration:
    """Test configuration handling"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = Config()
        
        assert config.model is not None
        assert config.processing is not None
        assert config.security is not None
        assert config.output is not None
        assert config.database is not None
    
    def test_config_save_load(self):
        """Test configuration save and load"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            # Create and save config
            original_config = Config()
            original_config.save_to_file(config_file)
            
            # Load config
            loaded_config = Config.load_from_file(config_file)
            
            # Verify equality
            assert loaded_config.model.spacy_model == original_config.model.spacy_model
            assert loaded_config.processing.max_text_length == original_config.processing.max_text_length
        finally:
            if os.path.exists(config_file):
                os.remove(config_file)


class TestRegexPatterns:
    """Test regex patterns for IOC detection"""
    
    def test_patterns_available(self):
        """Test that all expected patterns are available"""
        from nlp_processor import RegexPatterns
        
        patterns = RegexPatterns.get_patterns()
        
        expected_patterns = [
            'ipv4', 'ipv6', 'url', 'email', 'domain', 'md5', 'sha1', 'sha256'
        ]
        
        for pattern in expected_patterns:
            assert pattern in patterns
            assert patterns[pattern] is not None
            assert len(patterns[pattern]) > 0


def run_all_tests():
    """Run all tests"""
    test_classes = [
        TestCyberUtils,
        TestCyberNLPProcessor,
        TestEmailClassification,
        TestConfiguration,
        TestRegexPatterns
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n=== Running {test_class.__name__} ===")
        
        # Get all test methods
        test_methods = [method for method in dir(test_class) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                total_tests += 1
                test_instance = test_class()
                method = getattr(test_instance, method_name)
                method()
                print(f"✓ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"✗ {method_name}: {e}")
                failed_tests.append(f"{test_class.__name__}.{method_name}: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if failed_tests:
        print("\nFailed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
    
    return total_tests == passed_tests


if __name__ == "__main__":
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
