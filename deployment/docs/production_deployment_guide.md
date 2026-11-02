# Production Deployment Guide
## Threat Intelligence Platform

**Version:** 1.0.0  
**Last Updated:** 2025-10-30  
**Classification:** CONFIDENTIAL

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Production Deployment Steps](#production-deployment-steps)
3. [Cloud Provider Deployments](#cloud-provider-deployments)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Performance Tuning](#performance-tuning)
6. [Security Hardening](#security-hardening)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Backup Configuration](#backup-configuration)
9. [Maintenance Procedures](#maintenance-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Infrastructure Requirements

#### Minimum Hardware Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU Cores** | 8 | 16 | 32+ |
| **Memory** | 16GB | 32GB | 64GB+ |
| **Storage** | 500GB SSD | 1TB SSD | 2TB+ NVMe |
| **Network** | 1Gbps | 10Gbps | 10Gbps+ |
| **IOPS** | 3,000 | 10,000 | 20,000+ |

#### Network Requirements

```bash
# Required ports
TCP 22    - SSH access
TCP 80    - HTTP traffic
TCP 443   - HTTPS traffic
TCP 5432  - PostgreSQL
TCP 27017 - MongoDB
TCP 6379  - Redis
TCP 8000  - FastAPI
TCP 9090  - Prometheus
TCP 3000  - Grafana
TCP 5601  - Kibana
TCP 9200  - Elasticsearch
```

### Security Prerequisites

#### SSL/TLS Certificates
- [ ] Obtain SSL certificate for production domain
- [ ] Configure certificate chain
- [ ] Setup automatic renewal
- [ ] Test SSL configuration

#### Secrets Management
```bash
# Required secrets (generate with proper entropy)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 48)
JWT_SECRET=$(openssl rand -base64 48)
GRAFANA_PASSWORD=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Store in secure location
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> /tmp/secrets.env
echo "REDIS_PASSWORD=$REDIS_PASSWORD" >> /tmp/secrets.env
echo "SECRET_KEY=$SECRET_KEY" >> /tmp/secrets.env
echo "JWT_SECRET=$JWT_SECRET" >> /tmp/secrets.env
echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> /tmp/secrets.env
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> /tmp/secrets.env

# Secure storage
chmod 600 /tmp/secrets.env
```

#### Access Control
- [ ] Create dedicated deployment user
- [ ] Configure SSH key authentication
- [ ] Setup sudo privileges
- [ ] Configure firewall rules
- [ ] Enable audit logging

### Database Preparation

#### PostgreSQL + TimescaleDB Setup

```sql
-- Create database and user
CREATE DATABASE threatintel;
CREATE USER threatintel_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE threatintel TO threatintel_user;

-- Connect to database
\c threatintel

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create hypertables for time-series data
SELECT create_hypertable('threat_events', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('security_logs', 'timestamp', if_not_exists => TRUE);
SELECT create_hypertable('threat_indicators', 'created_at', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX CONCURRENTLY idx_threat_events_ip ON threat_events(ip_address);
CREATE INDEX CONCURRENTLY idx_threat_events_timestamp ON threat_events(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_threat_events_threat_type ON threat_events(threat_type);
CREATE INDEX CONCURRENTLY idx_security_logs_level ON security_logs(log_level);
CREATE INDEX CONCURRENTLY idx_security_logs_timestamp ON security_logs(timestamp DESC);

-- Configure connection limits
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET default_statistics_target = '100';
ALTER SYSTEM SET random_page_cost = '1.1';
ALTER SYSTEM SET effective_io_concurrency = '200';

SELECT pg_reload_conf();
```

#### MongoDB Setup

```javascript
// Switch to threatintel_logs database
use threatintel_logs

// Create collections with validation
db.createCollection("security_events", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "event_type", "source"],
      properties: {
        timestamp: {
          bsonType: "date",
          description: "Event timestamp"
        },
        event_type: {
          bsonType: "string",
          enum: ["login", "access", "data_export", "system", "security"],
          description: "Type of security event"
        },
        source: {
          bsonType: "string",
          description: "Source of the event"
        },
        severity: {
          bsonType: "string",
          enum: ["low", "medium", "high", "critical"],
          description: "Event severity level"
        },
        details: {
          bsonType: "object",
          description: "Additional event details"
        }
      }
    }
  }
});

// Create indexes for performance
db.security_events.createIndex({ "timestamp": 1 });
db.security_events.createIndex({ "event_type": 1, "timestamp": -1 });
db.security_events.createIndex({ "severity": 1, "timestamp": -1 });
db.security_events.createIndex({ "source": 1 });

// Enable TTL for automatic document expiration (7 years retention)
db.security_events.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 220752000 });

// Create audit log collection
db.createCollection("audit_logs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "action", "user"],
      properties: {
        timestamp: { bsonType: "date" },
        action: { bsonType: "string" },
        user: { bsonType: "string" },
        resource: { bsonType: "string" },
        result: { bsonType: "string", enum: ["success", "failure"] },
        details: { bsonType: "object" }
      }
    }
  }
});

db.audit_logs.createIndex({ "timestamp": 1 });
db.audit_logs.createIndex({ "user": 1, "timestamp": -1 });
```

---

## Production Deployment Steps

### Step 1: System Preparation

```bash
#!/bin/bash
# prepare_production_system.sh

set -euo pipefail

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    curl \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    software-properties-common \
    apt-transport-https \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    git \
    jq \
    htop \
    iotop \
    netstat-nat \
    tcpdump \
    nmap

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Create application directories
sudo mkdir -p /opt/threatintel
sudo mkdir -p /opt/data/{postgres_timescaledb,mongodb,redis}
sudo mkdir -p /opt/backups
sudo mkdir -p /var/log/threatintel
sudo mkdir -p /etc/threatintel

# Set permissions
sudo chown -R $USER:$USER /opt/threatintel
sudo chown -R $USER:$USER /opt/backups
sudo chown -R $USER:$USER /var/log/threatintel

# Configure firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Configure log rotation
sudo tee /etc/logrotate.d/threatintel > /dev/null << 'EOF'
/var/log/threatintel/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /opt/threatintel/docker-compose.yml restart nginx
    endscript
}
EOF

echo "System preparation completed"
```

### Step 2: Application Deployment

```bash
#!/bin/bash
# deploy_production.sh

set -euo pipefail

APP_DIR="/opt/threatintel"
BACKUP_DIR="/opt/backups"
LOG_FILE="/var/log/threatintel/deployment.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Clone repository
log "Cloning application repository..."
cd "$APP_DIR"
git clone https://github.com/your-org/threat-intel-platform.git . || error_exit "Failed to clone repository"

# Checkout production branch
git checkout production || error_exit "Failed to checkout production branch"

# Copy deployment configuration
cp deployment/docker/docker-compose.yml .
cp deployment/docker/.env.template .env

# Generate secure secrets
log "Generating secure secrets..."
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -base64 48)
JWT_SECRET=$(openssl rand -base64 48)
GRAFANA_PASSWORD=$(openssl rand -base64 32)
ENCRYPTION_KEY=$(openssl rand -base64 32)

# Update environment file
cat > .env << EOF
ENVIRONMENT=production
DEBUG=false

# Database Configuration
POSTGRES_DB=threatintel
POSTGRES_USER=threatintel_user
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_HOST=postgres-timescaledb
POSTGRES_PORT=5432

MONGO_INITDB_DATABASE=threatintel_logs
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=$POSTGRES_PASSWORD

REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_HOST=redis
REDIS_PORT=6379

# Security
SECRET_KEY=$SECRET_KEY
JWT_SECRET=$JWT_SECRET

# Monitoring
GRAFANA_ADMIN_PASSWORD=$GRAFANA_PASSWORD

# Backup Configuration
BACKUP_RETENTION_DAYS=30
S3_BACKUP_BUCKET=threatintel-backups-prod
AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
AWS_REGION=us-west-2

# Encryption
BACKUP_ENCRYPTION_KEY=$ENCRYPTION_KEY
EOF

# Secure environment file
chmod 600 .env

# Build application images
log "Building application images..."
docker-compose build --no-cache

# Create initial database backups directory
mkdir -p "$BACKUP_DIR"/{postgres,mongodb,redis}

# Start infrastructure services first
log "Starting infrastructure services..."
docker-compose up -d postgres-timescaledb mongodb redis

# Wait for databases to be ready
log "Waiting for databases to be ready..."
timeout 300 bash -c 'until docker-compose exec postgres-timescaledb pg_isready; do sleep 5; done'
timeout 300 bash -c 'until docker-compose exec mongodb mongosh --eval "db.adminCommand(\"ping\")" > /dev/null; do sleep 5; done'
timeout 300 bash -c 'until docker-compose exec redis redis-cli ping | grep -q PONG; do sleep 5; done'

# Initialize database schema
log "Initializing database schema..."
docker-compose run --rm fastapi-app python -c "
from database import engine
from models import Base
Base.metadata.create_all(bind=engine)
print('Database schema initialized')
"

# Start application services
log "Starting application services..."
docker-compose up -d fastapi-app celery-worker celery-beat

# Start load balancer
log "Starting load balancer..."
docker-compose up -d nginx

# Start monitoring stack
log "Starting monitoring stack..."
docker-compose up -d prometheus grafana alertmanager elasticsearch kibana logstash victoria-metrics

# Verify all services
log "Verifying services..."
sleep 30
docker-compose ps

echo "Deployment completed successfully!"
```

### Step 3: SSL/TLS Configuration

```bash
#!/bin/bash
# setup_ssl.sh

set -euo pipefail

DOMAIN="${1:-yourdomain.com}"
EMAIL="${2:-admin@yourdomain.com}"
SSL_DIR="/etc/ssl/threatintel"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Install Certbot
sudo apt-get install -y certbot

# Create SSL directory
sudo mkdir -p "$SSL_DIR"

# Generate strong Diffie-Hellman parameters
sudo openssl dhparam -out "$SSL_DIR/dhparam.pem" 2048

# Obtain SSL certificate
sudo certbot certonly \
    --standalone \
    --agree-tos \
    --email "$EMAIL" \
    --domains "$DOMAIN,www.$DOMAIN,api.$DOMAIN,monitoring.$DOMAIN"

# Setup automatic renewal
sudo tee /etc/cron.d/certbot-renew > /dev/null << EOF
0 12 * * * root certbot renew --quiet --deploy-hook "docker-compose -f /opt/threatintel/docker-compose.yml restart nginx"
EOF

# Copy certificates to application directory
sudo cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem "$SSL_DIR/"
sudo cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem "$SSL_DIR/"
sudo chown $USER:$USER "$SSL_DIR"/*.pem
sudo chmod 600 "$SSL_DIR"/*.pem

# Update nginx configuration
cat > /tmp/nginx_ssl.conf << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/ssl/threatintel/fullchain.pem;
    ssl_certificate_key /etc/ssl/threatintel/privkey.pem;
    ssl_dhparam /etc/ssl/threatintel/dhparam.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";

    location / {
        proxy_pass http://fastapi-app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://fastapi-app:8000/health;
        access_log off;
    }
}
EOF

sudo cp /tmp/nginx_ssl.conf /etc/nginx/sites-available/threatintel
sudo ln -sf /etc/nginx/sites-available/threatintel /etc/nginx/sites-enabled/threatintel

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
docker-compose restart nginx

log "SSL/TLS configuration completed"
```

---

## Cloud Provider Deployments

### AWS Production Deployment

```bash
#!/bin/bash
# deploy_aws_production.sh

set -euo pipefail

# Use ECS Fargate for production
aws ecs create-cluster \
  --cluster-name threatintel-production \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=80 capacityProvider=FARGATE_SPOT,weight=20

# Create task definitions
aws ecs register-task-definition \
  --cli-input-json file://aws/task-definition-production.json

# Create services
aws ecs create-service \
  --cluster threatintel-production \
  --service-name threatintel-api-service \
  --task-definition threatintel-api:1 \
  --desired-count 6 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[subnet-12345678,subnet-87654321],
    securityGroups=[sg-12345678],
    assignPublicIp=DISABLED
  }" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/threatintel-api/1234567890123456,containerName=fastapi,containerPort=8000 \
  --service-connect-configuration namespace=threatintel-prod

# Enable auto-scaling
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/threatintel-production/threatintel-api-service \
  --policy-name threatintel-api-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }'

echo "AWS production deployment completed"
```

### GCP Production Deployment

```bash
#!/bin/bash
# deploy_gcp_production.sh

set -euo pipefail

# Create GKE cluster
gcloud container clusters create threatintel-production \
  --zone=us-west1-a \
  --num-nodes=6 \
  --enable-autoscaling \
  --min-nodes=3 \
  --max-nodes=20 \
  --machine-type=n1-standard-4 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-network-policy \
  --addons=HorizontalPodAutoscaling,NetworkPolicy \
  --enable-stackdriver-kubernetes

# Get cluster credentials
gcloud container clusters get-credentials threatintel-production \
  --zone=us-west1-a

# Deploy application with Helm
helm upgrade --install threatintel-platform \
  ../kubernetes/helm/threatintel-platform \
  --namespace threatintel-prod \
  --create-namespace \
  --values values-production.yaml \
  --set replicaCount=6 \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=3 \
  --set autoscaling.maxReplicas=20 \
  --set database.host=postgresql.threatintel-prod.svc.cluster.local \
  --set redis.host=redis-master.threatintel-prod.svc.cluster.local

echo "GCP production deployment completed"
```

### Azure Production Deployment

```bash
#!/bin/bash
# deploy_azure_production.sh

set -euo pipefail

# Create AKS cluster
az aks create \
  --resource-group threatintel-prod-rg \
  --name threatintel-aks-prod \
  --node-count 6 \
  --enable-cluster-autoscaler \
  --min-count 3 \
  --max-count 20 \
  --node-vm-size Standard_D4s_v3 \
  --load-balancer-sku standard \
  --enable-managed-identity \
  --enable-addons monitoring,azure-policy \
  --network-plugin azure \
  --vnet-subnet-id /subscriptions/xxx/resourceGroups/threatintel-prod-rg/providers/Microsoft.Network/virtualNetworks/threatintel-vnet/subnets/aks-subnet

# Get credentials
az aks get-credentials \
  --resource-group threatintel-prod-rg \
  --name threatintel-aks-prod

# Deploy with Helm
helm upgrade --install threatintel-platform \
  ../kubernetes/helm/threatintel-platform \
  --namespace threatintel-prod \
  --create-namespace \
  --values values-production.yaml \
  --set replicaCount=6 \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=3 \
  --set autoscaling.maxReplicas=20

echo "Azure production deployment completed"
```

---

## Post-Deployment Verification

### Comprehensive Health Check

```bash
#!/bin/bash
# comprehensive_health_check.sh

set -euo pipefail

API_ENDPOINT="${API_ENDPOINT:-https://yourdomain.com}"
LOG_FILE="/var/log/threatintel/health_check.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_service_status() {
    log "Checking service status..."
    
    # Check Docker services
    docker-compose ps | tee -a "$LOG_FILE"
    
    # Check port accessibility
    for port in 80 443 8000 5432 27017 6379 9090 3000 5601; do
        if nc -z localhost "$port"; then
            log "Port $port: OPEN"
        else
            log "Port $port: CLOSED ❌"
            return 1
        fi
    done
}

check_database_connectivity() {
    log "Checking database connectivity..."
    
    # PostgreSQL
    if docker-compose exec -T postgres-timescaledb pg_isready; then
        log "PostgreSQL: HEALTHY"
    else
        log "PostgreSQL: UNHEALTHY ❌"
        return 1
    fi
    
    # MongoDB
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        log "MongoDB: HEALTHY"
    else
        log "MongoDB: UNHEALTHY ❌"
        return 1
    fi
    
    # Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        log "Redis: HEALTHY"
    else
        log "Redis: UNHEALTHY ❌"
        return 1
    fi
}

check_application_health() {
    log "Checking application health..."
    
    # FastAPI health endpoint
    if curl -sf "$API_ENDPOINT/health" > /dev/null; then
        log "FastAPI: HEALTHY"
    else
        log "FastAPI: UNHEALTHY ❌"
        return 1
    fi
    
    # Check API response time
    response_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_ENDPOINT/health")
    if (( $(echo "$response_time < 1.0" | bc -l) )); then
        log "API Response Time: ${response_time}s (GOOD)"
    else
        log "API Response Time: ${response_time}s (SLOW) ⚠️"
    fi
}

check_monitoring_stack() {
    log "Checking monitoring stack..."
    
    # Prometheus
    if curl -sf "http://localhost:9090/-/healthy" > /dev/null; then
        log "Prometheus: HEALTHY"
    else
        log "Prometheus: UNHEALTHY ❌"
        return 1
    fi
    
    # Grafana
    if curl -sf "http://localhost:3000/api/health" > /dev/null; then
        log "Grafana: HEALTHY"
    else
        log "Grafana: UNHEALTHY ❌"
        return 1
    fi
    
    # Elasticsearch
    if curl -sf "http://localhost:9200/_cluster/health" > /dev/null; then
        log "Elasticsearch: HEALTHY"
    else
        log "Elasticsearch: UNHEALTHY ❌"
        return 1
    fi
    
    # Kibana
    if curl -sf "http://localhost:5601/api/status" > /dev/null; then
        log "Kibana: HEALTHY"
    else
        log "Kibana: UNHEALTHY ❌"
        return 1
    fi
}

check_ssl_certificate() {
    log "Checking SSL certificate..."
    
    ssl_info=$(echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    
    if [ -n "$ssl_info" ]; then
        log "SSL Certificate: VALID"
        echo "$ssl_info" | tee -a "$LOG_FILE"
    else
        log "SSL Certificate: INVALID ❌"
        return 1
    fi
}

check_performance_metrics() {
    log "Checking performance metrics..."
    
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    log "CPU Usage: ${cpu_usage}%"
    
    # Memory usage
    memory_usage=$(free | grep Mem | awk '{printf("%.1f"), $3/$2 * 100.0}')
    log "Memory Usage: ${memory_usage}%"
    
    # Disk usage
    disk_usage=$(df -h / | awk 'NR==2{printf "%s", $5}')
    log "Disk Usage: ${disk_usage}"
    
    # Database connections
    db_connections=$(docker-compose exec -T postgres-timescaledb psql -U threatintel_user -d threatintel -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
    log "Database Connections: $db_connections"
}

check_backup_status() {
    log "Checking backup status..."
    
    # Check latest backup timestamps
    if [ -f /opt/backups/postgres/latest_backup.txt ]; then
        last_backup=$(cat /opt/backups/postgres/latest_backup.txt)
        log "Last PostgreSQL Backup: $last_backup"
    else
        log "No PostgreSQL backup found ❌"
    fi
    
    # Test backup restoration
    if ./backup/scripts/test_backup_restore.sh --quick-test; then
        log "Backup System: HEALTHY"
    else
        log "Backup System: ISSUES DETECTED ⚠️"
    fi
}

check_security_configuration() {
    log "Checking security configuration..."
    
    # Check SSL/TLS configuration
    if curl -sf "https://yourdomain.com" > /dev/null; then
        log "HTTPS: ENABLED"
    else
        log "HTTPS: DISABLED ❌"
    fi
    
    # Check security headers
    security_headers=$(curl -sI "https://yourdomain.com" | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options")
    if [ -n "$security_headers" ]; then
        log "Security Headers: PRESENT"
    else
        log "Security Headers: MISSING ⚠️"
    fi
    
    # Check failed login attempts
    failed_logins=$(docker-compose exec -T postgres-timescaledb psql -U threatintel_user -d threatintel -t -c "SELECT COUNT(*) FROM security_logs WHERE event_type='login' AND result='failure' AND timestamp > NOW() - INTERVAL '1 hour';" | xargs)
    log "Failed Logins (1h): $failed_logins"
}

# Main execution
main() {
    log "=== Comprehensive Health Check Started ==="
    
    check_service_status
    check_database_connectivity
    check_application_health
    check_monitoring_stack
    check_ssl_certificate
    check_performance_metrics
    check_backup_status
    check_security_configuration
    
    log "=== Health Check Completed ==="
    
    # Summary
    log "System is operational and ready for production traffic"
}

main "$@"
```

### Load Testing

```bash
#!/bin/bash
# load_test_production.sh

set -euo pipefail

API_ENDPOINT="${API_ENDPOINT:-https://yourdomain.com}"
DURATION="${DURATION:-300}"  # 5 minutes
CONCURRENT_USERS="${CONCURRENT_USERS:-100}"
RAMP_UP="${RAMP_UP:-60}"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Install Apache Bench
sudo apt-get install -y apache2-utils

# Install wrk
git clone https://github.com/wg/wrk.git
cd wrk && make -j4 && sudo cp wrk /usr/local/bin

# Run load test
log "Starting load test..."
log "Target: $API_ENDPOINT"
log "Duration: ${DURATION}s"
log "Concurrent Users: $CONCURRENT_USERS"
log "Ramp-up: ${RAMP_UP}s"

wrk -t4 -c$CONCURRENT_USERS -d${DURATION}s -R1000 \
    --timeout 10s \
    --script=load_test.lua \
    "$API_ENDPOINT/performance-test"

log "Load test completed"

# Monitor system during load test
log "Monitoring system metrics..."
docker stats --no-stream &
DOCKER_STATS_PID=$!

# Cleanup
cleanup() {
    log "Cleaning up..."
    kill $DOCKER_STATS_PID 2>/dev/null || true
    pkill wrk 2>/dev/null || true
    pkill ab 2>/dev/null || true
}
trap cleanup EXIT
```

---

## Performance Tuning

### Database Performance Optimization

```sql
-- PostgreSQL Performance Tuning
-- Connection Pooling
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '8GB';
ALTER SYSTEM SET effective_cache_size = '24GB';
ALTER SYSTEM SET maintenance_work_mem = '2GB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers = '64MB';
ALTER SYSTEM SET default_statistics_target = '200';
ALTER SYSTEM SET random_page_cost = '1.1';
ALTER SYSTEM SET effective_io_concurrency = '200';
ALTER SYSTEM SET work_mem = '256MB';
ALTER SYSTEM SET min_wal_size = '2GB';
ALTER SYSTEM SET max_wal_size = '8GB';

-- TimescaleDB Optimization
SELECT set_chunk_time_interval('threat_events', INTERVAL '1 day');
SELECT set_chunk_time_interval('security_logs', INTERVAL '1 day');
SELECT set_chunk_time_interval('threat_indicators', INTERVAL '1 day');

-- Enable compression
ALTER TABLE threat_events SET (timescaledb.compress, timescaledb.compress_segmentby = 'ip_address');
SELECT add_compression_policy('threat_events', INTERVAL '7 days');
SELECT add_compression_policy('security_logs', INTERVAL '7 days');

-- Create materialized views for performance
CREATE MATERIALIZED VIEW threat_summary_hourly AS
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    threat_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT ip_address) AS unique_ips
FROM threat_events
GROUP BY hour, threat_type
ORDER BY hour DESC;

CREATE UNIQUE INDEX ON threat_summary_hourly (hour, threat_type);
CREATE INDEX ON threat_summary_hourly (hour DESC);

-- Create continuous aggregate
CREATE MATERIALIZED VIEW threat_summary_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS day,
    threat_type,
    COUNT(*) AS event_count,
    COUNT(DISTINCT ip_address) AS unique_ips,
    AVG(severity_score) AS avg_severity
FROM threat_events
GROUP BY day, threat_type;

SELECT add_continuous_aggregate_policy('threat_summary_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT pg_reload_conf();
```

### Redis Performance Optimization

```conf
# Redis Configuration - /opt/threatintel/config/redis/redis.conf

# Memory Management
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes

# Performance
tcp-keepalive 300
timeout 300
tcp-backlog 511
databases 16

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log

# Slow Log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Client Output Buffer Limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command KEYS ""
rename-command CONFIG "CONFIG_a8b3c9d2e1"
```

### Application Performance Tuning

```python
# FastAPI Performance Configuration - /opt/threatintel/api/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uvicorn
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(
    title="Threat Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(
            f"Slow request: {request.method} {request.url.path} - {process_time:.3f}s"
        )
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        worker_class="uvicorn.workers.UvicornWorker",
        max_requests=1000,
        max_requests_jitter=100,
        keepalive_timeout=60,
        access_log=True
    )
```

---

## Security Hardening

### System Security Configuration

```bash
#!/bin/bash
# security_hardening.sh

set -euo pipefail

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Configure firewall (ufw)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Disable root SSH login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PermitRootLogin/PermitRootLogin/' /etc/ssh/sshd_config

# Disable password authentication
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config

# Enable key-based authentication
sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart ssh

# Install and configure fail2ban
sudo apt-get install -y fail2ban
sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Configure log rotation
sudo tee /etc/logrotate.d/threatintel > /dev/null << 'EOF'
/var/log/threatintel/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /opt/threatintel/docker-compose.yml kill -s USR1 nginx
    endscript
}

/var/log/threatintel/access.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /opt/threatintel/docker-compose.yml kill -s USR1 nginx
    endscript
}
EOF

# Configure automatic security updates
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Setup AIDE (Advanced Intrusion Detection Environment)
sudo apt-get install -y aide
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Configure file integrity monitoring
sudo tee /etc/cron.daily/aide-check > /dev/null << 'EOF'
#!/bin/bash
/usr/bin/aide --check | mail -s "AIDE integrity check" root@localhost
EOF
sudo chmod +x /etc/cron.daily/aide-check

# Setup intrusion detection (optional - OSSEC)
# wget -q -O - https://updates.atomicorp.com/keys/atomicsign.key | sudo apt-key add -
# sudo sh -c 'echo deb https://updates.atomicorp.com/channels/atomic/ubuntu $(lsb_release -sc) main >> /etc/apt/sources.list.d/atomic.list'
# sudo apt-get update && sudo apt-get install -y ossec-hids

# Configure network security
sudo tee /etc/sysctl.d/99-security.conf > /dev/null << 'EOF'
# Disable IP forwarding
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Disable redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Disable secure redirects
net.ipv4.conf.all.accept_secure_redirects = 0

# Ignore ping requests
net.ipv4.icmp_echo_ignore_all = 1

# Enable reverse path filtering
net.ipv4.conf.all.rp_filter = 1

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0

# Disable IPv6 if not needed
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF

sudo sysctl -p /etc/sysctl.d/99-security.conf

echo "Security hardening completed"
```

### Application Security

```python
# Security Middleware - /opt/threatintel/api/app/middleware/security.py

import os
import hmac
import hashlib
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 3600):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = int(time.time())
        
        # Clean old entries
        self.requests = {k: v for k, v in self.requests.items() 
                        if current_time - v['first_request'] < self.period}
        
        # Check rate limit
        if client_ip in self.requests:
            if self.requests[client_ip]['count'] >= self.calls:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self.requests[client_ip]['count'] += 1
        else:
            self.requests[client_ip] = {
                'count': 1,
                'first_request': current_time
            }
        
        response = await call_next(request)
        return response

class HMACMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or os.getenv("HMAC_SECRET_KEY", "")
    
    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE"]:
            signature = request.headers.get("X-Signature")
            if signature:
                body = await request.body()
                expected_signature = hmac.new(
                    self.secret_key.encode(),
                    body,
                    hashlib.sha256
                ).hexdigest()
                
                if not hmac.compare_digest(signature, f"sha256={expected_signature}"):
                    raise HTTPException(status_code=401, detail="Invalid signature")
        
        response = await call_next(request)
        return response
```

---

## Monitoring and Alerting

### Prometheus Configuration

```yaml
# /opt/threatintel/config/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

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

  - job_name: 'fastapi'
    static_configs:
      - targets: ['fastapi-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'mongodb-exporter'
    static_configs:
      - targets: ['mongodb-exporter:9216']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 'node-exporter:9100'
```

### Alert Rules

```yaml
# /opt/threatintel/config/prometheus/rules/alert_rules.yml
groups:
  - name: threatintel.rules
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} on instance {{ $labels.instance }} has been down for more than 1 minute."

      - alert: HighCPUUsage
        expr: 100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for more than 5 minutes on {{ $labels.instance }}."

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 80% for more than 5 minutes on {{ $labels.instance }}."

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} * 100) < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space is low on {{ $labels.instance }}"
          description: "Disk space is below 10% on {{ $labels.instance }}."

      - alert: DatabaseDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"
          description: "PostgreSQL database has been down for more than 1 minute."

      - alert: HighDatabaseConnections
        expr: pg_stat_database_numbackends / pg_settings_max_connections * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High database connections"
          description: "Database connections are above 80% of maximum for more than 5 minutes."

      - alert: RedisDown
        expr: redis_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for more than 1 minute."

      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "95th percentile response time is above 1 second for more than 5 minutes."

      - alert: ManyFailedLogins
        expr: increase(failed_login_attempts_total[5m]) > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Many failed login attempts"
          description: "More than 50 failed login attempts in the last 5 minutes."

      - alert: SecurityEvent
        expr: increase(security_events_total{severity="critical"}[1m]) > 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Critical security event detected"
          description: "A critical security event has been detected."
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "ThreatIntel Platform - Production Overview",
    "tags": ["threatintel", "production"],
    "timezone": "UTC",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "System Overview",
        "type": "stat",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "up",
            "legendFormat": "Services Up"
          },
          {
            "expr": "avg(up) * 100",
            "legendFormat": "Availability %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 90},
                {"color": "green", "value": 95}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "API Response Time",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "99th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Request Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "id": 4,
        "title": "Database Connections",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "{{datname}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "CPU Usage",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 6,
        "title": "Memory Usage",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "id": 7,
        "title": "Disk I/O",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
        "targets": [
          {
            "expr": "rate(node_disk_io_time_seconds_total[5m]) * 100",
            "legendFormat": "{{device}}"
          }
        ]
      },
      {
        "id": 8,
        "title": "Security Events",
        "type": "table",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 32},
        "targets": [
          {
            "expr": "security_events_total",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {"Time": true},
              "indexByName": {},
              "renameByName": {
                "event_type": "Event Type",
                "severity": "Severity",
                "Value": "Count"
              }
            }
          }
        ]
      }
    ]
  }
}
```

---

## Conclusion

This production deployment guide provides comprehensive procedures for deploying the Threat Intelligence Platform in a production environment. Key highlights include:

- **Comprehensive pre-deployment checklist** to ensure all prerequisites are met
- **Step-by-step deployment procedures** for various environments
- **Cloud provider specific deployments** for AWS, GCP, and Azure
- **Security hardening** measures to protect the production environment
- **Performance tuning** optimizations for optimal system performance
- **Monitoring and alerting** configuration for proactive system management
- **Backup and disaster recovery** procedures for business continuity

Follow this guide carefully to ensure a successful production deployment with optimal security, performance, and reliability.

---

**Document Owner:** Infrastructure Team  
**Approved By:** CTO  
**Review Date:** Quarterly  
**Next Review:** 2026-01-30
