-- ==============================================================================
-- Schema Validation Script
-- ==============================================================================
-- This script validates that the security intelligence schema was created correctly
-- Run this after executing postgresql_schema.sql to verify successful installation
-- ==============================================================================

-- Check that all required extensions are installed
DO $$
BEGIN
    RAISE NOTICE 'Validating required extensions...';
    
    -- Check uuid-ossp
    PERFORM 1 FROM pg_extension WHERE extname = 'uuid-ossp';
    IF FOUND THEN
        RAISE NOTICE '✓ uuid-ossp extension is installed';
    ELSE
        RAISE EXCEPTION '✗ uuid-ossp extension is NOT installed';
    END IF;
    
    -- Check pgcrypto
    PERFORM 1 FROM pg_extension WHERE extname = 'pgcrypto';
    IF FOUND THEN
        RAISE NOTICE '✓ pgcrypto extension is installed';
    ELSE
        RAISE EXCEPTION '✗ pgcrypto extension is NOT installed';
    END IF;
    
    -- Check citext
    PERFORM 1 FROM pg_extension WHERE extname = 'citext';
    IF FOUND THEN
        RAISE NOTICE '✓ citext extension is installed';
    ELSE
        RAISE EXCEPTION '✗ citext extension is NOT installed';
    END IF;
    
    -- Check ip4r
    PERFORM 1 FROM pg_extension WHERE extname = 'ip4r';
    IF FOUND THEN
        RAISE NOTICE '✓ ip4r extension is installed';
    ELSE
        RAISE EXCEPTION '✗ ip4r extension is NOT installed';
    END IF;
    
    -- Check pg_trgm
    PERFORM 1 FROM pg_extension WHERE extname = 'pg_trgm';
    IF FOUND THEN
        RAISE NOTICE '✓ pg_trgm extension is installed';
    ELSE
        RAISE EXCEPTION '✗ pg_trgm extension is NOT installed';
    END IF;
    
END $$;

-- Verify all 13 tables exist
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    RAISE NOTICE 'Validating core security tables...';
    
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE'
    AND table_name IN (
        'threat_feed_sources',
        'domains_intelligence', 
        'ip_addresses_reputation',
        'email_addresses_validation',
        'sender_reputation_scoring',
        'threat_intelligence_indicators',
        'malware_signatures',
        'phishing_urls_database',
        'spam_patterns_database',
        'blacklists_aggregation',
        'validation_audit_log',
        'ml_model_predictions',
        'attack_campaigns_tracking'
    );
    
    IF table_count = 13 THEN
        RAISE NOTICE '✓ All 13 core security tables exist';
    ELSE
        RAISE EXCEPTION '✗ Only % of 13 required tables exist', table_count;
    END IF;
    
END $$;

-- Check custom types
DO $$
DECLARE
    type_count INTEGER;
BEGIN
    RAISE NOTICE 'Validating custom data types...';
    
    SELECT COUNT(*) INTO type_count
    FROM pg_type 
    WHERE typname IN (
        'domain_threat_type',
        'ip_threat_type',
        'email_validation_status',
        'threat_severity',
        'confidence_level',
        'campaign_status',
        'prediction_status'
    );
    
    IF type_count = 7 THEN
        RAISE NOTICE '✓ All 7 custom types exist';
    ELSE
        RAISE EXCEPTION '✗ Only % of 7 required types exist', type_count;
    END IF;
    
END $$;

-- Verify views exist
DO $$
DECLARE
    view_count INTEGER;
BEGIN
    RAISE NOTICE 'Validating analytics views...';
    
    SELECT COUNT(*) INTO view_count
    FROM information_schema.views
    WHERE table_schema = 'public'
    AND table_name IN (
        'high_risk_domains',
        'malicious_ip_addresses',
        'active_phishing_urls',
        'ml_predictions_requiring_review',
        'fast_threat_lookup',
        'recent_malicious_activity'
    );
    
    IF view_count = 6 THEN
        RAISE NOTICE '✓ All 6 analytics views exist';
    ELSE
        RAISE EXCEPTION '✗ Only % of 6 required views exist', view_count;
    END IF;
    
END $$;

-- Check functions exist
DO $$
DECLARE
    function_count INTEGER;
BEGIN
    RAISE NOTICE 'Validating utility functions...';
    
    SELECT COUNT(*) INTO function_count
    FROM information_schema.routines
    WHERE routine_schema = 'public'
    AND routine_type = 'FUNCTION'
    AND routine_name IN (
        'update_updated_at_column',
        'anonymize_ip_address',
        'calculate_domain_reputation',
        'validate_threat_indicator',
        'cleanup_old_audit_logs',
        'update_prediction_accuracy'
    );
    
    IF function_count = 6 THEN
        RAISE NOTICE '✓ All 6 utility functions exist';
    ELSE
        RAISE EXCEPTION '✗ Only % of 6 required functions exist', function_count;
    END IF;
    
END $$;

-- Check triggers exist
DO $$
DECLARE
    trigger_count INTEGER;
BEGIN
    RAISE NOTICE 'Validating automatic triggers...';
    
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers
    WHERE event_object_schema = 'public'
    AND trigger_name LIKE '%updated_at%';
    
    IF trigger_count = 13 THEN
        RAISE NOTICE '✓ All 13 updated_at triggers exist';
    ELSE
        RAISE EXCEPTION '✗ Only % of 13 required triggers exist', trigger_count;
    END IF;
    
END $$;

-- Test sample data
DO $$
BEGIN
    RAISE NOTICE 'Validating sample data...';
    
    -- Check threat feed sources
    IF (SELECT COUNT(*) FROM threat_feed_sources) > 0 THEN
        RAISE NOTICE '✓ Threat feed sources contain data';
    ELSE
        RAISE EXCEPTION '✗ No threat feed sources found';
    END IF;
    
    -- Check domains intelligence
    IF (SELECT COUNT(*) FROM domains_intelligence) > 0 THEN
        RAISE NOTICE '✓ Domains intelligence contains data';
    ELSE
        RAISE EXCEPTION '✗ No domains intelligence found';
    END IF;
    
END $$;

-- Test utility functions
DO $$
BEGIN
    RAISE NOTICE 'Testing utility functions...';
    
    -- Test IP anonymization
    IF anonymize_ip_address('192.168.1.100'::inet) = '192.168.1.0'::inet THEN
        RAISE NOTICE '✓ IP anonymization function works';
    ELSE
        RAISE EXCEPTION '✗ IP anonymization function failed';
    END IF;
    
END $$;

-- Final validation message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════════';
    RAISE NOTICE '✅ SCHEMA VALIDATION COMPLETED SUCCESSFULLY';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════════';
    RAISE NOTICE '';
    RAISE NOTICE 'Your PostgreSQL Security Intelligence Schema is ready for use!';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Connect to your database';
    RAISE NOTICE '2. Run: \i validate_schema.sql';
    RAISE NOTICE '3. Start importing threat intelligence data';
    RAISE NOTICE '4. Monitor performance and adjust indexes as needed';
    RAISE NOTICE '';
    RAISE NOTICE 'Documentation: See README.md for usage examples';
    RAISE NOTICE '';
    
END $$;
