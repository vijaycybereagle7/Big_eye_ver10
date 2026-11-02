# AWS Deployment Guide

## Threat Intelligence Platform on Amazon Web Services (AWS)

This guide provides step-by-step instructions for deploying the Threat Intelligence Platform on AWS using multiple approaches for different use cases.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Options](#deployment-options)
4. [Option 1: ECS Fargate Deployment](#option-1-ecs-fargate-deployment)
5. [Option 2: EKS Kubernetes Deployment](#option-2-eks-kubernetes-deployment)
6. [Option 3: EC2 Docker Compose](#option-3-ec2-docker-compose)
7. [Database Setup](#database-setup)
8. [Load Balancer Configuration](#load-balancer-configuration)
9. [SSL/TLS Setup](#ssltls-setup)
10. [Monitoring Setup](#monitoring-setup)
11. [Backup Configuration](#backup-configuration)
12. [Security Configuration](#security-configuration)
13. [Cost Optimization](#cost-optimization)
14. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform (for infrastructure)
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/

# kubectl (for EKS)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Helm (for Kubernetes)
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

### AWS Account Setup

1. **Create AWS Account**: https://aws.amazon.com/free/
2. **Enable MFA** on root account
3. **Create IAM User** with administrator privileges
4. **Configure AWS CLI**:
   ```bash
   aws configure
   # AWS Access Key ID: YOUR_ACCESS_KEY
   # AWS Secret Access Key: YOUR_SECRET_KEY
   # Default region name: us-west-2
   # Default output format: json
   ```

### Required IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "ecs:*",
                "eks:*",
                "rds:*",
                "elasticache:*",
                "elasticfilesystem:*",
                "iam:*",
                "logs:*",
                "s3:*",
                "secretsmanager:*",
                "wafv2:*",
                "cloudfront:*",
                "route53:*",
                "acm:*"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Region (us-west-2)                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Internet   │    │   CloudFront │    │     WAF      │  │
│  │     (0.0.0.0/0)   │   CDN/DDoS   │    │   Protection │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Application Load Balancer                │ │
│  │                  (ALB) + TLS                          │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Target Groups & Health Checks             │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                    │
│                       ▼                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ ECS/EKS  │ │ ECS/EKS  │ │ ECS/EKS  │ │ ECS/EKS  │    │
│  │ Tasks/   │ │ Tasks/   │ │ Tasks/   │ │ Tasks/   │    │
│  │ Pods     │ │ Pods     │ │ Pods     │ │ Pods     │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│        │          │          │          │               │
│        │          │          │          │               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                 Security Groups                      │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Private Subnets (2 AZ)                  │ │
│  │  ┌──────────────┐  ┌──────────────┐                 │ │
│  │  │  Subnet-1    │  │  Subnet-2    │                 │ │
│  │  │  (us-west-2a)│  │  (us-west-2b)│                 │ │
│  │  └──────────────┘  └──────────────┘                 │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Infrastructure Components

| Component | Service | Purpose | High Availability |
|-----------|---------|---------|-------------------|
| **Load Balancer** | ALB | Traffic distribution, SSL termination | Multi-AZ |
| **Container Orchestration** | ECS/EKS | Application containers | Multi-AZ |
| **Database** | RDS + ElastiCache | PostgreSQL + Redis | Multi-AZ |
| **Log Storage** | S3 + CloudWatch | Centralized logging | Multi-region |
| **Monitoring** | CloudWatch + Prometheus | Metrics and alerting | Multi-AZ |
| **Storage** | EFS | Persistent file storage | Multi-AZ |
| **Secrets** | Secrets Manager | Credential management | Multi-AZ |
| **CDN** | CloudFront | Static content delivery | Global |
| **Security** | WAF + Security Groups | DDoS protection, firewall | Multi-AZ |

---

## Deployment Options

### Option Comparison

| Option | Complexity | Cost | Scalability | Management Overhead |
|--------|------------|------|-------------|-------------------|
| **ECS Fargate** | Low | Medium | Good | Low |
| **EKS Kubernetes** | High | High | Excellent | High |
| **EC2 Docker** | Medium | Low | Limited | Medium |

---

## Option 1: ECS Fargate Deployment

### Step 1: Create VPC and Networking

#### Create VPC

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=threatintel-vpc}]' \
  --query 'Vpc.VpcId' --output text)

# Enable DNS hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Enable DNS support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support

echo "VPC ID: $VPC_ID"
```

#### Create Subnets

```bash
# Create public subnets
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=threatintel-public-1}]' \
  --query 'Subnet.SubnetId' --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-west-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=threatintel-public-2}]' \
  --query 'Subnet.SubnetId' --output text)

# Create private subnets
PRIVATE_SUBNET_1=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-west-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=threatintel-private-1}]' \
  --query 'Subnet.SubnetId' --output text)

PRIVATE_SUBNET_2=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.12.0/24 \
  --availability-zone us-west-2b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=threatintel-private-2}]' \
  --query 'Subnet.SubnetId' --output text)

echo "Public Subnet 1: $PUBLIC_SUBNET_1"
echo "Public Subnet 2: $PUBLIC_SUBNET_2"
echo "Private Subnet 1: $PRIVATE_SUBNET_1"
echo "Private Subnet 2: $PRIVATE_SUBNET_2"
```

#### Create Internet Gateway and NAT Gateways

```bash
# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=threatintel-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)

# Attach to VPC
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create Elastic IPs for NAT Gateways
NAT_EIP_1=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
NAT_EIP_2=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

# Create NAT Gateways
NAT_GW_1=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_1 \
  --allocation-id $NAT_EIP_1 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=threatintel-nat-1}]' \
  --query 'NatGateway.NatGatewayId' --output text)

