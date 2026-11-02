# Disaster Recovery Plan
## Threat Intelligence Platform

**Version:** 1.0  
**Date:** $(date +%Y-%m-%d)  
**RTO Target:** < 1 hour  
**RPO Target:** < 15 minutes  

---

## Executive Summary

This disaster recovery plan outlines the procedures and strategies for recovering the Threat Intelligence Platform in the event of a disaster or major service disruption. The plan is designed to achieve a Recovery Time Objective (RTO) of less than 1 hour and a Recovery Point Objective (RPO) of less than 15 minutes.

---

## 1. Recovery Objectives

### 1.1 Recovery Time Objective (RTO)
- **Target:** < 1 hour
- **Definition:** Maximum acceptable time to restore full service functionality
- **Components:**
  - Infrastructure provisioning: 15 minutes
  - Database restoration: 30 minutes
  - Application deployment: 10 minutes
  - Service verification: 5 minutes

### 1.2 Recovery Point Objective (RPO)
- **Target:** < 15 minutes
- **Definition:** Maximum acceptable data loss measured in time
- **Components:**
  - PostgreSQL with TimescaleDB: WAL archiving (5-minute intervals)
  - MongoDB: Oplog-based replication
  - Redis: RDB snapshots with AOF

---

## 2. Backup Strategy

### 2.1 Automated Backups

#### PostgreSQL + TimescaleDB
- **Frequency:** Daily full backup, WAL archiving every 5 minutes
- **Retention:** 30 days local, 90 days in S3
- **Backup Types:**
  - Base backup (pg_basebackup): Weekly
  - Transaction log (WAL) archiving: Continuous
  - Point-in-time recovery: Supported
- **Storage:**
  - Local: `/opt/backups/postgres`
  - Remote: `s3://threatintel-backups/postgres/`

#### MongoDB
- **Frequency:** Daily full backup, oplog every 10 minutes
- **Retention:** 30 days local, 90 days in S3
- **Backup Types:**
  - Full database dump (mongodump): Daily
  - Oplog backup: Continuous
  - Point-in-time recovery: Supported via oplog
- **Storage:**
  - Local: `/opt/backups/mongodb`
  - Remote: `s3://threatintel-backups/mongodb/`

#### Redis
- **Frequency:** Daily RDB backup, AOF continuous
- **Retention:** 7 days local, 30 days in S3
- **Backup Types:**
  - RDB snapshot: Daily at 2 AM
  - AOF file: Continuous
- **Storage:**
  - Local: `/opt/backups/redis`
  - Remote: `s3://threatintel-backups/redis/`

### 2.2 Backup Verification
- **Automated Verification:** Every backup verified within 1 hour
- **Test Restores:** Monthly test restores to verify backup integrity
- **Monitoring:** All backups monitored via Prometheus + Grafana

---

## 3. Disaster Scenarios and Response

### 3.1 Database Corruption

#### PostgreSQL Corruption
**Detection:**
- Health checks failing
- Database queries timing out
- PostgreSQL logs showing errors

**Response:**
1. **Immediate (0-15 minutes):**
   - Stop application connections
   - Identify corrupted objects
   - Assess backup availability

2. **Short-term (15-30 minutes):**
   - Restore from latest consistent backup
   - Replay WAL files to point of failure
   - Verify data integrity

3. **Recovery (30-60 minutes):**
   - Restore full service
   - Validate application functionality
   - Monitor for performance issues

**Tools:**
- `pg_basebackup` for base restoration
- `pg_restore` for point-in-time recovery
- WAL archiving for continuous recovery

#### MongoDB Corruption
**Detection:**
- MongoDB instance unresponsive
- Data directory corruption
- Replica set failures

**Response:**
1. **Immediate (0-15 minutes):**
   - Switch to backup replica if available
   - Assess extent of corruption
   - Check oplog availability

2. **Short-term (15-30 minutes):**
   - Restore from latest backup
   - Replay oplog operations
   - Validate collection integrity

3. **Recovery (30-60 minutes):**
   - Restore full service
   - Verify replica set functionality
   - Monitor application connectivity

**Tools:**
- `mongodump`/`mongorestore` for full restoration
- Oplog replay for point-in-time recovery

### 3.2 Complete Infrastructure Failure

**Detection:**
- All services down
- Network connectivity issues
- Physical server failure

**Response:**
1. **Assessment (0-15 minutes):**
   - Determine scope of failure
   - Check disaster recovery site
   - Validate backup availability

2. **Infrastructure Provisioning (15-30 minutes):**
   - Deploy new infrastructure (Docker/Kubernetes)
   - Configure networking and storage
   - Provision load balancers

3. **Data Restoration (30-50 minutes):**
   - Restore databases from backups
   - Configure application connections
   - Set up monitoring and logging

