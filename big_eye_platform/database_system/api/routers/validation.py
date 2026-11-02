"""Validation endpoints for the cybersecurity validation API."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
import logging
import time
from datetime import datetime

from ..models.schemas import (
    ValidationResponse, EmailValidationRequest, EmailValidationResult,
    DomainValidationRequest, DomainValidationResult,
    IPValidationRequest, IPValidationResult,
    URLValidationRequest, URLValidationResult,
    SenderValidationRequest, SenderValidationResult,
    BulkValidationRequest, BulkValidationResponse, ValidationResult
)
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.validation import validation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/validate", tags=["validation"])


@router.post(
    "/email",
    response_model=ValidationResponse,
    summary="Validate email address",
    description="Comprehensive email validation including syntax, domain, MX records, and reputation checks."
)
async def validate_email(
    request: EmailValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate email address with comprehensive checks."""
    start_time = time.time()
    
    try:
        logger.info(f"Email validation request: {request.email}")
        
        result = await validation_service.validate_email(
            email=request.email,
            verify_syntax=request.verify_syntax,
            verify_mx_record=request.verify_mx_record,
            check_disposable=request.check_disposable
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_usage(
            current_key.key_id,
            "/validate/email",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            request.email
        )
        
        return ValidationResponse(
            success=True,
            message="Email validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Email validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_validation_usage(
            current_key.key_id,
            "/validate/email",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            request.email
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email validation failed: {str(e)}"
        )


@router.post(
    "/domain",
    response_model=ValidationResponse,
    summary="Validate domain name",
    description="Comprehensive domain validation including format, DNS resolution, and reputation checks."
)
async def validate_domain(
    request: DomainValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate domain name."""
    start_time = time.time()
    
    try:
        logger.info(f"Domain validation request: {request.domain}")
        
        result = await validation_service.validate_domain(
            domain=request.domain,
            check_dns=request.check_dns,
            check_whois=request.check_whois,
            check_reputation=request.check_reputation
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_usage(
            current_key.key_id,
            "/validate/domain",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            request.domain
        )
        
        return ValidationResponse(
            success=True,
            message="Domain validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Domain validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_validation_usage(
            current_key.key_id,
            "/validate/domain",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            request.domain
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain validation failed: {str(e)}"
        )


@router.post(
    "/ip",
    response_model=ValidationResponse,
    summary="Validate IP address",
    description="Comprehensive IP validation including format, geolocation, and reputation checks."
)
async def validate_ip(
    request: IPValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate IP address."""
    start_time = time.time()
    
    try:
        logger.info(f"IP validation request: {request.ip_address}")
        
        result = await validation_service.validate_ip(
            ip_address=request.ip_address,
            check_reputation=request.check_reputation,
            check_geolocation=request.check_geolocation
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_usage(
            current_key.key_id,
            "/validate/ip",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            request.ip_address
        )
        
        return ValidationResponse(
            success=True,
            message="IP validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"IP validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_validation_usage(
            current_key.key_id,
            "/validate/ip",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            request.ip_address
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IP validation failed: {str(e)}"
        )


@router.post(
    "/url",
    response_model=ValidationResponse,
    summary="Validate URL",
    description="Comprehensive URL validation including format, accessibility, and safety checks."
)
async def validate_url(
    request: URLValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate URL."""
    start_time = time.time()
    
    try:
        logger.info(f"URL validation request: {request.url}")
        
        result = await validation_service.validate_url(
            url=request.url,
            check_safety=request.check_safety,
            check_reputation=request.check_reputation,
            follow_redirects=request.follow_redirects
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_usage(
            current_key.key_id,
            "/validate/url",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            request.url
        )
        
        return ValidationResponse(
            success=True,
            message="URL validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_validation_usage(
            current_key.key_id,
            "/validate/url",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            request.url
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL validation failed: {str(e)}"
        )


@router.post(
    "/sender",
    response_model=ValidationResponse,
    summary="Validate email sender",
    description="Validate email sender with SPF, DKIM, and DMARC authentication checks."
)
async def validate_sender(
    request: SenderValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate email sender with SPF, DKIM, DMARC checks."""
    start_time = time.time()
    
    try:
        logger.info(f"Sender validation request: {request.email}@{request.domain}")
        
        result = await validation_service.validate_sender(
            email=request.email,
            domain=request.domain,
            check_spf=request.check_spf,
            check_dkim=request.check_dkim,
            check_dmarc=request.check_dmarc
        )
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_usage(
            current_key.key_id,
            "/validate/sender",
            True,
            processing_time,
            request.dict(),
            result.dict(),
            f"{request.email}@{request.domain}"
        )
        
        return ValidationResponse(
            success=True,
            message="Sender validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Sender validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        await log_validation_usage(
            current_key.key_id,
            "/validate/sender",
            False,
            processing_time,
            request.dict(),
            {"error": str(e)},
            f"{request.email}@{request.domain}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sender validation failed: {str(e)}"
        )


@router.post(
    "/bulk",
    response_model=BulkValidationResponse,
    summary="Bulk validation",
    description="Perform bulk validation of multiple items (emails, domains, IPs, URLs, senders)."
)
async def validate_bulk(
    request: BulkValidationRequest,
    background_tasks: BackgroundTasks,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Perform bulk validation."""
    start_time = time.time()
    
    try:
        # Count total items
        total_items = 0
        if request.emails:
            total_items += len(request.emails)
        if request.domains:
            total_items += len(request.domains)
        if request.ip_addresses:
            total_items += len(request.ip_addresses)
        if request.urls:
            total_items += len(request.urls)
        if request.senders:
            total_items += len(request.senders)
        
        # Check maximum limit
        if total_items > 1000:  # From settings
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum 1000 items allowed per bulk request, got {total_items}"
            )
        
        logger.info(f"Bulk validation request: {total_items} items")
        
        # Perform validation
        results = await validation_service.validate_bulk(
            emails=request.emails,
            domains=request.domains,
            ip_addresses=request.ip_addresses,
            urls=request.urls,
            senders=request.senders
        )
        
        # Count valid/invalid
        valid_items = sum(1 for result in results if result.is_valid)
        invalid_items = len(results) - valid_items
        
        processing_time = (time.time() - start_time) * 1000
        
        # Log usage in background
        background_tasks.add_task(
            log_bulk_validation_usage,
            current_key.key_id,
            "/validate/bulk",
            True,
            processing_time,
            request.dict(),
            results
        )
        
        return BulkValidationResponse(
            success=True,
            message="Bulk validation completed",
            total_items=total_items,
            valid_items=valid_items,
            invalid_items=invalid_items,
            results=results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Bulk validation error: {e}")
        processing_time = (time.time() - start_time) * 1000
        
        # Log error
        background_tasks.add_task(
            log_bulk_validation_usage,
            current_key.key_id,
            "/validate/bulk",
            False,
            processing_time,
            request.dict(),
            []
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk validation failed: {str(e)}"
        )


@router.get(
    "/health",
    summary="Validation service health check",
    description="Check the health of validation services."
)
async def validation_health_check(current_key: APIKeyInfo = Depends(get_current_api_key)):
    """Check validation service health."""
    try:
        from ..database.connections import check_postgresql_health, check_mongodb_health
        from ..cache.redis_cache import check_redis_health
        
        # Check all service health
        postgresql_health = await check_postgresql_health()
        mongodb_health = await check_mongodb_health()
        redis_health = await check_redis_health()
        
        overall_healthy = all(
            health["status"] == "healthy" 
            for health in [postgresql_health, mongodb_health, redis_health]
        )
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "services": {
                "postgresql": postgresql_health,
                "mongodb": mongodb_health,
                "redis": redis_health
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


async def log_validation_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    response_data: dict,
    value: str
):
    """Log validation usage to database."""
    try:
        from ..middleware.auth import log_api_usage
        
        await log_api_usage(
            api_key=api_key,
            endpoint=endpoint,
            success=success,
            processing_time_ms=processing_time_ms,
            request_data={
                **request_data,
                "validated_value": value
            },
            response_data=response_data
        )
        
    except Exception as e:
        logger.warning(f"Failed to log validation usage: {e}")


async def log_bulk_validation_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    results: List[ValidationResult]
):
    """Log bulk validation usage."""
    try:
        from ..middleware.auth import log_api_usage
        
        # Create summary of results
        summary = {
            "total_items": len(results),
            "valid_items": sum(1 for r in results if r.is_valid),
            "avg_confidence": sum(r.confidence_score for r in results) / len(results) if results else 0,
            "threats_detected": sum(len(r.threats) for r in results)
        }
        
        await log_api_usage(
            api_key=api_key,
            endpoint=endpoint,
            success=success,
            processing_time_ms=processing_time_ms,
            request_data=request_data,
            response_data={
                "summary": summary,
                "sample_results": [r.dict() for r in results[:5]] if results else []
            }
        )
        
    except Exception as e:
        logger.warning(f"Failed to log bulk validation usage: {e}")