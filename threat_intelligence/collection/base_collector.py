#!/usr/bin/env python3
"""
Base Threat Intelligence Collector
Provides common functionality for all threat intelligence collectors
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ThreatIntelligenceData:
    """Standardized threat intelligence data format"""
    source: str
    indicator_type: str  # 'ip', 'domain', 'url', 'hash', 'email'
    indicator: str
    timestamp: datetime
    confidence: Optional[float] = None
    score: Optional[float] = None
    tags: List[str] = None
    raw_data: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.raw_data is None:
            self.raw_data = {}
        if self.metadata is None:
            self.metadata = {}


class BaseThreatCollector(ABC):
    """Base class for all threat intelligence collectors"""
    
    def __init__(self, name: str, rate_limit: int = 60, time_window: int = 60):
        self.name = name
        self.rate_limit = rate_limit  # requests per time_window
        self.time_window = time_window  # time window in seconds
        self.request_times = []
        self.session = None
        self.api_key = None
        self.api_key_header = None
        
    def set_api_key(self, api_key: str, header_name: str = "X-API-Key"):
        """Set API key and header name for authentication"""
        self.api_key = api_key
        self.api_key_header = header_name
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        # Remove old timestamps
        self.request_times = [t for t in self.request_times if now - t < self.time_window]
        
        if len(self.request_times) >= self.rate_limit:
            sleep_time = self.time_window - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                return self._rate_limit()  # Check again after sleeping
        
        self.request_times.append(now)
    
    async def _make_request(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Dict[str, str] = None,
        params: Dict[str, str] = None,
        json_data: Dict[str, Any] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling and rate limiting"""
        await self._rate_limit()
        
        if headers is None:
            headers = {}
        
        # Add authentication header if API key is set
        if self.api_key and self.api_key_header:
            headers[self.api_key_header] = self.api_key
        
        # Add default headers
        headers.update({
            'User-Agent': f'ThreatIntelligenceCollector/1.0',
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
                    logger.warning(f"Rate limited by {self.name}. Waiting...")
                    await asyncio.sleep(60)
                    return await self._make_request(url, method, headers, params, json_data, timeout)
                else:
                    logger.error(f"HTTP {response.status} for {self.name}: {await response.text()}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout for {self.name} request to {url}")
            return None
        except Exception as e:
            logger.error(f"Error making request to {self.name}: {str(e)}")
            return None
    
    @abstractmethod
    async def lookup_ip(self, ip: str) -> List[ThreatIntelligenceData]:
        """Lookup threat intelligence for IP address"""
        pass
    
    @abstractmethod
    async def lookup_domain(self, domain: str) -> List[ThreatIntelligenceData]:
        """Lookup threat intelligence for domain"""
        pass
    
    @abstractmethod
    async def lookup_url(self, url: str) -> List[ThreatIntelligenceData]:
        """Lookup threat intelligence for URL"""
        pass
    
    @abstractmethod
    async def lookup_hash(self, file_hash: str) -> List[ThreatIntelligenceData]:
        """Lookup threat intelligence for file hash"""
        pass
    
    def normalize_ip_data(
        self, 
        indicator: str, 
        data: Dict[str, Any], 
        tags: List[str] = None,
        confidence: float = None,
        score: float = None
    ) -> ThreatIntelligenceData:
        """Normalize IP data to standard format"""
        return ThreatIntelligenceData(
            source=self.name,
            indicator_type='ip',
            indicator=indicator,
            timestamp=datetime.now(timezone.utc),
            confidence=confidence,
            score=score,
            tags=tags or [],
            raw_data=data
        )
    
    def normalize_domain_data(
        self, 
        indicator: str, 
        data: Dict[str, Any], 
        tags: List[str] = None,
        confidence: float = None,
        score: float = None
    ) -> ThreatIntelligenceData:
        """Normalize domain data to standard format"""
        return ThreatIntelligenceData(
            source=self.name,
            indicator_type='domain',
            indicator=indicator,
            timestamp=datetime.now(timezone.utc),
            confidence=confidence,
            score=score,
            tags=tags or [],
            raw_data=data
        )
    
    def normalize_url_data(
        self, 
        indicator: str, 
        data: Dict[str, Any], 
        tags: List[str] = None,
        confidence: float = None,
        score: float = None
    ) -> ThreatIntelligenceData:
        """Normalize URL data to standard format"""
        return ThreatIntelligenceData(
            source=self.name,
            indicator_type='url',
            indicator=indicator,
            timestamp=datetime.now(timezone.utc),
            confidence=confidence,
            score=score,
            tags=tags or [],
            raw_data=data
        )
    
    def normalize_hash_data(
        self, 
        indicator: str, 
        data: Dict[str, Any], 
        tags: List[str] = None,
        confidence: float = None,
        score: float = None
    ) -> ThreatIntelligenceData:
        """Normalize hash data to standard format"""
        return ThreatIntelligenceData(
            source=self.name,
            indicator_type='hash',
            indicator=indicator,
            timestamp=datetime.now(timezone.utc),
            confidence=confidence,
            score=score,
            tags=tags or [],
            raw_data=data
        )
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


def save_results_to_file(results: List[ThreatIntelligenceData], filename: str):
    """Save threat intelligence results to JSON file"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump([
                {
                    'source': result.source,
                    'indicator_type': result.indicator_type,
                    'indicator': result.indicator,
                    'timestamp': result.timestamp.isoformat(),
                    'confidence': result.confidence,
                    'score': result.score,
                    'tags': result.tags,
                    'raw_data': result.raw_data,
                    'metadata': result.metadata
                }
                for result in results
            ], f, indent=2)
        
        logger.info(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving results to {filename}: {str(e)}")