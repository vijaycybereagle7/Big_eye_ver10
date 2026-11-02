"""Simplified reputation service for Vercel serverless deployment."""

import logging
import hashlib
import ipaddress
import dns.resolver
from typing import Dict, Any, List, Optional
import httpx

from ..database.supabase import get_cached_result, set_cached_result
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ReputationService:
    """Simplified reputation service optimized for serverless."""
    
    def __init__(self):
        """Initialize reputation service."""
        self.malicious_domains = set([
            # Common malicious domains (would be populated from threat feeds)
            'malware-example.com', 'phishing-example.net'
        ])
        
        self.suspicious_ips = set([
            # Common malicious IPs (would be populated from threat feeds)
        ])
    
    async def query_reputation(
        self,
        value: str,
        value_type: str,
        sources: Optional[List[str]] = None,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """Query reputation for a value."""
        try:
            cache_key = f"reputation:{value_type}:{value}"
            cached = await get_cached_result(cache_key)
            if cached:
                return cached["data"]
            
            result = {
                "value": value,
                "value_type": value_type,
                "reputation_score": 0.0,
                "threat_level": "low",
                "sources": {},
                "last_seen": None,
                "indicators": []
            }
            
            # Query based on value type
            if value_type == "ip":
                await self._check_ip_reputation(value, result)
            elif value_type == "domain":
                await self._check_domain_reputation(value, result)
            elif value_type == "url":
                await self._check_url_reputation(value, result)
            elif value_type == "hash":
                await self._check_hash_reputation(value, result)
            elif value_type == "email":
                await self._check_email_reputation(value, result)
            
            # Determine threat level based on score
            if result["reputation_score"] >= 0.8:
                result["threat_level"] = "critical"
            elif result["reputation_score"] >= 0.6:
                result["threat_level"] = "high"
            elif result["reputation_score"] >= 0.3:
                result["threat_level"] = "medium"
            else:
                result["threat_level"] = "low"
            
            return await self._cache_and_return(result, cache_key)
            
        except Exception as e:
            logger.error(f"Reputation query error for {value_type}:{value}: {e}")
            return {
                "value": value,
                "value_type": value_type,
                "reputation_score": 0.0,
                "threat_level": "low",
                "sources": {"error": str(e)},
                "indicators": ["reputation_check_failed"]
            }
    
    async def _check_ip_reputation(self, ip: str, result: Dict[str, Any]) -> None:
        """Check IP reputation."""
        sources = result["sources"]
        
        # Basic validation
        try:
            ip_obj = ipaddress.ip_address(ip)
            sources["basic_validation"] = {
                "valid": True,
                "ip_type": "IPv6" if ip_obj.version == 6 else "IPv4",
                "is_private": ip_obj.is_private,
                "is_reserved": ip_obj.is_reserved
            }
            
            if ip_obj.is_private or ip_obj.is_reserved:
                result["reputation_score"] = 0.1
                result["indicators"].append("private_or_reserved_ip")
                return
                
        except ValueError:
            sources["basic_validation"] = {
                "valid": False,
                "error": "Invalid IP address"
            }
            result["reputation_score"] = 0.9
            result["indicators"].append("invalid_ip")
            return
        
        # Check against local malicious list
        if ip in self.suspicious_ips:
            result["reputation_score"] = 1.0
            result["indicators"].append("known_malicious_ip")
            sources["local_list"] = {
                "status": "malicious",
                "reason": "Found in local malicious IP list"
            }
            return
        
        # DNS-based reputation checks
        try:
            # Check for DNS reputation indicators
            hostname = socket.gethostbyaddr(ip)[0]
            sources["dns"] = {
                "hostname": hostname,
                "reverse_dns": True
            }
            
            # Check for suspicious hostname patterns
            if any(pattern in hostname.lower() for pattern in ['malware', 'phishing', 'spam']):
                result["reputation_score"] = max(result["reputation_score"], 0.8)
                result["indicators"].append("suspicious_hostname")
                
        except socket.herror:
            sources["dns"] = {
                "reverse_dns": False,
                "message": "No reverse DNS record"
            }
        
        # Check VirusTotal API if available
        if settings.VIRUSTOTAL_API_KEY:
            try:
                vt_result = await self._check_virustotal_ip(ip)
                sources["virustotal"] = vt_result
                if vt_result.get("malicious", False):
                    result["reputation_score"] = max(result["reputation_score"], 0.9)
                    result["indicators"].append("virustotal_malicious")
            except Exception as e:
                logger.warning(f"VirusTotal API error: {e}")
        
        # Check AbuseIPDB if available
        if settings.ABUSEIPDB_API_KEY:
            try:
                abuse_result = await self._check_abuseipdb(ip)
                sources["abuseipdb"] = abuse_result
                if abuse_result.get("abuse_confidence", 0) > 50:
                    result["reputation_score"] = max(result["reputation_score"], 0.7)
                    result["indicators"].append("abuseipdb_suspicious")
            except Exception as e:
                logger.warning(f"AbuseIPDB API error: {e}")
        
        # Default reputation score for clean IPs
        if result["reputation_score"] == 0.0:
            result["reputation_score"] = 0.1  # Very clean
    
    async def _check_domain_reputation(self, domain: str, result: Dict[str, Any]) -> None:
        """Check domain reputation."""
        sources = result["sources"]
        
        # Check against local malicious list
        if domain in self.malicious_domains:
            result["reputation_score"] = 1.0
            result["indicators"].append("known_malicious_domain")
            sources["local_list"] = {
                "status": "malicious",
                "reason": "Found in local malicious domain list"
            }
            return
        
        # DNS-based checks
        try:
            # Check A records
            a_records = dns.resolver.resolve(domain, 'A')
            sources["dns"] = {
                "a_records": [str(record) for record in a_records],
                "resolved": True
            }
            
            # Check for suspicious IP associations
            for record in a_records:
                ip = str(record)
                if ip in self.suspicious_ips:
                    result["reputation_score"] = max(result["reputation_score"], 0.8)
                    result["indicators"].append("associated_malicious_ip")
            
        except dns.resolver.NXDOMAIN:
            sources["dns"] = {
                "resolved": False,
                "error": "Domain does not exist"
            }
            result["reputation_score"] = 0.7
            result["indicators"].append("non_existent_domain")
        except Exception as e:
            sources["dns"] = {
                "resolved": False,
                "error": str(e)
            }
        
        # Check VirusTotal if available
        if settings.VIRUSTOTAL_API_KEY:
            try:
                vt_result = await self._check_virustotal_domain(domain)
                sources["virustotal"] = vt_result
                if vt_result.get("malicious", False):
                    result["reputation_score"] = max(result["reputation_score"], 0.9)
                    result["indicators"].append("virustotal_malicious")
            except Exception as e:
                logger.warning(f"VirusTotal API error: {e}")
        
        # Default reputation score
        if result["reputation_score"] == 0.0:
            result["reputation_score"] = 0.1
    
    async def _check_url_reputation(self, url: str, result: Dict[str, Any]) -> None:
        """Check URL reputation."""
        sources = result["sources"]
        
        # Basic URL analysis
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        
        sources["url_analysis"] = {
            "domain": parsed.netloc,
            "scheme": parsed.scheme,
            "has_params": bool(parsed.query)
        }
        
        # Check domain reputation
        if parsed.netloc:
            domain_result = {
                "value": parsed.netloc,
                "value_type": "domain",
                "reputation_score": 0.0,
                "threat_level": "low",
                "sources": {}
            }
            await self._check_domain_reputation(parsed.netloc, domain_result)
            
            result["sources"]["domain_reputation"] = domain_result["sources"]
            result["reputation_score"] = max(
                result["reputation_score"], 
                domain_result["reputation_score"]
            )
        
        # Check for suspicious URL patterns
        import re
        suspicious_patterns = [
            r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP in URL
            r'@',  # @ symbol
            r'%[0-9A-Fa-f]{2}',  # URL encoding
            r'(bit\.ly|tinyurl|t\.co)',  # URL shorteners
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, url):
                result["reputation_score"] = max(result["reputation_score"], 0.6)
                result["indicators"].append(f"suspicious_pattern_{pattern}")
        
        # Default reputation score
        if result["reputation_score"] == 0.0:
            result["reputation_score"] = 0.2
    
    async def _check_hash_reputation(self, hash_value: str, result: Dict[str, Any]) -> None:
        """Check hash reputation."""
        sources = result["sources"]
        
        # Validate hash format
        if len(hash_value) == 32:
            hash_type = "MD5"
        elif len(hash_value) == 40:
            hash_type = "SHA1"
        elif len(hash_value) == 64:
            hash_type = "SHA256"
        else:
            sources["validation"] = {
                "valid": False,
                "error": "Invalid hash format"
            }
            result["reputation_score"] = 0.8
            result["indicators"].append("invalid_hash_format")
            return
        
        sources["validation"] = {
            "valid": True,
            "hash_type": hash_type
        }
        
        # Check VirusTotal if available
        if settings.VIRUSTOTAL_API_KEY:
            try:
                vt_result = await self._check_virustotal_hash(hash_value)
                sources["virustotal"] = vt_result
                if vt_result.get("malicious", False):
                    result["reputation_score"] = 1.0
                    result["indicators"].append("virustotal_malicious")
            except Exception as e:
                logger.warning(f"VirusTotal API error: {e}")
        
        # Default reputation score
        if result["reputation_score"] == 0.0:
            result["reputation_score"] = 0.1
    
    async def _check_email_reputation(self, email: str, result: Dict[str, Any]) -> None:
        """Check email reputation."""
        sources = result["sources"]
        
        domain = email.split('@')[1] if '@' in email else None
        
        # Check domain reputation if available
        if domain:
            domain_result = {
                "value": domain,
                "value_type": "domain",
                "reputation_score": 0.0,
                "threat_level": "low",
                "sources": {}
            }
            await self._check_domain_reputation(domain, domain_result)
            
            result["sources"]["domain_reputation"] = domain_result["sources"]
            result["reputation_score"] = domain_result["reputation_score"]
        
        # Check for disposable email services
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'yopmail.com', 'dispostable.com'
        ]
        
        if domain in disposable_domains:
            result["reputation_score"] = max(result["reputation_score"], 0.7)
            result["indicators"].append("disposable_email")
            sources["disposable_check"] = {"is_disposable": True}
        
        # Default reputation score
        if result["reputation_score"] == 0.0:
            result["reputation_score"] = 0.2
    
    async def _check_virustotal_ip(self, ip: str) -> Dict[str, Any]:
        """Check IP reputation via VirusTotal."""
        if not settings.VIRUSTOTAL_API_KEY:
            return {"available": False}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://www.virustotal.com/vtapi/v2/ip-address/report",
                params={
                    "apikey": settings.VIRUSTOTAL_API_KEY,
                    "ip": ip
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "malicious": data.get("positives", 0) > 0,
                    "positives": data.get("positives", 0),
                    "total": data.get("total", 0)
                }
            
            return {"available": False, "error": f"HTTP {response.status_code}"}
    
    async def _check_virustotal_domain(self, domain: str) -> Dict[str, Any]:
        """Check domain reputation via VirusTotal."""
        if not settings.VIRUSTOTAL_API_KEY:
            return {"available": False}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://www.virustotal.com/vtapi/v2/domain/report",
                params={
                    "apikey": settings.VIRUSTOTAL_API_KEY,
                    "domain": domain
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "malicious": data.get("positives", 0) > 0,
                    "positives": data.get("positives", 0),
                    "total": data.get("total", 0)
                }
            
            return {"available": False, "error": f"HTTP {response.status_code}"}
    
    async def _check_virustotal_hash(self, hash_value: str) -> Dict[str, Any]:
        """Check hash reputation via VirusTotal."""
        if not settings.VIRUSTOTAL_API_KEY:
            return {"available": False}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://www.virustotal.com/vtapi/v2/file/report",
                params={
                    "apikey": settings.VIRUSTOTAL_API_KEY,
                    "resource": hash_value
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "malicious": data.get("positives", 0) > 0,
                    "positives": data.get("positives", 0),
                    "total": data.get("total", 0)
                }
            
            return {"available": False, "error": f"HTTP {response.status_code}"}
    
    async def _check_abuseipdb(self, ip: str) -> Dict[str, Any]:
        """Check IP reputation via AbuseIPDB."""
        if not settings.ABUSEIPDB_API_KEY:
            return {"available": False}
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://api.abuseipdb.com/api/v2/check",
                headers={
                    "Key": settings.ABUSEIPDB_API_KEY,
                    "Accept": "application/json"
                },
                params={
                    "ipAddress": ip,
                    "maxAgeInDays": "90"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "abuse_confidence": data.get("data", {}).get("abuseConfidencePercentage", 0),
                    "total_reports": data.get("data", {}).get("totalReports", 0)
                }
            
            return {"available": False, "error": f"HTTP {response.status_code}"}
    
    async def _cache_and_return(self, result: Dict[str, Any], cache_key: str) -> Dict[str, Any]:
        """Cache result and return it."""
        if settings.CACHE_ENABLED:
            try:
                await set_cached_result(cache_key, result, settings.CACHE_TTL_LONG)
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result


# Global service instance
reputation_service = ReputationService()
