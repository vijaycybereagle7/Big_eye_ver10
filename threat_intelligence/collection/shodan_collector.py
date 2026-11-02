#!/usr/bin/env python3
"""
Shodan API Collector
Provides threat intelligence from Shodan
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import quote

from base_collector import BaseThreatCollector, ThreatIntelligenceData

logger = logging.getLogger(__name__)


class ShodanCollector(BaseThreatCollector):
    """Shodan collector"""
    
    def __init__(self, api_key: str):
        super().__init__("Shodan", rate_limit=100, time_window=86400)  # 100 requests per day (free tier)
        self.set_api_key(api_key)
        self.base_url = "https://api.shodan.io"
    
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
    
    async def _make_request(self, url: str, method: str = "GET", headers: Dict[str, str] = None, params: Dict[str, str] = None, json_data: Dict[str, Any] = None, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make HTTP request with Shodan API key parameter"""
        await self._rate_limit()
        
        if headers is None:
            headers = {}
        
        # Add API key to query parameters for Shodan
        if params is None:
            params = {}
        
        params['key'] = self.api_key
        
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
                elif response.status == 429:
                    logger.warning(f"Rate limited by Shodan. Waiting...")
                    await asyncio.sleep(60)
                    return await self._make_request(url, method, headers, params, json_data, timeout)
                else:
                    error_text = await response.text()
                    logger.error(f"HTTP {response.status} for Shodan: {error_text}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout for Shodan request to {url}")
            return None
        except Exception as e:
            logger.error(f"Error making request to Shodan: {str(e)}")
            return None
    
    def _extract_shodan_tags(self, host_info: Dict[str, Any]) -> List[str]:
        """Extract relevant tags from Shodan host information"""
        tags = []
        
        # Extract tags from host data
        if 'tags' in host_info:
            tags.extend(host_info['tags'])
        
        # Add tags based on detected vulnerabilities
        vulns = host_info.get('vulns', {})
        if vulns:
            tags.append('has-vulnerabilities')
            for vuln_id in vulns.keys():
                if 'CVE' in vuln_id:
                    tags.append('cve-vulnerability')
        
        # Add tags based on services
        services = host_info.get('data', [])
        if services:
            ports = [str(service.get('port', 0)) for service in services if service.get('port')]
            if ports:
                tags.extend([f'port-{port}' for port in set(ports)])
            
            protocols = [service.get('transport', 'unknown') for service in services]
            tags.extend([f'transport-{proto}' for proto in set(protocols)])
        
        # Add location-based tags
        if host_info.get('country_name'):
            tags.append(f'country-{host_info["country_name"].lower().replace(" ", "-")}')
        
        if host_info.get('city'):
            tags.append(f'city-{host_info["city"].lower().replace(" ", "-")}')
        
        # Add organization tags
        if host_info.get('org'):
            tags.append('has-organization')
        
        # Add ISP tags
        if host_info.get('isp'):
            tags.append('has-isp')
        
        return tags
    
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup IP address information"""
        results = []
        
        if not self._is_valid_ip(ip):
            logger.warning(f"Invalid IP address: {ip}")
            return results
        
        try:
            # Get host information
            url = f"{self.base_url}/shodan/host/{ip}"
            data = await self._make_request(url)
            
            if data:
                host_info = data
                
                # Extract threat intelligence
                tags = self._extract_shodan_tags(host_info)
                tags.append('shodan-host')
                
                # Calculate confidence based on data richness
                confidence_factors = [
                    host_info.get('tags', []),
                    host_info.get('vulns', {}),
                    host_info.get('hostnames', []),
                    host_info.get('ports', []),
                    host_info.get('data', [])
                ]
                
                non_empty_factors = sum(1 for factor in confidence_factors if factor)
                confidence = min(1.0, non_empty_factors * 0.2)
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data={
                        'ip': host_info.get('ip'),
                        'ip_str': host_info.get('ip_str'),
                        'port': host_info.get('port'),
                        'protocol': host_info.get('protocol'),
                        'timestamp': host_info.get('timestamp'),
                        'hostnames': host_info.get('hostnames', []),
                        'domains': host_info.get('domains', []),
                        'org': host_info.get('org'),
                        'isp': host_info.get('isp'),
                        'hostnames': host_info.get('hostnames', []),
                        'city': host_info.get('city'),
                        'country_name': host_info.get('country_name'),
                        'country_code': host_info.get('country_code'),
                        'latitude': host_info.get('latitude'),
                        'longitude': host_info.get('longitude'),
                        'open_ports': host_info.get('ports', []),
                        'tags': host_info.get('tags', []),
                        'vulns': host_info.get('vulns', {}),
                        'services': len(host_info.get('data', [])),
                        'data_count': len(host_info.get('data', [])),
                        'raw_url': url
                    },
                    tags=tags,
                    confidence=confidence,
                    score=len(host_info.get('vulns', {})) * 10 + len(host_info.get('ports', []))
                )
                results.append(result)
                
                # Get detailed service information
                await self._get_ip_services(ip, results)
                
                # Get vulnerabilities if any
                await self._get_ip_vulnerabilities(ip, results)
                
        except Exception as e:
            logger.error(f"Error looking up IP {ip} in Shodan: {str(e)}")
        
        return results
    
    async def _get_ip_services(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get detailed service information for IP"""
        try:
            # Use the same host endpoint to get detailed data
            url = f"{self.base_url}/shodan/host/{ip}"
            data = await self._make_request(url)
            
            if data and 'data' in data:
                for service in data['data'][:10]:  # Limit to first 10 services
                    service_data = {
                        'service_info': {
                            'port': service.get('port'),
                            'transport': service.get('transport'),
                            'protocol': service.get('protocol'),
                            'banner': service.get('banner'),
                            'service': service.get('service', {}),
                            'product': service.get('product'),
                            'version': service.get('version'),
                            'extrainfo': service.get('extrainfo'),
                            'hostnames': service.get('hostnames', []),
                            'timestamp': service.get('timestamp'),
                            'hostnames': service.get('hostnames', []),
                            'location': service.get('location', {})
                        },
                        'raw_url': url
                    }
                    
                    tags = ['service-analysis']
                    if service.get('product'):
                        tags.append(f"product-{service['product'].lower().replace(' ', '-')}")
                    if service.get('port'):
                        tags.append(f"port-{service['port']}")
                    
                    result = self.normalize_ip_data(
                        indicator=ip,
                        data=service_data,
                        tags=tags,
                        confidence=0.6,
                        score=1.0
                    )
                    results.append(result)
                    
        except Exception as e:
            logger.error(f"Error getting services for IP {ip}: {str(e)}")
    
    async def _get_ip_vulnerabilities(self, ip: str, results: List[ThreatIntelligenceData]):
        """Get vulnerability information for IP"""
        try:
            # Check vulnerabilities in host info
            url = f"{self.base_url}/shodan/host/{ip}"
            data = await self._make_request(url)
            
            if data and 'vulns' in data and data['vulns']:
                vuln_data = {
                    'vulnerability_info': {
                        'total_vulnerabilities': len(data['vulns']),
                        'vulnerabilities': data['vulns'],
                        'cvss_scores': [
                            vuln_data.get('cvss', 0) 
                            for vuln_data in data['vulns'].values()
                        ],
                        'high_cvss_count': sum(
                            1 for vuln_data in data['vulns'].values()
                            if vuln_data.get('cvss', 0) >= 7.0
                        )
                    },
                    'raw_url': url
                }
                
                tags = ['vulnerability', 'cvss-scoring']
                avg_cvss = sum(vuln_data['cvss_scores']) / len(vuln_data['cvss_scores'])
                if avg_cvss >= 9.0:
                    tags.append('critical-vulnerability')
                elif avg_cvss >= 7.0:
                    tags.append('high-vulnerability')
                elif avg_cvss >= 4.0:
                    tags.append('medium-vulnerability')
                else:
                    tags.append('low-vulnerability')
                
                result = self.normalize_ip_data(
                    indicator=ip,
                    data=vuln_data,
                    tags=tags,
                    confidence=min(1.0, avg_cvss / 10.0),
                    score=avg_cvss * 10
                )
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error getting vulnerabilities for IP {ip}: {str(e)}")
    
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup domain information"""
        results = []
        
        try:
            # Search for domain in Shodan
            query = f"hostname:{domain}"
            url = f"{self.base_url}/shodan/host/search"
            params = {
                'query': query,
                'minify': 'true'
            }
            
            data = await self._make_request(url, params=params)
            
            if data and 'matches' in data:
                matches = data['matches']
                
                if matches:
                    # Analyze results
                    total_results = len(matches)
                    ports = set()
                    services = set()
                    ips = set()
                    vulns = 0
                    
                    for match in matches[:20]:  # Analyze first 20 results
                        if 'port' in match:
                            ports.add(match['port'])
                        if 'product' in match:
                            services.add(match['product'])
                        if 'ip_str' in match:
                            ips.add(match['ip_str'])
                        if 'vulns' in match:
                            vulns += len(match['vulns'])
                    
                    tags = ['domain-shodan-search']
                    tags.extend([f"port-{port}" for port in ports])
                    tags.extend([f"service-{service.lower().replace(' ', '-')}" for service in services])
                    
                    if vulns > 0:
                        tags.append('has-vulnerabilities')
                    
                    confidence = min(1.0, (total_results + len(ips)) * 0.1)
                    
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'total_results': total_results,
                            'unique_ips': len(ips),
                            'ip_addresses': list(ips),
                            'unique_ports': len(ports),
                            'ports': list(ports),
                            'services': list(services),
                            'vulnerability_count': vulns,
                            'query_used': query,
                            'sample_results': matches[:5],  # First 5 results as sample
                            'raw_url': url
                        },
                        tags=tags,
                        confidence=confidence,
                        score=total_results + vulns
                    )
                    results.append(result)
                else:
                    # No results found
                    result = self.normalize_domain_data(
                        indicator=domain,
                        data={
                            'total_results': 0,
                            'query_used': query,
                            'status': 'no-results',
                            'raw_url': url
                        },
                        tags=['domain-clean'],
                        confidence=0.0,
                        score=0
                    )
                    results.append(result)
                
        except Exception as e:
            logger.error(f"Error looking up domain {domain} in Shodan: {str(e)}")
        
        return results
    
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
                            'note': 'Information derived from Shodan domain search'
                        },
                        tags=domain_result.tags + ['url-analysis'],
                        confidence=domain_result.confidence * 0.9,
                        score=domain_result.score
                    )
                    results.append(url_result)
                    
        except Exception as e:
            logger.error(f"Error looking up URL {url} in Shodan: {str(e)}")
        
        return results
    
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup file hash - Shodan doesn't support hash lookups directly"""
        results = []
        
        result = self.normalize_hash_data(
            indicator=file_hash,
            data={
                'note': 'Shodan does not directly support file hash lookups',
                'suggested_approach': 'Use Shodan to find malware distribution infrastructure',
                'supported_indicators': ['IP addresses', 'domains', 'network services'],
                'raw_url': None
            },
            tags=['not-supported'],
            confidence=0.0,
            score=0.0
        )
        results.append(result)
        
        return results
    
    async def search_query(self, query: str, limit: int = 100) -> List[ThreatIntelligenceData]:
        """Search Shodan with arbitrary query"""
        results = []
        
        try:
            url = f"{self.base_url}/shodan/host/search"
            params = {
                'query': query,
                'minify': 'true'
            }
            
            if limit:
                params['limit'] = str(limit)
            
            data = await self._make_request(url, params=params)
            
            if data and 'matches' in data:
                for match in data['matches'][:limit]:
                    ip_str = match.get('ip_str', '')
                    
                    if self._is_valid_ip(ip_str):
                        result = self.normalize_ip_data(
                            indicator=ip_str,
                            data={
                                'search_result': {
                                    'query': query,
                                    'product': match.get('product'),
                                    'version': match.get('version'),
                                    'port': match.get('port'),
                                    'protocol': match.get('protocol'),
                                    'org': match.get('org'),
                                    'isp': match.get('isp'),
                                    'country_name': match.get('country_name'),
                                    'city': match.get('city'),
                                    'tags': match.get('tags', []),
                                    'hostnames': match.get('hostnames', [])
                                },
                                'raw_url': url
                            },
                            tags=['shodan-search-result'],
                            confidence=0.7,
                            score=1.0
                        )
                        results.append(result)
                        
        except Exception as e:
            logger.error(f"Error searching Shodan with query '{query}': {str(e)}")
        
        return results


# Example usage and testing
async def main():
    """Example usage of Shodan collector"""
    # Set your Shodan API key here
    api_key = "YOUR_SHODAN_API_KEY"
    
    async with ShodanCollector(api_key) as collector:
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
        
        # Test search query
        print("\nTesting search query...")
        search_results = await collector.search_query("country:CN product:nginx", limit=5)
        print(f"Search results: {len(search_results)} found")
        for result in search_results:
            print(f"  - {result.indicator} (confidence: {result.confidence})")


if __name__ == "__main__":
    asyncio.run(main())