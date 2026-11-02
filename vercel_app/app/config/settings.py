"""Application configuration optimized for Vercel serverless deployment."""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator
import json


class Settings(BaseSettings):
    """Application settings optimized for Vercel serverless environment."""
    
    # Application Settings
    APP_NAME: str = "Cybersecurity Validation API - Vercel"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "vercel-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # API Key Authentication (simplified)
    VALID_API_KEYS: Dict[str, Dict[str, Any]] = {
        "default": {"key": "vercel-api-key-123", "name": "Default API Key", "admin": False},
        "demo": {"key": "demo-api-key-456", "name": "Demo API Key", "admin": True}
    }
    
    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Cache Settings (simplified, no Redis)
    CACHE_ENABLED: bool = True
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_SHORT: int = 60     # 1 minute
    CACHE_TTL_LONG: int = 86400   # 24 hours
    
    # External API Keys (optional, for enhanced features)
    VIRUSTOTAL_API_KEY: Optional[str] = os.getenv("VIRUSTOTAL_API_KEY")
    ABUSEIPDB_API_KEY: Optional[str] = os.getenv("ABUSEIPDB_API_KEY")
    SHODAN_API_KEY: Optional[str] = os.getenv("SHODAN_API_KEY")
    GREYNOISE_API_KEY: Optional[str] = os.getenv("GREYNOISE_API_KEY")
    OTX_API_KEY: Optional[str] = os.getenv("OTX_API_KEY")
    
    # Validation Rules
    MAX_BULK_VALIDATION_ITEMS: int = 100  # Reduced for serverless
    MIN_DOMAIN_LENGTH: int = 3
    MAX_DOMAIN_LENGTH: int = 253
    MIN_IP_LENGTH: int = 7
    MAX_IP_LENGTH: int = 45
    
    # Logging Settings (simplified for serverless)
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Rate Limiting (simplified for serverless)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100  # Reduced for serverless constraints
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("VALID_API_KEYS", pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from JSON string or dictionary."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback for simple string format
                return {
                    "default": {"key": v, "name": "Default API Key", "admin": False}
                }
        return v


# Global settings instance
settings = Settings()
