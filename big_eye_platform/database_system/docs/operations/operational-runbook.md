# Operational Runbook

## Table of Contents
1. [Overview](#overview)
2. [Daily Operations](#daily-operations)
3. [Weekly Operations](#weekly-operations)
4. [Monthly Operations](#monthly-operations)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Emergency Procedures](#emergency-procedures)
7. [Backup and Recovery](#backup-and-recovery)
8. [Performance Monitoring](#performance-monitoring)
9. [Security Maintenance](#security-maintenance)
10. [Incident Response](#incident-response)

## Overview

This operational runbook provides step-by-step procedures for maintaining and operating the Cybersecurity Threat Intelligence System. It covers routine operations, maintenance tasks, and emergency procedures.

**System Components**:
- FastAPI REST API Service
- PostgreSQL Database
- MongoDB Database  
- Redis Cache
- Prometheus Monitoring
- Grafana Dashboards
- ELK Stack (Elasticsearch, Logstash, Kibana)

**Contact Information**:
- Primary Operations: ops@yourdomain.com
- Emergency Contact: +1-555-EMERGENCY
- Security Team: security@yourdomain.com
- Database Administrator: dba@yourdomain.com

## Daily Operations

### 1. System Health Check

**Frequency**: Every 4 hours during business hours
**Estimated Time**: 10 minutes

#### 1.1 Check API Service Status
```bash
# Check API service status
curl -f https://api.yourdomain.com/health || echo "API Health Check Failed"

# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health

# Check API error logs
tail -f /var/log/threat-intel/api/error.log | grep ERROR
```

#### 1.2 Database Health Check
```bash
# PostgreSQL connectivity
psql -h localhost -U app_user -d threatintel -c "SELECT version();"

# PostgreSQL connection count
psql -h localhost -U app_user -d threatintel -c "
SELECT count(*) as active_connections, 
       state, 
       usename 
FROM pg_stat_activity 
WHERE state = 'active' 
GROUP BY state, usename;"

# MongoDB connectivity
mongo --host localhost --eval "db.adminCommand('ismaster')"

# MongoDB operation count
mongo --host localhost --eval "db.adminCommand('serverStatus').opcounters"
```

#### 1.3 Redis Cache Check
```bash
# Redis connectivity and memory usage
redis-cli -h localhost info memory | grep used_memory_human

# Redis key count
redis-cli -h localhost dbsize

# Check slow queries
redis-cli -h localhost slowlog get 10
```

#### 1.4 Monitoring Systems Check
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Check Grafana dashboards accessibility
curl -f http://localhost:3000/api/health || echo "Grafana Health Check Failed"

# Check Elasticsearch cluster health
curl -s http://localhost:9200/_cluster/health | jq '.status'
```

### 2. System Metrics Review

**Frequency**: Once daily (9:00 AM)
**Estimated Time**: 15 minutes

#### 2.1 Key Performance Indicators
Review these Grafana dashboards:
- **System Overview Dashboard**: CPU, Memory, Disk usage
- **API Performance Dashboard**: Response times, request rates, error rates
- **Database Performance Dashboard**: Query performance, connection counts
- **Cache Performance Dashboard**: Hit rates, memory usage

#### 2.2 Critical Metrics Thresholds
| Metric | Warning Threshold | Critical Threshold | Action Required |
|--------|-------------------|--------------------|-----------------|
| API Response Time | > 500ms | > 1000ms | Investigate performance |
| API Error Rate | > 1% | > 5% | Immediate investigation |
| Database Connections | > 80% | > 95% | Scale or investigate |
| Disk Space | > 80% | > 90% | Clean up or add storage |
| Memory Usage | > 85% | > 95% | Scale or investigate |
| Cache Hit Rate | < 80% | < 60% | Review cache configuration |

#### 2.3 Log Analysis
```bash
# Check for critical errors in the last 24 hours
journalctl --since "24 hours ago" --priority=3 | grep -i "threat.intel"

# Check API error patterns
grep "ERROR" /var/log/threat-intel/api/app.log | tail -20

# Check authentication failures
grep "authentication failed" /var/log/threat-intel/api/app.log | tail -10

# Check database error patterns
grep "ERROR" /var/log/postgresql/postgresql-*.log | tail -20
```

### 3. Data Quality Checks

**Frequency**: Once daily (10:00 AM)
**Estimated Time**: 10 minutes

#### 3.1 Data Consistency Checks
```sql
-- Check for orphaned threat intelligence records
SELECT ti.id, ti.indicator_type, ti.indicator_value, ti.created_at
FROM threat_intelligence ti
LEFT JOIN threat_sources ts ON ti.source_id = ts.id
WHERE ts.id IS NULL;

-- Check for duplicate IP addresses with different scores
SELECT ip_address, COUNT(*) as count
FROM ip_analysis 
GROUP BY ip_address 
HAVING COUNT(*) > 1;

-- Check for invalid email domains
SELECT email, email_domain, created_at
FROM email_analysis 
WHERE email_domain !~ '^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$';
```

#### 3.2 Data Freshness Check
```sql
-- Check last update times for threat intelligence sources
SELECT source_name, 
       COUNT(*) as record_count,
       MAX(last_seen) as latest_entry,
       NOW() - MAX(last_seen) as time_since_update
FROM threat_intelligence ti
JOIN threat_sources ts ON ti.source_id = ts.id
GROUP BY source_name
ORDER BY time_since_update DESC;

-- Check for stale reputation data
SELECT indicator_type, indicator_value, 
       last_updated,
       NOW() - last_updated as age
FROM reputation_intelligence 
WHERE NOW() - last_updated > INTERVAL '7 days';
```

### 4. External API Health Check

**Frequency**: Once daily (11:00 AM)
**Estimated Time**: 5 minutes

#### 4.1 Threat Intelligence Source Status
```bash
#!/bin/bash
# External API health check script

APIS=(
    "VirusTotal:https://www.virustotal.com/api/v3"
    "AbuseIPDB:https://api.abuseipdb.com/api/v2"
    "Shodan:https://api.shodan.io"
    "GreyNoise:https://api.greynoise.io/v3"
    "OTX:https://otx.alienvault.com/api/v1"
)

for api in "${APIS[@]}"; do
    IFS=':' read -r name url <<< "$api"
    echo "Checking $name API..."
    
    case $name in
        "VirusTotal")
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "x-apikey: $VIRUSTOTAL_API_KEY" "$url/files/scan" -X POST)
            ;;
        "AbuseIPDB")
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "Key: $ABUSEIPDB_API_KEY" "$url/check/127.0.0.1")
            ;;
        "Shodan")
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Shodan-API-Key: $SHODAN_API_KEY" "$url/host/127.0.0.1")
            ;;
        "GreyNoise")
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "X-GreyNoise-API-Key: $GREYNOISE_API_KEY" "$url/v2/noise/query?ip=127.0.0.1")
            ;;
        "OTX")
            response=$(curl -s -o /dev/null -w "%{http_code}" -H "X-OTX-API-KEY: $OTX_API_KEY" "$url/subscriptions/list")
            ;;
    esac
    
    if [ "$response" = "200" ] || [ "$response" = "401" ]; then
        echo "$name API: OK ($response)"
    else
        echo "$name API: FAILED ($response)"
    fi
