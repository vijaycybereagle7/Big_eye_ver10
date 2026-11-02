"""Threat intelligence endpoints for querying and analyzing threat data."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging
import time
from datetime import datetime

from ..models.schemas import (
    ThreatIntelligenceResponse, ThreatQueryRequest, ThreatIntelligenceResult,
    PaginatedResponse, SearchRequest
)
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.threat_intelligence import threat_intelligence_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threats", tags=["threat-intelligence"])


@router.post(
    "/query",
    response_model=ThreatIntelligenceResponse,
    summary="Query threat intelligence",
    description="Query comprehensive threat intelligence for IP, domain, URL, or hash indicators."
)
async def query_threat_intelligence(
    request: ThreatQueryRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Query threat intelligence for an indicator."""
    start_time = time.time()
    
    try:
        logger.info(
            f"Threat intelligence query: {request.query_type}:{request.value}"
        )
        
        # Validate query type
        if request.query_type not in ["ip", "domain", "url", "hash"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported query type: {request.query_type}"
            )
        
        # Validate time range
        if request.time_range_days < 1 or request.time_range_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range must be between 1 and 365 days"
            )
        
        result = await threat_intelligence_service.query_threat_intelligence(
            indicator=request.value,
            indicator_type=request.query_type,
            include_context=request.include_context,
            include_related=request.include_related,
            time_range_days=request.time_range_days
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/query",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            f"{request.query_type}:{request.value}"
        )
        
        return ThreatIntelligenceResponse(
            success=True,
            message="Threat intelligence query completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Threat intelligence query error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/query",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            f"{request.query_type}:{request.value}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat intelligence query failed: {str(e)}"
        )