NAT_GW_2=$(aws ec2 create-nat-gateway \
  --subnet-id $PUBLIC_SUBNET_2 \
  --allocation-id $NAT_EIP_2 \
  --tag-specifications 'ResourceType=nat-gateway,Tags=[{Key=Name,Value=threatintel-nat-2}]' \
  --query 'NatGateway.NatGatewayId' --output text)

echo "NAT Gateway 1: $NAT_GW_1"
echo "NAT Gateway 2: $NAT_GW_2"
```

#### Configure Route Tables

```bash
# Create public route table
PUBLIC_RT=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=threatintel-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)

# Add route to Internet Gateway
aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Associate public subnets
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_1 --route-table-id $PUBLIC_RT
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET_2 --route-table-id $PUBLIC_RT

# Create private route tables
PRIVATE_RT_1=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=threatintel-private-rt-1}]' \
  --query 'RouteTable.RouteTableId' --output text)

PRIVATE_RT_2=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=threatintel-private-rt-2}]' \
  --query 'RouteTable.RouteTableId' --output text)

# Add routes to NAT Gateways
aws ec2 create-route --route-table-id $PRIVATE_RT_1 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_1
aws ec2 create-route --route-table-id $PRIVATE_RT_2 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_2

# Associate private subnets
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_1 --route-table-id $PRIVATE_RT_1
aws ec2 associate-route-table --subnet-id $PRIVATE_SUBNET_2 --route-table-id $PRIVATE_RT_2
```

### Step 2: Create Security Groups

#### Application Security Group

```bash
# Application Security Group
APP_SG=$(aws ec2 create-security-group \
  --group-name threatintel-app-sg \
  --description "ThreatIntel Application Security Group" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=threatintel-app-sg}]' \
  --query 'GroupId' --output text)

# Add inbound rules
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 22 --cidr 0.0.0.0/0

# Add intra-group communication
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 8000 --source-group $APP_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 5432 --source-group $APP_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 6379 --source-group $APP_SG
aws ec2 authorize-security-group-ingress --group-id $APP_SG --protocol tcp --port 27017 --source-group $APP_SG

echo "Application Security Group: $APP_SG"
```

#### RDS Security Group

```bash
# RDS Security Group
RDS_SG=$(aws ec2 create-security-group \
  --group-name threatintel-rds-sg \
  --description "ThreatIntel RDS Security Group" \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=threatintel-rds-sg}]' \
  --query 'GroupId' --output text)

# Allow PostgreSQL from application security group only
aws ec2 authorize-security-group-ingress --group-id $RDS_SG --protocol tcp --port 5432 --source-group $APP_SG

echo "RDS Security Group: $RDS_SG"
```

### Step 3: Create RDS PostgreSQL Instance

```bash
# Create DB Subnet Group
aws rds create-db-subnet-group \
  --db-subnet-group-name threatintel-db-subnet-group \
  --db-subnet-group-description "ThreatIntel DB Subnet Group" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2 \
  --tags Key=Name,Value=threatintel-db-subnet-group

# Create RDS Instance
DB_INSTANCE_ID="threatintel-db-$(date +%s)"
DB_PASSWORD="CHANGE_ME_SECURE_PASSWORD"

aws rds create-db-instance \
  --db-instance-identifier $DB_INSTANCE_ID \
  --db-instance-class db.r5.large \
  --engine postgres \
  --engine-version 15.3 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --master-username threatintel_user \
  --master-user-password $DB_PASSWORD \
  --db-name threatintel \
  --vpc-security-group-ids $RDS_SG \
  --db-subnet-group-name threatintel-db-subnet-group \
  --backup-retention-period 30 \
  --preferred-backup-window "02:00-03:00" \
  --preferred-maintenance-window "Sun:03:00-Sun:04:00" \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --deletion-protection

echo "DB Instance: $DB_INSTANCE_ID"
echo "DB Password: $DB_PASSWORD (SAVE THIS!)"
```

### Step 4: Create ElastiCache Redis

```bash
# Create ElastiCache Subnet Group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name threatintel-cache-subnet-group \
  --cache-subnet-group-description "ThreatIntel Cache Subnet Group" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2

