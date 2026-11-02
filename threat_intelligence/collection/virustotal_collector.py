#!/usr/bin/env python3
"""
VirusTotal API v3 Collector
Provides threat intelligence from VirusTotal
"""

import asyncio
import aiohttp
import logging
import hashlib
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import json

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class VirusTotalCollector(BaseThreatCollector):
    """VirusTotal API v3 collector"""
    
    def __init__(self, api_key: str):
        super().__init__("VirusTotal", rate_limit=60, time_window=60)
        self.set_api_key(api_key, "x-apikey")
        self.base_url = "https://www.virustotal.com/api/v3"
    
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
    
    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return None
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        try:
            # Get IP analysis
            url = f"{self.base_url}/ip_addresses/{ip}"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                ip_data = data['data']
                attributes = ip_data.get('attributes', {})
                
                # Extract threat information
                tags = attributes.get('tags', [])
                reputation = attributes.get('reputation', 0)
                
                # Get last analysis stats
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                malicious = last_analysis_stats.get('malicious', 0)
                suspicious = last_analysis_stats.get('suspicious', 0)
                harmless = last_analysis_stats.get('harmless', 0)
                
                # Calculate confidence score
                total = malicious + suspicious + harmless
                if total > 0:
                    confidence = (malicious + suspicious) / total
                else:
                    confidence = 0.5
                
                # Create result
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'reputation': reputation,
                        'last_analysis_stats': last_analysis_stats,
                        'country': attributes.get('country'),
                        'owner': attributes.get('owner'),
                        'as_owner': attributes.get('as_owner'),
                        'asn': attributes.get('asn'),
                        'tags': tags,
                        'votes': attributes.get('votes'),
                        'whois': attributes.get('whois'),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=reputation
                )
                results.append(result)
                
                # Get related URLs
                await self._get_ip_related_urls(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in VirusTotal: {str(e)}")
        
        return results
    
    async def _get_ip_related_urls(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get URLs related to an IP"""
        try:
            url = f"{self.base_url}/ip_addresses/{ip}/relationships"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                for relationship in data['data']:
                    if relationship.get('type') == 'related_samples':
                        sample_data = {
                            'relationship_type': 'related_samples',
                            'sample_info': relationship.get('attributes', {}),
                            'raw_url': relationship.get('links', {}).get('related')
                        }
                        
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data=sample_data,
                            tags=['related-samples'],
                            confidence=0.7
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error getting related URLs for IP {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Get domain analysis
            url = f"{self.base_url}/domains/{domain}"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                domain_data = data['data']
                attributes = domain_data.get('attributes', {})
                
                tags = attributes.get('tags', [])
                reputation = attributes.get('reputation', 0)
                
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                malicious = last_analysis_stats.get('malicious', 0)
                suspicious = last_analysis_stats.get('suspicious', 0)
                
                total = malicious + suspicious
                confidence = min(1.0, total * 0.1) if total > 0 else 0.0
                
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'reputation': reputation,
                        'last_analysis_stats': last_analysis_stats,
                        'creation_date': attributes.get('creation_date'),
                        'whois': attributes.get('whois'),
                        'tags': tags,
                        'votes': attributes.get('votes'),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=reputation
                )
                results.append(result)
                
                # Get resolutions (IP addresses)
                await self._get_domain_resolutions(domain, results)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in VirusTotal: {str(e)}")
        
        return results
    
    async def _get_domain_resolutions(self, domain: str, results: List[ThreatIntelligenceData]):
        """Get IP resolutions for domain"""
        try:
            url = f"{self.base_url}/domains/{domain}/relationships"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                for relationship in data['data']:
                    if relationship.get('type') == 'resolutions':
                        res_data = {
                            'relationship_type': 'resolutions',
                            'resolution_info': relationship.get('attributes', {}),
                            'raw_url': relationship.get('links', {}).get('related')
                        }
                        
                        result = self.normalize_domain_data(
                            indicator=domain,
                            data=res_data,
                            tags=['resolution'],
                            confidence=0.6
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error getting resolutions for domain {domain}: {str(e)}")
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # URL encode the URL
            import urllib.parse
            encoded_url = urllib.parse.quote(url, safe='')
            
            url_api = f"{self.base_url}/urls/{encoded_url}"
            data = await self._make_request(url_api)
            
            if data and 'data' in data:
                url_data = data['data']
                attributes = url_data.get('attributes', {})
                
                tags = attributes.get('tags', [])
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                
                malicious = last_analysis_stats.get('malicious', 0)
                suspicious = last_analysis_stats.get('suspicious', 0)
                
                total = malicious + suspicious
                confidence = min(1.0, total * 0.1) if total > 0 else 0.0
                
                result = self.normalize_url_data(
                    indicator=url,
                    data={
                        'last_analysis_stats': last_analysis_stats,
                        'last_modification_date': attributes.get('last_modification_date'),
                        'tags': tags,
                        'title': attributes.get('title'),
                        'html_url': attributes.get('html_url'),
                        'raw_url': url_api
                    },
                    tags=tags,
                    confidence=confidence
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in VirusTotal: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash information"""
        results = []
        
        try:
            # Normalize hash
            hash_value = self._normalize_hash(file_hash)
            
            if not self._is_valid_hash(hash_value):
                logger.warning(f"Invalid hash format: {hash_value}")
                return results
            
            url = f"{self.base_url}/files/{hash_value}"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                file_data = data['data']
                attributes = file_data.get('attributes', {})
                
                # Extract file information
                names = attributes.get('names', [])
                tags = attributes.get('tags', [])
                reputation = attributes.get('reputation', 0)
                
                last_analysis_stats = attributes.get('last_analysis_stats', {})
                malicious = last_analysis_stats.get('malicious', 0)
                suspicious = last_analysis_stats.get('suspicious', 0)
                
                # Calculate confidence
                total = malicious + suspicious
                confidence = min(1.0, total * 0.1) if total > 0 else 0.0
                
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'names': names,
                        'reputation': reputation,
                        'last_analysis_stats': last_analysis_stats,
                        'size': attributes.get('size'),
                        'type_description': attributes.get('type_description'),
                        'md5': attributes.get('md5'),
                        'sha1': attributes.get('sha1'),
                        'sha256': attributes.get('sha256'),
                        'times_submitted': attributes.get('times_submitted'),
                        'tags': tags,
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=reputation
                )
                results.append(result)
                
                # Get related samples
                await self._get_hash_related_samples(hash_value, results)
                
        except Exception as e:
            logger.error(f"Error looking up hash {file_hash} in VirusTotal: {str(e)}")
        
        return results
    
    async def _get_hash_related_samples(self, hash_value: str, results: List[ThreatIntelligenceData]):
        """Get related samples for a hash"""
        try:
            url = f"{self.base_url}/files/{hash_value}/relationships"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                for relationship in data['data']:
                    if relationship.get('type') in ['similar_samples', 'related_samples']:
                        sample_data = {
                            'relationship_type': relationship.get('type'),
                            'sample_info': relationship.get('attributes', {}),
                            'raw_url': relationship.get('links', {}).get('related')
                        }
                        
                        result = self.normalize_hash_data(
                            indicator=hash_value,
                            data=sample_data,
                            tags=['related-samples'],
                            confidence=0.7
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error getting related samples for hash {hash_value}: {str(e)}")


# Example usage and testing
async def main():
    """Example usage of VirusTotal collector"""
    # Set your VirusTotal API key here
    api_key = "YOUR_VIRUSTOTAL_API_KEY"
    
    async with VirusTotalCollector(api_key) as collector:
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
        
        # Test hash lookup
        print("\nTesting hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())