done
```

## Weekly Operations

### 1. Performance Analysis

**Frequency**: Every Monday (2:00 PM)
**Estimated Time**: 30 minutes

#### 1.1 Database Performance Analysis
```sql
-- Top 10 slowest queries
SELECT query, 
       calls,
       total_time,
       mean_time,
       rows,
       100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Index usage analysis
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('threat_intelligence', 'email_analysis', 'url_analysis', 'ip_analysis')
ORDER BY tablename, attname;

-- Table size analysis
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE tablename IN ('threat_intelligence', 'email_analysis', 'url_analysis', 'ip_analysis')
ORDER BY tablename, attname;

-- Check for unused indexes
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY tablename, indexname;
```

#### 1.2 Cache Performance Analysis
```bash
# Redis memory analysis
redis-cli -h localhost --bigkeys

# Cache hit rate analysis
redis-cli -h localhost info stats | grep keyspace

# Slow query log analysis
redis-cli -h localhost slowlog len
redis-cli -h localhost slowlog get 100 | head -50
```

### 2. Security Review

**Frequency**: Every Wednesday (10:00 AM)
**Estimated Time**: 20 minutes

#### 2.1 Access Log Analysis
```bash
# Failed authentication attempts
grep "authentication failed" /var/log/threat-intel/api/app.log | \
    awk '{print $1}' | sort | uniq -c | sort -nr | head -10

