#!/usr/bin/env python3
"""
ThreatFox API Collector
Provides threat intelligence from ThreatFox (Indicator of Compromise database)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote
import hashlib
import re

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class ThreatFoxCollector(BaseThreatCollector):
    """ThreatFox collector"""
    
    def __init__(self, api_key: str = None):  # ThreatFox public API doesn't require key
        super().__init__("ThreatFox", rate_limit=1000, time_window=3600)  # 1000 requests per hour
        self.base_url = "https://threatfox-api.abuse.ch/api/v1"
    
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
    
    def _normalize_hash(self, hash_value: str) -> str:
        """Normalize hash format"""
        return hash_value.lower().strip()
    
    def _is_valid_hash(self, hash_value: str) -> bool:
        """Check if hash value is valid"""
        hash_value = self._normalize_hash(hash_value)
        patterns = {
            'md5': re.compile(r'^[a-fA-F0-9]{32}$'),
            'sha1': re.compile(r'^[a-fA-F0-9]{40}$'),
            'sha256': re.compile(r'^[a-fA-F0-9]{64}$'),
            'sha512': re.compile(r'^[a-fA-F0-9]{128}$')
        }
        
        for hash_type, pattern in patterns.items():
            if pattern.match(hash_value):
                return True
        return False
    
    def _classify_malware_family(self, ioc_type: str, value: str) -> List[str]:
        """Classify malware based on IOC type and value"""
        value_lower = value.lower()
        tags = ['threatfox-ioc']
        
        # Add IOC type tags
        tags.append(f"ioc-type-{ioc_type}")
        
        # Classify based on IOCs
        malware_indicators = {
            'domain': [
                'emotet', 'trickbot', 'cobalt', 'quasar', 'netwalker',
                'phishing', 'malware', 'trojan', 'botnet', 'c2'
            ],
            'url': [
                'phishing', 'malware-download', 'payload', 'exploit',
                'drive-by', 'c2-server', 'command-control'
            ],
            'ip': [
                'c2', 'command-control', 'malware-server', 'phishing-server',
                'botnet-ip', 'exfiltration'
            ],
            'file': [
                'emotet', 'trickbot', 'ransomware', 'loader', 'stealer',
                'backdoor', 'trojan', 'virus', 'worm'
            ]
        }
        
        for category, indicators in malware_indicators.items():
            if any(indicator in value_lower for indicator in indicators):
                tags.append(f"malware-{category}")
        
        return tags
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            request_data = {
                'query': 'search_ioc',
                'ioc': url,
                'limit': 100
            }
            
            data = await self._make_request(self.base_url, method="POST", json_data=request_data)
            
            if data and data.get('query_status') == 'ok' and 'data' in data:
                for ioc in data['data']:
                    if ioc.get('ioc') == url:
                        # Extract threat intelligence
                        confidence = float(ioc.get('confidence', '0'))
                        confidence = min(1.0, confidence / 100.0)  # Convert percentage to 0-1
                        
                        tags = self._classify_malware_family('url', ioc.get('ioc', ''))
                        tags.extend(ioc.get('tags', []))
                        
                        result = self.normalize_url_data(
                            indicator=url,
                            data={
                                'ioc': ioc.get('ioc'),
                                'ioc_type': ioc.get('ioc_type'),
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                
                if not results:
                    # URL not found as specific IOC
                    result = self.normalize_url_data(
                        indicator=url,
                        data={
                            'query_status': 'not_found',
                            'status': 'clean',
                            'raw_url': self.base_url
                        },
                        tags=['threatfox-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
            else:
                result = self.normalize_url_data(
                    indicator=url,
                    data={
                        'query_status': 'error',
                        'error': data.get('error_message', 'Unknown error') if data else 'No response',
                        'raw_url': self.base_url
                    },
                    tags=['error'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in ThreatFox: {str(e)}")
        
        return results
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            request_data = {
                'query': 'search_ioc',
                'ioc': domain,
                'limit': 100
            }
            
            data = await self._make_request(self.base_url, method="POST", json_data=request_data)
            
            if data and data.get('query_status') == 'ok' and 'data' in data:
                for ioc in data['data']:
                    if ioc.get('ioc') == domain:
                        # Extract threat intelligence
                        confidence = float(ioc.get('confidence', '0'))
                        confidence = min(1.0, confidence / 100.0)
                        
                        tags = self._classify_malware_family('domain', ioc.get('ioc', ''))
                        tags.extend(ioc.get('tags', []))
                        
                        result = self.normalize_domain_data(
                            indicator=domain,
                            data={
                                'ioc': ioc.get('ioc'),
                                'ioc_type': ioc.get('ioc_type'),
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                
                if not results:
                    # Domain not found as specific IOC
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'query_status': 'not_found',
                            'status': 'clean',
                            'raw_url': self.base_url
                        },
                        tags=['threatfox-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
            else:
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'query_status': 'error',
                        'error': data.get('error_message', 'Unknown error') if data else 'No response',
                        'raw_url': self.base_url
                    },
                    tags=['error'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in ThreatFox: {str(e)}")
        
        return results
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            request_data = {
                'query': 'search_ioc',
                'ioc': ip,
                'limit': 100
            }
            
            data = await self._make_request(self.base_url, method="POST", json_data=request_data)
            
            if data and data.get('query_status') == 'ok' and 'data' in data:
                for ioc in data['data']:
                    if ioc.get('ioc') == ip:
                        # Extract threat intelligence
                        confidence = float(ioc.get('confidence', '0'))
                        confidence = min(1.0, confidence / 100.0)
                        
                        tags = self._classify_malware_family('ip', ioc.get('ioc', ''))
                        tags.extend(ioc.get('tags', []))
                        
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data={
                                'ioc': ioc.get('ioc'),
                                'ioc_type': ioc.get('ioc_type'),
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                
                if not results:
                    # IP not found as specific IOC
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data={
                            'query_status': 'not_found',
                            'status': 'clean',
                            'raw_url': self.base_url
                        },
                        tags=['threatfox-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
            else:
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'query_status': 'error',
                        'error': data.get('error_message', 'Unknown error') if data else 'No response',
                        'raw_url': self.base_url
                    },
                    tags=['error'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in ThreatFox: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash information"""
        results = []
        
        try:
            # Normalize hash
            hash_value = self._normalize_hash(file_hash)
            
            if not self._is_valid_hash(hash_value):
                logger.warning(f"Invalid hash format: {hash_value}")
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'error': 'Invalid hash format',
                        'supported_formats': ['MD5 (32 chars)', 'SHA1 (40 chars)', 'SHA256 (64 chars)', 'SHA512 (128 chars)'],
                        'raw_url': None
                    },
                    tags=['invalid-hash'],
                    confidence=0.0,
                    score=0.0
                )
                results.append(result)
                return results
            
            request_data = {
                'query': 'search_ioc',
                'ioc': hash_value,
                'limit': 100
            }
            
            data = await self._make_request(self.base_url, method="POST", json_data=request_data)
            
            if data and data.get('query_status') == 'ok' and 'data' in data:
                for ioc in data['data']:
                    if ioc.get('ioc') == hash_value:
                        # Extract threat intelligence
                        confidence = float(ioc.get('confidence', '0'))
                        confidence = min(1.0, confidence / 100.0)
                        
                        tags = self._classify_malware_family('file', ioc.get('ioc', ''))
                        tags.extend(ioc.get('tags', []))
                        
                        result = self.normalize_hash_data(
                            indicator=hash_value,
                            data={
                                'ioc': ioc.get('ioc'),
                                'ioc_type': ioc.get('ioc_type'),
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                
                if not results:
                    # Hash not found as specific IOC
                    result = self.normalize_hash_data(
                        indicator=hash_value,
                        data={
                            'query_status': 'not_found',
                            'status': 'clean',
                            'raw_url': self.base_url
                        },
                        tags=['threatfox-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
            else:
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'query_status': 'error',
                        'error': data.get('error_message', 'Unknown error') if data else 'No response',
                        'raw_url': self.base_url
                    },
                    tags=['error'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up hash {hash_value} in ThreatFox: {str(e)}")
        
        return results
    
    async def get_recent_iocs(self, limit: int = 100, ioc_type: str = None) -> List[ThreatIntelligenceData]:
        """Get recent IOCs"""
        results = []
        
        try:
            request_data = {
                'query': 'search_recent',
                'limit': limit
            }
            
            if ioc_type:
                request_data['ioc_type'] = ioc_type
            
            data = await self._make_request(self.base_url, method="POST", json_data=request_data)
            
            if data and data.get('query_status') == 'ok' and 'data' in data:
                for ioc in data['data']:
                    ioc_value = ioc.get('ioc', '')
                    ioc_type = ioc.get('ioc_type', '')
                    confidence = float(ioc.get('confidence', '0'))
                    confidence = min(1.0, confidence / 100.0)
                    
                    tags = self._classify_malware_family(ioc_type, ioc_value)
                    tags.extend(['threatfox-recent'])
                    tags.extend(ioc.get('tags', []))
                    
                    # Create result based on IOC type
                    if ioc_type == 'url':
                        result = self.normalize_url_data(
                            indicator=ioc_value,
                            data={
                                'ioc': ioc_value,
                                'ioc_type': ioc_type,
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                    elif ioc_type == 'domain':
                        result = self.normalize_domain_data(
                            indicator=ioc_value,
                            data={
                                'ioc': ioc_value,
                                'ioc_type': ioc_type,
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                    elif ioc_type == 'ip':
                        result = self.normalize_ip_data(
                            indicator=ioc_value,
                            data={
                                'ioc': ioc_value,
                                'ioc_type': ioc_type,
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                    elif ioc_type == 'file':
                        result = self.normalize_hash_data(
                            indicator=ioc_value,
                            data={
                                'ioc': ioc_value,
                                'ioc_type': ioc_type,
                                'threat_type': ioc.get('threat_type'),
                                'malware': ioc.get('malware'),
                                'confidence': ioc.get('confidence'),
                                'first_seen': ioc.get('first_seen'),
                                'last_seen': ioc.get('last_seen'),
                                'reporter': ioc.get('reporter'),
                                'source': ioc.get('source'),
                                'tags': ioc.get('tags', []),
                                'references': ioc.get('references', []),
                                'raw_url': self.base_url
                            },
                            tags=tags,
                            confidence=confidence,
                            score=confidence * 100
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error getting recent IOCs: {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of ThreatFox collector"""
    # ThreatFox doesn't require API key for public API
    async with ThreatFoxCollector() as collector:
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
        
        # Test IP lookup
        print("\nTesting IP lookup...")
        ip_results = await collector.lookup_ip("192.0.2.1")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test hash lookup
        print("\nTesting hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())