"""Simplified threat intelligence endpoints for Vercel serverless deployment."""

import time
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query

from ..models.schemas import ReputationResponse, ReputationResult
from ..middleware.auth import get_current_api_key, APIKeyInfo
from ..services.reputation import reputation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/threats", tags=["threat-intelligence"])


@router.get(
    "/search",
    response_model=List[ReputationResult],
    summary="Search threat intelligence",
    description="Search for threats across IP, domain, URL, hash, or email."
)
async def search_threats(
    query: str = Query(..., description="Search query"),
    type: str = Query(..., description="Type to search (ip, domain, url, hash, email)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return"),
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Search threat intelligence for a specific value."""
    try:
        logger.info(f"Threat search request: {type}:{query}")
        
        # Validate type
        if type not in ["ip", "domain", "url", "hash", "email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported search type: {type}"
            )
        
        # Query reputation service
        result_data = await reputation_service.query_reputation(
            value=query,
            value_type=type,
            sources=None,
            detailed=False
        )
        
        # Return single result as list
        return [ReputationResult(**result_data)]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Threat search error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Threat search failed: {str(e)}"
        )


@router.get(
    "/recent",
    response_model=List[Dict[str, Any]],
    summary="Get recent threats",
    description="Get recently detected threats (simplified for serverless)."
)
async def get_recent_threats(
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get recently detected threats (mock data for serverless)."""
    try:
        logger.info(f"Recent threats request: limit={limit}")
        
        # Return mock data for serverless deployment
        # In a full implementation, this would query Supabase for recent threats
        mock_threats = [
            {
                "value": "192.168.1.100",
                "value_type": "ip",
                "threat_level": "medium",
                "indicators": ["port_scan_detected"],
                "last_seen": "2025-10-30T10:00:00Z",
                "source": "internal_detection"
            },
            {
                "value": "suspicious-domain.com",
                "value_type": "domain",
                "threat_level": "high",
                "indicators":["phishing_campaign", "malware_distribution"],
                "last_seen": "2025-10-30T09:45:00Z",
                "source": "threat_feed"
            }
        ]
        
        return mock_threats[:limit]
        
    except Exception as e:
        logger.error(f"Recent threats error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent threats: {str(e)}"
        )


@router.get(
    "/stats",
    summary="Get threat intelligence statistics",
    description="Get statistics about threat intelligence data."
)
async def get_threat_stats(
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get threat intelligence statistics."""
    try:
        logger.info("Threat stats request")
        
        # Return mock statistics for serverless
        # In a full implementation, this would aggregate data from Supabase
        return {
            "total_threats": 15420,
            "threats_last_24h": 145,
            "threats_last_hour": 12,
            "top_threat_types": {
                "malicious_ip": 45,
                "phishing_domain": 38,
                "malware_url": 29,
                "suspicious_hash": 15
            },
            "threat_levels": {
                "critical": 156,
                "high": 423,
                "medium": 1089,
                "low": 3792
            },
            "data_sources": {
                "virustotal": "active",
                "abuseipdb": "active",
                "local_feeds": "active",
                "user_reports": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Threat stats error: {e}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get threat statistics: {str(e)}"
        )


@router.get(
    "/types",
    summary="Get supported threat types",
    description="Get list of supported threat types for searching."
)
async def get_threat_types(
    current_key: APIKeyInfo = Depends(get_current_api_key)
):
    """Get supported threat types."""
    return {
        "supported_types": [
            {
                "type": "ip",
                "description": "IP address reputation and threat analysis",
                "examples": ["192.168.1.1", "8.8.8.8"]
            },
            {
                "type": "domain",
                "description": "Domain reputation and threat analysis",
                "examples": ["google.com", "malware-example.com"]
            },
            {
                "type": "url",
                "description": "URL reputation and threat analysis",
                "examples": ["https://google.com", "http://malware-site.com/payload.exe"]
            },
            {
                "type": "hash",
                "description": "File hash reputation (MD5, SHA1, SHA256)",
                "examples": ["d41d8cd98f00b204e9800998ecf8427e", "da39a3ee5e6b4b0d3255bfef95601890afd80709"]
            },
            {
                "type": "email",
                "description": "Email address reputation and analysis",
                "examples": ["user@example.com", "spam@suspicious-domain.com"]
            }
        ],
        "threat_levels": ["low", "medium", "high", "critical"],
        "data_sources": ["virustotal", "abuseipdb", "local_feeds"]
    }