# Suspicious IP addresses
grep "suspicious activity" /var/log/threat-intel/api/app.log | \
    awk '{print $1}' | sort | uniq -c | sort -nr | head -10

# Rate limit violations
grep "rate limit exceeded" /var/log/threat-intel/api/app.log | \
    awk '{print $1}' | sort | uniq -c | sort -nr | head -10
```

#### 2.2 Database Security Check
```sql
-- Check user privileges
SELECT usename, usesuper, usecreatedb FROM pg_user;

-- Check recent failed login attempts
SELECT user_name, ip_address, attempt_time, failure_reason
FROM authentication_logs
WHERE attempt_time > NOW() - INTERVAL '7 days'
  AND success = false
ORDER BY attempt_time DESC;

-- Check for privilege escalation attempts
SELECT * FROM security_audit_log
WHERE action = 'privilege_escalation_attempt'
  AND timestamp > NOW() - INTERVAL '7 days';
```

### 3. Capacity Planning Review

**Frequency**: Every Friday (3:00 PM)
**Estimated Time**: 15 minutes

#### 3.1 Storage Analysis
```bash
# Database storage usage
psql -h localhost -U app_user -d threatintel -c "
SELECT 
    pg_size_pretty(pg_database_size('threatintel')) as database_size,
    (SELECT pg_size_pretty(pg_relation_size('threat_intelligence'))) as threat_intelligence_size,
    (SELECT pg_size_pretty(pg_relation_size('email_analysis'))) as email_analysis_size,
    (SELECT pg_size_pretty(pg_relation_size('url_analysis'))) as url_analysis_size,
    (SELECT pg_size_pretty(pg_relation_size('ip_analysis'))) as ip_analysis_size;"

# MongoDB storage usage
mongo --host localhost threatintel --eval "
db.stats().dataSize;
db.threatIntelligence.find().count();
db.emailAnalysis.find().count();
db.urlAnalysis.find().count();
db.ipAnalysis.find().count();"

# Redis memory usage
redis-cli -h localhost info memory
```

#### 3.2 Growth Trend Analysis
Review Grafana dashboards for:
- Storage consumption trends over the past month
- Database growth rate
- API request volume trends
- Cache usage patterns

## Monthly Operations

### 1. System Maintenance

**Frequency**: First Sunday of each month (2:00 AM)
**Estimated Time**: 2 hours

#### 1.1 Database Maintenance
```sql
-- Update table statistics
ANALYZE;

-- Reindex critical tables
REINDEX INDEX CONCURRENTLY idx_threat_intelligence_composite;
REINDEX INDEX CONCURRENTLY idx_email_analysis_domain;
REINDEX INDEX CONCURRENTLY idx_url_analysis_url_hash;
REINDEX INDEX CONCURRENTLY idx_ip_analysis_ip_address;

-- Vacuum tables to reclaim space
VACUUM (VERBOSE, ANALYZE) threat_intelligence;
VACUUM (VERBOSE, ANALYZE) email_analysis;
VACUUM (VERBOSE, ANALYZE) url_analysis;
VACUUM (VERBOSE, ANALYZE) ip_analysis;

-- Clean up old logs
DELETE FROM api_logs WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM security_audit_log WHERE timestamp < NOW() - INTERVAL '90 days';
```

#### 1.2 Archive Old Data
```bash
# Create database backup before cleanup
pg_dump -h localhost -U app_user threatintel > /backup/pre-maintenance-$(date +%Y%m%d).sql

# Archive old threat intelligence data to cold storage
psql -h localhost -U app_user -d threatintel << EOF
-- Move old data to archive tables
INSERT INTO threat_intelligence_archive 
SELECT * FROM threat_intelligence 
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM threat_intelligence 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Move old API logs to archive
INSERT INTO api_logs_archive 
SELECT * FROM api_logs 
WHERE created_at < NOW() - INTERVAL '30 days';

DELETE FROM api_logs 
WHERE created_at < NOW() - INTERVAL '30 days';
EOF
```

### 2. Security Audit

**Frequency**: First Monday of each month (9:00 AM)
**Estimated Time**: 4 hours

#### 2.1 Comprehensive Security Review
```bash
# Update security patches
apt update && apt list --upgradable | grep security
apt upgrade -y

