"""Mock external API services for testing."""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock, Mock
import aiohttp


class MockAbuseIPDB:
    """Mock AbuseIPDB API responses."""
    
    def __init__(self):
        self.base_url = "https://api.abuseipdb.com/api/v2"
        self.api_key = "mock-api-key"
    
    async def check_ip(self, ip: str, max_age_days: int = 30) -> Dict[str, Any]:
        """Mock check IP endpoint."""
        # Simulate different response types
        if ip == "8.8.8.8":  # Google DNS - clean
            return {
                "data": {
                    "ipAddress": ip,
                    "abuseConfidenceScore": 0,
                    "totalReports": 0,
                    "lastReportedAt": None,
                    "usageType": "Hosting Provider",
                    "isp": "Google LLC",
                    "domain": "google.com",
                    "hostnames": "dns.google",
                    "isWhiteListed": True,
                    "isBlackListed": False,
                    "isWhitelisted": True,
                    "countryCode": "US",
                    "countryName": "United States",
                    "region": "California",
                    "city": "Mountain View",
                    "latitude": 37.4056,
                    "longitude": -122.0775
                }
            }
        elif ip == "192.0.2.100":  # Test malicious IP
            return {
                "data": {
                    "ipAddress": ip,
                    "abuseConfidenceScore": 95,
                    "totalReports": 127,
                    "lastReportedAt": datetime.now().isoformat(),
                    "usageType": "Unknown",
                    "isp": "Unknown",
                    "domain": "unknown",
                    "hostnames": "",
                    "isWhiteListed": False,
                    "isBlackListed": True,
                    "isWhitelisted": False,
                    "countryCode": "Unknown",
                    "countryName": "Unknown",
                    "region": "",
                    "city": "",
                    "latitude": None,
                    "longitude": None
                }
            }
        else:  # Random response
            confidence = random.randint(0, 100)
            return {
                "data": {
                    "ipAddress": ip,
                    "abuseConfidenceScore": confidence,
                    "totalReports": random.randint(0, 50),
                    "lastReportedAt": datetime.now().isoformat() if confidence > 20 else None,
                    "usageType": random.choice(["Hosting Provider", " ISP", " University", " Unknown"]),
                    "isp": f"ISP-{random.randint(1, 100)}",
                    "domain": f"domain-{random.randint(1, 100)}.com",
                    "hostnames": f"host{random.randint(1, 100)}.example.com",
                    "isWhiteListed": confidence < 10,
                    "isBlackListed": confidence > 80,
                    "isWhitelisted": confidence < 10,
                    "countryCode": "US",
                    "countryName": "United States",
                    "region": "California",
                    "city": "San Francisco",
                    "latitude": 37.7749,
                    "longitude": -122.4194
                }
            }
    
    async def blacklist_check(self, ips: List[str]) -> Dict[str, Any]:
        """Mock blacklist check endpoint."""
        results = []
        for ip in ips:
            confidence = random.randint(0, 100)
            results.append({
                "ipAddress": ip,
                "abuseConfidenceScore": confidence,
                "totalReports": random.randint(0, 100),
                "lastReportedAt": datetime.now().isoformat() if confidence > 20 else None
            })
        
        return {
            "data": results,
            "meta": {
                "total_count": len(ips),
                "last_updated": datetime.now().isoformat()
            }
        }


