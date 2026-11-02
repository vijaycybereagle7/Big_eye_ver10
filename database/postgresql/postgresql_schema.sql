-- ==============================================================================
-- PostgreSQL Security Intelligence Schema
-- ==============================================================================
-- Description: Complete schema for security intelligence and threat detection
--              tables including domains, IPs, emails, threats, and ML predictions
-- Author: MiniMax Agent
-- Created: 2025-10-30
-- Version: 1.0
-- ==============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";
CREATE EXTENSION IF NOT EXISTS "ip4r";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==============================================================================
-- ENUMS AND CUSTOM TYPES
-- ==============================================================================

-- Domain threat types
CREATE TYPE domain_threat_type AS ENUM (
    'malware',
    'phishing',
    'spam',
    'botnet',
    'c_and_c',
    'exfiltration',
    'suspicious',
    'legitimate',
    'unknown'
);

-- IP address threat types
CREATE TYPE ip_threat_type AS ENUM (
    'malware',
    'botnet',
    'spam',
    'ddos',
    'scanner',
    'exfiltration',
    'brute_force',
    'suspicious',
    'legitimate',
    'unknown'
);

-- Email validation status
CREATE TYPE email_validation_status AS ENUM (
    'valid',
    'invalid',
    'disposable',
    'role_account',
    'free_provider',
    'mx_record_missing',
    'timeout',
    'error'
);

-- Threat severity levels
CREATE TYPE threat_severity AS ENUM (
    'low',
    'medium',
    'high',
    'critical'
);

-- Threat confidence levels
CREATE TYPE confidence_level AS ENUM (
    'very_low',
    'low',
    'medium',
    'high',
    'very_high'
);

-- Campaign status types
CREATE TYPE campaign_status AS ENUM (
    'active',
    'contained',
    'resolved',
    'investigating'
);

-- Model prediction status
CREATE TYPE prediction_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed'
);

-- ==============================================================================
-- THREAT FEED SOURCES TABLE
-- ==============================================================================
-- Purpose: Store information about threat intelligence feed sources
CREATE TABLE threat_feed_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic source information
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    url TEXT,
    api_endpoint TEXT,
    api_key_encrypted TEXT,
    
    -- Source characteristics
    source_type TEXT NOT NULL CHECK (source_type IN ('commercial', 'free', 'government', 'research', 'community')),
    data_format TEXT NOT NULL CHECK (data_format IN ('stix', 'json', 'csv', 'xml', 'csv', 'yaml')),
    update_frequency INTERVAL NOT NULL DEFAULT '24 hours',
    
    -- Status and reliability
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    reliability_score NUMERIC(3,2) CHECK (reliability_score >= 0.0 AND reliability_score <= 1.0),
    last_updated TIMESTAMPTZ,
    last_successful_update TIMESTAMPTZ,
    
    -- Contact information
    contact_email TEXT,
    contact_person TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    updated_by TEXT
);

-- Indexes for threat_feed_sources
CREATE INDEX idx_threat_feed_sources_name ON threat_feed_sources(name);
CREATE INDEX idx_threat_feed_sources_active ON threat_feed_sources(is_active);
CREATE INDEX idx_threat_feed_sources_type ON threat_feed_sources(source_type);
CREATE INDEX idx_threat_feed_sources_last_updated ON threat_feed_sources(last_successful_update);

-- ==============================================================================
-- DOMAINS INTELLIGENCE TABLE
-- ==============================================================================
-- Purpose: Store domain reputation and threat intelligence data
CREATE TABLE domains_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Domain identification
    domain TEXT NOT NULL UNIQUE,
    registrable_domain TEXT NOT NULL,
    apex_domain TEXT NOT NULL,
    
    -- Threat intelligence data
    threat_type domain_threat_type NOT NULL,
    threat_severity threat_severity NOT NULL,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Reputation metrics
    reputation_score NUMERIC(3,2) CHECK (reputation_score >= 0.0 AND reputation_score <= 1.0),
    age_days INTEGER CHECK (age_days >= 0),
    alexa_rank INTEGER,
    suspicious_score NUMERIC(3,2) CHECK (suspicious_score >= 0.0 AND suspicious_score <= 1.0),
    
    -- Domain characteristics
    is_parked BOOLEAN DEFAULT FALSE,
    has_dmarc BOOLEAN DEFAULT FALSE,
    has_spf BOOLEAN DEFAULT FALSE,
    has_dkim BOOLEAN DEFAULT FALSE,
    
    -- WHOIS data
    registrar TEXT,
    registrant_name TEXT,
    registrant_email TEXT,
    creation_date TIMESTAMPTZ,
    expiration_date TIMESTAMPTZ,
    
    -- Technical details
    ssl_certificate TEXT,
    nameservers TEXT[],
    ip_addresses INET[],
    
    -- Source and classification
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE SET NULL,
    tags TEXT[],
    categories TEXT[],
    
    -- Classification flags
    is_malicious BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    is_whitelisted BOOLEAN DEFAULT FALSE,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    
    -- Analysis data
    malware_samples TEXT[],
    phishing_campaigns TEXT[],
    spam_triggers TEXT[],
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_domain CHECK (domain ~* '^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$'),
    CONSTRAINT valid_registrable_domain CHECK (registrable_domain IS NOT NULL AND registrable_domain != ''),
    CONSTRAINT apex_domain_matches CHECK (apex_domain IS NOT NULL AND apex_domain != '')
);

-- Indexes for domains_intelligence
CREATE INDEX idx_domains_intelligence_domain ON domains_intelligence(domain);
CREATE INDEX idx_domains_intelligence_registrable ON domains_intelligence(registrable_domain);
CREATE INDEX idx_domains_intelligence_threat_type ON domains_intelligence(threat_type);
CREATE INDEX idx_domains_intelligence_severity ON domains_intelligence(threat_severity);
CREATE INDEX idx_domains_intelligence_score ON domains_intelligence(confidence_score DESC);
CREATE INDEX idx_domains_intelligence_reputation ON domains_intelligence(reputation_score DESC);
CREATE INDEX idx_domains_intelligence_malicious ON domains_intelligence(is_malicious) WHERE is_malicious = TRUE;
CREATE INDEX idx_domains_intelligence_suspicious ON domains_intelligence(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_domains_intelligence_first_seen ON domains_intelligence(first_seen DESC);
CREATE INDEX idx_domains_intelligence_last_seen ON domains_intelligence(last_seen DESC);
CREATE INDEX idx_domains_intelligence_tags ON domains_intelligence USING GIN(tags);
CREATE INDEX idx_domains_intelligence_categories ON domains_intelligence USING GIN(categories);
CREATE INDEX idx_domains_intelligence_apex_domain ON domains_intelligence(apex_domain);

-- ==============================================================================
-- IP ADDRESSES REPUTATION TABLE
-- ==============================================================================
-- Purpose: Store IP address reputation and threat intelligence data
CREATE TABLE ip_addresses_reputation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- IP identification
    ip_address INET NOT NULL UNIQUE,
    ip_range CIDR,
    
    -- Threat intelligence
    threat_type ip_threat_type NOT NULL,
    threat_severity threat_severity NOT NULL,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Reputation metrics
    reputation_score NUMERIC(3,2) CHECK (reputation_score >= 0.0 AND reputation_score <= 1.0),
    suspicious_score NUMERIC(3,2) CHECK (suspicious_score >= 0.0 AND suspicious_score <= 1.0),
    
    -- Geographic data
    country_code CHAR(2),
    country_name TEXT,
    city TEXT,
    latitude NUMERIC(10,8),
    longitude NUMERIC(11,8),
    
    -- Network information
    asn INTEGER,
    as_name TEXT,
    isp_name TEXT,
    organization TEXT,
    is_hosting_provider BOOLEAN DEFAULT FALSE,
    
    -- Behavioral analysis
    is_proxy BOOLEAN DEFAULT FALSE,
    is_vpn BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_datacenter BOOLEAN DEFAULT FALSE,
    is_mobile BOOLEAN DEFAULT FALSE,
    
    -- Security analysis
    open_ports INTEGER[],
    vulnerabilities TEXT[],
    malware_activity INTEGER DEFAULT 0,
    spam_activity INTEGER DEFAULT 0,
    
    -- Source and classification
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE SET NULL,
    tags TEXT[],
    categories TEXT[],
    
    -- Classification flags
    is_malicious BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    is_whitelisted BOOLEAN DEFAULT FALSE,
    is_blacklisted BOOLEAN DEFAULT FALSE,
    
    -- Traffic analysis
    packet_count BIGINT DEFAULT 0,
    byte_count BIGINT DEFAULT 0,
    protocol_distribution JSONB,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_ip_address CHECK (ip_address IS NOT NULL)
);

