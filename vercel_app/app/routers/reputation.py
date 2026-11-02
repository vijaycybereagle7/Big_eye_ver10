"""Simplified reputation endpoints for Vercel serverless deployment."""

import time
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models.schemas import (
    ReputationResponse, ReputationQueryRequest, ReputationResult
)
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.reputation import reputation_service
from ..database.supabase import log_reputation_query

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
        
        result_data = await reputation_service.query_reputation(
            value=request.value,
            value_type=request.value_type,
            sources=None,  # Simplified for serverless
            detailed=False  # Simplified for serverless
        )
        
        # Create result object
        result = ReputationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_reputation_query(
            endpoint="/reputation/query",
            value=request.value,
            value_type=request.value_type,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ReputationResponse(
            success=True,
            message="Reputation query completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Reputation query error: {e}")
        
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
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get reputation for a specific value using GET request."""
    start_time = time.time()
    
    try:
        logger.info(f"Reputation GET request: {value_type}:{value}")
        
        # Validate value type
        if value_type not in ["ip", "domain", "url", "hash", "email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported value type: {value_type}"
            )
        
        result_data = await reputation_service.query_reputation(
            value=value,
            value_type=value_type,
            sources=None,
            detailed=False
        )
        
        # Create result object
        result = ReputationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_reputation_query(
            endpoint=f"/reputation/{value_type}/{value}",
            value=value,
            value_type=value_type,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ReputationResponse(
            success=True,
            message="Reputation query completed",
            result=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reputation GET error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reputation query failed: {str(e)}"
        )


@router.get(
    "/ip/{ip}",
    response_model=ReputationResponse,
    summary="Get IP reputation",
    description="Get reputation information for an IP address."
)
async def get_ip_reputation(
    ip: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get IP reputation."""
    return await get_reputation("ip", ip)


@router.get(
    "/domain/{domain}",
    response_model=ReputationResponse,
    summary="Get domain reputation",
    description="Get reputation information for a domain."
)
async def get_domain_reputation(
    domain: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get domain reputation."""
    return await get_reputation("domain", domain)


@router.get(
    "/url/{url}",
    response_model=ReputationResponse,
    summary="Get URL reputation",
    description="Get reputation information for a URL."
)
async def get_url_reputation(
    url: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get URL reputation."""
    return await get_reputation("url", url)


@router.get(
    "/email/{email}",
    response_model=ReputationResponse,
    summary="Get email reputation",
    description="Get reputation information for an email address."
)
async def get_email_reputation(
    email: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get email reputation."""
    return await get_reputation("email", email)


@router.get(
    "/hash/{hash_value}",
    response_model=ReputationResponse,
    summary="Get hash reputation",
    description="Get reputation information for a file hash (MD5, SHA1, SHA256)."
)
async def get_hash_reputation(
    hash_value: str,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get hash reputation."""
    return await get_reputation("hash", hash_value)
