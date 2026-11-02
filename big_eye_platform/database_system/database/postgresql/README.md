# PostgreSQL Security Intelligence Schema

## Overview
This comprehensive PostgreSQL schema is designed for security intelligence, threat detection, and machine learning-based analysis. It includes 13 core security tables with complete data types, indexes, constraints, relationships, and detailed documentation.

## Schema Components

### Core Security Tables

1. **threat_feed_sources** - Threat intelligence feed sources and characteristics
2. **domains_intelligence** - Domain reputation and threat intelligence data
3. **ip_addresses_reputation** - IP address reputation and threat classifications
4. **email_addresses_validation** - Email validation and verification results
5. **sender_reputation_scoring** - Sender reputation metrics and ML-based scoring
6. **threat_intelligence_indicators** - Indicators of Compromise (IOCs) from feeds
7. **malware_signatures** - Malware signature definitions for detection systems
8. **phishing_urls_database** - Known phishing URLs and threat assessments
9. **spam_patterns_database** - Spam detection patterns and machine learning rules
10. **blacklists_aggregation** - Aggregated blacklist data from multiple sources
11. **validation_audit_log** - Comprehensive audit trail for security validations
12. **ml_model_predictions** - ML model predictions and confidence scores
13. **attack_campaigns_tracking** - Security attack campaigns and threat actors

### Key Features

- **Comprehensive Security Data**: Tracks domains, IPs, emails, threats, and attack campaigns
- **Machine Learning Integration**: Built-in support for ML predictions and model performance tracking
- **Audit Trail**: Complete validation and decision audit logging for compliance
- **Performance Optimized**: Strategic indexing for fast lookups and analysis
- **Extensible Design**: Custom types and constraints for security data validation
- **Real-time Updates**: Automatic timestamp tracking and status management

## Installation

1. **Create Database**:
```sql
CREATE DATABASE security_intelligence;
```

2. **Install Required Extensions**:
```sql
\c security_intelligence;
\i postgresql_schema.sql
```

The schema will automatically install required extensions:
- uuid-ossp (UUID generation)
- pgcrypto (encryption functions)
- citext (case-insensitive text)
- ip4r (IP address handling)
- pg_trgm (trigram search)

## Usage Examples

### Query High-Risk Domains
```sql
SELECT * FROM high_risk_domains ORDER BY confidence_score DESC LIMIT 10;
```

### Check IP Reputation
```sql
SELECT * FROM malicious_ip_addresses 
WHERE country_code = 'US' 
ORDER BY last_seen DESC;
```

### Analyze Phishing Campaigns
```sql
SELECT phishing_type, COUNT(*) as url_count, AVG(confidence_score) as avg_confidence
FROM active_phishing_urls 
GROUP BY phishing_type 
ORDER BY url_count DESC;
```

### Review ML Predictions
```sql
SELECT * FROM ml_predictions_requiring_review;
```

### Track Attack Campaigns
```sql
SELECT campaign_name, threat_severity, campaign_status, impact_score
FROM attack_campaigns_tracking 
WHERE is_active = TRUE 
ORDER BY start_date DESC;
```

## Custom Types

### Enumerations
- `domain_threat_type` - Types of domain threats (malware, phishing, spam, etc.)
- `ip_threat_type` - Types of IP threats (botnet, DDoS, scanner, etc.)
- `email_validation_status` - Email validation states (valid, invalid, disposable, etc.)
- `threat_severity` - Security threat severity levels (low, medium, high, critical)
- `confidence_level` - Confidence levels (very_low to very_high)
- `campaign_status` - Attack campaign status (active, contained, resolved)
- `prediction_status` - ML prediction status (pending, processing, completed, failed)

## Views

The schema includes several pre-built views for common queries:

- `high_risk_domains` - Domains with high/critical severity and high confidence
- `malicious_ip_addresses` - IP addresses marked as malicious with high confidence
- `active_phishing_urls` - Active phishing URLs with high confidence scores
- `ml_predictions_requiring_review` - ML predictions needing human review
- `fast_threat_lookup` - Quick threat intelligence lookups
- `recent_malicious_activity` - Recent malicious activity across all entity types

## Functions

### Utility Functions
- `anonymize_ip_address(ip)` - GDPR-compliant IP anonymization
- `calculate_domain_reputation(domain)` - Domain reputation scoring
- `validate_threat_indicator()` - Threat indicator validation
- `cleanup_old_audit_logs()` - Clean up old audit log entries
- `update_prediction_accuracy()` - Update ML prediction accuracy metrics

### Automatic Triggers
All tables include automatic `updated_at` timestamp triggers for tracking changes.

## Performance Considerations

### Indexing Strategy
- **Primary Keys**: UUID-based primary keys for all tables
- **Foreign Keys**: Indexed for join performance
- **Search Fields**: GIN indexes for array fields, B-tree for standard fields
- **Time-based Fields**: Descending indexes for recent data queries
- **Full-text Search**: GIN indexes on text content fields

### Query Optimization
- Composite indexes for multi-column lookups
- Partial indexes for active records only
- Specialized indexes (GIST for IP ranges, GIN for arrays)

## Security Features

### Data Protection
- Case-insensitive email validation
- IP address anonymization functions
- GDPR compliance helpers
- Comprehensive audit logging

### Data Integrity
- Domain format validation
- Email syntax checking
- IP address validation
- Hash format validation
- STIX ID format verification

## Maintenance

### Regular Cleanup
```sql
-- Clean up audit logs older than 1 year
SELECT cleanup_old_audit_logs(365);

-- Update ML prediction accuracy metrics
SELECT update_prediction_accuracy();
```

### Monitoring
```sql
-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_tup_read DESC;
```

## Integration Examples

### Python Integration
```python
import psycopg2
from datetime import datetime

# Connect to database
conn = psycopg2.connect("dbname=security_intelligence user=postgres")
cur = conn.cursor()

# Add new threat intelligence indicator
cur.execute("""
    INSERT INTO threat_intelligence_indicators 
    (indicator_value, indicator_type, threat_name, threat_severity, created_by)
    VALUES (%s, %s, %s, %s, %s)
""", ('example.com', 'domain', 'Known Malware Domain', 'high', 'security_team'))

conn.commit()
```

### API Integration
The schema is designed to work with REST APIs and real-time threat intelligence feeds. Use the validation functions and audit logging to ensure data quality and compliance.

## Contributing

When adding new tables or modifications:

1. Follow the established naming conventions
2. Include comprehensive comments
3. Add appropriate indexes
4. Create validation constraints
5. Update this README
6. Test with sample data

## License

This schema is provided as-is for security intelligence and threat detection purposes. Ensure compliance with applicable data protection regulations when implementing in production environments.

## Support

For issues or questions about this schema:
1. Review the inline comments in the SQL file
2. Check the sample data and queries provided
3. Consult the PostgreSQL documentation for advanced features

## Version History

- **v1.0** (2025-10-30): Initial release with 13 core security tables
  - Complete threat intelligence data model
  - ML prediction tracking
  - Comprehensive audit logging
  - Performance-optimized indexing
  - Security validation functions
