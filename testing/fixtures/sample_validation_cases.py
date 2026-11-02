"""Sample validation test cases with known good/bad data."""

import pytest
from typing import Dict, Any, List


class ValidationTestCases:
    """Collection of validation test cases with known outcomes."""
    
    # Email validation test cases
    EMAIL_TEST_CASES = {
        "valid_emails": [
            {
                "email": "user@example.com",
                "expected": {"is_valid": True, "confidence": 0.95},
                "description": "Standard valid email"
            },
            {
                "email": "test.user@subdomain.example.com",
                "expected": {"is_valid": True, "confidence": 0.90},
                "description": "Email with subdomain"
            },
            {
                "email": "admin+tag@company.org",
                "expected": {"is_valid": True, "confidence": 0.90},
                "description": "Email with plus addressing"
            },
            {
                "email": "user123@domain-with-dash.net",
                "expected": {"is_valid": True, "confidence": 0.90},
                "description": "Email with dash in domain"
            },
            {
                "email": "a@b.co",
                "expected": {"is_valid": True, "confidence": 0.85},
                "description": "Short but valid email"
            },
            {
                "email": "very.long.email.address.with.many.parts@example.com",
                "expected": {"is_valid": True, "confidence": 0.90},
                "description": "Long email address"
            },
            {
                "email": "user123@example123.com",
                "expected": {"is_valid": True, "confidence": 0.90},
                "description": "Email with numbers"
            }
        ],
        
        "invalid_emails": [
            {
                "email": "invalid-email",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Missing @ symbol"
            },
            {
                "email": "@example.com",
                "expected": {"is_valid": False, "confidence": 0.05},
                "description": "Missing local part"
            },
            {
                "email": "user@",
                "expected": {"is_valid": False, "confidence": 0.05},
                "description": "Missing domain"
            },
            {
                "email": "user@@example.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Double @ symbol"
            },
            {
                "email": "user..user@example.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Double dots in local part"
            },
            {
                "email": ".user@example.com",
                "expected": {"is_valid": False, "confidence": 0.15},
                "description": "Leading dot in local part"
            },
            {
                "email": "user.@example.com",
                "expected": {"is_valid": False, "confidence": 0.15},
                "description": "Trailing dot in local part"
            },
            {
                "email": "user@.example.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Leading dot in domain"
            },
            {
                "email": "user@example.com.",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Trailing dot in domain"
            },
            {
                "email": "user@-example.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Leading dash in domain"
            },
            {
                "email": "user@example-.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Trailing dash in domain"
            },
            {
                "email": "user@exam ple.com",
                "expected": {"is_valid": False, "confidence": 0.10},
                "description": "Space in domain"
            },
            {
                "email": "user@",
                "expected": {"is_valid": False, "confidence": 0.05},
                "description": "Incomplete email"
            },
            {
                "email": "",
                "expected": {"is_valid": False, "confidence": 0.00},
                "description": "Empty email"
            },
            {
                "email": "user@",
                "expected": {"is_valid": False, "confidence": 0.05},
                "description": "Domain missing TLD"
            }
        ],
        
        "suspicious_emails": [
            {
                "email": "security@paypal-secure-verify.com",
                "expected": {"is_suspicious": True, "reason": "phishing_pattern"},
                "description": "Phishing pattern - PayPal"
            },
            {
                "email": "admin@update-credentials.net",
                "expected": {"is_suspicious": True, "reason": "credential_harvesting"},
                "description": "Credential harvesting pattern"
            },
            {
                "email": "support@bank-security-alert.org",
                "expected": {"is_suspicious": True, "reason": "bank_phishing"},
                "description": "Bank phishing pattern"
            },
            {
                "email": "alert@urgent-account-suspension.com",
                "expected": {"is_suspicious": True, "reason": "urgency_tactics"},
                "description": "Urgency tactics pattern"
            },
            {
                "email": "verify@secure-login-update.net",
                "expected": {"is_suspicious": True, "reason": "fake_security"},
                "description": "Fake security update pattern"
            }
        ],
        
        "disposable_emails": [
            {
                "email": "user@10minutemail.com",
                "expected": {"is_disposable": True, "disposable_provider": "10minutemail"},
                "description": "10 Minute Mail"
            },
            {
                "email": "temp@guerrillamail.com",
                "expected": {"is_disposable": True, "disposable_provider": "guerrillamail"},
                "description": "Guerrilla Mail"
            },
            {
                "email": "test@mailinator.com",
                "expected": {"is_disposable": True, "disposable_provider": "mailinator"},
                "description": "Mailinator"
            },
            {
                "email": "disposable@temp-mail.org",
                "expected": {"is_disposable": True, "disposable_provider": "temp-mail"},
                "description": "Temp Mail"
            },
            {
                "email": "random@yopmail.com",
                "expected": {"is_disposable": True, "disposable_provider": "yopmail"},
                "description": "Yopmail"
            }
        ]
    }
    
    # Domain validation test cases
    DOMAIN_TEST_CASES = {
        "valid_domains": [
            {
                "domain": "example.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Standard valid domain"
            },
            {
                "domain": "subdomain.example.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Domain with subdomain"
            },
            {
                "domain": "example-domain.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Domain with dash"
            },
            {
                "domain": "123domain.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Domain starting with numbers"
            },
            {
                "domain": "domain123.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Domain with numbers"
            },
            {
                "domain": "a.b.c.d.e.f.com",
                "expected": {"is_valid": True, "has_dns": True, "has_mx": True},
                "description": "Domain with many subdomains"
            }
        ],
        
        "invalid_domains": [
            {
                "domain": "invalid..domain.com",
                "expected": {"is_valid": False, "reason": "double_dots"},
                "description": "Double dots"
            },
            {
                "domain": ".domain.com",
                "expected": {"is_valid": False, "reason": "leading_dot"},
                "description": "Leading dot"
            },
            {
                "domain": "domain.com.",
                "expected": {"is_valid": False, "reason": "trailing_dot"},
                "description": "Trailing dot"
            },
            {
                "domain": "-domain.com",
                "expected": {"is_valid": False, "reason": "leading_dash"},
                "description": "Leading dash"
            },
            {
                "domain": "domain-.com",
                "expected": {"is_valid": False, "reason": "trailing_dash"},
                "description": "Trailing dash"
            },
            {
                "domain": "dom ain.com",
                "expected": {"is_valid": False, "reason": "contains_space"},
                "description": "Contains space"
            },
            {
                "domain": "domain",
                "expected": {"is_valid": False, "reason": "missing_tld"},
                "description": "Missing TLD"
            },
            {
                "domain": "",
                "expected": {"is_valid": False, "reason": "empty"},
                "description": "Empty domain"
            },
            {
                "domain": "192.168.1.1",
                "expected": {"is_valid": False, "reason": "ip_address"},
                "description": "IP address instead of domain"
            },
            {
                "domain": "domain@invalid.com",
                "expected": {"is_valid": False, "reason": "contains_at_symbol"},
                "description": "Contains @ symbol"
            }
        ],
        
        "suspicious_domains": [
            {
                "domain": "paypal-secure-login.net",
                "expected": {"is_suspicious": True, "suspicious_pattern": "brand_impersonation"},
                "description": "PayPal brand impersonation"
            },
            {
                "domain": "banking-security-alert.org",
                "expected": {"is_suspicious": True, "suspicious_pattern": "financial_phishing"},
                "description": "Financial phishing domain"
            },
            {
                "domain": "secure-update-required.com",
                "expected": {"is_suspicious": True, "suspicious_pattern": "update_scam"},
                "description": "Update scam domain"
            },
            {
                "domain": "account-verify-now.net",
                "expected": {"is_suspicious": True, "suspicious_pattern": "verification_scam"},
                "description": "Verification scam domain"
            },
            {
                "domain": "microsoft-security-check.com",
                "expected": {"is_suspicious": True, "suspicious_pattern": "tech_support_scam"},
                "description": "Tech support scam domain"
            },
            {
                "domain": "urgent-account-suspension.com",
                "expected": {"is_suspicious": True, "suspicious_pattern": "urgency_tactics"},
                "description": "Urgency tactics domain"
            }
        ],
        
        "parked_domains": [
            {
                "domain": "example-parked-domain.com",
                "expected": {"is_parked": True, "parking_service": "sedo"},
                "description": "Sedo parked domain"
            },
            {
                "domain": "unused-domain-for-sale.com",
                "expected": {"is_parked": True, "parking_service": "afternic"},
                "description": "Afternic parked domain"
            }
        ]
    }
    
    # IP address validation test cases
    IP_TEST_CASES = {
        "valid_ipv4": [
            {
                "ip": "192.168.1.1",
                "expected": {"is_valid": True, "version": 4, "is_private": True},
                "description": "Private IP range"
            },
            {
                "ip": "8.8.8.8",
                "expected": {"is_valid": True, "version": 4, "is_public": True},
                "description": "Public IP - Google DNS"
            },
            {
                "ip": "1.1.1.1",
                "expected": {"is_valid": True, "version": 4, "is_public": True},
                "description": "Public IP - Cloudflare"
            },
            {
                "ip": "10.0.0.1",
                "expected": {"is_valid": True, "version": 4, "is_private": True},
                "description": "Private IP range 10.0.0.0/8"
            },
            {
                "ip": "172.16.0.1",
                "expected": {"is_valid": True, "version": 4, "is_private": True},
                "description": "Private IP range 172.16.0.0/12"
            },
            {
                "ip": "127.0.0.1",
                "expected": {"is_valid": True, "version": 4, "is_loopback": True},
                "description": "Loopback address"
            },
            {
                "ip": "169.254.1.1",
                "expected": {"is_valid": True, "version": 4, "is_link_local": True},
                "description": "Link-local address"
            }
        ],
        
        "valid_ipv6": [
            {
                "ip": "2001:4860:4860::8888",
                "expected": {"is_valid": True, "version": 6, "is_public": True},
                "description": "IPv6 Google DNS"
            },
            {
                "ip": "::1",
                "expected": {"is_valid": True, "version": 6, "is_loopback": True},
                "description": "IPv6 loopback"
            },
            {
                "ip": "fe80::1",
                "expected": {"is_valid": True, "version": 6, "is_link_local": True},
                "description": "IPv6 link-local"
            },
            {
                "ip": "fc00::1",
                "expected": {"is_valid": True, "version": 6, "is_private": True},
                "description": "IPv6 unique local"
            }
        ],
        
        "invalid_ips": [
            {
                "ip": "999.999.999.999",
                "expected": {"is_valid": False, "reason": "out_of_range"},
                "description": "IPv4 octets out of range"
            },
            {
                "ip": "256.1.1.1",
                "expected": {"is_valid": False, "reason": "octet_too_large"},
                "description": "IPv4 octet > 255"
            },
            {
                "ip": "192.168.1",
                "expected": {"is_valid": False, "reason": "incomplete"},
                "description": "Incomplete IPv4"
            },
            {
                "ip": "192.168.1.1.1",
                "expected": {"is_valid": False, "reason": "too_many_octets"},
                "description": "Too many IPv4 octets"
            },
            {
                "ip": "not-an-ip",
                "expected": {"is_valid": False, "reason": "not_ip_format"},
                "description": "Not an IP format"
            },
            {
                "ip": "",
                "expected": {"is_valid": False, "reason": "empty"},
                "description": "Empty IP"
            },
            {
                "ip": "::gggg",
                "expected": {"is_valid": False, "reason": "invalid_hex"},
                "description": "Invalid hex characters in IPv6"
            }
        ],
        
        "malicious_ips": [
            {
                "ip": "192.0.2.100",
                "expected": {"is_malicious": True, "threat_level": "high"},
                "description": "TEST-NET-1 known malicious"
            },
            {
                "ip": "198.51.100.100",
                "expected": {"is_malicious": True, "threat_level": "medium"},
                "description": "TEST-NET-2 suspicious activity"
            },
            {
                "ip": "203.0.113.100",
                "expected": {"is_malicious": True, "threat_level": "medium"},
                "description": "TEST-NET-3 C&C server"
            },
            {
                "ip": "127.0.0.2",
                "expected": {"is_suspicious": True, "threat_level": "low"},
                "description": "Tor exit node pattern"
            }
        ]
    }
    
    # URL validation test cases
    URL_TEST_CASES = {
        "valid_urls": [
            {
                "url": "https://www.example.com",
                "expected": {"is_valid": True, "scheme": "https", "has_host": True},
                "description": "Basic HTTPS URL"
            },
            {
                "url": "http://example.com/path?param=value",
                "expected": {"is_valid": True, "scheme": "http", "has_path": True, "has_query": True},
                "description": "URL with path and query"
            },
            {
                "url": "ftp://files.example.com/download",
                "expected": {"is_valid": True, "scheme": "ftp"},
                "description": "FTP URL"
            },
            {
                "url": "https://subdomain.example.com:8080/path",
                "expected": {"is_valid": True, "scheme": "https", "has_port": True},
                "description": "URL with port"
            },
            {
                "url": "https://example.com/path/to/resource",
                "expected": {"is_valid": True, "scheme": "https", "has_path": True},
                "description": "URL with deep path"
            }
        ],
        
        "invalid_urls": [
            {
                "url": "not-a-url",
                "expected": {"is_valid": False, "reason": "no_scheme"},
                "description": "Missing scheme"
            },
            {
                "url": "http://",
                "expected": {"is_valid": False, "reason": "missing_host"},
                "description": "Missing host"
            },
            {
                "url": "https://",
                "expected": {"is_valid": False, "reason": "missing_host"},
                "description": "HTTPS missing host"
            },
            {
                "url": "ftp://user@domain.com",
                "expected": {"is_valid": False, "reason": "userinfo_no_host"},
                "description": "User info without host"
            },
            {
                "url": "",
                "expected": {"is_valid": False, "reason": "empty"},
                "description": "Empty URL"
            },
            {
                "url": "https://[invalid::ipv6",
                "expected": {"is_valid": False, "reason": "malformed_ipv6"},
                "description": "Malformed IPv6"
            }
        ],
        
        "malicious_urls": [
            {
                "url": "http://malware-download.exe",
                "expected": {"is_malicious": True, "threat_type": "malware_download"},
                "description": "Direct malware download"
            },
            {
                "url": "https://phishing-site.com/login",
                "expected": {"is_malicious": True, "threat_type": "phishing"},
                "description": "Phishing landing page"
            },
            {
                "url": "http://fake-bank.com/verify",
                "expected": {"is_malicious": True, "threat_type": "banking_phishing"},
                "description": "Banking phishing"
            },
            {
                "url": "https://bit.ly/2X123",  # Shortened URL
                "expected": {"is_suspicious": True, "threat_type": "url_shortener"},
                "description": "Shortened URL - potentially malicious"
            },
            {
                "url": "http://trojan-site.org/keylogger",
                "expected": {"is_malicious": True, "threat_type": "trojan"},
                "description": "Trojan distribution"
            }
        ]
    }
    
    # Hash validation test cases
    HASH_TEST_CASES = {
        "valid_hashes": [
            {
                "hash": "098f6bcd4621d373cade4e832627b4f6",
                "expected": {"is_valid": True, "type": "md5", "length": 32},
                "description": "Valid MD5 hash"
            },
            {
                "hash": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",
                "expected": {"is_valid": True, "type": "sha1", "length": 40},
                "description": "Valid SHA1 hash"
            },
            {
                "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "expected": {"is_valid": True, "type": "sha256", "length": 64},
                "description": "Valid SHA256 hash"
            },
            {
                "hash": "b109f3bbbc244eb82441917ed06d618b9008dd09b3befd1b5e07394c706a8bb980b1d7785e5976ec049b46df5f1326af5a2ea6d103fd07c95385ffab0cacbc86",
                "expected": {"is_valid": True, "type": "sha512", "length": 128},
                "description": "Valid SHA512 hash"
            }
        ],
        
        "invalid_hashes": [
            {
                "hash": "not_a_hash",
                "expected": {"is_valid": False, "reason": "invalid_format"},
                "description": "Invalid hash format"
            },
            {
                "hash": "123456789",
                "expected": {"is_valid": False, "reason": "too_short"},
                "description": "Hash too short"
            },
            {
                "hash": "g098f6bcd4621d373cade4e832627b4f6",  # Contains 'g'
                "expected": {"is_valid": False, "reason": "invalid_characters"},
                "description": "Contains invalid characters"
            },
            {
                "hash": "098f6bcd4621d373cade4e832627b4f",  # One character short
                "expected": {"is_valid": False, "reason": "wrong_length"},
                "description": "Wrong length for MD5"
            },
            {
                "hash": "098F6BCD4621D373CADE4E832627B4F6",  # All uppercase
                "expected": {"is_valid": False, "reason": "uppercase_not_allowed"},
                "description": "Uppercase not allowed"
            }
        ]
    }
    
    # Bulk validation test cases
    BULK_TEST_CASES = {
        "mixed_validity": {
            "input": {
                "emails": ["user@example.com", "invalid-email", "test@domain.com"],
                "domains": ["example.com", "not-a-domain", "google.com"],
                "ip_addresses": ["8.8.8.8", "invalid-ip", "1.1.1.1"]
            },
            "expected": {
                "total_items": 9,
                "valid_items": 6,
                "invalid_items": 3,
                "validation_results": {
                    "emails": {
                        "valid_count": 2,
                        "invalid_count": 1
                    },
                    "domains": {
                        "valid_count": 2,
                        "invalid_count": 1
                    },
                    "ip_addresses": {
                        "valid_count": 2,
                        "invalid_count": 1
                    }
                }
            },
            "description": "Mixed validity bulk validation"
        },
        
        "all_valid": {
            "input": {
                "emails": ["user1@example.com", "user2@test.org"],
                "domains": ["example.com", "test.org"],
                "ip_addresses": ["8.8.8.8", "1.1.1.1"]
            },
            "expected": {
                "total_items": 6,
                "valid_items": 6,
                "invalid_items": 0
            },
            "description": "All valid bulk validation"
        },
        
        "all_invalid": {
            "input": {
                "emails": ["invalid-email", "not-an-email"],
                "domains": ["not-a-domain", "invalid..domain"],
                "ip_addresses": ["999.999.999.999", "not-an-ip"]
            },
            "expected": {
                "total_items": 6,
                "valid_items": 0,
                "invalid_items": 6
            },
            "description": "All invalid bulk validation"
        }
    }


