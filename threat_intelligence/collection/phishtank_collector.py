#!/usr/bin/env python3
"""
PhishTank API Collector
Provides threat intelligence from PhishTank (phishing URL database)
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class PhishTankCollector(BaseThreatCollector):
    """PhishTank collector"""
    
    def __init__(self, app_key: str):
        super().__init__("PhishTank", rate_limit=1000, time_window=3600)  # 1000 requests per hour
        self.app_key = app_key
        self.base_url = "https://checkurl.phishtank.com/checkurl/"
    
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
    
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup URL information"""
        results = []
        
        try:
            # Canonicalize URL
            canonical_url = self._canonicalize_url(url)
            
            # Prepare PhishTank API request
            form_data = {
                'url': canonical_url,
                'app_key': self.app_key,
                'format': 'json',
                'verbose': 'yes'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'ThreatIntelligenceCollector/1.0'
            }
            
            data = await self._make_request(
                self.base_url, 
                method="POST", 
                headers=headers,
                json_data=form_data  # Will be converted to form data
            )
            
            if data and 'results' in data:
                result_data = data['results']
                
                # Extract phishing information
                in_database = result_data.get('in_database', 'false')
                verified = result_data.get('verified', 'false')
                valid = result_data.get('valid', 'false')
                
                tags = ['phishtank-url']
                
                confidence = 0.0
                score = 0
                
                if in_database == 'true':
                    tags.append('in-phishtank-db')
                    
                    if valid == 'true':
                        tags.append('verified-phishing')
                        confidence = 0.95
                        score = 100
                    elif verified == 'true':
                        tags.append('verified-suspicious')
                        confidence = 0.8
                        score = 80
                    else:
                        tags.append('reported-phishing')
                        confidence = 0.6
                        score = 60
                else:
                    tags.append('not-in-phishtank-db')
                    confidence = 0.1
                    score = 0
                
                # Add additional metadata
                if in_database == 'true':
                    metadata = {
                        'phish_id': result_data.get('phish_id'),
                        'url': result_data.get('url'),
                        'in_database': in_database,
                        'verified': verified,
                        'valid': valid,
                        'submitted': result_data.get('submitted'),
                        'verified_at': result_data.get('verified_at'),
                        'online': result_data.get('online'),
                        'target': result_data.get('target'),
                        'ip_address': result_data.get('ip_address'),
                        'country': result_data.get('country'),
                        'cname': result_data.get('cname'),
                        'ans': result_data.get('ans'),
                        'raw_url': self.base_url
                    }
                else:
                    metadata = {
                        'in_database': in_database,
                        'url': canonical_url,
                        'raw_url': self.base_url
                    }
                
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data=metadata,
                    tags=tags,
                    confidence=confidence,
                    score=score
                )
                results.append(result)
                
                # Get additional details if URL is in database
                if in_database == 'true':
                    await self._get_phishing_details(result_data.get('phish_id'), results)
                
            else:
                # Response format unexpected
                result = self.normalize_url_data(
                    indicator=canonical_url,
                    data={
                        'error': 'Unexpected response format',
                        'raw_response': data,
                        'raw_url': self.base_url
                    },
                    tags=['error'],
                    confidence=0.0,
                    score=0
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up URL {url} in PhishTank: {str(e)}")
        
        return results
    
    async def _get_phishing_details(self, phish_id: str, results: List[ThreatIntelligenceData]):
        """Get detailed phishing information"""
        try:
            # PhishTank doesn't provide a detailed lookup API,
            # so we'll note that the information is already included in the main response
            detail_data = {
                'detailed_info': {
                    'note': 'Detailed phishing information included in main response',
                    'phish_id': phish_id,
                    'lookup_complete': True
                }
            }
            
            # Add as additional result to the first URL result
            if results:
                url_indicator = results[0].indicator
                
                result = self.normalize_url_data(
                    indicator=url_indicator,
                    data=detail_data,
                    tags=['phishtank-details'],
                    confidence=0.8,
                    score=10
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error getting phishing details for {phish_id}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Search for URLs with this domain by testing common phishing patterns
            # PhishTank doesn't provide domain-based search, so we'll check if the domain
            # has been used in known phishing campaigns
            
            # Check if domain itself is used as a URL
            url_tests = [
                f"http://{domain}",
                f"https://{domain}",
                f"http://{domain}/",
                f"https://{domain}/",
                f"http://www.{domain}",
                f"https://www.{domain}"
            ]
            
            for test_url in url_tests:
                url_results = await self.lookup_url(test_url)
                
                # Convert URL results to domain results with context
                for url_result in url_results:
                    domain_result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'url_check': {
                                'url': test_url,
                                'url_data': url_result.raw_data
                            },
                            'note': 'Domain checked via URL lookup in PhishTank'
                        },
                        tags=url_result.tags + ['domain-check'],
                        confidence=url_result.confidence * 0.8,  # Lower confidence for domain inference
                        score=url_result.score * 0.8
                    )
                    results.append(domain_result)
                
                # If we found phishing, no need to check other URLs
                if any(result.confidence > 0.5 for result in url_results):
                    break
                    
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in PhishTank: {str(e)}")
        
        return results
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        try:
            # Check if IP has been used in phishing campaigns
            ip_url = f"http://{ip}/"
            url_results = await self.lookup_url(ip_url)
            
            # Convert URL results to IP results
            for url_result in url_results:
                ip_result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'url_check': {
                            'url': ip_url,
                            'url_data': url_result.raw_data
                        },
                        'note': 'IP checked via URL lookup in PhishTank'
                    },
                    tags=url_result.tags + ['ip-check'],
                    confidence=url_result.confidence * 0.8,
                    score=url_result.score * 0.8
                )
                results.append(ip_result)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in PhishTank: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - PhishTank doesn't support hash lookups"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'PhishTank does not support file hash lookups',
                'supported_indicators': ['URLs'],
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
    """Example usage of PhishTank collector"""
    # Set your PhishTank app key here
    app_key = "YOUR_PHISHTANK_APP_KEY"
    
    async with PhishTankCollector(app_key) as collector:
        # Test URL lookup
        print("Testing URL lookup...")
        url_results = await collector.lookup_url("http://fake-bank.com/login")
        print(f"URL results: {len(url_results)} found")
        for result in url_results:
            print(f"  - {result.indicator[:50]}... (confidence: {result.confidence}, tags: {result.tags})")
        
        # Test domain lookup
        print("\nTesting domain lookup...")
        domain_results = await collector.lookup_domain("fake-bank.com")
        print(f"Domain results: {len(domain_results)} found")
        for result in domain_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")
        
        # Test IP lookup
        print("\nTesting IP lookup...")
        ip_results = await collector.lookup_ip("192.0.2.1")
        print(f"IP results: {len(ip_results)} found")
        for result in ip_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())