class MockVirusTotal:
    """Mock VirusTotal API responses."""
    
    def __init__(self):
        self.base_url = "https://www.virustotal.com/vtapi/v2"
        self.api_key = "mock-api-key"
    
    async def scan_ip(self, ip: str) -> Dict[str, Any]:
        """Mock IP scan endpoint."""
        if ip == "8.8.8.8":
            return {
                "response_code": 1,
                "resolutions": [],
                "detected_urls": [],
                "undetected_urls": 0,
                "detected_samples": [],
                "undetected_samples": 0,
                "detected_referrer_samples": [],
                "undetected_referrer_samples": 0,
                "detected_communicating_samples": [],
                "undetected_communicating_samples": 10,
                "detected_downloaded_samples": [],
                "undetected_downloaded_samples": 5,
                "detected_embedded_samples": [],
                "undetected_embedded_samples": 2
            }
        elif ip == "192.0.2.100":
            return {
                "response_code": 1,
                "resolutions": [],
                "detected_urls": [
                    {
                        "url": "http://malware-site.com/malware.exe",
                        "positives": 45,
                        "scan_date": datetime.now().isoformat(),
                        "url_status": "available"
                    }
                ],
                "undetected_urls": 1,
                "detected_samples": [
                    {
                        "sha256": "malware-hash-123",
                        "positives": 42,
                        "scan_date": datetime.now().isoformat(),
                        "type": "PE32"
                    }
                ],
                "undetected_samples": 0,
                "detected_communicating_samples": [
                    {
                        "sha256": "communicating-malware-456",
                        "positives": 38,
                        "scan_date": datetime.now().isoformat(),
                        "type": "PE32"
                    }
                ],
                "undetected_communicating_samples": 2,
                "detected_downloaded_samples": [
                    {
                        "sha256": "downloaded-malware-789",
                        "positives": 40,
                        "scan_date": datetime.now().isoformat(),
                        "type": "PE32"
                    }
                ],
                "undetected_downloaded_samples": 1,
                "detected_embedded_samples": [],
                "undetected_embedded_samples": 5
            }
        else:
            # Random scan result
            detected_urls = random.randint(0, 3)
            return {
                "response_code": 1,
                "resolutions": [],
                "detected_urls": [
                    {
                        "url": f"http://suspicious{random.randint(1, 100)}.com/payload",
                        "positives": random.randint(5, 60),
                        "scan_date": datetime.now().isoformat(),
                        "url_status": "available"
                    }
                ] * detected_urls,
                "undetected_urls": random.randint(0, 10),
                "detected_samples": [
                    {
                        "sha256": f"hash-{random.randint(1000, 9999)}",
                        "positives": random.randint(10, 50),
                        "scan_date": datetime.now().isoformat(),
                        "type": "PE32"
                    }
                ] * random.randint(0, 3),
                "undetected_samples": random.randint(0, 10),
                "detected_communicating_samples": [],
                "undetected_communicating_samples": random.randint(0, 10),
                "detected_downloaded_samples": [],
                "undetected_downloaded_samples": random.randint(0, 10),
                "detected_embedded_samples": [],
                "undetected_embedded_samples": random.randint(0, 10)
            }
    
    async def scan_domain(self, domain: str) -> Dict[str, Any]:
        """Mock domain scan endpoint."""
        if domain in ["google.com", "example.com", "github.com"]:
            return {
                "response_code": 1,
                "resolutions": [
                    {
                        "ip_address": "8.8.8.8",
                        "last_resolved": datetime.now().isoformat()
                    }
                ],
                "detected_urls": [],
                "undetected_urls": 0,
                "detected_files": [],
                "undetected_files": 10,
                "detected_communicating_samples": [],
                "undetected_communicating_samples": 5,
                "detected_referrer_samples": [],
                "undetected_referrer_samples": 2
            }
        elif "malware" in domain.lower() or "suspicious" in domain.lower():
            return {
                "response_code": 1,
                "resolutions": [
                    {
                        "ip_address": "192.0.2.100",
                        "last_resolved": datetime.now().isoformat()
                    }
                ],
                "detected_urls": [
                    {
                        "url": f"https://{domain}/phishing",
                        "positives": 50,
                        "scan_date": datetime.now().isoformat(),
                        "url_status": "available"
                    }
                ],
                "undetected_urls": 1,
                "detected_files": [
                    {
                        "sha256": f"phishing-file-{random.randint(1000, 9999)}",
                        "positives": 45,
                        "scan_date": datetime.now().isoformat(),
                        "type": "HTML"
                    }
                ],
                "undetected_files": 0,
                "detected_communicating_samples": [
                    {
                        "sha256": f"communicating-malware-{random.randint(1000, 9999)}",
                        "positives": 40,
                        "scan_date": datetime.now().isoformat(),
                        "type": "PE32"
                    }
                ],
                "undetected_communicating_samples": 0,
                "detected_referrer_samples": [],
                "undetected_referrer_samples": 1
            }
        else:
            # Random domain
            return {
                "response_code": 1,
                "resolutions": [
                    {
                        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
                        "last_resolved": datetime.now().isoformat()
                    }
                ],
                "detected_urls": [],
                "undetected_urls": random.randint(0, 5),
                "detected_files": [],
                "undetected_files": random.randint(0, 10),
                "detected_communicating_samples": [],
                "undetected_communicating_samples": random.randint(0, 10),
                "detected_referrer_samples": [],
                "undetected_referrer_samples": random.randint(0, 5)
            }
    
    async def scan_url(self, url: str) -> Dict[str, Any]:
        """Mock URL scan endpoint."""
        if "google.com" in url:
            return {
                "response_code": 1,
                "resource": url,
                "url": url,
                "scan_date": datetime.now().isoformat(),
                "scan_id": f"scan-{random.randint(1000000, 9999999)}",
                "permalink": f"https://www.virustotal.com/gui/analysis/{random.randint(1000000, 9999999)}",
                "verbose_msg": "Scan finished, report embedded",
                "filescan_id": None,
                "filescan_id": None,
                "status": "completed",
                "stats": {
                    "harmless": 70,
                    "malicious": 0,
                    "suspicious": 0,
                    "undetected": 5,
                    "failure": 0,
                    "timeout": 0,
                    "failure_timestamp": None,
                    "failure_reason": None
                },
                "reputation": 0
            }
        elif "malware" in url.lower():
            return {
                "response_code": 1,
                "resource": url,
                "url": url,
                "scan_date": datetime.now().isoformat(),
                "scan_id": f"scan-{random.randint(1000000, 9999999)}",
                "permalink": f"https://www.virustotal.com/gui/analysis/{random.randint(1000000, 9999999)}",
                "verbose_msg": "Scan finished, report embedded",
                "filescan_id": None,
                "status": "completed",
                "stats": {
                    "harmless": 5,
                    "malicious": 60,
                    "suspicious": 5,
                    "undetected": 5,
                    "failure": 0,
                    "timeout": 0,
                    "failure_timestamp": None,
                    "failure_reason": None
                },
                "reputation": -90
            }
        else:
            # Random URL
            return {
                "response_code": 1,
                "resource": url,
                "url": url,
                "scan_date": datetime.now().isoformat(),
                "scan_id": f"scan-{random.randint(1000000, 9999999)}",
                "permalink": f"https://www.virustotal.com/gui/analysis/{random.randint(1000000, 9999999)}",
                "verbose_msg": "Scan finished, report embedded",
                "stats": {
                    "harmless": random.randint(50, 65),
                    "malicious": random.randint(0, 5),
                    "suspicious": random.randint(0, 3),
                    "undetected": random.randint(5, 15),
                    "failure": 0,
                    "timeout": 0
                },
                "reputation": random.randint(-50, 50)
            }


