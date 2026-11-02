"""Authentication and authorization middleware."""

import re
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import json

from ..config.settings import settings
from ..database.connections import get_postgresql_session
from ..models.database import APIKeyDB
from ..cache.redis_cache import get_redis_client, cache_increment, cache_get

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Custom authorization error."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class APIKeyInfo:
    """API key information container."""
    
    def __init__(
        self, 
        key_id: str, 
        name: str, 
        is_admin: bool = False,
        rate_limit: int = 100,
        is_active: bool = True
    ):
        self.key_id = key_id
        self.name = name
        self.is_admin = is_admin
        self.rate_limit = rate_limit
        self.is_active = is_active


class AuthManager:
    """Authentication and authorization manager."""
    
    def __init__(self):
        self.valid_api_keys: Dict[str, APIKeyInfo] = {}
        self.admin_api_keys: Set[str] = set()
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from configuration and database."""
        try:
            # Load from configuration
            for key_id, key_info in settings.VALID_API_KEYS.items():
                api_key = key_info["key"]
                self.valid_api_keys[api_key] = APIKeyInfo(
                    key_id=key_id,
                    name=key_info["name"],
                    is_admin=key_info.get("admin", False),
                    rate_limit=settings.RATE_LIMIT_ADMIN_REQUESTS if key_info.get("admin") else settings.RATE_LIMIT_REQUESTS
                )
                
                if key_info.get("admin"):
                    self.admin_api_keys.add(api_key)
            
            # Load from database
            try:
                with get_postgresql_session() as session:
                    db_keys = session.query(APIKeyDB).filter(
                        APIKeyDB.is_active == True
                    ).all()
                    
                    for db_key in db_keys:
                        self.valid_api_keys[db_key.api_key] = APIKeyInfo(
                            key_id=db_key.key_id,
                            name=db_key.name,
                            is_admin=db_key.is_admin,
                            rate_limit=db_key.rate_limit,
                            is_active=db_key.is_active
                        )
                        
                        if db_key.is_admin:
                            self.admin_api_keys.add(db_key.api_key)
            
            except Exception as e:
                logger.warning(f"Failed to load API keys from database: {e}")
            
            logger.info(f"Loaded {len(self.valid_api_keys)} API keys ({len(self.admin_api_keys)} admin)")
            
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
    
    def authenticate_request(
        self, 
        request: Request, 
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> APIKeyInfo:
        """Authenticate API request."""
        
        # Try to get API key from Authorization header
        api_key = None
        
        if credentials and credentials.scheme == "Bearer":
            api_key = credentials.credentials
        
        # Try to get API key from X-API-Key header
        if not api_key:
            api_key = request.headers.get("X-API-Key")
        
        # Try to get API key from query parameter (not recommended for production)
        if not api_key and hasattr(request, "_query_params"):
            api_key = request.query_params.get("api_key")
        
        if not api_key:
            raise AuthenticationError("API key is required")
        
        # Validate API key
        if api_key not in self.valid_api_keys:
            logger.warning(f"Invalid API key used: {api_key[:8]}...")
            raise AuthenticationError("Invalid API key")
        
        key_info = self.valid_api_keys[api_key]
        
        # Check if key is active
        if not key_info.is_active:
            raise AuthenticationError("API key is inactive")
        
        return key_info
    
    def authorize_admin_request(self, key_info: APIKeyInfo):
        """Authorize admin-only request."""
        if not key_info.is_admin:
            raise AuthorizationError("Admin privileges required")
    
    def authorize_endpoint(self, key_info: APIKeyInfo, endpoint: str) -> bool:
        """Authorize specific endpoint for API key."""
        # Admin keys can access all endpoints
        if key_info.is_admin:
            return True
        
        # Define endpoint restrictions for regular keys
        restricted_endpoints = [
            "/admin",
            "/api/v1/admin"
        ]
        
        # Check if trying to access restricted endpoint
        for restricted in restricted_endpoints:
            if endpoint.startswith(restricted):
                return False
        
        return True


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = security
) -> APIKeyInfo:
    """Dependency to get current authenticated API key."""
    return auth_manager.authenticate_request(request, credentials)


async def require_admin(
    key_info: APIKeyInfo = get_current_api_key
) -> APIKeyInfo:
    """Dependency to require admin privileges."""
    auth_manager.authorize_admin_request(key_info)
    return key_info


async def log_api_usage(
    api_key: str,
    endpoint: str,
    success: bool,
    processing_time_ms: float,
    request_data: dict,
    response_data: dict,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log API usage to database."""
    try:
        from ..database.connections import get_mongodb_collection
        
        log_entry = {
            "api_key": api_key,
            "endpoint": endpoint,
            "success": success,
            "processing_time_ms": processing_time_ms,
            "request_data": request_data,
            "response_data": response_data,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow()
        }
        
        # Insert into MongoDB
        collection = get_mongodb_collection("api_usage_logs")
        await collection.insert_one(log_entry)
        
        # Update API key usage statistics
        client = get_redis_client()
        await cache_increment(f"api_key_usage:{api_key}")
        
    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")


