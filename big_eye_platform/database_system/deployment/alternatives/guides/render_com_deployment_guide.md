# Render.com Deployment Guide for Threat Intelligence Platform

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Platform Overview](#platform-overview)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Custom Domains & SSL](#custom-domains--ssl)
7. [Monitoring & Logs](#monitoring--logs)
8. [Scaling & Performance](#scaling--performance)
9. [Background Jobs](#background-jobs)
10. [Backup & Recovery](#backup--recovery)
11. [Troubleshooting](#troubleshooting)
12. [Cost Optimization](#cost-optimization)

## Prerequisites

### Required Tools
- Git
- GitHub/GitLab account
- Render account (free signup)
- Docker (optional, for local testing)

### System Requirements
- Minimum 0.5 vCPU, 1GB RAM per service
- 10GB storage minimum
- Persistent storage for databases

### Pre-deployment Checklist
- [ ] Threat Intelligence Platform source code ready
- [ ] Render configuration files prepared
- [ ] Environment variables documented
- [ ] Domain name configured (optional)

## Platform Overview

### What is Render.com?
Render is a unified cloud platform providing:
- **Web Services** (for FastAPI, Node.js apps)
- **Background Workers** (for Celery, queue processing)
- **Cron Jobs** (for scheduled tasks)
- **Databases** (PostgreSQL, Redis)
- **Static Sites** (for frontend)

### Pricing Structure
- **Free Tier**: Limited resources, 30-minute spin-down
- **Starter**: $7/month (always-on instances)
- **Standard**: $25/month (better performance)
- **Database Add-ons**: $9-29/month depending on size
- **Usage**: CPU, RAM, storage, bandwidth

### Why Render.com for Threat Intelligence Platform?
✅ **Heroku-like experience** - Familiar deployment model  
✅ **Database add-ons** - PostgreSQL and Redis available  
✅ **Background jobs** - Built-in worker support  
✅ **Cron jobs** - Scheduled tasks built-in  
✅ **Reliable uptime** - 99.95% SLA  

## Step-by-Step Deployment

### Step 1: Create Render Account

1. **Sign up**: Go to [render.com](https://render.com) and create account
2. **Connect GitHub/GitLab**: Link your repository
3. **Authorize Render**: Grant necessary permissions

### Step 2: Prepare Your Repository

Create `render.yaml` in your project root:

```yaml
services:
  # FastAPI Web Service
  - type: web
    name: threat-intel-api
    env: python
    plan: starter
    buildCommand: |
      pip install -r requirements.txt
      python manage.py migrate
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: false
      - key: LOG_LEVEL
        value: INFO

  # Celery Worker
  - type: worker
    name: threat-intel-worker
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString

  # Celery Beat Scheduler
  - type: worker
    name: threat-intel-beat
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery beat --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString

  # Cron Job for Data Collection
  - type: cron
    name: threat-intel-cron
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/collect_threat_data.py
    schedule: "0 */6 * * *"  # Every 6 hours

databases:
  # PostgreSQL Database
  - name: threat-intel-db
    databaseName: threatintel
    user: threatintel
    plan: starter

  # Redis Cache
  - name: threat-intel-cache
    plan: starter
```

### Step 3: Create Procfile

Create `Procfile` in your project root:

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
worker: celery -A app.celery worker --loglevel=info --concurrency=2
beat: celery -A app.celery beat --loglevel=info
```

### Step 4: Configure Requirements.txt

Ensure your `requirements.txt` includes all necessary dependencies:

```txt
# Core FastAPI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
asyncpg==0.29.0

# Background Jobs
celery==5.3.4
kombu==5.3.4

# Monitoring
prometheus-client==0.19.0
structlog==23.2.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# API Documentation
fastapi[all]==0.104.1

# Time Series Database (TimescaleDB)
psycopg2-binary==2.9.9

# HTTP Client
httpx==0.25.2
aiohttp==3.9.1

# Utilities
python-dotenv==1.0.0
pytz==2023.3
orjson==3.9.10
```

### Step 5: Create Start Scripts

Create `start.sh`:

```bash
#!/bin/bash
set -e

echo "Starting Threat Intelligence Platform..."

# Wait for database
echo "Waiting for database..."
python scripts/wait_for_db.py

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Start the application
echo "Starting application..."
exec "$@"
```

Make it executable:

```bash
chmod +x start.sh
```

### Step 6: Deploy to Render

1. **Create New Service**:
   - Go to Render dashboard
   - Click "New +" → "Web Service"
   - Connect your Git repository

2. **Configure Service**:
   ```
   Name: threat-intel-api
   Region: Oregon (US West) [closest to you]
   Branch: main
   Root Directory: ./
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: ./start.sh uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Configure Environment**:
   - Add environment variables (see Environment Configuration section)
   - Connect databases if using managed database
   - Set scaling options

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for build and deployment (~5-10 minutes)
   - Monitor deployment in real-time logs

### Step 7: Verify Deployment

```bash
# Get your service URL from Render dashboard
# Test health endpoint
curl https://your-service.onrender.com/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

## Database Setup

### Option 1: Render Managed PostgreSQL

```yaml
# Add to render.yaml
databases:
  - name: threat-intel-db
    databaseName: threatintel
    user: threatintel
    plan: starter  # $9/month
    # or plan: standard  # $29/month for production
```

### Option 2: Render Managed Redis

```yaml
databases:
  - name: threat-intel-cache
    plan: starter  # $9/month
```

### Option 3: External Database

```bash
# Set DATABASE_URL manually
DATABASE_URL=postgresql://user:password@host:port/database
```

### Database Migration

Create `scripts/wait_for_db.py`:

```python
import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor

def wait_for_db():
    """Wait for database to be ready"""
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            DATABASE_URL = os.getenv('DATABASE_URL')
            if not DATABASE_URL:
                raise ValueError("DATABASE_URL not set")
            
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
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

if __name__ == "__main__":
    wait_for_db()
```

Run migrations:

```python
# Create manage.py
#!/usr/bin/env python
import os
import sys
from sqlalchemy import create_engine
from alembic.config import main as alembic_main

def main():
    """Run database migrations"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set")
    
    # Set alembic configuration
    os.environ['DATABASE_URL'] = DATABASE_URL
    
    # Run migrations
    sys.argv = ['alembic', 'upgrade', 'head']
    alembic_main()

if __name__ == "__main__":
    main()
```

### Database Backup

Render provides automatic backups for managed databases:

```bash
# Access database backups in Render dashboard:
# Database > Settings > Backups > Auto-backup

# Manual backup via pg_dump
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
psql $DATABASE_URL < backup_20251030_120000.sql
```

## Environment Configuration

### Set Environment Variables

In Render dashboard, go to your service → Environment:

```bash
# Application Settings
SECRET_KEY=your-256-bit-secret-key-here
DEBUG=false
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1
PROJECT_NAME=Threat Intelligence Platform

# Database Configuration
DATABASE_URL=${DATABASE_URL}  # Auto-populated for managed DB
REDIS_URL=${REDIS_URL}        # Auto-populated for managed Redis

# Security
JWT_SECRET=your-jwt-secret
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
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

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
```

### Use Environment File

Create `.env.production`:

```bash
# Copy template
cp .env.template .env.production

# Edit with your values
nano .env.production

# Set in Render dashboard manually or use Render CLI
render-cli variables set --service threat-intel-api --file .env.production
```

## Custom Domains & SSL

### Add Custom Domain

1. **In Render Dashboard**:
   - Go to your service → Settings → Domains
   - Add custom domain: `api.yourdomain.com`
   - Add www subdomain: `www.yourdomain.com`

2. **Configure DNS**:
   Add CNAME records in your DNS provider:

   ```
   Type: CNAME
   Name: api
   Value: threat-intel-api.onrender.com
   TTL: 300

   Type: CNAME
   Name: www
   Value: threat-intel-api.onrender.com
   TTL: 300
   ```

3. **Wait for SSL**:
   - Render automatically provisions Let's Encrypt certificates
   - SSL activation takes 5-10 minutes
   - Check status in dashboard

### Force HTTPS

```python
# Add to your FastAPI middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Redirect HTTP to HTTPS
if os.getenv("ENFORCE_HTTPS", "true").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)
```

## Monitoring & Logs

### Access Logs

1. **In Render Dashboard**:
   - Go to your service → Logs
   - View real-time or historical logs
   - Filter by service (web, worker, cron)

2. **Log Levels**:
   ```
   ERROR: Application errors
   WARN: Warnings and non-critical issues
   INFO: General application information
   DEBUG: Detailed debugging information
   ```

### Set Up Custom Logging

```python
# Add to app/main.py
import structlog
import logging
from pythonjsonlogger import jsonlogger

# Configure structured logging
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
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    # Add custom header with process time
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### Health Monitoring

```python
# Create app/api/v1/endpoints/health.py
from fastapi import APIRouter
from sqlalchemy import text
import redis
import os
import psutil

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database health
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Redis health
    try:
        redis_url = os.getenv('REDIS_URL')
        r = redis.from_url(redis_url)
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Memory usage
    memory = psutil.virtual_memory()
    health_status["checks"]["memory"] = {
        "total": memory.total,
        "available": memory.available,
        "percent": memory.percent
    }
    
    # Disk usage
    disk = psutil.disk_usage('/')
    health_status["checks"]["disk"] = {
        "total": disk.total,
        "free": disk.free,
        "percent": (disk.used / disk.total) * 100
    }
    
    return health_status
```

## Scaling & Performance

### Auto-scaling Configuration

Render provides automatic scaling based on CPU usage:

1. **In Render Dashboard**:
   - Go to your service → Settings → Scaling
   - Configure minimum and maximum instances
   - Set CPU threshold for scaling

2. **Manual Scaling**:
   ```yaml
   # In render.yaml
   services:
     - type: web
       name: threat-intel-api
       plan: standard  # Better for scaling
       minInstances: 1
       maxInstances: 5
   ```

### Performance Optimization

```python
# Optimize FastAPI for production
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Threat Intelligence Platform",
    description="Cybersecurity threat intelligence analysis",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG") == "true" else None
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "[]"),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection optimization
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 1000 -c 10 https://your-service.onrender.com/health

# Expected output should show:
# Requests per second: > 100
# Time per request: < 10ms
```

### Cache Implementation

```python
# Add Redis caching
from fastapi import HTTPException
import json
import hashlib

def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key"""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

async def get_cached_result(key: str, fetch_func, expiration: int = 300):
    """Get cached result or fetch new data"""
    redis_client = redis.from_url(os.getenv('REDIS_URL'))
    
    # Try to get from cache
    cached = redis_client.get(key)
    if cached:
        return json.loads(cached)
    
    # Fetch fresh data
    result = await fetch_func()
    
    # Cache the result
    redis_client.setex(key, expiration, json.dumps(result))
    return result

# Usage example
@router.get("/threats/search")
async def search_threats(query: str, limit: int = 10):
    key = cache_key("threats_search", query, limit)
    
    async def fetch_threats():
        # Your database query here
        return await threat_service.search_threats(query, limit)
    
    return await get_cached_result(key, fetch_threats, expiration=60)
```

## Background Jobs

### Render Worker Services

```yaml
# In render.yaml
services:
  # Celery Worker
  - type: worker
    name: threat-intel-worker
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery worker --loglevel=info --concurrency=2
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString

  # Celery Beat
  - type: worker
    name: threat-intel-beat
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery beat --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString
```

### Cron Jobs

```yaml
# In render.yaml
services:
  # Scheduled task
  - type: cron
    name: threat-intel-cron
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/collect_threat_data.py
    schedule: "0 */6 * * *"  # Every 6 hours
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: threat-intel-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: threat-intel-cache
          property: connectionString
```

### Celery Configuration

Create `app/celery.py`:

```python
from celery import Celery
import os

# Configure Celery
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
    task_routes={
        'app.tasks.threat_analysis': {'queue': 'threats'},
        'app.tasks.data_collection': {'queue': 'collection'},
        'app.tasks.report_generation': {'queue': 'reports'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

if __name__ == '__main__':
    celery_app.start()
```

## Backup & Recovery

### Automated Backups

Render provides automatic backups for managed databases:

```bash
# Enable in Render dashboard:
# Database > Settings > Backups > Auto-backup enabled

# Backup schedule:
# Starter plan: Daily backups, 7-day retention
# Standard plan: 4-hour backups, 30-day retention
```

### Manual Backup

```bash
# Create backup script
#!/bin/bash
# backup.sh

BACKUP_DIR="/tmp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/threatintel_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump $DATABASE_URL > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Upload to cloud storage (example with AWS S3)
if command -v aws &> /dev/null; then
    aws s3 cp $BACKUP_FILE.gz s3://your-backup-bucket/threatintel/
    echo "Backup uploaded to S3"
fi

# Clean up local backup
rm $BACKUP_FILE.gz

echo "Backup completed: $BACKUP_FILE.gz"
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster_recovery.sh

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./disaster_recovery.sh <backup_file>"
    exit 1
fi

echo "Starting disaster recovery from: $BACKUP_FILE"

# Stop all services
echo "Stopping services..."
# Services will be stopped via Render dashboard

# Restore database
echo "Restoring database..."
gunzip -c $BACKUP_FILE | psql $DATABASE_URL

# Verify restoration
echo "Verifying restoration..."
psql $DATABASE_URL -c "SELECT COUNT(*) FROM threats;"

# Start services
echo "Starting services..."
# Services will be started via Render dashboard

echo "Disaster recovery completed"
```

### Backup Verification

```python
# Add to your health check
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
        # Check backup files in cloud storage
        # This is a placeholder - implement based on your backup storage
        backup_status["status"] = "healthy"
    except Exception as e:
        backup_status["status"] = f"error: {str(e)}"
    
    return backup_status
```

## Troubleshooting

### Common Issues

#### 1. Build Failures

```bash
# Check build logs in Render dashboard

# Common issues:
# - Python version not specified
# - Missing dependencies in requirements.txt
# - Build timeout (max 15 minutes)

# Solutions:
# Add to requirements.txt:
# psycopg2-binary  # Not psycopg2 on Render

# Specify Python version in runtime.txt:
echo "3.11.7" > runtime.txt
```

#### 2. Database Connection Issues

```python
# Test database connection
import os
import psycopg2

def test_db_connection():
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print("ERROR: DATABASE_URL not set")
            return False
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"Database connected: {version}")
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()
```

#### 3. Environment Variable Issues

```python
# Add validation
def validate_environment():
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

# Run at startup
validate_environment()
```

#### 4. Worker Not Starting

```bash
# Check worker logs in Render dashboard

# Common issues:
# - Celery broker URL incorrect
# - Task import errors
# - Memory issues

# Solutions:
# 1. Verify REDIS_URL is set correctly
# 2. Check task module imports
# 3. Increase worker plan for memory-intensive tasks
```

#### 5. SSL Certificate Issues

```bash
# Check SSL status in Render dashboard
# Domain should show "Active" with green checkmark

# If SSL is not working:
# 1. Verify DNS points to Render
# 2. Wait 5-10 minutes for propagation
# 3. Check Render dashboard for status

# Test SSL
curl -I https://your-service.onrender.com
# Should return: HTTP/2 200
```

### Performance Issues

#### High Response Times

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
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            "Slow request detected",
            url=str(request.url),
            method=request.method,
            process_time=process_time
        )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

#### Memory Issues

```python
# Monitor memory usage
import psutil
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def memory_monitor(request: Request, call_next):
    memory = psutil.virtual_memory()
    
    if memory.percent > 80:
        logger.warning(
            "High memory usage",
            percent=memory.percent,
            available=memory.available
        )
    
    response = await call_next(request)
    return response
```

## Cost Optimization

### Monitor Costs

```bash
# Estimated monthly costs for Threat Intelligence Platform:
# Web Service (Starter): $7/month
# Worker Service (Starter): $7/month
# Beat Service (Starter): $7/month
# PostgreSQL (Starter): $9/month
# Redis (Starter): $9/month
# Bandwidth: $5-15/month
# Total: $44-54/month

# Use Standard plans for production:
# Web Service (Standard): $25/month
# Worker Service (Standard): $25/month
# PostgreSQL (Standard): $29/month
# Redis (Standard): $29/month
# Total: $108/month
```

### Optimization Strategies

1. **Use Starter Plans for Development**:
   ```yaml
   plan: starter  # Development
   # plan: standard  # Production
   ```

2. **Implement Caching**:
   ```python
   # Cache expensive operations
   @cache.cached(timeout=300)
   async def expensive_operation():
       # Your expensive code here
       pass
   ```

3. **Database Optimization**:
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_threats_timestamp ON threats(timestamp);
   CREATE INDEX idx_threats_ioc_hash ON threats(ioc_hash);
   
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM threats WHERE timestamp > NOW() - INTERVAL '1 day';
   ```

4. **Use Connection Pooling**:
   ```python
   # Optimize database connections
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool
   
   engine = create_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20,
       pool_recycle=3600,
       pool_pre_ping=True
   )
   ```

### Cost Monitoring Script

```bash
#!/bin/bash
# monitor_render_costs.sh

echo "=== Render.com Cost Analysis ==="
echo "Date: $(date)"
echo ""

# Render pricing (as of 2025)
echo "Current Configuration Costs:"
echo "- Web Service (Starter): $7/month"
echo "- Worker Service (Starter): $7/month"
echo "- Beat Service (Starter): $7/month"
echo "- PostgreSQL DB (Starter): $9/month"
echo "- Redis Cache (Starter): $9/month"
echo "- Estimated Bandwidth: $10/month"
echo "-----------------------------------"
echo "- Total (Starter): $49/month"
echo "- Total (Standard): $108/month"
echo ""

echo "Cost Optimization Recommendations:"
echo "1. Use Starter plans for development/testing"
echo "2. Implement Redis caching to reduce DB queries"
echo "3. Optimize database queries with indexes"
echo "4. Use connection pooling"
echo "5. Monitor bandwidth usage"
echo "6. Consider Standard plans for production"
echo ""

# Check service status
echo "Service Status:"
# Add commands to check service health here
```

## Conclusion

Render.com provides an excellent Heroku-like experience for deploying the Threat Intelligence Platform:

✅ **Familiar deployment model** - Easy migration from Heroku  
✅ **Comprehensive platform** - Web services, workers, cron jobs, databases  
✅ **Cost-effective** - $49/month for full application  
✅ **Good performance** - 99.95% uptime SLA  
✅ **Built-in scaling** - Automatic horizontal scaling  

### Next Steps
1. Follow this guide to deploy your application
2. Configure monitoring and alerting
3. Set up automated backups
4. Implement cost optimization strategies
5. Test disaster recovery procedures

### Additional Resources
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Best Practices](https://render.com/docs/deploy)

---

**Deployment Time**: ~45 minutes  
**Difficulty Level**: Beginner  
**Monthly Cost**: $49 (Starter) / $108 (Standard)  
**Last Updated**: October 30, 2025
