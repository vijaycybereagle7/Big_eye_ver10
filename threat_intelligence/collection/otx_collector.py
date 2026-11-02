#!/usr/bin/env python3
"""
AlienVault OTX API Collector
Provides threat intelligence from AlienVault Open Threat Exchange
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote
import re

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class AlienVaultOTXCollector(BaseThreatCollector):
    """AlienVault OTX collector"""
    
    def __init__(self, api_key: str):
        super().__init__("AlienVaultOTX", rate_limit=10000, time_window=86400)  # 10000 requests per day
        self.set_api_key(api_key, "X-OTX-API-KEY")
        self.base_url = "https://otx.alienvault.com/api/v1"
    
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
    
    def _extract_indicator_tags(self, pulse_info: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from pulse information"""
        tags = []
        
        # Extract TLP (Traffic Light Protocol)
        tlp = pulse_info.get('TLP', '').lower()
        if tlp:
            tags.append(f"tlp-{tlp}")
        
        # Extract threat categories
        threat_categories = pulse_info.get('threat_hunter_scoring', {}).get('threat_categories', [])
        tags.extend([f"threat-{cat.lower().replace(' ', '-')}" for cat in threat_categories])
        
        # Extract malware families
        malware_families = pulse_info.get('malware_families', [])
        tags.extend([f"malware-{family.lower()}" for family in malware_families])
        
        # Extract attack techniques
        attack_techniques = pulse_info.get('attack_ids', [])
        tags.extend([f"attack-{tech.get('technique', '').lower().replace(' ', '-')}" for tech in attack_techniques])
        
        return tags
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Get IP intelligence
            url = f"{self.base_url}/indicators/IPv4/{ip}/general"
            data = await self._make_request(url)
            
            if data and 'pulse_info' in data:
                pulse_info = data['pulse_info']
                count = pulse_info.get('count', 0)
                
                tags = []
                confidence = 0.0
                
                if count > 0:
                    # Extract basic pulse info
                    tags = self._extract_indicator_tags(pulse_info)
                    tags.append('ip-intelligence')
                    confidence = min(1.0, count * 0.1)  # Scale confidence based on count
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'pulse_count': count,
                        'raw_data': data,
                        'sections': data.get('sections', []),
                        'tools': data.get('tools', []),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=count
                )
                results.append(result)
                
                # Get related pulses
                await self._get_ip_pulses(ip, results)
                
                # Get passivedns information
                await self._get_ip_passivedns(ip, results)
                
                # Get malware information
                await self._get_ip_malware(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in AlienVault OTX: {str(e)}")
        
        return results
    
    async def _get_ip_pulses(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get pulses related to IP"""
        try:
            url = f"{self.base_url}/indicators/IPv4/{ip}/pulses"
            data = await self._make_request(url)
            
            if data and 'results' in data:
                for pulse in data['results'][:5]:  # Limit to first 5 pulses
                    pulse_data = {
                        'pulse_info': {
                            'id': pulse.get('id'),
                            'name': pulse.get('name'),
                            'description': pulse.get('description'),
                            'author_name': pulse.get('author_name'),
                            'created': pulse.get('created'),
                            'modified': pulse.get('modified'),
                            'tags': pulse.get('tags', []),
                            'TLP': pulse.get('TLP'),
                            'threat_hunter_scoring': pulse.get('threat_hunter_scoring', {}),
                            'adversary': pulse.get('adversary'),
                            'malware_families': pulse.get('malware_families', []),
                            'attack_ids': pulse.get('attack_ids', []),
                            'industries': pulse.get('industries', []),
                            'target_countries': pulse.get('target_countries', []),
                            'indicators_count': pulse.get('indicators_count')
                        },
                        'raw_url': url
                    }
                    
                    tags = self._extract_indicator_tags(pulse_data['pulse_info'])
                    tags.append('pulse')
                    
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data=pulse_data,
                        tags=tags,
                        confidence=0.7,
                        score=pulse.get('indicators_count', 0)
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting pulses for IP {ip}: {str(e)}")
    
    async def _get_ip_passivedns(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get passive DNS information for IP"""
        try:
            url = f"{self.base_url}/indicators/IPv4/{ip}/passive_dns"
            data = await self._make_request(url)
            
            if data and 'passive_dns' in data:
                for dns_entry in data['passive_dns'][:10]:  # Limit to first 10 entries
                    dns_data = {
                        'passive_dns_entry': {
                            'hostname': dns_entry.get('hostname'),
                            'first_seen': dns_entry.get('first_seen'),
                            'last_seen': dns_entry.get('last_seen')
                        },
                        'raw_url': url
                    }
                    
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data=dns_data,
                        tags=['passive-dns'],
                        confidence=0.6,
                        score=1.0
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting passive DNS for IP {ip}: {str(e)}")
    
    async def _get_ip_malware(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get malware information related to IP"""
        try:
            url = f"{self.base_url}/indicators/IPv4/{ip}/malware"
            data = await self._make_request(url)
            
            if data and 'malware' in data:
                for malware in data['malware'][:10]:  # Limit to first 10 entries
                    malware_data = {
                        'malware_info': {
                            'detection': malware.get('detection'),
                            'source': malware.get('source'),
                            'file_type': malware.get('file_type'),
                            'file_size': malware.get('file_size'),
                            'created': malware.get('created'),
                            'file_type_label': malware.get('file_type_label')
                        },
                        'raw_url': url
                    }
                    
                    tags = ['malware', 'ip-related-malware']
                    if malware.get('file_type'):
                        tags.append(f"file-type-{malware['file_type']}")
                    
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data=malware_data,
                        tags=tags,
                        confidence=0.8,
                        score=1.0
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting malware for IP {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Get domain intelligence
            url = f"{self.base_url}/indicators/domain/{quote(domain)}/general"
            data = await self._make_request(url)
            
            if data and 'pulse_info' in data:
                pulse_info = data['pulse_info']
                count = pulse_info.get('count', 0)
                
                tags = []
                confidence = 0.0
                
                if count > 0:
                    tags = self._extract_indicator_tags(pulse_info)
                    tags.append('domain-intelligence')
                    confidence = min(1.0, count * 0.1)
                
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'pulse_count': count,
                        'raw_data': data,
                        'sections': data.get('sections', []),
                        'tools': data.get('tools', []),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=count
                )
                results.append(result)
                
                # Get related pulses
                await self._get_domain_pulses(domain, results)
                
                # Get passivedns information
                await self._get_domain_passivedns(domain, results)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in AlienVault OTX: {str(e)}")
        
        return results
    
    async def _get_domain_pulses(self, domain: str, results: List[ThreatIntelligenceData]):
        """Get pulses related to domain"""
        try:
            url = f"{self.base_url}/indicators/domain/{quote(domain)}/pulses"
            data = await self._make_request(url)
            
            if data and 'results' in data:
                for pulse in data['results'][:5]:
                    pulse_data = {
                        'pulse_info': {
                            'id': pulse.get('id'),
                            'name': pulse.get('name'),
                            'description': pulse.get('description'),
                            'author_name': pulse.get('author_name'),
                            'created': pulse.get('created'),
                            'modified': pulse.get('modified'),
                            'tags': pulse.get('tags', []),
                            'TLP': pulse.get('TLP'),
                            'threat_hunter_scoring': pulse.get('threat_hunter_scoring', {}),
                            'adversary': pulse.get('adversary'),
                            'malware_families': pulse.get('malware_families', []),
                            'attack_ids': pulse.get('attack_ids', [])
                        },
                        'raw_url': url
                    }
                    
                    tags = self._extract_indicator_tags(pulse_data['pulse_info'])
                    tags.append('pulse')
                    
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data=pulse_data,
                        tags=tags,
                        confidence=0.7,
                        score=pulse.get('indicators_count', 0)
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting pulses for domain {domain}: {str(e)}")
    
    async def _get_domain_passivedns(self, domain: str, results: List[ThreatIntelligenceData]):
        """Get passive DNS information for domain"""
        try:
            url = f"{self.base_url}/indicators/domain/{quote(domain)}/passive_dns"
            data = await self._make_request(url)
            
            if data and 'passive_dns' in data:
                for dns_entry in data['passive_dns'][:10]:
                    dns_data = {
                        'passive_dns_entry': {
                            'hostname': dns_entry.get('hostname'),
                            'ip': dns_entry.get('ip'),
                            'first_seen': dns_entry.get('first_seen'),
                            'last_seen': dns_entry.get('last_seen')
                        },
                        'raw_url': url
                    }
                    
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data=dns_data,
                        tags=['passive-dns'],
                        confidence=0.6,
                        score=1.0
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting passive DNS for domain {domain}: {str(e)}")
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # URL encode the URL
            encoded_url = quote(url, safe='')
            url_api = f"{self.base_url}/indicators/url/{encoded_url}/general"
            data = await self._make_request(url_api)
            
            if data and 'pulse_info' in data:
                pulse_info = data['pulse_info']
                count = pulse_info.get('count', 0)
                
                tags = []
                confidence = 0.0
                
                if count > 0:
                    tags = self._extract_indicator_tags(pulse_info)
                    tags.append('url-intelligence')
                    confidence = min(1.0, count * 0.1)
                
                result = self.normalize_url_data(
                    indicator=url,
                    data={
                        'pulse_count': count,
                        'raw_data': data,
                        'sections': data.get('sections', []),
                        'tools': data.get('tools', []),
                        'raw_url': url_api
                    },
                    tags=tags,
                    confidence=confidence,
                    score=count
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in AlienVault OTX: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash information"""
        results = []
        
        try:
            # Normalize hash
            hash_value = self._normalize_hash(file_hash)
            
            # Get hash intelligence
            url = f"{self.base_url}/indicators/file/{hash_value}/general"
            data = await self._make_request(url)
            
            if data and 'pulse_info' in data:
                pulse_info = data['pulse_info']
                count = pulse_info.get('count', 0)
                
                tags = []
                confidence = 0.0
                
                if count > 0:
                    tags = self._extract_indicator_tags(pulse_info)
                    tags.append('hash-intelligence')
                    confidence = min(1.0, count * 0.1)
                
                result = self.normalize_hash_data(
                    indicator=hash_value,
                    data={
                        'pulse_count': count,
                        'raw_data': data,
                        'sections': data.get('sections', []),
                        'tools': data.get('tools', []),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=count
                )
                results.append(result)
                
                # Get hash-related pulses
                await self._get_hash_pulses(hash_value, results)
                
        except Exception as e:
            logger.error(f"Error looking up hash {hash_value} in AlienVault OTX: {str(e)}")
        
        return results
    
    async def _get_hash_pulses(self, hash_value: str, results: List[ThreatIntelligenceData]):
        """Get pulses related to hash"""
        try:
            url = f"{self.base_url}/indicators/file/{hash_value}/pulses"
            data = await self._make_request(url)
            
            if data and 'results' in data:
                for pulse in data['results'][:5]:
                    pulse_data = {
                        'pulse_info': {
                            'id': pulse.get('id'),
                            'name': pulse.get('name'),
                            'description': pulse.get('description'),
                            'author_name': pulse.get('author_name'),
                            'created': pulse.get('created'),
                            'modified': pulse.get('modified'),
                            'tags': pulse.get('tags', []),
                            'TLP': pulse.get('TLP'),
                            'threat_hunter_scoring': pulse.get('threat_hunter_scoring', {}),
                            'adversary': pulse.get('adversary'),
                            'malware_families': pulse.get('malware_families', []),
                            'attack_ids': pulse.get('attack_ids', [])
                        },
                        'raw_url': url
                    }
                    
                    tags = self._extract_indicator_tags(pulse_data['pulse_info'])
                    tags.append('pulse')
                    
                    result = self.normalize_hash_data(
                        indicator=hash_value,
                        data=pulse_data,
                        tags=tags,
                        confidence=0.7,
                        score=pulse.get('indicators_count', 0)
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting pulses for hash {hash_value}: {str(e)}")


# Example usage and testing
async def main():
    """Example usage of AlienVault OTX collector"""
    # Set your AlienVault OTX API key here
    api_key = "YOUR_ALIENVAULT_OTX_API_KEY"
    
    async with AlienVaultOTXCollector(api_key) as collector:
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
        
        # Test URL lookup
        print("\nTesting URL lookup...")
        url_results = await collector.lookup_url("https://www.google.com/search?q=test")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test hash lookup
        print("\nTesting hash lookup...")
        hash_results = await collector.lookup_hash("d41d8cd98f00b204e9800998ecf8427e")
        print(f"Hash results: {len(hash_results)} found")
        for result in hash_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())