async def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format."""
    if not api_key:
        return False
    
    # Check length (reasonable API key length)
    if len(api_key) < 10 or len(api_key) > 128:
        return False
    
    # Check for valid characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
        return False
    
    return True


async def get_api_key_analytics(api_key: str) -> Dict:
    """Get analytics for API key usage."""
    try:
        client = get_redis_client()
        
        # Get usage count
        usage_key = f"api_key_usage:{api_key}"
        usage_count = await cache_get(usage_key) or 0
        
        # Get rate limit info
        rate_limit_key = f"rate_limit_info:{api_key}"
        rate_limit_info = await cache_get(rate_limit_key) or {
            "requests_today": 0,
            "last_reset": datetime.utcnow().strftime("%Y-%m-%d")
        }
        
        return {
            "total_requests": usage_count,
            "requests_today": rate_limit_info.get("requests_today", 0),
            "last_reset": rate_limit_info.get("last_reset"),
            "rate_limit": auth_manager.valid_api_keys.get(api_key, APIKeyInfo("", "")).rate_limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get API key analytics: {e}")
        return {}


# API key generation utilities
def generate_api_key() -> str:
    """Generate a new API key."""
    import secrets
    import string
    
    # Generate random API key
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    
    return api_key


def create_api_key_in_database(
    name: str,
    is_admin: bool = False,
    rate_limit: int = 100
) -> tuple[str, APIKeyInfo]:
    """Create new API key in database."""
    try:
        api_key = generate_api_key()
        key_id = f"key_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Insert into database
        with get_postgresql_session() as session:
            db_key = APIKeyDB(
                key_id=key_id,
                name=name,
                api_key=api_key,
                is_admin=is_admin,
                rate_limit=rate_limit
            )
            session.add(db_key)
            session.commit()
        
        # Add to auth manager
        key_info = APIKeyInfo(
            key_id=key_id,
            name=name,
            is_admin=is_admin,
            rate_limit=rate_limit
        )
        
        auth_manager.valid_api_keys[api_key] = key_info
        if is_admin:
            auth_manager.admin_api_keys.add(api_key)
        
        logger.info(f"Created new API key: {key_id}")
        return api_key, key_info
        
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise


async def revoke_api_key(api_key: str) -> bool:
    """Revoke API key."""
    try:
        # Remove from database
        with get_postgresql_session() as session:
            db_key = session.query(APIKeyDB).filter(
                APIKeyDB.api_key == api_key
            ).first()
            
            if db_key:
                db_key.is_active = False
                session.commit()
        
        # Remove from auth manager
        if api_key in auth_manager.valid_api_keys:
            del auth_manager.valid_api_keys[api_key]
        auth_manager.admin_api_keys.discard(api_key)
        
        logger.info(f"Revoked API key: {api_key[:8]}...")
        return True
        
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        return False