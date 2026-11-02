#!/usr/bin/env python3
"""
SecurityTrails API Collector
Provides threat intelligence from SecurityTrails
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class SecurityTrailsCollector(BaseThreatCollector):
    """SecurityTrails collector"""
    
    def __init__(self, api_key: str):
        super().__init__("SecurityTrails", rate_limit=100, time_window=86400)  # 100 requests per day (free tier)
        self.set_api_key(api_key, "apikey")
        self.base_url = "https://api.securitytrails.com/v1"
    
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
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Get IP information
            url = f"{self.base_url}/ips/{ip}/current"
            data = await self._make_request(url)
            
            if data:
                ip_info = data
                
                # Extract domains associated with this IP
                domains = ip_info.get('domains', [])
                tags = ['ip-intelligence']
                
                if domains:
                    tags.append('has-associated-domains')
                    confidence = min(0.8, len(domains) * 0.1)
                else:
                    confidence = 0.0
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'associated_domains': domains,
                        'total_domains': len(domains),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=len(domains)
                )
                results.append(result)
                
                # Get historical data
                await self._get_ip_history(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in SecurityTrails: {str(e)}")
        
        return results
    
    async def _get_ip_history(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get IP historical data"""
        try:
            url = f"{self.base_url}/ips/{ip}/history"
            data = await self._make_request(url)
            
            if data and 'records' in data:
                records = data['records']
                
                if records:
                    # Analyze historical data
                    recent_domains = []
                    all_domains = set()
                    date_range = None
                    
                    for record in records[:10]:  # First 10 records
                        domains = record.get('domains', [])
                        all_domains.update(domains)
                        if record.get('first_seen') and record.get('last_seen'):
                            recent_domains.extend(domains)
                    
                    if not date_range and records:
                        date_range = {
                            'earliest': records[-1].get('first_seen'),
                            'latest': records[0].get('last_seen')
                        }
                    
                    history_data = {
                        'historical_info': {
                            'total_records': len(records),
                            'unique_domains': len(all_domains),
                            'current_domains': list(all_domains),
                            'date_range': date_range,
                            'sample_records': records[:5]
                        },
                        'raw_url': url
                    }
                    
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data=history_data,
                        tags=['ip-history', 'historical-analysis'],
                        confidence=0.6,
                        score=len(all_domains)
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting IP history for {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Get domain information
            url = f"{self.base_url}/domain/{domain}/current"
            data = await self._make_request(url)
            
            if data:
                domain_info = data
                
                tags = ['domain-intelligence']
                confidence = 0.0
                score = 0
                
                # Check for associated IPs
                associated_ips = domain_info.get('current', {}).get('A', [])
                if associated_ips:
                    tags.append('has-ip-addresses')
                    confidence = min(0.8, len(associated_ips) * 0.2)
                    score += len(associated_ips)
                
                # Check for subdomains
                subdomains = domain_info.get('current', {}).get('subdomains', [])
                if subdomains:
                    tags.append('has-subdomains')
                    confidence += min(0.2, len(subdomains) * 0.01)
                    score += len(subdomains)
                
                # Check for MX records (mail servers)
                mx_records = domain_info.get('current', {}).get('MX', [])
                if mx_records:
                    tags.append('has-mail-servers')
                
                # Check for NS records (name servers)
                ns_records = domain_info.get('current', {}).get('NS', [])
                if ns_records:
                    tags.append('has-name-servers')
                
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'current_records': domain_info.get('current', {}),
                        'associated_ips': associated_ips,
                        'subdomains': subdomains,
                        'mx_records': mx_records,
                        'ns_records': ns_records,
                        'total_subdomains': len(subdomains),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
                
                # Get domain history
                await self._get_domain_history(domain, results)
                
                # Get subdomain information
                await self._get_domain_subdomains(domain, results)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in SecurityTrails: {str(e)}")
        
        return results
    
    async def _get_domain_history(self, domain: str, results: List[ThreatIntelligenceData]):
        """Get domain historical data"""
        try:
            url = f"{self.base_url}/domain/{domain}/history"
            data = await self._make_request(url)
            
            if data and 'records' in data:
                records = data['records']
                
                if records:
                    # Analyze historical DNS changes
                    ip_changes = 0
                    mx_changes = 0
                    ns_changes = 0
                    
                    for record in records[:20]:  # Check first 20 records
                        record_data = record.get('record', {})
                        
                        if record_data.get('A'):
                            ip_changes += 1
                        if record_data.get('MX'):
                            mx_changes += 1
                        if record_data.get('NS'):
                            ns_changes += 1
                    
                    history_data = {
                        'dns_history': {
                            'total_changes': len(records),
                            'ip_changes': ip_changes,
                            'mx_changes': mx_changes,
                            'ns_changes': ns_changes,
                            'date_range': {
                                'start': records[-1].get('first_seen'),
                                'end': records[0].get('last_seen')
                            },
                            'sample_changes': records[:5]
                        },
                        'raw_url': url
                    }
                    
                    tags = ['domain-history']
                    if ip_changes > 5:
                        tags.append('frequent-ip-changes')
                    if mx_changes > 3:
                        tags.append('frequent-mx-changes')
                    
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data=history_data,
                        tags=tags,
                        confidence=0.7,
                        score=ip_changes + mx_changes + ns_changes
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting domain history for {domain}: {str(e)}")
    
    async def _get_domain_subdomains(self, domain: str, results: List[ThreatIntelligenceData]):
        """Get subdomain information"""
        try:
            url = f"{self.base_url}/domain/{domain}/subdomains"
            data = await self._make_request(url)
            
            if data and 'subdomains' in data:
                subdomains = data['subdomains']
                
                subdomain_data = {
                    'subdomain_info': {
                        'total_subdomains': len(subdomains),
                        'subdomains': subdomains,
                        'raw_count': data.get('total', 0)
                    },
                    'raw_url': url
                }
                
                tags = ['subdomain-enumeration']
                result = self.normalize_domain_data(
                    indicator=domain,
                    data=subdomain_data,
                    tags=tags,
                    confidence=0.5,
                    score=len(subdomains)
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error getting subdomains for {domain}: {str(e)}")
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            from urllib.parse import urlparse
            
            # Extract domain from URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            if domain:
                # Search for the domain
                domain_results = await self.lookup_domain(domain)
                
                # Add URL context
                for domain_result in domain_results:
                    url_result = self.normalize_url_data(
                        indicator=url,
                        data={
                            'domain_info': domain_result.raw_data,
                            'full_url': url,
                            'domain': domain,
                            'path': parsed.path,
                            'query': parsed.query,
                            'note': 'Information derived from SecurityTrails domain search'
                        },
                        tags=domain_result.tags + ['url-analysis'],
                        confidence=domain_result.confidence * 0.9,
                        score=domain_result.score
                    )
                    results.append(url_result)
                    
        except Exception as e:
            logger.error(f"Error looking up URL {url} in SecurityTrails: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - SecurityTrails doesn't support hash lookups"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'SecurityTrails does not support file hash lookups',
                'supported_indicators': ['domains', 'IP addresses', 'subdomains'],
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
    """Example usage of SecurityTrails collector"""
    # Set your SecurityTrails API key here
    api_key = "YOUR_SECURITYTRAILS_API_KEY"
    
    async with SecurityTrailsCollector(api_key) as collector:
        # Test domain lookup
        print("Testing domain lookup...")
        domain_results = await collector.lookup_domain("google.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test IP lookup
        print("\nTesting IP lookup...")
        ip_results = await collector.lookup_ip("8.8.8.8")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test URL lookup
        print("\nTesting URL lookup...")
        url_results = await collector.lookup_url("https://www.google.com/search?q=test")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())