# Create Redis Cluster
CACHE_CLUSTER_ID="threatintel-redis-$(date +%s)"
REDIS_PASSWORD="CHANGE_ME_SECURE_REDIS_PASSWORD"

aws elasticache create-cache-cluster \
  --cache-cluster-id $CACHE_CLUSTER_ID \
  --cache-node-type cache.r5.large \
  --engine redis \
  --num-cache-nodes 1 \
  --cache-subnet-group-name threatintel-cache-subnet-group \
  --security-group-ids $APP_SG \
  --auth-token $REDIS_PASSWORD \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --tags Key=Name,Value=threatintel-redis

echo "Redis Cluster: $CACHE_CLUSTER_ID"
echo "Redis Password: $REDIS_PASSWORD (SAVE THIS!)"
```

### Step 5: Create ECR Repositories

```bash
# Create ECR repository for FastAPI application
aws ecr create-repository \
  --repository-name threatintel/fastapi \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Create ECR repository for Celery workers
aws ecr create-repository \
  --repository-name threatintel/celery \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256

# Get login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com
```

### Step 6: Create ECS Cluster

```bash
# Create ECS Cluster
CLUSTER_NAME="threatintel-cluster"

aws ecs create-cluster \
  --cluster-name $CLUSTER_NAME \
  --capacity-providers FARGATE \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
  --configuration executeCommandConfiguration kmsKeyId=alias/aws/ecs,logging=OVERRIDE,logConfiguration=STRING \
  --tags key=Name,value=threatintel-cluster \
  --serviceConnectConfiguration namespace=threatintel-ns

echo "ECS Cluster: $CLUSTER_NAME"
```

### Step 7: Build and Push Docker Images

#### Prepare Dockerfiles

```dockerfile
# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Push Images

```bash
# Build and push FastAPI image
docker build -t threatintel/fastapi:latest ../../api
docker tag threatintel/fastapi:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/fastapi:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/fastapi:latest

# Build and push Celery image
docker build -t threatintel/celery:latest -f Dockerfile.celery ../../api
docker tag threatintel/celery:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/celery:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/celery:latest
```

### Step 8: Create ECS Task Definitions

#### FastAPI Task Definition

```json
{
  "family": "threatintel-fastapi",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "fastapi",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/fastapi:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://threatintel_user:${DB_PASSWORD}@${DB_ENDPOINT}:5432/threatintel"
        },
        {
          "name": "REDIS_URL",
          "value": "redis://:${REDIS_PASSWORD}@${REDIS_ENDPOINT}:6379/0"
        },
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:threatintel/db-password-xxxxx"
        },
        {
          "name": "REDIS_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:threatintel/redis-password-xxxxx"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:threatintel/secret-key-xxxxx"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/threatintel",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Step 9: Create ECS Services

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition-fastapi.json

# Create ECS Service
aws ecs create-service \
  --cluster $CLUSTER_NAME \
  --service-name threatintel-fastapi-service \
  --task-definition threatintel-fastapi:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2],securityGroups=[$APP_SG],assignPublicIp=DISABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/threatintel-tg/1234567890123456,containerName=fastapi,containerPort=8000 \
  --service-connect-configuration namespace=threatintel-ns \
  --deployment-configuration maximumPercent=200,minimumHealthyPercent=100
```

### Step 10: Create Application Load Balancer

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name threatintel-alb \
  --subnets $PUBLIC_SUBNET_1 $PUBLIC_SUBNET_2 \
  --security-groups $APP_SG \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --tags Key=Name,Value=threatintel-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns $ALB_ARN \
  --query 'LoadBalancers[0].DNSName' --output text)

echo "ALB ARN: $ALB_ARN"
echo "ALB DNS: $ALB_DNS"
```

### Step 11: Create Target Groups

```bash
# Create target group for FastAPI
TG_ARN=$(aws elbv2 create-target-group \
  --name threatintel-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /health \
  --health-check-protocol HTTP \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --matcher HttpCode=200 \
  --tags Key=Name,Value=threatintel-tg \
  --query 'TargetGroups[0].TargetGroupArn' --output text)

echo "Target Group ARN: $TG_ARN"
```

### Step 12: Setup SSL Certificate

```bash
# Request SSL certificate
CERT_ARN=$(aws acm request-certificate \
  --domain-name yourdomain.com \
  --subject-alternative-names www.yourdomain.com \
  --validation-method DNS \
  --query 'CertificateArn' --output text)

echo "Certificate ARN: $CERT_ARN"
```

### Step 13: Create Listener Rules

```bash
# Create HTTPS listener
LISTENER_ARN=$(aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN \
  --query 'Listeners[0].ListenerArn' --output text)