4. **Service Validation (50-60 minutes):**
   - Verify all services operational
   - Test application functionality
   - Monitor system performance

**Tools:**
- Infrastructure as Code (Terraform/Ansible)
- Docker Compose/Kubernetes manifests
- Backup restoration scripts

### 3.3 Security Incident

**Detection:**
- Unauthorized access
- Data breach
- Malware infection
- System compromise

**Response:**
1. **Immediate (0-15 minutes):**
   - Isolate affected systems
   - Preserve forensic evidence
   - Change all passwords and keys
   - Activate incident response team

2. **Containment (15-30 minutes):**
   - Rebuild compromised systems
   - Restore from clean backups
   - Update security configurations
   - Scan for malware/artifacts

3. **Recovery (30-60 minutes):**
   - Deploy clean systems
   - Implement additional security measures
   - Monitor for continued threats
   - Document incident details

**Security Measures:**
- Encrypted backups
- Network segmentation
- Access control policies
- Security monitoring

---

## 4. Recovery Procedures

### 4.1 Pre-Recovery Checklist

- [ ] **Incident Assessment**
  - [ ] Determine scope and impact
  - [ ] Identify affected services
  - [ ] Check backup availability
  - [ ] Verify RTO/RPO requirements

- [ ] **Resource Preparation**
  - [ ] Allocate recovery resources
  - [ ] Prepare disaster recovery site
  - [ ] Coordinate team availability
  - [ ] Update stakeholder status

### 4.2 Database Recovery Procedures

#### PostgreSQL Recovery
```bash
#!/bin/bash
# PostgreSQL Disaster Recovery Script

# Configuration
BACKUP_FILE="${1:-}"
RESTORE_TIME="${2:-}"
PGHOST="${PGHOST:-postgres-timescaledb}"
PGUSER="${PGUSER:-threatintel_user}"
PGDATABASE="${PGDATABASE:-threatintel}"

echo "Starting PostgreSQL disaster recovery..."

# Stop application
docker stop fastapi-app celery-worker celery-beat

# Stop PostgreSQL
docker stop postgres-timescaledb

# Remove corrupted data
rm -rf /opt/data/postgres_timescaledb/*

# Create new data directory
mkdir -p /opt/data/postgres_timescaledb
chown postgres:postgres /opt/data/postgres_timescaledb

# Restore from backup
if [ -n "$BACKUP_FILE" ]; then
    if [[ "$BACKUP_FILE" == s3://* ]]; then
        # Download from S3
        aws s3 cp "$BACKUP_FILE" /tmp/backup.tar.gz
        BACKUP_FILE="/tmp/backup.tar.gz"
    fi
    
    # Extract and restore
    tar -xzf "$BACKUP_FILE" -C /tmp/
    cp -r /tmp/threatintel_postgres_base_*/* /opt/data/postgres_timescaledb/
fi

# Start PostgreSQL
docker start postgres-timescaledb

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if pg_isready -h "$PGHOST" -p 5432 -U "$PGUSER"; then
        echo "PostgreSQL is ready"
        break
    fi
    sleep 2
done

# Point-in-time recovery if specified
if [ -n "$RESTORE_TIME" ]; then
    echo "Performing point-in-time recovery to: $RESTORE_TIME"
    
    # Configure recovery.conf
    cat > /opt/data/postgres_timescaledb/postgresql.auto.conf << EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '$RESTORE_TIME'
recovery_target_timeline = 'latest'
EOF
    
    # Restart PostgreSQL
    docker restart postgres-timescaledb
    
    # Wait for recovery
    echo "Waiting for recovery to complete..."
    for i in {1..60}; do
        if ! docker exec postgres-timescaledb psql -U postgres -c "SELECT pg_is_in_recovery();" | grep -q t; then
            echo "Recovery completed"
            break
        fi
        sleep 5
    done
fi

# Verify database
echo "Verifying database integrity..."
pg_isready -h "$PGHOST" -p 5432 -U "$PGUSER" -d "$PGDATABASE"

# Start application
docker start fastapi-app celery-worker celery-beat

echo "PostgreSQL disaster recovery completed"
```

