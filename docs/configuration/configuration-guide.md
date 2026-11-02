# Configuration Guide

## Table of Contents
1. [Overview](#overview)
2. [API Configuration](#api-configuration)
3. [Database Configuration](#database-configuration)
4. [Redis Configuration](#redis-configuration)
5. [Monitoring Configuration](#monitoring-configuration)
6. [Security Configuration](#security-configuration)
7. [Performance Configuration](#performance-configuration)
8. [Environment Variables](#environment-variables)
9. [Configuration Files](#configuration-files)

## Overview

This guide provides detailed configuration instructions for all components of the Cybersecurity Threat Intelligence System. Each section covers essential configuration parameters, recommended settings, and best practices.

For installation instructions, see [Installation Guide](../setup/installation-guide.md).

## API Configuration

### FastAPI Application Configuration

**File**: `api/main.py`

```python
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

# Application configuration
app = FastAPI(
    title="Cybersecurity Threat Intelligence API",
    description="RESTful API for threat intelligence data processing and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "https://admin.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
```

### API Security Configuration

**Environment Variables**:
```bash
# API Authentication
API_SECRET_KEY="your-super-secret-key-here"
API_ALGORITHM="HS256"
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Database connections
POSTGRES_URL="postgresql://user:password@localhost:5432/threatintel"
MONGODB_URL="mongodb://localhost:27017/threatintel"
REDIS_URL="redis://localhost:6379/0"

# External API keys
VIRUSTOTAL_API_KEY="your-virustotal-api-key"
ABUSEIPDB_API_KEY="your-abuseipdb-api-key"
SHODAN_API_KEY="your-shodan-api-key"
GREYNOISE_API_KEY="your-greyNoise-api-key"
OTX_API_KEY="your-otx-api-key"
```

### Validation Service Configuration

**File**: `api/services/validation_service.py`

```python
class ValidationConfig:
    """Configuration for validation services"""
    
    # Email validation settings
    EMAIL_VALIDATION_TIMEOUT = 30
    EMAIL_VALIDATION_RETRY_ATTEMPTS = 3
    EMAIL_CACHE_TTL = 86400  # 24 hours
    
    # URL validation settings
    URL_VALIDATION_TIMEOUT = 15
    URL_VALIDATION_MAX_REDIRECTS = 5
    URL_SCAN_TIMEOUT = 300  # 5 minutes
    
    # Domain validation settings
    DOMAIN_VALIDATION_TIMEOUT = 20
    DNS_RESOLVER_TIMEOUT = 10
    WHOIS_LOOKUP_TIMEOUT = 30
    
    # IP address validation settings
    IP_VALIDATION_TIMEOUT = 10
    GEOLOCATION_TIMEOUT = 15
    REPUTATION_CHECK_TIMEOUT = 20

# Cache configuration
CACHE_CONFIG = {
    "default_ttl": 3600,
    "max_size": 10000,
    "cleanup_interval": 300
}
```

## Database Configuration

### PostgreSQL Configuration

**File**: `postgres/postgresql.conf`

```ini
# Memory and Performance
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint and WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 1GB
min_wal_size = 80MB

# Connection Settings
max_connections = 200
listen_addresses = 'localhost'
port = 5432

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

# Query Tuning
random_page_cost = 1.1
effective_io_concurrency = 200

# Security
ssl = on
password_encryption = scram-sha-256
```

**File**: `postgres/pg_hba.conf`

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             postgres                                peer
local   all             all                                     md5
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5
host    threatintel     app_user         192.168.1.0/24          scram-sha-256
host    threatintel     readonly_user    192.168.1.0/24          scram-sha-256
```

### MongoDB Configuration

**File**: `mongodb/mongod.conf`

```yaml
# MongoDB Configuration
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1,192.168.1.100
  maxIncomingConnections: 100
  wireObjectCheck: true

processManagement:
  timeZoneInfo: /usr/share/zoneinfo

security:
  authorization: enabled
  keyFile: /etc/mongodb/mongodb-keyfile

replication:
  replSetName: "threatintel-replica"
```

### Database Connection Pool Configuration

**File**: `api/database/connection.py`

```python
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
import os

# PostgreSQL connection configuration
POSTGRES_URL = os.getenv("POSTGRES_URL")
postgres_engine = create_engine(
    POSTGRES_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)

# MongoDB connection configuration
MONGODB_URL = os.getenv("MONGODB_URL")
mongo_client = MongoClient(
    MONGODB_URL,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=30000,
    connectTimeoutMS=10000,
    serverSelectionTimeoutMS=10000
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
```

## Redis Configuration

**File**: `redis/redis.conf`

```ini
# Network and Security
bind 127.0.0.1 192.168.1.100
port 6379
protected-mode yes
requirepass your-redis-password
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key

# Memory Management
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
syslog-enabled yes
syslog-ident redis

# Performance
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Memory optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

### Redis Cluster Configuration (Optional)

**File**: `redis/redis-cluster.conf`

```ini
# Redis Cluster Configuration
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 15000
cluster-announce-ip 192.168.1.100
cluster-announce-port 6379
cluster-announce-bus-port 16379
```

## Monitoring Configuration

### Prometheus Configuration

**File**: `monitoring/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'threat-intel-cluster'
    replica: 'prometheus-1'

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 5s

  - job_name: 'threat-intel-api'
    static_configs:
      - targets: ['api:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'
    scrape_timeout: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s

  - job_name: 'mongodb-exporter'
    static_configs:
      - targets: ['mongodb-exporter:9216']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  - job_name: 'blackbox-exporter'
    static_configs:
      - targets: ['blackbox-exporter:9115']
    scrape_interval: 60s
```

### Grafana Configuration

**File**: `monitoring/grafana/grafana.ini`

```ini
[DEFAULT]
instance_name = Threat Intelligence Grafana

[server]
http_addr = 0.0.0.0
http_port = 3000
domain = monitoring.yourdomain.com
root_url = https://monitoring.yourdomain.com/
serve_from_sub_path = false

[database]
type = postgres
host = postgres:5432
name = grafana
user = grafana
password = grafana_password
url = postgres://grafana:grafana_password@postgres:5432/grafana

[session]
provider = postgres
provider_config = host=postgres:5432 user=grafana password=grafana_password dbname=grafana sslmode=disable

[security]
admin_user = admin
admin_password = admin_password
secret_key = your-secret-key-here
cookie_secure = true
cookie_samesite = strict

[auth]
disable_login_form = false
disable_signout_menu = false
signout_redirect_url =

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_id = 1
auto_assign_org_role = Viewer
verify_email_enabled = false

[alerting]
enabled = true
execute_alerts = true

[smtp]
enabled = true
host = smtp.yourdomain.com:587
user = grafana@yourdomain.com
password = smtp_password
from_address = grafana@yourdomain.com
from_name = Grafana
ehlo_identity = monitoring.yourdomain.com

[external_image_storage]
provider = s3

[external_image_storage.s3]
endpoint = s3.yourdomain.com
path = grafana-images/
access_key = your-s3-access-key
secret_key = your-s3-secret-key
```

### Elasticsearch Configuration

**File**: `monitoring/elk/elasticsearch.yml`

```yaml
cluster.name: threat-intel-logs
node.name: es-node-1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# Memory and performance
bootstrap.memory_lock: true
indices.memory.index_buffer_size: 30%
indices.fielddata.cache.size: 40%

# Security
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true

# Monitoring
xpack.monitoring.collection.enabled: true
```

### Logstash Configuration

**File**: `monitoring/elk/logstash.conf`

```ruby
input {
  beats {
    port => 5044
  }
  
  syslog {
    port => 514
  }
  
  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  if [fields][log_type] == "threat-intel-api" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} \[%{LOGLEVEL:level}\] %{GREEDYDATA:message}" }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [level] == "ERROR" {
      mutate {
        add_tag => [ "error", "alert" ]
      }
    }
  }
  
  if [fields][log_type] == "database" {
    grok {
      match => { 
        "message" => "%{POSTGRESQL}" 
      }
    }
  }
  
  if [fields][log_type] == "security" {
    mutate {
      add_tag => [ "security" ]
    }
    
    if [message] =~ /authentication.*failed/i {
      mutate {
        add_tag => [ "failed-auth" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "threat-intel-logs-%{+YYYY.MM.dd}"
  }
  
  if "error" in [tags] {
    email {
      to => "admin@yourdomain.com"
      subject => "Alert: Error in Threat Intelligence System"
      body => "%{message}"
    }
  }
  
  stdout {
    codec => rubydebug
  }
}
```

### Kibana Configuration

**File**: `monitoring/elk/kibana.yml`

```yaml
server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: ["https://elasticsearch:9200"]
elasticsearch.username: kibana
elasticsearch.password: kibana_password

# SSL Configuration
server.ssl.enabled: true
server.ssl.certificate: /path/to/kibana.crt
server.ssl.key: /path/to/kibana.key

# Security
xpack.security.enabled: true

# Logging
logging.appenders:
  file:
    type: file
    fileName: /var/log/kibana/kibana.log
    layout:
      type: json

logging.root:
  level: info
  appenders:
    - default
    - file

logging.loggers:
  - name: http.server.response
    level: debug
```

## Security Configuration

### Firewall Configuration

**File**: `security/firewall.sh`

```bash
#!/bin/bash
# Threat Intelligence System Firewall Rules

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (restricted)
iptables -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -j ACCEPT

# Allow HTTP/HTTPS for API
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow monitoring interfaces
iptables -A INPUT -p tcp --dport 3000 -s 192.168.1.0/24 -j ACCEPT  # Grafana
iptables -A INPUT -p tcp --dport 9200 -s 192.168.1.0/24 -j ACCEPT  # Elasticsearch

# Allow database connections (internal only)
iptables -A INPUT -p tcp --dport 5432 -s 192.168.1.0/24 -j ACCEPT  # PostgreSQL
iptables -A INPUT -p tcp --dport 27017 -s 192.168.1.0/24 -j ACCEPT  # MongoDB
iptables -A INPUT -p tcp --dport 6379 -s 192.168.1.0/24 -j ACCEPT   # Redis

# Rate limiting for API endpoints
iptables -A INPUT -p tcp --dport 8000 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Block common attack patterns
iptables -A INPUT -p tcp --dport 8000 -m string --string "union select" --algo bm -j DROP
iptables -A INPUT -p tcp --dport 8000 -m string --string "script>" --algo bm -j DROP

# Log dropped packets
iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: "
iptables -A INPUT -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### SSL/TLS Configuration

**File**: `security/ssl-nginx.conf`

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/threat-intel.crt;
    ssl_certificate_key /etc/ssl/private/threat-intel.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    location / {
        proxy_pass http://threat-intel-api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;
    }
    
    location /metrics {
        proxy_pass http://threat-intel-api/metrics;
        allow 192.168.1.0/24;
        deny all;
    }
}

limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

### API Security Configuration

**File**: `api/security/rbac.py`

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

class Permission(Enum):
    READ_THREAT_DATA = "read_threat_data"
    WRITE_THREAT_DATA = "write_threat_data"
    DELETE_THREAT_DATA = "delete_threat_data"
    READ_ANALYTICS = "read_analytics"
    WRITE_ANALYTICS = "write_analytics"
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_ALERTS = "manage_alerts"

class Role(BaseModel):
    name: str
    permissions: List[Permission]

# Predefined roles
ROLES = {
    "admin": Role(
        name="admin",
        permissions=[p for p in Permission]
    ),
    "analyst": Role(
        name="analyst",
        permissions=[
            Permission.READ_THREAT_DATA,
            Permission.WRITE_THREAT_DATA,
            Permission.READ_ANALYTICS,
            Permission.WRITE_ANALYTICS,
            Permission.MANAGE_ALERTS
        ]
    ),
    "viewer": Role(
        name="viewer",
        permissions=[
            Permission.READ_THREAT_DATA,
            Permission.READ_ANALYTICS
        ]
    ),
    "operator": Role(
        name="operator",
        permissions=[
            Permission.READ_THREAT_DATA,
            Permission.READ_ANALYTICS,
            Permission.MANAGE_ALERTS,
            Permission.VIEW_LOGS
        ]
    )
}

def check_permission(user_role: str, required_permission: Permission) -> bool:
    """Check if user role has required permission"""
    if user_role not in ROLES:
        return False
    return required_permission in ROLES[user_role].permissions
```

## Performance Configuration

### Database Indexing Strategy

**File**: `database/indexes.sql`

```sql
-- Email domain analysis indexes
CREATE INDEX CONCURRENTLY idx_email_analysis_domain 
ON email_analysis(email_domain);

CREATE INDEX CONCURRENTLY idx_email_analysis_created_at 
ON email_analysis(created_at DESC);

CREATE INDEX CONCURRENTLY idx_email_analysis_suspicious_score 
ON email_analysis(suspicious_score DESC) 
WHERE suspicious_score > 0.5;

-- URL analysis indexes
CREATE INDEX CONCURRENTLY idx_url_analysis_url_hash 
ON url_analysis(url_hash);

CREATE INDEX CONCURRENTLY idx_url_analysis_malicious_score 
ON url_analysis(malicious_score DESC);

CREATE INDEX CONCURRENTLY idx_url_analysis_tags 
ON url_analysis USING GIN(tags);

-- IP analysis indexes
CREATE INDEX CONCURRENTLY idx_ip_analysis_ip_address 
ON ip_analysis(ip_address);

CREATE INDEX CONCURRENTLY idx_ip_analysis_reputation_score 
ON ip_analysis(reputation_score DESC);

CREATE INDEX CONCURRENTLY idx_ip_analysis_geo_country 
ON ip_analysis(geo_country);

-- Combined indexes for common queries
CREATE INDEX CONCURRENTLY idx_threat_intelligence_composite 
ON threat_intelligence(source, indicator_type, confidence_score DESC) 
WHERE confidence_score > 0.7;

-- Partial indexes for active records
CREATE INDEX CONCURRENTLY idx_threat_intelligence_active 
ON threat_intelligence(last_seen DESC) 
WHERE is_active = true;

-- Text search indexes
CREATE INDEX CONCURRENTLY idx_threat_intelligence_search 
ON threat_intelligence USING GIN(to_tsvector('english', notes));
```

### Redis Caching Configuration

**File**: `api/cache/redis_config.py`

```python
import redis
from typing import Optional, Dict, Any
import json
import time

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            password='your-redis-password',
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        try:
            serialized_value = json.dumps(value)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            print(f"Redis TTL error: {e}")
            return -1

# Cache key patterns
CACHE_KEYS = {
    "email_reputation": "email:rep:{email_hash}",
    "url_scan": "url:scan:{url_hash}",
    "ip_reputation": "ip:rep:{ip_address}",
    "domain_whois": "domain:whois:{domain}",
    "threat_intel": "ti:data:{source}:{indicator}",
    "validation_result": "val:{type}:{hash}"
}

def generate_cache_key(pattern: str, **kwargs) -> str:
    """Generate cache key using pattern and parameters"""
    return pattern.format(**kwargs)

# Default TTL values
CACHE_TTL = {
    "email_reputation": 86400,  # 24 hours
    "url_scan": 7200,           # 2 hours
    "ip_reputation": 86400,     # 24 hours
    "domain_whois": 604800,     # 1 week
    "threat_intel": 3600,       # 1 hour
    "validation_result": 1800   # 30 minutes
}

redis_cache = RedisCache()
```

### Connection Pooling Configuration

**File**: `api/database/pool_config.py`

```python
import asyncpg
import motor.motor_asyncio
import asyncio
from typing import AsyncGenerator

class DatabasePoolManager:
    def __init__(self):
        self.postgres_pool = None
        self.mongodb_client = None
        self.mongodb_db = None
    
    async def init_pools(self):
        """Initialize database connection pools"""
        # PostgreSQL connection pool
        self.postgres_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            user="app_user",
            password="app_password",
            database="threatintel",
            min_size=10,
            max_size=50,
            max_queries=50000,
            max_inactive_connection_lifetime=300.0,
            command_timeout=60
        )
        
        # MongoDB connection pool
        self.mongodb_client = motor.motor_asyncio.AsyncIOMotorClient(
            "mongodb://localhost:27017",
            minPoolSize=10,
            maxPoolSize=50,
            maxIdleTimeMS=30000,
            connectTimeoutMS=10000,
            serverSelectionTimeoutMS=10000,
            heartbeatFrequencyMS=10000
        )
        self.mongodb_db = self.mongodb_client.threatintel
    
    async def get_postgres_connection(self):
        """Get PostgreSQL connection from pool"""
        async with self.postgres_pool.acquire() as connection:
            async with connection.transaction():
                yield connection
    
    async def get_mongodb_collection(self, collection_name: str):
        """Get MongoDB collection"""
        return self.mongodb_db[collection_name]
    
    async def close_pools(self):
        """Close all database pools"""
        if self.postgres_pool:
            await self.postgres_pool.close()
        if self.mongodb_client:
            self.mongodb_client.close()

pool_manager = DatabasePoolManager()
```

## Environment Variables

### Production Environment Variables

**File**: `.env.production`

```bash
# Application Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_SECRET_KEY=your-production-secret-key
API_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database Configuration
POSTGRES_URL=postgresql://app_user:secure_password@postgres:5432/threatintel
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=threatintel
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_password

MONGODB_URL=mongodb://threatintel_user:secure_password@mongodb:27017/threatintel?authSource=admin
MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DB=threatintel
MONGODB_USER=threatintel_user
MONGODB_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://:secure_password@redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=secure_password
REDIS_DB=0

# External API Keys
VIRUSTOTAL_API_KEY=your-production-virustotal-key
ABUSEIPDB_API_KEY=your-production-abuseipdb-key
SHODAN_API_KEY=your-production-shodan-key
GREYNOISE_API_KEY=your-production-greyNoise-key
OTX_API_KEY=your-production-otx-key

# Monitoring Configuration
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_grafana_password

# Security Configuration
SSL_CERT_PATH=/etc/ssl/certs/threat-intel.crt
SSL_KEY_PATH=/etc/ssl/private/threat-intel.key
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256

# Rate Limiting
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Cache Configuration
CACHE_TTL_DEFAULT=3600
CACHE_MAX_SIZE=10000

# Alert Configuration
ALERT_EMAIL_SMTP=smtp.yourdomain.com
ALERT_EMAIL_PORT=587
ALERT_EMAIL_USER=alerts@yourdomain.com
ALERT_EMAIL_PASSWORD=alert_email_password
ALERT_EMAIL_FROM=Threat Intelligence System <alerts@yourdomain.com>
ALERT_SLACK_WEBHOOK=https://hooks.slack.com/your-webhook-url

# Performance Configuration
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
WORKER_PROCESSES=4
WORKER_THREADS=2

# Logging
LOG_FORMAT=json
LOG_FILE=/var/log/threat-intel/app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# GDPR Compliance
GDPR_DATA_RETENTION_DAYS=365
GDPR_ANONYMIZATION_ENABLED=true
GDPR_LOG_RETENTION_DAYS=2555  # 7 years
```

### Development Environment Variables

**File**: `.env.development`

```bash
# Application Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=1
API_SECRET_KEY=dev-secret-key-not-for-production
API_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database Configuration (Local)
POSTGRES_URL=postgresql://dev_user:dev_password@localhost:5432/threatintel_dev
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=threatintel_dev
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=dev_password

MONGODB_URL=mongodb://localhost:27017/threatintel_dev
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=threatintel_dev
MONGODB_USER=
MONGODB_PASSWORD=

# Redis Configuration (Local)
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Test API Keys (Use test/sandbox endpoints)
VIRUSTOTAL_API_KEY=test-key-not-for-production
ABUSEIPDB_API_KEY=test-key-not-for-production
SHODAN_API_KEY=test-key-not-for-production
GREYNOISE_API_KEY=test-key-not-for-production
OTX_API_KEY=test-key-not-for-production

# Development monitoring (disabled)
PROMETHEUS_ENABLED=false
GRAFANA_ENABLED=false

# Development security
SSL_ENABLED=false
JWT_SECRET_KEY=dev-jwt-key-not-secure

# Development rate limits (more permissive)
RATE_LIMIT_REQUESTS=5000
RATE_LIMIT_WINDOW=3600

# Development cache
CACHE_TTL_DEFAULT=300  # 5 minutes
CACHE_MAX_SIZE=1000

# Development logging
LOG_FORMAT=text
LOG_LEVEL=DEBUG
LOG_FILE=logs/app.log
```

## Configuration Files

### Docker Compose Configuration

**File**: `docker-compose.production.yml`

```yaml
version: '3.8'

services:
  api:
    build: ./api
    environment:
      - ENVIRONMENT=production
      - POSTGRES_URL=${POSTGRES_URL}
      - MONGODB_URL=${MONGODB_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./logs:/app/logs
      - ./ssl:/app/ssl
    depends_on:
      - postgres
      - mongodb
      - redis
    restart: unless-stopped
    networks:
      - threat-intel

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=threatintel
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/pg_hba.conf:/etc/postgresql/pg_hba.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    restart: unless-stopped
    networks:
      - threat-intel

  mongodb:
    image: mongo:6.0
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USER}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PASSWORD}
      - MONGO_INITDB_DATABASE=threatintel
    volumes:
      - mongodb_data:/data/db
      - ./mongodb/mongod.conf:/etc/mongod.conf
    command: mongod --config /etc/mongod.conf
    restart: unless-stopped
    networks:
      - threat-intel

  redis:
    image: redis:7-alpine
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf
      - ./redis/redis-cluster.conf:/usr/local/etc/redis/redis-cluster.conf
    restart: unless-stopped
    networks:
      - threat-intel

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - threat-intel

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/grafana.ini:/etc/grafana/grafana.ini
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    networks:
      - threat-intel

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: unless-stopped
    networks:
      - threat-intel

  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    environment:
      - ELASTICSEARCH_HOSTS=https://elasticsearch:9200
      - ELASTICSEARCH_USERNAME=kibana
      - ELASTICSEARCH_PASSWORD=${ELASTIC_PASSWORD}
    ports:
      - "5601:5601"
    restart: unless-stopped
    networks:
      - threat-intel
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    volumes:
      - ./monitoring/elk/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
      - ./logs:/var/log/threat-intel
    ports:
      - "5044:5044"
      - "5000:5000"
      - "9600:9600"
    restart: unless-stopped
    networks:
      - threat-intel
    depends_on:
      - elasticsearch

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  threat-intel:
    driver: bridge
    ipam:
      config:
        - subnet: 192.168.1.0/24
```

### Kubernetes Configuration

**File**: `kubernetes/api-deployment.yml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: threat-intel-api
  namespace: threat-intel
spec:
  replicas: 3
  selector:
    matchLabels:
      app: threat-intel-api
  template:
    metadata:
      labels:
        app: threat-intel-api
    spec:
      containers:
      - name: api
        image: threat-intel/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: POSTGRES_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: postgres-url
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: mongodb-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: cache-secret
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
        - name: ssl
          mountPath: /app/ssl
      volumes:
      - name: logs
        persistentVolumeClaim:
          claimName: logs-pvc
      - name: ssl
        secret:
          secretName: ssl-certs
```

---

For more detailed configuration options, refer to:
- [Installation Guide](../setup/installation-guide.md) for initial setup
- [Architecture Overview](../architecture/architecture-overview.md) for system design
- [Database Schema](../database/database-schema.md) for data structure
- [API Documentation](../api/openapi-specification.md) for endpoint configuration

For support, see the [Troubleshooting Guide](../troubleshooting/troubleshooting-guide.md).