class ValidationTestRunner:
    """Runner for validation test cases."""
    
    def __init__(self):
        self.test_cases = ValidationTestCases()
    
    def get_test_cases(self, data_type: str, category: str) -> List[Dict[str, Any]]:
        """Get test cases for specific data type and category."""
        return self.test_cases.EMAIL_TEST_CASES.get(f"{data_type}_{category}", [])
    
    def validate_test_case(self, test_case: Dict[str, Any], actual_result: Dict[str, Any]) -> bool:
        """Validate a test case against actual results."""
        expected = test_case["expected"]
        
        for key, expected_value in expected.items():
            if key not in actual_result:
                return False
            
            actual_value = actual_result[key]
            
            # Handle different comparison types
            if isinstance(expected_value, dict):
                # Nested validation
                if not self.validate_test_case(
                    {"expected": expected_value},
                    actual_value
                ):
                    return False
            elif expected_value != actual_value:
                return False
        
        return True
    
    def generate_test_parameters(self, data_type: str, category: str):
        """Generate pytest parameters for test cases."""
        test_cases = self.get_test_cases(data_type, category)
        
        return [
            (test_case, category) for test_case in test_cases
        ]


# Example usage and fixtures
@pytest.fixture
def validation_test_cases():
    """Provide validation test cases."""
    return ValidationTestCases()


