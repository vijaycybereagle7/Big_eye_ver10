"""Reputation endpoints for querying threat intelligence and reputation data."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging
import time
from datetime import datetime

from ..models.schemas import (
    ReputationResponse, ReputationQueryRequest, ReputationResult,
    PaginatedResponse, SearchRequest
)
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.reputation import reputation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reputation", tags=["reputation"])


@router.post(
    "/query",
    response_model=ReputationResponse,
    summary="Query reputation for value",
    description="Query reputation from multiple threat intelligence sources for IP, domain, URL, hash, or email."
)
async def query_reputation(
    request: ReputationQueryRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Query reputation for a specific value."""
    start_time = time.time()
    
    try:
        logger.info(f"Reputation query request: {request.value_type}:{request.value}")
        
        # Validate value type
        if request.value_type not in ["ip", "domain", "url", "hash", "email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported value type: {request.value_type}"
            )
        
        result = await reputation_service.query_reputation(
            value=request.value,
            value_type=request.value_type,
            sources=request.sources,
            detailed=request.detailed
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_reputation_usage(
            current_key.key_id,
            "/reputation/query",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            f"{request.value_type}:{request.value}"
        )
        
        return ReputationResponse(
            success=True,
            message="Reputation query completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Reputation query error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_reputation_usage(
            current_key.key_id,
            "/reputation/query",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            f"{request.value_type}:{request.value}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation query failed: {str(e)}"
        )


@router.get(
    "/{value_type}/{value}",
    response_model=ReputationResponse,
    summary="Get reputation by value",
    description="Get reputation for a specific value using GET request."
)
async def get_reputation(
    value_type: str,
    value: str,
    sources: Optional[str] = None,
    detailed: bool = False,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get reputation using GET request."""
    start_time = time.time()
    
    try:
        # Parse sources parameter
        sources_list = sources.split(",") if sources else None
        
        logger.info(f"Reputation GET request: {value_type}:{value}")
        
        result = await reputation_service.query_reputation(
            value=value,
            value_type=value_type,
            sources=sources_list,
            detailed=detailed
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_reputation_usage(
            current_key.key_id,
            f"/reputation/{value_type}/{value}",
            True,
            processing_time,
            {"value_type": value_type, "value": value, "sources": sources_list, "detailed": detailed},
            result.dict(),
            f"{value_type}:{value}"
        )
        
        return ReputationResponse(
            success=True,
            message="Reputation query completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Reputation GET error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_reputation_usage(
            current_key.key_id,
            f"/reputation/{value_type}/{value}",
            False,
            processing_time,
            {"value_type": value_type, "value": value, "sources": sources_list, "detailed": detailed},
            {"error": str(e)},
            f"{value_type}:{value}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation query failed: {str(e)}"
        )


@router.post(
    "/batch",
    response_model=List[dict],
    summary="Batch reputation queries",
    description="Query reputation for multiple values concurrently."
)
async def batch_reputation_query(
    values: List[dict],
    max_concurrent: int = 10,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Batch query reputation for multiple values."""
    start_time = time.time()
    
    try:
        # Validate request
        if len(values) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 100 items allowed per batch request"
            )
        
        logger.info(f"Batch reputation query: {len(values)} items")
        
        # Validate each value
        validated_values = []
        for i, value_data in enumerate(values):
            if not isinstance(value_data, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i}: Must be a dictionary with 'value' and 'value_type' fields"
                )
            
            value = value_data.get("value")
            value_type = value_data.get("value_type")
            
            if not value or not value_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i}: Both 'value' and 'value_type' are required"
                )
            
            if value_type not in ["ip", "domain", "url", "hash", "email"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item {i}: Unsupported value type: {value_type}"
                )
            
            validated_values.append(value_data)
        
        # Perform batch query
        results = await reputation_service.batch_reputation_query(
            values=validated_values,
            max_concurrent=max_concurrent
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage
        await log_batch_reputation_usage(
            current_key.key_id,
            "/reputation/batch",
            True,
            processing_time,
            {"values": values, "max_concurrent": max_concurrent},
            {"results_count": len(results)},
            f"batch:{len(values)}items"
        )
        
        return {
            "success": True,
            "message": "Batch reputation query completed",
            "total_items": len(results),
            "successful_items": sum(1 for r in results if r.get("success", False)),
            "failed_items": sum(1 for r in results if not r.get("success", False)),
            "processing_time_ms": processing_time,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Batch reputation query error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_batch_reputation_usage(
            current_key.key_id,
            "/reputation/batch",
            False,
            processing_time,
            {"values": values, "max_concurrent": max_concurrent},
            {"error": str(e)},
            "batch:error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch reputation query failed: {str(e)}"
        )


@router.get(
    "/summary/{value_type}/{value}",
    response_model=dict,
    summary="Get reputation summary",
    description="Get a simplified reputation summary for quick analysis."
)
async def get_reputation_summary(
    value_type: str,
    value: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get reputation summary."""
    start_time = time.time()
    
    try:
        logger.info(f"Reputation summary request: {value_type}:{value}")
        
        summary = await reputation_service.get_reputation_summary(value, value_type)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage
        await log_reputation_usage(
            current_key.key_id,
            f"/reputation/summary/{value_type}/{value}",
            True,
            processing_time,
            {"value_type": value_type, "value": value},
            summary,
            f"{value_type}:{value}"
        )
        
        return {
            "success": True,
            "message": "Reputation summary retrieved",
            "summary": summary,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Reputation summary error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        await log_reputation_usage(
            current_key.key_id,
            f"/reputation/summary/{value_type}/{value}",
            False,
            processing_time,
            {"value_type": value_type, "value": value},
            {"error": str(e)},
            f"{value_type}:{value}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation summary failed: {str(e)}"
        )


@router.get(
    "/sources",
    response_model=dict,
    summary="Get available reputation sources",
    description="Get list of available reputation sources and their capabilities."
)
async def get_reputation_sources(current_key: APIKeyInfo = Depends(get_current_api_key)):
    """Get available reputation sources."""
    try:
        sources_info = {}
        
        # Define source information
        source_definitions = {
            "virustotal": {
                "name": "VirusTotal",
                "description": "Multi-engine antivirus and URL/file analysis",
                "supported_types": ["ip", "domain", "url", "hash"],
                "weight": 0.25,
                "api_configured": bool(reputation_service.sources["virustotal"]["api_key"])
            },
            "abuseipdb": {
                "name": "AbuseIPDB",
                "description": "IP abuse reports and reputation database",
                "supported_types": ["ip"],
                "weight": 0.20,
                "api_configured": bool(reputation_service.sources["abuseipdb"]["api_key"])
            },
            "shodan": {
                "name": "Shodan",
                "description": "Internet-connected device search engine",
                "supported_types": ["ip", "domain"],
                "weight": 0.15,
                "api_configured": bool(reputation_service.sources["shodan"]["api_key"])
            },
            "greynoise": {
                "name": "GreyNoise",
                "description": "IP reputation and threat classification",
                "supported_types": ["ip"],
                "weight": 0.20,
                "api_configured": bool(reputation_service.sources["greynoise"]["api_key"])
            },
            "otx": {
                "name": "AlienVault OTX",
                "description": "Open Threat Exchange with community threat intelligence",
                "supported_types": ["ip", "domain", "url", "hash"],
                "weight": 0.10,
                "api_configured": bool(reputation_service.sources["otx"]["api_key"])
            },
            "securitytrails": {
                "name": "SecurityTrails",
                "description": "DNS, domain and IP intelligence platform",
                "supported_types": ["ip", "domain"],
                "weight": 0.10,
                "api_configured": bool(reputation_service.sources["securitytrails"]["api_key"])
            }
        }
        
        # Filter available sources
        available_sources = {
            key: info for key, info in source_definitions.items()
            if info["api_configured"]
        }
        
        return {
            "success": True,
            "message": "Reputation sources retrieved",
            "sources": {
                "available": available_sources,
                "total_available": len(available_sources),
                "total_configured": len(source_definitions)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get reputation sources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sources: {str(e)}"
        )


@router.get(
    "/statistics",
    response_model=dict,
    summary="Get reputation statistics",
    description="Get usage statistics and performance metrics for reputation queries."
)
async def get_reputation_statistics(current_key: APIKeyInfo = Depends(get_current_api_key)):
    """Get reputation query statistics."""
    try:
        # Get cache statistics
        from ..cache.redis_cache import get_cache_stats
        
        cache_stats = await get_cache_stats()
        
        # Mock statistics (in real implementation, query database)
        statistics = {
            "cache_performance": cache_stats,
            "query_counts": {
                "total_queries": 0,
                "successful_queries": 0,
                "failed_queries": 0,
                "cache_hits": 0,
                "cache_misses": 0
            },
            "popular_values": {
                "ips": [],
                "domains": [],
                "urls": [],
                "hashes": []
            },
            "source_performance": {
                "virustotal": {"success_rate": 0.95, "avg_response_time": 1200},
                "abuseipdb": {"success_rate": 0.98, "avg_response_time": 500},
                "shodan": {"success_rate": 0.92, "avg_response_time": 800},
                "greynoise": {"success_rate": 0.96, "avg_response_time": 400},
                "otx": {"success_rate": 0.94, "avg_response_time": 600},
                "securitytrails": {"success_rate": 0.90, "avg_response_time": 1000}
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "message": "Reputation statistics retrieved",
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"Failed to get reputation statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


async def log_reputation_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    response_data: dict,
    value: str
):
    """Log reputation query usage."""
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
        logger.warning(f"Failed to log reputation usage: {e}")


async def log_batch_reputation_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    response_data: dict,
    batch_info: str
):
    """Log batch reputation query usage."""
    try:
        from ..middleware.auth import log_api_usage
        
        await log_api_usage(
            api_key=api_key,
            endpoint=endpoint,
            success=success,
            processing_time_ms=processing_time_ms,
            request_data=request_data,
            response_data={
                **response_data,
                "batch_info": batch_info
            }
        )
        
    except Exception as e:
        logger.warning(f"Failed to log batch reputation usage: {e}")