# Create HTTP listener with redirect
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig='Protocol=HTTPS,Port=443,StatusCode=HTTP_301'

echo "Listener ARN: $LISTENER_ARN"
```

### Step 14: Configure CloudWatch Logs

```bash
# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/threatintel
aws logs put-retention-policy --log-group-name /ecs/threatintel --retention-in-days 30
```

---

## Option 2: EKS Kubernetes Deployment

### Prerequisites for EKS

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
```

### Create EKS Cluster

```bash
# Create EKS cluster
eksctl create cluster \
  --name threatintel-cluster \
  --version 1.27 \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.large \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 10 \
  --managed \
  --enable-ssm \
  --full-ecr-access \
  --appmesh-access \
  --vpc-private-subnets $PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2 \
  --vpc-public-subnets $PUBLIC_SUBNET_1,$PUBLIC_SUBNET_2 \
  --vpc-cidr 10.0.0.0/16 \
  --tags Name=threatintel-cluster,Environment=production \
  --asg-access \
  --external-dns-access \
  --full-access

echo "EKS cluster created successfully!"
```

### Deploy with Helm

```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add elastic https://helm.elastic.co
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy PostgreSQL
helm install postgresql bitnami/postgresql \
  --set auth.postgresPassword=$DB_PASSWORD \
  --set auth.username=threatintel_user \
  --set auth.password=$DB_PASSWORD \
  --set auth.database=threatintel \
  --set primary.persistence.size=100Gi \
  --set primary.persistence.storageClass=gp3 \
  --set primary.resources.requests.cpu=500m \
  --set primary.resources.requests.memory=1Gi \
  --set primary.resources.limits.cpu=1000m \
  --set primary.resources.limits.memory=2Gi \
  --namespace threatintel --create-namespace

# Deploy Redis
helm install redis bitnami/redis \
  --set auth.password=$REDIS_PASSWORD \
  --set master.persistence.size=20Gi \
  --set master.persistence.storageClass=gp3 \
  --set replica.replicaCount=2 \
  --set master.resources.requests.cpu=250m \
  --set master.resources.requests.memory=512Mi \
  --namespace threatintel

# Deploy FastAPI application
helm install threatintel-platform ../kubernetes/helm/threatintel-platform \
  --namespace threatintel \
  --create-namespace \
  --values ../kubernetes/helm/threatintel-platform/values-production.yaml \
  --set image.repository=123456789012.dkr.ecr.us-west-2.amazonaws.com/threatintel/fastapi \
  --set image.tag=latest \
  --set database.host=postgresql \
  --set database.password=$DB_PASSWORD \
  --set redis.host=redis-master \
  --set redis.password=$REDIS_PASSWORD
```

---

## Option 3: EC2 Docker Compose

### Launch EC2 Instance

```bash
# Launch EC2 instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1d0 \
  --count 1 \
  --instance-type t3.large \
  --key-name threatintel-keypair \
  --security-group-ids $APP_SG \
  --subnet-id $PRIVATE_SUBNET_1 \
  --associate-public-ip-address \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=threatintel-ec2}]' \
  --query 'Instances[0].InstanceId' --output text)

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "EC2 Instance: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"

# SSH into instance and install Docker
ssh -i ~/.ssh/threatintel-keypair.pem ubuntu@$PUBLIC_IP << 'EOF'
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker
EOF

echo "Docker installed on EC2 instance"
```

### Deploy Application

```bash
# Copy deployment files
scp -i ~/.ssh/threatintel-keypair.pem -r deployment/ ubuntu@$PUBLIC_IP:/home/ubuntu/

# SSH and deploy
ssh -i ~/.ssh/threatintel-keypair.pem ubuntu@$PUBLIC_IP << 'EOF'
cd /home/ubuntu/deployment/docker
cp .env.template .env
# Edit .env with actual values
vim .env

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
EOF
```

---

## Database Setup

### PostgreSQL Configuration

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create hypertables for time-series data
SELECT create_hypertable('threat_events', 'timestamp', if_not_exists => TRUE);

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_threat_events_ip ON threat_events(ip_address);
CREATE INDEX CONCURRENTLY idx_threat_events_timestamp ON threat_events(timestamp DESC);
CREATE INDEX CONCURRENTLY idx_threat_events_threat_type ON threat_events(threat_type);

-- Configure connection pooling
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers = '16MB';
SELECT pg_reload_conf();
```

### MongoDB Configuration

```javascript
// Switch to threatintel_logs database
use threatintel_logs

// Create collections
db.createCollection("security_events", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "event_type", "source"],
      properties: {
        timestamp: {
          bsonType: "date"
        },
        event_type: {
          bsonType: "string"
        },
        source: {
          bsonType: "string"
        },
        details: {
          bsonType: "object"
        }
      }
    }
  }
});