# Check SSL certificates expiration
openssl x509 -in /etc/ssl/certs/threat-intel.crt -noout -dates

# Review firewall rules
iptables -L -n -v

# Check for security updates
docker pull --platform linux/amd64 postgres:15
docker pull --platform linux/amd64 mongo:6.0
docker pull --platform linux/amd64 redis:7-alpine
```

#### 2.2 Compliance Check
```sql
-- GDPR compliance check - data retention
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count,
    (SELECT COUNT(*) FROM information_schema.column_privileges WHERE table_name = t.table_name) as privilege_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE';

-- Access audit for the past month
SELECT user_name, 
       action,
       resource_type,
       COUNT(*) as action_count,
       MIN(timestamp) as first_action,
       MAX(timestamp) as last_action
FROM security_audit_log
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY user_name, action, resource_type
ORDER BY action_count DESC;
```

### 3. Performance Optimization

**Frequency**: Second Sunday of each month (3:00 AM)
**Estimated Time**: 3 hours

#### 3.1 Database Optimization
```sql
-- Check for query optimization opportunities
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM threat_intelligence 
WHERE confidence_score > 0.8 
  AND is_active = true 
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY confidence_score DESC;

-- Analyze index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Update cost-based optimizer statistics
ANALYZE VERBOSE;
```

#### 3.2 Cache Optimization
```bash
# Analyze cache patterns
redis-cli -h localhost --scan --pattern "*threat*"

# Clear expired cache entries
redis-cli -h localhost EVAL "
local keys = redis.call('KEYS', '*')
local expired = 0
for i=1,#keys do
  if redis.call('TTL', keys[i]) == -1 then
    redis.call('DEL', keys[i])
    expired = expired + 1
  end
end
return expired
" 0

# Optimize cache key structure
redis-cli -h localhost CONFIG SET maxmemory-policy allkeys-lru
```

## Maintenance Procedures

### 1. Regular Maintenance Windows

**Scheduled Maintenance**: Sundays 2:00 AM - 4:00 AM EST
**Emergency Maintenance**: 24/7 as needed

#### 1.1 Pre-Maintenance Checklist
```bash
#!/bin/bash
# Pre-maintenance checklist

echo "=== Pre-Maintenance Checklist ==="

# Check current system load
uptime
free -h
df -h

# Verify backup status
ls -la /backup/daily/
echo "Latest backup: $(ls -t /backup/daily/ | head -1)"

# Check running services
systemctl status threat-intel-api
systemctl status postgresql
systemctl status mongod
systemctl status redis-server

# Check active connections
ss -tulpn | grep -E "(8000|5432|27017|6379)"

# Notify stakeholders
echo "Maintenance window started at $(date)" >> /var/log/threat-intel/maintenance.log
```

#### 1.2 Maintenance Completion Checklist
```bash
#!/bin/bash
# Post-maintenance checklist

echo "=== Post-Maintenance Checklist ==="

# Restart services
systemctl restart threat-intel-api
systemctl restart postgresql
systemctl restart mongod
systemctl restart redis-server

# Wait for services to start
sleep 30

# Verify services are running
systemctl is-active threat-intel-api
systemctl is-active postgresql
systemctl is-active mongod
systemctl is-active redis-server

# Test API health
curl -f https://api.yourdomain.com/health

# Test database connectivity
psql -h localhost -U app_user -d threatintel -c "SELECT 1;"
mongo --host localhost --eval "db.adminCommand('ismaster')"
redis-cli -h localhost ping

# Clear cache
redis-cli -h localhost FLUSHDB

echo "Maintenance completed at $(date)" >> /var/log/threat-intel/maintenance.log
```

### 2. Database Maintenance Procedures

#### 2.1 PostgreSQL Maintenance
```sql
-- Routine maintenance procedure
BEGIN;

-- Update statistics
ANALYZE;

-- Reindex if needed (based on weekly analysis)
-- REINDEX INDEX CONCURRENTLY idx_slow_performing_index;

-- Clean up old data
DELETE FROM api_logs WHERE created_at < NOW() - INTERVAL '30 days';
DELETE FROM security_audit_log WHERE timestamp < NOW() - INTERVAL '90 days';

