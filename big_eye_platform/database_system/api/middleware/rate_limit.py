"""Rate limiting middleware."""

import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging

from ..config.settings import settings
from ..cache.redis_cache import check_rate_limit, cache_get, cache_set
from ..models.database import RateLimitLogDB
from ..database.connections import get_postgresql_session, get_mongodb_collection

logger = logging.getLogger(__name__)


class RateLimitError(HTTPException):
    """Rate limit exceeded error."""
    
    def __init__(self, detail: str, retry_after: Optional[int] = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)} if retry_after else None,
        )


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for FastAPI."""
    
    def __init__(self, app, calls: int = None, period: int = None):
        super().__init__(app)
        self.calls = calls or settings.RATE_LIMIT_REQUESTS
        self.period = period or settings.RATE_LIMIT_WINDOW
        self.requests: Dict[str, list] = {}
        self.client_requests: Dict[str, list] = {}
        
        # Different limits for different types of clients
        self.limits = {
            "default": {
                "calls": self.calls,
                "period": self.period
            },
            "admin": {
                "calls": settings.RATE_LIMIT_ADMIN_REQUESTS,
                "period": self.period
            },
            "premium": {
                "calls": self.calls * 2,
                "period": self.period
            }
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request and apply rate limiting."""
        start_time = time.time()
        
        # Skip rate limiting for health checks and docs
        if self._should_skip_rate_limit(request):
            return await call_next(request)
        
        try:
            # Get API key from request
            api_key = await self._get_api_key(request)
            
            # Skip rate limiting for local requests (development)
            if settings.DEBUG and not api_key:
                return await call_next(request)
            
            # Determine client type and limits
            client_type = await self._get_client_type(request, api_key)
            limits = self.limits.get(client_type, self.limits["default"])
            
            # Check rate limit
            allowed, remaining = await self._check_rate_limit(
                api_key or request.client.host,
                request.url.path,
                limits["calls"],
                limits["period"]
            )
            
            if not allowed:
                # Log rate limit hit
                await self._log_rate_limit_hit(
                    api_key or "anonymous",
                    request.url.path,
                    limits["calls"],
                    limits["period"],
                    request.client.host if request.client else None,
                    request.headers.get("user-agent")
                )
                
                # Calculate retry after time
                retry_after = await self._calculate_retry_after(
                    api_key or request.client.host,
                    request.url.path,
                    limits["period"]
                )
                
                raise RateLimitError(
                    detail=f"Rate limit exceeded. {remaining} requests remaining. Try again in {retry_after} seconds.",
                    retry_after=retry_after
                )
            
            # Add rate limit headers
            response = await call_next(request)
            
            # Add rate limiting headers
            response.headers["X-RateLimit-Limit"] = str(limits["calls"])
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + limits["period"])
            
            # Log successful request
            processing_time = (time.time() - start_time) * 1000
            await self._log_rate_limit_success(
                api_key or "anonymous",
                request.url.path,
                processing_time,
                request.client.host if request.client else None
            )
            
            return response
            
        except RateLimitError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow the request but log warning
            return await call_next(request)
    
    def _should_skip_rate_limit(self, request: Request) -> bool:
        """Check if request should skip rate limiting."""
        skip_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico"
        ]
        
        path = str(request.url.path)
        return any(path.startswith(skip_path) for skip_path in skip_paths)
    
    async def _get_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request."""
        # Check Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        # Check X-API-Key header
        api_key = request.headers.get("x-api-key")
        if api_key:
            return api_key
        
        # Check query parameter
        if hasattr(request, "_query_params"):
            api_key = request.query_params.get("api_key")
            if api_key:
                return api_key
        
        return None
    
    async def _get_client_type(self, request: Request, api_key: Optional[str]) -> str:
        """Determine client type based on request."""
        # Check if it's an admin key
        if api_key:
            from .auth import auth_manager
            key_info = auth_manager.valid_api_keys.get(api_key)
            if key_info:
                if key_info.is_admin:
                    return "admin"
                # You could implement premium checking here
                # if key_info.is_premium:
                #     return "premium"
        
        return "default"
    
    async def _check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """Check if request is within rate limit."""
        try:
            # Try Redis-based rate limiting first
            return await check_rate_limit(identifier, endpoint, max_requests, window_seconds)
            
        except Exception as e:
            logger.warning(f"Redis rate limit check failed, falling back to in-memory: {e}")
            return self._fallback_rate_limit_check(identifier, endpoint, max_requests, window_seconds)
    
    def _fallback_rate_limit_check(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """Fallback rate limiting using in-memory storage."""
        now = time.time()
        
        if identifier not in self.requests:
            self.requests[identifier] = {}
        
        if endpoint not in self.requests[identifier]:
            self.requests[identifier][endpoint] = []
        
        # Clean old requests
        self.requests[identifier][endpoint] = [
            req_time for req_time in self.requests[identifier][endpoint]
            if now - req_time < window_seconds
        ]
        
        # Check if within limit
        current_requests = len(self.requests[identifier][endpoint])
        remaining = max(0, max_requests - current_requests - 1)
        
        if current_requests >= max_requests:
            return False, remaining
        
        # Record this request
        self.requests[identifier][endpoint].append(now)
        
        return True, remaining
    
    async def _calculate_retry_after(
        self,
        identifier: str,
        endpoint: str,
        window_seconds: int
    ) -> int:
        """Calculate seconds until rate limit resets."""
        try:
            if identifier in self.requests and endpoint in self.requests[identifier]:
                if self.requests[identifier][endpoint]:
                    oldest_request = min(self.requests[identifier][endpoint])
                    window_start = oldest_request
                    return max(1, int(window_start + window_seconds - time.time()))
        except Exception:
            pass
        
        return window_seconds
    
    async def _log_rate_limit_hit(
        self,
        api_key: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
        ip_address: Optional[str],
        user_agent: Optional[str]
    ):
        """Log rate limit hit to database."""
        try:
            from datetime import datetime
            
            # Log to PostgreSQL
            with get_postgresql_session() as session:
                log_entry = RateLimitLogDB(
                    api_key=api_key,
                    endpoint=endpoint,
                    requests_count=max_requests,
                    window_start=datetime.utcnow(),
                    window_end=datetime.utcnow(),
                    blocked=True
                )
                session.add(log_entry)
                session.commit()
            
            # Log to MongoDB for analytics
            collection = get_mongodb_collection("rate_limit_logs")
            await collection.insert_one({
                "api_key": api_key,
                "endpoint": endpoint,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "blocked": True,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "timestamp": datetime.utcnow()
            })
            
            logger.warning(f"Rate limit exceeded for API key: {api_key[:8]}... on {endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to log rate limit hit: {e}")
    
    async def _log_rate_limit_success(
        self,
        api_key: str,
        endpoint: str,
        processing_time_ms: float,
        ip_address: Optional[str]
    ):
        """Log successful rate limit check."""
        try:
            # Log to analytics collection for monitoring
            collection = get_mongodb_collection("rate_limit_analytics")
            await collection.insert_one({
                "api_key": api_key,
                "endpoint": endpoint,
                "processing_time_ms": processing_time_ms,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            logger.error(f"Failed to log rate limit success: {e}")


class RateLimitConfig:
    """Rate limit configuration for different endpoints."""
    
    # Different rate limits for different endpoints
    ENDPOINT_LIMITS = {
        # Validation endpoints - moderate rate limiting
        "validate_email": {"requests": 100, "window": 60},
        "validate_domain": {"requests": 100, "window": 60},
        "validate_ip": {"requests": 100, "window": 60},
        "validate_url": {"requests": 100, "window": 60},
        "validate_sender": {"requests": 100, "window": 60},
        "validate_bulk": {"requests": 10, "window": 60},  # Lower limit for bulk operations
        
        # Reputation endpoints - higher rate limiting
        "reputation": {"requests": 200, "window": 60},
        
        # Threat intelligence - moderate rate limiting
        "threats": {"requests": 150, "window": 60},
        
        # Admin endpoints - highest rate limiting
        "admin": {"requests": 1000, "window": 60},
    }
    
    @classmethod
    def get_limit_for_endpoint(cls, endpoint: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        # Extract endpoint type from full path
        endpoint_type = endpoint.split("/")[-1] if "/" in endpoint else endpoint
        
        return cls.ENDPOINT_LIMITS.get(
            endpoint_type,
            {"requests": settings.RATE_LIMIT_REQUESTS, "window": settings.RATE_LIMIT_WINDOW}
        )


async def get_rate_limit_info(api_key: str) -> Dict[str, any]:
    """Get current rate limit information for API key."""
    try:
        # Get usage stats from Redis
        client = None
        try:
            from ..cache.redis_cache import get_redis_client
            client = get_redis_client()
        except:
            pass
        
        if client:
            # Get current usage
            usage_key = f"rate_limit:{api_key}:*"
            # Note: This is a simplified version - you'd need to get specific endpoint usage
            
            return {
                "api_key": api_key[:8] + "...",
                "limits": {
                    "requests_per_minute": settings.RATE_LIMIT_REQUESTS,
                    "requests_per_hour": settings.RATE_LIMIT_REQUESTS * 60
                }
            }
        
        return {
            "api_key": api_key[:8] + "...",
            "message": "Rate limiting info not available"
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit info: {e}")
        return {"error": str(e)}


async def reset_rate_limit(api_key: str, endpoint: str = None) -> bool:
    """Reset rate limit for API key (admin only)."""
    try:
        # This would require Redis Lua script or similar for proper implementation
        # For now, this is a placeholder
        
        logger.info(f"Rate limit reset requested for API key: {api_key[:8]}... on endpoint: {endpoint or 'all'}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}")
        return False