// Create indexes
db.security_events.createIndex({ "timestamp": 1 });
db.security_events.createIndex({ "event_type": 1 });
db.security_events.createIndex({ "source": 1 });
db.security_events.createIndex({ "timestamp": 1, "event_type": 1 });

// Enable TTL for automatic document expiration
db.security_events.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 7776000 }); // 90 days
```

---

## Load Balancer Configuration

### Application Load Balancer (ALB)

```yaml
# ALB Configuration
LoadBalancer:
  Name: threatintel-alb
  Scheme: internet-facing
  Type: application
  IpAddressType: ipv4
  SecurityGroups:
    - sg-app
  Subnets:
    - subnet-public-1
    - subnet-public-2

TargetGroups:
  - Name: threatintel-api-tg
    Protocol: HTTP
    Port: 8000
    HealthCheck:
      Path: /health
      Protocol: HTTP
      Interval: 30
      Timeout: 5
      HealthyThreshold: 2
      UnhealthyThreshold: 3

Listeners:
  - Protocol: HTTPS
    Port: 443
    Certificates:
      - CertificateArn: arn:aws:acm:...
    DefaultActions:
      - Type: forward
        TargetGroupArn: arn:aws:elasticloadbalancing:...

  - Protocol: HTTP
    Port: 80
    DefaultActions:
      - Type: redirect
        RedirectConfig:
          Protocol: HTTPS
          Port: 443
          StatusCode: HTTP_301
```

### CloudFront Distribution

```json
{
  "DistributionConfig": {
    "CallerReference": "threatintel-2025-10-30",
    "DefaultRootObject": "index.html",
    "Origins": [
      {
        "Id": "ThreatIntel-ALB",
        "DomainName": "threatintel-alb.us-west-2.elb.amazonaws.com",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only",
          "OriginSslProtocols": ["TLSv1.2"]
        }
      }
    ],
    "DefaultCacheBehavior": {
      "TargetOriginId": "ThreatIntel-ALB",
      "ViewerProtocolPolicy": "redirect-to-https",
      "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
      "CachedMethods": ["GET", "HEAD"],
      "Compress": true,
      "ForwardedValues": {
        "QueryString": true,
        "Headers": ["Accept-Language", "CloudFront-Forwarded-Proto"]
      }
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100",
    "ViewerCertificate": {
      "ACMCertificateArn": "arn:aws:acm:...",
      "SSLSupportMethod": "sni-only",
      "MinimumProtocolVersion": "TLSv1.2_2021"
    }
  }
}
```

---

## SSL/TLS Setup

### AWS Certificate Manager

```bash
# Request certificate
CERT_ARN=$(aws acm request-certificate \
  --domain-name yourdomain.com \
  --subject-alternative-names www.yourdomain.com api.yourdomain.com \
  --validation-method DNS \
  --query 'CertificateArn' --output text)

echo "Certificate ARN: $CERT_ARN"

# Verify certificate (check via AWS Console)
echo "Please verify the certificate via AWS Console"
echo "Add the DNS validation record to your domain"
```

### Route 53 DNS Configuration

```bash
# Create hosted zone
ZONE_ID=$(aws route53 create-hosted-zone \
  --name yourdomain.com \
  --caller-reference $(date +%s) \
  --query 'HostedZone.Id' --output text)

# Create record sets
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch file://route53-records.json
```

**route53-records.json:**
```json
{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "yourdomain.com",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "threatintel-alb.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": false,
          "HostedZoneId": "Z2FDTNDATAQYW2"
        }
      }
    },
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.yourdomain.com",
        "Type": "A",
        "AliasTarget": {
          "DNSName": "threatintel-alb.us-west-2.elb.amazonaws.com",
          "EvaluateTargetHealth": false,
          "HostedZoneId": "Z2FDTNDATAQYW2"
        }
      }
    }
  ]
}
```

---

## Monitoring Setup

### CloudWatch Metrics

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name "ThreatIntel-Platform" \
  --dashboard-body file://cloudwatch-dashboard.json
```

**cloudwatch-dashboard.json:**
```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/ECS", "CPUUtilization", "ServiceName", "threatintel-fastapi-service"],
          ["AWS/ECS", "MemoryUtilization", "ServiceName", "threatintel-fastapi-service"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "ECS CPU and Memory"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "threatintel-db"],
          ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "threatintel-db"]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-west-2",
        "title": "RDS Metrics"
      }
    }
  ]
}
```

### SNS Notifications

```bash
# Create SNS topic
TOPIC_ARN=$(aws sns create-topic \
  --name threatintel-alerts \
  --query 'TopicArn' --output text)

# Subscribe email
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint admin@yourdomain.com

# Create CloudWatch alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "ThreatIntel-High-CPU" \
  --alarm-description "Alarm when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions $TOPIC_ARN
```

---

## Backup Configuration

### S3 Backup Bucket