-- Vacuum tables
VACUUM ANALYZE threat_intelligence;
VACUUM ANALYZE email_analysis;
VACUUM ANALYZE url_analysis;
VACUUM ANALYZE ip_analysis;

-- Update materialized views
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_threat_statistics;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_reputation_summary;

COMMIT;
```

#### 2.2 MongoDB Maintenance
```javascript
// MongoDB maintenance script

// Compact collections
db.threatIntelligence.runCommand("compact", {force: false});
db.emailAnalysis.runCommand("compact", {force: false});
db.urlAnalysis.runCommand("compact", {force: false});
db.ipAnalysis.runCommand("compact", {force: false});

// Rebuild indexes if needed
db.threatIntelligence.reIndex();
db.emailAnalysis.reIndex();
db.urlAnalysis.reIndex();
db.ipAnalysis.reIndex();

// Clean up old data
db.apiLogs.remove({createdAt: {$lt: new Date(Date.now() - 30*24*60*60*1000)}});
db.securityAuditLog.remove({timestamp: {$lt: new Date(Date.now() - 90*24*60*60*1000)}});

// Check for orphaned documents
db.threatIntelligence.aggregate([
    {$lookup: {
        from: "threatSources",
        localField: "sourceId",
        foreignField: "_id",
        as: "source"
    }},
    {$match: {source: {$size: 0}}},
    {$count: "orphaned"}
]);
```

### 3. Application Updates

#### 3.1 API Service Updates
```bash
#!/bin/bash
# API update procedure

# Backup current version
cp -r /opt/threat-intel/api /backup/api-backup-$(date +%Y%m%d)

# Download new version
cd /opt/threat-intel
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Restart service
systemctl restart threat-intel-api

# Verify update
curl -f https://api.yourdomain.com/health
curl -f https://api.yourdomain.com/version
```

#### 3.2 Security Updates
```bash
#!/bin/bash
# Security update procedure

# Update system packages
apt update
apt list --upgradable | grep -i security
apt upgrade -y

# Update Docker images
docker pull postgres:15
docker pull mongo:6.0
docker pull redis:7-alpine

# Update API dependencies
cd /opt/threat-intel/api
pip install --upgrade -r requirements.txt

# Update SSL certificates if needed
certbot renew --dry-run

# Restart services
systemctl restart threat-intel-api
systemctl restart postgresql
systemctl restart mongod
systemctl restart redis-server
```

## Emergency Procedures

### 1. Service Outage Response

#### 1.1 API Service Outage
```bash
#!/bin/bash
# API outage response

# Check service status
systemctl status threat-intel-api

# Check logs for errors
journalctl -u threat-intel-api --since "5 minutes ago" --no-pager

# Check resource usage
htop
df -h
free -h

# Restart service if needed
systemctl restart threat-intel-api

# Verify recovery
curl -f https://api.yourdomain.com/health
```

#### 1.2 Database Outage
```bash
#!/bin/bash
# Database outage response

# Check PostgreSQL
systemctl status postgresql
psql -h localhost -U app_user -d threatintel -c "SELECT 1;"

# Check MongoDB
systemctl status mongod
mongo --host localhost --eval "db.adminCommand('ismaster')"

# Check connections
ss -tulpn | grep 5432
ss -tulpn | grep 27017

# Restart databases if needed
systemctl restart postgresql
systemctl restart mongod

# Wait and verify
sleep 30
psql -h localhost -U app_user -d threatintel -c "SELECT version();"
```

### 2. Performance Emergency

#### 2.1 High CPU/Memory Usage
```bash
#!/bin/bash
# Performance emergency response

# Identify resource-intensive processes
top -o %CPU
top -o %MEM

# Check database connections
psql -h localhost -U app_user -d threatintel -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check for slow queries
psql -h localhost -U app_user -d threatintel -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Clear cache if memory is low
echo "Clearing Redis cache..."
redis-cli -h localhost FLUSHDB

# Kill long-running queries if needed
psql -h localhost -U app_user -d threatintel << EOF
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < NOW() - INTERVAL '5 minutes';
EOF
```

### 3. Security Incident Response

#### 3.1 Security Breach Detection
```bash
#!/bin/bash
# Security incident response

# Check for suspicious activities
grep -i "authentication failed\|privilege escalation\|sql injection" /var/log/threat-intel/api/app.log | tail -50

