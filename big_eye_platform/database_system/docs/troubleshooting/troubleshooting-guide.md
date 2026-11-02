# Troubleshooting Guide

## Table of Contents
1. [Overview](#overview)
2. [Common Issues Quick Reference](#common-issues-quick-reference)
3. [API Issues](#api-issues)
4. [Database Issues](#database-issues)
5. [Cache Issues](#cache-issues)
6. [Monitoring Issues](#monitoring-issues)
7. [Performance Issues](#performance-issues)
8. [Security Issues](#security-issues)
9. [Network and Connectivity Issues](#network-and-connectivity-issues)
10. [External API Issues](#external-api-issues)
11. [Diagnostic Tools](#diagnostic-tools)
12. [Log Analysis](#log-analysis)
13. [Emergency Procedures](#emergency-procedures)

## Overview

This troubleshooting guide provides solutions to common issues encountered in the Cybersecurity Threat Intelligence System. Each section includes diagnostic steps, root causes, and resolution procedures.

**Before Starting**:
- Check system status dashboard: https://monitoring.yourdomain.com
- Review recent logs for error patterns
- Verify external service status
- Check system resource usage

## Common Issues Quick Reference

| Issue | Symptoms | Quick Fix |
|-------|----------|-----------|
| API not responding | 503/Connection refused | Restart API service |
| Database connection timeout | Timeout errors in logs | Check DB connections, restart if needed |
| High API response time | Slow performance | Clear cache, check DB indexes |
| Cache misses | High latency | Check Redis status, increase memory |
| External API errors | 4xx/5xx from threat feeds | Check API keys, rate limits |
| Memory issues | OOM errors, system slow | Restart services, check memory usage |
| Disk space full | Cannot write data | Clean up logs, archive old data |

## API Issues

### 1. API Service Not Starting

#### Symptoms
- Service fails to start
- Port 8000 not listening
- 503 Service Unavailable errors

#### Diagnosis
```bash
# Check service status
systemctl status threat-intel-api

# Check service logs
journalctl -u threat-intel-api --since "5 minutes ago" --no-pager

# Check port availability
netstat -tlnp | grep 8000

# Check system resources
free -h
df -h
```

#### Common Causes and Solutions

**1. Port Already in Use**
```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -tlnp | grep 8000

# Kill the process
kill -9 PID

# Restart service
systemctl restart threat-intel-api
```

**2. Missing Dependencies**
```bash
# Check Python dependencies
cd /opt/threat-intel/api
pip install -r requirements.txt

# Check environment variables
cat /opt/threat-intel/.env | grep -E "(POSTGRES|MONGODB|REDIS)"

# Test database connections
python -c "import psycopg2; print('PostgreSQL OK')"
python -c "import pymongo; print('MongoDB OK')"
python -c "import redis; print('Redis OK')"
```

**3. Permission Issues**
```bash
# Check file permissions
ls -la /opt/threat-intel/api/

# Fix permissions
chown -R threat-intel:threat-intel /opt/threat-intel/api/
chmod -R 755 /opt/threat-intel/api/

# Check SELinux context (if applicable)
getenforce
semanage fcontext -a -t httpd_exec_t /opt/threat-intel/api/main.py
restorecon -R /opt/threat-intel/api/
```

### 2. API High Response Times

#### Symptoms
- Response times > 1 second
- Timeouts (504 Gateway Timeout)
- High CPU usage

#### Diagnosis
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.yourdomain.com/health

# Check API metrics
curl -s https://api.yourdomain.com/metrics | grep -E "(response_time|requests_total)"

# Check database query performance
psql -h localhost -U app_user -d threatintel << EOF
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 5;
EOF
```

#### Solutions

**1. Database Performance Issues**
```sql
-- Identify slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
WHERE mean_time > 1000
ORDER BY mean_time DESC 
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0;

-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_threat_intelligence_created_at 
ON threat_intelligence(created_at DESC);
```

**2. Cache Issues**
```bash
# Check cache hit rate
redis-cli -h localhost info stats | grep keyspace

# Check cache memory usage
redis-cli -h localhost info memory | grep used_memory_human

# Clear cache if needed
redis-cli -h localhost FLUSHDB

# Restart Redis if memory is full
systemctl restart redis-server
```

### 3. API Authentication Errors

#### Symptoms
- 401 Unauthorized errors
- 403 Forbidden errors
- JWT token errors

#### Diagnosis
```bash
# Check authentication logs
tail -f /var/log/threat-intel/api/auth.log

# Test token generation
curl -X POST https://api.yourdomain.com/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"

# Check JWT configuration
grep -E "(JWT|SECRET)" /opt/threat-intel/.env
```

#### Solutions

**1. JWT Configuration Issues**
```bash
# Generate new secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update environment variable
echo "API_SECRET_KEY=new-secret-key" >> /opt/threat-intel/.env

# Restart service
systemctl restart threat-intel-api
```

**2. User Authentication Issues**
```sql
-- Check user exists
SELECT username, is_active, last_login FROM users WHERE username = 'test';

-- Reset user password
UPDATE users 
SET password_hash = crypt('newpassword', gen_salt('bf')) 
WHERE username = 'test';

-- Activate user if needed
UPDATE users SET is_active = true WHERE username = 'test';
```

### 4. API Rate Limiting Issues

#### Symptoms
- 429 Too Many Requests errors
- Users blocked unexpectedly
- Rate limit exceeded messages

#### Diagnosis
```bash
# Check rate limiting logs
grep "rate limit" /var/log/threat-intel/api/app.log | tail -20

# Check current rate limit configuration
grep RATE_LIMIT /opt/threat-intel/.env

# Check Redis for rate limit data
redis-cli -h localhost keys "*rate*"
```

#### Solutions

**1. Adjust Rate Limits**
```bash
# Increase rate limits in environment
sed -i 's/RATE_LIMIT_REQUESTS=1000/RATE_LIMIT_REQUESTS=2000/' /opt/threat-intel/.env

# Clear rate limit data
redis-cli -h localhost FLUSHDB

# Restart service
systemctl restart threat-intel-api
```

**2. Whitelist Trusted IPs**
```python
# Add to API configuration
WHITELISTED_IPS = [
    "192.168.1.100",  # Admin office
    "10.0.0.0/8",     # Internal network
]
```

## Database Issues

### 1. PostgreSQL Connection Issues

#### Symptoms
- "could not connect to server" errors
- Connection timeouts
- Too many connections errors

#### Diagnosis
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check connection count
psql -h localhost -U app_user -d threatintel << EOF
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections
FROM pg_stat_activity;
EOF

# Check connection limits
psql -h localhost -U app_user -d threatintel << EOF
SELECT setting, unit, value, category 
FROM pg_settings 
WHERE name IN ('max_connections', 'superuser_reserved_connections');
EOF
```

#### Solutions

**1. Too Many Connections**
```sql
-- Kill long-running connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND usename != 'postgres';

-- Increase connection limit
-- Edit postgresql.conf: max_connections = 200
-- Restart PostgreSQL
```

**2. Authentication Issues**
```bash
# Check pg_hba.conf
cat /etc/postgresql/*/main/pg_hba.conf

# Test connection with different user
psql -h localhost -U postgres -d threatintel

# Reset password
psql -h localhost -U postgres -c "ALTER USER app_user PASSWORD 'newpassword';"
```

### 2. PostgreSQL Performance Issues

#### Symptoms
- Slow query execution
- High CPU usage
- Database timeouts

#### Diagnosis
```sql
-- Identify slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;

-- Check for blocking queries
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement,
       blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- Check table bloat
SELECT schemaname, tablename, n_dead_tup, n_live_tup,
       ROUND(n_dead_tup::float / NULLIF(n_live_tup, 0) * 100, 2) AS dead_tuples_percent
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY dead_tuples_percent DESC;
```

#### Solutions

**1. Slow Queries**
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_threat_intelligence_source_created 
ON threat_intelligence(source_id, created_at DESC);

-- Update table statistics
ANALYZE threat_intelligence;
ANALYZE email_analysis;
ANALYZE url_analysis;
ANALYZE ip_analysis;

-- Vacuum tables to reclaim space
VACUUM (VERBOSE, ANALYZE) threat_intelligence;
```

**2. Table Bloat**
```sql
-- Check bloated tables
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Reindex and vacuum
REINDEX INDEX CONCURRENTLY idx_threat_intelligence_composite;
VACUUM (VERBOSE, ANALYZE) threat_intelligence;
```

### 3. MongoDB Issues

#### Symptoms
- Connection refused errors
- Write operations failing
- High memory usage

#### Diagnosis
```bash
# Check MongoDB status
systemctl status mongod

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Check connections
mongo --host localhost --eval "db.adminCommand('serverStatus').connections"

# Check memory usage
mongo --host localhost --eval "db.adminCommand('serverStatus').mem"
```

#### Solutions

**1. Connection Issues**
```javascript
// Test connection
db.adminCommand('ismaster')

// Check auth issues
db.auth("admin", "password")

// Recreate user
db.dropUser("threatintel_user")
db.createUser({
  user: "threatintel_user",
  pwd: "newpassword",
  roles: [
    { role: "readWrite", db: "threatintel" },
    { role: "dbAdmin", db: "threatintel" }
  ]
})
```

**2. Performance Issues**
```javascript
// Check slow operations
db.setProfilingLevel(2, { slowms: 100 })
db.system.profile.find().sort({ ts: -1 }).limit(5)

// Analyze collection statistics
db.threatIntelligence.stats()
db.emailAnalysis.stats()

// Rebuild indexes
db.threatIntelligence.reIndex()
db.emailAnalysis.reIndex()
db.urlAnalysis.reIndex()
db.ipAnalysis.reIndex()
```

## Cache Issues

### 1. Redis Connection Issues

#### Symptoms
- Cache connection refused
- Application timeouts
- High cache miss rate

#### Diagnosis
```bash
# Check Redis status
systemctl status redis-server

# Test Redis connection
redis-cli -h localhost ping

# Check Redis info
redis-cli -h localhost info

# Check memory usage
redis-cli -h localhost info memory
```

#### Solutions

**1. Memory Issues**
```bash
# Check memory usage
redis-cli -h localhost info memory

# Clear expired keys
redis-cli -h localhost EVAL "
local keys = redis.call('KEYS', '*')
local expired = 0
for i=1,#keys do
  if redis.call('TTL', keys[i]) <= 0 then
    redis.call('DEL', keys[i])
    expired = expired + 1
  end
end
return expired
" 0

# Restart Redis if memory is critical
systemctl restart redis-server
```

**2. Configuration Issues**
```bash
# Check Redis configuration
redis-cli -h localhost config get "*"

# Update maxmemory policy
redis-cli -h localhost config set maxmemory-policy allkeys-lru

# Persist configuration
redis-cli -h localhost config rewrite
```

### 2. Cache Performance Issues

#### Symptoms
- High latency
- Low hit rates
- Cache thrashing

#### Diagnosis
```bash
# Check hit rate
redis-cli -h localhost info stats | grep keyspace

# Check slow commands
redis-cli -h localhost slowlog get 10

# Check large keys
redis-cli -h localhost --bigkeys

# Analyze key patterns
redis-cli -h localhost --scan --pattern "*threat*" | head -20
```

#### Solutions

**1. Optimize Key Structure**
```python
# Review cache key patterns in application code
# Use shorter key names
# Consider key expiration policies

# Example optimization
# Instead of: "threat_intelligence_virus_total_ip_192.168.1.1"
# Use: "ti:vt:ip:192.168.1.1"
```

**2. Implement Cache Warming**
```python
# Preload frequently accessed data
def warm_cache():
    # Load popular threat intelligence data
    popular_indicators = get_popular_indicators()
    
    for indicator in popular_indicators:
        cache_key = f"ti:{indicator.type}:{indicator.value}"
        data = fetch_threat_intelligence(indicator)
        redis_client.setex(cache_key, 3600, json.dumps(data))
```

## Monitoring Issues

### 1. Prometheus Not Scraping Targets

#### Symptoms
- Missing metrics in Grafana
- Targets showing as down
- Empty dashboards

#### Diagnosis
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[]'

# Check Prometheus logs
tail -f /var/log/prometheus/prometheus.log

# Validate configuration
cat /etc/prometheus/prometheus.yml
```

#### Solutions

**1. Target Configuration Issues**
```yaml
# Update prometheus.yml
scrape_configs:
  - job_name: 'threat-intel-api'
    static_configs:
      - targets: ['api:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'
    scrape_timeout: 10s
    params:
      format: ['prometheus']
```

**2. Network Connectivity**
```bash
# Test connectivity from Prometheus container
docker exec prometheus-container nc -zv api 8000

# Check firewall rules
iptables -L | grep 9090
```

### 2. Grafana Dashboard Issues

#### Symptoms
- Dashboards not loading
- Data source errors
- Missing panels

#### Diagnosis
```bash
# Check Grafana logs
tail -f /var/log/grafana/grafana.log

# Test data source connectivity
curl -u admin:password http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up

# Check data source configuration
curl -u admin:password http://localhost:3000/api/datasources
```

#### Solutions

**1. Data Source Configuration**
```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true,
  "jsonData": {
    "timeInterval": "30s",
    "queryTimeout": "60s"
  }
}
```

**2. Dashboard Import Issues**
```bash
# Import dashboards programmatically
curl -X POST \
  -H "Content-Type: application/json" \
  -d @dashboard.json \
  -u admin:password \
  http://localhost:3000/api/dashboards/db
```

## Performance Issues

### 1. High CPU Usage

#### Symptoms
- System unresponsive
- Process timeouts
- High load average

#### Diagnosis
```bash
# Check CPU usage by process
top -o %CPU

# Check system load
uptime
iostat -x 1 5

# Check for runaway processes
ps aux --sort=-%cpu | head -20
```

#### Solutions

**1. Process Optimization**
```bash
# Kill CPU-intensive processes
kill -TERM PID

# Restart services if needed
systemctl restart threat-intel-api

# Check for infinite loops in application logs
grep -i "infinite\|loop" /var/log/threat-intel/api/app.log
```

### 2. High Memory Usage

#### Symptoms
- Out of memory errors
- System slowdown
- OOM killer activated

#### Diagnosis
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Check for memory leaks
ps -p PID -o pid,vsz,rss,comm

# Check system messages
dmesg | grep -i "killed process"
```

#### Solutions

**1. Memory Optimization**
```bash
# Restart memory-intensive services
systemctl restart threat-intel-api
systemctl restart mongod

# Clear cache if safe to do so
echo 3 > /proc/sys/vm/drop_caches

# Increase swap if needed
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### 3. Disk Space Issues

#### Symptoms
- Write failures
- Database errors
- Log file errors

#### Diagnosis
```bash
# Check disk usage
df -h
du -sh /* | sort -hr

# Find large files
find / -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Check inode usage
df -i
```

#### Solutions

**1. Clean Up Disk Space**
```bash
# Clean old logs
find /var/log -name "*.log" -mtime +30 -delete

# Clean old backups
find /backup -name "*.dump" -mtime +7 -delete

# Clean temporary files
rm -rf /tmp/*

# Clean package cache
apt clean
```

**2. Archive Old Data**
```sql
-- Archive old threat intelligence data
INSERT INTO threat_intelligence_archive 
SELECT * FROM threat_intelligence 
WHERE created_at < NOW() - INTERVAL '90 days';

DELETE FROM threat_intelligence 
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Security Issues

### 1. Authentication Failures

#### Symptoms
- Increased failed login attempts
- Security alerts
- Locked user accounts

#### Diagnosis
```bash
# Check authentication logs
grep "authentication failed" /var/log/threat-intel/api/app.log | tail -20

# Check for brute force attempts
awk '/authentication failed/ {print $1}' /var/log/threat-intel/api/app.log | sort | uniq -c | sort -nr | head -10

# Check firewall logs
tail -f /var/log/syslog | grep -i "iptables\|fail2ban"
```

#### Solutions

**1. Block Malicious IPs**
```bash
# Add IP to blacklist
iptables -A INPUT -s MALICIOUS_IP -j DROP

# Update fail2ban configuration
echo "bantime = 3600" >> /etc/fail2ban/jail.local
systemctl restart fail2ban

# Check banned IPs
fail2ban-client status threat-intel-api
```

### 2. SSL/TLS Certificate Issues

#### Symptoms
- Certificate expiration warnings
- Browser security errors
- SSL handshake failures

#### Diagnosis
```bash
# Check certificate expiration
openssl x509 -in /etc/ssl/certs/threat-intel.crt -noout -dates

# Test SSL connection
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Check certificate chain
echo | openssl s_client -connect api.yourdomain.com:443 2>/dev/null | openssl x509 -noout -text
```

#### Solutions

**1. Renew Certificate**
```bash
# Renew Let's Encrypt certificate
certbot renew --dry-run
certbot renew

# Restart web server
systemctl restart nginx

# Update certificate permissions
chmod 644 /etc/ssl/certs/threat-intel.crt
chmod 600 /etc/ssl/private/threat-intel.key
```

## Network and Connectivity Issues

### 1. API Not Accessible

#### Symptoms
- Connection timeouts
- DNS resolution errors
- Service unreachable

#### Diagnosis
```bash
# Check DNS resolution
nslookup api.yourdomain.com
dig api.yourdomain.com

# Check network connectivity
ping api.yourdomain.com
traceroute api.yourdomain.com

# Check service ports
nmap -p 80,443 api.yourdomain.com
```

#### Solutions

**1. DNS Issues**
```bash
# Update DNS configuration
echo "nameserver 8.8.8.8" >> /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf

# Restart networking
systemctl restart networking
```

**2. Firewall Issues**
```bash
# Check firewall rules
iptables -L -n

# Allow traffic on required ports
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables-save > /etc/iptables/rules.v4
```

### 2. External API Connectivity Issues

#### Symptoms
- Timeout errors from threat intelligence feeds
- API authentication failures
- Rate limit exceeded errors

#### Diagnosis
```bash
# Test external API connectivity
curl -w "@curl-format.txt" -o /dev/null -s "https://www.virustotal.com/api/v3"

# Check API key validity
curl -H "x-apikey: $VIRUSTOTAL_API_KEY" \
     "https://www.virustotal.com/api/v3/files/scan" -X POST

# Check rate limits
curl -I "https://www.virustotal.com/api/v3"
```

#### Solutions

**1. API Key Issues**
```bash
# Rotate API keys
# Update in environment variables
sed -i 's/VIRUSTOTAL_API_KEY=old_key/VIRUSTOTAL_API_KEY=new_key/' /opt/threat-intel/.env

# Restart service
systemctl restart threat-intel-api
```

**2. Rate Limiting**
```python
# Implement exponential backoff
import time
import random

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            delay = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)
```

## Diagnostic Tools

### 1. System Diagnostics

#### System Health Check Script
```bash
#!/bin/bash
# Comprehensive system health check

echo "=== System Health Check - $(date) ==="

# System load
echo "System Load:"
uptime

# Memory usage
echo -e "\nMemory Usage:"
free -h

# Disk usage
echo -e "\nDisk Usage:"
df -h

# CPU usage
echo -e "\nCPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}'

# Service status
echo -e "\nService Status:"
systemctl is-active threat-intel-api
systemctl is-active postgresql
systemctl is-active mongod
systemctl is-active redis-server
systemctl is-active nginx

# Port status
echo -e "\nPort Status:"
netstat -tlnp | grep -E "(8000|5432|27017|6379)"

# Recent errors
echo -e "\nRecent Errors:"
journalctl -u threat-intel-api --since "1 hour ago" --priority=3 --no-pager | tail -10
```

### 2. Database Diagnostics

#### PostgreSQL Health Check
```bash
#!/bin/bash
# PostgreSQL specific diagnostics

echo "=== PostgreSQL Diagnostics ==="

# Connection count
psql -h localhost -U app_user -d threatintel -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity;"

# Database size
psql -h localhost -U app_user -d threatintel -c "
SELECT 
    pg_size_pretty(pg_database_size('threatintel')) as database_size;"

# Slow queries
psql -h localhost -U app_user -d threatintel -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 1000
ORDER BY mean_time DESC 
LIMIT 5;"

# Table sizes
psql -h localhost -U app_user -d threatintel -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

#### MongoDB Health Check
```bash
#!/bin/bash
# MongoDB specific diagnostics

echo "=== MongoDB Diagnostics ==="

# Connection test
mongo --host localhost --eval "print('MongoDB Connection: OK')"

# Database stats
mongo --host localhost --eval "
db.adminCommand('serverStatus').connections;

db.adminCommand('serverStatus').mem;

db.adminCommand('serverStatus').opcounters;"

# Collection statistics
mongo --host localhost threatintel --eval "
db.threatIntelligence.countDocuments();
db.emailAnalysis.countDocuments();
db.urlAnalysis.countDocuments();
db.ipAnalysis.countDocuments();"
```

### 3. Cache Diagnostics

#### Redis Health Check
```bash
#!/bin/bash
# Redis specific diagnostics

echo "=== Redis Diagnostics ==="

# Connection test
redis-cli -h localhost ping

# Memory usage
redis-cli -h localhost info memory | grep used_memory_human

# Key statistics
redis-cli -h localhost dbsize

# Hit rate
redis-cli -h localhost info stats | grep keyspace

# Slow queries
redis-cli -h localhost slowlog len

# Memory details
redis-cli -h localhost info memory | grep -E "(used_memory_human|maxmemory)"
```

## Log Analysis

### 1. Log File Locations

| Component | Log File | Purpose |
|-----------|----------|---------|
| API Service | `/var/log/threat-intel/api/app.log` | Application events |
| API Access | `/var/log/threat-intel/api/access.log` | HTTP requests |
| API Errors | `/var/log/threat-intel/api/error.log` | Error messages |
| PostgreSQL | `/var/log/postgresql/postgresql-*.log` | Database events |
| MongoDB | `/var/log/mongodb/mongod.log` | MongoDB events |
| Redis | `/var/log/redis/redis-server.log` | Redis events |
| Nginx | `/var/log/nginx/error.log` | Web server errors |
| System | `/var/log/syslog` | System events |
| Security | `/var/log/auth.log` | Authentication events |

### 2. Common Log Patterns

#### API Error Patterns
```bash
# Find authentication errors
grep "authentication failed" /var/log/threat-intel/api/app.log

# Find rate limit violations
grep "rate limit exceeded" /var/log/threat-intel/api/app.log

# Find validation errors
grep "validation error" /var/log/threat-intel/api/app.log

# Find database connection errors
grep "database connection" /var/log/threat-intel/api/app.log
```

#### Database Error Patterns
```bash
# PostgreSQL connection errors
grep "could not connect" /var/log/postgresql/postgresql-*.log

# PostgreSQL deadlock detection
grep "deadlock detected" /var/log/postgresql/postgresql-*.log

# MongoDB connection errors
grep "connection refused" /var/log/mongodb/mongod.log

# MongoDB replication errors
grep "replica set" /var/log/mongodb/mongod.log
```

### 3. Log Analysis Tools

#### ELK Stack Query Examples
```json
// Search for API errors in last 24 hours
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "now-24h"
            }
          }
        },
        {
          "match": {
            "level": "ERROR"
          }
        }
      ]
    }
  }
}

// Find authentication failures by IP
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "message": "authentication failed"
          }
        },
        {
          "range": {
            "@timestamp": {
              "gte": "now-1h"
            }
          }
        }
      ]
    }
  },
  "aggs": {
    "by_ip": {
      "terms": {
        "field": "client_ip",
        "size": 10
      }
    }
  }
}
```

## Emergency Procedures

### 1. System Recovery

#### Emergency Restart Script
```bash
#!/bin/bash
# Emergency system recovery

echo "Starting emergency recovery procedures..."

# Stop all services
systemctl stop threat-intel-api
systemctl stop nginx

# Check disk space
df -h
if [ $(df / | tail -1 | awk '{print $5}' | sed 's/%//') -gt 90 ]; then
    echo "WARNING: Disk space low! Cleaning up..."
    find /var/log -name "*.log" -mtime +7 -delete
    find /backup -name "*.dump" -mtime +3 -delete
fi

# Restart databases
systemctl restart postgresql
systemctl restart mongod
systemctl restart redis-server

# Wait for databases to start
sleep 30

# Test database connections
psql -h localhost -U app_user -d threatintel -c "SELECT 1;" || {
    echo "PostgreSQL connection failed!"
    exit 1
}

mongo --host localhost --eval "db.adminCommand('ismaster')" || {
    echo "MongoDB connection failed!"
    exit 1
}

# Start application services
systemctl start threat-intel-api
systemctl start nginx

# Wait for API to start
sleep 30

# Test API health
curl -f https://api.yourdomain.com/health || {
    echo "API health check failed!"
    journalctl -u threat-intel-api --since "5 minutes ago"
    exit 1
}

echo "Emergency recovery completed successfully!"
```

### 2. Data Recovery

#### Quick Data Recovery
```bash
#!/bin/bash
# Quick data recovery from latest backup

BACKUP_FILE=$(ls -t /backup/daily/threatintel_*.dump | head -1)

if [ -z "$BACKUP_FILE" ]; then
    echo "No backup file found!"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"

# Stop application
systemctl stop threat-intel-api

# Restore database
pg_restore --host localhost --username app_user \
    --dbname threatintel \
    --clean \
    --verbose \
    "$BACKUP_FILE"

# Start application
systemctl start threat-intel-api

# Verify restore
psql -h localhost -U app_user -d threatintel -c "SELECT count(*) FROM threat_intelligence;"
```

### 3. Performance Emergency

#### Emergency Performance Fix
```bash
#!/bin/bash
# Emergency performance optimization

echo "Applying emergency performance fixes..."

# Clear all caches
redis-cli -h localhost FLUSHDB

# Kill long-running database queries
psql -h localhost -U app_user -d threatintel << EOF
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
  AND query_start < NOW() - INTERVAL '2 minutes';
EOF

# Vacuum critical tables
psql -h localhost -U app_user -d threatintel -c "
VACUUM (VERBOSE, ANALYZE) threat_intelligence;
VACUUM (VERBOSE, ANALYZE) email_analysis;
VACUUM (VERBOSE, ANALYZE) url_analysis;
VACUUM (VERBOSE, ANALYZE) ip_analysis;"

# Restart Redis with optimized settings
systemctl stop redis-server
redis-server /etc/redis/redis.conf --maxmemory 1gb --maxmemory-policy allkeys-lru
systemctl start redis-server

# Restart API with increased worker count
sed -i 's/API_WORKERS=4/API_WORKERS=8/' /opt/threat-intel/.env
systemctl restart threat-intel-api

echo "Emergency performance fixes applied!"
```

---

For system administration procedures, see the [Operational Runbook](../operations/operational-runbook.md).

For performance tuning details, see the [Performance Tuning Guide](../performance/performance-tuning-guide.md).

For security considerations, see the [Security Considerations](../security/security-considerations.md).