class MockGreyNoise:
    """Mock GreyNoise API responses."""
    
    def __init__(self):
        self.base_url = "https://api.greynoise.io/v3"
        self.api_key = "mock-api-key"
    
    async def ip_lookup(self, ip: str) -> Dict[str, Any]:
        """Mock IP lookup endpoint."""
        if ip == "8.8.8.8":
            return {
                "ip": ip,
                "noise": False,
                "riot": True,
                "classification": "benign",
                "name": "Google Public DNS",
                "link": "https://viz.greynoise.io/ip/8.8.8.8",
                "last_seen": datetime.now().isoformat(),
                "message": "Success"
            }
        elif ip == "192.0.2.100":
            return {
                "ip": ip,
                "noise": True,
                "riot": False,
                "classification": "malicious",
                "name": "Known Malware C&C",
                "link": "https://viz.greynoise.io/ip/192.0.2.100",
                "last_seen": datetime.now().isoformat(),
                "message": "Success"
            }
        else:
            # Random IP
            is_noise = random.choice([True, False])
            return {
                "ip": ip,
                "noise": is_noise,
                "riot": not is_noise and random.random() > 0.5,
                "classification": "malicious" if is_noise else "benign",
                "name": f"Scanner-{random.randint(1, 1000)}",
                "link": f"https://viz.greynoise.io/ip/{ip}",
                "last_seen": datetime.now().isoformat(),
                "message": "Success"
            }