# Check for unusual API usage patterns
awk '{print $1}' /var/log/threat-intel/api/access.log | sort | uniq -c | sort -nr | head -20

# Block suspicious IP addresses (temporary)
iptables -A INPUT -s SUSPICIOUS_IP -j DROP

# Enable enhanced logging
echo "LOG_LEVEL=DEBUG" >> /opt/threat-intel/.env
systemctl restart threat-intel-api

# Notify security team
echo "Security incident detected at $(date)" | mail -s "URGENT: Security Alert" security@yourdomain.com
```

## Backup and Recovery

### 1. Backup Procedures

#### 1.1 Automated Daily Backup
```bash
#!/bin/bash
# Daily backup script

BACKUP_DIR="/backup/daily"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h localhost -U app_user -d threatintel \
    --format=custom \
    --verbose \
    --file="$BACKUP_DIR/threatintel_$DATE.dump"

# MongoDB backup
mongodump --host localhost --db threatintel \
    --out="$BACKUP_DIR/mongodb_$DATE"

# Configuration backup
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    /opt/threat-intel/api/config/ \
    /etc/postgresql/ \
    /etc/mongod.conf \
    /etc/redis/redis.conf

# Remove backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

# Compress and move to offsite storage
aws s3 sync $BACKUP_DIR s3://threat-intel-backups/daily/
```

#### 1.2 Weekly Full Backup
```bash
#!/bin/bash
# Weekly full backup script

BACKUP_DIR="/backup/weekly"
DATE=$(date +%Y%m%d)

# Complete system backup
tar -czf "$BACKUP_DIR/system_$DATE.tar.gz" \
    /opt/threat-intel \
    /var/log/threat-intel \
    /etc/nginx \
    /etc/ssl

# Database logical backup
pg_dump -h localhost -U app_user -d threatintel \
    --format=plain \
    --clean \
    --create \
    --file="$BACKUP_DIR/threatintel_full_$DATE.sql"

# Upload to secure storage
aws s3 cp "$BACKUP_DIR/" s3://threat-intel-backups/weekly/ --recursive

# Verify backup integrity
pg_restore --list "$BACKUP_DIR/threatintel_$DATE.dump" > /dev/null
```

### 2. Recovery Procedures

#### 2.1 Database Recovery
```bash
#!/bin/bash
# Database recovery procedure

# Stop services
systemctl stop threat-intel-api
systemctl stop postgresql

# Restore PostgreSQL
pg_restore --host localhost --username app_user \
    --dbname threatintel \
    --verbose \
    /backup/daily/threatintel_latest.dump

# Restore MongoDB
mongorestore --host localhost --db threatintel \
    /backup/daily/mongodb_latest/threatintel/

# Start services
systemctl start postgresql
systemctl start threat-intel-api

# Verify recovery
psql -h localhost -U app_user -d threatintel -c "SELECT count(*) FROM threat_intelligence;"
```

#### 2.2 Configuration Recovery
```bash
#!/bin/bash
# Configuration recovery procedure

# Backup current config
cp -r /opt/threat-intel/api/config /opt/threat-intel/api/config.backup

# Restore configuration
tar -xzf /backup/config_latest.tar.gz -C /

# Restore permissions
chown -R threat-intel:threat-intel /opt/threat-intel
chmod -R 750 /opt/threat-intel/config

# Restart services
systemctl restart threat-intel-api
systemctl restart nginx
```

## Performance Monitoring

### 1. Real-time Monitoring

#### 1.1 Key Metrics Dashboard
Access Grafana dashboard: `https://monitoring.yourdomain.com/d/threat-intel-overview`

**Critical Metrics to Monitor**:
- API Response Time (P50, P95, P99)
- API Error Rate
- Database Connection Count
- Query Performance
- Cache Hit Rate
- Memory Usage
- Disk I/O

#### 1.2 Alert Thresholds
```
API Response Time > 1000ms for 5 minutes
API Error Rate > 5% for 2 minutes
Database Connections > 90% for 10 minutes
Cache Hit Rate < 60% for 15 minutes
Memory Usage > 90% for 5 minutes
Disk Space < 10% remaining
```

### 2. Performance Tuning