@router.get(
    "/{query_type}/{value}",
    response_model=ThreatIntelligenceResponse,
    summary="Get threat intelligence by indicator",
    description="Get threat intelligence using GET request."
)
async def get_threat_intelligence(
    query_type: str,
    value: str,
    include_context: bool = True,
    include_related: bool = True,
    time_range_days: int = 30,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get threat intelligence using GET request."""
    start_time = time.time()
    
    try:
        logger.info(f"Threat intelligence GET: {query_type}:{value}")
        
        result = await threat_intelligence_service.query_threat_intelligence(
            indicator=value,
            indicator_type=query_type,
            include_context=include_context,
            include_related=include_related,
            time_range_days=time_range_days
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_threat_intel_usage(
            current_key.key_id,
            f"/threats/{query_type}/{value}",
            True,
            processing_time,
            {
                "query_type": query_type,
                "value": value,
                "include_context": include_context,
                "include_related": include_related,
                "time_range_days": time_range_days
            },
            result.dict(),
            f"{query_type}:{value}"
        )
        
        return ThreatIntelligenceResponse(
            success=True,
            message="Threat intelligence query completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Threat intelligence GET error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_threat_intel_usage(
            current_key.key_id,
            f"/threats/{query_type}/{value}",
            False,
            processing_time,
            {
                "query_type": query_type,
                "value": value,
                "include_context": include_context,
                "include_related": include_related,
                "time_range_days": time_range_days
            },
            {"error": str(e)},
            f"{query_type}:{value}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat intelligence query failed: {str(e)}"
        )


@router.post(
    "/search",
    response_model=dict,
    summary="Search threat indicators",
    description="Search for threat indicators matching query criteria."
)
async def search_threat_indicators(
    request: SearchRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Search for threat indicators."""
    start_time = time.time()
    
    try:
        logger.info(f"Threat indicator search: {request.query}")
        
        # Validate pagination
        if request.page < 1 or request.page > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be between 1 and 1000"
            )
        
        if request.page_size < 1 or request.page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page size must be between 1 and 100"
            )
        
        # Perform search
        results = await threat_intelligence_service.search_threat_indicators(
            query=request.query,
            indicator_types=request.filters.get("indicator_types") if request.filters else None,
            time_range_days=request.filters.get("time_range_days", 30) if request.filters else 30,
            min_confidence=request.filters.get("min_confidence", 0.0) if request.filters else 0.0
        )
        
        # Apply pagination
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        paginated_results = results[start_idx:end_idx]
        
        total_pages = (len(results) + request.page_size - 1) // request.page_size
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/search",
            True,
            processing_time,
            request.dict(),
            {
                "results_count": len(paginated_results),
                "total_count": len(results),
                "page": request.page,
                "page_size": request.page_size,
                "total_pages": total_pages
            },
            f"search:{request.query}"
        )
        
        return {
            "success": True,
            "message": "Threat indicator search completed",
            "results": [intel.dict() for intel in paginated_results],
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": len(results),
                "pages": total_pages
            },
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Threat indicator search error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/search",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            f"search:{request.query}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat indicator search failed: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=dict,
    summary="Get threat intelligence statistics",
    description="Get statistics and trends for threat intelligence data."
)
async def get_threat_statistics(
    time_range_days: int = 30,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get threat intelligence statistics."""
    start_time = time.time()
    
    try:
        logger.info(f"Threat statistics request: {time_range_days} days")
        
        # Validate time range
        if time_range_days < 1 or time_range_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range must be between 1 and 365 days"
            )
        
        # Get statistics
        statistics = await threat_intelligence_service.get_threat_statistics(time_range_days)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/statistics",
            True,
            processing_time,
            {"time_range_days": time_range_days},
            statistics,
            f"stats:{time_range_days}days"
        )
        
        return {
            "success": True,
            "message": "Threat intelligence statistics retrieved",
            "statistics": statistics,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Threat statistics error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/statistics",
            False,
            processing_time,
            {"time_range_days": time_range_days},
            {"error": str(e)},
            f"stats:{time_range_days}days"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat statistics query failed: {str(e)}"
        )


@router.get(
    "/categories",
    response_model=dict,
    summary="Get threat categories",
    description="Get list of available threat categories and their descriptions."
)
async def get_threat_categories(current_key: APIKeyInfo = Depends(get_current_api_key)):
    """Get threat categories."""
    try:
        categories = {
            "malware": {
                "name": "Malware",
                "description": "Malicious software including trojans, viruses, worms, ransomware, and spyware",
                "subcategories": [
                    "trojan", "virus", "worm", "ransomware", "spyware", 
                    "adware", "rootkit", "keylogger", "backdoor"
                ]
            },
            "phishing": {
                "name": "Phishing",
                "description": "Fraudulent attempts to obtain sensitive information",
                "subcategories": [
                    "phishing", "fraud", "social_engineering", "credential_harvesting"
                ]
            },
            "botnet": {
                "name": "Botnet",
                "description": "Network of compromised computers controlled by attackers",
                "subcategories": [
                    "botnet", "c2", "command_control", "zombie", "bot"
                ]
            },
            "spam": {
                "name": "Spam",
                "description": "Unsolicited and unwanted communications",
                "subcategories": [
                    "spam", "spamhaus", "blacklist", "bulk_mail"
                ]
            },
            "exploit": {
                "name": "Exploitation",
                "description": "Exploitation of vulnerabilities and security weaknesses",
                "subcategories": [
                    "exploit", "vulnerability", "cve", "zero_day", "payload"
                ]
            },
            "scanning": {
                "name": "Reconnaissance",
                "description": "Information gathering and scanning activities",
                "subcategories": [
                    "port_scan", "reconnaissance", "scanner", "enumeration"
                ]
            },
            "ddos": {
                "name": "DDoS",
                "description": "Distributed Denial of Service attacks",
                "subcategories": [
                    "ddos", "dos", "amplification", "reflection"
                ]
            },
            "threat_actor": {
                "name": "Threat Actor",
                "description": "Attribution to specific threat groups and campaigns",
                "subcategories": [
                    "apt", "threat_group", "campaign", "attribution"
                ]
            }
        }
        
        return {
            "success": True,
            "message": "Threat categories retrieved",
            "categories": categories,
            "total_categories": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get(
    "/sources",
    response_model=dict,
    summary="Get threat intelligence sources",
    description="Get information about threat intelligence sources and their data feeds."
)
async def get_threat_intelligence_sources(current_key: APIKeyInfo = Depends(get_current_api_key)):
    """Get threat intelligence sources."""
    try:
        sources = {
            "local_db": {
                "name": "Local Database",
                "description": "Internal threat intelligence database",
                "data_types": ["ip", "domain", "url", "hash"],
                "confidence_weight": 0.8,
                "realtime": True
            },
            "virustotal": {
                "name": "VirusTotal",
                "description": "Multi-engine antivirus and URL/file analysis",
                "data_types": ["ip", "domain", "url", "hash"],
                "confidence_weight": 0.9,
                "realtime": True
            },
            "abuseipdb": {
                "name": "AbuseIPDB",
                "description": "IP abuse reports and reputation database",
                "data_types": ["ip"],
                "confidence_weight": 0.8,
                "realtime": True
            },
            "greynoise": {
                "name": "GreyNoise",
                "description": "IP reputation and threat classification",
                "data_types": ["ip"],
                "confidence_weight": 0.8,
                "realtime": True
            },
            "otx": {
                "name": "AlienVault OTX",
                "description": "Open Threat Exchange with community threat intelligence",
                "data_types": ["ip", "domain", "url", "hash"],
                "confidence_weight": 0.7,
                "realtime": True
            },
            "internal_logs": {
                "name": "Internal Logs",
                "description": "Analysis of internal security logs and events",
                "data_types": ["ip", "domain", "url", "email"],
                "confidence_weight": 0.6,
                "realtime": True
            }
        }
        
        # Count available sources
        available_sources = sum(1 for source in sources.values() if source.get("realtime", False))
        
        return {
            "success": True,
            "message": "Threat intelligence sources retrieved",
            "sources": sources,
            "total_sources": len(sources),
            "available_sources": available_sources
        }
        
    except Exception as e:
        logger.error(f"Failed to get threat intelligence sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sources: {str(e)}"
        )


@router.post(
    "/analyze",
    response_model=dict,
    summary="Analyze threat patterns",
    description="Analyze patterns and trends in threat intelligence data."
)
async def analyze_threat_patterns(
    request: dict,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Analyze threat patterns and trends."""
    start_time = time.time()
    
    try:
        # Extract analysis parameters
        time_range_days = request.get("time_range_days", 30)
        indicators = request.get("indicators", [])
        analysis_type = request.get("analysis_type", "trends")
        
        # Validate parameters
        if time_range_days < 1 or time_range_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range must be between 1 and 365 days"
            )
        
        if len(indicators) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 indicators allowed for analysis"
            )
        
        logger.info(f"Threat pattern analysis: {analysis_type} for {len(indicators)} indicators")
        
        # Mock analysis results (in real implementation, would perform actual analysis)
        analysis_results = {
            "analysis_type": analysis_type,
            "time_range_days": time_range_days,
            "indicators_analyzed": len(indicators),
            "threat_trends": {
                "increasing_threats": ["phishing", "malware"],
                "decreasing_threats": ["spam"],
                "stable_threats": ["ddos"]
            },
            "geographical_distribution": {
                "top_countries": ["US", "RU", "CN"],
                "threat_density": "medium"
            },
            "temporal_patterns": {
                "peak_hours": ["09:00-11:00", "14:00-16:00"],
                "peak_days": ["Monday", "Tuesday"]
            },
            "confidence_score": 0.75,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/analyze",
            True,
            processing_time,
            request,
            analysis_results,
            f"analyze:{analysis_type}:{len(indicators)}items"
        )
        
        return {
            "success": True,
            "message": "Threat pattern analysis completed",
            "analysis": analysis_results,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Threat pattern analysis error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_threat_intel_usage(
            current_key.key_id,
            "/threats/analyze",
            False,
            processing_time,
            request,
            {"error": str(e)},
            f"analyze:error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat pattern analysis failed: {str(e)}"
        )


async def log_threat_intel_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    response_data: dict,
    value: str
):
    """Log threat intelligence usage."""
    try:
        from ..middleware.auth import log_api_usage
        
        await log_api_usage(
            api_key=api_key,
            endpoint=endpoint,
            success=success,
            processing_time_ms=processing_time_ms,
            request_data={
                **request_data,
                "query_value": value
            },
            response_data=response_data
        )
        
    except Exception as e:
        logger.warning(f"Failed to log threat intel usage: {e}")