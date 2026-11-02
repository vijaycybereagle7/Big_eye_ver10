"""Simplified validation service for Vercel serverless deployment."""

import logging
import re
import socket
import ipaddress
from typing import Dict, Any, List, Optional
import dns.resolver
import whois
from datetime import datetime
import hashlib
import urllib.parse

from ..database.supabase import get_cached_result, set_cached_result
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ValidationService:
    """Simplified validation service optimized for serverless."""
    
    def __init__(self):
        """Initialize validation service."""
        self.disposable_domains = set([
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'yopmail.com', 'dispostable.com', 'throwaway.email'
        ])
        
        self.suspicious_tlds = set([
            'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'work', 'date'
        ])
    
    async def validate_email(
        self,
        email: str,
        verify_syntax: bool = True,
        verify_mx_record: bool = False,
        check_disposable: bool = True
    ) -> Dict[str, Any]:
        """Validate email address."""
        try:
            # Check cache first
            cache_key = f"email_validation:{email}"
            cached = await get_cached_result(cache_key)
            if cached:
                return cached["data"]
            
            result = {
                "email": email,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {},
                "is_disposable": False,
                "provider": None,
                "domain": None
            }
            
            # Basic syntax validation
            if verify_syntax:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    result["checks"]["syntax"] = {
                        "valid": False,
                        "message": "Invalid email format"
                    }
                    return await self._cache_and_return(result, cache_key)
                
                result["checks"]["syntax"] = {
                    "valid": True,
                    "message": "Valid email format"
                }
            
            # Extract domain
            domain = email.split('@')[1].lower()
            result["domain"] = domain
            
            # Check disposable email
            if check_disposable:
                is_disposable = domain in self.disposable_domains
                result["is_disposable"] = is_disposable
                result["checks"]["disposable"] = {
                    "valid": not is_disposable,
                    "is_disposable": is_disposable
                }
                
                if is_disposable:
                    result["confidence"] = "medium"
                    return await self._cache_and_return(result, cache_key)
            
            # Check MX records (optional, can be slow)
            if verify_mx_record:
                try:
                    mx_records = dns.resolver.resolve(domain, 'MX')
                    result["checks"]["mx_record"] = {
                        "valid": True,
                        "mx_records": [str(record.exchange) for record in mx_records]
                    }
                except Exception as e:
                    result["checks"]["mx_record"] = {
                        "valid": False,
                        "message": f"MX record lookup failed: {str(e)}"
                    }
            
            # Determine provider
            result["provider"] = self._detect_email_provider(domain)
            
            # Calculate final score and confidence
            result["is_valid"] = True
            result["score"] = 0.8
            result["confidence"] = "high"
            
            return await self._cache_and_return(result, cache_key)
            
        except Exception as e:
            logger.error(f"Email validation error for {email}: {e}")
            return {
                "email": email,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {"error": str(e)},
                "message": f"Validation failed: {str(e)}"
            }
    
    async def validate_domain(self, domain: str) -> Dict[str, Any]:
        """Validate domain name."""
        try:
            cache_key = f"domain_validation:{domain}"
            cached = await get_cached_result(cache_key)
            if cached:
                return cached["data"]
            
            result = {
                "domain": domain,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {},
                "is_active": False,
                "expires_at": None,
                "registrar": None
            }
            
            # Basic format validation
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            if not re.match(domain_pattern, domain):
                result["checks"]["format"] = {
                    "valid": False,
                    "message": "Invalid domain format"
                }
                return await self._cache_and_return(result, cache_key)
            
            result["checks"]["format"] = {
                "valid": True,
                "message": "Valid domain format"
            }
            
            # Check DNS resolution
            try:
                ip = socket.gethostbyname(domain)
                result["checks"]["dns"] = {
                    "valid": True,
                    "resolved_ip": ip
                }
                result["is_active"] = True
            except socket.gaierror:
                result["checks"]["dns"] = {
                    "valid": False,
                    "message": "Domain does not resolve"
                }
                result["score"] = 0.1
                return await self._cache_and_return(result, cache_key)
            
            # Check WHOIS info (optional, can be slow)
            try:
                w = whois.whois(domain)
                result["expires_at"] = w.expiration_date[0] if w.expiration_date else None
                result["registrar"] = w.registrar if w.registrar else None
                result["checks"]["whois"] = {
                    "valid": True,
                    "registrar": result["registrar"],
                    "expires_at": result["expires_at"]
                }
            except Exception as e:
                result["checks"]["whois"] = {
                    "valid": False,
                    "message": f"WHOIS lookup failed: {str(e)}"
                }
            
            # Check for suspicious TLDs
            tld = domain.split('.')[-1].lower()
            if tld in self.suspicious_tlds:
                result["checks"]["tld"] = {
                    "valid": False,
                    "message": f"Suspicious TLD: {tld}",
                    "tld": tld
                }
                result["score"] = 0.6
            
            # Calculate final score
            result["is_valid"] = True
            result["score"] = 0.9 if tld not in self.suspicious_tlds else 0.7
            result["confidence"] = "high"
            
            return await self._cache_and_return(result, cache_key)
            
        except Exception as e:
            logger.error(f"Domain validation error for {domain}: {e}")
            return {
                "domain": domain,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {"error": str(e)},
                "message": f"Validation failed: {str(e)}"
            }
    
    async def validate_ip(self, ip: str) -> Dict[str, Any]:
        """Validate IP address."""
        try:
            cache_key = f"ip_validation:{ip}"
            cached = await get_cached_result(cache_key)
            if cached:
                return cached["data"]
            
            result = {
                "ip": ip,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {},
                "ip_type": "IPv4",
                "is_private": False,
                "is_reserved": False
            }
            
            # Parse IP address
            ip_obj = ipaddress.ip_address(ip)
            result["ip_type"] = "IPv6" if ip_obj.version == 6 else "IPv4"
            result["is_private"] = ip_obj.is_private
            result["is_reserved"] = ip_obj.is_reserved
            
            # Check if it's a valid public IP
            if result["is_private"] or result["is_reserved"]:
                result["checks"]["ip_type"] = {
                    "valid": False,
                    "message": "Private or reserved IP address"
                }
                result["score"] = 0.3
                return await self._cache_and_return(result, cache_key)
            
            result["checks"]["ip_type"] = {
                "valid": True,
                "message": "Valid public IP address"
            }
            
            # Reverse DNS lookup (optional)
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                result["checks"]["reverse_dns"] = {
                    "valid": True,
                    "hostname": hostname
                }
            except socket.herror:
                result["checks"]["reverse_dns"] = {
                    "valid": False,
                    "message": "No reverse DNS record"
                }
            
            result["is_valid"] = True
            result["score"] = 0.8
            result["confidence"] = "high"
            
            return await self._cache_and_return(result, cache_key)
            
        except Exception as e:
            logger.error(f"IP validation error for {ip}: {e}")
            return {
                "ip": ip,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {"error": str(e)},
                "message": f"Validation failed: {str(e)}"
            }
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate URL."""
        try:
            cache_key = f"url_validation:{url}"
            cached = await get_cached_result(cache_key)
            if cached:
                return cached["data"]
            
            result = {
                "url": url,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {},
                "domain": None,
                "is_https": False,
                "is_suspicious": False,
                "threat_indicators": []
            }
            
            # Parse URL
            try:
                parsed = urllib.parse.urlparse(url)
                result["domain"] = parsed.netloc.lower()
                result["is_https"] = parsed.scheme == "https"
            except Exception as e:
                result["checks"]["format"] = {
                    "valid": False,
                    "message": f"Invalid URL format: {str(e)}"
                }
                return await self._cache_and_return(result, cache_key)
            
            result["checks"]["format"] = {
                "valid": True,
                "message": "Valid URL format"
            }
            
            # Check protocol
            if parsed.scheme not in ['http', 'https']:
                result["checks"]["protocol"] = {
                    "valid": False,
                    "message": "Unsupported protocol"
                }
                result["threat_indicators"].append("unsupported_protocol")
                return await self._cache_and_return(result, cache_key)
            
            result["checks"]["protocol"] = {
                "valid": True,
                "message": f"Valid {parsed.scheme.upper()} protocol"
            }
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'\b(bit\.ly|tinyurl|t\.co)\b',  # URL shorteners
                r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}',  # IP addresses
                r'@',  # @ symbol in URL
                r'%[0-9A-Fa-f]{2}',  # URL encoding
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url):
                    result["threat_indicators"].append(f"suspicious_pattern_{pattern}")
                    result["is_suspicious"] = True
            
            # Validate domain
            if result["domain"]:
                domain_result = await self.validate_domain(result["domain"])
                if domain_result["is_valid"]:
                    result["checks"]["domain"] = {
                        "valid": True,
                        "message": "Domain is valid"
                    }
                else:
                    result["checks"]["domain"] = {
                        "valid": False,
                        "message": "Domain validation failed"
                    }
                    result["threat_indicators"].append("invalid_domain")
                    result["is_suspicious"] = True
            
            result["is_valid"] = len(result["threat_indicators"]) == 0
            result["score"] = 0.9 if not result["is_suspicious"] else 0.4
            result["confidence"] = "high" if not result["is_suspicious"] else "medium"
            
            return await self._cache_and_return(result, cache_key)
            
        except Exception as e:
            logger.error(f"URL validation error for {url}: {e}")
            return {
                "url": url,
                "is_valid": False,
                "score": 0.0,
                "confidence": "low",
                "checks": {"error": str(e)},
                "message": f"Validation failed: {str(e)}"
            }
    
    def _detect_email_provider(self, domain: str) -> Optional[str]:
        """Detect email provider from domain."""
        provider_domains = {
            'gmail.com': 'Gmail',
            'yahoo.com': 'Yahoo',
            'hotmail.com': 'Hotmail',
            'outlook.com': 'Outlook',
            'aol.com': 'AOL',
            'icloud.com': 'iCloud',
            'protonmail.com': 'ProtonMail',
            'mail.com': 'Mail.com'
        }
        
        return provider_domains.get(domain.lower())
    
    async def _cache_and_return(self, result: Dict[str, Any], cache_key: str) -> Dict[str, Any]:
        """Cache result and return it."""
        if settings.CACHE_ENABLED:
            try:
                await set_cached_result(cache_key, result, settings.CACHE_TTL_DEFAULT)
            except Exception as e:
                logger.warning(f"Failed to cache result: {e}")
        
        return result


# Global service instance
validation_service = ValidationService()
