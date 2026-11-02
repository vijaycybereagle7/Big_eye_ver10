"""Main FastAPI application optimized for Vercel serverless deployment."""

import logging
import asyncio
import socket
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config.settings import settings
from .routers import validation, reputation, threat_intelligence
from .models.schemas import ErrorResponse, APIError, HealthResponse, RootResponse

# Configure logging for serverless
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for serverless."""
    logger.info("Starting Vercel-optimized Cybersecurity Validation API...")
    
    try:
        # Test Supabase connection if configured
        if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
            try:
                from .database.supabase import get_supabase_client
                client = get_supabase_client()
                # Simple test query
                response = client.table("api_cache").select("count").limit(1).execute()
                logger.info("Supabase connection verified")
            except Exception as e:
                logger.warning(f"Supabase connection test failed: {e}")
        
        logger.info("API startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        # Don't raise exception in serverless context
    
    yield
    
    # Shutdown
    logger.info("Shutting down Cybersecurity Validation API...")


# Create FastAPI application optimized for serverless
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Vercel-optimized cybersecurity validation and threat intelligence API with validation, reputation analysis, and threat intelligence capabilities.",
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


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Basic health check endpoint."""
    # Check Supabase connection
    supabase_connected = False
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        try:
            from .database.supabase import get_supabase_client
            client = get_supabase_client()
            # Simple test query
            response = client.table("api_cache").select("count").limit(1).execute()
            supabase_connected = True
        except Exception:
            supabase_connected = False
    
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        debug=settings.DEBUG,
        supabase_connected=supabase_connected
    )


@app.get("/", response_model=RootResponse, tags=["root"])
async def root():
    """Root endpoint with API information."""
    return RootResponse(
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Vercel-optimized cybersecurity validation and threat intelligence API",
        endpoints={
            "validation": "/api/v1/validate",
            "reputation": "/api/v1/reputation",
            "threat_intelligence": "/api/v1/threats",
            "health": "/health"
        },
        timestamp=datetime.utcnow(),
        supabase_enabled=bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY),
        serverless_mode=True
    )


# OpenAPI schema customization
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "Vercel-optimized cybersecurity validation and threat intelligence API",
            "contact": {
                "name": "Cybersecurity API Team",
                "email": "support@cybersec-api.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Vercel serverless deployment"
            }
        ],
        "components": {
            "securitySchemes": {
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
        }
    }
    
    try:
        from fastapi.openapi.utils import get_openapi
        base_schema = get_openapi(
            title=settings.APP_NAME,
            version=settings.APP_VERSION,
            description="Vercel-optimized cybersecurity validation and threat intelligence API",
            routes=app.routes,
        )
        
        # Merge with custom schema
        openapi_schema.update({
            "paths": base_schema.get("paths", {}),
            "components": {
                **openapi_schema.get("components", {}),
                **base_schema.get("components", {})
            }
        })
        
        # Apply security to all paths except health and root
        for path in openapi_schema.get("paths", {}):
            if path not in ["/health", "/"]:
                for method in openapi_schema["paths"][path]:
                    openapi_schema["paths"][path][method]["security"] = [{"ApiKeyAuth": []}]
    
    except Exception as e:
        logger.warning(f"Failed to generate complete OpenAPI schema: {e}")
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
