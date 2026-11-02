"""Simplified validation endpoints for Vercel serverless deployment."""

import time
import logging
from typing import List, Union
from fastapi import APIRouter, Depends, HTTPException, status

from ..models.schemas import (
    ValidationResponse, EmailValidationRequest, EmailValidationResult,
    DomainValidationRequest, DomainValidationResult,
    IPValidationRequest, IPValidationResult,
    URLValidationRequest, URLValidationResult,
    BulkValidationRequest
)
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.validation import validation_service
from ..database.supabase import log_validation_request

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
        
        result_data = await validation_service.validate_email(
            email=request.email,
            verify_syntax=request.verify_syntax,
            verify_mx_record=request.verify_mx_record,
            check_disposable=request.check_disposable
        )
        
        # Create result object
        result = EmailValidationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_request(
            endpoint="/validate/email",
            value=request.email,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ValidationResponse(
            success=True,
            message="Email validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Email validation error: {e}")
        
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
        
        result_data = await validation_service.validate_domain(request.domain)
        
        # Create result object
        result = DomainValidationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_request(
            endpoint="/validate/domain",
            value=request.domain,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ValidationResponse(
            success=True,
            message="Domain validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Domain validation error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Domain validation failed: {str(e)}"
        )


@router.post(
    "/ip",
    response_model=ValidationResponse,
    summary="Validate IP address",
    description="Comprehensive IP address validation including format, type, and reputation checks."
)
async def validate_ip(
    request: IPValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate IP address."""
    start_time = time.time()
    
    try:
        logger.info(f"IP validation request: {request.ip}")
        
        result_data = await validation_service.validate_ip(request.ip)
        
        # Create result object
        result = IPValidationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_request(
            endpoint="/validate/ip",
            value=request.ip,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ValidationResponse(
            success=True,
            message="IP validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"IP validation error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IP validation failed: {str(e)}"
        )


@router.post(
    "/url",
    response_model=ValidationResponse,
    summary="Validate URL",
    description="Comprehensive URL validation including format, domain, and threat indicators."
)
async def validate_url(
    request: URLValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Validate URL."""
    start_time = time.time()
    
    try:
        logger.info(f"URL validation request: {request.url}")
        
        result_data = await validation_service.validate_url(request.url)
        
        # Create result object
        result = URLValidationResult(**result_data)
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_request(
            endpoint="/validate/url",
            value=request.url,
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ValidationResponse(
            success=True,
            message="URL validation completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"URL validation failed: {str(e)}"
        )


@router.post(
    "/bulk",
    summary="Bulk validation",
    description="Validate multiple items of the same type in a single request."
)
async def validate_bulk(
    request: BulkValidationRequest,
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Bulk validation for multiple items."""
    start_time = time.time()
    
    try:
        logger.info(f"Bulk validation request: {len(request.items)} items of type {request.validation_type}")
        
        results = []
        
        for item in request.items:
            try:
                if request.validation_type == "email":
                    result_data = await validation_service.validate_email(str(item))
                elif request.validation_type == "domain":
                    result_data = await validation_service.validate_domain(str(item))
                elif request.validation_type == "ip":
                    result_data = await validation_service.validate_ip(str(item))
                elif request.validation_type == "url":
                    result_data = await validation_service.validate_url(str(item))
                else:
                    raise ValueError(f"Unsupported validation type: {request.validation_type}")
                
                results.append(result_data)
                
            except Exception as e:
                logger.warning(f"Failed to validate item {item}: {e}")
                results.append({
                    "value": str(item),
                    "is_valid": False,
                    "score": 0.0,
                    "confidence": "low",
                    "checks": {"error": str(e)}
                })
        
        # Log usage
        processing_time = (time.time() - start_time) * 1000
        await log_validation_request(
            endpoint="/validate/bulk",
            value=f"{len(request.items)} {request.validation_type} items",
            success=True,
            processing_time_ms=processing_time,
            api_key=current_key.key
        )
        
        return ValidationResponse(
            success=True,
            message=f"Bulk validation completed for {len(results)} items",
            result=results
        )
        
    except Exception as e:
        logger.error(f"Bulk validation error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk validation failed: {str(e)}"
        )
