"""Reputation intelligence service with external API integration."""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor

from ..config.settings import settings
from ..cache.redis_cache import cached, cache_get, cache_set, generate_cache_key
from ..models.schemas import ReputationResult, ReputationSource

logger = logging.getLogger(__name__)


class ReputationService:
    """Service for querying reputation from multiple threat intelligence sources."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Reputation sources configuration
        self.sources = {
            "virustotal": {
                "name": "VirusTotal",
                "url": "https://www.virustotal.com/vtapi/v2/",
                "api_key": settings.VIRUSTOTAL_API_KEY,
                "weight": 0.25,
                "supported_types": ["ip", "domain", "url", "hash"]
            },
            "abuseipdb": {
                "name": "AbuseIPDB",
                "url": "https://api.abuseipdb.com/api/v2/",
                "api_key": settings.ABUSEIPDB_API_KEY,
                "weight": 0.20,
                "supported_types": ["ip"]
            },
            "shodan": {
                "name": "Shodan",
                "url": "https://api.shodan.io/",
                "api_key": settings.SHODAN_API_KEY,
                "weight": 0.15,
                "supported_types": ["ip", "domain"]
            },
            "greynoise": {
                "name": "GreyNoise",
                "url": "https://api.greynoise.io/v3/",
                "api_key": settings.GREYNOISE_API_KEY,
                "weight": 0.20,
                "supported_types": ["ip"]
            },
            "otx": {
                "name": "AlienVault OTX",
                "url": "https://otx.alienvault.com/api/v1/",
                "api_key": settings.OTX_API_KEY,
                "weight": 0.10,
                "supported_types": ["ip", "domain", "url", "hash"]
            },
            "securitytrails": {
                "name": "SecurityTrails",
                "url": "https://api.securitytrails.com/v1/",
                "api_key": settings.SECURITYTRAILS_API_KEY,
                "weight": 0.10,
                "supported_types": ["ip", "domain"]
            }
        }
    
    async def query_reputation(
        self,
        value: str,
        value_type: str,
        sources: Optional[List[str]] = None,
        detailed: bool = False
    ) -> ReputationResult:
        """Query reputation from multiple sources."""
        start_time = datetime.utcnow()
        
        try:
            # Validate value type
            if value_type not in ["ip", "domain", "url", "hash", "email"]:
                raise ValueError(f"Unsupported value type: {value_type}")
            
            # Check cache first
            cache_key = generate_cache_key("reputation", f"{value_type}:{value}", "default")
            cached_result = await cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for reputation query: {value_type}:{value}")
                return ReputationResult(**cached_result)
            
            # Determine which sources to use
            if sources:
                # Use specified sources
                active_sources = {k: v for k, v in self.sources.items() if k in sources}
            else:
                # Use all available sources that support this value type
                active_sources = {
                    k: v for k, v in self.sources.items() 
                    if v["api_key"] and value_type in v["supported_types"]
                }
            
            if not active_sources:
                logger.warning(f"No reputation sources available for {value_type}:{value}")
                return self._create_empty_result(value, value_type)
            
            # Query all sources concurrently
            source_results = await self._query_all_sources(
                value, value_type, active_sources, detailed
            )
            
            # Calculate overall reputation
            overall_score, overall_verdict, categories = self._calculate_overall_reputation(source_results)
            
            # Get first/last seen from source data
            first_seen, last_seen = self._extract_seen_dates(source_results)
            
            # Build result
            result = ReputationResult(
                value=value,
                value_type=value_type,
                overall_score=overall_score,
                overall_verdict=overall_verdict,
                sources=list(source_results.values()),
                first_seen=first_seen,
                last_seen=last_seen,
                total_reports=sum(s.total_reports for s in source_results.values()),
                categories=categories
            )
            
            # Cache result
            await cache_set(
                cache_key,
                result.dict(),
                settings.CACHE_TTL_DEFAULT
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"Reputation query completed: {value_type}:{value} in {processing_time:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Reputation query error for {value_type}:{value}: {e}")
            return self._create_error_result(value, value_type, str(e))
    
    async def _query_all_sources(
        self,
        value: str,
        value_type: str,
        sources: Dict[str, Dict],
        detailed: bool
    ) -> Dict[str, ReputationSource]:
        """Query all reputation sources concurrently."""
        tasks = []
        
        for source_key, source_config in sources.items():
            tasks.append(self._query_single_source(source_key, source_config, value, value_type, detailed))
        
        # Execute all queries concurrently
        source_results = {}
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_key = list(sources.keys())[i]
                
                if isinstance(result, Exception):
                    logger.warning(f"Source {source_key} query failed: {result}")
                    # Create error source result
                    source_results[source_key] = ReputationSource(
                        name=sources[source_key]["name"],
                        score=None,
                        verdict="unknown",
                        confidence=0.0,
                        metadata={"error": str(result)}
                    )
                else:
                    source_results[source_key] = result
        
        return source_results
    
    async def _query_single_source(
        self,
        source_key: str,
        source_config: Dict,
        value: str,
        value_type: str,
        detailed: bool
    ) -> ReputationSource:
        """Query a single reputation source."""
        try:
            if source_key == "virustotal":
                return await self._query_virustotal(value, value_type, source_config, detailed)
            elif source_key == "abuseipdb":
                return await self._query_abuseipdb(value, source_config, detailed)
            elif source_key == "shodan":
                return await self._query_shodan(value, value_type, source_config, detailed)
            elif source_key == "greynoise":
                return await self._query_greynoise(value, source_config, detailed)
            elif source_key == "otx":
                return await self._query_otx(value, value_type, source_config, detailed)
            elif source_key == "securitytrails":
                return await self._query_securitytrails(value, value_type, source_config, detailed)
            else:
                raise ValueError(f"Unknown source: {source_key}")
                
        except Exception as e:
            logger.error(f"Source {source_key} query failed: {e}")
            raise
    
    async def _query_virustotal(
        self,
        value: str,
        value_type: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query VirusTotal reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("VirusTotal API key not configured")
            
            url = f"{source_config['url']}{value_type}/report"
            params = {
                "apikey": source_config["api_key"],
                "resource": value
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request,
                "GET",
                url,
                params
            )
            
            if response.get("response_code") == 1:  # Found
                positives = response.get("positives", 0)
                total = response.get("total", 0)
                
                score = (total - positives) / total if total > 0 else 1.0
                verdict = self._determine_verdict(score)
                
                metadata = {
                    "positives": positives,
                    "total": total,
                    "scan_date": response.get("scan_date"),
                    "permalink": response.get("permalink")
                }
                
                if detailed:
                    metadata["scans"] = response.get("scans", {})
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.9,
                    last_seen=datetime.utcnow(),
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,  # No detection = clean
                    verdict="clean",
                    confidence=0.5,
                    last_seen=datetime.utcnow(),
                    metadata={"message": "No results found"}
                )
                
        except Exception as e:
            raise Exception(f"VirusTotal query failed: {e}")
    
    async def _query_abuseipdb(
        self,
        value: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query AbuseIPDB reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("AbuseIPDB API key not configured")
            
            url = f"{source_config['url']}check"
            headers = {
                "Key": source_config["api_key"],
                "Accept": "application/json"
            }
            params = {"ipAddress": value, "maxAgeInDays": "90"}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers,
                params
            )
            
            if response.get("data"):
                data = response["data"]
                abuse_confidence_score = data.get("abuseConfidenceScore", 0)
                
                # Convert AbuseIPDB score to our scale (0-1)
                score = 1.0 - (abuse_confidence_score / 100.0)
                verdict = self._determine_verdict(score)
                
                metadata = {
                    "abuse_confidence_score": abuse_confidence_score,
                    "total_reports": data.get("totalReports", 0),
                    "last_reported": data.get("lastReportedAt"),
                    "is_public": data.get("isPublic", False)
                }
                
                if detailed:
                    metadata["usage_type"] = data.get("usageType")
                    metadata["isp"] = data.get("isp")
                    metadata["domain"] = data.get("domain")
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.8,
                    last_seen=data.get("lastReportedAt"),
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,
                    verdict="clean",
                    confidence=0.5,
                    metadata={"message": "No reports found"}
                )
                
        except Exception as e:
            raise Exception(f"AbuseIPDB query failed: {e}")
    
    async def _query_shodan(
        self,
        value: str,
        value_type: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query Shodan reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("Shodan API key not configured")
            
            if value_type == "ip":
                url = f"{source_config['url']}host/{value}"
                params = {"key": source_config["api_key"]}
            elif value_type == "domain":
                url = f"{source_config['url']}dns/lookup"
                params = {"key": source_config["api_key"], "hostname": value}
            else:
                raise ValueError(f"Shodan doesn't support {value_type}")
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request,
                "GET",
                url,
                params
            )
            
            if response:
                # Shodan doesn't provide reputation scores, so we infer from tags
                tags = response.get("tags", [])
                suspicious_tags = ["malware", "botnet", "scanner", "exploit"]
                is_suspicious = any(tag in tags for tag in suspicious_tags)
                
                score = 0.3 if is_suspicious else 0.8
                verdict = "suspicious" if is_suspicious else "clean"
                
                metadata = {
                    "tags": tags,
                    "ports": response.get("ports", [])[:10] if detailed else [],
                    "org": response.get("org"),
                    "isp": response.get("isp")
                }
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.7,
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,
                    verdict="clean",
                    confidence=0.5,
                    metadata={"message": "No data found"}
                )
                
        except Exception as e:
            raise Exception(f"Shodan query failed: {e}")
    
    async def _query_greynoise(
        self,
        value: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query GreyNoise reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("GreyNoise API key not configured")
            
            url = f"{source_config['url']}v3/community/{value}"
            headers = {"key": source_config["api_key"]}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers
            )
            
            if response:
                # GreyNoise provides classification
                classification = response.get("classification")
                
                if classification == "malicious":
                    score = 0.1
                    verdict = "malicious"
                elif classification == "suspicious":
                    score = 0.4
                    verdict = "suspicious"
                else:
                    score = 0.9
                    verdict = "clean"
                
                metadata = {
                    "classification": classification,
                    "seen": response.get("seen"),
                    "last_seen": response.get("last_seen")
                }
                
                if detailed:
                    metadata["tags"] = response.get("tags", [])
                    metadata["_raw_data"] = response
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.8,
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,
                    verdict="unknown",
                    confidence=0.3,
                    metadata={"message": "IP not classified"}
                )
                
        except Exception as e:
            raise Exception(f"GreyNoise query failed: {e}")
    
    async def _query_otx(
        self,
        value: str,
        value_type: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query AlienVault OTX reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("OTX API key not configured")
            
            url = f"{source_config['url']}indicators/{value_type}/{value}/general"
            headers = {"X-OTX-API-KEY": source_config["api_key"]}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers
            )
            
            if response and "pulse_info" in response:
                pulses = response["pulse_info"]["count"]
                
                # More pulses = more suspicious
                if pulses > 10:
                    score = 0.2
                    verdict = "malicious"
                elif pulses > 3:
                    score = 0.5
                    verdict = "suspicious"
                else:
                    score = 0.8
                    verdict = "clean"
                
                metadata = {
                    "pulse_count": pulses,
                    "sections": response.get("sections", [])
                }
                
                if detailed:
                    metadata["pulse_info"] = response["pulse_info"]
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.7,
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,
                    verdict="clean",
                    confidence=0.5,
                    metadata={"message": "No OTX data found"}
                )
                
        except Exception as e:
            raise Exception(f"OTX query failed: {e}")
    
    async def _query_securitytrails(
        self,
        value: str,
        value_type: str,
        source_config: Dict,
        detailed: bool
    ) -> ReputationSource:
        """Query SecurityTrails reputation."""
        try:
            if not source_config["api_key"]:
                raise ValueError("SecurityTrails API key not configured")
            
            headers = {"apikey": source_config["api_key"]}
            
            if value_type == "domain":
                url = f"{source_config['url']}domain/{value}/dns"
            elif value_type == "ip":
                url = f"{source_config['url']}ip/{value}/dns"
            else:
                raise ValueError(f"SecurityTrails doesn't support {value_type}")
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers
            )
            
            if response:
                # SecurityTrails doesn't provide direct reputation, 
                # but we can infer from historical data
                score = 0.7  # Default score
                verdict = "clean"
                
                metadata = {
                    "domain_age_days": response.get("domain_age", {}).get("days"),
                    "subdomain_count": len(response.get("subdomains", [])),
                    "mx_records": len(response.get("mx", []))
                }
                
                return ReputationSource(
                    name=source_config["name"],
                    score=score,
                    verdict=verdict,
                    confidence=0.6,
                    metadata=metadata
                )
            else:
                return ReputationSource(
                    name=source_config["name"],
                    score=1.0,
                    verdict="clean",
                    confidence=0.5,
                    metadata={"message": "No SecurityTrails data found"}
                )
                
        except Exception as e:
            raise Exception(f"SecurityTrails query failed: {e}")
    
    def _make_request(self, method: str, url: str, params: Dict = None) -> Dict:
        """Make HTTP request (synchronous)."""
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'CybersecAPI/1.0'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _make_request_with_headers(self, method: str, url: str, headers: Dict, params: Dict = None) -> Dict:
        """Make HTTP request with custom headers (synchronous)."""
        try:
            request_headers = {'User-Agent': 'CybersecAPI/1.0', **(headers or {})}
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _determine_verdict(self, score: float) -> str:
        """Determine verdict based on score."""
        if score >= 0.8:
            return "clean"
        elif score >= 0.6:
            return "mostly_clean"
        elif score >= 0.4:
            return "suspicious"
        elif score >= 0.2:
            return "likely_malicious"
        else:
            return "malicious"
    
    def _calculate_overall_reputation(
        self,
        source_results: Dict[str, ReputationSource]
    ) -> Tuple[float, str, List[str]]:
        """Calculate overall reputation score from multiple sources."""
        if not source_results:
            return 0.5, "unknown", []
        
        weighted_sum = 0.0
        total_weight = 0.0
        categories = set()
        total_reports = 0
        
        for source_key, source_result in source_results.items():
            source_config = self.sources.get(source_key, {})
            weight = source_config.get("weight", 0.1)
            
            if source_result.score is not None:
                weighted_sum += source_result.score * weight
                total_weight += weight
            
            # Collect categories and reports
            if source_result.metadata:
                if "tags" in source_result.metadata:
                    categories.update(source_result.metadata["tags"])
                if "classification" in source_result.metadata:
                    categories.add(source_result.metadata["classification"])
            
            total_reports += source_result.metadata.get("total_reports", 0)
        
        # Calculate weighted average
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = 0.5
        
        # Determine overall verdict
        overall_verdict = self._determine_verdict(overall_score)
        
        return overall_score, overall_verdict, list(categories)
    
    def _extract_seen_dates(self, source_results: Dict[str, ReputationSource]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract first and last seen dates from source results."""
        seen_dates = []
        
        for source_result in source_results.values():
            if source_result.last_seen:
                if isinstance(source_result.last_seen, str):
                    try:
                        # Parse various date formats
                        seen_dates.append(datetime.fromisoformat(source_result.last_seen.replace('Z', '+00:00')))
                    except ValueError:
                        try:
                            seen_dates.append(datetime.strptime(source_result.last_seen, "%Y-%m-%d"))
                        except ValueError:
                            continue
                else:
                    seen_dates.append(source_result.last_seen)
        
        if seen_dates:
            first_seen = min(seen_dates)
            last_seen = max(seen_dates)
            return first_seen, last_seen
        
        return None, None
    
    def _create_empty_result(self, value: str, value_type: str) -> ReputationResult:
        """Create empty reputation result."""
        return ReputationResult(
            value=value,
            value_type=value_type,
            overall_score=0.5,
            overall_verdict="unknown",
            sources=[],
            total_reports=0,
            categories=[]
        )
    
    def _create_error_result(self, value: str, value_type: str, error: str) -> ReputationResult:
        """Create error reputation result."""
        return ReputationResult(
            value=value,
            value_type=value_type,
            overall_score=0.0,
            overall_verdict="error",
            sources=[],
            total_reports=0,
            categories=[]
        )
    
    async def get_reputation_summary(
        self,
        value: str,
        value_type: str
    ) -> Dict[str, Any]:
        """Get a summary of reputation for a value."""
        try:
            # Check cache first
            cache_key = generate_cache_key("reputation_summary", f"{value_type}:{value}", "summary")
            cached_summary = await cache_get(cache_key)
            if cached_summary:
                return cached_summary
            
            # Get full reputation result
            result = await self.query_reputation(value, value_type, detailed=False)
            
            # Create summary
            summary = {
                "value": value,
                "value_type": value_type,
                "overall_verdict": result.overall_verdict,
                "overall_score": result.overall_score,
                "source_count": len(result.sources),
                "last_updated": datetime.utcnow().isoformat(),
                "key_findings": []
            }
            
            # Add key findings
            for source in result.sources:
                if source.score and source.score < 0.3:
                    summary["key_findings"].append(
                        f"{source.name}: {source.verdict} (confidence: {source.confidence:.2f})"
                    )
            
            # Cache summary for shorter time
            await cache_set(cache_key, summary, settings.CACHE_TTL_SHORT)
            
            return summary
            
        except Exception as e:
            logger.error(f"Reputation summary failed for {value_type}:{value}: {e}")
            return {
                "value": value,
                "value_type": value_type,
                "error": str(e),
                "overall_verdict": "unknown",
                "overall_score": 0.5
            }
    
    async def batch_reputation_query(
        self,
        values: List[Dict[str, Any]],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """Query reputation for multiple values concurrently."""
        try:
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def query_with_semaphore(value_data: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    try:
                        value = value_data["value"]
                        value_type = value_data["value_type"]
                        sources = value_data.get("sources")
                        
                        result = await self.query_reputation(value, value_type, sources)
                        
                        return {
                            "value": value,
                            "value_type": value_type,
                            "success": True,
                            "result": result.dict()
                        }
                    except Exception as e:
                        return {
                            "value": value_data.get("value", "unknown"),
                            "value_type": value_data.get("value_type", "unknown"),
                            "success": False,
                            "error": str(e)
                        }
            
            # Execute all queries
            tasks = [query_with_semaphore(value_data) for value_data in values]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append({
                        "success": False,
                        "error": str(result)
                    })
                else:
                    processed_results.append(result)
            
            logger.info(f"Batch reputation query completed: {len(processed_results)} items")
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch reputation query failed: {e}")
            return [{
                "success": False,
                "error": str(e)
            }]


# Global reputation service instance
reputation_service = ReputationService()