class MockOTX:
    """Mock OTX (Open Threat Exchange) API responses."""
    
    def __init__(self):
        self.base_url = "https://otx.alienvault.com/api/v1"
        self.api_key = "mock-api-key"
    
    async def get_ip_reputation(self, ip: str) -> Dict[str, Any]:
        """Mock IP reputation endpoint."""
        if ip == "8.8.8.8":
            return {
                "pulse_info": {
                    "count": 0,
                    "pulses": []
                },
                "reputation": 0,
                "sections": {
                    "general": {},
                    "geo": {},
                    "malware": {},
                    "url_list": {
                        "hashtags": [],
                        "count": 0,
                        "url_list": []
                    },
                    "passive_dns": {
                        "passive_dns": [],
                        "count": 0
                    }
                },
                "indicators": [],
                "count": 0
            }
        elif "192.0.2." in ip:
            return {
                "pulse_info": {
                    "count": 5,
                    "pulses": [
                        {
                            "id": f"pulse-{random.randint(1000, 9999)}",
                            "name": f"Botnet C&C - {random.randint(1, 100)}",
                            "description": "Known botnet command and control server",
                            "author_name": "ThreatHunter",
                            "TLP": "AMBER",
                            "created": datetime.now().isoformat()
                        }
                    ]
                },
                "reputation": -80,
                "sections": {
                    "general": {},
                    "geo": {},
                    "malware": {
                        "hash_list": [
                            "malware-hash-123",
                            "trojan-hash-456"
                        ]
                    },
                    "url_list": {
                        "hashtags": ["botnet", "malware"],
                        "count": 2,
                        "url_list": [
                            {
                                "url": "http://malware-site.com/c2",
                                "date_created": datetime.now().isoformat()
                            }
                        ]
                    },
                    "passive_dns": {
                        "passive_dns": [
                            {
                                "address": ip,
                                "hostname": f"botnet{random.randint(1, 100)}.malware.com",
                                "first": datetime.now().isoformat(),
                                "last": datetime.now().isoformat()
                            }
                        ],
                        "count": 1
                    }
                },
                "indicators": [
                    {
                        "content": f"Botnet indicator - {ip}",
                        "author": "ThreatHunter",
                        "date_created": datetime.now().isoformat()
                    }
                ],
                "count": 5
            }
        else:
            return {
                "pulse_info": {
                    "count": random.randint(0, 5),
                    "pulses": []
                },
                "reputation": random.randint(-50, 50),
                "sections": {
                    "general": {},
                    "geo": {},
                    "malware": {},
                    "url_list": {
                        "hashtags": [],
                        "count": 0,
                        "url_list": []
                    },
                    "passive_dns": {
                        "passive_dns": [],
                        "count": 0
                    }
                },
                "indicators": [],
                "count": 0
            }


