#!/usr/bin/env python3
"""
URLhaus API Collector
Provides threat intelligence from URLhaus (malware URL database)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class URLhausCollector(BaseThreatCollector):
    """URLhaus collector"""
    
    def __init__(self, api_key: str = None):  # URLhaus doesn't require API key for public API
        super().__init__("URLhaus", rate_limit=1000, time_window=3600)  # 1000 requests per hour
        # URLhaus public API doesn't require authentication
        self.base_url = "https://urlhaus-api.abuse.ch/v1"
    
    def _canonicalize_url(self, url: str) -> str:
        """Canonicalize URL for lookup"""
        if not url.startswith(('http://', 'https://')):
            url = f'http://{url}'
        return url
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url
    
    def _classify_malware_family(self, signature: str) -> List[str]:
        """Classify malware based on signature"""
        signature_lower = signature.lower()
        malware_families = []
        
        # Common malware families
        families = {
            'emotet': ['emotet', 'geodo', 'heodo'],
            'trickbot': ['trickbot', 'trickloader'],
            'ransomware': ['ransom', 'locky', 'cerber', 'wannacry'],
            'banking_trojan': ['banking', 'zeus', 'gozi'],
            'botnet': ['botnet', 'bot', 'c&c', 'command-and-control'],
            'stealer': ['stealer', 'mimikatz', 'credential'],
            'loader': ['loader', 'dropper', 'installer'],
            'backdoor': ['backdoor', 'remote-access'],
            'rootkit': ['rootkit', 'kernel'],
            'cryptominer': ['crypto', 'mining', 'monero']
        }
        
        for family_name, keywords in families.items():
            if any(keyword in signature_lower for keyword in keywords):
                malware_families.append(family_name)
        
        return malware_families
    
    def _classify_threat_level(self, threat_level: str) -> str:
        """Classify threat level"""
        level = threat_level.lower()
        if level == 'online':
            return 'active'
        elif level == 'offline':
            return 'inactive'
        elif level == 'unknown':
            return 'unknown'
        else:
            return 'undetermined'
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # Canonicalize URL
            canonical_url = self._canonicalize_url(url)
            
            # URL submission lookup
            url_api = f"{self.base_url}/url/"
            params = {'url': canonical_url}
            
            data = await self._make_request(url_api, params=params)
            
            if data and data.get('query_status') == 'ok':
                url_info = data
                
                # Extract threat intelligence
                tags = ['urlhaus-url']
                threat_level = url_info.get('threat_level', 'unknown')
                status = self._classify_threat_level(threat_level)
                
                tags.append(f"threat-level-{status}")
                
                # Add malware family tags
                signature = url_info.get('signature', '')
                if signature:
                    families = self._classify_malware_family(signature)
                    tags.extend([f"malware-{family}" for family in families])
                    tags.append('malicious-signature')
                
                # Calculate confidence
                confidence = 0.8 if status == 'active' else 0.6 if status == 'inactive' else 0.3
                
                if signature:
                    confidence = min(1.0, confidence + 0.2)
                
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data={
                        'url_id': url_info.get('url_id'),
                        'threat_level': threat_level,
                        'threat_types': url_info.get('threat_types', []),
                        'malware_family': url_info.get('malware_family', signature),
                        'signature': signature,
                        'reporter': url_info.get('reporter'),
                        'date_added': url_info.get('date_added'),
                        'last_online': url_info.get('last_online'),
                        'host': url_info.get('host'),
                        'ip_address': url_info.get('ip_address'),
                        'country': url_info.get('country'),
                        'url_status': url_info.get('url_status'),
                        'larted': url_info.get('larted'),  # Link added to redirect lists
                        'tags': url_info.get('tags', []),
                        'raw_url': url_api
                    },
                    tags=tags,
                    confidence=confidence,
                    score=10 if status == 'active' else 5
                )
                results.append(result)
                
                # Get sample information if available
                await self._get_url_sample(canonical_url, results)
                
            else:
                # URL not found in URLhaus
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data={
                        'query_status': 'not_found',
                        'status': 'clean',
                        'raw_url': url_api
                    },
                    tags=['urlhaus-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in URLhaus: {str(e)}")
        
        return results
    
    async def _get_url_sample(self, url: str, results: List[ThreatIntelligenceData]):
        """Get sample information for URL"""
        try:
            # Check if there's a sample associated with this URL
            sample_api = f"{self.base_url}/sample/"
            params = {'url': url}
            
            data = await self._make_request(sample_api, params=params)
            
            if data and data.get('query_status') == 'ok' and 'samples' in data:
                for sample in data['samples'][:5]:  # First 5 samples
                    sample_data = {
                        'sample_info': {
                            'file_type': sample.get('file_type'),
                            'file_size': sample.get('file_size'),
                            'file_name': sample.get('file_name'),
                            'sha256_hash': sample.get('sha256_hash'),
                            'first_seen': sample.get('first_seen'),
                            'last_seen': sample.get('last_seen'),
                            'signature': sample.get('signature'),
                            'imphash': sample.get('imphash'),
                            'tlsh': sample.get('tlsh')
                        },
                        'raw_url': sample_api
                    }
                    
                    tags = ['urlhaus-sample', 'malware-sample']
                    if sample.get('file_type'):
                        tags.append(f"file-type-{sample['file_type'].lower()}")
                    
                    result = self.normalize_url_data(
                        indicator=url,
                        data=sample_data,
                        tags=tags,
                        confidence=0.8,
                        score=5
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting sample for URL {url}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Domain submission lookup
            domain_api = f"{self.base_url}/domain/"
            params = {'domain': domain}
            
            data = await self._make_request(domain_api, params=params)
            
            if data and data.get('query_status') == 'ok':
                domain_info = data
                
                # Extract threat intelligence
                tags = ['urlhaus-domain']
                urls_count = domain_info.get('urls_count', 0)
                status = domain_info.get('threat_level', 'unknown')
                
                if status:
                    tags.append(f"threat-level-{status}")
                
                if urls_count > 0:
                    tags.append('has-malicious-urls')
                    confidence = min(0.9, urls_count * 0.1)
                else:
                    confidence = 0.3
                
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'domain_id': domain_info.get('domain_id'),
                        'threat_level': domain_info.get('threat_level'),
                        'urls_count': urls_count,
                        'first_seen': domain_info.get('first_seen'),
                        'last_seen': domain_info.get('last_seen'),
                        'country': domain_info.get('country'),
                        'asn': domain_info.get('asn'),
                        'registrar': domain_info.get('registrar'),
                        'malicious_urls_sample': domain_info.get('urls_sample', [])[:5],
                        'raw_url': domain_api
                    },
                    tags=tags,
                    confidence=confidence,
                    score=urls_count
                )
                results.append(result)
                
            else:
                # Domain not found in URLhaus
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'query_status': 'not_found',
                        'status': 'clean',
                        'raw_url': domain_api
                    },
                    tags=['urlhaus-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in URLhaus: {str(e)}")
        
        return results
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        try:
            # IP submission lookup
            ip_api = f"{self.base_url}/host/"
            params = {'host': ip}
            
            data = await self._make_request(ip_api, params=params)
            
            if data and data.get('query_status') == 'ok':
                ip_info = data
                
                # Extract threat intelligence
                tags = ['urlhaus-ip']
                urls_count = ip_info.get('urls_count', 0)
                status = ip_info.get('threat_level', 'unknown')
                
                if status:
                    tags.append(f"threat-level-{status}")
                
                if urls_count > 0:
                    tags.append('has-malicious-urls')
                    confidence = min(0.9, urls_count * 0.1)
                else:
                    confidence = 0.3
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'host_id': ip_info.get('host_id'),
                        'threat_level': ip_info.get('threat_level'),
                        'urls_count': urls_count,
                        'first_seen': ip_info.get('first_seen'),
                        'last_seen': ip_info.get('last_seen'),
                        'country': ip_info.get('country'),
                        'asn': ip_info.get('asn'),
                        'malicious_urls_sample': ip_info.get('urls_sample', [])[:5],
                        'raw_url': ip_api
                    },
                    tags=tags,
                    confidence=confidence,
                    score=urls_count
                )
                results.append(result)
                
            else:
                # IP not found in URLhaus
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'query_status': 'not_found',
                        'status': 'clean',
                        'raw_url': ip_api
                    },
                    tags=['urlhaus-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in URLhaus: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash information"""
        results = []
        
        try:
            # Sample lookup by hash
            sample_api = f"{self.base_url}/sample/"
            params = {'hash': file_hash.lower()}
            
            data = await self._make_request(sample_api, params=params)
            
            if data and data.get('query_status') == 'ok':
                sample_info = data
                
                # Extract threat intelligence
                tags = ['urlhaus-sample']
                signature = sample_info.get('signature', '')
                
                if signature:
                    families = self._classify_malware_family(signature)
                    tags.extend([f"malware-{family}" for family in families])
                    tags.append('malicious-signature')
                
                confidence = 0.9 if signature else 0.7
                
                result = self.normalize_hash_data(
                    indicator=file_hash.lower(),
                    data={
                        'sample_id': sample_info.get('sample_id'),
                        'signature': signature,
                        'file_type': sample_info.get('file_type'),
                        'file_size': sample_info.get('file_size'),
                        'file_name': sample_info.get('file_name'),
                        'first_seen': sample_info.get('first_seen'),
                        'last_seen': sample_info.get('last_seen'),
                        'imphash': sample_info.get('imphash'),
                        'tlsh': sample_info.get('tlsh'),
                        'associated_urls': sample_info.get('urls', [])[:5],
                        'raw_url': sample_api
                    },
                    tags=tags,
                    confidence=confidence,
                    score=10 if signature else 5
                )
                results.append(result)
                
            else:
                # Hash not found in URLhaus
                result = self.normalize_hash_data(
                    indicator=file_hash.lower(),
                    data={
                        'query_status': 'not_found',
                        'status': 'clean',
                        'raw_url': sample_api
                    },
                    tags=['urlhaus-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up hash {file_hash} in URLhaus: {str(e)}")
        
        return results
    
    async def get_recent_malware(self, limit: int = 100) -> List[ThreatIntelligenceData]:
        """Get recent malware submissions"""
        results = []
        
        try:
            url = f"{self.base_url}/recent/"
            params = {}
            
            if limit:
                params['limit'] = str(limit)
            
            data = await self._make_request(url, params=params)
            
            if data and data.get('query_status') == 'ok' and 'urls' in data:
                for entry in data['urls'][:limit]:
                    url_entry = entry.get('url', '')
                    
                    tags = ['recent-malware', 'urlhaus-recent']
                    threat_level = entry.get('threat_level', 'unknown')
                    
                    if threat_level:
                        tags.append(f"threat-level-{threat_level}")
                    
                    signature = entry.get('signature', '')
                    if signature:
                        families = self._classify_malware_family(signature)
                        tags.extend([f"malware-{family}" for family in families])
                    
                    confidence = 0.8 if threat_level == 'online' else 0.6
                    
                    result = self.normalize_url_data(
                        indicator=url_entry,
                        data={
                            'recent_entry': entry,
                            'date_added': entry.get('date_added'),
                            'threat_level': threat_level,
                            'threat_types': entry.get('threat_types', []),
                            'malware_family': signature,
                            'signature': signature,
                            'host': entry.get('host'),
                            'country': entry.get('country'),
                            'tags': entry.get('tags', []),
                            'raw_url': url
                        },
                        tags=tags,
                        confidence=confidence,
                        score=5
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting recent malware: {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of URLhaus collector"""
    # URLhaus doesn't require API key for public API
    async with URLhausCollector() as collector:
        # Test URL lookup
        print("Testing URL lookup...")
        url_results = await collector.lookup_url("http://malware-example.com/payload.exe")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator[:50]}... (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test domain lookup
        print("\nTesting domain lookup...")
        domain_results = await collector.lookup_domain("malware-example.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test hash lookup
        print("\nTesting hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test recent malware
        print("\nTesting recent malware...")
        recent_results = await collector.get_recent_malware(limit=5)
        print(f"Recent results: {len(recent_results)} found")
        for result in recent_results:
            print(f"  - {result.indicator[:50]}... (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())