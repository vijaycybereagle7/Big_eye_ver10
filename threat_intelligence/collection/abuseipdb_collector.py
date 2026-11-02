#!/usr/bin/env python3
"""
AbuseIPDB API Collector
Provides threat intelligence from AbuseIPDB
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class AbuseIPDBCollector(BaseThreatCollector):
    """AbuseIPDB collector"""
    
    def __init__(self, api_key: str):
        super().__init__("AbuseIPDB", rate_limit=1000, time_window=86400)  # 1000 requests per day
        self.set_api_key(api_key, "Key")
        self.base_url = "https://api.abuseipdb.com/api/v2"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if IP address is valid"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except:
            return False
    
    def _calculate_abuse_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate abuse confidence from data"""
        total_reports = data.get('totalReports', 0)
        abuse_confidence_score = data.get('abuseConfidenceScore', 0)
        is_whitelisted = data.get('isWhitelisted', False)
        is_public = data.get('isPublic', True)
        
        if is_whitelisted:
            return 0.0
        if abuse_confidence_score > 0:
            return min(1.0, abuse_confidence_score / 100.0)
        if total_reports > 0 and not is_public:
            return 0.5
        
        return 0.0
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Get IP check data
            params = {
                'ipAddress': ip,
                'maxAgeInDays': '90'
            }
            
            url = f"{self.base_url}/check"
            data = await self._make_request(url, params=params)
            
            if data and 'data' in data:
                ip_data = data['data']
                
                # Extract threat intelligence
                abuse_confidence_score = self._calculate_abuse_confidence(ip_data)
                tags = []
                
                # Add relevant tags based on data
                if ip_data.get('abuseConfidenceScore', 0) > 50:
                    tags.append('high-confidence-abuse')
                if ip_data.get('totalReports', 0) > 0:
                    tags.append('reported-malicious')
                if ip_data.get('isTor', False):
                    tags.append('tor-node')
                if ip_data.get('isWhiteListed', False):
                    tags.append('whitelisted')
                if ip_data.get('hostnames'):
                    tags.append('has-hostname')
                
                # Create main result
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'ip': ip_data.get('ipAddress'),
                        'abuse_confidence_score': ip_data.get('abuseConfidenceScore'),
                        'total_reports': ip_data.get('totalReports'),
                        'is_public': ip_data.get('isPublic'),
                        'is_tor': ip_data.get('isTor'),
                        'is_whitelisted': ip_data.get('isWhiteListed'),
                        'isp': ip_data.get('isp'),
                        'domain': ip_data.get('domain'),
                        'country_code': ip_data.get('countryCode'),
                        'country_name': ip_data.get('countryName'),
                        'usage_type': ip_data.get('usageType'),
                        'hostnames': ip_data.get('hostnames'),
                        'is_known_abuser': ip_data.get('isKnownAbuser', False),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=abuse_confidence_score,
                    score=ip_data.get('abuseConfidenceScore', 0)
                )
                results.append(result)
                
                # Get recent reports if any exist
                await self._get_ip_reports(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in AbuseIPDB: {str(e)}")
        
        return results
    
    async def _get_ip_reports(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get recent reports for IP address"""
        try:
            # Get blacklist data which might contain reports
            url = f"{self.base_url}/blacklist"
            params = {
                'limit': '100',
                'onlyActive': 'false'
            }
            
            blacklist_data = await self._make_request(url, params=params)
            
            if blacklist_data and 'data' in blacklist_data:
                # Look for the IP in blacklist data
                for entry in blacklist_data['data']:
                    if entry.get('ipAddress') == ip:
                        report_data = {
                            'blacklist_entry': {
                                'date_added': entry.get('dateAdded'),
                                'ip': entry.get('ipAddress'),
                                'num_reports': entry.get('numReports'),
                                'country_code': entry.get('countryCode'),
                                'country_name': entry.get('countryName'),
                                'iso_code': entry.get('isoCode'),
                                'is_whitelisted': entry.get('isWhitelisted'),
                                'abuse_confidence_score': entry.get('abuseConfidenceScore'),
                                'most_recent_report': entry.get('mostRecentReport'),
                                'times_reported': entry.get('timesReported'),
                                'publish_date': entry.get('publishDate')
                            },
                            'raw_url': url
                        }
                        
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data=report_data,
                            tags=['blacklist-report'],
                            confidence=min(1.0, entry.get('abuseConfidenceScore', 0) / 100.0)
                        )
                        results.append(result)
                        break
                        
        except Exception as e:
            logger.error(f"Error getting reports for IP {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information - AbuseIPDB primarily focuses on IPs"""
        # AbuseIPDB doesn't provide domain lookup directly
        # Could potentially resolve domain to IP and check that
        results = []
        
        try:
            import socket
            
            # Resolve domain to IP
            try:
                ip = socket.gethostbyname(domain)
                
                # Look up the resolved IP
                ip_results = await self.lookup_ip(ip)
                
                # Convert to domain results with additional context
                for ip_result in ip_results:
                    domain_result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'resolved_ip': ip,
                            'original_ip_data': ip_result.raw_data,
                            'note': 'Information derived from resolved IP address'
                        },
                        tags=ip_result.tags + ['domain-resolution'],
                        confidence=ip_result.confidence * 0.8,  # Slightly lower confidence for domain
                        score=ip_result.score
                    )
                    results.append(domain_result)
                    
            except socket.gaierror:
                logger.warning(f"Could not resolve domain {domain} to IP")
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in AbuseIPDB: {str(e)}")
        
        return results
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information - AbuseIPDB primarily focuses on IPs"""
        # Extract domain from URL and check that
        results = []
        
        try:
            from urllib.parse import urlparse
            
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            if domain:
                domain_results = await self.lookup_domain(domain)
                
                # Add URL context
                for domain_result in domain_results:
                    url_result = self.normalize_url_data(
                        indicator=url,
                        data={
                            'domain_data': domain_result.raw_data,
                            'full_url': url,
                            'note': 'Information derived from URL domain'
                        },
                        tags=domain_result.tags + ['url-analysis'],
                        confidence=domain_result.confidence * 0.9,
                        score=domain_result.score
                    )
                    results.append(url_result)
                    
        except Exception as e:
            logger.error(f"Error looking up URL {url} in AbuseIPDB: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - AbuseIPDB doesn't support hash lookups"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'AbuseIPDB does not support file hash lookups',
                'supported_indicators': ['IP addresses'],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results


# Example usage and testing
async def main():
    """Example usage of AbuseIPDB collector"""
    # Set your AbuseIPDB API key here
    api_key = "YOUR_ABUSEIPDB_API_KEY"
    
    async with AbuseIPDBCollector(api_key) as collector:
        # Test IP lookup
        print("Testing IP lookup...")
        ip_results = await collector.lookup_ip("8.8.8.8")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test domain lookup
        print("\nTesting domain lookup...")
        domain_results = await collector.lookup_domain("google.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test URL lookup
        print("\nTesting URL lookup...")
        url_results = await collector.lookup_url("https://www.google.com/search?q=test")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())