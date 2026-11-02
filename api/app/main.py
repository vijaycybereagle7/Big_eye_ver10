"""Main FastAPI application for the Cybersecurity Validation API."""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
import uvicorn

from .config.settings import settings
from .database.connections import init_databases, close_databases
from .cache.redis_cache import init_redis, check_redis_health
from .routers import validation, reputation, threat_intelligence, admin
from .middleware.auth import auth_manager
from .middleware.rate_limit import RateLimitingMiddleware
from .models.schemas import ErrorResponse, APIError

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE)
    ] if settings.LOG_FILE != "api/logs/app.log" else [logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting Cybersecurity Validation API...")
    
    try:
        # Initialize databases
        logger.info("Initializing databases...")
        await asyncio.get_event_loop().run_in_executor(None, init_databases)
        
        # Initialize Redis
        logger.info("Initializing Redis cache...")
        await init_redis()
        
        # Reload API keys
        logger.info("Loading API keys...")
        auth_manager._load_api_keys()
        
        # Check service health
        redis_health = await check_redis_health()
        logger.info(f"Redis health: {redis_health}")
        
        logger.info("Cybersecurity Validation API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cybersecurity Validation API...")
    
    try:
        # Close databases
        await asyncio.get_event_loop().run_in_executor(None, close_databases)
        logger.info("Databases closed")
        
        # Close Redis
        try:
            from .cache.redis_cache import get_redis_client
            client = get_redis_client()
            await client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.warning(f"Failed to close Redis: {e}")
        
        logger.info("Cybersecurity Validation API shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Comprehensive cybersecurity validation and threat intelligence API with validation, reputation analysis, and threat intelligence capabilities.",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitingMiddleware,
    calls=settings.RATE_LIMIT_REQUESTS,
    period=settings.RATE_LIMIT_WINDOW
)


# Custom exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        success=False,
        message=exc.detail,
        error=APIError(
            error_code=f"HTTP_{exc.status_code}",
            error_message=exc.detail,
            details={"status_code": exc.status_code, "path": str(request.url.path)}
        )
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    error_response = ErrorResponse(
        success=False,
        message="Request validation failed",
        error=APIError(
            error_code="VALIDATION_ERROR",
            error_message="Invalid request parameters",
            details={"validation_errors": exc.errors()}
        )
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        success=False,
        message="Internal server error",
        error=APIError(
            error_code="INTERNAL_ERROR",
            error_message="An unexpected error occurred",
            details={"path": str(request.url.path)} if not settings.DEBUG else {"error": str(exc)}
        )
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.dict()
    )


# Include routers
app.include_router(validation.router, prefix="/api/v1")
app.include_router(reputation.router, prefix="/api/v1")
app.include_router(threat_intelligence.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": asyncio.get_event_loop().time(),
        "debug": settings.DEBUG
    }


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Comprehensive cybersecurity validation and threat intelligence API",
        "documentation": "/docs" if settings.DEBUG else "Contact administrator for API documentation",
        "endpoints": {
            "validation": "/api/v1/validate",
            "reputation": "/api/v1/reputation",
            "threat_intelligence": "/api/v1/threats",
            "admin": "/api/v1/admin"
        },
        "authentication": "API Key authentication required (X-API-Key or Authorization header)",
        "timestamp": asyncio.get_event_loop().time()
    }


# OpenAPI schema customization
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Comprehensive cybersecurity validation and threat intelligence API",
        routes=app.routes,
    )
    
    # Add custom info
    openapi_schema["info"]["contact"] = {
        "name": "Cybersecurity API Team",
        "email": "support@cybersec-api.com"
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API Key for authentication"
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API Key",
            "description": "Bearer authentication using API key"
        }
    }
    
    # Apply security to all paths except health check and root
    for path in openapi_schema["paths"]:
        if path not in ["/health", "/"]:
            openapi_schema["paths"][path]["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Background tasks for system maintenance
@app.on_event("startup")
async def startup_tasks():
    """Run startup tasks."""
    try:
        # Initialize any background services
        logger.info("Running startup tasks...")
        
        # Example: Warm up cache with common queries
        # await warm_cache()
        
        logger.info("Startup tasks completed")
        
    except Exception as e:
        logger.error(f"Startup tasks failed: {e}")


@app.on_event("shutdown")
async def shutdown_tasks():
    """Run shutdown tasks."""
    try:
        logger.info("Running shutdown tasks...")
        
        # Example: Save state, cleanup resources
        # await save_application_state()
        
        logger.info("Shutdown tasks completed")
        
    except Exception as e:
        logger.error(f"Shutdown tasks failed: {e}")


if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )