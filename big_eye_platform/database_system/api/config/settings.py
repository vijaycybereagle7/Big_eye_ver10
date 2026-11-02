"""Application configuration and settings."""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    APP_NAME: str = "Cybersecurity Validation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # API Key Authentication
    VALID_API_KEYS: Dict[str, Dict[str, Any]] = {
        "default": {"key": "default-api-key-123", "name": "Default API Key", "admin": False},
        "admin": {"key": "admin-api-key-456", "name": "Admin API Key", "admin": True}
    }
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    RATE_LIMIT_ADMIN_REQUESTS: int = 1000
    
    # Database Settings
    # PostgreSQL
    POSTGRESQL_URL: str = os.getenv(
        "POSTGRESQL_URL", 
        "postgresql://user:password@localhost/cybersec_db"
    )
    
    # MongoDB
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL", 
        "mongodb://localhost:27017"
    )
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "cybersec_db")
    
    # Redis Settings
    REDIS_URL: str = os.getenv(
        "REDIS_URL", 
        "redis://localhost:6379/0"
    )
    REDIS_TTL: int = 3600  # 1 hour
    
    # External API Keys
    VIRUSTOTAL_API_KEY: Optional[str] = os.getenv("VIRUSTOTAL_API_KEY")
    ABUSEIPDB_API_KEY: Optional[str] = os.getenv("ABUSEIPDB_API_KEY")
    SHODAN_API_KEY: Optional[str] = os.getenv("SHODAN_API_KEY")
    GREYNOISE_API_KEY: Optional[str] = os.getenv("GREYNOISE_API_KEY")
    OTX_API_KEY: Optional[str] = os.getenv("OTX_API_KEY")
    URLHAUS_API_KEY: Optional[str] = os.getenv("URLHAUS_API_KEY")
    SECURITYTRAILS_API_KEY: Optional[str] = os.getenv("SECURITYTRAILS_API_KEY")
    
    # Email Validation Settings
    EMAIL_VALIDATION_API_KEY: Optional[str] = os.getenv("EMAIL_VALIDATION_API_KEY")
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER")
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "api/logs/app.log")
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # Cache Settings
    CACHE_ENABLED: bool = True
    CACHE_TTL_DEFAULT: int = 300  # 5 minutes
    CACHE_TTL_SHORT: int = 60     # 1 minute
    CACHE_TTL_LONG: int = 86400   # 24 hours
    
    # Validation Rules
    MAX_BULK_VALIDATION_ITEMS: int = 1000
    MIN_DOMAIN_LENGTH: int = 3
    MAX_DOMAIN_LENGTH: int = 253
    MIN_IP_LENGTH: int = 7
    MAX_IP_LENGTH: int = 45
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("VALID_API_KEYS", pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from JSON string or dictionary."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


settings = Settings()