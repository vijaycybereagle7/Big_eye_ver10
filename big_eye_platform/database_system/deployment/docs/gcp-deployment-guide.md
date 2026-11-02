# GCP Deployment Guide

## Threat Intelligence Platform on Google Cloud Platform (GCP)

This guide provides step-by-step instructions for deploying the Threat Intelligence Platform on Google Cloud Platform using multiple approaches.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Options](#deployment-options)
4. [Option 1: GKE Kubernetes Deployment](#option-1-gke-kubernetes-deployment)
5. [Option 2: Cloud Run Deployment](#option-2-cloud-run-deployment)
6. [Option 3: Compute Engine](#option-3-compute-engine)
7. [Database Setup](#database-setup)
8. [Load Balancer Configuration](#load-balancer-configuration)
9. [SSL/TLS Setup](#ssltls-setup)
10. [Monitoring Setup](#monitoring-setup)
11. [Backup Configuration](#backup-configuration)
12. [Security Configuration](#security-configuration)
13. [Cost Optimization](#cost-optimization)

---

## Prerequisites

### Required Tools

```bash
# Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# kubectl
gcloud components install kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Terraform (optional)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### GCP Project Setup

```bash
# Create project
export PROJECT_ID="threatintel-platform"
gcloud projects create $PROJECT_ID --name="Threat Intelligence Platform"

# Set project
gcloud config set project $PROJECT_ID

# Enable billing
echo "Please enable billing for project $PROJECT_ID via GCP Console"

# Enable required APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable sql.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

### Service Account Creation

```bash
# Create service account
gcloud iam service-accounts create threatintel-sa \
  --display-name="ThreatIntel Service Account" \
  --description="Service account for ThreatIntel Platform"

# Grant roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/sql.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Download key
gcloud iam service-accounts keys create ~/threatintel-key.json \
  --iam-account=threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/threatintel-key.json
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Region (us-west1)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Internet   │    │ Cloud CDN    │    │  Cloud Armor │  │
│  │  (0.0.0.0/0) │    │   Global     │    │   WAF/DDoS   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │            Global HTTP(S) Load Balancer              │ │
│  │                 (SSL/TLS Terminated)                  │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │             Backend Services & Health Checks          │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │   GKE    │ │   GKE    │ │   GKE    │ │   GKE    │    │
│  │ Pods/    │ │ Pods/    │ │ Pods/    │ │ Pods/    │    │
│  │ Services │ │ Services │ │ Services │ │ Services │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│        │          │          │          │               │
│        └──────────┴──────────┴──────────┘               │
│                        │                                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              VPC Network                           │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │ Private     │  │ Private     │  │ Public      │  │ │
│  │  │ Subnet-1    │  │ Subnet-2    │  │ Subnet      │  │ │
│  │  │ (us-west1-a)│  │ (us-west1-b)│  │ (us-west1-a)│  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Option 1: GKE Kubernetes Deployment

### Step 1: Create VPC Network

```bash
# Create VPC network
gcloud compute networks create threatintel-vpc \
  --subnet-mode=custom \
  --description="ThreatIntel VPC Network"

# Create private subnets
gcloud compute networks subnets create threatintel-private-1 \
  --network=threatintel-vpc \
  --range=10.0.1.0/24 \
  --region=us-west1 \
  --secondary-range=pod-range=10.1.1.0/16,svc-range=10.1.2.0/16 \
  --description="Private Subnet 1"

gcloud compute networks subnets create threatintel-private-2 \
  --network=threatintel-vpc \
  --range=10.0.2.0/24 \
  --region=us-west1 \
  --secondary-range=pod-range=10.1.3.0/16,svc-range=10.1.4.0/16 \
  --description="Private Subnet 2"

# Create public subnet
gcloud compute networks subnets create threatintel-public \
  --network=threatintel-vpc \
  --range=10.0.10.0/24 \
  --region=us-west1 \
  --description="Public Subnet"
```

### Step 2: Configure Firewall Rules

```bash
# Allow internal traffic
gcloud compute firewall-rules create threatintel-allow-internal \
  --network=threatintel-vpc \
  --allow=tcp:0-65535,udp:0-65535,icmp \
  --source-ranges=10.0.0.0/16

# Allow SSH
gcloud compute firewall-rules create threatintel-allow-ssh \
  --network=threatintel-vpc \
  --allow=tcp:22 \
  --source-ranges=0.0.0.0/0

# Allow HTTP/HTTPS
gcloud compute firewall-rules create threatintel-allow-http \
  --network=threatintel-vpc \
  --allow=tcp:80,443 \
  --source-ranges=0.0.0.0/0

# Allow GKE cluster management
gcloud compute firewall-rules create threatintel-allow-gke \
  --network=threatintel-vpc \
  --allow=tcp:10250,tcp:30000-32767 \
  --source-ranges=10.0.1.0/24,10.0.2.0/24
```

### Step 3: Create GKE Cluster

```bash
# Create GKE cluster
gcloud container clusters create threatintel-cluster \
  --zone=us-west1-a \
  --network=threatintel-vpc \
  --subnetwork=threatintel-private-1 \
  --cluster-secondary-range-name=pod-range \
  --services-secondary-range-name=svc-range \
  --enable-ip-alias \
  --enable-autoscaling \
  --min-nodes=2 \
  --max-nodes=10 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-shielded-nodes \
  --enable-network-policy \
  --enable-master-global-access \
  --addons=HorizontalPodAutoscaling,NetworkPolicy,CloudRun,ConfigConnector \
  --enable-cloud-logging \
  --enable-cloud-monitoring

# Get cluster credentials
gcloud container clusters get-credentials threatintel-cluster \
  --zone=us-west1-a \
  --project=$PROJECT_ID
```

### Step 4: Create Cloud SQL PostgreSQL

```bash
# Create Cloud SQL instance
DB_INSTANCE="threatintel-postgres-$(date +%s)"
DB_PASSWORD="CHANGE_ME_SECURE_PASSWORD"

gcloud sql instances create $DB_INSTANCE \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-8192 \
  --region=us-west1 \
  --storage-auto-increase \
  --backup \
  --backup-start-time="02:00" \
  --maintenance-release-channel=production \
  --maintenance-day=SUN \
  --maintenance-hour=03 \
  --storage-type=SSD \
  --storage-size=100GB \
  --enable-point-in-time-recovery \
  --retained-transaction-log-retention-days=7

# Create database
gcloud sql databases create threatintel \
  --instance=$DB_INSTANCE

# Create user
gcloud sql users create threatintel_user \
  --instance=$DB_INSTANCE \
  --password=$DB_PASSWORD

echo "Cloud SQL Instance: $DB_INSTANCE"
echo "Database: threatintel"
echo "User: threatintel_user"
echo "Password: $DB_PASSWORD (SAVE THIS!)"
```

### Step 5: Create Memorystore Redis

```bash
# Create Redis instance
REDIS_INSTANCE="threatintel-redis-$(date +%s)"
REDIS_PASSWORD="CHANGE_ME_SECURE_REDIS_PASSWORD"

gcloud redis instances create $REDIS_INSTANCE \
  --size=1 \
  --region=us-west1 \
  --redis-version=redis_7_0 \
  --tier=STANDARD_HA \
  --authorized-network=threatintel-vpc \
  --transit-encryption-mode=SERVER_AUTHENTICATION \
  --redis-config maxmemory-policy=allkeys-lru

echo "Redis Instance: $REDIS_INSTANCE"
echo "Redis Password: $REDIS_PASSWORD (SAVE THIS!)"
```

### Step 6: Create Artifact Registry

```bash
# Create repository
gcloud artifacts repositories create threatintel-repo \
  --repository-format=docker \
  --location=us-west1 \
  --description="ThreatIntel Docker Repository"

# Configure Docker authentication
gcloud auth configure-docker us-west1-docker.pkg.dev
```

### Step 7: Build and Push Images

```bash
# Build FastAPI image
docker build -t threatintel/fastapi:latest ../../api
docker tag threatintel/fastapi:latest us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:latest
docker push us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:latest

# Build Celery image
docker build -t threatintel/celery:latest -f Dockerfile.celery ../../api
docker tag threatintel/celery:latest us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/celery:latest
docker push us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/celery:latest
```

### Step 8: Deploy with Helm

```bash
# Add repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install postgresql bitnami/postgresql \
  --set auth.postgresPassword=$DB_PASSWORD \
  --set auth.username=threatintel_user \
  --set auth.password=$DB_PASSWORD \
  --set auth.database=threatintel \
  --set primary.persistence.size=100Gi \
  --set primary.persistence.storageClass=premium-rwo \
  --namespace threatintel --create-namespace

# Install Redis
helm install redis bitnami/redis \
  --set auth.password=$REDIS_PASSWORD \
  --set master.persistence.size=20Gi \
  --set master.persistence.storageClass=premium-rwo \
  --set replica.replicaCount=2 \
  --namespace threatintel

# Get connection information
echo "PostgreSQL: postgresql://threatintel_user:$DB_PASSWORD@postgresql.threatintel.svc.cluster.local:5432/threatintel"
echo "Redis: redis://:$REDIS_PASSWORD@redis-master.threatintel.svc.cluster.local:6379/0"
```

### Step 9: Deploy Application

```bash
# Create namespace
kubectl create namespace threatintel

# Create secret
kubectl create secret generic threatintel-secrets \
  --from-literal=db-password=$DB_PASSWORD \
  --from-literal=redis-password=$REDIS_PASSWORD \
  --from-literal=secret-key="CHANGE_ME_TO_A_SECURE_32_CHARACTER_MINIMUM_SECRET_KEY" \
  --namespace=threatintel

# Deploy FastAPI
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
  namespace: threatintel
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
      - name: fastapi
        image: us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://threatintel_user:$(kubectl get secret threatintel-secrets -n threatintel -o jsonpath='{.data.db-password}' | base64 -d)@postgresql.threatintel.svc.cluster.local:5432/threatintel"
        - name: REDIS_URL
          value: "redis://:$(kubectl get secret threatintel-secrets -n threatintel -o jsonpath='{.data.redis-password}' | base64 -d)@redis-master.threatintel.svc.cluster.local:6379/0"
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 1000m
            memory: 2Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi
  namespace: threatintel
spec:
  selector:
    app: fastapi
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
EOF
```

### Step 10: Setup Ingress

```bash
# Create managed certificate
cat <<EOF | kubectl apply -f -
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: threatintel-ssl
  namespace: threatintel
spec:
  domains:
    - yourdomain.com
    - www.yourdomain.com
EOF

# Create frontend config
cat <<EOF | kubectl apply -f -
apiVersion: networking.gke.io/v1
kind: FrontendConfig
metadata:
  name: threatintel-frontend
  namespace: threatintel
spec:
  redirectToHttps:
    enabled: true
  sslPolicy: termination-policy-ssl
EOF

# Create ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: threatintel-ingress
  namespace: threatintel
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "threatintel-ip"
    networking.gke.io/managed-certificates: threatintel-ssl
    networking.gke.io/frontend-config: threatintel-frontend
    cloud.google.com/backend-config: '{"default": "threatintel-backend"}'
spec:
  defaultBackend:
    service:
      name: fastapi
      port:
        number: 8000
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /*
        pathType: Prefix
        backend:
          service:
            name: fastapi
            port:
              number: 8000
EOF
```

---

## Option 2: Cloud Run Deployment

### Prepare Application

```yaml
# cloudbuild.yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:$COMMIT_SHA', '.']
    dir: 'api'
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'threatintel-api'
      - '--image=us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:$COMMIT_SHA'
      - '--region=us-west1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--memory=1Gi'
      - '--cpu=1'
      - '--concurrency=80'
      - '--max-instances=10'
      - '--port=8000'
      - '--set-env-vars=ENVIRONMENT=production'
```

### Deploy to Cloud Run

```bash
# Deploy FastAPI
gcloud run deploy threatintel-api \
  --image us-west1-docker.pkg.dev/$PROJECT_ID/threatintel-repo/fastapi:latest \
  --region us-west1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --port 8000 \
  --set-env-vars ENVIRONMENT=production \
  --add-cloudsql-instances $PROJECT_ID:us-west1:$DB_INSTANCE \
  --set-secrets DB_PASSWORD=db-password:latest \
  --set-secrets REDIS_PASSWORD=redis-password:latest \
  --set-secrets SECRET_KEY=secret-key:latest
```

---

## Option 3: Compute Engine

### Launch VM Instance

```bash
# Create VM
gcloud compute instances create threatintel-vm \
  --zone=us-west1-a \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --network=threatintel-vpc \
  --subnet=threatintel-public \
  --tags=http-server,https-server \
  --service-account=threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com

# Install Docker
gcloud compute ssh threatintel-vm --zone=us-west1-a << 'EOF'
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
sudo systemctl enable docker
sudo systemctl start docker
EOF
```

---

## Monitoring Setup

### Cloud Monitoring

```bash
# Enable Cloud Monitoring and Logging
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

# Create custom dashboards
cat << 'EOF' > cloud-dashboard.json
{
  "displayName": "ThreatIntel Platform",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "CPU Utilization",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"gke_container\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create --config-from-file=cloud-dashboard.json

# Create alerting policy
cat << 'EOF' > alert-policy.json
{
  "displayName": "ThreatIntel High CPU",
  "conditions": [
    {
      "displayName": "CPU > 80%",
      "conditionThreshold": {
        "filter": "resource.type=\"gke_container\"",
        "comparison": "COMPARISON_GREATER_THAN",
        "thresholdValue": 0.8,
        "duration": "300s"
      }
    }
  ],
  "notificationChannels": ["projects/$PROJECT_ID/notificationChannels/xxx"],
  "enabled": true
}
EOF

gcloud alpha monitoring policies create --policy-from-file=alert-policy.json
```

---

## Backup Configuration

### Cloud Storage

```bash
# Create backup bucket
BACKUP_BUCKET="threatintel-backups-$PROJECT_ID"

gsutil mb -p $PROJECT_ID -l us-west1 gs://$BACKUP_BUCKET

# Enable versioning
gsutil versioning set on gs://$BACKUP_BUCKET

# Configure lifecycle
cat << 'EOF' > lifecycle.json
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "NEARLINE"
        },
        "condition": {
          "age": 30
        }
      },
      {
        "action": {
          "type": "SetStorageClass",
          "storageClass": "COLDLINE"
        },
        "condition": {
          "age": 90
        }
      },
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 365
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://$BACKUP_BUCKET
```

### Automated Backup Script

```bash
#!/bin/bash
# gcp-backup.sh

BACKUP_BUCKET="threatintel-backups-$PROJECT_ID"
DATE=$(date +%Y%m%d_%H%M%S)

# Cloud SQL backup
echo "Creating Cloud SQL backup..."
gcloud sql backups create \
  --instance=$DB_INSTANCE \
  --description="ThreatIntel backup $DATE" \
  --format="value(id)"

# Application data backup
echo "Syncing application data..."
gsutil -m rsync -r -d /opt/data/postgres_timescaledb gs://$BACKUP_BUCKET/postgres/$DATE/
gsutil -m rsync -r -d /opt/data/mongodb gs://$BACKUP_BUCKET/mongodb/$DATE/

echo "Backup completed: $DATE"
```

---

## Security Configuration

### Cloud Armor

```bash
# Create security policy
gcloud compute security-policies create threatintel-security \
  --description="ThreatIntel Security Policy"

# Add rate-based rule
gcloud compute security-policies rules create 1000 \
  --security-policy=threatintel-security \
  --expression="true" \
  --action="rate-based-ban" \
  --rate-threshold-count=100 \
  --rate-threshold-interval=60 \
  --ban-duration=3600 \
  --conform-action=allow \
  --exceed-action=deny-429

# Add IP blacklist rule
gcloud compute security-policies rules create 2000 \
  --security-policy=threatintel-security \
  --expression="source.ip == '1.2.3.4'" \
  --action="deny-403"

# Add SQL injection protection
gcloud compute security-policies rules create 3000 \
  --security-policy=threatintel-security \
  --expression="evaluatePreconfiguredExpr('sqli-stable')" \
  --action=deny-403
```

### Secret Manager

```bash
# Create secrets
echo -n "CHANGE_ME_SECURE_PASSWORD" | gcloud secrets create db-password --data-file=-

echo -n "CHANGE_ME_SECURE_REDIS_PASSWORD" | gcloud secrets create redis-password --data-file=-

echo -n "CHANGE_ME_TO_A_SECURE_32_CHARACTER_MINIMUM_SECRET_KEY" | gcloud secrets create secret-key --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding db-password \
  --member="serviceAccount:threatintel-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Cost Optimization

### Cost Breakdown (Monthly)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **GKE** | 3x n1-standard-4 | $350 - $450 |
| **Cloud SQL** | db-custom-2-8192 HA | $250 - $350 |
| **Memorystore** | Redis Standard HA | $150 - $200 |
| **Load Balancer** | Global HTTP(S) | $25 - $40 |
| **Cloud Storage** | 500GB with lifecycle | $15 - $25 |
| **Cloud CDN** | 1TB transfer | $75 |
| **Data Transfer** | 1TB egress | $85 |
| **Cloud Monitoring** | Custom metrics | $50 |
| **Artifact Registry** | Storage | $10 |
| **Cloud Armor** | Security policy | $5 |
| **Secret Manager** | 3 secrets | $3 |
| **Total** | | **$1,018 - $1,283** |

### Cost Optimization Strategies

1. **Use Preemptible Instances**
2. **Configure Auto-scaling**
3. **Implement SUSTAINED_USE_DISCOUNTS**
4. **Use Committed Use Discounts**
5. **Optimize Storage Classes**

---

## Troubleshooting

### Common Issues

#### GKE Issues

```bash
# Check cluster status
gcloud container clusters describe threatintel-cluster --zone=us-west1-a

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check pod status
kubectl get pods -n threatintel
kubectl logs <pod-name> -n threatintel

# Check events
kubectl get events -n threatintel --sort-by='.lastTimestamp'
```

#### Cloud SQL Issues

```bash
# Check instance status
gcloud sql instances describe $DB_INSTANCE

# Check database connectivity
gcloud sql connect $DB_INSTANCE --user=threatintel_user

# Check backup status
gcloud sql backups list --instance=$DB_INSTANCE
```

---

## Conclusion

This comprehensive GCP deployment guide provides a production-ready infrastructure for the Threat Intelligence Platform. The GKE deployment offers the best balance of features, scalability, and integration with GCP services.

Key benefits of GCP deployment:
- **Managed Services**: Minimal infrastructure management
- **Global Network**: Low-latency worldwide access
- **Built-in Security**: Comprehensive security features
- **Cost Effective**: Competitive pricing with discounts
- **Observability**: Integrated monitoring and logging
- **Scalability**: Automatic scaling capabilities

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-30  
**Author**: Threat Intelligence Platform Team