class MockThreatIntelligenceAPI:
    """Combined mock threat intelligence API service."""
    
    def __init__(self):
        self.abuseipdb = MockAbuseIPDB()
        self.virustotal = MockVirusTotal()
        self.greynoise = MockGreyNoise()
        self.otx = MockOTX()
    
    async def query_ip_comprehensive(self, ip: str) -> Dict[str, Any]:
        """Get comprehensive IP intelligence from all sources."""
        try:
            results = {}
            
            # Query all sources in parallel
            abuseipdb_task = self.abuseipdb.check_ip(ip)
            virustotal_task = self.virustotal.scan_ip(ip)
            greynoise_task = self.greynoise.ip_lookup(ip)
            otx_task = self.otx.get_ip_reputation(ip)
            
            abuseipdb_data, virustotal_data, greynoise_data, otx_data = await asyncio.gather(
                abuseipdb_task, virustotal_task, greynoise_task, otx_task,
                return_exceptions=True
            )
            
            results.update({
                "abuseipdb": abuseipdb_data if not isinstance(abuseipdb_data, Exception) else {"error": str(abuseipdb_data)},
                "virustotal": virustotal_data if not isinstance(virustotal_data, Exception) else {"error": str(virustotal_data)},
                "greynoise": greynoise_data if not isinstance(greynoise_data, Exception) else {"error": str(greynoise_data)},
                "otx": otx_data if not isinstance(otx_data, Exception) else {"error": str(otx_data)}
            })
            
            # Calculate overall threat score
            scores = []
            if "abuseipdb" in results and "data" in results["abuseipdb"]:
                scores.append(results["abuseipdb"]["data"].get("abuseConfidenceScore", 0))
            if "greynoise" in results and results["greynoise"].get("noise"):
                scores.append(90)
            if "virustotal" in results and "detected_urls" in results["virustotal"]:
                if results["virustotal"]["detected_urls"]:
                    avg_detections = sum(det["positives"] for det in results["virustotal"]["detected_urls"]) / len(results["virustotal"]["detected_urls"])
                    scores.append(avg_detections)
            
            overall_score = sum(scores) / len(scores) if scores else 0
            
            results["summary"] = {
                "overall_threat_score": overall_score,
                "sources_queried": 4,
                "threat_level": self._calculate_threat_level(overall_score),
                "confidence": min(100, len([s for s in scores if s > 0]) * 25)
            }
            
            return results
            
        except Exception as e:
            return {"error": str(e), "summary": {"error": True}}
    
    def _calculate_threat_level(self, score: float) -> str:
        """Calculate threat level from score."""
        if score >= 80:
            return "critical"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        elif score >= 20:
            return "low"
        else:
            return "benign"


# Mock responses for testing
MOCK_RESPONSES = {
    "abuseipdb": {
        "check_ip": {
            "8.8.8.8": {"abuseConfidenceScore": 0, "totalReports": 0},
            "192.0.2.100": {"abuseConfidenceScore": 95, "totalReports": 127}
        }
    },
    "virustotal": {
        "scan_ip": {
            "8.8.8.8": {"detected_urls": [], "response_code": 1},
            "192.0.2.100": {"detected_urls": [{"positives": 45}], "response_code": 1}
        }
    },
    "greynoise": {
        "ip_lookup": {
            "8.8.8.8": {"noise": False, "riot": True, "classification": "benign"},
            "192.0.2.100": {"noise": True, "riot": False, "classification": "malicious"}
        }
    }
}


def create_mock_session() -> Dict[str, AsyncMock]:
    """Create a mock session for HTTP client testing."""
    session = {}
    
    # Mock AbuseIPDB
    session["abuseipdb"] = AsyncMock()
    session["abuseipdb"].get.return_value.status = 200
    session["abuseipdb"].get.return_value.json = lambda: MOCK_RESPONSES["abuseipdb"]["check_ip"]["8.8.8.8"]
    
    # Mock VirusTotal
    session["virustotal"] = AsyncMock()
    session["virustotal"].get.return_value.status = 200
    session["virustotal"].get.return_value.json = lambda: MOCK_RESPONSES["virustotal"]["scan_ip"]["8.8.8.8"]
    
    # Mock GreyNoise
    session["greynoise"] = AsyncMock()
    session["greynoise"].get.return_value.status = 200
    session["greynoise"].get.return_value.json = lambda: MOCK_RESPONSES["greynoise"]["ip_lookup"]["8.8.8.8"]
    
    return session


if __name__ == "__main__":
    # Test the mock APIs
    async def test_mocks():
        mock_api = MockThreatIntelligenceAPI()
        
        # Test IP lookup
        result = await mock_api.query_ip_comprehensive("8.8.8.8")
        print("Clean IP result:", json.dumps(result, indent=2, default=str))
        
        result = await mock_api.query_ip_comprehensive("192.0.2.100")
        print("Malicious IP result:", json.dumps(result, indent=2, default=str))
    
    asyncio.run(test_mocks())