```bash
# Create S3 bucket
BACKUP_BUCKET="threatintel-backups-$(date +%s)"

aws s3 mb s3://$BACKUP_BUCKET \
  --region us-west-2

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BACKUP_BUCKET \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BACKUP_BUCKET \
  --server-side-encryption-configuration '{
    "Rules": [
      {
        "ApplyServerSideEncryptionByDefault": {
          "SSEAlgorithm": "AES256"
        }
      }
    ]
  }'

# Set lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket $BACKUP_BUCKET \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "DeleteOldBackups",
        "Status": "Enabled",
        "Filter": { "Prefix": "" },
        "Expiration": {
          "Days": 90
        },
        "Transitions": [
          {
            "Days": 30,
            "StorageClass": "STANDARD_IA"
          },
          {
            "Days": 60,
            "StorageClass": "GLACIER"
          }
        ]
      }
    ]
  }'

echo "Backup bucket: $BACKUP_BUCKET"
```

### Automated Backup Script

```bash
#!/bin/bash
# backup-aws.sh

# Environment variables
BACKUP_BUCKET="threatintel-backups-xxxx"
DB_INSTANCE="threatintel-db"
REDIS_CLUSTER="threatintel-redis-xxxx"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
echo "Starting PostgreSQL backup..."
aws rds create-db-snapshot \
  --db-instance-identifier $DB_INSTANCE \
  --db-snapshot-identifier "threatintel-snapshot-$DATE"

# Redis backup (manual snapshot)
echo "Creating Redis snapshot..."
aws elasticache create-snapshot \
  --cache-cluster-id $REDIS_CLUSTER \
  --snapshot-name "threatintel-redis-snapshot-$DATE"

# S3 sync of application data
echo "Syncing application data to S3..."
aws s3 sync /opt/data/postgres_timescaledb s3://$BACKUP_BUCKET/postgres/$DATE/
aws s3 sync /opt/data/mongodb s3://$BACKUP_BUCKET/mongodb/$DATE/
aws s3 sync /opt/data/redis s3://$BACKUP_BUCKET/redis/$DATE/

echo "Backup completed: $DATE"
```

### Lambda Function for Automated Backups

```python
# lambda_backup.py
import boto3
import json
from datetime import datetime

def lambda_handler(event, context):
    rds = boto3.client('rds')
    efs = boto3.client('efs')
    s3 = boto3.client('s3')
    
    date = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_bucket = 'threatintel-backups'
    
    # Create RDS snapshot
    try:
        snapshot = rds.create_db_snapshot(
            DBInstanceIdentifier='threatintel-db',
            DBSnapshotIdentifier=f'threatintel-snapshot-{date}'
        )
        print(f"RDS snapshot created: {snapshot['DBSnapshot']['DBSnapshotIdentifier']}")
    except Exception as e:
        print(f"Error creating RDS snapshot: {e}")
    
    # Sync data to S3
    try:
        # This would typically involve mounting EFS and syncing
        print(f"Data backup initiated for {date}")
    except Exception as e:
        print(f"Error syncing to S3: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps(f'Backup completed for {date}')
    }
```

---

## Security Configuration

### WAF Setup

```bash
# Create WAF Web ACL
WAF_ARN=$(aws wafv2 create-web-acl \
  --scope REGIONAL \
  --default-action Allow={} \
  --name threatintel-waf \
  --description "ThreatIntel WAF" \
  --rules file://waf-rules.json \
  --query 'Summary.ARN' --output text)

# Associate with CloudFront distribution
aws wafv2 associate-web-acl \
  --web-acl-arn $WAF_ARN \
  --resource-arn arn:aws:cloudfront::123456789012:distribution/xxxxxxxxxxxx
```

**waf-rules.json:**
```json
[
  {
    "Name": "AWSManagedRulesCommonRuleSet",
    "Priority": 1,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesCommonRuleSet"
      }
    },
    "OverrideAction": {
      "None": {}
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "ThreatIntel-Common"
    }
  },
  {
    "Name": "AWSManagedRulesKnownBadInputsRuleSet",
    "Priority": 2,
    "Statement": {
      "ManagedRuleGroupStatement": {
        "VendorName": "AWS",
        "Name": "AWSManagedRulesKnownBadInputsRuleSet"
      }
    },
    "OverrideAction": {
      "None": {}
    },
    "VisibilityConfig": {
      "SampledRequestsEnabled": true,
      "CloudWatchMetricsEnabled": true,
      "MetricName": "ThreatIntel-BadInputs"
    }
  }
]
```

### Secrets Manager