#### MongoDB Recovery
```bash
#!/bin/bash
# MongoDB Disaster Recovery Script

BACKUP_FILE="${1:-}"
MONGO_HOST="${MONGO_HOST:-mongodb}"
MONGO_USER="${MONGO_USER:-admin}"
MONGO_PASSWORD="${MONGO_PASSWORD:-}"
MONGO_AUTH_DB="${MONGO_AUTH_DB:-admin}"
MONGO_DATABASE="${MONGO_DATABASE:-threatintel_logs}"

echo "Starting MongoDB disaster recovery..."

# Stop application
docker stop fastapi-app celery-worker celery-beat

# Stop MongoDB
docker stop mongodb

# Remove corrupted data
rm -rf /opt/data/mongodb/*

# Create new data directory
mkdir -p /opt/data/mongodb
chown mongodb:mongodb /opt/data/mongodb

# Restore from backup
if [ -n "$BACKUP_FILE" ]; then
    if [[ "$BACKUP_FILE" == s3://* ]]; then
        # Download from S3
        aws s3 cp "$BACKUP_FILE" /tmp/backup.tar.gz
        BACKUP_FILE="/tmp/backup.tar.gz"
    fi
    
    # Extract backup
    tar -xzf "$BACKUP_FILE" -C /tmp/
    
    # Restore data
    mongorestore --host "$MONGO_HOST" --port 27017 \
        --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
        --authenticationDatabase "$MONGO_AUTH_DB" \
        --db "$MONGO_DATABASE" \
        "/tmp/threatintel_mongodb_*/*/"
fi

# Start MongoDB
docker start mongodb

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
for i in {1..30}; do
    if mongosh --host "$MONGO_HOST" --port 27017 \
        --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
        --authenticationDatabase "$MONGO_AUTH_DB" \
        --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        echo "MongoDB is ready"
        break
    fi
    sleep 2
done

# Verify database
echo "Verifying database integrity..."
mongosh --host "$MONGO_HOST" --port 27017 \
    --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
    --authenticationDatabase "$MONGO_AUTH_DB" \
    --eval "db.$MONGO_DATABASE.stats()" --quiet

# Start application
docker start fastapi-app celery-worker celery-beat

echo "MongoDB disaster recovery completed"
```

#### Redis Recovery
```bash
#!/bin/bash
# Redis Disaster Recovery Script

BACKUP_FILE="${1:-}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

echo "Starting Redis disaster recovery..."

# Stop application
docker stop fastapi-app celery-worker celery-beat

# Stop Redis
docker stop redis

# Remove corrupted data
rm -rf /opt/data/redis/*

# Restore from backup
if [ -n "$BACKUP_FILE" ]; then
    if [[ "$BACKUP_FILE" == s3://* ]]; then
        # Download from S3
        aws s3 cp "$BACKUP_FILE" /tmp/backup.tar.gz
        BACKUP_FILE="/tmp/backup.tar.gz"
    fi
    
    # Extract backup
    tar -xzf "$BACKUP_FILE" -C /tmp/
    
    # Find RDB file
    RDB_FILE=$(find /tmp -name "*.rdb" | head -1)
    
    if [ -n "$RDB_FILE" ]; then
        cp "$RDB_FILE" /opt/data/redis/dump.rdb
    fi
fi

# Start Redis
docker start redis

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
for i in {1..30}; do
    if redis-cli -h "$REDIS_HOST" -p 6379 ping >/dev/null 2>&1; then
        echo "Redis is ready"
        break
    fi
    sleep 2
done

# Verify Redis
echo "Verifying Redis integrity..."
KEY_COUNT=$(redis-cli -h "$REDIS_HOST" -p 6379 DBSIZE)
echo "Redis key count: $KEY_COUNT"

# Start application
docker start fastapi-app celery-worker celery-beat

echo "Redis disaster recovery completed"
```

### 4.3 Application Recovery Procedures

#### Kubernetes Deployment Recovery
```bash
#!/bin/bash
# Kubernetes Application Recovery

NAMESPACE="${NAMESPACE:-threatintel-platform}"
RELEASE_NAME="${RELEASE_NAME:-threatintel}"

echo "Starting Kubernetes application recovery..."

# Check cluster connectivity
kubectl cluster-info
kubectl get nodes

# Delete existing deployments
kubectl delete deployment -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME

# Wait for pods to be terminated
kubectl wait --for=delete pod -l app.kubernetes.io/instance=$RELEASE_NAME -n $NAMESPACE --timeout=300s

# Deploy from Helm chart
helm upgrade --install $RELEASE_NAME ./deployment/kubernetes/helm/threatintel-platform \
    --namespace $NAMESPACE \
    --create-namespace \
    --values ./deployment/kubernetes/helm/threatintel-platform/values-production.yaml \
    --timeout 600s

# Wait for deployments to be ready
kubectl rollout status deployment/$RELEASE_NAME-fastapi -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/$RELEASE_NAME-celery-worker -n $NAMESPACE --timeout=600s
kubectl rollout status deployment/$RELEASE_NAME-celery-beat -n $NAMESPACE --timeout=600s

# Verify services
kubectl get services -n $NAMESPACE
kubectl get ingress -n $NAMESPACE

# Check application health
kubectl get pods -n $NAMESPACE

echo "Kubernetes application recovery completed"
```

