"""Threat intelligence service for aggregating and analyzing threat data."""

import json
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor

from ..config.settings import settings
from ..cache.redis_cache import cached, cache_get, cache_set, generate_cache_key
from ..database.connections import get_mongodb_collection, get_postgresql_session
from ..models.schemas import ThreatIntelligenceResult, ThreatIntel, ThreatContext

logger = logging.getLogger(__name__)


class ThreatIntelligenceService:
    """Service for threat intelligence analysis and aggregation."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Threat categories mapping
        self.threat_categories = {
            "malware": ["trojan", "virus", "worm", "ransomware", "spyware"],
            "phishing": ["phishing", "fraud", "social_engineering"],
            "botnet": ["botnet", "c2", "command_control"],
            "spam": ["spam", "spamhaus", "blacklist"],
            "exploit": ["exploit", "vulnerability", "cve"],
            "scanning": ["port_scan", "reconnaissance", "scanner"],
            "ddos": ["ddos", "dos", "amplification"],
            "threat_actor": ["apt", "threat_group", "campaign"]
        }
        
        # Severity mapping
        self.severity_mapping = {
            "low": {"min_score": 0.0, "max_score": 0.3},
            "medium": {"min_score": 0.3, "max_score": 0.6},
            "high": {"min_score": 0.6, "max_score": 0.8},
            "critical": {"min_score": 0.8, "max_score": 1.0}
        }
        
        # Related indicators patterns
        self.related_patterns = {
            "ip": {
                "domains": [],  # Would be populated from DNS records
                "urls": [],     # Would be populated from logs
                "hashes": []    # Would be populated from malware analysis
            },
            "domain": {
                "ips": [],
                "urls": [],
                "hashes": [],
                "emails": []
            },
            "url": {
                "domains": [],
                "ips": [],
                "hashes": []
            },
            "hash": {
                "domains": [],
                "urls": [],
                "ips": []
            }
        }
    
    async def query_threat_intelligence(
        self,
        indicator: str,
        indicator_type: str,
        include_context: bool = True,
        include_related: bool = True,
        time_range_days: int = 30
    ) -> ThreatIntelligenceResult:
        """Query threat intelligence for an indicator."""
        start_time = datetime.utcnow()
        
        try:
            # Validate indicator type
            if indicator_type not in ["ip", "domain", "url", "hash"]:
                raise ValueError(f"Unsupported indicator type: {indicator_type}")
            
            # Check cache first
            cache_key = generate_cache_key(
                "threat_intel", 
                f"{indicator_type}:{indicator}", 
                f"context:{include_context}:related:{include_related}:range:{time_range_days}"
            )
            cached_result = await cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for threat intelligence: {indicator_type}:{indicator}")
                return ThreatIntelligenceResult(**cached_result)
            
            # Query multiple threat intelligence sources
            intelligence_data = await self._aggregate_threat_intelligence(
                indicator, indicator_type, time_range_days
            )
            
            # Process intelligence data
            processed_intel = self._process_intelligence_data(intelligence_data, indicator, indicator_type)
            
            # Get context information
            context = None
            if include_context:
                context = await self._get_threat_context(indicator, indicator_type)
            
            # Get related indicators
            related_indicators = []
            if include_related:
                related_indicators = await self._get_related_indicators(indicator, indicator_type)
            
            # Calculate overall confidence and risk level
            confidence_score = self._calculate_confidence_score(processed_intel)
            risk_level = self._determine_risk_level(processed_intel)
            
            # Build result
            result = ThreatIntelligenceResult(
                indicator=indicator,
                indicator_type=indicator_type,
                intelligence=processed_intel,
                context=context,
                related_indicators=related_indicators,
                confidence_score=confidence_score,
                risk_level=risk_level
            )
            
            # Cache result
            await cache_set(
                cache_key,
                result.dict(),
                settings.CACHE_TTL_DEFAULT
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(
                f"Threat intelligence query completed: {indicator_type}:{indicator} "
                f"in {processing_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Threat intelligence query error for {indicator_type}:{indicator}: {e}")
            return self._create_error_result(indicator, indicator_type, str(e))
    
    async def _aggregate_threat_intelligence(
        self,
        indicator: str,
        indicator_type: str,
        time_range_days: int
    ) -> List[Dict[str, Any]]:
        """Aggregate threat intelligence from multiple sources."""
        intelligence_sources = []
        
        # Check local database first
        local_intel = await self._get_local_threat_intel(indicator, indicator_type, time_range_days)
        intelligence_sources.extend(local_intel)
        
        # Query external threat intelligence APIs
        external_intel = await self._query_external_threat_sources(indicator, indicator_type)
        intelligence_sources.extend(external_intel)
        
        # Query internal logs and reports
        log_intel = await self._analyze_internal_logs(indicator, indicator_type, time_range_days)
        intelligence_sources.extend(log_intel)
        
        return intelligence_sources
    
    async def _get_local_threat_intel(
        self,
        indicator: str,
        indicator_type: str,
        time_range_days: int
    ) -> List[Dict[str, Any]]:
        """Get threat intelligence from local database."""
        try:
            # Query MongoDB for stored threat intelligence
            collection = get_mongodb_collection("threat_intelligence")
            
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            
            cursor = collection.find({
                "indicator": indicator,
                "indicator_type": indicator_type,
                "last_seen": {"$gte": cutoff_date}
            }).sort("last_seen", -1)
            
            intel_list = []
            async for doc in cursor:
                intel_list.append({
                    "source": doc.get("source", "local_db"),
                    "threat_data": doc.get("threat_data", {}),
                    "confidence": doc.get("confidence", 0.5),
                    "first_seen": doc.get("first_seen"),
                    "last_seen": doc.get("last_seen")
                })
            
            logger.debug(f"Found {len(intel_list)} local threat intelligence records")
            return intel_list
            
        except Exception as e:
            logger.warning(f"Failed to query local threat intelligence: {e}")
            return []
    
    async def _query_external_threat_sources(
        self,
        indicator: str,
        indicator_type: str
    ) -> List[Dict[str, Any]]:
        """Query external threat intelligence sources."""
        external_intel = []
        
        # VirusTotal integration
        if settings.VIRUSTOTAL_API_KEY:
            try:
                vt_intel = await self._query_virustotal_threats(indicator, indicator_type)
                external_intel.extend(vt_intel)
            except Exception as e:
                logger.warning(f"VirusTotal threat query failed: {e}")
        
        # AbuseIPDB integration
        if settings.ABUSEIPDB_API_KEY and indicator_type == "ip":
            try:
                abuse_intel = await self._query_abuseipdb_threats(indicator)
                external_intel.extend(abuse_intel)
            except Exception as e:
                logger.warning(f"AbuseIPDB threat query failed: {e}")
        
        # GreyNoise integration
        if settings.GREYNOISE_API_KEY and indicator_type == "ip":
            try:
                gn_intel = await self._query_greynoise_threats(indicator)
                external_intel.extend(gn_intel)
            except Exception as e:
                logger.warning(f"GreyNoise threat query failed: {e}")
        
        # OTX integration
        if settings.OTX_API_KEY:
            try:
                otx_intel = await self._query_otx_threats(indicator, indicator_type)
                external_intel.extend(otx_intel)
            except Exception as e:
                logger.warning(f"OTX threat query failed: {e}")
        
        return external_intel
    
    async def _query_virustotal_threats(
        self,
        indicator: str,
        indicator_type: str
    ) -> List[Dict[str, Any]]:
        """Query VirusTotal for threat intelligence."""
        try:
            url = f"https://www.virustotal.com/vtapi/v2/{indicator_type}/report"
            params = {
                "apikey": settings.VIRUSTOTAL_API_KEY,
                "resource": indicator
            }
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request,
                "GET",
                url,
                params
            )
            
            if response.get("response_code") == 1:
                intel_data = {
                    "source": "virustotal",
                    "threat_data": {
                        "positives": response.get("positives", 0),
                        "total": response.get("total", 0),
                        "scan_date": response.get("scan_date"),
                        "scan_results": response.get("scans", {})
                    },
                    "confidence": 0.9,
                    "last_seen": datetime.utcnow()
                }
                
                # Extract threat types from scan results
                threat_types = self._extract_threat_types_from_virustotal(response.get("scans", {}))
                if threat_types:
                    intel_data["threat_data"]["threat_types"] = threat_types
                
                return [intel_data]
            
            return []
            
        except Exception as e:
            logger.warning(f"VirusTotal threat intelligence query failed: {e}")
            return []
    
    async def _query_abuseipdb_threats(self, indicator: str) -> List[Dict[str, Any]]:
        """Query AbuseIPDB for threat intelligence."""
        try:
            url = f"https://api.abuseipdb.com/api/v2/check"
            headers = {
                "Key": settings.ABUSEIPDB_API_KEY,
                "Accept": "application/json"
            }
            params = {"ipAddress": indicator, "maxAgeInDays": "90"}
            
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
                
                intel_data = {
                    "source": "abuseipdb",
                    "threat_data": {
                        "abuse_confidence_score": abuse_confidence_score,
                        "total_reports": data.get("totalReports", 0),
                        "last_reported": data.get("lastReportedAt"),
                        "categories": data.get("categories", [])
                    },
                    "confidence": 0.8,
                    "last_seen": data.get("lastReportedAt") or datetime.utcnow()
                }
                
                return [intel_data]
            
            return []
            
        except Exception as e:
            logger.warning(f"AbuseIPDB threat intelligence query failed: {e}")
            return []
    
    async def _query_greynoise_threats(self, indicator: str) -> List[Dict[str, Any]]:
        """Query GreyNoise for threat intelligence."""
        try:
            url = f"https://api.greynoise.io/v3/v3/community/{indicator}"
            headers = {"key": settings.GREYNOISE_API_KEY}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers
            )
            
            if response:
                classification = response.get("classification")
                
                intel_data = {
                    "source": "greynoise",
                    "threat_data": {
                        "classification": classification,
                        "seen": response.get("seen"),
                        "last_seen": response.get("last_seen"),
                        "tags": response.get("tags", [])
                    },
                    "confidence": 0.8,
                    "last_seen": response.get("last_seen") or datetime.utcnow()
                }
                
                return [intel_data]
            
            return []
            
        except Exception as e:
            logger.warning(f"GreyNoise threat intelligence query failed: {e}")
            return []
    
    async def _query_otx_threats(
        self,
        indicator: str,
        indicator_type: str
    ) -> List[Dict[str, Any]]:
        """Query OTX for threat intelligence."""
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{indicator}/general"
            headers = {"X-OTX-API-KEY": settings.OTX_API_KEY}
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._make_request_with_headers,
                "GET",
                url,
                headers
            )
            
            if response and "pulse_info" in response:
                pulse_count = response["pulse_info"]["count"]
                
                intel_data = {
                    "source": "otx",
                    "threat_data": {
                        "pulse_count": pulse_count,
                        "pulse_info": response["pulse_info"],
                        "sections": response.get("sections", []),
                        "tags": [tag.get("name") for tag in response.get("tags", [])]
                    },
                    "confidence": 0.7,
                    "last_seen": datetime.utcnow()
                }
                
                return [intel_data]
            
            return []
            
        except Exception as e:
            logger.warning(f"OTX threat intelligence query failed: {e}")
            return []
    
    async def _analyze_internal_logs(
        self,
        indicator: str,
        indicator_type: str,
        time_range_days: int
    ) -> List[Dict[str, Any]]:
        """Analyze internal logs for threat intelligence."""
        try:
            # Query validation logs for patterns
            collection = get_mongodb_collection("validation_logs")
            
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            
            # Query for logs containing this indicator
            cursor = collection.find({
                "timestamp": {"$gte": cutoff_date},
                "$or": [
                    {"request_data.value": indicator},
                    {"response_data.result.value": indicator}
                ]
            }).sort("timestamp", -1).limit(100)
            
            log_intel = []
            async for doc in cursor:
                # Analyze request patterns
                request_data = doc.get("request_data", {})
                response_data = doc.get("response_data", {})
                
                # Look for threat indicators in responses
                result = response_data.get("result", {})
                threats = result.get("threats", [])
                confidence_score = result.get("confidence_score", 0.5)
                
                if threats or confidence_score < 0.3:
                    log_intel.append({
                        "source": "internal_logs",
                        "threat_data": {
                            "threats": threats,
                            "confidence_score": confidence_score,
                            "endpoint": doc.get("endpoint"),
                            "success": doc.get("success"),
                            "processing_time": doc.get("processing_time_ms")
                        },
                        "confidence": 0.6,
                        "last_seen": doc.get("timestamp")
                    })
            
            logger.debug(f"Analyzed {len(log_intel)} threat patterns from internal logs")
            return log_intel
            
        except Exception as e:
            logger.warning(f"Internal log analysis failed: {e}")
            return []
    
    def _process_intelligence_data(
        self,
        intelligence_data: List[Dict[str, Any]],
        indicator: str,
        indicator_type: str
    ) -> List[ThreatIntel]:
        """Process raw intelligence data into standardized format."""
        processed_intel = []
        
        for intel_data in intelligence_data:
            try:
                source = intel_data["source"]
                threat_data = intel_data["threat_data"]
                confidence = intel_data.get("confidence", 0.5)
                first_seen = intel_data.get("first_seen")
                last_seen = intel_data.get("last_seen")
                
                # Extract threat types
                threat_types = self._extract_threat_types(source, threat_data)
                
                # Generate description
                description = self._generate_threat_description(source, threat_data)
                
                # Extract tags
                tags = self._extract_threat_tags(source, threat_data)
                
                # Extract references
                references = self._extract_references(source, threat_data)
                
                # Extract malware families
                malware_families = self._extract_malware_families(source, threat_data)
                
                # Determine severity based on confidence and threat data
                severity = self._determine_threat_severity(confidence, threat_data, threat_types)
                
                threat_intel = ThreatIntel(
                    indicator=indicator,
                    indicator_type=indicator_type,
                    threat_types=threat_types,
                    confidence=confidence,
                    severity=severity,
                    description=description,
                    first_seen=first_seen,
                    last_seen=last_seen,
                    tags=tags,
                    references=references,
                    malware_families=malware_families,
                    attribution=self._extract_attribution(source, threat_data)
                )
                
                processed_intel.append(threat_intel)
                
            except Exception as e:
                logger.warning(f"Failed to process intelligence data: {e}")
        
        return processed_intel
    
    def _extract_threat_types(self, source: str, threat_data: Dict[str, Any]) -> List[str]:
        """Extract threat types from threat data."""
        threat_types = []
        
        try:
            if source == "virustotal":
                # Extract from scan results
                scans = threat_data.get("scan_results", {})
                for vendor, result in scans.items():
                    if result.get("detected"):
                        threat_types.append(result.get("result", "malware"))
            
            elif source == "abuseipdb":
                # Extract from categories
                categories = threat_data.get("categories", [])
                threat_types.extend([f"abuse_{cat}" for cat in categories])
            
            elif source == "greynoise":
                # Extract from classification and tags
                classification = threat_data.get("classification")
                if classification and classification != "unknown":
                    threat_types.append(f"greynoise_{classification}")
                threat_types.extend(threat_data.get("tags", []))
            
            elif source == "otx":
                # Extract from pulses
                threat_types.extend(threat_data.get("tags", []))
            
            elif source == "internal_logs":
                # Extract from threats field
                threats = threat_data.get("threats", [])
                threat_types.extend(threats)
            
            # Normalize threat types
            normalized_types = []
            for threat_type in threat_types:
                if threat_type:
                    normalized_type = threat_type.lower().replace(" ", "_")
                    normalized_types.append(normalized_type)
            
            return list(set(normalized_types))  # Remove duplicates
            
        except Exception as e:
            logger.warning(f"Failed to extract threat types: {e}")
            return []
    
    def _generate_threat_description(self, source: str, threat_data: Dict[str, Any]) -> str:
        """Generate human-readable threat description."""
        try:
            if source == "virustotal":
                positives = threat_data.get("positives", 0)
                total = threat_data.get("total", 0)
                if positives > 0:
                    return f"Detected by {positives}/{total} antivirus engines on VirusTotal"
                else:
                    return "Clean according to VirusTotal"
            
            elif source == "abuseipdb":
                confidence = threat_data.get("abuse_confidence_score", 0)
                reports = threat_data.get("total_reports", 0)
                if confidence > 50:
                    return f"High confidence ({confidence}%) abuse reports ({reports} total)"
                elif confidence > 20:
                    return f"Moderate confidence ({confidence}%) abuse reports ({reports} total)"
                else:
                    return f"Low confidence ({confidence}%) abuse reports ({reports} total)"
            
            elif source == "greynoise":
                classification = threat_data.get("classification", "unknown")
                return f"Classified as {classification} by GreyNoise"
            
            elif source == "otx":
                pulse_count = threat_data.get("pulse_count", 0)
                if pulse_count > 0:
                    return f"Associated with {pulse_count} threat intelligence pulses on OTX"
                else:
                    return "No threat intelligence pulses found on OTX"
            
            elif source == "internal_logs":
                threats = threat_data.get("threats", [])
                if threats:
                    return f"Flagged for threats: {', '.join(threats)}"
                else:
                    return "No threats detected in internal analysis"
            
            else:
                return f"Threat data from {source}"
                
        except Exception as e:
            logger.warning(f"Failed to generate threat description: {e}")
            return f"Threat intelligence from {source}"
    
    def _extract_threat_tags(self, source: str, threat_data: Dict[str, Any]) -> List[str]:
        """Extract tags from threat data."""
        try:
            if source == "greynoise":
                return threat_data.get("tags", [])
            elif source == "otx":
                return threat_data.get("tags", [])
            elif source == "abuseipdb":
                return [f"abuse_cat_{cat}" for cat in threat_data.get("categories", [])]
            else:
                return []
        except Exception:
            return []
    
    def _extract_references(self, source: str, threat_data: Dict[str, Any]) -> List[str]:
        """Extract references from threat data."""
        try:
            references = []
            
            if source == "virustotal":
                permalink = threat_data.get("permalink")
                if permalink:
                    references.append(permalink)
            
            # Add source-specific references
            references.append(f"{source}:{threat_data.get('id', 'unknown')}")
            
            return references
        except Exception:
            return []
    
    def _extract_malware_families(self, source: str, threat_data: Dict[str, Any]) -> List[str]:
        """Extract malware family names from threat data."""
        try:
            families = []
            
            if source == "virustotal":
                # Extract from scan results
                scans = threat_data.get("scan_results", {})
                for vendor, result in scans.items():
                    if result.get("detected") and result.get("result"):
                        # Try to extract family name from detection result
                        result_str = result.get("result", "")
                        if result_str:
                            families.append(result_str)
            
            return list(set(families))  # Remove duplicates
        except Exception:
            return []
    
    def _extract_attribution(self, source: str, threat_data: Dict[str, Any]) -> Optional[str]:
        """Extract threat actor attribution."""
        try:
            # This would require more sophisticated parsing
            # For now, return None
            return None
        except Exception:
            return None
    
    def _determine_threat_severity(
        self,
        confidence: float,
        threat_data: Dict[str, Any],
        threat_types: List[str]
    ) -> str:
        """Determine threat severity based on various factors."""
        try:
            # Base severity on confidence
            if confidence >= 0.8:
                base_severity = "high"
            elif confidence >= 0.6:
                base_severity = "medium"
            elif confidence >= 0.3:
                base_severity = "low"
            else:
                base_severity = "low"
            
            # Adjust based on threat types
            critical_threats = ["malware", "ransomware", "apt", "botnet"]
            high_threats = ["trojan", "phishing", "exploit"]
            
            for threat_type in threat_types:
                if any(critical in threat_type for critical in critical_threats):
                    return "critical"
                elif any(high in threat_type for high in high_threats):
                    if base_severity in ["low", "medium"]:
                        return "high"
            
            return base_severity
            
        except Exception:
            return "low"
    
    async def _get_threat_context(
        self,
        indicator: str,
        indicator_type: str
    ) -> Optional[ThreatContext]:
        """Get additional context about the threat."""
        try:
            context_data = {}
            
            # Geographical context (for IP addresses)
            if indicator_type == "ip":
                context_data["geographical_data"] = await self._get_ip_geolocation(indicator)
            
            # Network context
            context_data["network_data"] = await self._get_network_context(indicator, indicator_type)
            
            # Behavioral context
            context_data["behavioral_data"] = await self._get_behavioral_context(indicator, indicator_type)
            
            # Historical context
            context_data["historical_data"] = await self._get_historical_context(indicator, indicator_type)
            
            # Only return context if we have meaningful data
            if any(context_data.values()):
                return ThreatContext(**context_data)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get threat context: {e}")
            return None
    
    async def _get_ip_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Get IP geolocation data."""
        try:
            # This would integrate with IP geolocation API
            return {"country": "Unknown", "city": "Unknown", "coordinates": None}
        except Exception:
            return {}
    
    async def _get_network_context(self, indicator: str, indicator_type: str) -> Dict[str, Any]:
        """Get network-related context."""
        try:
            # This would query network databases
            return {"asn": "Unknown", "organization": "Unknown"}
        except Exception:
            return {}
    
    async def _get_behavioral_context(self, indicator: str, indicator_type: str) -> Dict[str, Any]:
        """Get behavioral context."""
        try:
            # This would analyze behavior patterns
            return {"activity_level": "unknown", "last_activity": None}
        except Exception:
            return {}
    
    async def _get_historical_context(self, indicator: str, indicator_type: str) -> Dict[str, Any]:
        """Get historical context."""
        try:
            # This would query historical data
            return {"first_seen": None, "last_seen": None, "activity_frequency": "unknown"}
        except Exception:
            return {}
    
    async def _get_related_indicators(
        self,
        indicator: str,
        indicator_type: str
    ) -> List[str]:
        """Get related indicators."""
        try:
            # This would query relationship databases
            return []
        except Exception:
            return []
    
    def _calculate_confidence_score(self, intelligence: List[ThreatIntel]) -> float:
        """Calculate overall confidence score."""
        if not intelligence:
            return 0.5
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for intel in intelligence:
            # Weight by confidence and recency
            weight = intel.confidence
            
            # Adjust weight based on source reliability
            if "virustotal" in intel.tags or "internal_logs" in intel.tags:
                weight *= 1.0
            else:
                weight *= 0.8
            
            weighted_sum += intel.confidence * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _determine_risk_level(self, intelligence: List[ThreatIntel]) -> str:
        """Determine overall risk level."""
        if not intelligence:
            return "unknown"
        
        # Count threats by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        
        for intel in intelligence:
            severity_counts[intel.severity] = severity_counts.get(intel.severity, 0) + 1
        
        # Determine risk level based on highest severity threats
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] > 2:
            return "high"
        elif severity_counts["high"] > 0:
            return "medium"
        elif severity_counts["medium"] > 0:
            return "low"
        else:
            return "minimal"
    
    def _extract_threat_types_from_virustotal(self, scans: Dict[str, Any]) -> List[str]:
        """Extract threat types from VirusTotal scan results."""
        threat_types = []
        
        try:
            for vendor, result in scans.items():
                if result.get("detected") and result.get("result"):
                    threat_types.append(result.get("result"))
        except Exception as e:
            logger.warning(f"Failed to extract threat types from VirusTotal: {e}")
        
        return threat_types
    
    def _make_request(self, method: str, url: str, params: Dict = None) -> Dict:
        """Make HTTP request (synchronous)."""
        try:
            import requests
            response = requests.request(
                method=method,
                url=url,
                params=params,
                timeout=30,
                headers={'User-Agent': 'CybersecAPI/1.0'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _make_request_with_headers(self, method: str, url: str, headers: Dict, params: Dict = None) -> Dict:
        """Make HTTP request with custom headers (synchronous)."""
        try:
            import requests
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
        except Exception as e:
            raise Exception(f"HTTP request failed: {e}")
    
    def _create_error_result(self, indicator: str, indicator_type: str, error: str) -> ThreatIntelligenceResult:
        """Create error result."""
        return ThreatIntelligenceResult(
            indicator=indicator,
            indicator_type=indicator_type,
            intelligence=[],
            confidence_score=0.0,
            risk_level="unknown"
        )
    
    async def search_threat_indicators(
        self,
        query: str,
        indicator_types: Optional[List[str]] = None,
        time_range_days: int = 30,
        min_confidence: float = 0.0
    ) -> List[ThreatIntel]:
        """Search for threat indicators matching query."""
        try:
            # This would implement full-text search across threat intelligence
            return []
        except Exception as e:
            logger.error(f"Threat search failed: {e}")
            return []
    
    async def get_threat_statistics(
        self,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get threat statistics and trends."""
        try:
            # Query local database for statistics
            collection = get_mongodb_collection("threat_intelligence")
            
            cutoff_date = datetime.utcnow() - timedelta(days=time_range_days)
            
            # Aggregate statistics
            pipeline = [
                {"$match": {"last_seen": {"$gte": cutoff_date}}},
                {
                    "$group": {
                        "_id": "$indicator_type",
                        "count": {"$sum": 1},
                        "avg_confidence": {"$avg": "$confidence"},
                        "unique_indicators": {"$addToSet": "$indicator"}
                    }
                },
                {
                    "$project": {
                        "indicator_type": "$_id",
                        "count": 1,
                        "avg_confidence": 1,
                        "unique_indicators": {"$size": "$unique_indicators"}
                    }
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            results = await cursor.to_list(length=None)
            
            # Process results
            statistics = {
                "time_range_days": time_range_days,
                "total_indicators": sum(r["count"] for r in results),
                "by_type": {r["indicator_type"]: {
                    "count": r["count"],
                    "unique_indicators": r["unique_indicators"],
                    "avg_confidence": r["avg_confidence"]
                } for r in results},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get threat statistics: {e}")
            return {}


# Global threat intelligence service instance
threat_intelligence_service = ThreatIntelligenceService()
