"""Test data generators for comprehensive testing."""

import random
import string
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union
from faker import Faker
import json


class TestDataGenerator:
    """Generate comprehensive test data for all API components."""
    
    def __init__(self):
        self.fake = Faker()
        Faker.seed(42)  # For reproducible tests
        random.seed(42)
    
    def generate_valid_emails(self, count: int = 100) -> List[str]:
        """Generate valid email addresses."""
        domains = [
            "example.com", "gmail.com", "yahoo.com", "outlook.com", 
            "company.org", "university.edu", "government.mil", 
            "startup.io", "business.net", "org.org"
        ]
        return [
            f"{self.fake.user_name()}@{random.choice(domains)}"
            for _ in range(count)
        ]
    
    def generate_invalid_emails(self, count: int = 50) -> List[str]:
        """Generate invalid email addresses."""
        patterns = [
            lambda: f"user@{self.fake.word()}",
            lambda: f"{self.fake.user_name()}{self.fake.word()}",
            lambda: f"{self.fake.user_name()}@",
            lambda: f"@{self.fake.word()}.com",
            lambda: self.fake.word() * 3,
            lambda: f"{self.fake.user_name()}@{self.fake.word()}{self.fake.random_element(['', '.'])}{self.fake.random_element(['c', 'co', 'com', 'comm'])}"
        ]
        return [random.choice(patterns)() for _ in range(count)]
    
    def generate_disposable_emails(self, count: int = 20) -> List[str]:
        """Generate disposable email addresses."""
        disposable_domains = [
            "10minutemail.com", "guerrillamail.com", "mailinator.com",
            "temp-mail.org", "throwaway.email", "fakeinbox.com",
            "yopmail.com", "sharklasers.com", "guerrillamail.net"
        ]
        return [
            f"{self.fake.user_name()}@{random.choice(disposable_domains)}"
            for _ in range(count)
        ]
    
    def generate_valid_domains(self, count: int = 100) -> List[str]:
        """Generate valid domain names."""
        domains = []
        for _ in range(count):
            domain = self.fake.domain()
            # Ensure it looks realistic
            if not domain.startswith(('xn--', '.', '-')):
                domains.append(domain)
        return domains[:count]
    
    def generate_invalid_domains(self, count: int = 50) -> List[str]:
        """Generate invalid domain names."""
        patterns = [
            lambda: f"{self.fake.word()}-{self.fake.word()}-",
            lambda: f"{'x' * 64}.com",  # Too long
            lambda: f"192.168.1.1",  # IP instead of domain
            lambda: f"{self.fake.word()}.{self.fake.random_element(['c', 'co', 'comm'])}",
            lambda: f"{self.fake.word()}..{self.fake.word()}.com",  # Double dots
            lambda: self.fake.word()  # No TLD
        ]
        return [random.choice(patterns)() for _ in range(count)]
    
    def generate_suspicious_domains(self, count: int = 30) -> List[str]:
        """Generate suspicious domain patterns."""
        suspicious_patterns = [
            "secure-login-update.com",
            "account-verify-required.net",
            "banking-security-alert.org",
            "paypal-security-check.com",
            "microsoft-authentication.net",
            "google-account-security.com",
            "fraud-alert-system.org",
            "billing-update-required.net"
        ]
        
        # Generate variations
        suspicious_domains = []
        for _ in range(count):
            base = random.choice(suspicious_patterns)
            # Add variations
            variations = [
                base.replace("com", "co.uk"),
                base.replace("com", "info"),
                base.replace("-", "--"),
                f"secure-{base}",
                f"{base}-verify.com"
            ]
            suspicious_domains.extend(random.sample(variations, min(3, len(variations))))
        
        return suspicious_domains[:count]
    
    def generate_valid_ips(self, count: int = 100, include_ipv6: bool = True) -> List[str]:
        """Generate valid IP addresses."""
        ips = []
        
        # Generate IPv4 addresses
        for _ in range(count):
            # Mix of public and private IPs
            if random.random() < 0.7:  # 70% public
                ip = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                # Exclude reserved ranges
                if not ipaddress.ip_address(ip).is_multicast and not ipaddress.ip_address(ip).is_reserved:
                    ips.append(ip)
            else:  # 30% private
                private_ranges = [
                    ("192.168.0.0/16", lambda: f"192.168.{random.randint(0, 255)}.{random.randint(1, 254)}"),
                    ("10.0.0.0/8", lambda: f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"),
                    ("172.16.0.0/12", lambda: f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(1, 254)}")
                ]
                _, generator = random.choice(private_ranges)
                ips.append(generator())
        
        # Add IPv6 addresses if requested
        if include_ipv6:
            ipv6_count = count // 4
            for _ in range(ipv6_count):
                # Generate a valid IPv6 address
                parts = [f"{random.randint(0, 65535):x}" for _ in range(8)]
                # Avoid all zeros
                if all(p == "0" for p in parts):
                    parts[0] = "2001"
                ipv6 = ":".join(parts)
                ips.append(ipv6)
        
        return ips[:count]
    
    def generate_malicious_ips(self, count: int = 20) -> List[str]:
        """Generate known malicious IP patterns."""
        # Common malicious IP patterns (these are examples, not actual malicious IPs)
        malicious_patterns = [
            "192.0.2.100",  # TEST-NET-1
            "198.51.100.100",  # TEST-NET-2
            "203.0.113.100",  # TEST-NET-3
            "127.0.0.2",  # Tor exit node pattern
            "10.0.0.1",  # Could be suspicious in certain contexts
            "172.16.0.1",  # Private gateway
        ]
        
        # Generate variations
        malicious_ips = []
        for _ in range(count):
            base = random.choice(malicious_patterns)
            # Generate similar IPs in the same range
            if base == "192.0.2.100":
                malicious_ips.append(f"192.0.2.{random.randint(1, 254)}")
            elif base == "198.51.100.100":
                malicious_ips.append(f"198.51.100.{random.randint(1, 254)}")
            elif base == "203.0.113.100":
                malicious_ips.append(f"203.0.113.{random.randint(1, 254)}")
            else:
                malicious_ips.append(base)
        
        return malicious_ips[:count]
    
    def generate_valid_urls(self, count: int = 100) -> List[str]:
        """Generate valid URLs."""
        protocols = ["http", "https"]
        domains = self.generate_valid_domains(count)
        paths = ["", "/", "/home", "/login", "/dashboard", "/api/v1", "/search?q=test"]
        
        urls = []
        for _ in range(count):
            protocol = random.choice(protocols)
            domain = random.choice(domains)
            path = random.choice(paths)
            url = f"{protocol}://{domain}{path}"
            urls.append(url)
        
        return urls
    
    def generate_malicious_urls(self, count: int = 30) -> List[str]:
        """Generate malicious URL patterns."""
        malicious_patterns = [
            "http://malware-download.exe",
            "https://phishing-site.com/login",
            "http://suspicious-domain.net/credit-card",
            "https://fake-bank.com/verify",
            "http://malicious-site.xyz/malware",
            "https://fake-paypal.com/account",
            "http://trojan-site.org/keylogger",
            "https://scam-site.com/credentials"
        ]
        
        # Generate variations
        malicious_urls = []
        for _ in range(count):
            base = random.choice(malicious_patterns)
            variations = [
                base.replace("com", "co.uk"),
                base.replace("com", "net"),
                base.replace("http", "https"),
                base.replace("https", "http"),
                f"www.{base}",
                f"secure.{base}"
            ]
            malicious_urls.extend(random.sample(variations, min(2, len(variations))))
        
        return malicious_urls[:count]
    
    def generate_hash_values(self, count: int = 50, hash_type: str = "all") -> Dict[str, List[str]]:
        """Generate hash values (MD5, SHA1, SHA256)."""
        hashes = {"md5": [], "sha1": [], "sha256": []}
        
        for _ in range(count):
            # Generate random data and hash it
            data = self.fake.text(max_nb_chars=100).encode('utf-8')
            
            if hash_type in ["all", "md5"]:
                md5_hash = hashlib.md5(data).hexdigest()
                hashes["md5"].append(md5_hash)
            
            if hash_type in ["all", "sha1"]:
                sha1_hash = hashlib.sha1(data).hexdigest()
                hashes["sha1"].append(sha1_hash)
            
            if hash_type in ["all", "sha256"]:
                sha256_hash = hashlib.sha256(data).hexdigest()
                hashes["sha256"].append(sha256_hash)
        
        return hashes
    
    def generate_bulk_validation_data(self, size: int = 1000) -> Dict[str, List[str]]:
        """Generate bulk validation test data."""
        # Mix of valid and invalid data
        valid_ratio = 0.7
        invalid_ratio = 0.3
        
        valid_count = int(size * valid_ratio)
        invalid_count = size - valid_count
        
        return {
            "emails": self.generate_valid_emails(int(valid_count * 0.6)) + 
                     self.generate_invalid_emails(int(invalid_count * 0.6)),
            "domains": self.generate_valid_domains(int(valid_count * 0.4)) +
                      self.generate_invalid_domains(int(invalid_count * 0.4)),
            "ip_addresses": self.generate_valid_ips(int(valid_count * 0.3)) +
                          self.generate_malicious_ips(int(invalid_count * 0.3)),
            "urls": self.generate_valid_urls(int(valid_count * 0.2)) +
                   self.generate_malicious_urls(int(invalid_count * 0.2)),
            "hashes": self.generate_hash_values(int(valid_count * 0.1) + int(invalid_count * 0.1))
        }
    
    def generate_reputation_test_data(self) -> Dict[str, Any]:
        """Generate comprehensive reputation test data."""
        return {
            "high_reputation": {
                "ip": "8.8.8.8",  # Google DNS
                "domain": "google.com",
                "url": "https://www.google.com",
                "expected_score": 90,
                "expected_verdict": "good"
            },
            "low_reputation": {
                "ip": "192.0.2.100",  # Test malicious IP
                "domain": "malware-site.com",
                "url": "http://malware-download.exe",
                "expected_score": 10,
                "expected_verdict": "malicious"
            },
            "unknown_reputation": {
                "ip": "192.168.1.100",  # Private IP
                "domain": "new-company.com",
                "url": "https://new-domain.org",
                "expected_score": 50,
                "expected_verdict": "unknown"
            }
        }
    
    def generate_threat_intelligence_data(self) -> Dict[str, Any]:
        """Generate threat intelligence test cases."""
        return {
            "malware_family": {
                "indicator": "Trojan.Generic.123456",
                "type": "hash",
                "family": "Zeus",
                "threat_level": "high",
                "confidence": 0.95
            },
            "botnet_indicator": {
                "indicator": "192.0.2.100",
                "type": "ip",
                "botnet": "Mirai",
                "threat_level": "critical",
                "confidence": 0.98
            },
            "phishing_campaign": {
                "indicator": "fake-bank-login.com",
                "type": "domain",
                "campaign": "PayPal Phishing",
                "threat_level": "medium",
                "confidence": 0.87
            }
        }
    
    def generate_load_test_data(self, user_count: int = 100) -> List[Dict[str, Any]]:
        """Generate data for load testing."""
        test_cases = []
        
        for user_id in range(user_count):
            user_data = {
                "user_id": user_id,
                "email": f"user{user_id}@test.com",
                "requests": [
                    {
                        "endpoint": "/api/v1/validate/email",
                        "payload": {"email": f"user{user_id}@example.com"},
                        "weight": 0.4
                    },
                    {
                        "endpoint": "/api/v1/validate/domain",
                        "payload": {"domain": f"domain{user_id}.com"},
                        "weight": 0.3
                    },
                    {
                        "endpoint": "/api/v1/reputation/query",
                        "payload": {
                            "value": f"192.168.1.{user_id % 255}",
                            "value_type": "ip"
                        },
                        "weight": 0.2
                    },
                    {
                        "endpoint": "/api/v1/threats/query",
                        "payload": {
                            "value": f"malware{user_id}.com",
                            "query_type": "domain"
                        },
                        "weight": 0.1
                    }
                ]
            }
            test_cases.append(user_data)
        
        return test_cases
    
    def generate_ml_test_data(self) -> Dict[str, List[Any]]:
        """Generate test data for ML model validation."""
        # Normal network traffic patterns
        normal_traffic = []
        for _ in range(1000):
            record = {
                "timestamp": datetime.now() - timedelta(minutes=random.randint(0, 1000)),
                "source_ip": self.generate_valid_ips(1)[0],
                "dest_ip": self.generate_valid_ips(1)[0],
                "port": random.choice([80, 443, 22, 25, 53, 110, 143, 993, 995]),
                "bytes_sent": random.randint(1000, 5000000),
                "bytes_received": random.randint(1000, 10000000),
                "duration": random.uniform(0.1, 300),
                "protocol": random.choice(["TCP", "UDP"]),
                "is_anomaly": False
            }
            normal_traffic.append(record)
        
        # Anomalous traffic patterns
        anomalous_traffic = []
        for _ in range(100):
            record = {
                "timestamp": datetime.now() - timedelta(minutes=random.randint(0, 1000)),
                "source_ip": self.generate_malicious_ips(1)[0],
                "dest_ip": self.generate_valid_ips(1)[0],
                "port": random.choice([4444, 6666, 8888, 12345, 31337]),  # Suspicious ports
                "bytes_sent": random.randint(50000000, 1000000000),  # Large transfers
                "bytes_received": random.randint(1, 100),  # Very small response
                "duration": random.uniform(0.01, 0.1),  # Very short or very long
                "protocol": "TCP",
                "is_anomaly": True
            }
            anomalous_traffic.append(record)
        
        return {
            "normal_traffic": normal_traffic,
            "anomalous_traffic": anomalous_traffic,
            "mixed": normal_traffic + anomalous_traffic
        }
    
    def export_test_data(self, filename: str, data: Any):
        """Export test data to JSON file."""
        filepath = Path("testing/fixtures/generated") / filename
        
        with open(filepath, 'w') as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2, default=str)
            else:
                f.write(str(data))
        
        return filepath
    
    def generate_all_test_data(self):
        """Generate all types of test data and export to files."""
        print("Generating comprehensive test data...")
        
        # Basic validation data
        self.export_test_data("valid_emails.json", self.generate_valid_emails(1000))
        self.export_test_data("invalid_emails.json", self.generate_invalid_emails(500))
        self.export_test_data("disposable_emails.json", self.generate_disposable_emails(200))
        
        self.export_test_data("valid_domains.json", self.generate_valid_domains(1000))
        self.export_test_data("invalid_domains.json", self.generate_invalid_domains(500))
        self.export_test_data("suspicious_domains.json", self.generate_suspicious_domains(300))
        
        self.export_test_data("valid_ips.json", self.generate_valid_ips(1000))
        self.export_test_data("malicious_ips.json", self.generate_malicious_ips(200))
        
        self.export_test_data("valid_urls.json", self.generate_valid_urls(1000))
        self.export_test_data("malicious_urls.json", self.generate_malicious_urls(300))
        
        self.export_test_data("hashes.json", self.generate_hash_values(500))
        
        # Complex test data
        self.export_test_data("bulk_validation.json", self.generate_bulk_validation_data(10000))
        self.export_test_data("reputation_test_data.json", self.generate_reputation_test_data())
        self.export_test_data("threat_intel_data.json", self.generate_threat_intelligence_data())
        self.export_test_data("ml_test_data.json", self.generate_ml_test_data())
        self.export_test_data("load_test_data.json", self.generate_load_test_data(1000))
        
        print("All test data generated successfully!")
        print("Files saved in: testing/fixtures/generated/")


if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.generate_all_test_data()