```bash
# Create secrets
aws secretsmanager create-secret \
  --name threatintel/db-password \
  --description "Database password for ThreatIntel" \
  --secret-string '{"password":"CHANGE_ME_SECURE_PASSWORD"}'

aws secretsmanager create-secret \
  --name threatintel/redis-password \
  --description "Redis password for ThreatIntel" \
  --secret-string '{"password":"CHANGE_ME_SECURE_REDIS_PASSWORD"}'

aws secretsmanager create-secret \
  --name threatintel/secret-key \
  --description "Application secret key" \
  --secret-string '{"key":"CHANGE_ME_TO_A_SECURE_32_CHARACTER_MINIMUM_SECRET_KEY"}'

# Create secret rotation
aws secretsmanager rotate-secret \
  --secret-id threatintel/db-password \
  --rotation-rules AutomaticallyAfterDays=90
```

### VPC Flow Logs

```bash
# Create IAM role for VPC Flow Logs
aws iam create-role \
  --role-name AWSVPCFlowLogsRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "vpc-flow-logs.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Create VPC Flow Logs
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $VPC_ID \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name VPCFlowLogs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/AWSVPCFlowLogsRole
```

---

## Cost Optimization

### Cost Breakdown (Monthly Estimates)

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| **EC2/EKS** | 3x t3.large | $150 - $250 |
| **RDS** | db.r5.large Multi-AZ | $200 - $300 |
| **ElastiCache** | cache.r5.large | $100 - $150 |
| **Load Balancer** | Application LB | $20 - $30 |
| **S3** | 500GB with lifecycle | $10 - $15 |
| **CloudFront** | 1TB transfer | $85 |
| **NAT Gateway** | 2x NAT in 2 AZ | $90 |
| **Data Transfer** | 1TB egress | $90 |
| **CloudWatch** | Custom metrics | $50 |
| **Backup Storage** | S3 + Glacier | $30 |
| **SSL Certificate** | ACM | Free |
| **Route 53** | DNS hosting | $50 |
| **WAF** | Basic rules | $30 |
| **Total** | | **$905 - $1,080** |

### Cost Optimization Strategies

#### 1. Reserved Instances

```bash
# Purchase Reserved Instance for RDS
aws rds purchase-reserved-db-instance-offering \
  --reserved-db-instance-offering-id db.r5.large-2yr \
  --db-instance-class db.r5.large \
  --duration-in-years 2 \
  --payment-option partial_upfront
```

#### 2. Spot Instances for Non-Production

```yaml
# Spot capacity allocation
nodeGroups:
  - name: spot-workers
    instanceTypes: ["t3.large", "m5.large", "c5.large"]
    spot: true
    capacityRebalance: true
    maxPrice: "0.10"
    minSize: 2
    maxSize: 10
    desiredCapacity: 3
```

#### 3. S3 Lifecycle Policies

```json
{
  "Rules": [
    {
      "ID": "ThreatIntelLifecycle",
      "Status": "Enabled",
      "Filter": { "Prefix": "" },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ]
    }
  ]
}
```

#### 4. Auto Scaling

```bash
# Configure ECS Service Auto Scaling
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/threatintel-cluster/threatintel-fastapi-service \
  --policy-name threatintel-cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 300,
    "ScaleInCooldown": 300
  }'
```

### Cost Monitoring

```bash
# Create cost budget
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "ThreatIntel-Monthly",
    "BudgetLimit": {
      "Amount": "1000",
      "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {
          "SubscriptionType": "EMAIL",
          "Address": "admin@yourdomain.com"
        }
      ]
    }
  ]'
```

---

## Troubleshooting

### Common Issues

#### 1. ECS Tasks Failing to Start

```bash
# Check ECS service events
aws ecs describe-services \
  --cluster threatintel-cluster \
  --services threatintel-fastapi-service \
  --query 'services[0].events'

# Check task definition
aws ecs describe-task-definition \
  --task-definition threatintel-fastapi

# View logs
aws logs get-log-events \
  --log-group-name /ecs/threatintel \
  --log-stream-name ecs/threatintel/fastapi/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
psql "postgresql://user:pass@host:5432/db" -c "SELECT 1;"

# Check security group rules
aws ec2 describe-security-groups \
  --group-ids sg-xxxxxxxxx

# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier threatintel-db
```

#### 3. Load Balancer Issues

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...

# Check ALB attributes
aws elbv2 describe-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:...
```

### Performance Optimization

#### 1. Database Performance

```sql
-- Monitor slow queries
SELECT query, calls, total_time, mean_time, stddev_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 20;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'threat_events';

-- Check connection pool usage
SELECT count(*) as current_connections,
       sum(numbackends) as total_backends
FROM pg_stat_database;
```

#### 2. Application Performance

```python
# Add to FastAPI application
from prometheus_client import Counter, Histogram

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request latency')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.observe(duration)
    return response
```

### Monitoring Dashboard

#### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "ThreatIntel AWS Monitoring",
    "panels": [
      {
        "title": "ECS CPU Utilization",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) by (container_label_com_amazonaws_ecs_container_name)",
            "legendFormat": "{{container_label_com_amazonaws_ecs_container_name}}"
          }
        ]
      },
      {
        "title": "RDS Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "aws_rds_database_connections",
            "legendFormat": "Connections"
          }
        ]
      },
      {
        "title": "ALB Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(aws_elbv2_request_count_sum[5m]))",
            "legendFormat": "Requests/sec"
          }
        ]
      }
    ]
  }
}
```

