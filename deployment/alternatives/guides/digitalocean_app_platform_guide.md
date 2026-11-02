# DigitalOcean App Platform Deployment Guide for Threat Intelligence Platform

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Platform Overview](#platform-overview)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Custom Domains & SSL](#custom-domains--ssl)
7. [Monitoring & Logs](#monitoring--logs)
8. Scaling & Performance
9. Background Jobs
10. Backup & Recovery
11. Troubleshooting
12. Cost Optimization

## Prerequisites

### Required Tools
- DigitalOcean account
- doctl (DigitalOcean CLI) - optional
- Git
- GitHub/GitLab account

### System Requirements
- Minimum 0.6 vCPU, 1GB RAM per component
- 10GB storage minimum
- DO Spaces for file storage (optional)

### Pre-deployment Checklist
- [ ] DigitalOcean account with billing enabled
- [ ] GitHub/GitLab repository ready
- [ ] App spec configuration prepared
- [ ] Environment variables documented
- [ ] Domain configured (optional)

## Platform Overview

### What is DigitalOcean App Platform?
DigitalOcean App Platform is a managed PaaS providing:
- **Web applications** with automatic scaling
- **Background workers** for queue processing
- **Cron jobs** for scheduled tasks
- **Databases** (Managed PostgreSQL, MySQL, Redis)
- **Spaces** for static file storage

### Pricing Structure
- **Starter**: $5/month (512MB RAM, shared CPU)
- **Basic**: $12/month (1GB RAM, 1 vCPU)
- **Professional**: $24/month (2GB RAM, 2 vCPUs)
- **Database Add-ons**: $15-90/month depending on size
- **Usage**: Compute, database, storage, bandwidth

### Why DigitalOcean App Platform for Threat Intelligence Platform?
✅ **Predictable pricing** - Transparent cost structure  
✅ **Managed databases** - Built-in PostgreSQL with extensions  
✅ **Integration** - Works seamlessly with DO ecosystem  
✅ **Enterprise-grade** - SLA and security features  
✅ **Developer-friendly** - Good documentation and support  

## Step-by-Step Deployment

### Step 1: Create DigitalOcean Account

1. **Sign up**: Go to [digitalocean.com](https://digitalocean.com)
2. **Enable billing**: Add payment method
3. **Verify email**: Complete account verification
4. **Install doctl** (optional but recommended):
   ```bash
   # macOS
   brew install doctl
   
   # Linux
   wget https://github.com/digitalocean/doctl/releases/download/v1.94.0/doctl-1.94.0-linux-amd64.tar.gz
   tar xf doctl-1.94.0-linux-amd64.tar.gz
   sudo mv doctl /usr/local/bin
   ```

### Step 2: Authenticate doctl (Optional)

```bash
# Create API token in DO dashboard
# Then authenticate
doctl auth init

# Test authentication
doctl account get
```

### Step 3: Create App Specification

Create `.do/app.yaml` in your project root:

```yaml
name: threat-intelligence-platform
services:
  # FastAPI Web Service
  - name: web
    source_dir: /
    github:
      repo: your-username/threat-intelligence-platform
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    health_check:
      http_path: /health
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}
      - key: SECRET_KEY
        type: SECRET
        value: your-secret-key-here
      - key: DEBUG
        value: "false"
      - key: LOG_LEVEL
        value: INFO
    routes:
      - path: /
    auto_deploy: true
    static_sites: []

  # Celery Worker
  - name: worker
    source_dir: /
    github:
      repo: your-username/threat-intelligence-platform
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: celery -A app.celery worker --loglevel=info
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}
    auto_deploy: true

  # Celery Beat Scheduler
  - name: beat
    source_dir: /
    github:
      repo: your-username/threat-intelligence-platform
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: celery -A app.celery beat --loglevel=info
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}
    auto_deploy: true

jobs:
  # Cron Job for Data Collection
  - name: collect-threat-data
    source_dir: /
    github:
      repo: your-username/threat-intelligence-platform
      branch: main
      deploy_on_push: true
    build_command: pip install -r requirements.txt
    run_command: python scripts/collect_threat_data.py
    environment_slug: python
    instance_size_slug: basic-xxs
    schedule: "0 */6 * * *"  # Every 6 hours
    envs:
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
      - key: REDIS_URL
        value: ${redis.REDIS_URL}

databases:
  # PostgreSQL Database
  - name: db
    engine: PG
    version: "14"
    size: db-s-dev-database
    num_nodes: 1
    protect: false
    production: false
  
  # Redis Cache
  - name: redis
    engine: REDIS
    version: "7"
    size: db-s-dev-database
    num_nodes: 1
    protect: false
    production: false

static_sites: []
```

### Step 4: Create App Spec Using Dashboard

1. **Create New App**:
   - Go to DigitalOcean dashboard
   - Click "Create" → "Apps"
   - Select "GitHub" or "GitLab" as source

2. **Configure Source**:
   ```
   Repository: your-username/threat-intelligence-platform
   Branch: main
   Source Directory: /
   ```

3. **Configure Web Service**:
   ```
   Name: web
   Build Command: pip install -r requirements.txt
   Run Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   Environment: Python
   Instance Type: Basic ($12/month)
   Instance Count: 1
   ```

4. **Add Worker Services**:
   Add "Worker" components for Celery worker and beat

5. **Add Cron Jobs**:
   Add cron job for scheduled threat data collection

6. **Add Databases**:
   - PostgreSQL 14 database
   - Redis 7 database

7. **Configure Environment Variables**:
   Add all required environment variables (see Environment Configuration section)

8. **Review and Deploy**:
   - Review all settings
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)

### Step 5: Verify Deployment

```bash
# Get your app URL from DO dashboard
# Test health endpoint
curl https://your-app.ondigitalocean.app/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

### Step 6: Deploy Using doctl (Alternative)

```bash
# Save app spec as app.yaml
# Deploy app
doctl apps create --spec app.yaml

# Get app details
doctl apps list

# Check app status
doctl apps get <app-id>
```

## Database Setup

### Managed PostgreSQL Configuration

```yaml
# In app.yaml
databases:
  - name: db
    engine: PG
    version: "14"
    size: db-s-dev-database  # $15/month
    # or db-s-1vcpu-1gb: $29/month for production
    num_nodes: 1
    protect: false
```

### TimescaleDB Extension

DigitalOcean managed PostgreSQL supports TimescaleDB:

```sql
-- Connect to your database
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'timescaledb';
```

### Database Migration

Create `scripts/init_db.py`:

```python
import os
import sys
from sqlalchemy import create_engine, text
from alembic.config import main as alembic_main

def wait_for_db():
    """Wait for database to be ready"""
    import time
    import psycopg2
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            print("Database is ready!")
            return True
        except psycopg2.OperationalError:
            attempt += 1
            print(f"Waiting for database... (attempt {attempt}/{max_attempts})")
            time.sleep(2)
    
    raise Exception("Database not available after maximum attempts")

def run_migrations():
    """Run database migrations"""
    # Set alembic environment
    os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL')
    
    # Run migrations
    sys.argv = ['alembic', 'upgrade', 'head']
    alembic_main()

def enable_extensions():
    """Enable necessary PostgreSQL extensions"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Enable TimescaleDB
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        
        # Enable other useful extensions
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\" CASCADE"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm CASCADE"))
        
        conn.commit()

def main():
    print("Initializing database...")
    
    # Wait for database
    wait_for_db()
    
    # Enable extensions
    print("Enabling extensions...")
    enable_extensions()
    
    # Run migrations
    print("Running migrations...")
    run_migrations()
    
    print("Database initialization completed!")

if __name__ == "__main__":
    main()
```

### Database Backup

DigitalOcean provides automated backups for managed databases:

```bash
# Backup frequency:
# Starter: Daily backups, 7-day retention
# Standard: Daily backups, 30-day retention
# Premium: 4-hour backups, 30-day retention

# Manual backup via pg_dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_20251030_120000.sql
```

### Database Connection Configuration

```python
# Database connection optimization for DO managed PostgreSQL
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import os

DATABASE_URL = os.getenv('DATABASE_URL')

# Optimize for managed database
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "application_name": "threat_intel_platform"
    }
)
```

## Environment Configuration

### Environment Variables

In DO App Platform dashboard, go to your app → Settings → Environment Variables:

```bash
# Application Configuration
SECRET_KEY=your-256-bit-secret-key-here
DEBUG=false
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1
PROJECT_NAME=Threat Intelligence Platform

# Database Configuration
DATABASE_URL=${db.DATABASE_URL}  # Auto-populated
REDIS_URL=${redis.REDIS_URL}     # Auto-populated

# Security Settings
JWT_SECRET=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600
CORS_ORIGINS=["https://yourdomain.com"]

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Background Jobs
CELERY_BROKER_URL=${redis.REDIS_URL}
CELERY_RESULT_BACKEND=${redis.REDIS_URL}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_ACKS_LATE=true

# Monitoring
PROMETHEUS_PORT=9090
METRICS_ENDPOINT=/metrics

# External APIs
VIRUSTOTAL_API_KEY=your-virustotal-api-key
ABUSEIPDB_API_KEY=your-abuseipdb-api-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# File Storage
UPLOAD_PATH=/tmp/uploads
MAX_FILE_SIZE=10485760  # 10MB

# Timezone
TZ=UTC

# Application Performance
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
TIMEOUT=30
KEEPALIVE=5
```

### Environment File Setup

Create `.env.production`:

```bash
# Copy template
cp .env.template .env.production

# Update with production values
# Set in DO dashboard or via doctl

# Upload via doctl (if using CLI)
doctl apps update <app-id> --env-file .env.production
```

### Environment Validation

```python
# Add environment validation at startup
import os
from typing import List

def validate_environment():
    """Validate required environment variables"""
    required_vars: List[str] = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'JWT_SECRET',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    # Validate specific formats
    secret_key = os.getenv('SECRET_KEY')
    if len(secret_key) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters")
    
    # Validate URLs
    database_url = os.getenv('DATABASE_URL')
    if not database_url.startswith('postgresql://'):
        raise ValueError("DATABASE_URL must be a PostgreSQL URL")

# Run validation at startup
validate_environment()
```

## Custom Domains & SSL

### Add Custom Domain

1. **In DO Dashboard**:
   - Go to your app → Settings → Domains
   - Add domain: `api.yourdomain.com`
   - Add root domain: `yourdomain.com`

2. **Configure DNS**:
   Add CNAME records in your DNS provider:

   ```
   Type: CNAME
   Name: api
   Value: your-app.ondigitalocean.app
   TTL: 300

   Type: CNAME
   Name: www
   Value: your-app.ondigitalocean.app
   TTL: 300

   Type: A (for root domain)
   Name: @
   Value: [IP provided by DO]
   TTL: 300
   ```

### SSL Certificate

DigitalOcean automatically provisions Let's Encrypt certificates:

```bash
# SSL is automatically enabled
# Check SSL status in dashboard

# Test SSL certificate
curl -I https://api.yourdomain.com

# Expected: HTTP/2 200
# Certificate: Let's Encrypt Authority X3
```

### Force HTTPS

```python
# Add to your FastAPI application
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os

app = FastAPI()

# Force HTTPS in production
if os.getenv("ENFORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# Alternatively, handle in reverse proxy
```

## Monitoring & Logs

### Access Logs

1. **In DO Dashboard**:
   - Go to your app → Overview → Activity
   - View deployment logs
   - Monitor component status

2. **Component Logs**:
   - Click on any service (web, worker, cron)
   - View runtime logs in real-time

### Structured Logging

```python
# Configure structured logging
import structlog
import logging
import sys

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    import time
    
    start_time = time.time()
    
    # Log request
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "request_completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Health Check Endpoint

```python
# Comprehensive health check
from fastapi import APIRouter
from sqlalchemy import create_engine, text
import redis
import os
import psutil
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check for DO App Platform"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "platform": "digitalocean_app_platform",
        "checks": {}
    }
    
    # Database health
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Redis health
    try:
        redis_url = os.getenv('REDIS_URL')
        r = redis.from_url(redis_url)
        r.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "type": "redis"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy", 
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # System health
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        health_status["checks"]["system"] = {
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "cpu": {
                "percent": cpu_percent
            }
        }
        
        # Alert if resources are high
        if memory.percent > 80:
            health_status["status"] = "degraded"
            health_status["checks"]["system"]["alert"] = "High memory usage"
        
        if cpu_percent > 80:
            health_status["status"] = "degraded"
            health_status["checks"]["system"]["alert"] = "High CPU usage"
            
    except Exception as e:
        health_status["checks"]["system"] = {
            "status": "unavailable",
            "error": str(e)
        }
    
    # Background jobs health
    try:
        from app.celery import celery_app
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        
        health_status["checks"]["background_jobs"] = {
            "status": "healthy" if stats else "no_workers",
            "active_workers": len(stats) if stats else 0
        }
    except Exception as e:
        health_status["checks"]["background_jobs"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
```

### Prometheus Metrics

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
ACTIVE_CONNECTIONS = Gauge('active_database_connections', 'Active database connections')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()
    
    REQUEST_LATENCY.observe(process_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Scaling & Performance

### Horizontal Scaling

```yaml
# In app.yaml
services:
  - name: web
    instance_count: 2  # Scale to multiple instances
    instance_size_slug: basic-s  # Upgrade instance size
```

### Vertical Scaling

Upgrade instance size in DO dashboard:

```
Basic ($12/month): 1GB RAM, 1 vCPU
Professional ($24/month): 2GB RAM, 2 vCPUs
```

### Auto-scaling Configuration

```yaml
# Add scaling rules to app.yaml
services:
  - name: web
    instance_count: 1
    instance_size_slug: basic-xxs
    autoscaling:
      enabled: true
      min_instance_count: 1
      max_instance_count: 5
      target_cpu_utilization_percentage: 70
      target_memory_utilization_percentage: 80
```

### Performance Optimization

```python
# Optimize for DO App Platform
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(
    title="Threat Intelligence Platform",
    description="Cybersecurity threat intelligence analysis",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG") == "true" else None
)

# Add middleware for performance
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "[]"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.ondigitalocean.app"]
)

# Database optimization
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.getenv('DATABASE_URL'),
    poolclass=QueuePool,
    pool_size=25,
    max_overflow=50,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "connect_timeout": 10,
        "application_name": "threat_intel_platform"
    }
)
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test your application
ab -n 1000 -c 10 https://your-app.ondigitalocean.app/health

# Test with specific endpoint
ab -n 500 -c 5 -p payload.json -T "application/json" \
   https://your-app.ondigitalocean.app/api/v1/search
```

### Caching Implementation

```python
# Redis caching implementation
from fastapi import HTTPException
import json
import hashlib
import redis

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key"""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

async def get_cached_data(cache_key: str, fetch_func, expiration: int = 300):
    """Get cached data or fetch fresh data"""
    redis_client = redis.from_url(os.getenv('REDIS_URL'))
    
    try:
        # Try to get from cache
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache read error: {e}")
    
    # Fetch fresh data
    try:
        result = await fetch_func()
        
        # Cache the result
        redis_client.setex(cache_key, expiration, json.dumps(result))
        return result
    except Exception as e:
        logger.error(f"Cache write error: {e}")
        raise HTTPException(status_code=500, detail="Data fetch failed")

# Usage example
@router.get("/threats/search")
async def search_threats(query: str, limit: int = 10):
    cache_key = generate_cache_key("threats_search", query, limit)
    
    async def fetch_threats():
        # Your database query logic here
        # return await threat_service.search_threats(query, limit)
        return {"results": [], "count": 0}
    
    return await get_cached_data(cache_key, fetch_threats, expiration=60)
```

## Background Jobs

### Celery Worker Configuration

```python
# app/celery.py
from celery import Celery
import os

# Initialize Celery
celery_app = Celery(
    'threat_intel',
    broker=os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL')),
    backend=os.getenv('CELERY_RESULT_BACKEND', os.getenv('REDIS_URL')),
    include=['app.tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task routing
    task_routes={
        'app.tasks.threat_analysis': {'queue': 'threats'},
        'app.tasks.data_collection': {'queue': 'collection'},
        'app.tasks.report_generation': {'queue': 'reports'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Result backend configuration
    result_expires=3600,  # 1 hour
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Beat scheduler configuration
celery_app.conf.beat_schedule = {
    'collect-threat-data': {
        'task': 'app.tasks.collect_threat_data',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-data': {
        'task': 'app.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Daily
    },
}
```

### Task Implementation

```python
# app/tasks.py
from app.celery import celery_app
import structlog
import asyncio
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Threat, ThreatIndicator

logger = structlog.get_logger()

@celery_app.task(name='app.tasks.threat_analysis')
def analyze_threat(threat_id: int):
    """Analyze a threat indicator"""
    logger.info("Starting threat analysis", threat_id=threat_id)
    
    try:
        # Get database session
        db = SessionLocal()
        
        # Fetch threat
        threat = db.query(Threat).filter(Threat.id == threat_id).first()
        if not threat:
            logger.error("Threat not found", threat_id=threat_id)
            return
        
        # Perform analysis
        # ... your analysis logic here
        
        # Update threat status
        threat.analysis_status = 'completed'
        threat.analysis_completed_at = datetime.utcnow()
        
        db.commit()
        db.close()
        
        logger.info("Threat analysis completed", threat_id=threat_id)
        
    except Exception as e:
        logger.error("Threat analysis failed", threat_id=threat_id, error=str(e))
        raise

@celery_app.task(name='app.tasks.collect_threat_data')
def collect_threat_data():
    """Collect threat data from external sources"""
    logger.info("Starting threat data collection")
    
    try:
        # Your data collection logic
        # ... collect from VirusTotal, AbuseIPDB, etc.
        
        logger.info("Threat data collection completed")
        
    except Exception as e:
        logger.error("Threat data collection failed", error=str(e))
        raise

@celery_app.task(name='app.tasks.generate_report')
def generate_report(report_id: int):
    """Generate threat intelligence report"""
    logger.info("Generating report", report_id=report_id)
    
    try:
        # Your report generation logic
        # ...
        
        logger.info("Report generation completed", report_id=report_id)
        
    except Exception as e:
        logger.error("Report generation failed", report_id=report_id, error=str(e))
        raise
```

## Backup & Recovery

### Automated Backups

DigitalOcean provides automatic backups for managed databases:

```bash
# Backup schedule:
# Starter: Daily backups, 7-day retention
# Standard: Daily backups, 30-day retention  
# Premium: 4-hour backups, 30-day retention

# Configure in DO dashboard:
# Database > Settings > Backups > Auto-backup
```

### Manual Backup

```bash
#!/bin/bash
# backup_do_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/backups"
BACKUP_FILE="$BACKUP_DIR/threatintel_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Upload to DO Spaces (optional)
# Configure spaces credentials first
if command -v aws &> /dev/null && [ -n "$DO_SPACES_KEY" ]; then
    aws s3 cp $BACKUP_FILE.gz \
        s3://your-backup-bucket/threatintel/ \
        --endpoint-url https://nyc3.digitaloceanspaces.com \
        --access-key-id $DO_SPACES_KEY \
        --secret-access-key $DO_SPACES_SECRET
    
    echo "Backup uploaded to DO Spaces"
fi

# Clean up local backup
rm $BACKUP_FILE.gz

echo "Backup completed: threatintel_backup_$DATE.sql.gz"
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster_recovery_do.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./disaster_recovery_do.sh <backup_file>"
    exit 1
fi

echo "Starting disaster recovery from: $BACKUP_FILE"

# Decompress backup
gunzip -c $BACKUP_FILE > /tmp/restore.sql

# Connect to database and restore
psql $DATABASE_URL < /tmp/restore.sql

# Verify restoration
echo "Verifying restoration..."
psql $DATABASE_URL -c "SELECT COUNT(*) FROM threats;"

# Clean up
rm /tmp/restore.sql

echo "Disaster recovery completed"
```

### Backup Verification

```python
# Add backup verification to health check
@router.get("/health/backup")
async def backup_health():
    """Check backup status"""
    backup_status = {
        "last_backup": None,
        "backup_size": 0,
        "backup_count": 0,
        "status": "unknown"
    }
    
    try:
        # Check DO Spaces for backup files
        # This is a placeholder - implement based on your backup storage
        backup_status["status"] = "healthy"
        backup_status["last_backup"] = "2025-10-30T12:00:00Z"
        backup_status["backup_count"] = 7
        
    except Exception as e:
        backup_status["status"] = f"error: {str(e)}"
    
    return backup_status
```

## Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Check build logs in DO dashboard
# Component > Deployments > View logs

# Common issues:
# - Python dependencies missing
# - Build timeout
# - Incorrect build command

# Solutions:
# 1. Add missing dependencies to requirements.txt
# 2. Optimize build command
# 3. Use --no-cache-dir for pip installs
```

#### 2. Database Connection Issues

```python
# Test database connectivity
import os
import psycopg2

def test_database_connection():
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Database connected successfully: {version[0]}")
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()
```

#### 3. Environment Variable Issues

```python
# Environment variable validation
def validate_environment():
    required_vars = {
        'SECRET_KEY': 'Application secret key',
        'DATABASE_URL': 'Database connection string',
        'REDIS_URL': 'Redis connection string',
        'JWT_SECRET': 'JWT signing secret',
    }
    
    missing = []
    warnings = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var}: {description}")
        elif var == 'SECRET_KEY' and len(value) < 32:
            warnings.append(f"{var}: Should be at least 32 characters")
    
    if missing:
        raise ValueError(f"Missing required environment variables:\n" + "\n".join(missing))
    
    if warnings:
        logger.warning("Environment variable warnings:\n" + "\n".join(warnings))

# Run validation at startup
validate_environment()
```

#### 4. SSL Certificate Issues

```bash
# Check SSL status in DO dashboard
# Domain should show "Active" with green checkmark

# Test SSL
curl -I https://api.yourdomain.com
# Expected: HTTP/2 200

# If SSL is not working:
# 1. Verify DNS is correctly configured
# 2. Wait 5-10 minutes for certificate provisioning
# 3. Check domain settings in DO dashboard
```

#### 5. High Response Times

```python
# Add performance monitoring
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    import time
    import structlog
    
    logger = structlog.get_logger()
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    # Log slow requests (> 1 second)
    if process_time > 1.0:
        logger.warning(
            "Slow request detected",
            url=str(request.url),
            method=request.method,
            process_time=process_time,
            client_ip=request.client.host
        )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Performance Monitoring

#### Database Performance

```sql
-- Enable query logging (requires database settings)
-- Check slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database connections
SELECT count(*) as active_connections FROM pg_stat_activity;

-- Check database size
SELECT pg_size_pretty(pg_database_size('threatintel'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

#### Application Performance

```python
# Add detailed metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Application metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
ACTIVE_USERS = Gauge('active_users', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections', 'Active database connections')

@app.middleware("http")
async def detailed_metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Get request info
    method = request.method
    endpoint = request.url.path
    
    response = await call_next(request)
    
    # Record metrics
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
    REQUEST_LATENCY.observe(time.time() - start_time)
    
    return response

@app.get("/admin/metrics")
async def admin_metrics():
    """Admin-only metrics endpoint"""
    # Add authentication check here
    return Response(generate_latest(), media_type="text/plain")
```

## Cost Optimization

### Monitor Costs

```bash
# Estimated monthly costs for DO App Platform:
# Web Service (Basic): $12/month
# Worker Service (Basic): $12/month  
# Beat Service (Basic): $12/month
# PostgreSQL DB: $15/month
# Redis DB: $15/month
# Bandwidth: $5-15/month
# Total: $71-81/month

# Production costs (Professional tier):
# Web Service (Professional): $24/month
# Worker Service (Professional): $24/month
# PostgreSQL DB: $29/month
# Redis DB: $29/month
# Bandwidth: $10-20/month
# Total: $116-126/month
```

### Optimization Strategies

1. **Right-size instances**:
   ```yaml
   # Use Basic tier for development
   instance_size_slug: basic-xxs  # $12/month
   
   # Upgrade to Professional for production
   instance_size_slug: basic-s    # $24/month
   ```

2. **Implement caching**:
   ```python
   # Cache expensive operations
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_computation(param: str):
       # Your expensive computation
       return result
   ```

3. **Database optimization**:
   ```sql
   -- Add indexes for frequent queries
   CREATE INDEX CONCURRENTLY idx_threats_timestamp ON threats(timestamp);
   CREATE INDEX CONCURRENTLY idx_threats_ioc_hash ON threats(ioc_hash);
   
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM threats WHERE timestamp > NOW() - INTERVAL '1 day';
   ```

4. **Connection pooling**:
   ```python
   # Optimize database connections
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_recycle=3600,
       pool_pre_ping=True
   )
   ```

### Cost Monitoring Script

```bash
#!/bin/bash
# monitor_do_costs.sh

echo "=== DigitalOcean App Platform Cost Analysis ==="
echo "Date: $(date)"
echo ""

echo "Current Configuration Costs:"
echo "Development Configuration:"
echo "- Web Service (Basic): $12/month"
echo "- Worker Service (Basic): $12/month"
echo "- Beat Service (Basic): $12/month"
echo "- PostgreSQL DB: $15/month"
echo "- Redis DB: $15/month"
echo "- Estimated Bandwidth: $10/month"
echo "Subtotal: $76/month"
echo ""

echo "Production Configuration:"
echo "- Web Service (Professional): $24/month"
echo "- Worker Service (Professional): $24/month"
echo "- PostgreSQL DB: $29/month"
echo "- Redis DB: $29/month"
echo "- Estimated Bandwidth: $15/month"
echo "Subtotal: $121/month"
echo ""

echo "Cost Optimization Strategies:"
echo "1. Use Basic tier for development/testing"
echo "2. Implement Redis caching to reduce DB queries"
echo "3. Add database indexes for common queries"
echo "4. Use connection pooling"
echo "5. Monitor bandwidth usage"
echo "6. Consider Reserved Database instances for production"
echo ""

echo "Estimated Savings:"
echo "- Caching: 20-30% reduction in database load"
echo "- Optimization: 15-25% reduction in compute usage"
echo "- Reserved instances: 30-40% reduction in database costs"
```

## Conclusion

DigitalOcean App Platform provides an excellent balance of features, performance, and cost for deploying the Threat Intelligence Platform:

✅ **Predictable pricing** - Transparent cost structure, $76-121/month  
✅ **Managed infrastructure** - No server management required  
✅ **Database integration** - Built-in PostgreSQL and Redis  
✅ **Good performance** - Fast response times and reliability  
✅ **Developer experience** - Good documentation and support  

### Next Steps
1. Follow this guide to deploy your application
2. Configure monitoring and alerting
3. Set up automated backups
4. Implement cost optimization strategies
5. Test disaster recovery procedures

### Additional Resources
- [DigitalOcean App Platform Documentation](https://docs.digitalocean.com/products/app-platform/)
- [DigitalOcean Community](https://community.digitalocean.com)
- [Best Practices Guide](https://docs.digitalocean.com/products/app-platform/how-to/app-platform-best-practices/)

---

**Deployment Time**: ~45 minutes  
**Difficulty Level**: Intermediate  
**Monthly Cost**: $76 (Basic) / $121 (Professional)  
**Last Updated**: October 30, 2025
