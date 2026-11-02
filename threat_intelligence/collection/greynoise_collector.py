#!/usr/bin/env python3
"""
GreyNoise API Collector
Provides threat intelligence from GreyNoise
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class GreyNoiseCollector(BaseThreatCollector):
    """GreyNoise collector"""
    
    def __init__(self, api_key: str):
        super().__init__("GreyNoise", rate_limit=1000, time_window=3600)  # 1000 requests per hour
        self.set_api_key(api_key, "key")
        self.base_url = "https://api.greynoise.io/v2"
    
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
    
    def _classify_noise_level(self, classification: str) -> List[str]:
        """Classify GreyNoise classification"""
        tags = ['greynoise']
        
        classification_lower = classification.lower()
        
        if classification_lower == 'malicious':
            tags.append('malicious-activity')
            tags.append('threat-actor')
        elif classification_lower == 'benign':
            tags.append('legitimate-traffic')
            tags.append('safe')
        elif classification_lower == 'unknown':
            tags.append('unknown-classification')
            tags.append('unclassified')
        else:
            tags.append(f'classification-{classification_lower}')
        
        return tags
    
    def _extract_tags(self, ip_data: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from GreyNoise IP data"""
        tags = []
        
        # From classification
        if 'classification' in ip_data:
            tags.extend(self._classify_noise_level(ip_data['classification']))
        
        # From raw_tags
        if 'raw_tags' in ip_data:
            tags.extend(ip_data['raw_tags'])
        
        # From activity
        if 'seen' in ip_data:
            tags.append('scanner-activity')
            if ip_data['seen'].get('first_seen'):
                tags.append('recent-activity')
        
        # From metadata
        if 'metadata' in ip_data:
            metadata = ip_data['metadata']
            if metadata.get('asn'):
                tags.append(f"asn-{metadata['asn'].replace('AS', '')}")
            if metadata.get('country'):
                tags.append(f"country-{metadata['country'].lower()}")
            if metadata.get('os'):
                tags.append(f"os-{metadata['os'].lower()}")
            if metadata.get('category'):
                tags.append(f"category-{metadata['category'].lower()}")
        
        # From bot status
        if ip_data.get('bot'):
            tags.append('bot-detection')
            if ip_data['bot'].get('status') == 'True':
                tags.append('confirmed-bot')
        
        return tags
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Get IP information
            url = f"{self.base_url}/ip/{ip}"
            data = await self._make_request(url)
            
            if data:
                ip_data = data
                
                # Determine confidence based on classification
                classification = ip_data.get('classification', 'unknown')
                
                if classification == 'malicious':
                    confidence = 0.9
                    score = 90
                elif classification == 'benign':
                    confidence = 0.8
                    score = 20
                elif classification == 'unknown':
                    confidence = 0.5
                    score = 50
                else:
                    confidence = 0.3
                    score = 30
                
                # If IP is not in GreyNoise database
                if 'noise' in ip_data and not ip_data['noise']:
                    confidence = 0.1
                    score = 0
                    classification = 'not-noisy'
                
                tags = self._extract_tags(ip_data)
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'ip': ip_data.get('ip'),
                        'classification': classification,
                        'name': ip_data.get('name'),
                        'link': ip_data.get('link'),
                        'seen': ip_data.get('seen', {}),
                        'raw_data': ip_data,
                        'noise': ip_data.get('noise', False),
                        'riot': ip_data.get('riot', False),
                        'bot': ip_data.get('bot', {}),
                        'metadata': ip_data.get('metadata', {}),
                        'raw_tags': ip_data.get('raw_tags', []),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
                
                # Get timeline if available
                await self._get_ip_timeline(ip, results)
                
                # Get tags
                await self._get_ip_tags(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in GreyNoise: {str(e)}")
        
        return results
    
    async def _get_ip_timeline(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get IP timeline information"""
        try:
            url = f"{self.base_url}/ip/{ip}/timeline"
            data = await self._make_request(url)
            
            if data and 'timeline' in data:
                timeline_data = {
                    'timeline_info': {
                        'timeline': data['timeline'],
                        'period': data.get('period'),
                        'period_start': data.get('period_start'),
                        'period_end': data.get('period_end')
                    },
                    'raw_url': url
                }
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data=timeline_data,
                    tags=['greynoise-timeline'],
                    confidence=0.7,
                    score=5
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error getting timeline for IP {ip}: {str(e)}")
    
    async def _get_ip_tags(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get IP tags information"""
        try:
            url = f"{self.base_url}/ip/{ip}/tags"
            data = await self._make_request(url)
            
            if data and 'tags' in data:
                tags_data = {
                    'tags_info': {
                        'tags': data['tags'],
                        'tag_count': len(data['tags']),
                        'categories': data.get('categories', {})
                    },
                    'raw_url': url
                }
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data=tags_data,
                    tags=['greynoise-tags'],
                    confidence=0.6,
                    score=len(data['tags'])
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error getting tags for IP {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information - GreyNoise primarily focuses on IPs"""
        results = []
        
        try:
            # GreyNoise doesn't provide direct domain lookup
            # We can check if the domain has any known associated IPs
            import socket
            
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
                            'ip_intelligence': ip_result.raw_data,
                            'note': 'Information derived from resolved IP address'
                        },
                        tags=ip_result.tags + ['domain-resolution'],
                        confidence=ip_result.confidence * 0.7,  # Lower confidence for domain inference
                        score=ip_result.score * 0.7
                    )
                    results.append(domain_result)
                    
            except socket.gaierror:
                logger.warning(f"Could not resolve domain {domain} to IP")
                
                # Still return a result indicating domain not resolvable
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'status': 'unresolvable',
                        'note': 'Domain does not resolve to an IP address'
                    },
                    tags=['unresolvable-domain'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in GreyNoise: {str(e)}")
        
        return results
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information - GreyNoise primarily focuses on IPs"""
        results = []
        
        try:
            from urllib.parse import urlparse
            
            # Extract domain from URL
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
                            'domain': domain,
                            'path': parsed_url.path,
                            'query': parsed_url.query,
                            'note': 'Information derived from URL domain'
                        },
                        tags=domain_result.tags + ['url-analysis'],
                        confidence=domain_result.confidence * 0.9,
                        score=domain_result.score
                    )
                    results.append(url_result)
                    
        except Exception as e:
            logger.error(f"Error looking up URL {url} in GreyNoise: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - GreyNoise doesn't support hash lookups"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'GreyNoise does not support file hash lookups',
                'supported_indicators': ['IP addresses'],
                'specializes_in': 'Internet background noise and scanning activity',
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def gnql_search(self, query: str, size: int = 100) -> List[ThreatIntelligenceData]:
        """Search using GreyNoise Query Language (GNQL)"""
        results = []
        
        try:
            url = f"{self.base_url}/gnql"
            params = {
                'query': query,
                'size': str(size)
            }
            
            data = await self._make_request(url, params=params)
            
            if data and 'data' in data:
                for ip_info in data['data'][:size]:
                    ip = ip_info.get('ip', '')
                    
                    if self._is_valid_ip(ip):
                        tags = self._extract_tags(ip_info)
                        tags.append('gnql-search-result')
                        
                        # Determine confidence based on classification
                        classification = ip_info.get('classification', 'unknown')
                        if classification == 'malicious':
                            confidence = 0.9
                            score = 90
                        elif classification == 'benign':
                            confidence = 0.8
                            score = 20
                        else:
                            confidence = 0.6
                            score = 50
                        
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data={
                                'gnql_query': query,
                                'ip_data': ip_info,
                                'rank': ip_info.get('rank'),
                                'raw_url': url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=score
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error in GNQL search with query '{query}': {str(e)}")
        
        return results
    
    async def get_riot_ips(self) -> List[ThreatIntelligenceData]:
        """Get IPs in GreyNoise RIOT (Reputation Intelligence on Threats) list"""
        results = []
        
        try:
            url = f"{self.base_url}/riot"
            data = await self._make_request(url)
            
            if data and 'ips' in data:
                for ip_entry in data['ips']:
                    ip = ip_entry.get('ip', '')
                    
                    if self._is_valid_ip(ip):
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data={
                                'riot_info': ip_entry,
                                'provider': ip_entry.get('provider'),
                                'category': ip_entry.get('category'),
                                'raw_url': url
                            },
                            tags=['greynoise-riot', 'reputation-intelligence'],
                            confidence=0.9,
                            score=95
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error getting RIOT IPs: {str(e)}")
        
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get GreyNoise stats"""
        try:
            url = f"{self.base_url}/stats"
            data = await self._make_request(url)
            return data
        except Exception as e:
            logger.error(f"Error getting GreyNoise stats: {str(e)}")
            return None


# Example usage and testing
async def main():
    """Example usage of GreyNoise collector"""
    # Set your GreyNoise API key here
    api_key = "YOUR_GREYNOISE_API_KEY"
    
    async with GreyNoiseCollector(api_key) as collector:
        # Test IP lookup
        print("Testing IP lookup...")
        ip_results = await collector.lookup_ip("8.8.8.8")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test domain lookup
        print("\nTesting domain lookup...")
        domain_results = await collector.lookup_domain("google.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test GNQL search
        print("\nTesting GNQL search...")
        gnql_results = await collector.gnql_search("classification:malicious country:US", size=5)
        print(f"GNQL results: {len(gnql_results)} found")
        for result in gnql_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test RIOT list
        print("\nTesting RIOT list...")
        riot_results = await collector.get_riot_ips()
        print(f"RIOT results: {len(riot_results)} found")
        for result in riot_results[:3]:  # Show first 3
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Get stats
        print("\nGetting GreyNoise stats...")
        stats = await collector.get_stats()
        if stats:
            print(f"Stats: {stats}")


if __name__ == "__main__":
    asyncio.run(main())