#### 2.1 Database Optimization
```sql
-- Monthly performance tuning
-- Check for missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename IN ('threat_intelligence', 'email_analysis', 'url_analysis', 'ip_analysis')
ORDER BY tablename, attname;

-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM threat_intelligence 
WHERE confidence_score > 0.8 
  AND is_active = true 
ORDER BY confidence_score DESC;

-- Update table statistics
ANALYZE threat_intelligence;
ANALYZE email_analysis;
ANALYZE url_analysis;
ANALYZE ip_analysis;
```

#### 2.2 Cache Optimization
```bash
# Monthly cache analysis
redis-cli -h localhost --bigkeys

# Check cache patterns
redis-cli -h localhost --scan --pattern "*threat*" | wc -l

# Optimize cache memory
redis-cli -h localhost MEMORY PURGE

# Update cache configuration
redis-cli -h localhost CONFIG SET maxmemory-policy allkeys-lru
```

## Security Maintenance

### 1. Access Control Review

#### 1.1 User Access Audit
```sql
-- Monthly user access review
SELECT 
    username,
    role,
    last_login,
    created_at,
    is_active
FROM users
WHERE is_active = true
ORDER BY last_login DESC;

-- Check for dormant accounts
SELECT username, last_login
FROM users
WHERE last_login < NOW() - INTERVAL '90 days'
  AND is_active = true;
```

#### 1.2 Permission Review
```sql
-- Review user permissions
SELECT 
    u.username,
    ur.role_name,
    p.permission_name,
    p.description
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN role_permissions rp ON ur.role_id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = true
ORDER BY u.username, ur.role_name;
```

### 2. Security Updates

#### 2.1 Monthly Security Patch Cycle
```bash
#!/bin/bash
# Security update procedure

# Update system packages
apt update
apt list --upgradable | grep -i security
apt upgrade -y

# Update Docker images
docker pull --platform linux/amd64 postgres:15
docker pull --platform linux/amd64 mongo:6.0
docker pull --platform linux/amd64 redis:7-alpine

# Update Python dependencies
cd /opt/threat-intel/api
pip install --upgrade -r requirements.txt

# Update SSL certificates
certbot renew --quiet

# Run security scan
nmap -sS -O localhost

# Restart services
systemctl restart threat-intel-api
```

## Incident Response

### 1. Incident Classification

**Severity Levels**:
- **P0 (Critical)**: Complete system outage, data breach, security incident
- **P1 (High)**: Major functionality degraded, performance severely impacted
- **P2 (Medium)**: Minor functionality issues, limited user impact
- **P3 (Low)**: Cosmetic issues, feature requests

### 2. Response Procedures

#### 2.1 P0 Critical Incident
```bash
#!/bin/bash
# Critical incident response

# Immediate actions
echo "$(date): P0 Critical incident detected" >> /var/log/threat-intel/incidents.log

# Activate incident response team
echo "P0 Incident: System Down" | mail -s "CRITICAL INCIDENT" incident-response@yourdomain.com

# Execute emergency procedures
# - Isolate affected systems
# - Activate backup systems
# - Notify stakeholders
# - Document all actions

# Communication plan
# - Internal: Slack #incident-response
# - External: Status page updates
# - Customer: Email notifications
```

#### 2.2 Incident Documentation Template
```markdown
# Incident Report

**Incident ID**: INC-2024-XXX
**Date/Time**: YYYY-MM-DD HH:MM:SS UTC
**Severity**: P0/P1/P2/P3
**Status**: Open/Investigating/Resolved/Closed

## Summary
Brief description of the incident.

## Impact
- Users affected: X
- Duration: X hours
- Business impact: X

## Timeline
- HH:MM: Issue detected
- HH:MM: Investigation started
- HH:MM: Root cause identified
- HH:MM: Fix implemented
- HH:MM: System restored
- HH:MM: Incident closed

## Root Cause
Detailed explanation of what caused the incident.

## Resolution
Steps taken to resolve the incident.

## Prevention
Actions to prevent similar incidents in the future.

## Lessons Learned
What we learned from this incident.

## Actions Required
- [ ] Action item 1 (Owner: Name, Due: Date)
- [ ] Action item 2 (Owner: Name, Due: Date)
```

---

For emergency contact information, see the [Security Considerations](../security/security-considerations.md) document.

For performance optimization details, see the [Performance Tuning Guide](../performance/performance-tuning-guide.md).

For troubleshooting assistance, see the [Troubleshooting Guide](../troubleshooting/troubleshooting-guide.md).