@pytest.fixture
def validation_test_runner():
    """Provide validation test runner."""
    return ValidationTestRunner()


# Specific test implementations
def test_email_validation_specific(test_client, validation_test_cases):
    """Test specific email validation cases."""
    test_runner = ValidationTestRunner()
    
    # Test valid emails
    valid_cases = test_runner.get_test_cases("email", "valid_emails")
    
    for test_case in valid_cases[:3]:  # Test first 3 valid cases
        response = test_client.post(
            "/api/v1/validate/email",
            json={"email": test_case["email"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is True
        
        # Validate specific expectations
        if "confidence" in test_case["expected"]:
            assert data["result"]["confidence_score"] >= test_case["expected"]["confidence"]
    
    # Test invalid emails
    invalid_cases = test_runner.get_test_cases("email", "invalid_emails")
    
    for test_case in invalid_cases[:3]:  # Test first 3 invalid cases
        response = test_client.post(
            "/api/v1/validate/email",
            json={"email": test_case["email"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is False
        
        # Validate specific expectations
        if "confidence" in test_case["expected"]:
            assert data["result"]["confidence_score"] <= test_case["expected"]["confidence"]


def test_domain_validation_specific(test_client, validation_test_cases):
    """Test specific domain validation cases."""
    test_runner = ValidationTestRunner()
    
    # Test valid domains
    valid_cases = test_runner.get_test_cases("domain", "valid_domains")
    
    for test_case in valid_cases[:3]:
        response = test_client.post(
            "/api/v1/validate/domain",
            json={"domain": test_case["domain"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is True
    
    # Test invalid domains
    invalid_cases = test_runner.get_test_cases("domain", "invalid_domains")
    
    for test_case in invalid_cases[:3]:
        response = test_client.post(
            "/api/v1/validate/domain",
            json={"domain": test_case["domain"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is False


def test_ip_validation_specific(test_client, validation_test_cases):
    """Test specific IP validation cases."""
    test_runner = ValidationTestRunner()
    
    # Test valid IPv4 addresses
    valid_ipv4_cases = test_runner.get_test_cases("ip", "valid_ipv4")
    
    for test_case in valid_ipv4_cases[:3]:
        response = test_client.post(
            "/api/v1/validate/ip",
            json={"ip_address": test_case["ip"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is True
        assert data["result"]["ip_version"] == 4
    
    # Test valid IPv6 addresses
    valid_ipv6_cases = test_runner.get_test_cases("ip", "valid_ipv6")
    
    for test_case in valid_ipv6_cases[:2]:
        response = test_client.post(
            "/api/v1/validate/ip",
            json={"ip_address": test_case["ip"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is True
        assert data["result"]["ip_version"] == 6
    
    # Test invalid IPs
    invalid_cases = test_runner.get_test_cases("ip", "invalid_ips")
    
    for test_case in invalid_cases[:3]:
        response = test_client.post(
            "/api/v1/validate/ip",
            json={"ip_address": test_case["ip"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["result"]["is_valid"] is False


def test_bulk_validation_specific(test_client, validation_test_cases):
    """Test specific bulk validation cases."""
    test_runner = ValidationTestRunner()
    
    # Test mixed validity
    mixed_case = test_runner.test_cases.BULK_TEST_CASES["mixed_validity"]
    
    response = test_client.post(
        "/api/v1/validate/bulk",
        json=mixed_case["input"]
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Validate bulk results
    expected = mixed_case["expected"]
    assert data["total_items"] == expected["total_items"]
    assert data["valid_items"] == expected["valid_items"]
    assert data["invalid_items"] == expected["invalid_items"]
    
    # Validate category-specific counts
    validation_results = data["results"]
    assert validation_results["email_validation"]["valid_count"] == expected["validation_results"]["emails"]["valid_count"]
    assert validation_results["domain_validation"]["valid_count"] == expected["validation_results"]["domains"]["valid_count"]
    assert validation_results["ip_validation"]["valid_count"] == expected["validation_results"]["ip_addresses"]["valid_count"]


if __name__ == "__main__":
    # Example usage
    test_runner = ValidationTestRunner()
    
    print("Email Validation Test Cases:")
    print(f"Valid emails: {len(test_runner.get_test_cases('email', 'valid_emails'))}")
    print(f"Invalid emails: {len(test_runner.get_test_cases('email', 'invalid_emails'))}")
    print(f"Suspicious emails: {len(test_runner.get_test_cases('email', 'suspicious_emails'))}")
    print(f"Disposable emails: {len(test_runner.get_test_cases('email', 'disposable_emails'))}")
    
    print("\nDomain Validation Test Cases:")
    print(f"Valid domains: {len(test_runner.get_test_cases('domain', 'valid_domains'))}")
    print(f"Invalid domains: {len(test_runner.get_test_cases('domain', 'invalid_domains'))}")
    print(f"Suspicious domains: {len(test_runner.get_test_cases('domain', 'suspicious_domains'))}")
    
    print("\nIP Validation Test Cases:")
    print(f"Valid IPv4: {len(test_runner.get_test_cases('ip', 'valid_ipv4'))}")
    print(f"Valid IPv6: {len(test_runner.get_test_cases('ip', 'valid_ipv6'))}")
    print(f"Invalid IPs: {len(test_runner.get_test_cases('ip', 'invalid_ips'))}")
    print(f"Malicious IPs: {len(test_runner.get_test_cases('ip', 'malicious_ips'))}")
    
    print("\nURL Validation Test Cases:")
    print(f"Valid URLs: {len(test_runner.get_test_cases('url', 'valid_urls'))}")
    print(f"Invalid URLs: {len(test_runner.get_test_cases('url', 'invalid_urls'))}")
    print(f"Malicious URLs: {len(test_runner.get_test_cases('url', 'malicious_urls'))}")
    
    print("\nHash Validation Test Cases:")
    print(f"Valid hashes: {len(test_runner.get_test_cases('hash', 'valid_hashes'))}")
    print(f"Invalid hashes: {len(test_runner.get_test_cases('hash', 'invalid_hashes'))}")
    
    print("\nBulk Validation Test Cases:")
    print(f"Bulk test cases: {len(test_runner.test_cases.BULK_TEST_CASES)}")