"""Simplified authentication middleware for Vercel deployment."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config.settings import settings
from ..models.schemas import APIKeyInfo
import logging

logger = logging.getLogger(__name__)

# Simple bearer token authentication
security = HTTPBearer(auto_error=False)


def verify_api_key(api_key: str) -> APIKeyInfo:
    """Verify API key and return key info."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check against configured API keys
    for key_id, key_info in settings.VALID_API_KEYS.items():
        if key_info["key"] == api_key:
            return APIKeyInfo(
                key_id=key_id,
                key=api_key,
                name=key_info["name"],
                admin=key_info.get("admin", False)
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> APIKeyInfo:
    """Get current API key from bearer token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return verify_api_key(credentials.credentials)


class AuthManager:
    """Simple authentication manager."""
    
    def __init__(self):
        """Initialize auth manager."""
        self.api_keys = settings.VALID_API_KEYS
    
    def verify_key(self, api_key: str) -> Optional[APIKeyInfo]:
        """Verify API key."""
        try:
            return verify_api_key(api_key)
        except HTTPException:
            return None
    
    def is_admin_key(self, api_key: str) -> bool:
        """Check if API key has admin privileges."""
        key_info = self.verify_key(api_key)
        return key_info.admin if key_info else False
    
    def get_key_info(self, api_key: str) -> Optional[APIKeyInfo]:
        """Get API key information."""
        return self.verify_key(api_key)


# Global auth manager instance
auth_manager = AuthManager()