### Health Checks

```bash
#!/bin/bash
# health-check.sh

# Check ECS service health
ECS_STATUS=$(aws ecs describe-services \
  --cluster threatintel-cluster \
  --services threatintel-fastapi-service \
  --query 'services[0].runningCount' --output text)

if [ "$ECS_STATUS" -ge 3 ]; then
  echo "ECS Service: HEALTHY"
else
  echo "ECS Service: UNHEALTHY (Running: $ECS_STATUS)"
fi

# Check RDS status
RDS_STATUS=$(aws rds describe-db-instances \
  --db-instance-identifier threatintel-db \
  --query 'DBInstances[0].DBInstanceStatus' --output text)

echo "RDS Status: $RDS_STATUS"

# Check ALB health
TG_HEALTH=$(aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:us-west-2:123456789012:targetgroup/threatintel-tg/1234567890123456 \
  --query 'TargetHealthDescriptions[0].TargetHealth.State' --output text)

echo "Target Group Health: $TG_HEALTH"
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] AWS CLI configured
- [ ] IAM permissions granted
- [ ] Key pair created
- [ ] Domain name registered (optional)
- [ ] SSL certificate requested
- [ ] Secrets generated

### Infrastructure Setup
- [ ] VPC created
- [ ] Subnets configured (public + private)
- [ ] Internet Gateway attached
- [ ] NAT Gateways created
- [ ] Route Tables configured
- [ ] Security Groups created
- [ ] ECR repositories created

### Database Setup
- [ ] RDS PostgreSQL instance created
- [ ] ElastiCache Redis cluster created
- [ ] DB credentials stored in Secrets Manager
- [ ] Connection strings configured

### Application Deployment
- [ ] Docker images built
- [ ] Images pushed to ECR
- [ ] ECS task definitions created
- [ ] ECS services deployed
- [ ] Load Balancer configured
- [ ] Target Groups created
- [ ] Health checks passing

### SSL/TLS
- [ ] SSL certificate validated
- [ ] HTTPS listener configured
- [ ] HTTP to HTTPS redirect set
- [ ] Certificate bound to ALB

### Monitoring
- [ ] CloudWatch dashboard created
- [ ] Alarms configured
- [ ] SNS notifications set
- [ ] Log groups created
- [ ] VPC Flow Logs enabled

### Backup
- [ ] S3 backup bucket created
- [ ] Lifecycle policies configured
- [ ] Encryption enabled
- [ ] Backup scripts deployed
- [ ] Backup verification tested

### Security
- [ ] WAF configured
- [ ] Secrets Manager setup
- [ ] IAM roles created
- [ ] Security groups validated
- [ ] VPC Flow Logs enabled

### Testing
- [ ] Application health checks passing
- [ ] Database connectivity verified
- [ ] SSL certificate validated
- [ ] Load balancer routing tested
- [ ] Monitoring alerts tested
- [ ] Backup restore tested

### Post-Deployment
- [ ] DNS records configured (if using custom domain)
- [ ] CDN distribution created (optional)
- [ ] Performance testing completed
- [ ] Security scan performed
- [ ] Documentation updated
- [ ] Team access granted
- [ ] Monitoring dashboards verified

---

## Support and Maintenance

### Daily Tasks
- Review CloudWatch metrics
- Check application logs
- Verify backup completion
- Monitor costs
- Check security alerts

### Weekly Tasks
- Review performance metrics
- Update security patches
- Analyze cost reports
- Test alert notifications
- Review access logs

### Monthly Tasks
- Update dependencies
- Review security configurations
- Analyze usage trends
- Update documentation
- DR testing

### Quarterly Tasks
- Full disaster recovery test
- Security audit
- Performance optimization review
- Cost optimization analysis
- Architecture review

---

## Conclusion

This comprehensive AWS deployment guide provides multiple deployment options to suit different requirements and budgets. The ECS Fargate approach offers the best balance of simplicity and scalability, while EKS provides maximum control and flexibility. For smaller deployments or testing environments, the EC2 Docker Compose approach is most cost-effective.

Key benefits of this AWS deployment:
- **High Availability**: Multi-AZ deployments with automatic failover
- **Scalability**: Auto-scaling based on demand
- **Security**: Multiple layers of protection (WAF, Security Groups, VPC)
- **Cost Effective**: Pay-as-you-go pricing with optimization strategies
- **Reliability**: Automated backups and disaster recovery
- **Monitoring**: Comprehensive observability with CloudWatch and Prometheus

For additional support or customization, refer to the AWS documentation or contact the platform team.

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-30  
**Author**: Threat Intelligence Platform Team  
**Review Date**: 2026-10-30
