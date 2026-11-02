# Installation Guide
## Cybersecurity Threat Intelligence Platform

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Docker Installation](#docker-installation)
5. [Kubernetes Installation](#kubernetes-installation)
6. [Manual Installation](#manual-installation)
7. [Database Setup](#database-setup)
8. [Configuration](#configuration)
9. [External API Setup](#external-api-setup)
10. [SSL/TLS Configuration](#ssltls-configuration)
11. [Monitoring Setup](#monitoring-setup)
12. [Verification](#verification)
13. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software

Before installation, ensure the following software is installed:

#### Essential Components
```bash
# Docker and Docker Compose
Docker >= 24.0.0
Docker Compose >= v2.20.0

# Kubernetes (for K8s deployment)
kubectl >= 1.27.0
helm >= 3.12.0

# System utilities
git >= 2.40.0
curl >= 7.68.0
jq >= 1.6 (JSON processor)
```

#### Optional Components
```bash
# For development
Python >= 3.11
Node.js >= 18.0
npm >= 9.0

# For monitoring
Prometheus >= 2.47.0
Grafana >= 10.2.0
Elasticsearch >= 8.10.0
```

### Operating System Support

#### Supported Platforms
- **Linux**: Ubuntu 20.04+ LTS, RHEL 8+, CentOS 8+, Amazon Linux 2
- **macOS**: macOS 12+ (Monterey) with Docker Desktop
- **Windows**: Windows 10/11 with WSL2 and Docker Desktop

#### Recommended Cloud Platforms
- **AWS**: EC2, EKS, RDS, ElastiCache, DocumentDB
- **Azure**: AKS, Azure Database for PostgreSQL, Azure Cache for Redis
- **GCP**: GKE, Cloud SQL, Memorystore, MongoDB Atlas

### Access Requirements

#### Network Access
- Internet connectivity for external API calls
- Access to package repositories (PyPI, npm, Docker Hub)
- DNS resolution for all service endpoints

#### External APIs
You'll need API keys for the following services:
- VirusTotal (https://www.virustotal.com)
- AbuseIPDB (https://www.abuseipdb.com)
- Shodan (https://account.shodan.io)
- GreyNoise (https://www.greynoise.io)
- OTX (https://otx.alienvault.com)
- SecurityTrails (https://securitytrails.com)

---

## 💻 System Requirements

### Minimum Requirements

#### Development Environment
```yaml
CPU: 4 cores
RAM: 8 GB
Storage: 50 GB SSD
Network: 1 Gbps
OS: Ubuntu 20.04+ / macOS 12+ / Windows 10+
```

#### Production Environment
```yaml
Application Servers (3x):
  CPU: 8 cores
  RAM: 16 GB
  Storage: 100 GB SSD
  Network: 10 Gbps

Database Server:
  CPU: 16 cores
  RAM: 64 GB
  Storage: 500 GB SSD (RAID 1)
  Network: 10 Gbps

Cache Server:
  CPU: 8 cores
  RAM: 32 GB
  Storage: 100 GB SSD
  Network: 10 Gbps
```

### Recommended Requirements

#### High-Performance Production
```yaml
Application Servers (5x):
  CPU: 16 cores
  RAM: 32 GB
  Storage: 200 GB NVMe SSD
  Network: 25 Gbps

Database Cluster:
  CPU: 32 cores
  RAM: 128 GB
  Storage: 1 TB NVMe SSD (RAID 10)
  Network: 25 Gbps

Redis Cluster:
  CPU: 16 cores
  RAM: 64 GB
  Storage: 200 GB NVMe SSD
  Network: 25 Gbps

Load Balancers (2x):
  CPU: 8 cores
  RAM: 16 GB
  Storage: 50 GB SSD
  Network: 25 Gbps
```

### Disk Space Planning

```bash
# Estimated disk usage per component

# Application data
PostgreSQL: 100 GB (grows with usage)
MongoDB: 200 GB (unstructured data)
Redis: 20 GB (cache data)
Logs: 50 GB (30-day retention)

# System and backups
OS: 20 GB
Backups: 500 GB
Temporary files: 30 GB
Docker images: 10 GB

# Total for production: ~930 GB
# Recommended: 2 TB for safety
```

---

## 🚀 Installation Methods

The platform can be installed using several methods:

### Method Comparison

| Method | Complexity | Scalability | Best For |
|--------|------------|-------------|----------|
| Docker Compose | Low | Medium | Development, Small Production |
| Kubernetes | High | High | Production, Enterprise |
| Manual | Medium | Low | Development, Testing |
| Cloud Marketplace | Medium | High | Quick Deployment |

### Method Selection Guide

#### Choose Docker Compose if:
- You need quick deployment
- Working on development/staging
- Have small to medium traffic (< 1K req/sec)
- Want simple management

#### Choose Kubernetes if:
- Running production workloads
- Need high availability and scalability
- Have complex infrastructure requirements
- Want enterprise features

#### Choose Manual Installation if:
- Need custom configuration
- Integrating with existing systems
- Running on restricted environments
- Learning the architecture

---

## 🐳 Docker Installation

### Quick Start with Docker Compose

#### 1. Clone the Repository
```bash
# Clone the repository
git clone https://github.com/your-org/cybersecurity-platform.git
cd cybersecurity-platform

# Verify directory structure
ls -la
# Should show: api/, monitoring/, security/, performance/, etc.
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

#### Sample .env Configuration
```bash
# Application Configuration
APP_NAME="Cybersecurity Threat Intelligence Platform"
APP_VERSION="1.0.0"
DEBUG=false
SECRET_KEY="your-super-secret-key-change-this-in-production"

# Database Configuration
POSTGRESQL_HOST=postgres
POSTGRESQL_PORT=5432
POSTGRESQL_DB=cybersec_db
POSTGRESQL_USER=cybersec_user
POSTGRESQL_PASSWORD=secure_password_change_me
POSTGRESQL_URL="postgresql://cybersec_user:secure_password_change_me@postgres:5432/cybersec_db"

MONGODB_HOST=mongodb
MONGODB_PORT=27017
MONGODB_DB=cybersec_db
MONGODB_USER=cybersec_user
MONGODB_PASSWORD=mongo_password_change_me
MONGODB_URL="mongodb://cybersec_user:mongo_password_change_me@mongodb:27017/cybersec_db?authSource=admin"

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password_change_me
REDIS_URL="redis://:redis_password_change_me@redis:6379/0"

# External API Keys (get these from respective services)
VIRUSTOTAL_API_KEY=your_virustotal_api_key
ABUSEIPDB_API_KEY=your_abuseipdb_api_key
SHODAN_API_KEY=your_shodan_api_key
GREYNOISE_API_KEY=your_greynoise_api_key
OTX_API_KEY=your_otx_api_key
SECURITYTRAILS_API_KEY=your_securitytrails_api_key

# Security Configuration
JWT_SECRET_KEY="jwt-secret-key-change-this"
ENCRYPTION_KEY="encryption-key-32-chars-long"

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT="100/minute"
RATE_LIMIT_ADMIN="1000/minute"
RATE_LIMIT_BULK="10/minute"

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300
CACHE_TTL_SHORT=60
CACHE_TTL_LONG=86400

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
ELK_ENABLED=true

# SSL/TLS (for production)
SSL_ENABLED=false
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

#### 3. Start the Platform
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f mongodb
docker-compose logs -f redis
```

#### 4. Verify Installation
```bash
# Health check
curl -f http://localhost:8000/health

# API documentation
curl -f http://localhost:8000/docs

# Grafana dashboard
open http://localhost:3000
# Username: admin, Password: admin123 (change on first login)
```

### Advanced Docker Configuration

#### Custom Docker Compose Files
```yaml
# docker-compose.override.yml (for development)
version: '3.8'
services:
  api:
    build: .
    volumes:
      - ./api:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    ports:
      - "8000:8000"

# docker-compose.prod.yml (for production)
version: '3.8'
services:
  api:
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

#### Production Docker Deployment
```bash
# Use production configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With SSL/TLS
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d

# With monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.monitoring.yml up -d
```

#### Scaling Services
```bash
# Scale API service
docker-compose up -d --scale api=3

# Scale with load balancer
docker-compose -f docker-compose.yml -f docker-compose.scaling.yml up -d
```

---

## ☸️ Kubernetes Installation

### Prerequisites for Kubernetes

#### Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/helm

# Install kustomize (optional)
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
```

#### Kubernetes Cluster Setup
```bash
# For local development with kind
kind create cluster --name cybersecurity-platform

# For AWS EKS (requires aws-cli and eksctl)
eksctl create cluster \
  --name cybersecurity-platform \
  --version 1.27 \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed

# For Azure AKS
az aks create \
  --resource-group cybersecurity-rg \
  --name cybersecurity-platform \
  --node-count 3 \
  --node-vm-size Standard_D2s_v3 \
  --enable-addons monitoring \
  --generate-ssh-keys

# For GCP GKE
gcloud container clusters create cybersecurity-platform \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10
```

### Helm Chart Installation

#### 1. Add Helm Repository
```bash
# Add the cybersecurity platform Helm repository
helm repo add cybersecurity-platform https://charts.cybersecurity-platform.example.com
helm repo update

# List available charts
helm search repo cybersecurity-platform
```

#### 2. Create Values File
```yaml
# values-production.yaml
global:
  imageRegistry: your-registry.com
  imagePullSecrets: []
  storageClass: fast-ssd

image:
  repository: cybersecurity-platform/api
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: LoadBalancer
  port: 80
  targetPort: 8000

ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.cybersecurity-platform.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: cybersec-tls
      hosts:
        - api.cybersecurity-platform.example.com

# Database Configuration
postgresql:
  enabled: true
  auth:
    database: cybersec_db
    username: cybersec_user
    password: secure_password_change_me
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: fast-ssd
  readReplicas:
    replicaCount: 2
    persistence:
      enabled: true
      size: 50Gi
      storageClass: fast-ssd

mongodb:
  enabled: true
  auth:
    database: cybersec_db
    username: cybersec_user
    password: mongo_password_change_me
  replicaSet:
    enabled: true
    name: rs0
    key: cybersec_mongodb_key
    replicas:
      - hostsName: mongodb-0
      - hostsName: mongodb-1
      - hostsName: mongodb-2
  persistence:
    enabled: true
    size: 200Gi
    storageClass: fast-ssd

redis:
  enabled: true
  auth:
    enabled: true
    password: redis_password_change_me
  master:
    persistence:
      enabled: true
      size: 50Gi
      storageClass: fast-ssd
  replica:
    replicaCount: 2
    persistence:
      enabled: true
      size: 30Gi
      storageClass: fast-ssd

# External API Keys (as secrets)
apiKeys:
  virustotal: your_virustotal_api_key
  abuseipdb: your_abuseipdb_api_key
  shodan: your_shodan_api_key
  greynoise: your_greynoise_api_key
  otx: your_otx_api_key
  securitytrails: your_securitytrails_api_key

# Monitoring
monitoring:
  enabled: true
  grafana:
    adminPassword: admin_password_change_me
  prometheus:
    retention: 30d
  alertmanager:
    enabled: true

# Scaling
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Resources
resources:
  limits:
    cpu: 2
    memory: 4Gi
  requests:
    cpu: 1
    memory: 2Gi

# Security
security:
  podSecurityPolicy:
    enabled: true
  networkPolicy:
    enabled: true
  rbac:
    create: true
  serviceAccount:
    create: true
    annotations: {}
```

#### 3. Install with Helm
```bash
# Create namespace
kubectl create namespace cybersec-platform

# Install the platform
helm install cybersec-platform cybersecurity-platform/cybersec-platform \
  --namespace cybersec-platform \
  --values values-production.yaml \
  --timeout 10m

# Check installation status
helm status cybersec-platform -n cybersec-platform

# Get all resources
kubectl get all -n cybersec-platform
```

#### 4. Verify Installation
```bash
# Check pod status
kubectl get pods -n cybersec-platform

# Check services
kubectl get services -n cybersec-platform

# Check ingress
kubectl get ingress -n cybersec-platform

# Test API endpoint
curl -f http://api.cybersecurity-platform.example.com/health

# Check logs
kubectl logs -f deployment/cybersec-platform-api -n cybersec-platform
```

### Kustomize Installation

#### Using Kustomize Configuration
```bash
# Create kustomization.yaml
cat > kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: cybersec-platform

resources:
  - namespace.yaml
  - postgres-secret.yaml
  - mongodb-secret.yaml
  - redis-secret.yaml
  - api-keys-secret.yaml
  - configmap.yaml
  - postgres-deployment.yaml
  - mongodb-deployment.yaml
  - redis-deployment.yaml
  - api-deployment.yaml
  - service.yaml
  - ingress.yaml

configMapGenerator:
  - name: cybersec-config
    files:
      - config/.env

secretGenerator:
  - name: cybersec-secrets
    files:
      - secrets/api-keys.json
      - secrets/db-passwords.json
EOF

# Apply configuration
kubectl apply -k .
```

---

## 🔧 Manual Installation

### System Preparation

#### 1. Update System Packages
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git jq htop vim unzip

# RHEL/CentOS
sudo yum update -y
sudo yum install -y curl wget git jq htop vim unzip

# macOS (with Homebrew)
brew update
brew install curl wget git jq htop vim
```

#### 2. Install Python 3.11
```bash
# Ubuntu/Debian
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# RHEL/CentOS
sudo yum install -y python3.11 python3.11-venv python3.11-devel

# macOS
brew install python@3.11

# Verify installation
python3.11 --version
```

#### 3. Install Node.js (optional)
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# Verify installation
node --version
npm --version
```

### Application Installation

#### 1. Clone and Setup
```bash
# Clone repository
git clone https://github.com/your-org/cybersecurity-platform.git
cd cybersecurity-platform

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install application in development mode
pip install -e .
```

#### 2. Directory Structure Setup
```bash
# Create required directories
mkdir -p {logs,data/{postgresql,mongodb,redis},backups,ssl,config}

# Set permissions
chmod 755 logs data backups
chmod 700 ssl config

# Create log rotation config
sudo tee /etc/logrotate.d/cybersec-platform << EOF
/var/log/cybersec-platform/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload cybersec-platform
    endscript
}
EOF
```

#### 3. Systemd Service Setup
```bash
# Create systemd service file
sudo tee /etc/systemd/system/cybersec-platform.service << EOF
[Unit]
Description=Cybersecurity Threat Intelligence Platform
After=network.target postgresql.service mongodb.service redis.service
Requires=postgresql.service mongodb.service redis.service

[Service]
Type=simple
User=cybersec
Group=cybersec
WorkingDirectory=/opt/cybersec-platform
Environment=PATH=/opt/cybersec-platform/venv/bin
ExecStart=/opt/cybersec-platform/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cybersec-platform

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/cybersec-platform/logs /opt/cybersec-platform/data

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable cybersec-platform
```

### Database Installation

#### PostgreSQL Installation
```bash
# Ubuntu/Debian
sudo apt install -y postgresql-15 postgresql-contrib-15

# RHEL/CentOS
sudo yum install -y postgresql15-server postgresql15-contrib
sudo /usr/pgsql-15/bin/postgresql15-setup initdb
sudo systemctl enable postgresql-15
sudo systemctl start postgresql-15

# macOS
brew install postgresql@15
brew services start postgresql@15

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE cybersec_db;
CREATE USER cybersec_user WITH ENCRYPTED PASSWORD 'secure_password_change_me';
GRANT ALL PRIVILEGES ON DATABASE cybersec_db TO cybersec_user;
ALTER USER cybersec_user CREATEDB;
\\q
EOF
```

#### MongoDB Installation
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# RHEL/CentOS
cat > /etc/yum.repos.d/mongodb-org-6.0.repo << EOF
[mongodb-org-6.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/6.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
EOF
sudo yum install -y mongodb-org

# Start MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod

# Create database and user
mongosh << EOF
use cybersec_db
db.createUser({
  user: "cybersec_user",
  pwd: "mongo_password_change_me",
  roles: ["readWrite", "dbAdmin"]
})
EOF
```

#### Redis Installation
```bash
# Ubuntu/Debian
sudo apt install -y redis-server

# RHEL/CentOS
sudo yum install -y redis

# macOS
brew install redis

# Configure Redis
sudo tee /etc/redis/redis.conf << EOF
bind 127.0.0.1 ::1
port 6379
requirepass redis_password_change_me
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

---

## 🗄️ Database Setup

### PostgreSQL Configuration

#### 1. Post-Installation Setup
```bash
# Connect to PostgreSQL
sudo -u postgres psql cybersec_db

# Create extensions
\\i /opt/cybersec-platform/database/postgresql/extensions.sql

# Create tables
\\i /opt/cybersec-platform/database/postgresql/schema.sql

# Create indexes
\\i /opt/cybersec-platform/database/postgresql/indexes.sql

# Insert initial data
\\i /opt/cybersec-platform/database/postgresql/initial_data.sql

\\q
```

#### 2. Performance Tuning
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add performance settings
shared_buffers = 4GB                  # 25% of RAM
effective_cache_size = 12GB          # 75% of RAM
maintenance_work_mem = 1GB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1               # For SSD
effective_io_concurrency = 200       # For SSD

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 3. Connection Pooling Setup
```bash
# Install PgBouncer
sudo apt install -y pgbouncer

# Configure PgBouncer
sudo tee /etc/pgbouncer/pgbouncer.ini << EOF
[databases]
cybersec_db = host=localhost port=5432 dbname=cybersec_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = session
max_client_conn = 1000
default_pool_size = 100
reserve_pool_size = 10
log_connections = 1
log_pooler_errors = 1
stats_period = 60

# Logging
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
EOF

# Create auth file
sudo -u postgres psql cybersec_db -tAc "SELECT usename, passwd FROM pg_shadow WHERE usename != 'postgres';" \
  | sudo tee /etc/pgbouncer/userlist.txt

# Start PgBouncer
sudo systemctl enable pgbouncer
sudo systemctl start pgbouncer
```

### MongoDB Configuration

#### 1. Replica Set Setup
```bash
# Create replica set configuration
sudo tee /etc/mongod.conf << EOF
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  wiredTiger:
    engineConfig:
      cacheSizeGB: 4

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 127.0.0.1

security:
  authorization: enabled
  keyFile: /opt/mongodb/mongodb-keyfile

replication:
  replSetName: "rs0"
EOF

# Create keyfile for replica set
sudo mkdir -p /opt/mongodb
sudo openssl rand -base64 756 > /opt/mongodb/mongodb-keyfile
sudo chmod 400 /opt/mongodb/mongodb-keyfile

# Restart MongoDB
sudo systemctl restart mongod

# Initialize replica set
mongosh << EOF
use admin
db.createUser({
  user: "admin",
  pwd: "admin_password_change_me",
  roles: [ { role: "root", db: "admin" } ]
})
EOF

mongosh --username admin --password admin_password_change_me << EOF
use admin
rs.initiate({
  _id: "rs0",
  members: [
    { _id: 0, host: "localhost:27017" }
  ]
})
EOF
```

#### 2. Sharding Setup (Optional)
```bash
# Start config server
sudo mkdir -p /data/configdb
sudo mongod --configsvr --replSet configReplSet --port 27019

# Start shard server
sudo mkdir -p /data/shard1
sudo mongod --shardsvr --replSet shardReplSet --port 27018

# Initialize config server replica set
mongosh --host localhost:27019 << EOF
use admin
rs.initiate({
  _id: "configReplSet",
  configsvr: true,
  members: [ { _id: 0, host: "localhost:27019" } ]
})
EOF

# Initialize shard replica set
mongosh --host localhost:27018 << EOF
use admin
rs.initiate({
  _id: "shardReplSet",
  members: [ { _id: 0, host: "localhost:27018" } ]
})
EOF

# Add shard to cluster
mongosh --host localhost:27017 --username admin --password admin_password_change_me << EOF
use admin
sh.addShard("shardReplSet/localhost:27018")
sh.enableSharding("cybersec_db")
EOF
```

### Redis Configuration

#### 1. Cluster Setup
```bash
# Create Redis cluster configuration
sudo tee /etc/redis/redis-cluster.conf << EOF
port 7000
cluster-enabled yes
cluster-config-file nodes-7000.conf
cluster-node-timeout 5000
appendonly yes
protected-mode no
bind 127.0.0.1
requirepass redis_password_change_me
masterauth redis_password_change_me
EOF

# Start Redis cluster nodes
for port in 7000 7001 7002; do
  sudo redis-server /etc/redis/redis-cluster.conf --port $port &
done

# Create cluster
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  --cluster-replicas 0 \
  --pass redis_password_change_me
```

#### 2. Sentinel Setup (for high availability)
```bash
# Create Sentinel configuration
sudo tee /etc/redis/sentinel.conf << EOF
port 26379
bind 127.0.0.1
sentinel monitor mymaster 127.0.0.1 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 10000
sentinel parallel-syncs mymaster 1
sentinel resolve-hostnames no
requirepass redis_password_change_me
EOF

# Start Sentinel
sudo redis-sentinel /etc/redis/sentinel.conf
```

---

## ⚙️ Configuration

### Environment Configuration

#### 1. Application Configuration
```bash
# Create main configuration file
sudo tee /opt/cybersec-platform/config/app.conf << EOF
# Application Settings
APP_NAME=Cybersecurity Threat Intelligence Platform
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-change-this-in-production

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
TIMEOUT=30
KEEPALIVE=5

# CORS Configuration
CORS_ORIGINS=["https://app.cybersecurity-platform.example.com", "https://admin.cybersecurity-platform.example.com"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["*"]
CORS_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_ADMIN=1000/minute
RATE_LIMIT_BULK=10/minute

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300
CACHE_TTL_SHORT=60
CACHE_TTL_LONG=86400

# Database URLs
POSTGRESQL_URL=postgresql://cybersec_user:secure_password_change_me@localhost:5432/cybersec_db?sslmode=disable
MONGODB_URL=mongodb://cybersec_user:mongo_password_change_me@localhost:27017/cybersec_db?authSource=admin
REDIS_URL=redis://:redis_password_change_me@localhost:6379/0

# Database Pool Settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600

# External API Configuration
VIRUSTOTAL_API_KEY=your_virustotal_api_key
ABUSEIPDB_API_KEY=your_abuseipdb_api_key
SHODAN_API_KEY=your_shodan_api_key
GREYNOISE_API_KEY=your_greynoise_api_key
OTX_API_KEY=your_otx_api_key
SECURITYTRAILS_API_KEY=your_securitytrails_api_key

# API Timeout Settings
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_BACKOFF_FACTOR=2
API_RATE_LIMIT=1000

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
ELK_ENABLED=true

# Security
JWT_SECRET_KEY=jwt-secret-key-change-this
ENCRYPTION_ALGORITHM=AES-256-GCM
ENCRYPTION_KEY_ROTATION_DAYS=90
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO

# SSL/TLS
SSL_ENABLED=false
SSL_CERT_PATH=/opt/cybersec-platform/ssl/cert.pem
SSL_KEY_PATH=/opt/cybersec-platform/ssl/key.pem
SSL_VERIFY=true
EOF

# Set proper permissions
sudo chown cybersec:cybersec /opt/cybersec-platform/config/app.conf
sudo chmod 600 /opt/cybersec-platform/config/app.conf
```

#### 2. Logging Configuration
```bash
# Create logging configuration
sudo tee /opt/cybersec-platform/config/logging.conf << EOF
[loggers]
keys=root,cybersec

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler

[logger_cybersec]
level=INFO
handlers=consoleHandler,fileHandler
qualname=cybersec
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=simpleFormatter
args=('/var/log/cybersec-platform/app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
EOF
```

#### 3. Database Configuration
```bash
# Create database configuration
sudo tee /opt/cybersec-platform/config/database.conf << EOF
# PostgreSQL Configuration
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_DB=cybersec_db
POSTGRESQL_USER=cybersec_user
POSTGRESQL_PASSWORD=secure_password_change_me
POSTGRESQL_SSL_MODE=require
POSTGRESQL_POOL_SIZE=20
POSTGRESQL_MAX_OVERFLOW=30
POSTGRESQL_POOL_TIMEOUT=30
POSTGRESQL_POOL_RECYCLE=3600

# MongoDB Configuration
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DB=cybersec_db
MONGODB_USER=cybersec_user
MONGODB_PASSWORD=mongo_password_change_me
MONGODB_AUTH_SOURCE=admin
MONGODB_REPLICA_SET=rs0
MONGODB_READ_PREFERENCE=secondaryPreferred
MONGODB_WRITE_CONCERN=majority
MONGODB_READ_CONCERN=majority
MONGODB_CONNECT_TIMEOUT_MS=30000
MONGODB_SERVER_SELECTION_TIMEOUT_MS=30000

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis_password_change_me
REDIS_SSL=false
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30
REDIS_DECODE_RESPONSES=true
REDIS_SKIP_FULL_COVERAGE_CHECK=true

# Connection Pool Settings
CONNECTION_POOL_CLASS=redis.ConnectionPool
CONNECTION_POOL_MAX_CONNECTIONS=100
CONNECTION_POOL_RETRY_ON_TIMEOUT=true
CONNECTION_POOL_SOCKET_KEEPALIVE=true
EOF

sudo chown cybersec:cybersec /opt/cybersec-platform/config/database.conf
sudo chmod 600 /opt/cybersec-platform/config/database.conf
```

### Security Configuration

#### 1. SSL/TLS Setup
```bash
# Generate SSL certificates (self-signed for testing)
sudo mkdir -p /opt/cybersec-platform/ssl

# Generate private key
sudo openssl genrsa -out /opt/cybersec-platform/ssl/key.pem 2048

# Generate certificate signing request
sudo openssl req -new -key /opt/cybersec-platform/ssl/key.pem \
  -out /opt/cybersec-platform/ssl/cert.csr \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=OrgUnit/CN=cybersecurity-platform.example.com"

# Generate self-signed certificate
sudo openssl x509 -req -days 365 -in /opt/cybersec-platform/ssl/cert.csr \
  -signkey /opt/cybersec-platform/ssl/key.pem \
  -out /opt/cybersec-platform/ssl/cert.pem

# Remove CSR file
sudo rm /opt/cybersec-platform/ssl/cert.csr

# Set permissions
sudo chmod 600 /opt/cybersec-platform/ssl/*
sudo chown cybersec:cybersec /opt/cybersec-platform/ssl/*

# For production, use Let's Encrypt
sudo apt install -y certbot
sudo certbot certonly --standalone -d api.cybersecurity-platform.example.com

# Copy certificates
sudo cp /etc/letsencrypt/live/cybersecurity-platform.example.com/fullchain.pem \
  /opt/cybersec-platform/ssl/cert.pem
sudo cp /etc/letsencrypt/live/cybersecurity-platform.example.com/privkey.pem \
  /opt/cybersec-platform/ssl/key.pem
```

#### 2. Firewall Configuration
```bash
# Configure UFW (Ubuntu)
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application port (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 8000

# Allow database ports (internal only)
sudo ufw allow from 10.0.0.0/8 to any port 5432
sudo ufw allow from 10.0.0.0/8 to any port 27017
sudo ufw allow from 10.0.0.0/8 to any port 6379

# Enable firewall
sudo ufw --force enable

# Configure iptables rules (for iptables)
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT
sudo iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP/HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Log dropped packets
sudo iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: "
sudo iptables -A INPUT -j DROP

# Save iptables rules
sudo iptables-save > /etc/iptables/rules.v4
```

#### 3. Security Headers
```bash
# Create security configuration
sudo tee /opt/cybersec-platform/config/security.conf << EOF
# Security Headers
SECURITY_HEADERS=true
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
HSTS_PRELOAD=true

# Content Security Policy
CSP_ENABLED=true
CSP_POLICY="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:;"

# X-Frame-Options
X_FRAME_OPTIONS=DENY

# X-Content-Type-Options
X_CONTENT_TYPE_OPTIONS=nosniff

# X-XSS-Protection
X_XSS_PROTECTION=1; mode=block

# Referrer Policy
REFERRER_POLICY=strict-origin-when-cross-origin

# Permissions Policy
PERMISSIONS_POLICY=camera=(), microphone=(), geolocation=(), payment=()

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_ADMIN=1000/minute
RATE_LIMIT_BULK=10/minute

# Account Security
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_DURATION_MINUTES=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=15
SESSION_TIMEOUT_MINUTES=60

# Encryption
ENCRYPTION_ALGORITHM=AES-256-GCM
ENCRYPTION_KEY_ROTATION_DAYS=90
KEY_MANAGEMENT_SERVICE=local

# Audit Logging
AUDIT_LOG_ENABLED=true
AUDIT_LOG_LEVEL=INFO
AUDIT_LOG_RETENTION_DAYS=2555
AUDIT_LOG_ENCRYPTION=true
EOF

sudo chown cybersec:cybersec /opt/cybersec-platform/config/security.conf
sudo chmod 600 /opt/cybersec-platform/config/security.conf
```

---

## 🔌 External API Setup

### API Key Registration

#### 1. VirusTotal
```bash
# 1. Visit https://www.virustotal.com
# 2. Create account or sign in
# 3. Go to API Key section
# 4. Copy API key
# 5. Add to environment

echo "VIRUSTOTAL_API_KEY=your_virustotal_api_key" >> ~/.bashrc
source ~/.bashrc

# Test API key
curl -H "x-apikey: your_virustotal_api_key" \
  "https://www.virustotal.com/vtapi/v2/ip-address/report?ip=8.8.8.8"
```

#### 2. AbuseIPDB
```bash
# 1. Visit https://www.abuseipdb.com
# 2. Create account
# 3. Go to API documentation
# 4. Get your API key
# 5. Test API key

curl -G \
  -d key=your_abuseipdb_api_key \
  -d ipAddress=8.8.8.8 \
  -d maxAgeInDays=30 \
  "https://api.abuseipdb.com/api/v2/check"
```

#### 3. Shodan
```bash
# 1. Visit https://account.shodan.io
# 2. Create account
# 3. Go to API Key section
# 4. Copy API key
# 5. Test API key

curl "https://api.shodan.io/shodan/host/8.8.8.8?key=your_shodan_api_key"
```

#### 4. GreyNoise
```bash
# 1. Visit https://www.greynoise.io
# 2. Create account
# 3. Go to API section
# 4. Get API key
# 5. Test API key

curl -H "Accept: application/json" \
  -H "key: your_greynoise_api_key" \
  "https://api.greynoise.io/v2/noise/quick/8.8.8.8"
```

#### 5. OTX (AlienVault)
```bash
# 1. Visit https://otx.alienvault.com
# 2. Create account
# 3. Go to API Keys section
# 4. Generate new API key
# 5. Test API key

curl -H "X-OTX-API-KEY: your_otx_api_key" \
  "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general"
```

#### 6. SecurityTrails
```bash
# 1. Visit https://securitytrails.com
# 2. Create account
# 3. Go to API documentation
# 4. Get API key
# 5. Test API key

curl -H "APIKEY: your_securitytrails_api_key" \
  "https://api.securitytrails.com/v1/domain/example.com/dns"
```

### API Configuration

#### 1. Create API Keys Configuration
```bash
# Create API keys configuration file
sudo tee /opt/cybersec-platform/config/api-keys.conf << EOF
{
  "virustotal": {
    "api_key": "your_virustotal_api_key",
    "base_url": "https://www.virustotal.com/vtapi/v2",
    "rate_limit": 4,
    "rate_limit_unit": "minute",
    "timeout": 60,
    "retry_attempts": 3
  },
  "abuseipdb": {
    "api_key": "your_abuseipdb_api_key",
    "base_url": "https://api.abuseipdb.com/api/v2",
    "rate_limit": 100,
    "rate_limit_unit": "day",
    "timeout": 30,
    "retry_attempts": 3
  },
  "shodan": {
    "api_key": "your_shodan_api_key",
    "base_url": "https://api.shodan.io",
    "rate_limit": 100,
    "rate_limit_unit": "month",
    "timeout": 30,
    "retry_attempts": 3
  },
  "greynoise": {
    "api_key": "your_greynoise_api_key",
    "base_url": "https://api.greynoise.io/v3",
    "rate_limit": 100,
    "rate_limit_unit": "month",
    "timeout": 30,
    "retry_attempts": 3
  },
  "otx": {
    "api_key": "your_otx_api_key",
    "base_url": "https://otx.alienvault.com/api/v1",
    "rate_limit": 1000,
    "rate_limit_unit": "month",
    "timeout": 30,
    "retry_attempts": 3
  },
  "securitytrails": {
    "api_key": "your_securitytrails_api_key",
    "base_url": "https://api.securitytrails.com/v1",
    "rate_limit": 10000,
    "rate_limit_unit": "month",
    "timeout": 30,
    "retry_attempts": 3
  }
}
EOF

sudo chown cybersec:cybersec /opt/cybersec-platform/config/api-keys.conf
sudo chmod 600 /opt/cybersec-platform/config/api-keys.conf
```

#### 2. Test API Connectivity
```bash
# Create API test script
sudo tee /opt/cybersec-platform/scripts/test-apis.sh << EOF
#!/bin/bash

set -e

echo "Testing API connectivity..."

# Test VirusTotal
echo "Testing VirusTotal..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "x-apikey: your_virustotal_api_key" \
  "https://www.virustotal.com/vtapi/v2/ip-address/report?ip=8.8.8.8")

if [ "$response" = "200" ]; then
  echo "✓ VirusTotal: OK"
else
  echo "✗ VirusTotal: Failed (HTTP $response)"
fi

# Test AbuseIPDB
echo "Testing AbuseIPDB..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -G -d key=your_abuseipdb_api_key \
  -d ipAddress=8.8.8.8 \
  "https://api.abuseipdb.com/api/v2/check")

if [ "$response" = "200" ]; then
  echo "✓ AbuseIPDB: OK"
else
  echo "✗ AbuseIPDB: Failed (HTTP $response)"
fi

# Test Shodan
echo "Testing Shodan..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://api.shodan.io/shodan/host/8.8.8.8?key=your_shodan_api_key")

if [ "$response" = "200" ]; then
  echo "✓ Shodan: OK"
else
  echo "✗ Shodan: Failed (HTTP $response)"
fi

# Test GreyNoise
echo "Testing GreyNoise..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Accept: application/json" \
  -H "key: your_greynoise_api_key" \
  "https://api.greynoise.io/v2/noise/quick/8.8.8.8")

if [ "$response" = "200" ]; then
  echo "✓ GreyNoise: OK"
else
  echo "✗ GreyNoise: Failed (HTTP $response)"
fi

# Test OTX
echo "Testing OTX..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-OTX-API-KEY: your_otx_api_key" \
  "https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general")

if [ "$response" = "200" ]; then
  echo "✓ OTX: OK"
else
  echo "✗ OTX: Failed (HTTP $response)"
fi

# Test SecurityTrails
echo "Testing SecurityTrails..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "APIKEY: your_securitytrails_api_key" \
  "https://api.securitytrails.com/v1/domain/example.com/dns")

if [ "$response" = "200" ]; then
  echo "✓ SecurityTrails: OK"
else
  echo "✗ SecurityTrails: Failed (HTTP $response)"
fi

echo "API connectivity test completed."
EOF

chmod +x /opt/cybersec-platform/scripts/test-apis.sh
sudo /opt/cybersec-platform/scripts/test-apis.sh
```

---

## 🔒 SSL/TLS Configuration

### Production SSL Setup

#### 1. Let's Encrypt with Certbot
```bash
# Install Certbot
sudo apt install -y certbot

# Stop web server if running
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone \
  -d api.cybersecurity-platform.example.com \
  -d admin.cybersecurity-platform.example.com \
  --email admin@cybersecurity-platform.example.com \
  --agree-tos \
  --non-interactive

# Set up automatic renewal
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet

# Verify renewal
sudo certbot renew --dry-run
```

#### 2. Nginx SSL Configuration
```bash
# Install Nginx
sudo apt install -y nginx

# Create SSL configuration
sudo tee /etc/nginx/sites-available/cybersec-platform << EOF
server {
    listen 80;
    server_name api.cybersecurity-platform.example.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.cybersecurity-platform.example.com;

    ssl_certificate /etc/letsencrypt/live/cybersecurity-platform.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cybersecurity-platform.example.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    location /metrics {
        proxy_pass http://localhost:8000/metrics;
        auth_basic "Metrics";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/cybersec-platform /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create password file for metrics
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd metrics

# Test configuration
sudo nginx -t

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 3. SSL Testing
```bash
# Test SSL configuration
curl -I https://api.cybersecurity-platform.example.com/health

# Test SSL certificate
openssl s_client -connect api.cybersecurity-platform.example.com:443 -servername api.cybersecurity-platform.example.com

# Check SSL rating
ssllabs-scan https://api.cybersecurity-platform.example.com
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

#### 1. Install Prometheus
```bash
# Download and install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
sudo mv prometheus-2.47.0.linux-amd64/prometheus /usr/local/bin/
sudo mv prometheus-2.47.0.linux-amd64/promtool /usr/local/bin/

# Create user
sudo useradd -r -s /bin/false prometheus

# Create directories
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo chown prometheus:prometheus /etc/prometheus /var/lib/prometheus

# Create configuration
sudo tee /etc/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'cybersec-platform'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:9216']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Create alert rules
sudo tee /etc/prometheus/alert_rules.yml << EOF
groups:
- name: cybersec-platform
  rules:
  - alert: HighAPILatency
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API latency detected"

  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"

  - alert: DatabaseDown
    expr: up{job=~"postgresql|mongodb|redis"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Database instance is down"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
EOF

# Set permissions
sudo chown prometheus:prometheus /etc/prometheus/*
sudo chmod 644 /etc/prometheus/*

# Create systemd service
sudo tee /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file /etc/prometheus/prometheus.yml \
  --storage.tsdb.path /var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Start Prometheus
sudo systemctl daemon-reload
sudo systemctl enable prometheus
sudo systemctl start prometheus
```

### Grafana Configuration

#### 1. Install Grafana
```bash
# Install Grafana
sudo apt install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt update
sudo apt install -y grafana

# Configure Grafana
sudo tee /etc/grafana/grafana.ini << EOF
[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3000
domain = cybersecurity-platform.example.com
root_url = %(protocol)s://%(domain)s/grafana/
serve_from_sub_path = false

[database]
type = postgres
host = localhost:5432
name = cybersec_db
user = cybersec_user
password = secure_password_change_me
ssl_mode = disable

[security]
admin_user = admin
admin_password = admin_password_change_me
secret_key = your_secret_key_change_this
cookie_secure = true
cookie_samesite = strict

[users]
allow_sign_up = false

[auth.anonymous]
enabled = false

[alerting]
enabled = true

[smtp]
enabled = true
host = localhost:587
user = grafana@cybersecurity-platform.example.com
from_address = grafana@cybersecurity-platform.example.com
from_name = Grafana

[log]
mode = file
level = info
format = text
EOF

# Start Grafana
sudo systemctl daemon-reload
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access Grafana
# URL: http://your-server:3000
# Username: admin
# Password: admin_password_change_me
```

---

## ✅ Verification

### Health Checks

#### 1. Application Health Check
```bash
# Test basic health endpoint
curl -f http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-10-30T10:00:00Z",
#   "version": "1.0.0"
# }

# Test detailed health check
curl -f http://localhost:8000/health/detailed

# Test with authentication
curl -f -H "X-API-Key: cybersec_key_..." http://localhost:8000/admin/health
```

#### 2. Database Connectivity
```bash
# Test PostgreSQL
sudo -u postgres psql cybersec_db -c "SELECT version();"

# Test MongoDB
mongosh --eval "db.version()" cybersec_db

# Test Redis
redis-cli ping
```

#### 3. API Functionality Test
```bash
# Test email validation
curl -X POST "http://localhost:8000/api/v1/validate/email" \
  -H "X-API-Key: cybersec_key_..." \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Test bulk validation
curl -X POST "http://localhost:8000/api/v1/validate/bulk" \
  -H "X-API-Key: cybersec_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "emails": ["user@example.com"],
    "domains": ["example.com"]
  }'

# Test threat intelligence
curl -X POST "http://localhost:8000/api/v1/threats/query" \
  -H "X-API-Key: cybersec_key_..." \
  -H "Content-Type: application/json" \
  -d '{
    "value": "8.8.8.8",
    "query_type": "ip"
  }'
```

#### 4. Performance Test
```bash
# Install Apache Bench for testing
sudo apt install -y apache2-utils

# Test API performance
ab -n 1000 -c 10 -H "X-API-Key: cybersec_key_..." \
  http://localhost:8000/api/v1/validate/email

# Expected results:
# Requests per second: >100 req/sec
# Time per request: <100ms
# Error rate: <1%
```

### Log Verification

#### 1. Application Logs
```bash
# Check application logs
tail -f /var/log/cybersec-platform/app.log

# Check systemd logs
journalctl -u cybersec-platform -f

# Check error logs
grep -i error /var/log/cybersec-platform/app.log
```

#### 2. Database Logs
```bash
# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

#### 3. Nginx Logs
```bash
# Check access logs
tail -f /var/log/nginx/access.log

# Check error logs
tail -f /var/log/nginx/error.log
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# Test connection manually
psql -h localhost -U cybersec_user -d cybersec_db

# Check connection limits
sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;"

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### 2. MongoDB Connection Issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh --eval "db.adminCommand('ismaster')"

# Check replica set status
mongosh --eval "rs.status()"

# Restart MongoDB
sudo systemctl restart mongod
```

#### 3. Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli ping

# Check memory usage
redis-cli info memory

# Restart Redis
sudo systemctl restart redis-server
```

#### 4. Application Issues
```bash
# Check application status
sudo systemctl status cybersec-platform

# Check application logs
sudo journalctl -u cybersec-platform -f

# Check Python dependencies
pip list | grep -E "(fastapi|sqlalchemy|pydantic)"

# Check environment variables
sudo -u cybersec printenv | grep -E "(DATABASE|REDIS|API)"

# Restart application
sudo systemctl restart cybersec-platform
```

#### 5. SSL/TLS Issues
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect api.cybersecurity-platform.example.com:443

# Check certificate expiration
echo | openssl s_client -connect api.cybersecurity-platform.example.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
```

### Performance Issues

#### 1. High CPU Usage
```bash
# Check CPU usage
top -p $(pgrep -f "cybersec-platform")

# Check for slow queries
sudo -u postgres psql cybersec_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check Redis performance
redis-cli info stats
redis-cli slowlog get 10
```

#### 2. High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check database memory settings
sudo -u postgres psql cybersec_db -c "
SELECT name, setting, unit, context 
FROM pg_settings 
WHERE name LIKE '%memory%';"

# Clear Redis cache if needed
redis-cli FLUSHDB
```

#### 3. High Disk Usage
```bash
# Check disk usage
df -h
du -sh /var/log/cybersec-platform/*

# Check database size
sudo -u postgres psql cybersec_db -c "
SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) as size 
FROM pg_database;"

# Clean old logs
sudo logrotate -f /etc/logrotate.d/cybersec-platform
```

### Network Issues

#### 1. Port Connectivity
```bash
# Check if ports are listening
sudo netstat -tlnp | grep -E "(8000|5432|27017|6379)"

# Test port connectivity
telnet localhost 8000
telnet localhost 5432

# Check firewall rules
sudo ufw status
sudo iptables -L
```

#### 2. External API Issues
```bash
# Test internet connectivity
ping 8.8.8.8

# Test DNS resolution
nslookup virustotal.com

# Test API endpoints manually
curl -v -H "x-apikey: your_api_key" \
  "https://www.virustotal.com/vtapi/v2/ip-address/report?ip=8.8.8.8"

# Check API rate limits
curl -H "x-apikey: your_api_key" \
  "https://www.virustotal.com/vtapi/v2/users/search?query=test" \
  -i  # Include headers
```

---

**Document Version**: 1.0  
**Last Updated**: October 30, 2025  
**Classification**: Internal Use  
**Review Date**: January 30, 2026
