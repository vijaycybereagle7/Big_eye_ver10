#!/usr/bin/env python3
"""
Google Safe Browsing API v4 Collector
Provides threat intelligence from Google Safe Browsing
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urlparse, quote
import hashlib
import json

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class GoogleSafeBrowsingCollector(BaseThreatCollector):
    """Google Safe Browsing API v4 collector"""
    
    def __init__(self, api_key: str):
        super().__init__("GoogleSafeBrowsing", rate_limit=600, time_window=600)  # 600 requests per 10 minutes
        self.set_api_key(api_key, "key")
        self.base_url = "https://safebrowsing.googleapis.com/v4"
        self.threat_types = [
            "MALWARE",
            "SOCIAL_ENGINEERING",
            "UNWANTED_SOFTWARE",
            "POTENTIALLY_HARMFUL_APPLICATION"
        ]
        self.platform_types = [
            "ANY_PLATFORM",
            "WINDOWS",
            "MACOS",
            "LINUX",
            "ANDROID",
            "IOS",
            "CHROMEOS"
        ]
        self.threat_matches = {}
    
    def _canonicalize_url(self, url: str) -> str:
        """Canonicalize URL according to Google Safe Browsing standards"""
        try:
            parsed = urlparse(url if url.startswith(('http://', 'https://')) else f'http://{url}')
            
            # Add scheme if missing
            if not parsed.scheme:
                url = f'http://{url}'
                parsed = urlparse(url)
            
            # Remove fragments
            canonical = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Add query if present
            if parsed.query:
                canonical += f"?{parsed.query}"
            
            return canonical
        except:
            return url
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url
    
    async def _initialize_threat_matches(self):
        """Initialize threat match lookup table"""
        try:
            # Build lookup table from threat match info
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Google doesn't provide direct threat match lookup, so we'll cache results
            logger.info("Threat match lookup initialized")
            
        except Exception as e:
            logger.error(f"Error initializing threat matches: {str(e)}")
    
    def _classify_threat_type(self, threat_type: str) -> List[str]:
        """Classify Google Safe Browsing threat types"""
        threat_mapping = {
            "MALWARE": ["malware", "virus", "trojan"],
            "SOCIAL_ENGINEERING": ["phishing", "social-engineering", "fraud"],
            "UNWANTED_SOFTWARE": ["unwanted-software", "adware", "spyware"],
            "POTENTIALLY_HARMFUL_APPLICATION": ["potentially-harmful", "suspicious"]
        }
        
        return threat_mapping.get(threat_type, [threat_type.lower()])
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        try:
            # Convert IP to URL format
            url = f"http://{ip}/"
            return await self.lookup_url(url)
            
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in Google Safe Browsing: {str(e)}")
        
        return results
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Convert domain to URL format
            url = f"http://{domain}/"
            return await self.lookup_url(url)
            
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in Google Safe Browsing: {str(e)}")
        
        return results
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # Canonicalize the URL
            canonical_url = self._canonicalize_url(url)
            
            # Prepare threat search request
            threat_findings = []
            
            for platform_type in self.platform_types:
                request_body = {
                    "client": {
                        "clientId": "threat-intelligence-collector",
                        "clientVersion": "1.0"
                    },
                    "threatInfo": {
                        "threatTypes": self.threat_types,
                        "platformTypes": [platform_type],
                        "threatEntryTypes": ["URL"],
                        "threatEntries": [{"url": canonical_url}]
                    }
                }
                
                url_search = f"{self.base_url}/threatMatches:find"
                data = await self._make_request(url_search, method="POST", json_data=request_body)
                
                if data and 'matches' in data:
                    for match in data['matches']:
                        threat_finding = {
                            'platform_type': platform_type,
                            'threat_type': match.get('threatType'),
                            'cache_duration': match.get('cacheDuration'),
                            'threat_entry_metadata': match.get('threatEntryMetadata'),
                            'canonical_url': canonical_url
                        }
                        threat_findings.append(threat_finding)
            
            if threat_findings:
                # Calculate confidence based on number and severity of threats
                confidence = min(1.0, len(threat_findings) * 0.2)
                tags = []
                score = 0.0
                
                for finding in threat_findings:
                    threat_type = finding['threat_type']
                    tags.extend(self._classify_threat_type(threat_type))
                    
                    # Assign scores based on threat type
                    threat_scores = {
                        "MALWARE": 0.9,
                        "SOCIAL_ENGINEERING": 0.8,
                        "UNWANTED_SOFTWARE": 0.6,
                        "POTENTIALLY_HARMFUL_APPLICATION": 0.7
                    }
                    score = max(score, threat_scores.get(threat_type, 0.5))
                
                # Remove duplicates
                tags = list(set(tags))
                
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data={
                        'threat_findings': threat_findings,
                        'canonical_url': canonical_url,
                        'original_url': url,
                        'num_threats': len(threat_findings),
                        'platforms_affected': list(set(f['platform_type'] for f in threat_findings)),
                        'threat_types': list(set(f['threat_type'] for f in threat_findings)),
                        'raw_url': f"{self.base_url}/threatMatches:find"
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
            else:
                # No threats found
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data={
                        'threat_findings': [],
                        'canonical_url': canonical_url,
                        'original_url': url,
                        'status': 'clean',
                        'num_threats': 0,
                        'raw_url': f"{self.base_url}/threatMatches:find"
                    },
                    tags=['clean'],
                    confidence=0.0,
                    score=0.0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in Google Safe Browsing: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash information"""
        results = []
        
        try:
            # Normalize hash
            hash_value = file_hash.lower().strip()
            
            # Validate hash format
            if len(hash_value) not in [32, 40, 64, 128]:
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
            
            # Prepare threat search for hash
            threat_findings = []
            
            for platform_type in self.platform_types:
                request_body = {
                    "client": {
                        "clientId": "threat-intelligence-collector",
                        "clientVersion": "1.0"
                    },
                    "threatInfo": {
                        "threatTypes": self.threat_types,
                        "platformTypes": [platform_type],
                        "threatEntryTypes": ["EXECUTABLE"],
                        "threatEntries": [{"hash": hash_value}]
                    }
                }
                
                hash_search = f"{self.base_url}/threatMatches:find"
                data = await self._make_request(hash_search, method="POST", json_data=request_body)
                
                if data and 'matches' in data:
                    for match in data['matches']:
                        threat_finding = {
                            'platform_type': platform_type,
                            'threat_type': match.get('threatType'),
                            'cache_duration': match.get('cacheDuration'),
                            'threat_entry_metadata': match.get('threatEntryMetadata'),
                            'hash': hash_value
                        }
                        threat_findings.append(threat_finding)
            
            if threat_findings:
                # Calculate confidence based on number and severity of threats
                confidence = min(1.0, len(threat_findings) * 0.2)
                tags = []
                score = 0.0
                
                for finding in threat_findings:
                    threat_type = finding['threat_type']
                    tags.extend(self._classify_threat_type(threat_type))
                    
                    # Assign scores based on threat type
                    threat_scores = {
                        "MALWARE": 0.9,
                        "SOCIAL_ENGINEERING": 0.8,
                        "UNWANTED_SOFTWARE": 0.6,
                        "POTENTIALLY_HARMFUL_APPLICATION": 0.7
                    }
                    score = max(score, threat_scores.get(threat_type, 0.5))
                
                # Remove duplicates
                tags = list(set(tags))
                
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'threat_findings': threat_findings,
                        'hash': hash_value,
                        'hash_length': len(hash_value),
                        'num_threats': len(threat_findings),
                        'platforms_affected': list(set(f['platform_type'] for f in threat_findings)),
                        'threat_types': list(set(f['threat_type'] for f in threat_findings)),
                        'raw_url': hash_search
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
            else:
                # No threats found
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'threat_findings': [],
                        'hash': hash_value,
                        'hash_length': len(hash_value),
                        'status': 'clean',
                        'num_threats': 0,
                        'raw_url': hash_search
                    },
                    tags=['clean'],
                    confidence=0.0,
                    score=0.0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up hash {hash_value} in Google Safe Browsing: {str(e)}")
        
        return results
    
    async def bulk_lookup(self, urls: List[str]) -> List[ThreatIntelligenceData]:
        """Bulk lookup multiple URLs"""
        results = []
        
        # Process URLs in batches of 500 (Google Safe Browsing limit)
        batch_size = 500
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            
            try:
                request_body = {
                    "client": {
                        "clientId": "threat-intelligence-collector",
                        "clientVersion": "1.0"
                    },
                    "threatInfo": {
                        "threatTypes": self.threat_types,
                        "platformTypes": self.platform_types,
                        "threatEntryTypes": ["URL"],
                        "threatEntries": [{"url": url} for url in batch]
                    }
                }
                
                url_search = f"{self.base_url}/threatMatches:find"
                data = await self._make_request(url_search, method="POST", json_data=request_body)
                
                if data and 'matches' in data:
                    # Group matches by URL
                    url_matches = {}
                    for match in data['matches']:
                        url = match.get('threatEntry', {}).get('url')
                        if url not in url_matches:
                            url_matches[url] = []
                        url_matches[url].append(match)
                    
                    # Create results for each URL
                    for url in batch:
                        matches = url_matches.get(url, [])
                        
                        if matches:
                            confidence = min(1.0, len(matches) * 0.2)
                            tags = []
                            score = 0.0
                            
                            for match in matches:
                                threat_type = match.get('threatType')
                                tags.extend(self._classify_threat_type(threat_type))
                                
                                threat_scores = {
                                    "MALWARE": 0.9,
                                    "SOCIAL_ENGINEERING": 0.8,
                                    "UNWANTED_SOFTWARE": 0.6,
                                    "POTENTIALLY_HARMFUL_APPLICATION": 0.7
                                }
                                score = max(score, threat_scores.get(threat_type, 0.5))
                            
                            tags = list(set(tags))
                            
                            result = self.normalize_url_data(
                                indicator=url,
                                data={
                                    'threat_findings': matches,
                                    'bulk_lookup': True,
                                    'num_threats': len(matches),
                                    'raw_url': url_search
                                },
                                tags=tags,
                                confidence=confidence,
                                score=score
                            )
                            results.append(result)
                        else:
                            # No threats found
                            result = self.normalize_url_data(
                                indicator=url,
                                data={
                                    'threat_findings': [],
                                    'bulk_lookup': True,
                                    'status': 'clean',
                                    'num_threats': 0,
                                    'raw_url': url_search
                                },
                                tags=['clean'],
                                confidence=0.0,
                                score=0.0
                            )
                            results.append(result)
                
                # Add delay between batches
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in bulk lookup batch {i//batch_size + 1}: {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of Google Safe Browsing collector"""
    # Set your Google Safe Browsing API key here
    api_key = "YOUR_GOOGLE_SAFE_BROWSING_API_KEY"
    
    async with GoogleSafeBrowsingCollector(api_key) as collector:
        # Test URL lookup
        print("Testing URL lookup...")
        url_results = await collector.lookup_url("http://malware-example.com")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator} (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test domain lookup
        print("\nTesting domain lookup...")
        domain_results = await collector.lookup_domain("google.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test hash lookup
        print("\nTesting hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test bulk lookup
        print("\nTesting bulk lookup...")
        urls = ["http://example.com", "http://test.com", "http://clean.com"]
        bulk_results = await collector.bulk_lookup(urls)
        print(f"Bulk results: {len(bulk_results)} found")
        for result in bulk_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())