"""Simplified Pydantic models for Vercel-optimized cybersecurity API."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime


class APIError(BaseModel):
    """API error details."""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = False
    message: str
    error: Optional[APIError] = None
    timestamp: datetime = datetime.utcnow()


class ValidationResult(BaseModel):
    """Individual validation result."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    confidence: str  # low, medium, high
    checks: Dict[str, Any]
    message: Optional[str] = None


class EmailValidationRequest(BaseModel):
    """Email validation request."""
    email: EmailStr
    verify_syntax: bool = True
    verify_mx_record: bool = False
    check_disposable: bool = True


class EmailValidationResult(ValidationResult):
    """Email validation result."""
    email: str
    domain: Optional[str] = None
    mx_records: Optional[List[str]] = None
    is_disposable: bool = False
    provider: Optional[str] = None


class DomainValidationRequest(BaseModel):
    """Domain validation request."""
    domain: str
    
    @validator('domain')
    def validate_domain_format(cls, v):
        """Validate domain format."""
        if len(v) < 3 or len(v) > 253:
            raise ValueError("Domain length must be between 3 and 253 characters")
        
        if not v.replace('-', '').replace('.', '').isalnum():
            raise ValueError("Domain contains invalid characters")
        
        return v.lower()


class DomainValidationResult(ValidationResult):
    """Domain validation result."""
    domain: str
    is_active: bool = False
    expires_at: Optional[datetime] = None
    registrar: Optional[str] = None
    nameservers: Optional[List[str]] = None


class IPValidationRequest(BaseModel):
    """IP address validation request."""
    ip: str
    
    @validator('ip')
    def validate_ip_format(cls, v):
        """Validate IP address format."""
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError("Invalid IP address format")


class IPValidationResult(ValidationResult):
    """IP address validation result."""
    ip: str
    ip_type: str  # IPv4, IPv6
    is_private: bool = False
    is_reserved: bool = False
    geolocation: Optional[Dict[str, Any]] = None


class URLValidationRequest(BaseModel):
    """URL validation request."""
    url: str
    
    @validator('url')
    def validate_url_format(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class URLValidationResult(ValidationResult):
    """URL validation result."""
    url: str
    domain: Optional[str] = None
    is_https: bool = False
    is_suspicious: bool = False
    threat_indicators: Optional[List[str]] = None


class BulkValidationRequest(BaseModel):
    """Bulk validation request."""
    items: List[Union[str, Dict[str, Any]]]
    validation_type: str  # email, domain, ip, url
    async_mode: bool = False  # Disabled in serverless
    
    @validator('items')
    def validate_items_count(cls, v):
        """Validate items count."""
        if len(v) > 100:  # Reduced limit for serverless
            raise ValueError("Maximum 100 items allowed per bulk request")
        return v


class ValidationResponse(BaseModel):
    """Standard validation response."""
    success: bool
    message: str
    result: Union[
        EmailValidationResult,
        DomainValidationResult,
        IPValidationResult,
        URLValidationResult,
        List[ValidationResult]
    ]
    timestamp: datetime = datetime.utcnow()


class ReputationResult(BaseModel):
    """Reputation query result."""
    value: str
    value_type: str
    reputation_score: float  # 0.0 (clean) to 1.0 (malicious)
    threat_level: str  # low, medium, high, critical
    sources: Dict[str, Any]
    last_seen: Optional[datetime] = None
    indicators: Optional[List[str]] = None


class ReputationQueryRequest(BaseModel):
    """Reputation query request."""
    value: str
    value_type: str  # ip, domain, url, hash, email
    
    @validator('value_type')
    def validate_value_type(cls, v):
        """Validate value type."""
        allowed_types = ['ip', 'domain', 'url', 'hash', 'email']
        if v not in allowed_types:
            raise ValueError(f"Value type must be one of: {', '.join(allowed_types)}")
        return v


class ReputationResponse(BaseModel):
    """Reputation query response."""
    success: bool
    message: str
    result: ReputationResult
    timestamp: datetime = datetime.utcnow()


class APIKeyInfo(BaseModel):
    """API key information."""
    key_id: str
    key: str
    name: str
    admin: bool = False
    usage_count: int = 0


# Health check response
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str
    timestamp: datetime
    debug: bool = False
    supabase_connected: bool = False


# Root endpoint response
class RootResponse(BaseModel):
    """Root endpoint response."""
    service: str
    version: str
    description: str
    endpoints: Dict[str, str]
    timestamp: datetime
    supabase_enabled: bool = True
    serverless_mode: bool = True