-- Indexes for ip_addresses_reputation
CREATE INDEX idx_ip_addresses_reputation_ip ON ip_addresses_reputation(ip_address);
CREATE INDEX idx_ip_addresses_reputation_range ON ip_addresses_reputation USING GIST(ip_range) WHERE ip_range IS NOT NULL;
CREATE INDEX idx_ip_addresses_reputation_threat_type ON ip_addresses_reputation(threat_type);
CREATE INDEX idx_ip_addresses_reputation_severity ON ip_addresses_reputation(threat_severity);
CREATE INDEX idx_ip_addresses_reputation_score ON ip_addresses_reputation(confidence_score DESC);
CREATE INDEX idx_ip_addresses_reputation_malicious ON ip_addresses_reputation(is_malicious) WHERE is_malicious = TRUE;
CREATE INDEX idx_ip_addresses_reputation_suspicious ON ip_addresses_reputation(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_ip_addresses_reputation_asn ON ip_addresses_reputation(asn) WHERE asn IS NOT NULL;
CREATE INDEX idx_ip_addresses_reputation_country ON ip_addresses_reputation(country_code);
CREATE INDEX idx_ip_addresses_reputation_first_seen ON ip_addresses_reputation(first_seen DESC);
CREATE INDEX idx_ip_addresses_reputation_last_seen ON ip_addresses_reputation(last_seen DESC);
CREATE INDEX idx_ip_addresses_reputation_tags ON ip_addresses_reputation USING GIN(tags);
CREATE INDEX idx_ip_addresses_reputation_categories ON ip_addresses_reputation USING GIN(categories);

-- ==============================================================================
-- EMAIL ADDRESSES VALIDATION TABLE
-- ==============================================================================
-- Purpose: Store email address validation and verification data
CREATE TABLE email_addresses_validation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Email identification
    email CITEXT NOT NULL UNIQUE,
    local_part TEXT NOT NULL,
    domain_part TEXT NOT NULL,
    
    -- Validation results
    validation_status email_validation_status NOT NULL,
    is_valid_syntax BOOLEAN NOT NULL,
    is_valid_domain BOOLEAN NOT NULL,
    is_valid_mx_record BOOLEAN NOT NULL,
    
    -- SMTP validation
    smtp_validation_performed BOOLEAN DEFAULT FALSE,
    smtp_response_code INTEGER,
    smtp_response_text TEXT,
    smtp_has_fake_user BOOLEAN,
    
    -- Risk assessment
    risk_score NUMERIC(3,2) CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Email characteristics
    is_disposable BOOLEAN DEFAULT FALSE,
    is_role_account BOOLEAN DEFAULT FALSE,
    is_catch_all BOOLEAN DEFAULT FALSE,
    is_free_provider BOOLEAN DEFAULT FALSE,
    is_corporate BOOLEAN DEFAULT FALSE,
    
    -- Domain analysis
    domain_age_days INTEGER,
    domain_reputation_score NUMERIC(3,2),
    has_valid_spf BOOLEAN DEFAULT FALSE,
    has_valid_dkim BOOLEAN DEFAULT FALSE,
    has_valid_dmarc BOOLEAN DEFAULT FALSE,
    
    -- Additional checks
    mx_records TEXT[],
    spf_record TEXT,
    dkim_selector TEXT,
    dkim_public_key TEXT,
    dmarc_policy TEXT,
    
    -- Validation metadata
    validation_method TEXT NOT NULL,
    validation_details JSONB,
    error_message TEXT,
    
    -- Source tracking
    source_type TEXT NOT NULL CHECK (source_type IN ('api', 'manual', 'import', 'event')),
    source_reference TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    validated_at TIMESTAMPTZ,
    validation_expires_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT valid_email_syntax CHECK (email ~* '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'),
    CONSTRAINT local_part_present CHECK (local_part IS NOT NULL AND local_part != ''),
    CONSTRAINT domain_part_present CHECK (domain_part IS NOT NULL AND domain_part != ''),
    CONSTRAINT email_domain_consistency CHECK (email = local_part || '@' || domain_part)
);

-- Indexes for email_addresses_validation
CREATE INDEX idx_email_addresses_validation_email ON email_addresses_validation(email);
CREATE INDEX idx_email_addresses_validation_domain ON email_addresses_validation(domain_part);
CREATE INDEX idx_email_addresses_validation_status ON email_addresses_validation(validation_status);
CREATE INDEX idx_email_addresses_validation_valid_syntax ON email_addresses_validation(is_valid_syntax);
CREATE INDEX idx_email_addresses_validation_valid_mx ON email_addresses_validation(is_valid_mx_record);
CREATE INDEX idx_email_addresses_validation_risk_score ON email_addresses_validation(risk_score DESC);
CREATE INDEX idx_email_addresses_validation_confidence ON email_addresses_validation(confidence_score DESC);
CREATE INDEX idx_email_addresses_validation_disposable ON email_addresses_validation(is_disposable) WHERE is_disposable = TRUE;
CREATE INDEX idx_email_addresses_validation_role_account ON email_addresses_validation(is_role_account) WHERE is_role_account = TRUE;
CREATE INDEX idx_email_addresses_validation_corporate ON email_addresses_validation(is_corporate) WHERE is_corporate = TRUE;
CREATE INDEX idx_email_addresses_validation_validated_at ON email_addresses_validation(validated_at DESC);
CREATE INDEX idx_email_addresses_validation_source_type ON email_addresses_validation(source_type);
CREATE INDEX idx_email_addresses_validation_local_part ON email_addresses_validation(local_part);

-- ==============================================================================
-- SENDER REPUTATION SCORING TABLE
-- ==============================================================================
-- Purpose: Store sender reputation scores and metrics
CREATE TABLE sender_reputation_scoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Sender identification
    sender_identifier TEXT NOT NULL,
    identifier_type TEXT NOT NULL CHECK (identifier_type IN ('email', 'ip', 'domain', 'combined')),
    
    -- Email identification (when applicable)
    email_address CITEXT,
    ip_address INET,
    domain TEXT,
    
    -- Reputation metrics
    overall_reputation_score NUMERIC(3,2) CHECK (overall_reputation_score >= 0.0 AND overall_reputation_score <= 1.0),
    spam_score NUMERIC(3,2) CHECK (spam_score >= 0.0 AND spam_score <= 1.0),
    phishing_score NUMERIC(3,2) CHECK (phishing_score >= 0.0 AND phishing_score <= 1.0),
    malware_score NUMERIC(3,2) CHECK (malware_score >= 0.0 AND malware_score <= 1.0),
    
    -- Behavioral metrics
    email_volume_score NUMERIC(3,2) CHECK (email_volume_score >= 0.0 AND email_volume_score <= 1.0),
    bounce_rate NUMERIC(5,4) CHECK (bounce_rate >= 0.0 AND bounce_rate <= 1.0),
    complaint_rate NUMERIC(5,4) CHECK (complaint_rate >= 0.0 AND complaint_rate <= 1.0),
    engagement_rate NUMERIC(5,4) CHECK (engagement_rate >= 0.0 AND engagement_rate <= 1.0),
    
    -- Time-based analysis
    recent_activity_score NUMERIC(3,2) CHECK (recent_activity_score >= 0.0 AND recent_activity_score <= 1.0),
    consistency_score NUMERIC(3,2) CHECK (consistency_score >= 0.0 AND consistency_score <= 1.0),
    growth_rate NUMERIC(5,4) CHECK (growth_rate >= -1.0 AND growth_rate <= 1.0),
    
    -- Historical data
    first_email_date TIMESTAMPTZ,
    last_email_date TIMESTAMPTZ,
    total_emails_sent BIGINT DEFAULT 0,
    total_bounces INTEGER DEFAULT 0,
    total_complaints INTEGER DEFAULT 0,
    
    -- ML model features
    feature_vector JSONB,
    model_version TEXT,
    prediction_confidence NUMERIC(3,2),
    
    -- Classification
    reputation_level TEXT CHECK (reputation_level IN ('excellent', 'good', 'fair', 'poor', 'very_poor')),
    is_trusted BOOLEAN DEFAULT FALSE,
    is_flagged BOOLEAN DEFAULT FALSE,
    
    -- Source and context
    analysis_source TEXT NOT NULL,
    analysis_context JSONB,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_calculated TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT sender_identifier_present CHECK (sender_identifier IS NOT NULL AND sender_identifier != ''),
    CONSTRAINT identifier_type_consistency CHECK (
        (identifier_type = 'email' AND email_address IS NOT NULL) OR
        (identifier_type = 'ip' AND ip_address IS NOT NULL) OR
        (identifier_type = 'domain' AND domain IS NOT NULL) OR
        (identifier_type = 'combined' AND email_address IS NOT NULL AND ip_address IS NOT NULL AND domain IS NOT NULL)
    )
);

