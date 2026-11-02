# Azure Deployment Guide

## Threat Intelligence Platform on Microsoft Azure

This guide provides step-by-step instructions for deploying the Threat Intelligence Platform on Microsoft Azure using multiple approaches.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Options](#deployment-options)
4. [Option 1: AKS Kubernetes Deployment](#option-1-aks-kubernetes-deployment)
5. [Option 2: Container Instances](#option-2-container-instances)
6. [Option 3: Virtual Machines](#option-3-virtual-machines)
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
# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# kubectl
az aks install-cli

# Helm
curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Terraform (optional)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### Azure Account Setup

```bash
# Login to Azure
az login

# Set subscription
az account set --subscription "Your Subscription ID"

# Create resource group
RG_NAME="threatintel-rg"
LOCATION="westus2"
az group create --name $RG_NAME --location $LOCATION

# Create service principal
SP_NAME="threatintel-sp"
SP_PASSWORD=$(az ad sp create-for-rbac --name $SP_NAME --role contributor --scopes /subscriptions/$(az account show --query id -o tsv) --output tsv)
SP_APP_ID=$(az ad sp list --display-name $SP_NAME --query '[0].id' -o tsv)

echo "Service Principal: $SP_NAME"
echo "Client ID: $SP_APP_ID"
echo "Client Secret: $SP_PASSWORD (SAVE THIS!)"
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Azure Region (West US 2)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Internet   │    │   Azure CDN  │    │  DDoS        │  │
│  │  (0.0.0.0/0) │    │   (Global)   │    │  Protection  │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │        Azure Front Door / Application Gateway         │ │
│  │              (SSL/TLS Terminated)                     │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                Backend Pools                          │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │    AKS   │ │    AKS   │ │    AKS   │ │    AKS   │    │
│  │ Pods/    │ │ Pods/    │ │ Pods/    │ │ Pods/    │    │
│  │ Services │ │ Services │ │ Services │ │ Services │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│        │          │          │          │               │
│        └──────────┴──────────┴──────────┘               │
│                        │                                 │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Azure VNet                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │ │
│  │  │ Private     │  │ Private     │  │ Public      │  │ │
│  │  │ Subnet-1    │  │ Subnet-2    │  │ Subnet      │  │ │
│  │  │ (westus2-1) │  │ (westus2-2) │  │ (westus2-1) │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Option 1: AKS Kubernetes Deployment

### Step 1: Create Virtual Network

```bash
# Create VNet
VNET_NAME="threatintel-vnet"
VNET_ADDRESS="10.0.0.0/8"

az network vnet create \
  --resource-group $RG_NAME \
  --name $VNET_NAME \
  --address-prefixes $VNET_ADDRESS \
  --location $LOCATION

# Create subnets
az network vnet subnet create \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name aks-subnet \
  --address-prefixes 10.240.0.0/16

az network vnet subnet create \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name db-subnet \
  --address-prefixes 10.241.0.0/16

az network vnet subnet create \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name private-subnet \
  --address-prefixes 10.242.0.0/16

# Create NSG for AKS
az network nsg create \
  --resource-group $RG_NAME \
  --name aks-nsg

az network nsg rule create \
  --resource-group $RG_NAME \
  --nsg-name aks-nsg \
  --name AllowHTTP \
  --protocol Tcp \
  --priority 1000 \
  --destination-port-range 80 \
  --source-address-prefixes '*' \
  --access Allow

az network nsg rule create \
  --resource-group $RG_NAME \
  --nsg-name aks-nsg \
  --name AllowHTTPS \
  --protocol Tcp \
  --priority 1010 \
  --destination-port-range 443 \
  --source-address-prefixes '*' \
  --access Allow

# Associate NSG to AKS subnet
az network vnet subnet update \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name aks-subnet \
  --network-security-group aks-nsg
```

### Step 2: Create AKS Cluster

```bash
# Get subnet IDs
AKS_SUBNET_ID=$(az network vnet subnet show \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name aks-subnet \
  --query id -o tsv)

# Create AKS cluster
CLUSTER_NAME="threatintel-aks"
az aks create \
  --resource-group $RG_NAME \
  --name $CLUSTER_NAME \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --node-osdisk-size 100 \
  --node-osdisk-type Managed \
  --vm-set-type VirtualMachineScaleSets \
  --load-balancer-sku standard \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --network-plugin azure \
  --vnet-subnet-id $AKS_SUBNET_ID \
  --docker-bridge-address 172.17.0.1/16 \
  --dns-service-ip 10.2.0.10 \
  --service-cidr 10.2.0.0/24 \
  --service-principal $SP_APP_ID \
  --client-secret $SP_PASSWORD \
  --enable-managed-identity \
  --enable-addons monitoring \
  --workspace-resource-id $(az monitor log-analytics workspace create \
    --resource-group $RG_NAME \
    --workspace-name threatintel-workspace \
    --query id -o tsv) \
  --yes

# Get credentials
az aks get-credentials \
  --resource-group $RG_NAME \
  --name $CLUSTER_NAME
```

### Step 3: Create Azure Database for PostgreSQL

```bash
# Create server
DB_SERVER="threatintel-postgres-$(date +%s)"
DB_PASSWORD="CHANGE_ME_SECURE_PASSWORD"
DB_LOCATION=$LOCATION

az postgres server create \
  --resource-group $RG_NAME \
  --name $DB_SERVER \
  --location $DB_LOCATION \
  --admin-user threatintel_user \
  --admin-password $DB_PASSWORD \
  --sku-name GP_Gen5_2 \
  --storage-size 51200 \
  --version 15 \
  --public-network-access Disabled

# Create database
az postgres db create \
  --resource-group $RG_NAME \
  --server-name $DB_SERVER \
  --name threatintel

# Enable Azure AD authentication
az postgres server ad-admin create \
  --resource-group $RG_NAME \
  --server-name $DB_SERVER \
  --display-name ThreatIntelADAdmin \
  --object-id $(az ad signed-in-user show --query id -o tsv)

# Configure firewall rules
az postgres server firewall-rule create \
  --resource-group $RG_NAME \
  --server-name $DB_SERVER \
  --name AllowAKSNodes \
  --start-ip-address 10.240.0.0 \
  --end-ip-address 10.240.255.255

# Enable point-in-time restore
az postgres server configuration set \
  --resource-group $RG_NAME \
  --server-name $DB_SERVER \
  --name azure.realm \
  --value "*"

echo "PostgreSQL Server: $DB_SERVER"
echo "Database: threatintel"
echo "User: threatintel_user"
echo "Password: $DB_PASSWORD (SAVE THIS!)"
```

### Step 4: Create Azure Cache for Redis

```bash
# Create Redis cache
REDIS_NAME="threatintel-redis-$(date +%s)"
REDIS_PASSWORD="CHANGE_ME_SECURE_REDIS_PASSWORD"

az redis create \
  --resource-group $RG_NAME \
  --name $REDIS_NAME \
  --location $LOCATION \
  --sku Premium \
  --vm-size P1 \
  --redis-version 7.0 \
  --enable-non-ssl-port false \
  --shard-count 1 \
  --replicas-per-master 1 \
  --replica-priority high \
  --minimum-tls-version 1.2 \
  --redis-configuration '{"maxmemory-policy":"allkeys-lru","maxmemory-reservation":"512"}'

# Create firewall rule for AKS
az redis firewall-rules create \
  --resource-group $RG_NAME \
  --name AllowAKSNodes \
  --redis $REDIS_NAME \
  --start-ip 10.240.0.0 \
  --end-ip 10.240.255.255

echo "Redis Cache: $REDIS_NAME"
echo "Redis Password: $REDIS_PASSWORD (SAVE THIS!)"
```

### Step 5: Create Azure Container Registry

```bash
# Create ACR
ACR_NAME="threatintelacr$(date +%s)"
az acr create \
  --resource-group $RG_NAME \
  --name $ACR_NAME \
  --location $LOCATION \
  --sku Premium \
  --admin-enabled true \
  --georeplication-regions westus2 eastus

# Enable admin user
az acr update \
  --name $ACR_NAME \
  --resource-group $RG_NAME \
  --admin-enabled true

# Get login server
ACR_LOGIN=$(az acr show \
  --name $ACR_NAME \
  --resource-group $RG_NAME \
  --query loginServer -o tsv)

# Login to ACR
az acr login --name $ACR_NAME

echo "Container Registry: $ACR_NAME"
echo "Login Server: $ACR_LOGIN"
```

### Step 6: Build and Push Images

```bash
# Build FastAPI image
docker build -t threatintel/fastapi:latest ../../api
docker tag threatintel/fastapi:latest $ACR_LOGIN/threatintel/fastapi:latest
docker push $ACR_LOGIN/threatintel/fastapi:latest

# Build Celery image
docker build -t threatintel/celery:latest -f Dockerfile.celery ../../api
docker tag threatintel/celery:latest $ACR_LOGIN/threatintel/celery:latest
docker push $ACR_LOGIN/threatintel/threatintel/celery:latest
```

### Step 7: Deploy with Helm

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
  --set primary.persistence.storageClass=managed-premium \
  --namespace threatintel --create-namespace

# Install Redis
helm install redis bitnami/redis \
  --set auth.password=$REDIS_PASSWORD \
  --set master.persistence.size=20Gi \
  --set master.persistence.storageClass=managed-premium \
  --set replica.replicaCount=2 \
  --namespace threatintel

# Create ACR access token
az acr token create \
  --name threatintel-pull \
  --registry $ACR_NAME \
  --scope-map _repositories_pull \
  --output json

# Create image pull secret in Kubernetes
kubectl create secret docker-registry acr-secret \
  --docker-server=$ACR_LOGIN \
  --docker-username=$ACR_NAME \
  --docker-password=$(az acr token credential generate \
    --name threatintel-pull \
    --registry $ACR_NAME \
    --query passwords[0].value -o tsv) \
  --namespace=threatintel
```

### Step 8: Deploy Application

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
      imagePullSecrets:
      - name: acr-secret
      containers:
      - name: fastapi
        image: $ACR_LOGIN/threatintel/fastapi:latest
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

### Step 9: Setup Ingress with Application Gateway

```bash
# Create public IP
az network public-ip create \
  --resource-group $RG_NAME \
  --name threatintel-pip \
  --allocation-method Static \
  --sku Standard

# Create Application Gateway
GATEWAY_NAME="threatintel-gateway"
SUBNET_ID=$(az network vnet subnet show \
  --resource-group $RG_NAME \
  --vnet-name $VNET_NAME \
  --name public \
  --query id -o tsv)

az network application-gateway create \
  --name $GATEWAY_NAME \
  --location $LOCATION \
  --resource-group $RG_NAME \
  --sku WAF_v2 \
  --capacity 2 \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http \
  --public-ip-address threatintel-pip \
  --vnet-name $VNET_NAME \
  --subnet $SUBNET_ID \
  --servers postgresql.threatintel.svc.cluster.local:5432

# Create backend pool
az network application-gateway address-pool create \
  --gateway-name $GATEWAY_NAME \
  --resource-group $RG_NAME \
  --name threatintel-pool \
  --servers $(kubectl get svc fastapi -n threatintel -o jsonpath='{.spec.clusterIP}')

# Create HTTP settings
az network application-gateway http-settings create \
  --gateway-name $GATEWAY_NAME \
  --resource-group $RG_NAME \
  --name threatintel-http-settings \
  --protocol Http \
  --port 8000 \
  --cookie-based-affinity Disabled \
  --timeout 30 \
  --request-timeout 30

# Create listener
az network application-gateway listener create \
  --gateway-name $GATEWAY_NAME \
  --resource-group $RG_NAME \
  --name threatintel-listener \
  --frontend-port threatintel-port \
  --frontend-ip-address threatintel-pip

# Create rule
az network application-gateway rule create \
  --gateway-name $GATEWAY_NAME \
  --resource-group $RG_NAME \
  --name threatintel-rule \
  --http-settings-name threatintel-http-settings \
  --listener-name threatintel-listener \
  --address-pool threatintel-pool

echo "Application Gateway created successfully!"
```

---

## Option 2: Container Instances

### Deploy FastAPI to Container Instances

```bash
# Create container group
az container create \
  --resource-group $RG_NAME \
  --name threatintel-api \
  --image $ACR_LOGIN/threatintel/fastapi:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables ENVIRONMENT=production \
  --secure-environment-variables SECRET_KEY="CHANGE_ME_SECRET_KEY" \
  --registry-login-server $ACR_LOGIN \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show \
    --name $ACR_NAME \
    --query passwords[0].value -o tsv) \
  --restart-policy Always

# Get IP address
API_IP=$(az container show \
  --resource-group $RG_NAME \
  --name threatintel-api \
  --query ipAddress.ip -o tsv)

echo "Container Instance IP: $API_IP"
```

---

## Option 3: Virtual Machines

### Create VM

```bash
# Create VM
VM_NAME="threatintel-vm"
VM_SIZE="Standard_D4s_v3"

az vm create \
  --resource-group $RG_NAME \
  --name $VM_NAME \
  --image Ubuntu2204 \
  --size $VM_SIZE \
  --admin-username azureuser \
  --ssh-key-values ~/.ssh/id_rsa.pub \
  --vnet-name $VNET_NAME \
  --subnet public \
  --nsg-rule SSH \
  --storage-sku Premium_LRS

# Install Docker
az vm run-command create \
  --resource-group $RG_NAME \
  --vm-name $VM_NAME \
  --name install-docker \
  --script-url https://raw.githubusercontent.com/Azure/azure-vm-utils/master/runcommand/install-docker.sh

# Deploy application
az vm extension set \
  --resource-group $RG_NAME \
  --vm-name $VM_NAME \
  --name CustomScript \
  --publisher Microsoft.Azure.Extensions \
  --settings '{
    "fileUris": ["https://raw.githubusercontent.com/your-repo/deployment/azure/deploy.sh"],
    "commandToExecute": "bash deploy.sh"
  }'
```

---

## Database Setup

### Azure Database for PostgreSQL Configuration

```sql
-- Connect to database
az postgres server connect \
  --name $DB_SERVER \
  --database threatintel \
  --admin-user threatintel_user \
  --admin-password $DB_PASSWORD

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create hypertables
SELECT create_hypertable('threat_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX CONCURRENTLY idx_threat_events_ip ON threat_events(ip_address);
CREATE INDEX CONCURRENTLY idx_threat_events_timestamp ON threat_events(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_threat_events_threat_type ON threat_events(threat_type);

-- Configure connection pool
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '512MB';
SELECT pg_reload_conf();
```

---

## SSL/TLS Setup

### Application Gateway SSL

```bash
# Create SSL certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout threatintel.key \
  -out threatintel.crt \
  -subj "/C=US/ST=California/L=San Francisco/O=ThreatIntel/OU=IT/CN=yourdomain.com"

# Create PFX
openssl pkcs12 -export -out threatintel.pfx -inkey threatintel.key -in threatintel.crt

# Upload to Key Vault
az keyvault certificate import \
  --vault-name threatintel-kv \
  --name threatintel-ssl \
  --file threatintel.pfx

# Create HTTPS listener with SSL
az network application-gateway ssl-cert create \
  --resource-group $RG_NAME \
  --gateway-name $GATEWAY_NAME \
  --name threatintel-ssl-cert \
  --key-vault-secret-id $(az keyvault secret show \
    --vault-name threatintel-kv \
    --name threatintel-ssl \
    --query id -o tsv)
```

---

## Monitoring Setup

### Azure Monitor

```bash
# Enable Container Insights
az monitor app-insights component create \
  --app threatintel-insights \
  --location $LOCATION \
  --resource-group $RG_NAME \
  --application-type web

# Create custom metrics
az monitor metrics alert create \
  --name "ThreatIntel High CPU" \
  --resource-group $RG_NAME \
  --scopes $(az resource show --name $CLUSTER_NAME --resource-type Microsoft.ContainerService/managedClusters --query id -o tsv) \
  --condition "avg Percentage CPU > 80" \
  --description "Alert when CPU exceeds 80%" \
  --severity 2 \
  --window-size 5m

# Create Log Analytics workspace
WORKSPACE_NAME="threatintel-loganalytics"
az monitor log-analytics workspace create \
  --resource-group $RG_NAME \
  --workspace-name $WORKSPACE_NAME

# Enable diagnostic settings for AKS
DIAGNOSTIC_SETTING="threatintel-diagnostics"
az monitor diagnostic-settings create \
  --resource $(az resource show --name $CLUSTER_NAME --resource-type Microsoft.ContainerService/managedClusters --query id -o tsv) \
  --name $DIAGNOSTIC_SETTING \
  --workspace $WORKSPACE_NAME \
  --logs '[
    {
      "category": "kube-apiserver",
      "enabled": true
    },
    {
      "category": "kube-controller-manager",
      "enabled": true
    },
    {
      "category": "kube-scheduler",
      "enabled": true
    }
  ]'
```

---

## Backup Configuration

### Azure Backup

```bash
# Create Recovery Services vault
VAULT_NAME="threatintel-backup-vault"
az backup vault create \
  --resource-group $RG_NAME \
  --name $VAULT_NAME \
  --location $LOCATION \
  --sku Standard

# Backup PostgreSQL database
az backup protection enable-for-azurevm \
  --vault-name $VAULT_NAME \
  --resource-group $RG_NAME \
  --vm threatintel-vm \
  --policy-name DefaultPolicy

# Backup Azure Database for PostgreSQL
az backup protection enable-for-azurewaf \
  --vault-name $VAULT_NAME \
  --resource-group $RG_NAME \
  --server-name $DB_SERVER \
  --database-name threatintel \
  --policy-name DefaultPolicy

# Create backup policy
az backup policy create \
  --vault-name $VAULT_NAME \
  --name "ThreatIntelPolicy" \
  --policy '{
    "name": "DefaultPolicy",
    "backupManagementType": "AzureSql",
    "workLoadType": "SQLDataBase",
    "schedulePolicy": {
      "schedulePolicyType": "SimpleSchedulePolicy",
      "scheduleRunFrequency": "Daily",
      "scheduleRunTimes": ["2024-01-01T02:00:00Z"],
      "scheduleWeeklyFrequency": 0
    },
    "retentionPolicy": {
      "retentionPolicyType": "LongTermRetentionPolicy",
      "dailySchedule": {
        "retentionTimes": ["2024-01-01T02:00:00Z"],
        "retentionDuration": {
          "count": 30,
          "durationType": "Days"
        }
      }
    }
  }'
```

### Azure Storage Account

```bash
# Create storage account
STORAGE_ACCOUNT="threatintelbackup$(date +%s)"
az storage account create \
  --resource-group $RG_NAME \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --sku Standard_ZRS \
  --kind StorageV2 \
  --access-tier Hot

# Create container
az storage container create \
  --account-name $STORAGE_ACCOUNT \
  --name backups \
  --auth-mode login

# Configure lifecycle policy
cat << 'EOF' > lifecycle.json
{
  "rules": [
    {
      "enabled": true,
      "name": "threatintel-backup-lifecycle",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 90
            },
            "delete": {
              "daysAfterModificationGreaterThan": 365
            }
          }
        }
      }
    }
  ]
}
EOF

az storage account management-policy create \
  --account-name $STORAGE_ACCOUNT \
  --policy @lifecycle.json
```

---

## Security Configuration

### Azure Security Center

```bash
# Enable Security Center
az security workspace create \
  --name "threatintel-security" \
  --resource-group $RG_NAME

# Enable defender for Kubernetes
az security pricing create \
  --name kubernetesService \
  --tier Standard

# Enable defender for SQL
az security pricing create \
  --name SqlServers \
  --tier Standard
```

### Key Vault

```bash
# Create Key Vault
KEYVAULT_NAME="threatintel-kv-$(date +%s)"
az keyvault create \
  --resource-group $RG_NAME \
  --name $KEYVAULT_NAME \
  --location $LOCATION \
  --sku standard

# Store secrets
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name db-password \
  --value $DB_PASSWORD

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name redis-password \
  --value $REDIS_PASSWORD

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name secret-key \
  --value "CHANGE_ME_TO_A_SECURE_32_CHARACTER_MINIMUM_SECRET_KEY"

# Grant access to AKS
AZURE_CLIENT_ID=$(az aks show \
  --resource-group $RG_NAME \
  --name $CLUSTER_NAME \
  --query "servicePrincipalProfile.clientId" -o tsv)

az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $(az identity show \
    --resource-group $RG_NAME \
    --name "${CLUSTER_NAME}-agentpool" \
    --query "principalId" -o tsv) \
  --secret-permissions get list \
  --certificate-permissions get list
```

---

## Cost Optimization

### Cost Breakdown (Monthly)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **AKS** | 3x Standard_D4s_v3 | $450 - $600 |
| **PostgreSQL** | GP_Gen5_2 HA | $300 - $400 |
| **Redis Cache** | Premium P1 | $150 - $200 |
| **Container Registry** | Premium | $50 |
| **Load Balancer** | Standard | $25 |
| **Storage Account** | 500GB with lifecycle | $20 |
| **Virtual Network** | Custom VNet | $0 |
| **Backup** | 1TB retention | $50 |
| **Monitor** | Azure Monitor | $100 |
| **Traffic** | 1TB egress | $87 |
| **Key Vault** | Premium | $30 |
| **Total** | | **$1,262 - $1,562** |

### Cost Optimization Strategies

1. **Use Reserved VM Instances**
2. **Configure Auto-scaling**
3. **Implement Spot Instances**
4. **Use Azure Hybrid Benefit**
5. **Optimize Storage Classes**

---

## Troubleshooting

### Common Issues

#### AKS Issues

```bash
# Check cluster status
az aks show \
  --resource-group $RG_NAME \
  --name $CLUSTER_NAME \
  --query provisioningState

# Check node status
kubectl get nodes
kubectl describe node <node-name>

# Check pod status
kubectl get pods -n threatintel
kubectl logs <pod-name> -n threatintel

# Check events
kubectl get events -n threatintel --sort-by='.lastTimestamp'
```

#### Database Issues

```bash
# Check PostgreSQL status
az postgres server show \
  --resource-group $RG_NAME \
  --name $DB_SERVER \
  --query state

# Check connections
az postgres server list \
  --resource-group $RG_NAME

# Restore database
az postgres server restore \
  --resource-group $RG_NAME \
  --name $DB_SERVER-restored \
  --source-server $DB_SERVER \
  --restore-point-in-time "2025-10-30T12:00:00Z"
```

---

## Conclusion

This comprehensive Azure deployment guide provides a production-ready infrastructure for the Threat Intelligence Platform. The AKS deployment offers enterprise-grade features with deep integration with Azure services.

Key benefits of Azure deployment:
- **Enterprise Integration**: Deep integration with Microsoft ecosystem
- **Hybrid Cloud**: Seamless on-premises to cloud integration
- **Compliance**: Extensive compliance certifications
- **Cost Effective**: Competitive pricing with enterprise agreements
- **Security**: Advanced security features and controls
- **Support**: 24/7 enterprise support

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-30  
**Author**: Threat Intelligence Platform Team
