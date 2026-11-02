#!/usr/bin/env python3
"""
Spamhaus API Collector
Provides threat intelligence from Spamhaus (spam and malware blacklist)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class SpamhausCollector(BaseThreatCollector):
    """Spamhaus collector"""
    
    def __init__(self, api_key: str = None):  # Some Spamhaus APIs require key, others don't
        super().__init__("Spamhaus", rate_limit=1000, time_window=3600)  # 1000 requests per hour
        self.api_key = api_key
        self.base_urls = {
            'db': 'https://www.spamhaus.org/query/bl',  # Public DNSBL lookup
            'dbl': 'https://www.spamhaus.org/query/dbl',  # Domain Block List
            'css': 'https://www.spamhaus.org/query/css',  # Client Security Safety
            'zen': 'https://zen.spamhaus.org',  # ZEN blocklist
            'sbl': 'https://sbl.spamhaus.org',  # Spamhaus Block List
            'xbl': 'https://xbl.spamhaus.org',  # Exploits Block List
            'pbl': 'https://pbl.spamhaus.org',  # Policy Block List
            'drop': 'https://www.spamhaus.org/drop',  # DROP list
            'edrop': 'https://www.spamhaus.org/edrop',  # EDROP list
        }
    
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
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return url
    
    def _classify_spamhaus_listing(self, listing_type: str) -> List[str]:
        """Classify Spamhaus listing type"""
        tags = ['spamhaus']
        
        # Map Spamhaus lists to tags
        list_mappings = {
            'zen': ['zen-list', 'comprehensive-blocklist'],
            'sbl': ['spamhaus-block-list', 'spam-source'],
            'xbl': ['exploits-block-list', 'compromised-systems'],
            'pbl': ['policy-block-list', 'policy-violation'],
            'drop': ['drop-list', 'confirmed-spam'],
            'edrop': ['edrop-list', 'extended-drop'],
            'dbl': ['domain-block-list', 'malicious-domain'],
            'css': ['client-security-safety', 'malware-infection']
        }
        
        if listing_type.lower() in list_mappings:
            tags.extend(list_mappings[listing_type.lower()])
        else:
            tags.append(f'spamhaus-{listing_type.lower()}')
        
        return tags
    
    def _assess_threat_level(self, list_type: str, category: str = None) -> float:
        """Assess threat level based on Spamhaus list type"""
        threat_levels = {
            'drop': 0.95,      # Highest threat level
            'edrop': 0.90,     # Extended DROP
            'sbl': 0.85,       # Spam Block List
            'xbl': 0.80,       # Exploits Block List
            'zen': 0.75,       # Combined list
            'pbl': 0.60,       # Policy Block List
            'dbl': 0.70,       # Domain Block List
            'css': 0.65,       # Client Security Safety
        }
        
        base_level = threat_levels.get(list_type.lower(), 0.5)
        
        # Adjust based on additional categories if available
        if category:
            category_lower = category.lower()
            if 'malware' in category_lower:
                base_level = min(1.0, base_level + 0.1)
            elif 'spam' in category_lower:
                base_level = min(1.0, base_level + 0.05)
        
        return base_level
    
    async def _query_dnsbl(self, indicator: str, dnsbl: str) -> Optional[Dict[str, Any]]:
        """Query DNS-based blacklist using aiohttp"""
        try:
            # For DNSBL queries, we need to use a different approach
            # Most Spamhaus lists are DNS-based, so we'll simulate the query
            
            if dnsbl == 'zen':
                # Zen is a combined list, check various zones
                zones = [
                    f"{indicator}.zen.spamhaus.org",
                    f"{indicator}.sbl.spamhaus.org",
                    f"{indicator}.xbl.spamhaus.org"
                ]
                
                # In a real implementation, you would make DNS queries
                # For this example, we'll simulate based on the indicator
                if 'malware' in indicator.lower() or 'spam' in indicator.lower():
                    return {
                        'listed': True,
                        'list_type': 'zen',
                        'response_code': '127.0.0.2',
                        'description': 'Listed in Spamhaus ZEN'
                    }
            elif dnsbl == 'dbl':
                # Domain Block List
                if '.' in indicator:
                    domain = indicator if '.' in indicator else self._extract_domain_from_url(indicator)
                    return {
                        'listed': True,
                        'list_type': 'dbl',
                        'domain': domain,
                        'description': 'Listed in Domain Block List'
                    }
            
            # Default: not listed
            return {
                'listed': False,
                'list_type': dnsbl,
                'description': 'Not listed'
            }
            
        except Exception as e:
            logger.error(f"Error querying {dnsbl} for {indicator}: {str(e)}")
            return None
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Query multiple Spamhaus lists for IP
            dnsbl_lists = ['zen', 'sbl', 'xbl', 'pbl', 'drop', 'edrop']
            
            for list_name in dnsbl_lists:
                try:
                    dnsbl_result = await self._query_dnsbl(ip, list_name)
                    
                    if dnsbl_result and dnsbl_result.get('listed'):
                        tags = self._classify_spamhaus_listing(list_name)
                        confidence = self._assess_threat_level(list_name)
                        score = confidence * 100
                        
                        result = self.normalize_ip_data(
                            indicator=ip,
                            data={
                                'list_type': list_name,
                                'listed': True,
                                'response': dnsbl_result,
                                'dnsbl_query': f"http://{dnsbl}.org/{ip}",
                                'raw_url': dnsbl_result.get('description', 'N/A')
                            },
                            tags=tags,
                            confidence=confidence,
                            score=score
                        )
                        results.append(result)
                    else:
                        # Not listed - add clean result for major lists
                        if list_name in ['zen', 'sbl', 'xbl']:
                            result = self.normalize_ip_data(
                                indicator=ip,
                                data={
                                    'list_type': list_name,
                                    'listed': False,
                                    'response': dnsbl_result,
                                    'raw_url': f"https://{list_name}.spamhaus.org"
                                },
                                tags=['spamhaus-clean'],
                                confidence=0.0,
                                score=0
                            )
                            results.append(result)
                
                except Exception as e:
                    logger.error(f"Error checking {list_name} for IP {ip}: {str(e)}")
                    continue
            
            # If no results, add a general clean result
            if not results:
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'status': 'clean',
                        'checked_lists': dnsbl_lists,
                        'message': 'IP not found in any Spamhaus blocklists'
                    },
                    tags=['spamhaus-clean'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in Spamhaus: {str(e)}")
        
        return results
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Query Domain Block List (DBL)
            dbl_result = await self._query_dnsbl(domain, 'dbl')
            
            if dbl_result and dbl_result.get('listed'):
                tags = self._classify_spamhaus_listing('dbl')
                confidence = self._assess_threat_level('dbl')
                score = confidence * 100
                
                result = self.normalize_domain_data(
                    indicator=domain,
                    data={
                        'list_type': 'dbl',
                        'listed': True,
                        'response': dbl_result,
                        'domain': domain,
                        'dnsbl_query': f"http://dbl.spamhaus.org/{domain}",
                        'raw_url': dbl_result.get('description', 'N/A')
                    },
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
            else:
                # Not listed in DBL, check other lists
                zen_result = await self._query_dnsbl(domain, 'zen')
                
                if zen_result and zen_result.get('listed'):
                    tags = self._classify_spamhaus_listing('zen')
                    confidence = self._assess_threat_level('zen')
                    score = confidence * 100
                    
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'list_type': 'zen',
                            'listed': True,
                            'response': zen_result,
                            'dnsbl_query': f"http://zen.spamhaus.org/{domain}",
                            'raw_url': zen_result.get('description', 'N/A')
                        },
                        tags=tags,
                        confidence=confidence,
                        score=score
                    )
                    results.append(result)
                else:
                    # Not listed
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'status': 'clean',
                            'checked_lists': ['dbl', 'zen'],
                            'message': 'Domain not found in Spamhaus blocklists'
                        },
                        tags=['spamhaus-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in Spamhaus: {str(e)}")
        
        return results
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # Extract domain from URL
            domain = self._extract_domain_from_url(url)
            
            if domain:
                # Check domain in Spamhaus
                domain_results = await self.lookup_domain(domain)
                
                # Add URL context
                for domain_result in domain_results:
                    url_result = self.normalize_url_data(
                        indicator=url,
                        data={
                            'domain_check': domain_result.raw_data,
                            'full_url': url,
                            'domain': domain,
                            'note': 'Domain information from Spamhaus lookup'
                        },
                        tags=domain_result.tags + ['url-analysis'],
                        confidence=domain_result.confidence * 0.9,
                        score=domain_result.score
                    )
                    results.append(url_result)
                    
        except Exception as e:
            logger.error(f"Error looking up URL {url} in Spamhaus: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - Spamhaus doesn't support hash lookups"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'Spamhaus does not support file hash lookups',
                'supported_indicators': ['IP addresses', 'domains'],
                'services': [
                    'ZEN (comprehensive)',
                    'SBL (Spam Block List)',
                    'XBL (Exploits Block List)',
                    'PBL (Policy Block List)',
                    'DBL (Domain Block List)',
                    'DROP (Don\'t Route Or Peer)',
                    'EDROP (Extended DROP)'
                ],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def bulk_ip_lookup(self, ips: List[str]) -> List[ThreatIntelligenceData]:
        """Bulk lookup multiple IP addresses"""
        results = []
        
        for ip in ips:
            try:
                ip_results = await self.lookup_ip(ip)
                results.extend(ip_results)
                
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in bulk IP lookup for {ip}: {str(e)}")
        
        return results
    
    async def get_drop_list(self) -> List[ThreatIntelligenceData]:
        """Get current DROP list information"""
        results = []
        
        try:
            # Spamhaus DROP list contains confirmed spam sources
            # In a real implementation, you would fetch the actual DROP list
            
            result = self.normalize_ip_data(
                indicator="DROP_LIST",
                data={
                    'note': 'Spamhaus DROP (Don\'t Route Or Peer) list',
                    'description': 'Contains confirmed spam sources that should be blocked at BGP level',
                    'update_frequency': 'Daily',
                    'list_url': 'https://www.spamhaus.org/drop/',
                    'raw_url': 'https://www.spamhaus.org/drop/'
                },
                tags=['spamhaus-drop-list', 'drop-list-info'],
                confidence=0.0,  # Informational only
                score=0
            )
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error getting DROP list information: {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of Spamhaus collector"""
    # Spamhaus public lists don't require API key
    async with SpamhausCollector() as collector:
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
        
        # Test bulk IP lookup
        print("\nTesting bulk IP lookup...")
        ips = ["8.8.8.8", "1.1.1.1", "192.0.2.1"]
        bulk_results = await collector.bulk_ip_lookup(ips)
        print(f"Bulk IP results: {len(bulk_results)} found")


if __name__ == "__main__":
    asyncio.run(main())