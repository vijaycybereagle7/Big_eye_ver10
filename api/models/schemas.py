"""Database models and schemas for the cybersecurity validation API."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, validator
import uuid


# Base response models
class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Validation Models
class ValidationRequest(BaseModel):
    """Base validation request model."""
    async_mode: bool = False


class EmailValidationRequest(ValidationRequest):
    """Email validation request."""
    email: EmailStr
    verify_syntax: bool = True
    verify_mx_record: bool = True
    check_disposable: bool = True


class DomainValidationRequest(ValidationRequest):
    """Domain validation request."""
    domain: str
    check_dns: bool = True
    check_whois: bool = False
    check_reputation: bool = True


class IPValidationRequest(ValidationRequest):
    """IP validation request."""
    ip_address: str
    check_reputation: bool = True
    check_geolocation: bool = True


class URLValidationRequest(ValidationRequest):
    """URL validation request."""
    url: str
    check_safety: bool = True
    check_reputation: bool = True
    follow_redirects: bool = True


class SenderValidationRequest(ValidationRequest):
    """Sender validation request (email + domain)."""
    email: EmailStr
    domain: str
    check_spf: bool = True
    check_dkim: bool = True
    check_dmarc: bool = True


class BulkValidationRequest(ValidationRequest):
    """Bulk validation request."""
    emails: Optional[List[EmailStr]] = None
    domains: Optional[List[str]] = None
    ip_addresses: Optional[List[str]] = None
    urls: Optional[List[str]] = None
    senders: Optional[List[Dict[str, Any]]] = None


# Validation Results Models
class ValidationResult(BaseModel):
    """Individual validation result."""
    value: str
    is_valid: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_details: Dict[str, Any] = {}
    threats: List[str] = []
    reputation_score: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmailValidationResult(ValidationResult):
    """Email validation result with specific fields."""
    domain_exists: bool = False
    mx_record_exists: bool = False
    is_disposable: bool = False
    is_role_account: bool = False
    is_trash: bool = False
    suggestions: List[str] = []


class DomainValidationResult(ValidationResult):
    """Domain validation result with specific fields."""
    dns_resolves: bool = False
    is_parked: bool = False
    is_squatted: bool = False
    registration_age_days: Optional[int] = None
    expires_at: Optional[datetime] = None
    registrar: Optional[str] = None
    nameservers: List[str] = []


class IPValidationResult(ValidationResult):
    """IP validation result with specific fields."""
    ip_version: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    organization: Optional[str] = None
    is_proxy: bool = False
    is_vpn: bool = False
    is_tor: bool = False
    is_datacenter: bool = False


class URLValidationResult(ValidationResult):
    """URL validation result with specific fields."""
    final_url: Optional[str] = None
    response_status: Optional[int] = None
    content_type: Optional[str] = None
    page_title: Optional[str] = None
    is_malicious: bool = False
    is_phishing: bool = False
    is_suspicious: bool = False
    threat_categories: List[str] = []


class SenderValidationResult(ValidationResult):
    """Sender validation result with specific fields."""
    spf_pass: bool = False
    dkim_pass: bool = False
    dmarc_pass: bool = False
    spf_record: Optional[str] = None
    dkim_record: Optional[str] = None
    dmarc_record: Optional[str] = None


class BulkValidationResponse(BaseResponse):
    """Bulk validation response."""
    total_items: int
    valid_items: int
    invalid_items: int
    results: List[ValidationResult]
    processing_time_ms: Optional[float] = None


# Individual validation responses
class ValidationResponse(BaseResponse):
    """Generic validation response."""
    result: ValidationResult


# Reputation Models
class ReputationQueryRequest(BaseModel):
    """Reputation query request."""
    value: str
    sources: Optional[List[str]] = None
    detailed: bool = False


class ReputationSource(BaseModel):
    """Reputation source information."""
    name: str
    score: Optional[float] = None
    verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class ReputationResult(BaseModel):
    """Reputation query result."""
    value: str
    value_type: str
    overall_score: float = Field(ge=0.0, le=1.0)
    overall_verdict: str
    sources: List[ReputationSource]
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_reports: int = 0
    categories: List[str] = []


class ReputationResponse(BaseResponse):
    """Reputation query response."""
    result: ReputationResult


# Threat Intelligence Models
class ThreatQueryRequest(BaseModel):
    """Threat intelligence query request."""
    value: str
    query_type: str  # "ip", "domain", "url", "hash"
    include_context: bool = True
    include_related: bool = True
    time_range_days: int = 30


class ThreatIntel(BaseModel):
    """Threat intelligence data."""
    indicator: str
    indicator_type: str
    threat_types: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str
    description: str
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    tags: List[str] = []
    references: List[str] = []
    malware_families: List[str] = []
    attribution: Optional[str] = None


class ThreatContext(BaseModel):
    """Threat context information."""
    geographical_data: Dict[str, Any] = {}
    network_data: Dict[str, Any] = {}
    behavioral_data: Dict[str, Any] = {}
    historical_data: Dict[str, Any] = {}


class ThreatIntelligenceResult(BaseModel):
    """Threat intelligence query result."""
    indicator: str
    indicator_type: str
    intelligence: List[ThreatIntel]
    context: Optional[ThreatContext] = None
    related_indicators: List[str] = []
    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_level: str


class ThreatIntelligenceResponse(BaseResponse):
    """Threat intelligence query response."""
    result: ThreatIntelligenceResult


# Admin Models
class APIKeyInfo(BaseModel):
    """API key information."""
    key_id: str
    name: str
    is_admin: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    request_count: int = 0
    rate_limit: int = 0


class APIKeyCreate(BaseModel):
    """API key creation request."""
    name: str
    is_admin: bool = False
    rate_limit: Optional[int] = None


class APIKeyResponse(BaseResponse):
    """API key response."""
    api_key: str
    key_info: APIKeyInfo


class AdminStats(BaseModel):
    """Admin statistics."""
    total_requests: int
    valid_requests: int
    invalid_requests: int
    cached_requests: int
    active_api_keys: int
    top_queried_values: List[Dict[str, Any]]
    recent_threats: List[Dict[str, Any]]
    system_health: Dict[str, Any]


class AdminDashboardResponse(BaseResponse):
    """Admin dashboard response."""
    stats: AdminStats
    api_keys: List[APIKeyInfo]


# Database Models (for ORM)
class ValidationLog(BaseModel):
    """Validation log database model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    api_key: str
    endpoint: str
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    success: bool
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class CachedResult(BaseModel):
    """Cached result database model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cache_key: str
    value_type: str
    result_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class ThreatIntelDB(BaseModel):
    """Threat intelligence database model."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    indicator: str
    indicator_type: str
    threat_data: Dict[str, Any]
    source: str
    confidence: float
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Error Models
class APIError(BaseModel):
    """API error model."""
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """Error response model."""
    error: APIError


# Pagination Models
class PaginatedResponse(BaseResponse):
    """Paginated response model."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


# Search Models
class SearchRequest(BaseModel):
    """Search request model."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 20