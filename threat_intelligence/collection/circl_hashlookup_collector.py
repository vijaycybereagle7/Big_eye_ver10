#!/usr/bin/env python3
"""
CIRCL Hashlookup API Collector
Provides threat intelligence from CIRCL hashlookup service
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
import re

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class CIRCLHashlookupCollector(BaseThreatCollector):
    """CIRCL Hashlookup collector"""
    
    def __init__(self, username: str, password: str):
        super().__init__("CIRCLHashlookup", rate_limit=100, time_window=3600)  # 100 requests per hour
        # CIRCL hashlookup uses HTTP Basic Auth
        self.username = username
        self.password = password
        self.base_url = "https://hashlookup.circl.lu"
    
    async def _make_request(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Dict[str, str] = None,
        params: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with CIRCL Basic Auth"""
        await self._rate_limit()
        
        if headers is None:
            headers = {}
        
        # Add Basic Auth headers
        import base64
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded_credentials}'
        
        # Add default headers
        headers.update({
            'User-Agent': 'ThreatIntelligenceCollector/1.0',
            'Accept': 'application/json',
        })
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    connector=aiohttp.TCPConnector(limit=100)
                )
            
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            ) as response:
                content_type = response.headers.get('content-type', '')
                
                if response.status == 200:
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        return {'content': await response.text()}
                elif response.status == 401:
                    logger.error("CIRCL authentication failed. Check username/password.")
                    return None
                elif response.status == 404:
                    # Hash not found
                    return {'status': 'not_found', 'message': 'Hash not found'}
                elif response.status == 429:
                    logger.warning(f"Rate limited by CIRCL. Waiting...")
                    await asyncio.sleep(60)
                    return await self._make_request(url, method, headers, params, json_data, timeout)
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status} for CIRCL: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout for CIRCL request to {url}")
            return None
        except Exception as e:
            logger.error(f"Error making request to CIRCL: {str(e)}")
            return None
    
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
    
    def _get_hash_type(self, hash_value: str) -> Optional[str]:
        """Determine hash type"""
        hash_value = self._normalize_hash(hash_value)
        
        if len(hash_value) == 32:
            return 'md5'
        elif len(hash_value) == 40:
            return 'sha1'
        elif len(hash_value) == 64:
            return 'sha256'
        elif len(hash_value) == 128:
            return 'sha512'
        else:
            return None
    
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
            
            hash_type = self._get_hash_type(hash_value)
            
            # Get hash information
            if hash_type == 'md5':
                url = f"{self.base_url}/lookup/MD5/{hash_value}"
            elif hash_type == 'sha1':
                url = f"{self.base_url}/lookup/SHA1/{hash_value}"
            elif hash_type == 'sha256':
                url = f"{self.base_url}/lookup/SHA256/{hash_value}"
            elif hash_type == 'sha512':
                url = f"{self.base_url}/lookup/SHA512/{hash_value}"
            else:
                url = f"{self.base_url}/lookup/{hash_value}"
            
            data = await self._make_request(url)
            
            if data and data.get('status') != 'not_found':
                # Hash found
                tags = ['circl-hashlookup']
                
                # Determine confidence based on available information
                confidence = 0.5  # Default confidence
                score = 0
                
                # Check for malware information
                if 'virustotal' in data:
                    tags.append('virustotal-linked')
                    vt_data = data.get('virustotal', {})
                    if vt_data.get('positives', 0) > 0:
                        tags.append('malicious-vt')
                        confidence = min(1.0, (vt_data.get('positives', 0) / vt_data.get('total', 1)) * 0.8 + 0.2)
                        score = vt_data.get('positives', 0) * 10
                
                # Check for other sources
                sources = [key for key in data.keys() if key not in ['status', 'hash', 'hash_type']]
                if sources:
                    tags.append(f"multiple-sources-{len(sources)}")
                    confidence = min(1.0, confidence + len(sources) * 0.1)
                    score += len(sources) * 5
                
                # Add hash type specific tags
                if hash_type:
                    tags.append(f'hash-type-{hash_type}')
                
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'hash': data.get('hash'),
                        'hash_type': data.get('hash_type', hash_type),
                        'virustotal': data.get('virustotal', {}),
                        'sources': {key: value for key, value in data.items() if key not in ['status', 'hash', 'hash_type']},
                        'lookup_url': url,
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
                
            else:
                # Hash not found
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'status': 'not_found',
                        'hash_type': hash_type,
                        'lookup_url': url,
                        'raw_url': url
                    },
                    tags=['circl-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up hash {hash_value} in CIRCL: {str(e)}")
        
        return results
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address - CIRCL doesn't support IP lookups"""
        results = []
        
        result = self.normalize_ip_data(
            indicator=ip,
            data={
                'note': 'CIRCL hashlookup does not support IP address lookups',
                'supported_indicators': ['MD5', 'SHA1', 'SHA256', 'SHA512 hashes'],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain - CIRCL doesn't support domain lookups"""
        results = []
        
        result = self.normalize_domain_data(
            indicator=domain,
            data={
                'note': 'CIRCL hashlookup does not support domain lookups',
                'supported_indicators': ['MD5', 'SHA1', 'SHA256', 'SHA512 hashes'],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL - CIRCL doesn't support URL lookups"""
        results = []
        
        result = self.normalize_url_data(
            indicator=url,
            data={
                'note': 'CIRCL hashlookup does not support URL lookups',
                'supported_indicators': ['MD5', 'SHA1', 'SHA256', 'SHA512 hashes'],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def bulk_lookup(self, hashes: List[str]) -> List[ThreatIntelligenceData]:
        """Bulk lookup multiple hashes"""
        results = []
        
        # CIRCL hashlookup doesn't have a bulk API, so we need to loop
        for hash_value in hashes:
            try:
                hash_results = await self.lookup_hash(hash_value)
                results.extend(hash_results)
                
                # Add small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in bulk lookup for hash {hash_value}: {str(e)}")
        
        return results
    
    async def reverse_lookup(self, search_term: str) -> List[ThreatIntelligenceData]:
        """Reverse lookup - search for hashes by filename or other criteria"""
        results = []
        
        try:
            # CIRCL hashlookup doesn't have a reverse lookup API
            # This is just an informational result
            result = self.normalize_hash_data(
                indicator=search_term,
                data={
                    'note': 'CIRCL hashlookup does not support reverse lookups',
                    'suggestion': 'Use individual hash lookups',
                    'supported_operations': ['Direct hash lookup', 'Bulk lookup'],
                    'hash_formats': ['MD5', 'SHA1', 'SHA256', 'SHA512'],
                    'raw_url': None
                },
                tags=['reverse-lookup-not-supported'],
                confidence=0.0,
                score=0.0
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error in reverse lookup for '{search_term}': {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of CIRCL Hashlookup collector"""
    # Set your CIRCL credentials here
    username = "YOUR_CIRCL_USERNAME"
    password = "YOUR_CIRCL_PASSWORD"
    
    async with CIRCLHashlookupCollector(username, password) as collector:
        # Test hash lookup
        print("Testing hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test bulk lookup
        print("\nTesting bulk lookup...")
        hashes = [
            "d41d8cd98f00b204e9800998ecf8427e",  # MD5
            "da39a3ee5e6b4b0d3255bfef95601890afd80709",  # SHA1
        ]
        bulk_results = await collector.bulk_lookup(hashes)
        print(f"Bulk results: {len(bulk_results)} found")
        for result in bulk_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test unsupported indicator types
        print("\nTesting unsupported indicator types...")
        ip_results = await collector.lookup_ip("8.8.8.8")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())