### 4.4 Post-Recovery Validation

#### Health Check Script
```bash
#!/bin/bash
# Post-Recovery Health Check

echo "=== Starting Post-Recovery Health Check ==="

# Check all services are running
echo "Checking service status..."
docker-compose ps

# Check database connectivity
echo "Checking PostgreSQL..."
pg_isready -h postgres-timescaledb -p 5432 -U threatintel_user -d threatintel

echo "Checking MongoDB..."
mongosh --host mongodb --port 27017 --username admin \
    --password "$MONGO_ROOT_PASSWORD" \
    --authenticationDatabase admin \
    --eval "db.adminCommand('ping')" --quiet

echo "Checking Redis..."
redis-cli -h redis -p 6379 ping

# Check application endpoints
echo "Checking FastAPI health..."
curl -f http://localhost:8000/health || echo "FastAPI health check failed"

# Check monitoring
echo "Checking Prometheus..."
curl -f http://localhost:9090/-/healthy || echo "Prometheus health check failed"

echo "Checking Grafana..."
curl -f http://localhost:3000/api/health || echo "Grafana health check failed"

echo "=== Post-Recovery Health Check Completed ==="
```

---

## 5. Communication Plan

### 5.1 Incident Response Team
- **Incident Commander:** [Name] - [Contact]
- **Database Administrator:** [Name] - [Contact]
- **DevOps Engineer:** [Name] - [Contact]
- **Security Team:** [Name] - [Contact]
- **Management:** [Name] - [Contact]

### 5.2 Communication Channels
- **Primary:** Slack #incident-response
- **Secondary:** Email incident@threatintel.com
- **Escalation:** Phone calls
- **External:** Status page updates

### 5.3 Stakeholder Notifications
- **Immediate (0-15 minutes):** Incident response team
- **15-30 minutes:** Management and key stakeholders
- **30-60 minutes:** All users and external parties
- **Post-recovery:** Summary report to all stakeholders

---

## 6. Testing and Maintenance

### 6.1 DR Testing Schedule
- **Monthly:** Database recovery tests
- **Quarterly:** Full disaster recovery simulation
- **Annually:** Complete business continuity test

### 6.2 Testing Procedures
1. **Test Database Restores**
   - Restore from latest backup
   - Verify data integrity
   - Measure recovery time
   - Document results

2. **Infrastructure Recovery**
   - Deploy to clean environment
   - Test automation scripts
   - Validate monitoring
   - Performance testing

3. **Full DR Simulation**
   - Simulate complete failure
   - Execute full recovery process
   - Measure RTO/RPO compliance
   - Identify improvements

### 6.3 Plan Maintenance
- **Review frequency:** Semi-annually
- **Update triggers:** Major system changes
- **Version control:** Git repository
- **Approval process:** Technical review + Management sign-off

---

## 7. Risk Assessment

### 7.1 High-Risk Scenarios
1. **Database Corruption:** Medium probability, High impact
2. **Complete Infrastructure Failure:** Low probability, High impact
3. **Security Breach:** Medium probability, Critical impact
4. **Network Failure:** Medium probability, Medium impact

### 7.2 Mitigation Strategies
1. **Regular Backups:** Automated, encrypted, off-site
2. **Geographic Distribution:** Multi-region deployment
3. **Security Monitoring:** 24/7 SIEM and alerting
4. **Redundancy:** Load balancers, database replicas

---

## 8. Emergency Contacts

### 8.1 Internal Contacts
- **Incident Commander:** [Phone] [Email]
- **Database Team:** [Phone] [Email]
- **Infrastructure Team:** [Phone] [Email]
- **Security Team:** [Phone] [Email]

### 8.2 External Contacts
- **Cloud Provider Support:** [Phone] [Email]
- **Backup Service Provider:** [Phone] [Email]
- **Internet Service Provider:** [Phone] [Email]
- **Hardware Vendors:** [Phone] [Email]

---

## 9. Appendices

### 9.1 System Architecture Diagrams
- Current architecture
- Disaster recovery architecture
- Network topology

### 9.2 Backup Inventory
- Complete list of backups
- Retention schedules
- Storage locations
- Recovery procedures

### 9.3 Configuration Files
- Database configurations
- Application configurations
- Network configurations
- Monitoring configurations

### 9.4 Recovery Scripts
- Database recovery scripts
- Application deployment scripts
- Validation scripts
- Monitoring setup scripts

---

**Document Control:**
- **Author:** ThreatIntel Team
- **Reviewers:** Database Team, DevOps Team, Security Team
- **Approval:** CTO, CISO
- **Next Review:** $(date -d "+6 months" +%Y-%m-%d)
- **Distribution:** Incident Response Team, Management, All Staff