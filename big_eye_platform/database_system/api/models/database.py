"""SQLAlchemy database models for PostgreSQL."""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

from ..database.connections import PostgresBase


class ValidationLogDB(PostgresBase):
    """Database model for validation logs."""
    __tablename__ = "validation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_data = Column(JSON, nullable=False)
    response_data = Column(JSON, nullable=False)
    success = Column(Boolean, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_validation_logs_api_key_timestamp', 'api_key', 'timestamp'),
        Index('idx_validation_logs_endpoint_timestamp', 'endpoint', 'timestamp'),
        Index('idx_validation_logs_success_timestamp', 'success', 'timestamp'),
    )


class APIKeyDB(PostgresBase):
    """Database model for API keys."""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_used = Column(DateTime(timezone=True))
    request_count = Column(Integer, default=0, nullable=False)
    rate_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_admin', 'is_admin'),
    )


class ThreatIntelDB(PostgresBase):
    """Database model for threat intelligence data."""
    __tablename__ = "threat_intel"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator = Column(String(255), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False, index=True)
    threat_data = Column(JSON, nullable=False)
    source = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_intel_indicator_type', 'indicator', 'indicator_type'),
        Index('idx_threat_intel_source_confidence', 'source', 'confidence'),
        Index('idx_threat_intel_last_seen', 'last_seen'),
    )


class CachedResultDB(PostgresBase):
    """Database model for cached validation results."""
    __tablename__ = "cached_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    value_type = Column(String(50), nullable=False, index=True)
    result_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    access_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True))
    
    # Indexes
    __table_args__ = (
        Index('idx_cached_results_expires', 'expires_at'),
        Index('idx_cached_results_type', 'value_type'),
    )


class SystemStatsDB(PostgresBase):
    """Database model for system statistics."""
    __tablename__ = "system_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stat_date = Column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    total_requests = Column(Integer, default=0)
    valid_requests = Column(Integer, default=0)
    invalid_requests = Column(Integer, default=0)
    cached_requests = Column(Integer, default=0)
    unique_api_keys = Column(Integer, default=0)
    unique_values_queried = Column(Integer, default=0)
    threat_reports = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


class ReputationCacheDB(PostgresBase):
    """Database model for reputation data cache."""
    __tablename__ = "reputation_cache"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    value = Column(String(255), nullable=False, index=True)
    value_type = Column(String(50), nullable=False)
    reputation_sources = Column(JSON, nullable=False)
    overall_score = Column(Float, nullable=False)
    overall_verdict = Column(String(50), nullable=False)
    metadata = Column(JSON)
    first_seen = Column(DateTime(timezone=True))
    last_seen = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_reputation_value_type', 'value', 'value_type'),
        Index('idx_reputation_verdict_score', 'overall_verdict', 'overall_score'),
    )


class ErrorLogDB(PostgresBase):
    """Database model for error logging."""
    __tablename__ = "error_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    error_code = Column(String(50), nullable=False, index=True)
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON)
    api_key = Column(String(255), index=True)
    endpoint = Column(String(255), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_error_logs_code_timestamp', 'error_code', 'timestamp'),
        Index('idx_error_logs_api_key_timestamp', 'api_key', 'timestamp'),
    )


class RateLimitLogDB(PostgresBase):
    """Database model for rate limiting logs."""
    __tablename__ = "rate_limit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key = Column(String(255), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    requests_count = Column(Integer, nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    blocked = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_rate_limit_api_key_window', 'api_key', 'window_start', 'window_end'),
    )


class ThreatFeedDB(PostgresBase):
    """Database model for threat feed data."""
    __tablename__ = "threat_feeds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_name = Column(String(100), nullable=False, index=True)
    feed_type = Column(String(50), nullable=False)
    indicator = Column(String(255), nullable=False)
    indicator_type = Column(String(50), nullable=False)
    threat_data = Column(JSON, nullable=False)
    feed_url = Column(Text)
    last_updated = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    is_active = Column(Boolean, default=True, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_threat_feeds_indicator_type', 'indicator', 'indicator_type'),
        Index('idx_threat_feeds_feed_name_updated', 'feed_name', 'last_updated'),
    )