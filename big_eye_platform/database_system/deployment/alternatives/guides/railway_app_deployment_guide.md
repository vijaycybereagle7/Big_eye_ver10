# Railway.app Deployment Guide for Threat Intelligence Platform

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Platform Overview](#platform-overview)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Custom Domains & SSL](#custom-domains--ssl)
7. [Monitoring & Logs](#monitoring--logs)
8. [Scaling & Performance](#scaling--performance)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)
11. [Cost Optimization](#cost-optimization)

## Prerequisites

### Required Tools
- Git
- Railway CLI (`npm install -g @railway/cli`)
- Docker (for local testing)
- GitHub/GitLab account with your repository

### System Requirements
- Minimum 1 vCPU, 1GB RAM per service
- 10GB storage minimum
- Internet connectivity

### Pre-deployment Checklist
- [ ] Threat Intelligence Platform source code ready
- [ ] Docker configuration files prepared
- [ ] Environment variables documented
- [ ] Domain name configured (optional)
- [ ] SSL certificate ready (if custom domain)

## Platform Overview

### What is Railway.app?
Railway is a modern deployment platform that provides:
- **Native PostgreSQL, MySQL, and Redis databases**
- **Automatic HTTPS and custom domains**
- **Zero-config deployments**
- **Built-in monitoring and logs**
- **Usage-based pricing**

### Pricing Structure
- **Free Tier**: $5 monthly credit (perfect for testing)
- **Starter Plan**: $5/month base + usage
- **Pro Plan**: $20/month base + usage (team features)
- **Usage**: CPU, RAM, storage, bandwidth

### Why Railway.app for Threat Intelligence Platform?
✅ **Built-in database support** - PostgreSQL with TimescaleDB available  
✅ **Background job support** - Perfect for Celery workers  
✅ **Excellent performance** - ~100ms response times  
✅ **Developer-friendly** - Git-based deployments  
✅ **Cost-effective** - ~$55/month for medium load  

## Step-by-Step Deployment

### Step 1: Install Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Verify installation
railway --version

# Login to Railway
railway login
```

### Step 2: Initialize Railway Project

```bash
# Navigate to your project directory
cd /path/to/threat-intelligence-platform

# Initialize Railway in your project
railway init

# This creates railway.json configuration
```

### Step 3: Create Railway Configuration

Create `railway.json` in your project root:

```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Configure Docker for Railway

Create/update `Dockerfile` in your project root:

```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 5: Create docker-compose.yml for Railway

Railway can deploy services from docker-compose:

```yaml
version: '3.8'

services:
  # Main FastAPI application
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL database
  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Celery worker
  worker:
    build: .
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis

  # Celery beat scheduler
  beat:
    build: .
    command: celery -A app.celery beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/docker/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/docker/ssl:/etc/ssl/certs
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

### Step 6: Deploy to Railway

```bash
# Add services to Railway
railway add

# Deploy the application
railway up

# Check deployment status
railway status

# View logs
railway logs
```

### Step 7: Verify Deployment

```bash
# Get your app URL
railway domain

# Test health endpoint
curl https://your-app.railway.app/health

# Expected response: {"status": "healthy"}
```

## Database Setup

### Option 1: Railway Native PostgreSQL (Recommended)

```bash
# Add PostgreSQL database
railway add postgresql

# Railway automatically provides DATABASE_URL
# Format: postgresql://user:password@host:port/database
```

### Option 2: Railway Native Redis

```bash
# Add Redis cache
railway add redis

# Railway automatically provides REDIS_URL
# Format: redis://user:password@host:port
```

### Option 3: External Database (Advanced)

For TimescaleDB specifically:

```bash
# Create custom service
railway add

# Select "Empty Service" and configure manually
```

### Database Migration

```bash
# Run database migrations
railway run python manage.py migrate

# Or using Railway CLI
railway python manage.py migrate

# Load initial data
railway python manage.py loaddata initial_data.json
```

### Database Backup Configuration

Railway provides automatic backups. To configure:

1. **Access Railway Dashboard**
   - Go to [railway.app](https://railway.app)
   - Navigate to your project

2. **Configure Database Backups**
   ```bash
   # Enable automatic backups in Railway dashboard
   # PostgreSQL: Settings > Backups > Enable Auto-backup
   # Redis: Settings > Persistence > Enable RDB + AOF
   ```

3. **Manual Backup**
   ```bash
   # Create backup
   railway run pg_dump -U $PGUSER -h $PGHOST -d $PGDATABASE > backup.sql

   # Restore backup
   railway run psql -U $PGUSER -h $PGHOST -d $PGDATABASE < backup.sql
   ```

## Environment Configuration

### Set Environment Variables

```bash
# Set individual variables
railway variables set SECRET_KEY=your-secret-key
railway variables set DEBUG=false
railway variables set LOG_LEVEL=INFO

# Or set from file
railway variables set --file .env.production
```

### Required Environment Variables

Create `.env.production`:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port
POSTGRES_DB=threatintel
POSTGRES_USER=railway
POSTGRES_PASSWORD=secure-password

# Security
SECRET_KEY=your-256-bit-secret-key
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_TIME=3600

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
API_TIMEOUT=30

# CORS Settings
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
METRICS_ENDPOINT=/metrics

# External APIs
VIRUSTOTAL_API_KEY=your-virustotal-key
ABUSEIPDB_API_KEY=your-abuseipdb-key

# Background Jobs
CELERY_BROKER_URL=redis://user:password@host:port
CELERY_RESULT_BACKEND=redis://user:password@host:port
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=['json']
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/app.log

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/certs/key.pem

# Timezone
TZ=UTC
```

### Apply Environment Variables

```bash
# Upload environment file
railway variables set --file .env.production

# Verify variables are set
railway variables

# Redeploy with new variables
railway deploy
```

## Custom Domains & SSL

### Add Custom Domain

```bash
# In Railway dashboard:
# 1. Go to your service
# 2. Settings > Domains
# 3. Add custom domain: api.yourdomain.com

# Or via CLI (if supported)
railway domain add api.yourdomain.com
```

### Configure DNS

Add CNAME record in your DNS provider:

```
Type: CNAME
Name: api
Value: your-app.railway.app
TTL: 300
```

### SSL Certificate

Railway automatically provisions Let's Encrypt SSL certificates:

```bash
# Verify SSL is working
curl -I https://api.yourdomain.com

# Expected: HTTP/2 200
# SSL certificate: Let's Encrypt
```

### Force HTTPS

Configure in your application:

```python
# In main.py or middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)
```

## Monitoring & Logs

### Access Logs

```bash
# Real-time logs
railway logs --follow

# Historical logs
railway logs --since 1h

# Specific service logs
railway logs --service web

# Save logs to file
railway logs > app-logs.txt
```

### Railway Dashboard Monitoring

1. **Access Dashboard**: [railway.app/dashboard](https://railway.app/dashboard)
2. **Monitor Metrics**:
   - CPU usage
   - Memory consumption
   - Network traffic
   - Response times
   - Error rates

### Set Up Alerts

```bash
# Install Railway CLI alerts (if available)
railway alerts create --threshold=80 --metric=cpu

# Or configure via dashboard
# Settings > Notifications > Email Alerts
```

### External Monitoring Integration

```python
# Add to your application
from prometheus_client import Counter, Histogram, generate_latest

# Custom metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    REQUEST_COUNT.inc()
    REQUEST_LATENCY.observe(process_time)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Scaling & Performance

### Horizontal Scaling

```bash
# Scale web service
railway scale --replicas 3 --service web

# Scale worker service
railway scale --replicas 2 --service worker

# View current scaling
railway status
```

### Vertical Scaling

```bash
# Upgrade service plan
railway plan upgrade --service web

# Or via dashboard:
# Settings > Resources > Plan
```

### Auto-scaling Configuration

Add to `railway.json`:

```json
{
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10,
    "autoscaling": {
      "enabled": true,
      "minReplicas": 1,
      "maxReplicas": 5,
      "targetCPUUtilizationPercentage": 70,
      "targetMemoryUtilizationPercentage": 80
    }
  }
}
```

### Performance Optimization

```python
# Optimize FastAPI for production
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(
    title="Threat Intelligence Platform",
    description="Cybersecurity threat intelligence analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware for performance
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optimize database connections
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine

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
# Install locust for load testing
pip install locust

# Create load test
cat > loadtest.py << 'EOF'
from locust import HttpUser, task, between

class ThreatIntelligenceUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
    
    @task(1)
    def search_threats(self):
        self.client.post("/api/v1/search", json={
            "query": "malware analysis",
            "limit": 10
        })

if __name__ == "__main__":
    import subprocess
    subprocess.run(["locust", "-f", "loadtest.py", "--host", "https://your-app.railway.app"])
EOF

# Run load test
python loadtest.py
```

## Backup & Recovery

### Automated Backups

Railway provides automatic backups:

```bash
# Enable backup in dashboard:
# Database > Settings > Backups > Auto-backup enabled

# PostgreSQL: Daily backups, 7-day retention
# Redis: Real-time persistence with RDB/AOF
```

### Manual Backup

```bash
# Create database backup
railway run pg_dump -U $PGUSER -h $PGHOST -d $PGDATABASE \
  --format=custom --compress=6 > backup_$(date +%Y%m%d).dump

# Create application backup
tar -czf app_backup_$(date +%Y%m%d).tar.gz \
  --exclude=node_modules --exclude=.git --exclude=__pycache__ .
```

### Backup Verification

```bash
# Test backup integrity
railway run pg_restore --list backup_$(date +%Y%m%d).dump

# Restore to test database
railway run createdb threatintel_test
railway run pg_restore -d threatintel_test backup_$(date +%Y%m%d).dump
```

### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster_recovery.sh

BACKUP_DATE=$1
if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: ./disaster_recovery.sh YYYYMMDD"
    exit 1
fi

echo "Starting disaster recovery from backup: $BACKUP_DATE"

# Stop services
railway stop --service web
railway stop --service worker
railway stop --service beat

# Restore database
railway run dropdb --if-exists threatintel
railway run createdb threatintel
railway run pg_restore -d threatintel backup_${BACKUP_DATE}.dump

# Start services
railway start --service web
railway start --service worker
railway start --service beat

# Verify recovery
railway run python manage.py check --deploy
echo "Disaster recovery completed"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Build Failures

```bash
# Check build logs
railway logs --type=build

# Common issues:
# - Missing dependencies
# - Incorrect Python version
# - Build timeout

# Solutions:
# Update requirements.txt
# Add python_version to runtime.txt
# Optimize build process
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
railway run python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    print('Database connection successful')
    conn.close()
except Exception as e:
    print(f'Database connection failed: {e}')
"

# Check database status
railway run pg_isready -U $PGUSER -h $PGHOST
```

#### 3. Memory Issues

```bash
# Check memory usage
railway metrics --service web

# Increase memory
railway plan upgrade --service web

# Optimize application memory
# - Use connection pooling
# - Implement caching
# - Monitor memory leaks
```

#### 4. SSL Certificate Issues

```bash
# Check SSL certificate
curl -v https://your-app.railway.app

# Force SSL certificate renewal
railway domain renew your-app.railway.app

# Check certificate expiry
openssl s_client -connect your-app.railway.app:443 -servername your-app.railway.app | openssl x509 -noout -dates
```

#### 5. Application Not Starting

```bash
# Check application logs
railway logs --service web --tail 100

# Test locally
docker-compose up --build

# Check health endpoint
curl http://localhost:8000/health

# Debug specific components
railway run python manage.py check
railway run python -c "from app.main import app; print('App loads successfully')"
```

### Performance Issues

#### High Response Times

```python
# Add performance monitoring
import time
import logging

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logging.info(f"Request {request.url.path} took {process_time:.4f}s")
    
    if process_time > 1.0:  # Log slow requests
        logging.warning(f"Slow request: {request.url.path} took {process_time:.4f}s")
    
    return response
```

#### Database Performance

```sql
-- Enable query logging
-- In Railway dashboard: Database > Settings > Query Logging

-- Check slow queries
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check database connections
SELECT count(*) FROM pg_stat_activity;
```

## Cost Optimization

### Monitor Costs

```bash
# View current usage
railway usage

# Set budget alerts
railway budget set --amount 100 --period monthly

# Check cost breakdown
railway costs --service web
```

### Optimization Strategies

1. **Use appropriate instance sizes**
   ```bash
   # Right-size your services
   railway plan downgrade --service worker  # If over-provisioned
   railway plan upgrade --service web       # If under-provisioned
   ```

2. **Implement caching**
   ```python
   # Add Redis caching
   from redis import Redis
   from functools import wraps
   
   redis_client = Redis.from_url(os.getenv('REDIS_URL'))
   
   def cache_result(expiration=300):
       def decorator(func):
           @wraps(func)
           async def wrapper(*args, **kwargs):
               cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
               
               cached = redis_client.get(cache_key)
               if cached:
                   return json.loads(cached)
               
               result = await func(*args, **kwargs)
               redis_client.setex(cache_key, expiration, json.dumps(result))
               return result
           return wrapper
       return decorator
   ```

3. **Database optimization**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX CONCURRENTLY idx_threats_timestamp ON threats(timestamp);
   CREATE INDEX CONCURRENTLY idx_threats_ioc_value ON threats(ioc_value);
   
   -- Optimize queries
   EXPLAIN ANALYZE SELECT * FROM threats WHERE timestamp > NOW() - INTERVAL '1 day';
   ```

4. **Use connection pooling**
   ```python
   # Optimize database connections
   engine = create_engine(
       DATABASE_URL,
       pool_size=10,          # Adjust based on load
       max_overflow=20,
       pool_recycle=3600,
       pool_pre_ping=True
   )
   ```

### Estimated Monthly Costs

| Resource | Configuration | Monthly Cost |
|----------|---------------|--------------|
| Web Service | 1 vCPU, 2GB RAM | $25 |
| PostgreSQL | 1GB storage, backup | $15 |
| Redis | 512MB memory | $5 |
| Worker Service | 0.5 vCPU, 1GB RAM | $12 |
| Bandwidth | 100GB transfer | $8 |
| **Total** | | **$65** |

### Cost Monitoring Script

```bash
#!/bin/bash
# monitor_costs.sh

echo "=== Railway.app Cost Report ==="
echo "Date: $(date)"
echo ""

# Get current usage
railway usage --json > usage.json

# Parse and display costs
python3 << 'EOF'
import json
import sys

try:
    with open('usage.json', 'r') as f:
        usage = json.load(f)
    
    print("Current Monthly Costs:")
    print(f"- Compute: ${usage.get('compute_cost', 0):.2f}")
    print(f"- Database: ${usage.get('database_cost', 0):.2f}")
    print(f"- Storage: ${usage.get('storage_cost', 0):.2f}")
    print(f"- Bandwidth: ${usage.get('bandwidth_cost', 0):.2f}")
    
    total = usage.get('total_cost', 0)
    print(f"- Total: ${total:.2f}")
    
    if total > 100:
        print("\n⚠️  Warning: Costs are high!")
        print("Consider optimization strategies:")
        print("- Scale down unused services")
        print("- Implement caching")
        print("- Optimize database queries")
        print("- Use connection pooling")
    
except Exception as e:
    print(f"Error parsing usage data: {e}")
    sys.exit(1)
EOF

# Clean up
rm -f usage.json
```

## Conclusion

Railway.app provides an excellent platform for deploying the Threat Intelligence Platform with:

✅ **Easy setup** - Git-based deployment with minimal configuration  
✅ **Built-in databases** - PostgreSQL and Redis included  
✅ **Cost-effective** - ~$65/month for full application  
✅ **Developer-friendly** - Excellent CLI and dashboard  
✅ **Production-ready** - SSL, monitoring, and scaling built-in  

### Next Steps
1. Follow this guide to deploy your application
2. Monitor costs and performance in the Railway dashboard
3. Implement the optimization strategies provided
4. Set up alerts for budget and performance monitoring
5. Review the disaster recovery plan

### Additional Resources
- [Railway Documentation](https://docs.railway.app)
- [Railway Community Discord](https://discord.gg/railway)
- [Best Practices Guide](https://docs.railway.app/reference/best-practices)

---

**Deployment Time**: ~30 minutes  
**Difficulty Level**: Beginner to Intermediate  
**Monthly Cost**: $65 (medium load)  
**Last Updated**: October 30, 2025
