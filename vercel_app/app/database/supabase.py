"""Supabase database connection for Vercel-optimized API."""

import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from .config.settings import settings

logger = logging.getLogger(__name__)

# Global Supabase client
supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client."""
    global supabase_client
    
    if supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise ValueError("Supabase URL and ANON_KEY must be configured")
        
        supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        logger.info("Supabase client initialized")
    
    return supabase_client


async def log_validation_request(
    endpoint: str,
    value: str,
    success: bool,
    processing_time_ms: float,
    api_key: str
) -> None:
    """Log validation request to Supabase."""
    try:
        client = get_supabase_client()
        
        log_entry = {
            "endpoint": endpoint,
            "value": value,
            "success": success,
            "processing_time_ms": processing_time_ms,
            "api_key": api_key,
            "timestamp": "now()"
        }
        
        # Log to validation_logs table (needs to be created in Supabase)
        client.table("validation_logs").insert(log_entry).execute()
        
    except Exception as e:
        logger.warning(f"Failed to log validation request: {e}")


async def log_reputation_query(
    endpoint: str,
    value: str,
    value_type: str,
    success: bool,
    processing_time_ms: float,
    api_key: str
) -> None:
    """Log reputation query to Supabase."""
    try:
        client = get_supabase_client()
        
        log_entry = {
            "endpoint": endpoint,
            "value": value,
            "value_type": value_type,
            "success": success,
            "processing_time_ms": processing_time_ms,
            "api_key": api_key,
            "timestamp": "now()"
        }
        
        # Log to reputation_logs table (needs to be created in Supabase)
        client.table("reputation_logs").insert(log_entry).execute()
        
    except Exception as e:
        logger.warning(f"Failed to log reputation query: {e}")


async def get_cached_result(key: str) -> Optional[Dict[str, Any]]:
    """Get cached result from Supabase cache table."""
    try:
        client = get_supabase_client()
        
        # Query cache table for valid entry
        response = client.table("api_cache")\
            .select("*")\
            .eq("cache_key", key)\
            .gt("expires_at", "now()")\
            .limit(1)\
            .execute()
        
        if response.data:
            cache_entry = response.data[0]
            return {
                "data": cache_entry["cached_data"],
                "hit": True
            }
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to get cached result: {e}")
        return None


async def set_cached_result(key: str, data: Dict[str, Any], ttl_seconds: int = 300) -> None:
    """Set cached result in Supabase cache table."""
    try:
        client = get_supabase_client()
        
        # Calculate expiration timestamp
        from datetime import datetime, timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        cache_entry = {
            "cache_key": key,
            "cached_data": data,
            "expires_at": expires_at.isoformat(),
            "created_at": "now()"
        }
        
        # Upsert cache entry
        client.table("api_cache").upsert(cache_entry, on_conflict="cache_key").execute()
        
    except Exception as e:
        logger.warning(f"Failed to set cached result: {e}")


# Cache table structure for Supabase:
"""
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,
    cached_data JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_cache_expires_at ON api_cache(expires_at);

CREATE TABLE validation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reputation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
"""