-- Indexes for sender_reputation_scoring
CREATE INDEX idx_sender_reputation_sender_identifier ON sender_reputation_scoring(sender_identifier);
CREATE INDEX idx_sender_reputation_identifier_type ON sender_reputation_scoring(identifier_type);
CREATE INDEX idx_sender_reputation_email ON sender_reputation_scoring(email_address) WHERE email_address IS NOT NULL;
CREATE INDEX idx_sender_reputation_ip ON sender_reputation_scoring(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX idx_sender_reputation_domain ON sender_reputation_scoring(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_sender_reputation_overall_score ON sender_reputation_scoring(overall_reputation_score DESC);
CREATE INDEX idx_sender_reputation_spam_score ON sender_reputation_scoring(spam_score DESC);
CREATE INDEX idx_sender_reputation_phishing_score ON sender_reputation_scoring(phishing_score DESC);
CREATE INDEX idx_sender_reputation_malware_score ON sender_reputation_scoring(malware_score DESC);
CREATE INDEX idx_sender_reputation_reputation_level ON sender_reputation_scoring(reputation_level);
CREATE INDEX idx_sender_reputation_trusted ON sender_reputation_scoring(is_trusted) WHERE is_trusted = TRUE;
CREATE INDEX idx_sender_reputation_flagged ON sender_reputation_scoring(is_flagged) WHERE is_flagged = TRUE;
CREATE INDEX idx_sender_reputation_last_calculated ON sender_reputation_scoring(last_calculated DESC);
CREATE INDEX idx_sender_reputation_total_emails ON sender_reputation_scoring(total_emails_sent DESC);

-- ==============================================================================
-- THREAT INTELLIGENCE INDICATORS TABLE
-- ==============================================================================
-- Purpose: Store Indicators of Compromise (IOCs) from threat intelligence feeds
CREATE TABLE threat_intelligence_indicators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Indicator identification
    indicator_value TEXT NOT NULL,
    indicator_type TEXT NOT NULL CHECK (indicator_type IN ('ip', 'domain', 'url', 'email', 'hash', 'filename', 'certificate', 'registry_key')),
    
    -- Specific values based on type
    ip_address INET,
    domain_name TEXT,
    url TEXT,
    email_address CITEXT,
    file_hash TEXT,
    filename TEXT,
    certificate_fingerprint TEXT,
    registry_key TEXT,
    
    -- Threat information
    threat_name TEXT NOT NULL,
    threat_family TEXT,
    threat_category TEXT NOT NULL CHECK (threat_category IN ('malware', 'apt', 'botnet', 'phishing', 'spam', 'scam', 'fraud', 'spyware', 'ransomware')),
    threat_severity threat_severity NOT NULL,
    
    -- Indicator properties
    confidence_level confidence_level NOT NULL,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    threat_score NUMERIC(3,2) CHECK (threat_score >= 0.0 AND threat_score <= 1.0),
    
    -- TTP information
    attack_technique TEXT,
    kill_chain_phase TEXT CHECK (kill_chain_phase IN ('reconnaissance', 'weaponization', 'delivery', 'exploitation', 'installation', 'command_control', 'actions_objectives')),
    
    -- Context and attribution
    attribution_group TEXT,
    campaign_name TEXT,
    infrastructure_notes TEXT,
    usage_context TEXT,
    
    -- Technical details
    first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    expiration_time TIMESTAMPTZ,
    
    -- Source information
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE CASCADE,
    stix_id TEXT,
    mitre_attack_id TEXT,
    
    -- Validation and status
    is_validated BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    false_positive_count INTEGER DEFAULT 0,
    
    -- Metadata
    tags TEXT[],
    labels TEXT[],
    references TEXT[],
    description TEXT,
    
    -- Enrichment data
    enrichment_data JSONB,
    whois_data JSONB,
    geolocation_data JSONB,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    validated_by TEXT,
    
    -- Unique constraint for same indicator type and value
    CONSTRAINT unique_indicator_value_type UNIQUE (indicator_type, indicator_value),
    CONSTRAINT indicator_value_present CHECK (indicator_value IS NOT NULL AND indicator_value != ''),
    CONSTRAINT stix_id_format CHECK (stix_id IS NULL OR stix_id ~* '^indicator--[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
);

-- Indexes for threat_intelligence_indicators
CREATE INDEX idx_threat_intelligence_indicators_value ON threat_intelligence_indicators(indicator_value);
CREATE INDEX idx_threat_intelligence_indicators_type ON threat_intelligence_indicators(indicator_type);
CREATE INDEX idx_threat_intelligence_indicators_ip ON threat_intelligence_indicators(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_domain ON threat_intelligence_indicators(domain_name) WHERE domain_name IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_url ON threat_intelligence_indicators(url) WHERE url IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_email ON threat_intelligence_indicators(email_address) WHERE email_address IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_hash ON threat_intelligence_indicators(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_threat_name ON threat_intelligence_indicators(threat_name);
CREATE INDEX idx_threat_intelligence_indicators_threat_family ON threat_intelligence_indicators(threat_family);
CREATE INDEX idx_threat_intelligence_indicators_category ON threat_intelligence_indicators(threat_category);
CREATE INDEX idx_threat_intelligence_indicators_severity ON threat_intelligence_indicators(threat_severity);
CREATE INDEX idx_threat_intelligence_indicators_confidence ON threat_intelligence_indicators(confidence_score DESC);
CREATE INDEX idx_threat_intelligence_indicators_active ON threat_intelligence_indicators(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_threat_intelligence_indicators_validated ON threat_intelligence_indicators(is_validated) WHERE is_validated = TRUE;
CREATE INDEX idx_threat_intelligence_indicators_first_seen ON threat_intelligence_indicators(first_seen DESC);
CREATE INDEX idx_threat_intelligence_indicators_last_seen ON threat_intelligence_indicators(last_seen DESC);
CREATE INDEX idx_threat_intelligence_indicators_expiration ON threat_intelligence_indicators(expiration_time) WHERE expiration_time IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_source ON threat_intelligence_indicators(threat_feed_source_id);
CREATE INDEX idx_threat_intelligence_indicators_stix_id ON threat_intelligence_indicators(stix_id) WHERE stix_id IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_mitre_id ON threat_intelligence_indicators(mitre_attack_id) WHERE mitre_attack_id IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_tags ON threat_intelligence_indicators USING GIN(tags);
CREATE INDEX idx_threat_intelligence_indicators_labels ON threat_intelligence_indicators USING GIN(labels);
CREATE INDEX idx_threat_intelligence_indicators_campaign ON threat_intelligence_indicators(campaign_name) WHERE campaign_name IS NOT NULL;
CREATE INDEX idx_threat_intelligence_indicators_attribution ON threat_intelligence_indicators(attribution_group) WHERE attribution_group IS NOT NULL;

-- ==============================================================================
-- MALWARE SIGNATURES TABLE
-- ==============================================================================
-- Purpose: Store malware signature definitions for detection
CREATE TABLE malware_signatures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Signature identification
    signature_name TEXT NOT NULL UNIQUE,
    signature_id TEXT UNIQUE,
    
    -- Malware identification
    malware_family TEXT NOT NULL,
    malware_name TEXT NOT NULL,
    malware_variant TEXT,
    malware_type TEXT NOT NULL CHECK (malware_type IN ('virus', 'worm', 'trojan', 'ransomware', 'spyware', 'adware', 'rootkit', 'backdoor', 'downloader', 'dropper')),
    
    -- Signature characteristics
    signature_type TEXT NOT NULL CHECK (signature_type IN ('hash', 'string', 'yara', 'regex', 'behavioral', 'network', 'file')),
    signature_value TEXT NOT NULL,
    signature_hash TEXT,
    
    -- Detection metadata
    detection_string TEXT,
    file_size_range TEXT,
    entropy_score NUMERIC(3,2) CHECK (entropy_score >= 0.0 AND entropy_score <= 1.0),
    
    -- Technical details
    file_type TEXT,
    target_platform TEXT[],
    compilation_timestamp TIMESTAMPTZ,
    packer_info TEXT,
    signature_version TEXT NOT NULL,
    
    -- Threat assessment
    threat_severity threat_severity NOT NULL,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Attribution
    attribution_group TEXT,
    threat_actor TEXT,
    campaign_name TEXT,
    
    -- Analysis context
    first_discovered TIMESTAMPTZ,
    last_seen TIMESTAMPTZ,
    prevalence_score NUMERIC(3,2) CHECK (prevalence_score >= 0.0 AND prevalence_score <= 1.0),
    
    -- Capabilities and behavior
    capabilities TEXT[],
    behavior_indicators TEXT[],
    network_indicators TEXT[],
    file_indicators TEXT[],
    
    -- TTP information
    attack_techniques TEXT[],
    kill_chain_phases TEXT[],
    
    -- Source information
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE CASCADE,
    reference_urls TEXT[],
    research_papers TEXT[],
    
    -- Status and validation
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    false_positive_rate NUMERIC(5,4) CHECK (false_positive_rate >= 0.0 AND false_positive_rate <= 1.0),
    
    -- Metadata
    tags TEXT[],
    labels TEXT[],
    description TEXT,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    validated_by TEXT,
    
    -- Constraints
    CONSTRAINT signature_value_present CHECK (signature_value IS NOT NULL AND signature_value != ''),
    CONSTRAINT malware_name_present CHECK (malware_name IS NOT NULL AND malware_name != ''),
    CONSTRAINT malware_family_present CHECK (malware_family IS NOT NULL AND malware_family != '')
);

-- Indexes for malware_signatures
CREATE INDEX idx_malware_signatures_name ON malware_signatures(signature_name);
CREATE INDEX idx_malware_signatures_id ON malware_signatures(signature_id);
CREATE INDEX idx_malware_signatures_family ON malware_signatures(malware_family);
CREATE INDEX idx_malware_signatures_malware_name ON malware_signatures(malware_name);
CREATE INDEX idx_malware_signatures_variant ON malware_signatures(malware_variant) WHERE malware_variant IS NOT NULL;
CREATE INDEX idx_malware_signatures_type ON malware_signatures(malware_type);
CREATE INDEX idx_malware_signatures_signature_type ON malware_signatures(signature_type);
CREATE INDEX idx_malware_signatures_value ON malware_signatures(signature_value);
CREATE INDEX idx_malware_signatures_hash ON malware_signatures(signature_hash) WHERE signature_hash IS NOT NULL;
CREATE INDEX idx_malware_signatures_severity ON malware_signatures(threat_severity);
CREATE INDEX idx_malware_signatures_confidence ON malware_signatures(confidence_score DESC);
CREATE INDEX idx_malware_signatures_active ON malware_signatures(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_malware_signatures_validated ON malware_signatures(is_validated) WHERE is_validated = TRUE;
CREATE INDEX idx_malware_signatures_version ON malware_signatures(signature_version);
CREATE INDEX idx_malware_signatures_source ON malware_signatures(threat_feed_source_id);
CREATE INDEX idx_malware_signatures_first_discovered ON malware_signatures(first_discovered DESC);
CREATE INDEX idx_malware_signatures_last_seen ON malware_signatures(last_seen DESC);
CREATE INDEX idx_malware_signatures_tags ON malware_signatures USING GIN(tags);
CREATE INDEX idx_malware_signatures_labels ON malware_signatures USING GIN(labels);
CREATE INDEX idx_malware_signatures_attribution ON malware_signatures(attribution_group) WHERE attribution_group IS NOT NULL;
CREATE INDEX idx_malware_signatures_threat_actor ON malware_signatures(threat_actor) WHERE threat_actor IS NOT NULL;
CREATE INDEX idx_malware_signatures_campaign ON malware_signatures(campaign_name) WHERE campaign_name IS NOT NULL;
CREATE INDEX idx_malware_signatures_capabilities ON malware_signatures USING GIN(capabilities);
CREATE INDEX idx_malware_signatures_techniques ON malware_signatures USING GIN(attack_techniques);

-- ==============================================================================
-- PHISHING URLS DATABASE TABLE
-- ==============================================================================
-- Purpose: Store known phishing URLs for detection and blocking
CREATE TABLE phishing_urls_database (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- URL identification
    url TEXT NOT NULL UNIQUE,
    url_hash TEXT NOT NULL,
    domain TEXT NOT NULL,
    subdomain TEXT,
    path TEXT,
    query_string TEXT,
    fragment TEXT,
    
    -- Phishing details
    phishing_type TEXT CHECK (phishing_type IN ('credential_harvesting', 'payment_fraud', 'malware_download', 'brand_impersonation', 'ceo_fraud')),
    target_brand TEXT,
    target_industry TEXT,
    
    -- Threat assessment
    threat_severity threat_severity NOT NULL,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    
    -- Attack context
    attack_campaign TEXT,
    attribution_group TEXT,
    infrastructure_provider TEXT,
    
    -- Technical characteristics
    hosting_country CHAR(2),
    hosting_provider TEXT,
    ssl_certificate_valid BOOLEAN DEFAULT FALSE,
    ssl_certificate_issuer TEXT,
    
    -- Content analysis
    page_title TEXT,
    page_keywords TEXT[],
    form_count INTEGER DEFAULT 0,
    has_login_form BOOLEAN DEFAULT FALSE,
    has_payment_form BOOLEAN DEFAULT FALSE,
    suspicious_redirects BOOLEAN DEFAULT FALSE,
    
    -- URL characteristics
    url_length INTEGER,
    has_unicode BOOLEAN DEFAULT FALSE,
    has_subdomain BOOLEAN DEFAULT FALSE,
    days_since_registration INTEGER,
    
    -- Detection methods
    detection_methods TEXT[],
    manual_validation BOOLEAN DEFAULT FALSE,
    automated_score NUMERIC(3,2),
    
    -- Status and timeline
    is_active BOOLEAN DEFAULT TRUE,
    first_detected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    takedown_date TIMESTAMPTZ,
    
    -- Source information
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE CASCADE,
    reporter_type TEXT CHECK (reporter_type IN ('automated', 'user', 'security_team', 'partner')),
    
    -- Impact assessment
    victim_count INTEGER DEFAULT 0,
    data_stolen TEXT[],
    financial_impact_range TEXT,
    
    -- Metadata
    tags TEXT[],
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    
    -- Constraints
    CONSTRAINT url_present CHECK (url IS NOT NULL AND url != ''),
    CONSTRAINT domain_present CHECK (domain IS NOT NULL AND domain != ''),
    CONSTRAINT valid_url_length CHECK (length(url) <= 2048),
    CONSTRAINT url_hash_format CHECK (length(url_hash) = 64 OR length(url_hash) = 40) -- MD5 or SHA1
);

-- Indexes for phishing_urls_database
CREATE INDEX idx_phishing_urls_database_url ON phishing_urls_database(url);
CREATE INDEX idx_phishing_urls_database_hash ON phishing_urls_database(url_hash);
CREATE INDEX idx_phishing_urls_database_domain ON phishing_urls_database(domain);
CREATE INDEX idx_phishing_urls_database_subdomain ON phishing_urls_database(subdomain) WHERE subdomain IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_type ON phishing_urls_database(phishing_type);
CREATE INDEX idx_phishing_urls_database_target_brand ON phishing_urls_database(target_brand) WHERE target_brand IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_severity ON phishing_urls_database(threat_severity);
CREATE INDEX idx_phishing_urls_database_confidence ON phishing_urls_database(confidence_score DESC);
CREATE INDEX idx_phishing_urls_database_active ON phishing_urls_database(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_phishing_urls_database_campaign ON phishing_urls_database(attack_campaign) WHERE attack_campaign IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_attribution ON phishing_urls_database(attribution_group) WHERE attribution_group IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_hosting_country ON phishing_urls_database(hosting_country) WHERE hosting_country IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_first_detected ON phishing_urls_database(first_detected DESC);
CREATE INDEX idx_phishing_urls_database_last_seen ON phishing_urls_database(last_seen DESC);
CREATE INDEX idx_phishing_urls_database_takedown ON phishing_urls_database(takedown_date) WHERE takedown_date IS NOT NULL;
CREATE INDEX idx_phishing_urls_database_source ON phishing_urls_database(threat_feed_source_id);
CREATE INDEX idx_phishing_urls_database_reporter ON phishing_urls_database(reporter_type);
CREATE INDEX idx_phishing_urls_database_tags ON phishing_urls_database USING GIN(tags);
CREATE INDEX idx_phishing_urls_database_keywords ON phishing_urls_database USING GIN(page_keywords);
CREATE INDEX idx_phishing_urls_database_has_login_form ON phishing_urls_database(has_login_form) WHERE has_login_form = TRUE;
CREATE INDEX idx_phishing_urls_database_has_payment_form ON phishing_urls_database(has_payment_form) WHERE has_payment_form = TRUE;

-- ==============================================================================
-- SPAM PATTERNS DATABASE TABLE
-- ==============================================================================
-- Purpose: Store spam detection patterns and rules
CREATE TABLE spam_patterns_database (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Pattern identification
    pattern_name TEXT NOT NULL UNIQUE,
    pattern_id TEXT UNIQUE,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN ('regex', 'keyword', 'url', 'attachment', 'header', 'behavioral', 'ml_pattern')),
    
    -- Pattern definition
    pattern_expression TEXT NOT NULL,
    case_sensitive BOOLEAN DEFAULT FALSE,
    pattern_weight NUMERIC(3,2) CHECK (pattern_weight >= 0.0 AND pattern_weight <= 1.0),
    
    -- Spam classification
    spam_category TEXT NOT NULL CHECK (spam_category IN ('advertisement', 'fraud', 'phishing', 'malware', 'adult', 'gambling', 'pharmaceutical', 'political', 'scam', 'unsolicited_bulk')),
    spam_subcategory TEXT,
    
    -- Detection parameters
    detection_confidence NUMERIC(3,2) CHECK (detection_confidence >= 0.0 AND detection_confidence <= 1.0),
    false_positive_rate NUMERIC(5,4) CHECK (false_positive_rate >= 0.0 AND false_positive_rate <= 1.0),
    accuracy_rate NUMERIC(5,4) CHECK (accuracy_rate >= 0.0 AND accuracy_rate <= 1.0),
    
    -- Pattern scope
    applies_to TEXT NOT NULL CHECK (applies_to IN ('subject', 'body', 'headers', 'attachments', 'sender', 'url', 'full_message')),
    target_fields TEXT[],
    
    -- Language and regional settings
    language_code CHAR(2),
    region TEXT,
    is_multilingual BOOLEAN DEFAULT FALSE,
    
    -- Pattern context
    match_context TEXT,
    priority_level INTEGER DEFAULT 0 CHECK (priority_level >= 0 AND priority_level <= 100),
    
    -- Performance metrics
    match_count BIGINT DEFAULT 0,
    true_positive_count INTEGER DEFAULT 0,
    false_positive_count INTEGER DEFAULT 0,
    last_match_date TIMESTAMPTZ,
    
    -- Maintenance information
    pattern_version TEXT NOT NULL DEFAULT '1.0',
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    expiry_date TIMESTAMPTZ,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_experimental BOOLEAN DEFAULT FALSE,
    auto_tuning_enabled BOOLEAN DEFAULT FALSE,
    
    -- Source and creation
    threat_feed_source_id UUID REFERENCES threat_feed_sources(id) ON DELETE SET NULL,
    created_by TEXT NOT NULL,
    validated_by TEXT,
    
    -- Metadata
    tags TEXT[],
    description TEXT,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT pattern_expression_present CHECK (pattern_expression IS NOT NULL AND pattern_expression != ''),
    CONSTRAINT spam_category_present CHECK (spam_category IS NOT NULL AND spam_category != ''),
    CONSTRAINT applies_to_present CHECK (applies_to IS NOT NULL AND applies_to != ''),
    CONSTRAINT created_by_present CHECK (created_by IS NOT NULL AND created_by != '')
);

-- Indexes for spam_patterns_database
CREATE INDEX idx_spam_patterns_database_name ON spam_patterns_database(pattern_name);
CREATE INDEX idx_spam_patterns_database_id ON spam_patterns_database(pattern_id);
CREATE INDEX idx_spam_patterns_database_type ON spam_patterns_database(pattern_type);
CREATE INDEX idx_spam_patterns_database_category ON spam_patterns_database(spam_category);
CREATE INDEX idx_spam_patterns_database_subcategory ON spam_patterns_database(spam_subcategory) WHERE spam_subcategory IS NOT NULL;
CREATE INDEX idx_spam_patterns_database_applies_to ON spam_patterns_database(applies_to);
CREATE INDEX idx_spam_patterns_database_confidence ON spam_patterns_database(detection_confidence DESC);
CREATE INDEX idx_spam_patterns_database_weight ON spam_patterns_database(pattern_weight DESC);
CREATE INDEX idx_spam_patterns_database_active ON spam_patterns_database(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_spam_patterns_database_experimental ON spam_patterns_database(is_experimental) WHERE is_experimental = TRUE;
CREATE INDEX idx_spam_patterns_database_language ON spam_patterns_database(language_code) WHERE language_code IS NOT NULL;
CREATE INDEX idx_spam_patterns_database_priority ON spam_patterns_database(priority_level DESC);
CREATE INDEX idx_spam_patterns_database_version ON spam_patterns_database(pattern_version);
CREATE INDEX idx_spam_patterns_database_source ON spam_patterns_database(threat_feed_source_id) WHERE threat_feed_source_id IS NOT NULL;
CREATE INDEX idx_spam_patterns_database_created_by ON spam_patterns_database(created_by);
CREATE INDEX idx_spam_patterns_database_tags ON spam_patterns_database USING GIN(tags);
CREATE INDEX idx_spam_patterns_database_match_count ON spam_patterns_database(match_count DESC);
CREATE INDEX idx_spam_patterns_database_last_match ON spam_patterns_database(last_match_date DESC) WHERE last_match_date IS NOT NULL;
CREATE INDEX idx_spam_patterns_database_expiry ON spam_patterns_database(expiry_date) WHERE expiry_date IS NOT NULL;

-- Full text search index for pattern expressions
CREATE INDEX idx_spam_patterns_database_fts ON spam_patterns_database USING GIN(to_tsvector('english', pattern_expression));

-- ==============================================================================
-- BLACKLISTS AGGREGATION TABLE
-- ==============================================================================
-- Purpose: Store aggregated blacklist data from multiple sources
CREATE TABLE blacklists_aggregation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Blacklist entry identification
    entity_value TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('ip', 'domain', 'email', 'url', 'hash', 'asn')),
    
    -- Specific entity values
    ip_address INET,
    domain_name TEXT,
    email_address CITEXT,
    url TEXT,
    file_hash TEXT,
    asn INTEGER,
    
    -- Blacklist information
    blacklist_source TEXT NOT NULL,
    blacklist_type TEXT NOT NULL CHECK (blacklist_type IN ('spam', 'malware', 'phishing', 'botnet', 'abuse', 'general')),
    list_name TEXT NOT NULL,
    
    -- Threat assessment
    threat_severity threat_severity NOT NULL,
    threat_categories TEXT[],
    threat_reasons TEXT[],
    
    -- Listing details
    listed_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expiry_date TIMESTAMPTZ,
    last_verified TIMESTAMPTZ DEFAULT NOW(),
    
    -- Source reliability
    source_reliability NUMERIC(3,2) CHECK (source_reliability >= 0.0 AND source_reliability <= 1.0),
    source_confidence NUMERIC(3,2) CHECK (source_confidence >= 0.0 AND source_confidence <= 1.0),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_false_positive BOOLEAN DEFAULT FALSE,
    
    -- Additional context
    listing_reason TEXT,
    notes TEXT,
    tags TEXT[],
    
    -- Metadata
    api_endpoint TEXT,
    last_sync TIMESTAMPTZ DEFAULT NOW(),
    sync_frequency INTERVAL DEFAULT '24 hours',
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    
    -- Constraints
    CONSTRAINT entity_value_present CHECK (entity_value IS NOT NULL AND entity_value != ''),
    CONSTRAINT blacklist_source_present CHECK (blacklist_source IS NOT NULL AND blacklist_source != ''),
    CONSTRAINT list_name_present CHECK (list_name IS NOT NULL AND list_name != ''),
    CONSTRAINT entity_type_consistency CHECK (
        (entity_type = 'ip' AND ip_address IS NOT NULL) OR
        (entity_type = 'domain' AND domain_name IS NOT NULL) OR
        (entity_type = 'email' AND email_address IS NOT NULL) OR
        (entity_type = 'url' AND url IS NOT NULL) OR
        (entity_type = 'hash' AND file_hash IS NOT NULL) OR
        (entity_type = 'asn' AND asn IS NOT NULL)
    ),
    -- Prevent duplicates for same entity from same source
    CONSTRAINT unique_entity_source UNIQUE (entity_value, entity_type, blacklist_source, list_name)
);

-- Indexes for blacklists_aggregation
CREATE INDEX idx_blacklists_aggregation_entity ON blacklists_aggregation(entity_value, entity_type);
CREATE INDEX idx_blacklists_aggregation_ip ON blacklists_aggregation(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_domain ON blacklists_aggregation(domain_name) WHERE domain_name IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_email ON blacklists_aggregation(email_address) WHERE email_address IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_url ON blacklists_aggregation(url) WHERE url IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_hash ON blacklists_aggregation(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_asn ON blacklists_aggregation(asn) WHERE asn IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_source ON blacklists_aggregation(blacklist_source);
CREATE INDEX idx_blacklists_aggregation_type ON blacklists_aggregation(blacklist_type);
CREATE INDEX idx_blacklists_aggregation_list_name ON blacklists_aggregation(list_name);
CREATE INDEX idx_blacklists_aggregation_severity ON blacklists_aggregation(threat_severity);
CREATE INDEX idx_blacklists_aggregation_active ON blacklists_aggregation(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_blacklists_aggregation_verified ON blacklists_aggregation(is_verified) WHERE is_verified = TRUE;
CREATE INDEX idx_blacklists_aggregation_false_positive ON blacklists_aggregation(is_false_positive) WHERE is_false_positive = TRUE;
CREATE INDEX idx_blacklists_aggregation_listed_date ON blacklists_aggregation(listed_date DESC);
CREATE INDEX idx_blacklists_aggregation_expiry ON blacklists_aggregation(expiry_date) WHERE expiry_date IS NOT NULL;
CREATE INDEX idx_blacklists_aggregation_last_verified ON blacklists_aggregation(last_verified DESC);
CREATE INDEX idx_blacklists_aggregation_tags ON blacklists_aggregation USING GIN(tags);
CREATE INDEX idx_blacklists_aggregation_threat_categories ON blacklists_aggregation USING GIN(threat_categories);
CREATE INDEX idx_blacklists_aggregation_sync ON blacklists_aggregation(last_sync DESC);

-- ==============================================================================
-- VALIDATION AUDIT LOG TABLE
-- ==============================================================================
-- Purpose: Store comprehensive audit trail for security validations
CREATE TABLE validation_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event identification
    event_id TEXT UNIQUE,
    event_type TEXT NOT NULL CHECK (event_type IN ('domain_validation', 'email_validation', 'ip_reputation', 'threat_detection', 'blacklist_check', 'ml_prediction')),
    
    -- Entity being validated
    entity_type TEXT NOT NULL CHECK (entity_type IN ('domain', 'email', 'ip', 'url', 'hash')),
    entity_value TEXT NOT NULL,
    
    -- Specific entity values
    domain_name TEXT,
    email_address CITEXT,
    ip_address INET,
    url TEXT,
    file_hash TEXT,
    
    -- Validation details
    validation_method TEXT NOT NULL,
    validation_status TEXT NOT NULL CHECK (validation_status IN ('success', 'failed', 'timeout', 'error', 'pending')),
    
    -- Input data
    input_data JSONB,
    validation_parameters JSONB,
    
    -- Results
    result_data JSONB,
    score NUMERIC(3,2),
    risk_level TEXT CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Performance metrics
    execution_time_ms INTEGER,
    memory_used_mb NUMERIC(8,2),
    
    -- Error handling
    error_code TEXT,
    error_message TEXT,
    stack_trace TEXT,
    
    -- Context information
    client_ip INET,
    user_agent TEXT,
    session_id TEXT,
    request_id TEXT,
    
    -- Security context
    api_key_used TEXT,
    rate_limit_hit BOOLEAN DEFAULT FALSE,
    suspicious_activity BOOLEAN DEFAULT FALSE,
    
    -- Compliance
    data_processing_legal_basis TEXT,
    retention_category TEXT,
    gdpr_relevant BOOLEAN DEFAULT FALSE,
    
    -- Source and destination
    source_system TEXT,
    destination_system TEXT,
    processing_node TEXT,
    
    -- Audit trail
    actor_id TEXT,
    actor_type TEXT CHECK (actor_type IN ('user', 'system', 'api', 'service')),
    
    -- Timeline
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    processing_duration INTERVAL,
    
    -- Metadata
    tags TEXT[],
    annotations JSONB,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_id_present CHECK (event_id IS NOT NULL AND event_id != ''),
    CONSTRAINT entity_value_present CHECK (entity_value IS NOT NULL AND entity_value != ''),
    CONSTRAINT validation_method_present CHECK (validation_method IS NOT NULL AND validation_method != ''),
    CONSTRAINT entity_type_consistency CHECK (
        (entity_type = 'domain' AND domain_name IS NOT NULL) OR
        (entity_type = 'email' AND email_address IS NOT NULL) OR
        (entity_type = 'ip' AND ip_address IS NOT NULL) OR
        (entity_type = 'url' AND url IS NOT NULL) OR
        (entity_type = 'hash' AND file_hash IS NOT NULL)
    )
);

-- Indexes for validation_audit_log
CREATE INDEX idx_validation_audit_log_event_id ON validation_audit_log(event_id);
CREATE INDEX idx_validation_audit_log_event_type ON validation_audit_log(event_type);
CREATE INDEX idx_validation_audit_log_entity ON validation_audit_log(entity_value, entity_type);
CREATE INDEX idx_validation_audit_log_domain ON validation_audit_log(domain_name) WHERE domain_name IS NOT NULL;
CREATE INDEX idx_validation_audit_log_email ON validation_audit_log(email_address) WHERE email_address IS NOT NULL;
CREATE INDEX idx_validation_audit_log_ip ON validation_audit_log(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX idx_validation_audit_log_url ON validation_audit_log(url) WHERE url IS NOT NULL;
CREATE INDEX idx_validation_audit_log_hash ON validation_audit_log(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_validation_audit_log_status ON validation_audit_log(validation_status);
CREATE INDEX idx_validation_audit_log_score ON validation_audit_log(score DESC);
CREATE INDEX idx_validation_audit_log_risk_level ON validation_audit_log(risk_level);
CREATE INDEX idx_validation_audit_log_actor ON validation_audit_log(actor_id) WHERE actor_id IS NOT NULL;
CREATE INDEX idx_validation_audit_log_actor_type ON validation_audit_log(actor_type);
CREATE INDEX idx_validation_audit_log_client_ip ON validation_audit_log(client_ip) WHERE client_ip IS NOT NULL;
CREATE INDEX idx_validation_audit_log_started_at ON validation_audit_log(started_at DESC);
CREATE INDEX idx_validation_audit_log_completed_at ON validation_audit_log(completed_at DESC) WHERE completed_at IS NOT NULL;
CREATE INDEX idx_validation_audit_log_source_system ON validation_audit_log(source_system) WHERE source_system IS NOT NULL;
CREATE INDEX idx_validation_audit_log_tags ON validation_audit_log USING GIN(tags);
CREATE INDEX idx_validation_audit_log_rate_limit ON validation_audit_log(rate_limit_hit) WHERE rate_limit_hit = TRUE;
CREATE INDEX idx_validation_audit_log_suspicious ON validation_audit_log(suspicious_activity) WHERE suspicious_activity = TRUE;
CREATE INDEX idx_validation_audit_log_gdpr ON validation_audit_log(gdpr_relevant) WHERE gdpr_relevant = TRUE;

-- ==============================================================================
-- ML MODEL PREDICTIONS TABLE
-- ==============================================================================
-- Purpose: Store machine learning model predictions and confidence scores
CREATE TABLE ml_model_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Prediction identification
    prediction_id TEXT UNIQUE NOT NULL,
    
    -- Model information
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_type TEXT NOT NULL CHECK (model_type IN ('classification', 'regression', 'anomaly_detection', 'clustering')),
    prediction_task TEXT NOT NULL CHECK (prediction_task IN ('spam_detection', 'phishing_detection', 'malware_classification', 'threat_scoring', 'anomaly_detection')),
    
    -- Input data
    entity_type TEXT NOT NULL CHECK (entity_type IN ('email', 'domain', 'ip', 'url', 'file', 'message')),
    entity_value TEXT NOT NULL,
    
    -- Specific entity values
    email_address CITEXT,
    domain_name TEXT,
    ip_address INET,
    url TEXT,
    file_hash TEXT,
    message_content TEXT,
    
    -- Prediction results
    predicted_class TEXT,
    confidence_score NUMERIC(3,2) CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    probability_scores JSONB,
    
    -- Risk assessment
    risk_score NUMERIC(3,2) CHECK (risk_score >= 0.0 AND risk_score <= 1.0),
    risk_category TEXT CHECK (risk_category IN ('low', 'medium', 'high', 'critical')),
    
    -- Feature data
    input_features JSONB,
    feature_importance JSONB,
    model_metadata JSONB,
    
    -- Performance indicators
    prediction_latency_ms INTEGER,
    model_accuracy NUMERIC(5,4),
    training_data_version TEXT,
    
    -- Context and validation
    prediction_context TEXT,
    human_review_required BOOLEAN DEFAULT FALSE,
    final_decision TEXT CHECK (final_decision IN ('approved', 'rejected', 'pending_review', 'escalated')),
    human_reviewer_id TEXT,
    
    -- Status and lifecycle
    prediction_status prediction_status DEFAULT 'completed',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    
    -- Source tracking
    source_request_id TEXT,
    api_endpoint TEXT,
    client_id TEXT,
    
    -- Performance monitoring
    ground_truth TEXT,
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),
    correction_reason TEXT,
    
    -- Audit trail
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    predicted_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT prediction_id_present CHECK (prediction_id IS NOT NULL AND prediction_id != ''),
    CONSTRAINT model_name_present CHECK (model_name IS NOT NULL AND model_name != ''),
    CONSTRAINT entity_value_present CHECK (entity_value IS NOT NULL AND entity_value != ''),
    CONSTRAINT entity_type_consistency CHECK (
        (entity_type = 'email' AND email_address IS NOT NULL) OR
        (entity_type = 'domain' AND domain_name IS NOT NULL) OR
        (entity_type = 'ip' AND ip_address IS NOT NULL) OR
        (entity_type = 'url' AND url IS NOT NULL) OR
        (entity_type = 'file' AND file_hash IS NOT NULL) OR
        (entity_type = 'message' AND message_content IS NOT NULL)
    )
);

-- Indexes for ml_model_predictions
CREATE INDEX idx_ml_model_predictions_prediction_id ON ml_model_predictions(prediction_id);
CREATE INDEX idx_ml_model_predictions_model_name ON ml_model_predictions(model_name);
CREATE INDEX idx_ml_model_predictions_model_version ON ml_model_predictions(model_version);
CREATE INDEX idx_ml_model_predictions_model_type ON ml_model_predictions(model_type);
CREATE INDEX idx_ml_model_predictions_task ON ml_model_predictions(prediction_task);
CREATE INDEX idx_ml_model_predictions_entity ON ml_model_predictions(entity_value, entity_type);
CREATE INDEX idx_ml_model_predictions_email ON ml_model_predictions(email_address) WHERE email_address IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_domain ON ml_model_predictions(domain_name) WHERE domain_name IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_ip ON ml_model_predictions(ip_address) WHERE ip_address IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_url ON ml_model_predictions(url) WHERE url IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_hash ON ml_model_predictions(file_hash) WHERE file_hash IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_class ON ml_model_predictions(predicted_class);
CREATE INDEX idx_ml_model_predictions_confidence ON ml_model_predictions(confidence_score DESC);
CREATE INDEX idx_ml_model_predictions_risk_score ON ml_model_predictions(risk_score DESC);
CREATE INDEX idx_ml_model_predictions_risk_category ON ml_model_predictions(risk_category);
CREATE INDEX idx_ml_model_predictions_status ON ml_model_predictions(prediction_status);
CREATE INDEX idx_ml_model_predictions_active ON ml_model_predictions(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_ml_model_predictions_review_required ON ml_model_predictions(human_review_required) WHERE human_review_required = TRUE;
CREATE INDEX idx_ml_model_predictions_decision ON ml_model_predictions(final_decision);
CREATE INDEX idx_ml_model_predictions_predicted_at ON ml_model_predictions(predicted_at DESC);
CREATE INDEX idx_ml_model_predictions_created_at ON ml_model_predictions(created_at DESC);
CREATE INDEX idx_ml_model_predictions_source ON ml_model_predictions(source_request_id) WHERE source_request_id IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_client ON ml_model_predictions(client_id) WHERE client_id IS NOT NULL;
CREATE INDEX idx_ml_model_predictions_latency ON ml_model_predictions(prediction_latency_ms) WHERE prediction_latency_ms IS NOT NULL;

-- Full text search index for message content
CREATE INDEX idx_ml_model_predictions_content_fts ON ml_model_predictions USING GIN(to_tsvector('english', message_content)) WHERE message_content IS NOT NULL;

-- ==============================================================================
-- ATTACK CAMPAIGNS TRACKING TABLE
-- ==============================================================================
-- Purpose: Track and correlate security attack campaigns
CREATE TABLE attack_campaigns_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Campaign identification
    campaign_id TEXT UNIQUE NOT NULL,
    campaign_name TEXT NOT NULL,
    campaign_type TEXT NOT NULL CHECK (campaign_type IN ('phishing', 'malware', 'ransomware', 'apt', 'ddos', 'data_breach', 'social_engineering', 'credential_stuffing')),
    
    -- Attribution and classification
    threat_actor TEXT,
    attribution_confidence NUMERIC(3,2) CHECK (attribution_confidence >= 0.0 AND attribution_confidence <= 1.0),
    threat_group TEXT,
    malware_family TEXT,
    
    -- Campaign details
    campaign_description TEXT,
    campaign_objectives TEXT[],
    target_industries TEXT[],
    target_regions TEXT[],
    
    -- Timeline
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    peak_activity_date TIMESTAMPTZ,
    discovery_date TIMESTAMPTZ,
    
    -- Status and severity
    campaign_status campaign_status DEFAULT 'active',
    threat_severity threat_severity NOT NULL,
    impact_score NUMERIC(3,2) CHECK (impact_score >= 0.0 AND impact_score <= 1.0),
    
    -- Scale and scope
    estimated_victims INTEGER,
    actual_victims INTEGER,
    affected_organizations INTEGER,
    geographic_spread TEXT[],
    
    -- Technical indicators
    indicators_of_compromise TEXT[],
    techniques_used TEXT[],
    attack_vectors TEXT[],
    infrastructure_details JSONB,
    
    -- Financial impact
    estimated_cost NUMERIC(15,2),
    currency CHAR(3) DEFAULT 'USD',
    insurance_claim_filed BOOLEAN DEFAULT FALSE,
    claim_amount NUMERIC(15,2),
    
    -- Response and mitigation
    response_team TEXT,
    containment_date TIMESTAMPTZ,
    mitigation_measures TEXT[],
    lessons_learned TEXT,
    
    -- Intelligence sources
    intelligence_sources TEXT[],
    reporting_organizations TEXT[],
    public_disclosure BOOLEAN DEFAULT FALSE,
    disclosure_date TIMESTAMPTZ,
    
    -- Campaign tracking
    tracking_tags TEXT[],
    related_campaigns TEXT[],
    
    -- Status tracking
    is_active BOOLEAN DEFAULT TRUE,
    investigation_status TEXT CHECK (investigation_status IN ('ongoing', 'closed', 'suspended', 'escalated')),
    
    -- Metadata
    notes TEXT,
    external_references TEXT[],
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by TEXT,
    last_updated_by TEXT,
    
    -- Constraints
    CONSTRAINT campaign_id_present CHECK (campaign_id IS NOT NULL AND campaign_id != ''),
    CONSTRAINT campaign_name_present CHECK (campaign_name IS NOT NULL AND campaign_name != ''),
    CONSTRAINT campaign_type_present CHECK (campaign_type IS NOT NULL AND campaign_type != ''),
    CONSTRAINT dates_consistency CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

-- Indexes for attack_campaigns_tracking
CREATE INDEX idx_attack_campaigns_tracking_campaign_id ON attack_campaigns_tracking(campaign_id);
CREATE INDEX idx_attack_campaigns_tracking_name ON attack_campaigns_tracking(campaign_name);
CREATE INDEX idx_attack_campaigns_tracking_type ON attack_campaigns_tracking(campaign_type);
CREATE INDEX idx_attack_campaigns_tracking_actor ON attack_campaigns_tracking(threat_actor) WHERE threat_actor IS NOT NULL;
CREATE INDEX idx_attack_campaigns_tracking_group ON attack_campaigns_tracking(threat_group) WHERE threat_group IS NOT NULL;
CREATE INDEX idx_attack_campaigns_tracking_malware_family ON attack_campaigns_tracking(malware_family) WHERE malware_family IS NOT NULL;
CREATE INDEX idx_attack_campaigns_tracking_status ON attack_campaigns_tracking(campaign_status);
CREATE INDEX idx_attack_campaigns_tracking_severity ON attack_campaigns_tracking(threat_severity);
CREATE INDEX idx_attack_campaigns_tracking_impact ON attack_campaigns_tracking(impact_score DESC);
CREATE INDEX idx_attack_campaigns_tracking_start_date ON attack_campaigns_tracking(start_date DESC);
CREATE INDEX idx_attack_campaigns_tracking_end_date ON attack_campaigns_tracking(end_date DESC) WHERE end_date IS NOT NULL;
CREATE INDEX idx_attack_campaigns_tracking_active ON attack_campaigns_tracking(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_attack_campaigns_tracking_victims ON attack_campaigns_tracking(actual_victims DESC) WHERE actual_victims IS NOT NULL;
CREATE INDEX idx_attack_campaigns_tracking_investigation ON attack_campaigns_tracking(investigation_status);
CREATE INDEX idx_attack_campaigns_tracking_disclosure ON attack_campaigns_tracking(public_disclosure) WHERE public_disclosure = TRUE;
CREATE INDEX idx_attack_campaigns_tracking_tags ON attack_campaigns_tracking USING GIN(tracking_tags);
CREATE INDEX idx_attack_campaigns_tracking_objectives ON attack_campaigns_tracking USING GIN(campaign_objectives);
CREATE INDEX idx_attack_campaigns_tracking_techniques ON attack_campaigns_tracking USING GIN(techniques_used);
CREATE INDEX idx_attack_campaigns_tracking_vectors ON attack_campaigns_tracking USING GIN(attack_vectors);
CREATE INDEX idx_attack_campaigns_tracking_industries ON attack_campaigns_tracking USING GIN(target_industries);
CREATE INDEX idx_attack_campaigns_tracking_regions ON attack_campaigns_tracking USING GIN(target_regions);
CREATE INDEX idx_attack_campaigns_tracking_iocs ON attack_campaigns_tracking USING GIN(indicators_of_compromise);

-- Full text search indexes for campaign description and objectives
CREATE INDEX idx_attack_campaigns_tracking_description_fts ON attack_campaigns_tracking USING GIN(to_tsvector('english', campaign_description));
CREATE INDEX idx_attack_campaigns_tracking_objectives_fts ON attack_campaigns_tracking USING GIN(to_tsvector('english', array_to_string(campaign_objectives, ' ')));

-- ==============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ==============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_threat_feed_sources_updated_at
    BEFORE UPDATE ON threat_feed_sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_domains_intelligence_updated_at
    BEFORE UPDATE ON domains_intelligence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ip_addresses_reputation_updated_at
    BEFORE UPDATE ON ip_addresses_reputation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_addresses_validation_updated_at
    BEFORE UPDATE ON email_addresses_validation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sender_reputation_scoring_updated_at
    BEFORE UPDATE ON sender_reputation_scoring
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threat_intelligence_indicators_updated_at
    BEFORE UPDATE ON threat_intelligence_indicators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_malware_signatures_updated_at
    BEFORE UPDATE ON malware_signatures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_phishing_urls_database_updated_at
    BEFORE UPDATE ON phishing_urls_database
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_spam_patterns_database_updated_at
    BEFORE UPDATE ON spam_patterns_database
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blacklists_aggregation_updated_at
    BEFORE UPDATE ON blacklists_aggregation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validation_audit_log_updated_at
    BEFORE UPDATE ON validation_audit_log
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_model_predictions_updated_at
    BEFORE UPDATE ON ml_model_predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_attack_campaigns_tracking_updated_at
    BEFORE UPDATE ON attack_campaigns_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- VIEWS FOR COMMON QUERIES
-- ==============================================================================

-- High-risk domains view
CREATE VIEW high_risk_domains AS
SELECT 
    d.domain,
    d.threat_severity,
    d.confidence_score,
    d.is_malicious,
    d.threat_type,
    d.tags,
    d.first_seen,
    d.last_seen
FROM domains_intelligence d
WHERE d.threat_severity IN ('high', 'critical')
    AND d.confidence_score >= 0.8;

-- Malicious IP addresses view
CREATE VIEW malicious_ip_addresses AS
SELECT 
    i.ip_address,
    i.threat_severity,
    i.confidence_score,
    i.threat_type,
    i.is_malicious,
    i.country_code,
    i.asn,
    i.tags,
    i.first_seen,
    i.last_seen
FROM ip_addresses_reputation i
WHERE i.is_malicious = TRUE
    AND i.confidence_score >= 0.8;

-- Active phishing URLs view
CREATE VIEW active_phishing_urls AS
SELECT 
    p.url,
    p.domain,
    p.phishing_type,
    p.target_brand,
    p.threat_severity,
    p.confidence_score,
    p.has_login_form,
    p.has_payment_form,
    p.first_detected,
    p.last_seen
FROM phishing_urls_database p
WHERE p.is_active = TRUE
    AND p.confidence_score >= 0.8;

-- Recent ML predictions requiring review
CREATE VIEW ml_predictions_requiring_review AS
SELECT 
    m.prediction_id,
    m.model_name,
    m.prediction_task,
    m.entity_type,
    m.entity_value,
    m.confidence_score,
    m.risk_score,
    m.risk_category,
    m.predicted_class,
    m.predicted_at
FROM ml_model_predictions m
WHERE m.human_review_required = TRUE
    AND m.final_decision IS NULL
    AND m.created_at >= NOW() - INTERVAL '24 hours';

-- ==============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ==============================================================================

COMMENT ON SCHEMA security_intelligence IS 'Schema containing tables for security intelligence, threat detection, and ML-powered analysis';
COMMENT ON TABLE threat_feed_sources IS 'Stores information about threat intelligence feed sources and their characteristics';
COMMENT ON TABLE domains_intelligence IS 'Contains domain reputation data, threat intelligence, and security metrics for domain names';
COMMENT ON TABLE ip_addresses_reputation IS 'Stores IP address reputation scores, threat classifications, and geolocation data';
COMMENT ON TABLE email_addresses_validation IS 'Contains email validation results, risk assessments, and verification details';
COMMENT ON TABLE sender_reputation_scoring IS 'Stores sender reputation metrics, behavioral analysis, and ML-based scoring';
COMMENT ON TABLE threat_intelligence_indicators IS 'Contains Indicators of Compromise (IOCs) from various threat intelligence feeds';
COMMENT ON TABLE malware_signatures IS 'Stores malware signature definitions for detection systems including YARA rules';
COMMENT ON TABLE phishing_urls_database IS 'Contains known phishing URLs with detection details and threat assessments';
COMMENT ON TABLE spam_patterns_database IS 'Stores spam detection patterns, regex rules, and machine learning patterns';
COMMENT ON TABLE blacklists_aggregation IS 'Contains aggregated blacklist data from multiple sources for various entity types';
COMMENT ON TABLE validation_audit_log IS 'Comprehensive audit trail for all security validation operations and decisions';
COMMENT ON TABLE ml_model_predictions IS 'Stores machine learning model predictions, confidence scores, and performance metrics';
COMMENT ON TABLE attack_campaigns_tracking IS 'Tracks and correlates security attack campaigns, threat actors, and campaign details';

-- ==============================================================================
-- SECURITY FUNCTIONS AND UTILITIES
-- ==============================================================================

-- Function to anonymize IP addresses for GDPR compliance
CREATE OR REPLACE FUNCTION anonymize_ip_address(ip_address INET)
RETURNS INET AS $$
BEGIN
    -- Anonymize last octet of IPv4 or last 80 bits of IPv6
    RETURN CASE 
        WHEN family(ip_address) = 4 THEN set_masklen(ip_address, 24)::inet
        WHEN family(ip_address) = 6 THEN set_masklen(ip_address, 48)::inet
        ELSE ip_address
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate domain reputation score
CREATE OR REPLACE FUNCTION calculate_domain_reputation(domain_value TEXT)
RETURNS NUMERIC AS $$
DECLARE
    reputation_score NUMERIC := 0.5; -- Default neutral score
    age_factor NUMERIC := 0.0;
    threat_factor NUMERIC := 0.0;
    security_factor NUMERIC := 0.0;
BEGIN
    -- Age factor (older domains get higher scores if not malicious)
    SELECT 
        CASE 
            WHEN EXTRACT(days FROM (NOW() - d.creation_date)) > 365 THEN 0.3
            WHEN EXTRACT(days FROM (NOW() - d.creation_date)) > 30 THEN 0.1
            ELSE -0.2
        END INTO age_factor
    FROM domains_intelligence d
    WHERE d.domain = domain_value;
    
    -- Threat factor (reduce score for known threats)
    SELECT 
        CASE 
            WHEN d.is_malicious THEN -0.8
            WHEN d.is_suspicious THEN -0.4
            WHEN d.threat_severity = 'high' THEN -0.6
            WHEN d.threat_severity = 'critical' THEN -1.0
            ELSE 0.1
        END INTO threat_factor
    FROM domains_intelligence d
    WHERE d.domain = domain_value;
    
    -- Security factor (increase score for security features)
    SELECT 
        CASE 
            WHEN d.has_ssl_certificate AND d.has_dmarc THEN 0.2
            WHEN d.has_ssl_certificate OR d.has_dmarc THEN 0.1
            ELSE -0.1
        END INTO security_factor
    FROM domains_intelligence d
    WHERE d.domain = domain_value;
    
    -- Calculate final score
    reputation_score := 0.5 + COALESCE(age_factor, 0) + COALESCE(threat_factor, 0) + COALESCE(security_factor, 0);
    
    -- Ensure score stays within bounds
    RETURN LEAST(GREATEST(reputation_score, 0.0), 1.0);
END;
$$ LANGUAGE plpgsql;

-- Function to validate threat intelligence indicator
CREATE OR REPLACE FUNCTION validate_threat_indicator(
    indicator_value_param TEXT,
    indicator_type_param TEXT,
    threat_name_param TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Basic validation logic
    IF indicator_type_param NOT IN ('ip', 'domain', 'url', 'email', 'hash') THEN
        RETURN FALSE;
    END IF;
    
    IF threat_name_param IS NULL OR length(threat_name_param) < 3 THEN
        RETURN FALSE;
    END IF;
    
    -- Type-specific validation
    CASE indicator_type_param
        WHEN 'ip' THEN
            -- Validate IP format (simple check)
            RETURN indicator_value_param ~ '^([0-9]{1,3}\.){3}[0-9]{1,3}$' OR 
                   indicator_value_param ~ '^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$';
        
        WHEN 'domain' THEN
            -- Validate domain format
            RETURN indicator_value_param ~ '^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$';
        
        WHEN 'email' THEN
            -- Validate email format
            RETURN indicator_value_param ~ '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$';
        
        WHEN 'hash' THEN
            -- Validate hash format (MD5, SHA1, SHA256)
            RETURN length(indicator_value_param) IN (32, 40, 64) AND 
                   indicator_value_param ~ '^[a-fA-F0-9]+$';
        
        ELSE
            RETURN TRUE;
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- PERFORMANCE OPTIMIZATION VIEWS
-- ==============================================================================

-- View for fast threat intelligence lookups
CREATE VIEW fast_threat_lookup AS
SELECT 
    t.indicator_type,
    t.indicator_value,
    t.threat_name,
    t.threat_severity,
    t.confidence_score,
    t.is_active,
    t.first_seen,
    t.last_seen
FROM threat_intelligence_indicators t
WHERE t.is_active = TRUE
    AND t.is_validated = TRUE
    AND t.confidence_score >= 0.7;

-- View for recent malicious activity
CREATE VIEW recent_malicious_activity AS
SELECT 
    'domain' as entity_type,
    domain as entity_value,
    threat_severity,
    confidence_score,
    last_seen,
    threat_type
FROM domains_intelligence
WHERE is_malicious = TRUE
    AND last_seen >= NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'ip' as entity_type,
    ip_address::text as entity_value,
    threat_severity,
    confidence_score,
    last_seen,
    threat_type
FROM ip_addresses_reputation
WHERE is_malicious = TRUE
    AND last_seen >= NOW() - INTERVAL '7 days'

ORDER BY last_seen DESC;

-- ==============================================================================
-- MAINTENANCE AND CLEANUP PROCEDURES
-- ==============================================================================

-- Procedure to clean up old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(cleanup_before_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM validation_audit_log 
    WHERE created_at < NOW() - INTERVAL '1 day' * cleanup_before_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RAISE NOTICE 'Cleaned up % old audit log entries', deleted_count;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Procedure to update prediction accuracy metrics
CREATE OR REPLACE FUNCTION update_prediction_accuracy()
RETURNS void AS $$
BEGIN
    -- Update accuracy metrics for ML predictions with ground truth
    UPDATE ml_model_predictions m
    SET model_accuracy = CASE 
        WHEN m.feedback_score >= 4 THEN 1.0
        WHEN m.feedback_score = 3 THEN 0.7
        WHEN m.feedback_score = 2 THEN 0.3
        ELSE 0.0
    END
    WHERE m.feedback_score IS NOT NULL
    AND m.ground_truth IS NOT NULL;
    
    RAISE NOTICE 'Updated accuracy metrics for ML predictions';
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- SAMPLE DATA FOR TESTING
-- ==============================================================================

-- Insert sample threat feed source
INSERT INTO threat_feed_sources (name, description, source_type, data_format, created_by) VALUES
('MISP Threat Sharing', 'Open source threat intelligence platform', 'community', 'stix', 'system'),
('Commercial Threat Feed', 'Commercial threat intelligence provider', 'commercial', 'json', 'security_team');

-- Insert sample domains intelligence
INSERT INTO domains_intelligence (domain, registrable_domain, apex_domain, threat_type, threat_severity, confidence_score, is_malicious, created_by) VALUES
('malicious-example.com', 'example.com', 'example.com', 'malware', 'high', 0.95, TRUE, 'system'),
('legitimate-business.com', 'business.com', 'business.com', 'legitimate', 'low', 0.1, FALSE, 'security_team');

-- Insert sample IP reputation
INSERT INTO ip_addresses_reputation (ip_address, threat_type, threat_severity, confidence_score, is_malicious, created_by) VALUES
('192.168.1.100', 'malware', 'high', 0.90, TRUE, 'system'),
('8.8.8.8', 'legitimate', 'low', 0.05, FALSE, 'security_team');

-- Insert sample email validation
INSERT INTO email_addresses_validation (email, local_part, domain_part, validation_status, is_valid_syntax, is_valid_domain, is_valid_mx_record, source_type, source_reference) VALUES
('user@malicious.com', 'user', 'malicious.com', 'invalid', TRUE, TRUE, FALSE, 'api', 'bulk_validation_001'),
('admin@legitimate.com', 'admin', 'legitimate.com', 'valid', TRUE, TRUE, TRUE, 'api', 'bulk_validation_001');

-- ==============================================================================
-- END OF SCHEMA DEFINITION
-- ==============================================================================

-- Final verification query
SELECT 
    'Schema creation completed successfully' as status,
    count(*) as table_count
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
AND table_name LIKE '%_%' OR table_name LIKE '%intelligence%';

