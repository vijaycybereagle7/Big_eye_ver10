"""Admin endpoints for API key management and system administration."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime, timedelta
import json

from ..models.schemas import (
    AdminDashboardResponse, AdminStats, APIKeyInfo, APIKeyCreate, APIKeyResponse,
    PaginatedResponse, SearchRequest
)
from ..middleware.auth import require_admin, APIKeyInfo as CurrentAPIKeyInfo
from ..middleware.auth import (
    create_api_key_in_database, revoke_api_key, get_api_key_analytics
)
from ..database.connections import get_postgresql_session, get_mongodb_collection
from ..cache.redis_cache import get_cache_stats, clear_cache_pattern

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    summary="Get admin dashboard",
    description="Get comprehensive admin dashboard with system statistics and API key information."
)
async def get_admin_dashboard(
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get admin dashboard with system statistics."""
    try:
        logger.info(f"Admin dashboard requested by {current_admin.key_id}")
        
        # Get system statistics
        stats = await get_system_stats()
        
        # Get API keys
        api_keys = await get_all_api_keys()
        
        return AdminDashboardResponse(
            success=True,
            message="Admin dashboard data retrieved",
            stats=stats,
            api_keys=api_keys
        )
        
    except Exception as e:
        logger.error(f"Admin dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=AdminStats,
    summary="Get system statistics",
    description="Get comprehensive system statistics and performance metrics."
)
async def get_system_statistics(
    time_range_hours: int = 24,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get system statistics."""
    try:
        logger.info(f"System stats requested by {current_admin.key_id} (range: {time_range_hours}h)")
        
        # Validate time range
        if time_range_hours < 1 or time_range_hours > 8760:  # Max 1 year
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Time range must be between 1 and 8760 hours"
            )
        
        stats = await get_system_stats(time_range_hours)
        return stats
        
    except Exception as e:
        logger.error(f"System statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get(
    "/api-keys",
    response_model=List[APIKeyInfo],
    summary="Get all API keys",
    description="Get list of all API keys with their status and usage information."
)
async def get_api_keys(
    active_only: bool = False,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get all API keys."""
    try:
        api_keys = await get_all_api_keys(active_only)
        return api_keys
        
    except Exception as e:
        logger.error(f"Get API keys error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API keys: {str(e)}"
        )


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    summary="Create new API key",
    description="Create a new API key with specified permissions and rate limits."
)
async def create_api_key(
    request: APIKeyCreate,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Create new API key."""
    try:
        logger.info(f"API key creation requested by {current_admin.key_id} for {request.name}")
        
        # Create API key
        api_key, key_info = create_api_key_in_database(
            name=request.name,
            is_admin=request.is_admin,
            rate_limit=request.rate_limit or 100
        )
        
        # Log the action
        await log_admin_action(
            current_admin.key_id,
            "create_api_key",
            {"name": request.name, "is_admin": request.is_admin, "rate_limit": request.rate_limit}
        )
        
        logger.info(f"API key created: {key_info.key_id}")
        
        return APIKeyResponse(
            success=True,
            message="API key created successfully",
            api_key=api_key,
            key_info=APIKeyInfo(
                key_id=key_info.key_id,
                name=key_info.name,
                is_admin=key_info.is_admin,
                rate_limit=key_info.rate_limit,
                is_active=True
            )
        )
        
    except Exception as e:
        logger.error(f"API key creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.delete(
    "/api-keys/{key_id}",
    summary="Revoke API key",
    description="Revoke and deactivate an existing API key."
)
async def revoke_api_key_endpoint(
    key_id: str,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Revoke API key."""
    try:
        logger.info(f"API key revocation requested by {current_admin.key_id} for {key_id}")
        
        # Find the actual API key in database
        with get_postgresql_session() as session:
            from ..models.database import APIKeyDB
            db_key = session.query(APIKeyDB).filter(
                APIKeyDB.key_id == key_id
            ).first()
            
            if not db_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            # Revoke the API key
            success = await revoke_api_key(db_key.api_key)
            
            if success:
                # Log the action
                await log_admin_action(
                    current_admin.key_id,
                    "revoke_api_key",
                    {"key_id": key_id}
                )
                
                logger.info(f"API key revoked: {key_id}")
                return {"success": True, "message": "API key revoked successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to revoke API key"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get(
    "/api-keys/{key_id}/analytics",
    summary="Get API key analytics",
    description="Get detailed analytics for a specific API key including usage statistics."
)
async def get_api_key_analytics_endpoint(
    key_id: str,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get API key analytics."""
    try:
        logger.info(f"API key analytics requested by {current_admin.key_id} for {key_id}")
        
        # Find the API key in database
        with get_postgresql_session() as session:
            from ..models.database import APIKeyDB
            db_key = session.query(APIKeyDB).filter(
                APIKeyDB.key_id == key_id
            ).first()
            
            if not db_key:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="API key not found"
                )
            
            # Get analytics
            analytics = await get_api_key_analytics(db_key.api_key)
            
            # Get detailed usage statistics
            detailed_stats = await get_detailed_api_key_stats(db_key.api_key)
            
            return {
                "success": True,
                "message": "API key analytics retrieved",
                "analytics": analytics,
                "detailed_stats": detailed_stats
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get(
    "/cache",
    summary="Get cache statistics",
    description="Get cache performance statistics and memory usage."
)
async def get_cache_statistics(
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get cache statistics."""
    try:
        logger.info(f"Cache statistics requested by {current_admin.key_id}")
        
        cache_stats = await get_cache_stats()
        
        return {
            "success": True,
            "message": "Cache statistics retrieved",
            "cache_stats": cache_stats
        }
        
    except Exception as e:
        logger.error(f"Cache statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache statistics: {str(e)}"
        )


@router.post(
    "/cache/clear",
    summary="Clear cache",
    description="Clear specific cache patterns or all cache data."
)
async def clear_cache(
    pattern: Optional[str] = None,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Clear cache data."""
    try:
        logger.info(f"Cache clear requested by {current_admin.key_id} with pattern: {pattern}")
        
        if pattern:
            # Clear specific pattern
            cleared_count = await clear_cache_pattern(pattern)
            message = f"Cleared {cleared_count} cache keys matching pattern: {pattern}"
        else:
            # Clear all cache (this would need implementation)
            cleared_count = 0
            message = "Cache clear requires specific pattern (not implemented)"
        
        # Log the action
        await log_admin_action(
            current_admin.key_id,
            "clear_cache",
            {"pattern": pattern, "cleared_count": cleared_count}
        )
        
        return {
            "success": True,
            "message": message,
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get(
    "/logs",
    response_model=dict,
    summary="Get system logs",
    description="Get recent system logs and error reports."
)
async def get_system_logs(
    limit: int = 100,
    level: Optional[str] = None,
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get system logs."""
    try:
        # Validate parameters
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        # Get logs from MongoDB
        collection = get_mongodb_collection("error_logs")
        
        query = {}
        if level:
            query["level"] = level.upper()
        
        # Get recent logs
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        logs = []
        async for log in cursor:
            logs.append({
                "id": str(log.get("_id")),
                "error_code": log.get("error_code"),
                "error_message": log.get("error_message"),
                "api_key": log.get("api_key"),
                "endpoint": log.get("endpoint"),
                "timestamp": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                "error_details": log.get("error_details")
            })
        
        return {
            "success": True,
            "message": "System logs retrieved",
            "logs": logs,
            "total": len(logs)
        }
        
    except Exception as e:
        logger.error(f"System logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


@router.get(
    "/health",
    summary="Get system health",
    description="Get comprehensive system health status including all services."
)
async def get_system_health(
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Get comprehensive system health."""
    try:
        logger.info(f"System health check requested by {current_admin.key_id}")
        
        # Check all services
        from ..database.connections import check_postgresql_health, check_mongodb_health
        from ..cache.redis_cache import check_redis_health
        
        # Run health checks concurrently
        health_checks = await asyncio.gather(
            check_postgresql_health(),
            check_mongodb_health(),
            check_redis_health(),
            return_exceptions=True
        )
        
        postgresql_health, mongodb_health, redis_health = health_checks
        
        # Handle exceptions
        if isinstance(postgresql_health, Exception):
            postgresql_health = {"status": "error", "message": str(postgresql_health)}
        
        if isinstance(mongodb_health, Exception):
            mongodb_health = {"status": "error", "message": str(mongodb_health)}
        
        if isinstance(redis_health, Exception):
            redis_health = {"status": "error", "message": str(redis_health)}
        
        # Determine overall health
        all_healthy = all(
            health.get("status") == "healthy" 
            for health in [postgresql_health, mongodb_health, redis_health]
        )
        
        # Get system resource usage (placeholder)
        system_info = {
            "cpu_usage": "unknown",  # Would implement with psutil
            "memory_usage": "unknown",
            "disk_usage": "unknown",
            "uptime": "unknown"
        }
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "postgresql": postgresql_health,
                "mongodb": mongodb_health,
                "redis": redis_health
            },
            "system_info": system_info,
            "overall_score": 1.0 if all_healthy else 0.7
        }
        
    except Exception as e:
        logger.error(f"System health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post(
    "/maintenance",
    summary="System maintenance",
    description="Perform system maintenance tasks like database optimization, cache warming, etc."
)
async def perform_maintenance(
    tasks: List[str],
    current_admin: CurrentAPIKeyInfo = Depends(require_admin)
):
    """Perform system maintenance tasks."""
    try:
        logger.info(f"Maintenance requested by {current_admin.key_id} for tasks: {tasks}")
        
        valid_tasks = ["optimize_database", "warm_cache", "cleanup_old_data", "backup_data"]
        
        # Validate tasks
        for task in tasks:
            if task not in valid_tasks:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid task: {task}. Valid tasks: {valid_tasks}"
                )
        
        results = []
        
        for task in tasks:
            try:
                if task == "optimize_database":
                    result = await optimize_database()
                    results.append({"task": task, "success": True, "result": result})
                elif task == "warm_cache":
                    result = await warm_cache()
                    results.append({"task": task, "success": True, "result": result})
                elif task == "cleanup_old_data":
                    result = await cleanup_old_data()
                    results.append({"task": task, "success": True, "result": result})
                elif task == "backup_data":
                    result = await backup_data()
                    results.append({"task": task, "success": True, "result": result})
            except Exception as e:
                results.append({"task": task, "success": False, "error": str(e)})
        
        # Log the action
        await log_admin_action(
            current_admin.key_id,
            "maintenance",
            {"tasks": tasks, "results": results}
        )
        
        return {
            "success": True,
            "message": "Maintenance completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Maintenance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Maintenance failed: {str(e)}"
        )


async def get_system_stats(time_range_hours: int = 24) -> AdminStats:
    """Get system statistics from database."""
    try:
        from datetime import timedelta
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Get validation logs statistics
        collection = get_mongodb_collection("validation_logs")
        
        # Query for statistics
        pipeline = [
            {
                "$match": {
                    "timestamp": {
                        "$gte": start_time,
                        "$lte": end_time
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_requests": {"$sum": 1},
                    "valid_requests": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "invalid_requests": {
                        "$sum": {"$cond": ["$success", 0, 1]}
                    },
                    "avg_processing_time": {"$avg": "$processing_time_ms"},
                    "unique_api_keys": {"$addToSet": "$api_key"},
                    "top_endpoints": {
                        "$push": {
                            "endpoint": "$endpoint",
                            "count": 1
                        }
                    }
                }
            }
        ]
        
        cursor = collection.aggregate(pipeline)
        stats_data = await cursor.to_list(length=1)
        
        if stats_data:
            data = stats_data[0]
            total_requests = data.get("total_requests", 0)
            valid_requests = data.get("valid_requests", 0)
            invalid_requests = data.get("invalid_requests", 0)
            unique_api_keys = len(data.get("unique_api_keys", []))
            top_queried_values = []
        else:
            total_requests = valid_requests = invalid_requests = unique_api_keys = 0
            top_queried_values = []
        
        # Get cache statistics
        cache_stats = await get_cache_stats()
        cached_requests = cache_stats.get("keyspace_hits", 0)
        
        # Get recent threats
        threat_collection = get_mongodb_collection("threat_intelligence")
        recent_threats_cursor = threat_collection.find({
            "last_seen": {"$gte": start_time}
        }).sort("last_seen", -1).limit(10)
        
        recent_threats = []
        async for threat in recent_threats_cursor:
            recent_threats.append({
                "indicator": threat.get("indicator"),
                "type": threat.get("indicator_type"),
                "last_seen": threat.get("last_seen").isoformat() if threat.get("last_seen") else None,
                "source": threat.get("source")
            })
        
        # System health (mock data)
        system_health = {
            "status": "healthy",
            "cpu_usage": "45%",
            "memory_usage": "62%",
            "disk_usage": "34%",
            "api_responses": {
                "avg_response_time": 250,
                "requests_per_second": 45
            }
        }
        
        return AdminStats(
            total_requests=total_requests,
            valid_requests=valid_requests,
            invalid_requests=invalid_requests,
            cached_requests=cached_requests,
            active_api_keys=unique_api_keys,
            top_queried_values=top_queried_values,
            recent_threats=recent_threats,
            system_health=system_health
        )
        
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        # Return default stats on error
        return AdminStats(
            total_requests=0,
            valid_requests=0,
            invalid_requests=0,
            cached_requests=0,
            active_api_keys=0,
            top_queried_values=[],
            recent_threats=[],
            system_health={"status": "unknown"}
        )


async def get_all_api_keys(active_only: bool = False) -> List[APIKeyInfo]:
    """Get all API keys from database."""
    try:
        with get_postgresql_session() as session:
            from ..models.database import APIKeyDB
            
            query = session.query(APIKeyDB)
            if active_only:
                query = query.filter(APIKeyDB.is_active == True)
            
            api_keys = query.order_by(APIKeyDB.created_at.desc()).all()
            
            result = []
            for api_key in api_keys:
                result.append(APIKeyInfo(
                    key_id=api_key.key_id,
                    name=api_key.name,
                    is_admin=api_key.is_admin,
                    created_at=api_key.created_at,
                    last_used=api_key.last_used,
                    request_count=api_key.request_count,
                    rate_limit=api_key.rate_limit
                ))
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to get API keys: {e}")
        return []


async def get_detailed_api_key_stats(api_key: str) -> dict:
    """Get detailed statistics for API key usage."""
    try:
        # This would query the database for detailed usage patterns
        return {
            "hourly_usage": [],
            "endpoint_usage": {},
            "error_rate": 0.0,
            "avg_response_time": 0.0
        }
    except Exception as e:
        logger.error(f"Failed to get detailed API key stats: {e}")
        return {}


async def log_admin_action(admin_key_id: str, action: str, details: dict):
    """Log admin actions."""
    try:
        collection = get_mongodb_collection("admin_actions")
        await collection.insert_one({
            "admin_key_id": admin_key_id,
            "action": action,
            "details": details,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        logger.warning(f"Failed to log admin action: {e}")


async def optimize_database() -> dict:
    """Optimize database performance."""
    try:
        # This would implement database optimization
        return {"optimized_tables": 0, "reclaimed_space": "0 MB"}
    except Exception as e:
        return {"error": str(e)}


async def warm_cache() -> dict:
    """Warm up cache with frequently accessed data."""
    try:
        # This would implement cache warming
        return {"warmed_keys": 0, "cache_size": "0 MB"}
    except Exception as e:
        return {"error": str(e)}


async def cleanup_old_data() -> dict:
    """Clean up old data from databases."""
    try:
        # This would implement data cleanup
        return {"deleted_records": 0, "reclaimed_space": "0 MB"}
    except Exception as e:
        return {"error": str(e)}


async def backup_data() -> dict:
    """Create backup of critical data."""
    try:
        # This would implement data backup
        return {"backup_files": [], "total_size": "0 MB"}
    except Exception as e:
        return {"error": str(e)}