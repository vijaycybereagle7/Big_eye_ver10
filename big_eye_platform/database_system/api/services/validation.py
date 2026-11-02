"""Core validation services."""

import re
import dns.resolver
import socket
import requests
from typing import List, Dict, Any, Optional, Tuple
import urllib.parse
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

from ..config.settings import settings
from ..cache.redis_cache import cached, cache_get, cache_set, generate_cache_key
from ..models.schemas import (
    EmailValidationResult, DomainValidationResult, IPValidationResult,
    URLValidationResult, SenderValidationResult, ValidationResult
)

logger = logging.getLogger(__name__)


class ValidationService:
    """Core validation service with caching and external API integration."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Validation patterns
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        self.domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.?$'
        )
        self.ipv4_pattern = re.compile(
            r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )
        self.ipv6_pattern = re.compile(
            r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$'
        )
        self.url_pattern = re.compile(
            r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?$'
        )
        
        # Disposable email domains (sample list)
        self.disposable_domains = {
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'yopmail.com', 'tempmail.org', 'throwaway.email',
            'getnada.com', 'maildrop.cc', 'fakeinbox.com'
        }
        
        # Role-based email accounts
        self.role_accounts = {
            'admin', 'administrator', 'webmaster', 'noreply', 'no-reply',
            'support', 'help', 'info', 'sales', 'marketing', 'contact',
            'abuse', 'security', 'postmaster', 'hostmaster'
        }
    
    async def validate_email(
        self, 
        email: str, 
        verify_syntax: bool = True,
        verify_mx_record: bool = True,
        check_disposable: bool = True
    ) -> EmailValidationResult:
        """Validate email address with comprehensive checks."""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = generate_cache_key("email", email, f"check:{verify_syntax}:{verify_mx_record}:{check_disposable}")
            cached_result = await cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for email validation: {email}")
                return EmailValidationResult(**cached_result)
            
            # Validate syntax
            is_valid_syntax = bool(self.email_pattern.match(email))
            confidence_score = 0.5 if is_valid_syntax else 0.1
            
            if verify_syntax and not is_valid_syntax:
                result = EmailValidationResult(
                    value=email,
                    is_valid=False,
                    confidence_score=confidence_score,
                    validation_details={"syntax_error": "Invalid email format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            # Extract domain
            domain = email.split('@')[1].lower() if '@' in email else ''
            
            # Check domain exists and MX records
            domain_exists = False
            mx_record_exists = False
            dns_checks = {}
            
            if verify_mx_record:
                try:
                    loop = asyncio.get_event_loop()
                    domain_exists, mx_record_exists, dns_checks = await loop.run_in_executor(
                        self.executor, 
                        self._check_domain_mx_records, 
                        domain
                    )
                except Exception as e:
                    logger.warning(f"MX record check failed for {domain}: {e}")
                    dns_checks = {"error": str(e)}
            
            # Check if disposable
            is_disposable = check_disposable and domain in self.disposable_domains
            
            # Check if role account
            local_part = email.split('@')[0].lower() if '@' in email else ''
            is_role_account = local_part in self.role_accounts
            
            # Check if trash/format email
            is_trash = (is_disposable or 
                       bool(re.search(r'\+.*@', email)) or  # Plus addressing
                       bool(re.search(r'\..*@', local_part)))  # Dot before @
            
            # Generate suggestions for typos
            suggestions = await self._generate_email_suggestions(email, domain)
            
            # Calculate overall confidence
            confidence_score = self._calculate_email_confidence(
                is_valid_syntax, domain_exists, mx_record_exists, 
                not is_disposable, not is_role_account, not is_trash
            )
            
            # Build result
            result = EmailValidationResult(
                value=email,
                is_valid=is_valid_syntax and domain_exists and not is_disposable,
                confidence_score=confidence_score,
                validation_details={
                    "syntax_valid": is_valid_syntax,
                    "domain_exists": domain_exists,
                    **dns_checks
                },
                domain_exists=domain_exists,
                mx_record_exists=mx_record_exists,
                is_disposable=is_disposable,
                is_role_account=is_role_account,
                is_trash=is_trash,
                suggestions=suggestions
            )
            
            await self._cache_result(cache_key, result)
            logger.info(f"Email validation completed: {email} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Email validation error for {email}: {e}")
            return EmailValidationResult(
                value=email,
                is_valid=False,
                confidence_score=0.1,
                validation_details={"error": str(e)}
            )
    
    def _check_domain_mx_records(self, domain: str) -> Tuple[bool, bool, Dict[str, Any]]:
        """Check domain existence and MX records (synchronous)."""
        try:
            # Check if domain resolves
            socket.gethostbyname(domain)
            domain_exists = True
        except socket.gaierror:
            domain_exists = False
            return False, False, {"error": "Domain does not exist"}
        
        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record_exists = len(mx_records) > 0
            
            mx_data = [str(record.exchange) for record in mx_records]
            
            return domain_exists, mx_record_exists, {
                "mx_records": mx_data,
                "mx_count": len(mx_data)
            }
            
        except dns.resolver.NXDOMAIN:
            return domain_exists, False, {"error": "Domain does not exist"}
        except Exception as e:
            return domain_exists, False, {"error": f"DNS lookup failed: {e}"}
    
    async def _generate_email_suggestions(self, email: str, domain: str) -> List[str]:
        """Generate email correction suggestions."""
        suggestions = []
        
        try:
            # Common domain typos
            common_domains = {
                'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                'aol.com', 'icloud.com', 'protonmail.com'
            }
            
            if domain and domain not in common_domains:
                # Check for common misspellings
                for common_domain in common_domains:
                    if self._calculate_levenshtein_distance(domain, common_domain) <= 2:
                        local_part = email.split('@')[0] if '@' in email else email
                        suggestions.append(f"{local_part}@{common_domain}")
                        break
            
        except Exception as e:
            logger.warning(f"Suggestion generation failed: {e}")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _calculate_levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._calculate_levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _calculate_email_confidence(
        self,
        syntax_valid: bool,
        domain_exists: bool,
        mx_exists: bool,
        not_disposable: bool,
        not_role: bool,
        not_trash: bool
    ) -> float:
        """Calculate overall confidence score for email."""
        score = 0.0
        
        if syntax_valid: score += 0.2
        if domain_exists: score += 0.3
        if mx_exists: score += 0.3
        if not_disposable: score += 0.1
        if not_role: score += 0.05
        if not_trash: score += 0.05
        
        return min(score, 1.0)
    
    async def validate_domain(
        self,
        domain: str,
        check_dns: bool = True,
        check_whois: bool = False,
        check_reputation: bool = True
    ) -> DomainValidationResult:
        """Validate domain name with comprehensive checks."""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = generate_cache_key("domain", domain, f"check:{check_dns}:{check_whois}:{check_reputation}")
            cached_result = await cache_get(cache_key)
            if cached_result:
                return DomainValidationResult(**cached_result)
            
            # Validate domain format
            is_valid_format = self._is_valid_domain_format(domain)
            confidence_score = 0.3 if is_valid_format else 0.1
            
            if not is_valid_format:
                result = DomainValidationResult(
                    value=domain,
                    is_valid=False,
                    confidence_score=confidence_score,
                    validation_details={"format_error": "Invalid domain format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            # Check DNS
            dns_resolves = False
            nameservers = []
            dns_info = {}
            
            if check_dns:
                try:
                    loop = asyncio.get_event_loop()
                    dns_resolves, nameservers, dns_info = await loop.run_in_executor(
                        self.executor,
                        self._check_domain_dns,
                        domain
                    )
                except Exception as e:
                    logger.warning(f"DNS check failed for {domain}: {e}")
                    dns_info = {"error": str(e)}
            
            # Check if parked/squatted
            is_parked = dns_resolves and self._is_parked_domain(domain)
            is_squatted = not is_parked and self._is_squatted_domain(domain)
            
            # Check reputation (placeholder - would integrate with external APIs)
            reputation_score = None
            if check_reputation:
                reputation_score = await self._check_domain_reputation(domain)
            
            # Get domain info (placeholder for WHOIS)
            registration_info = {}
            if check_whois:
                registration_info = await self._get_domain_whois_info(domain)
            
            confidence_score = self._calculate_domain_confidence(
                is_valid_format, dns_resolves, not is_parked, not is_squatted
            )
            
            result = DomainValidationResult(
                value=domain,
                is_valid=is_valid_format and dns_resolves,
                confidence_score=confidence_score,
                validation_details={
                    "format_valid": is_valid_format,
                    **dns_info
                },
                dns_resolves=dns_resolves,
                is_parked=is_parked,
                is_squatted=is_squatted,
                registration_age_days=registration_info.get("age_days"),
                expires_at=registration_info.get("expires_at"),
                registrar=registration_info.get("registrar"),
                nameservers=nameservers
            )
            
            await self._cache_result(cache_key, result)
            logger.info(f"Domain validation completed: {domain} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Domain validation error for {domain}: {e}")
            return DomainValidationResult(
                value=domain,
                is_valid=False,
                confidence_score=0.1,
                validation_details={"error": str(e)}
            )
    
    def _is_valid_domain_format(self, domain: str) -> bool:
        """Check if domain has valid format."""
        if not domain or len(domain) > 253:
            return False
        
        domain = domain.lower().strip('.')
        
        if not self.domain_pattern.match(domain):
            return False
        
        # Check label lengths
        labels = domain.split('.')
        if len(labels) < 2:
            return False
        
        for label in labels:
            if len(label) < 1 or len(label) > 63:
                return False
        
        return True
    
    def _check_domain_dns(self, domain: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Check domain DNS resolution and nameservers."""
        try:
            # Check A record
            ip_address = socket.gethostbyname(domain)
            
            # Get nameservers
            ns_records = dns.resolver.resolve(domain, 'NS')
            nameservers = [str(ns) for ns in ns_records]
            
            return True, nameservers, {
                "ip_address": ip_address,
                "nameserver_count": len(nameservers)
            }
            
        except socket.gaierror:
            return False, [], {"error": "DNS resolution failed"}
        except Exception as e:
            return False, [], {"error": f"DNS lookup error: {e}"}
    
    def _is_parked_domain(self, domain: str) -> bool:
        """Check if domain appears to be parked (placeholder logic)."""
        # This would normally check for parked domain patterns
        # For now, return False as this requires external data
        return False
    
    def _is_squatted_domain(self, domain: str) -> bool:
        """Check if domain appears to be squatted (placeholder logic)."""
        # This would normally check against known trademark databases
        # For now, return False as this requires external data
        return False
    
    async def _check_domain_reputation(self, domain: str) -> Optional[float]:
        """Check domain reputation using external APIs."""
        try:
            # Placeholder - would integrate with VirusTotal, etc.
            return 0.8  # Good reputation
        except Exception as e:
            logger.warning(f"Reputation check failed for {domain}: {e}")
            return None
    
    async def _get_domain_whois_info(self, domain: str) -> Dict[str, Any]:
        """Get domain WHOIS information."""
        try:
            # Placeholder - would use python-whois library
            return {
                "registrar": "Unknown",
                "created_date": None,
                "expiry_date": None,
                "age_days": None
            }
        except Exception as e:
            logger.warning(f"WHOIS lookup failed for {domain}: {e}")
            return {}
    
    def _calculate_domain_confidence(
        self,
        format_valid: bool,
        dns_resolves: bool,
        not_parked: bool,
        not_squatted: bool
    ) -> float:
        """Calculate overall confidence score for domain."""
        score = 0.0
        
        if format_valid: score += 0.2
        if dns_resolves: score += 0.5
        if not_parked: score += 0.2
        if not_squatted: score += 0.1
        
        return min(score, 1.0)
    
    async def validate_ip(
        self,
        ip_address: str,
        check_reputation: bool = True,
        check_geolocation: bool = True
    ) -> IPValidationResult:
        """Validate IP address with comprehensive checks."""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = generate_cache_key("ip", ip_address, f"check:{check_reputation}:{check_geolocation}")
            cached_result = await cache_get(cache_key)
            if cached_result:
                return IPValidationResult(**cached_result)
            
            # Validate IP format
            is_valid_ip = self._is_valid_ip_format(ip_address)
            ip_version = self._get_ip_version(ip_address) if is_valid_ip else None
            confidence_score = 0.3 if is_valid_ip else 0.1
            
            if not is_valid_ip:
                result = IPValidationResult(
                    value=ip_address,
                    is_valid=False,
                    confidence_score=confidence_score,
                    validation_details={"format_error": "Invalid IP format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            # Check reputation (placeholder)
            reputation_score = None
            if check_reputation:
                reputation_score = await self._check_ip_reputation(ip_address)
            
            # Get geolocation (placeholder)
            geo_info = {}
            if check_geolocation:
                geo_info = await self._get_ip_geolocation(ip_address)
            
            # Check if IP is in known ranges (proxy, VPN, etc.)
            is_proxy, is_vpn, is_tor, is_datacenter = self._check_ip_reputation_flags(ip_address)
            
            confidence_score = self._calculate_ip_confidence(
                is_valid_ip, reputation_score, geo_info
            )
            
            result = IPValidationResult(
                value=ip_address,
                is_valid=is_valid_ip,
                confidence_score=confidence_score,
                validation_details={
                    "format_valid": is_valid_ip,
                    **geo_info
                },
                ip_version=ip_version,
                country=geo_info.get("country"),
                city=geo_info.get("city"),
                isp=geo_info.get("isp"),
                organization=geo_info.get("organization"),
                is_proxy=is_proxy,
                is_vpn=is_vpn,
                is_tor=is_tor,
                is_datacenter=is_datacenter,
                reputation_score=reputation_score
            )
            
            await self._cache_result(cache_key, result)
            logger.info(f"IP validation completed: {ip_address} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"IP validation error for {ip_address}: {e}")
            return IPValidationResult(
                value=ip_address,
                is_valid=False,
                confidence_score=0.1,
                validation_details={"error": str(e)}
            )
    
    def _is_valid_ip_format(self, ip_address: str) -> bool:
        """Check if IP address has valid format."""
        return bool(self.ipv4_pattern.match(ip_address) or self.ipv6_pattern.match(ip_address))
    
    def _get_ip_version(self, ip_address: str) -> Optional[int]:
        """Get IP version (4 or 6)."""
        if self.ipv4_pattern.match(ip_address):
            return 4
        elif self.ipv6_pattern.match(ip_address):
            return 6
        return None
    
    async def _check_ip_reputation(self, ip_address: str) -> Optional[float]:
        """Check IP reputation using external APIs."""
        try:
            # Placeholder - would integrate with AbuseIPDB, etc.
            return 0.8  # Good reputation
        except Exception as e:
            logger.warning(f"IP reputation check failed for {ip_address}: {e}")
            return None
    
    async def _get_ip_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get IP geolocation information."""
        try:
            # Placeholder - would integrate with IP geolocation API
            return {
                "country": "Unknown",
                "city": "Unknown",
                "isp": "Unknown",
                "organization": "Unknown"
            }
        except Exception as e:
            logger.warning(f"IP geolocation failed for {ip_address}: {e}")
            return {}
    
    def _check_ip_reputation_flags(self, ip_address: str) -> Tuple[bool, bool, bool, bool]:
        """Check if IP is in known reputation ranges."""
        try:
            # Parse IP address
            if self.ipv4_pattern.match(ip_address):
                octets = [int(octet) for octet in ip_address.split('.')]
                
                # Check for private IP ranges
                if (octets[0] == 10 or 
                    (octets[0] == 172 and 16 <= octets[1] <= 31) or
                    (octets[0] == 192 and octets[1] == 168)):
                    return False, False, False, False
                
                # Check for common data center ranges (placeholder)
                # This would normally check against known data center IP ranges
                
                return False, False, False, False
            
            return False, False, False, False
            
        except Exception:
            return False, False, False, False
    
    def _calculate_ip_confidence(
        self,
        format_valid: bool,
        reputation_score: Optional[float],
        geo_info: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score for IP."""
        score = 0.0
        
        if format_valid: score += 0.3
        if reputation_score and reputation_score > 0.5: score += 0.4
        if geo_info.get("country") and geo_info["country"] != "Unknown": score += 0.3
        
        return min(score, 1.0)
    
    async def validate_url(
        self,
        url: str,
        check_safety: bool = True,
        check_reputation: bool = True,
        follow_redirects: bool = True
    ) -> URLValidationResult:
        """Validate URL with comprehensive checks."""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = generate_cache_key("url", url, f"check:{check_safety}:{check_reputation}:{follow_redirects}")
            cached_result = await cache_get(cache_key)
            if cached_result:
                return URLValidationResult(**cached_result)
            
            # Validate URL format
            is_valid_url = bool(self.url_pattern.match(url))
            confidence_score = 0.3 if is_valid_url else 0.1
            
            if not is_valid_url:
                # Try to parse and fix URL
                try:
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme == '':
                        # Add https:// if missing
                        fixed_url = f"https://{url}"
                        if self.url_pattern.match(fixed_url):
                            url = fixed_url
                            is_valid_url = True
                            confidence_score = 0.4
                except Exception:
                    pass
            
            if not is_valid_url:
                result = URLValidationResult(
                    value=url,
                    is_valid=False,
                    confidence_score=confidence_score,
                    validation_details={"format_error": "Invalid URL format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            # Parse URL components
            parsed_url = urllib.parse.urlparse(url)
            response_info = {}
            final_url = url
            
            try:
                # Make HTTP request to check if URL is accessible
                loop = asyncio.get_event_loop()
                response_info = await loop.run_in_executor(
                    self.executor,
                    self._check_url_accessibility,
                    url,
                    follow_redirects
                )
                final_url = response_info.get("final_url", url)
                
            except Exception as e:
                logger.warning(f"URL accessibility check failed for {url}: {e}")
                response_info = {"error": str(e)}
            
            # Check safety (placeholder)
            is_malicious, is_phishing, is_suspicious, threat_categories = False, False, False, []
            if check_safety:
                is_malicious, is_phishing, is_suspicious, threat_categories = await self._check_url_safety(url)
            
            # Check reputation (placeholder)
            reputation_score = None
            if check_reputation:
                reputation_score = await self._check_url_reputation(url)
            
            confidence_score = self._calculate_url_confidence(
                is_valid_url, response_info.get("status_code", 0) < 400,
                not is_malicious, not is_phishing, not is_suspicious
            )
            
            result = URLValidationResult(
                value=url,
                is_valid=is_valid_url and response_info.get("status_code", 0) < 400,
                confidence_score=confidence_score,
                validation_details={
                    "format_valid": is_valid_url,
                    **response_info
                },
                final_url=final_url,
                response_status=response_info.get("status_code"),
                content_type=response_info.get("content_type"),
                page_title=response_info.get("page_title"),
                is_malicious=is_malicious,
                is_phishing=is_phishing,
                is_suspicious=is_suspicious,
                threat_categories=threat_categories,
                reputation_score=reputation_score
            )
            
            await self._cache_result(cache_key, result)
            logger.info(f"URL validation completed: {url} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"URL validation error for {url}: {e}")
            return URLValidationResult(
                value=url,
                is_valid=False,
                confidence_score=0.1,
                validation_details={"error": str(e)}
            )
    
    def _check_url_accessibility(self, url: str, follow_redirects: bool) -> Dict[str, Any]:
        """Check URL accessibility via HTTP request (synchronous)."""
        try:
            response = requests.get(
                url,
                timeout=10,
                allow_redirects=follow_redirects,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; CybersecAPI/1.0)'}
            )
            
            return {
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "page_title": self._extract_page_title(response.text) if response.text else "",
                "final_url": response.url,
                "redirects": len(response.history) if follow_redirects else 0
            }
            
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {"error": "Connection error"}
        except Exception as e:
            return {"error": f"HTTP request failed: {e}"}
    
    def _extract_page_title(self, html_content: str) -> str:
        """Extract page title from HTML content."""
        try:
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            return title_match.group(1).strip() if title_match else ""
        except Exception:
            return ""
    
    async def _check_url_safety(self, url: str) -> Tuple[bool, bool, bool, List[str]]:
        """Check URL safety using threat intelligence APIs."""
        try:
            # Placeholder - would integrate with URL filtering APIs
            # For now, return safe values
            return False, False, False, []
        except Exception as e:
            logger.warning(f"URL safety check failed for {url}: {e}")
            return False, False, False, []
    
    async def _check_url_reputation(self, url: str) -> Optional[float]:
        """Check URL reputation using external APIs."""
        try:
            # Placeholder - would integrate with URL reputation APIs
            return 0.8
        except Exception as e:
            logger.warning(f"URL reputation check failed for {url}: {e}")
            return None
    
    def _calculate_url_confidence(
        self,
        format_valid: bool,
        accessible: bool,
        not_malicious: bool,
        not_phishing: bool,
        not_suspicious: bool
    ) -> float:
        """Calculate overall confidence score for URL."""
        score = 0.0
        
        if format_valid: score += 0.2
        if accessible: score += 0.4
        if not_malicious: score += 0.2
        if not_phishing: score += 0.1
        if not_suspicious: score += 0.1
        
        return min(score, 1.0)
    
    async def validate_sender(
        self,
        email: str,
        domain: str,
        check_spf: bool = True,
        check_dkim: bool = True,
        check_dmarc: bool = True
    ) -> SenderValidationResult:
        """Validate email sender with SPF, DKIM, and DMARC checks."""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = generate_cache_key("sender", f"{email}_{domain}", f"check:{check_spf}:{check_dkim}:{check_dmarc}")
            cached_result = await cache_get(cache_key)
            if cached_result:
                return SenderValidationResult(**cached_result)
            
            # Basic validation
            if not self.email_pattern.match(email):
                result = SenderValidationResult(
                    value=f"{email}@{domain}",
                    is_valid=False,
                    confidence_score=0.1,
                    validation_details={"error": "Invalid email format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            if not self.domain_pattern.match(domain):
                result = SenderValidationResult(
                    value=f"{email}@{domain}",
                    is_valid=False,
                    confidence_score=0.1,
                    validation_details={"error": "Invalid domain format"}
                )
                await self._cache_result(cache_key, result)
                return result
            
            # Check SPF, DKIM, DMARC records
            spf_pass, spf_record = False, ""
            dkim_pass, dkim_record = False, ""
            dmarc_pass, dmarc_record = False, ""
            
            if check_spf:
                spf_pass, spf_record = await self._check_spf_record(domain)
            
            if check_dkim:
                dkim_pass, dkim_record = await self._check_dkim_record(domain)
            
            if check_dmarc:
                dmarc_pass, dmarc_record = await self._check_dmarc_record(domain)
            
            # Calculate overall validity and confidence
            all_pass = spf_pass and dkim_pass and dmarc_pass
            some_pass = spf_pass or dkim_pass or dmarc_pass
            
            confidence_score = self._calculate_sender_confidence(spf_pass, dkim_pass, dmarc_pass)
            
            result = SenderValidationResult(
                value=f"{email}@{domain}",
                is_valid=some_pass,  # Consider valid if at least one mechanism passes
                confidence_score=confidence_score,
                validation_details={
                    "spf_valid": spf_pass,
                    "dkim_valid": dkim_pass,
                    "dmarc_valid": dmarc_pass
                },
                spf_pass=spf_pass,
                dkim_pass=dkim_pass,
                dmarc_pass=dmarc_pass,
                spf_record=spf_record,
                dkim_record=dkim_record,
                dmarc_record=dmarc_record
            )
            
            await self._cache_result(cache_key, result)
            logger.info(f"Sender validation completed: {email}@{domain} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Sender validation error for {email}@{domain}: {e}")
            return SenderValidationResult(
                value=f"{email}@{domain}",
                is_valid=False,
                confidence_score=0.1,
                validation_details={"error": str(e)}
            )
    
    async def _check_spf_record(self, domain: str) -> Tuple[bool, str]:
        """Check SPF record for domain."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._get_spf_record_sync, domain)
        except Exception as e:
            logger.warning(f"SPF check failed for {domain}: {e}")
            return False, ""
    
    def _get_spf_record_sync(self, domain: str) -> Tuple[bool, str]:
        """Get SPF record (synchronous)."""
        try:
            txt_records = dns.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if txt_value.startswith('v=spf1'):
                    # Basic SPF validation
                    spf_pass = 'include:' not in txt_value or '~all' in txt_value or '-all' in txt_value
                    return spf_pass, txt_value
            return False, ""
        except Exception:
            return False, ""
    
    async def _check_dkim_record(self, domain: str) -> Tuple[bool, str]:
        """Check DKIM record for domain."""
        try:
            # DKIM records are typically stored under selector._domainkey.domain
            dkim_selector = "default"  # This would be configurable
            dkim_domain = f"{dkim_selector}._domainkey.{domain}"
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._get_dkim_record_sync, dkim_domain)
        except Exception as e:
            logger.warning(f"DKIM check failed for {domain}: {e}")
            return False, ""
    
    def _get_dkim_record_sync(self, dkim_domain: str) -> Tuple[bool, str]:
        """Get DKIM record (synchronous)."""
        try:
            txt_records = dns.resolver.resolve(dkim_domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if 'k=rsa' in txt_value or 'k=ed25519' in txt_value:
                    return True, txt_value
            return False, ""
        except Exception:
            return False, ""
    
    async def _check_dmarc_record(self, domain: str) -> Tuple[bool, str]:
        """Check DMARC record for domain."""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(self.executor, self._get_dmarc_record_sync, dmarc_domain)
        except Exception as e:
            logger.warning(f"DMARC check failed for {domain}: {e}")
            return False, ""
    
    def _get_dmarc_record_sync(self, dmarc_domain: str) -> Tuple[bool, str]:
        """Get DMARC record (synchronous)."""
        try:
            txt_records = dns.resolver.resolve(dmarc_domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if txt_value.startswith('v=DMARC1'):
                    # Basic DMARC validation
                    dmarc_pass = 'p=none' in txt_value or 'p=quarantine' in txt_value or 'p=reject' in txt_value
                    return dmarc_pass, txt_value
            return False, ""
        except Exception:
            return False, ""
    
    def _calculate_sender_confidence(
        self,
        spf_pass: bool,
        dkim_pass: bool,
        dmarc_pass: bool
    ) -> float:
        """Calculate overall confidence score for sender."""
        score = 0.0
        
        if spf_pass: score += 0.4
        if dkim_pass: score += 0.4
        if dmarc_pass: score += 0.2
        
        return min(score, 1.0)
    
    async def _cache_result(self, cache_key: str, result: ValidationResult):
        """Cache validation result."""
        try:
            if settings.CACHE_ENABLED:
                await cache_set(
                    cache_key, 
                    result.dict(), 
                    settings.CACHE_TTL_DEFAULT
                )
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
    
    # Bulk validation methods
    async def validate_bulk(
        self,
        emails: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        ip_addresses: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
        senders: Optional[List[Dict[str, Any]]] = None
    ) -> List[ValidationResult]:
        """Perform bulk validation."""
        start_time = datetime.utcnow()
        results = []
        
        try:
            tasks = []
            
            # Create validation tasks
            if emails:
                for email in emails:
                    tasks.append(self.validate_email(email))
            
            if domains:
                for domain in domains:
                    tasks.append(self.validate_domain(domain))
            
            if ip_addresses:
                for ip in ip_addresses:
                    tasks.append(self.validate_ip(ip))
            
            if urls:
                for url in urls:
                    tasks.append(self.validate_url(url))
            
            if senders:
                for sender in senders:
                    email = sender.get("email", "")
                    domain = sender.get("domain", "")
                    if email and domain:
                        tasks.append(self.validate_sender(email, domain))
            
            # Execute all tasks concurrently
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle exceptions
                processed_results = []
                for result in results:
                    if isinstance(result, Exception):
                        # Create error result
                        error_result = ValidationResult(
                            value="unknown",
                            is_valid=False,
                            confidence_score=0.1,
                            validation_details={"error": str(result)}
                        )
                        processed_results.append(error_result)
                    else:
                        processed_results.append(result)
                
                results = processed_results
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Bulk validation completed: {len(results)} items in {processing_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"Bulk validation error: {e}")
            # Return error result
            return [ValidationResult(
                value="bulk_validation_failed",
                is_valid=False,
                confidence_score=0.0,
                validation_details={"error": str(e)}
            )]


# Global validation service instance
validation_service = ValidationService()