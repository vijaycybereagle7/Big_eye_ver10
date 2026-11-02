# Deployment & Infrastructure Configuration

Comprehensive deployment and infrastructure configuration for the Big Eye Security Database, supporting both Docker Compose and Kubernetes deployments with automated backups, monitoring, and disaster recovery capabilities.

## 🏗️ Architecture Overview

### Services Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   FastAPI App   │    │  Celery Workers │
│     (Nginx)     │────│                 │────│                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Redis       │    │ PostgreSQL +    │    │     MongoDB     │
│    (Cache)      │    │   TimescaleDB   │    │   (Logs/Events) │
│                 │    │  (Time Series)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │     Grafana     │    │    ELK Stack    │
│  (Monitoring)   │    │  (Dashboards)   │    │(Logging/Analysis)│
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 Directory Structure

```
deployment/
├── docker/                      # Docker Compose Configuration
│   ├── docker-compose.yml       # Main compose file
│   ├── .env.template           # Environment template
│   └── config/                 # Service configurations
│       ├── nginx/              # Nginx configuration
│       ├── postgres/           # PostgreSQL + TimescaleDB
│       ├── mongodb/            # MongoDB
│       ├── redis/              # Redis
│       ├── prometheus/         # Prometheus
│       ├── grafana/            # Grafana
│       ├── logstash/           # Logstash
│       └── alertmanager/       # Alertmanager
├── kubernetes/                 # Kubernetes Configuration
│   ├── helm/                   # Helm Charts
│   │   └── threatintel-platform/
│   │       ├── Chart.yaml
│   │       ├── values.yaml
│   │       └── templates/      # Kubernetes templates
│   └── manifests/              # Raw Kubernetes manifests
├── backup/                     # Backup & Recovery
│   ├── scripts/               # Backup scripts
│   │   ├── postgres_backup.sh
│   │   ├── mongodb_backup.sh
│   │   ├── redis_backup.sh
│   │   └── restore.sh
│   └── templates/             # Backup configurations
├── scripts/                   # Deployment Scripts
│   ├── deploy.sh              # Main deployment script
│   └── setup.sh               # Setup utilities
├── docs/                      # Documentation
│   ├── disaster_recovery_plan.md
│   ├── backup_strategy.md
│   └── deployment_guide.md
└── config/                    # Shared configurations
```

## 🚀 Quick Start

### Docker Compose Deployment

1. **Prepare Environment:**
   ```bash
   cd deployment/docker
   cp .env.template .env
   # Edit .env with your configuration
   ```

2. **Deploy:**
   ```bash
   chmod +x ../scripts/deploy.sh
   ../scripts/deploy.sh --type docker-compose --env development
   ```

3. **Access Services:**
   - Application: http://localhost
   - API Documentation: http://localhost/docs
   - Grafana: http://localhost:3000
   - Prometheus: http://localhost:9090
   - Kibana: http://localhost:5601

### Kubernetes Deployment

1. **Prerequisites:**
   ```bash
   # Install kubectl, helm, and configure cluster access
   kubectl cluster-info
   ```

2. **Deploy:**
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh --type kubernetes --env production
   ```

3. **Access Services:**
   ```bash
   # Port-forward to access services
   kubectl port-forward -n threatintel-platform svc/threatintel-platform-fastapi 8000:8000
   kubectl port-forward -n threatintel-platform svc/threatintel-platform-grafana 3000:3000
   ```

## 🔧 Configuration

### Environment Variables

Key environment variables (see `.env.template`):

```bash
# Database Configuration
POSTGRES_DB=threatintel
POSTGRES_USER=threatintel_user
POSTGRES_PASSWORD=secure_password_here

MONGO_INITDB_DATABASE=threatintel_logs
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=secure_password_here

REDIS_PASSWORD=secure_password_here

# Security
SECRET_KEY=your_very_secure_secret_key_here_minimum_32_characters

# Monitoring
GRAFANA_ADMIN_PASSWORD=secure_password_here

# Backup Configuration
BACKUP_RETENTION_DAYS=30
S3_BACKUP_BUCKET=threatintel-backups
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### Service Configuration

#### PostgreSQL + TimescaleDB
- **Port:** 5432
- **Database:** threatintel
- **Features:** WAL archiving, point-in-time recovery
- **Configuration:** `config/postgres/postgresql.conf`

#### MongoDB
- **Port:** 27017
- **Database:** threatintel_logs
- **Features:** Authentication, oplog replication
- **Configuration:** `config/mongodb/mongod.conf`

#### Redis
- **Port:** 6379
- **Features:** Authentication, persistence (RDB + AOF)
- **Configuration:** `config/redis/redis.conf`

#### FastAPI Application
- **Port:** 8000
- **Features:** Health checks, metrics endpoint, API documentation
- **Autoscaling:** Enabled (3-10 replicas)

#### Celery Workers
- **Features:** Task processing, metrics endpoint
- **Autoscaling:** Enabled (2-8 replicas)
- **Beat Scheduler:** Included

#### Nginx Load Balancer
- **Ports:** 80, 443
- **Features:** SSL termination, rate limiting, health checks
- **Configuration:** `config/nginx/`

## 📊 Monitoring & Logging

### Monitoring Stack
- **Prometheus:** Metrics collection
- **Grafana:** Dashboards and alerting
- **Alertmanager:** Alert routing and escalation

### Logging Stack (ELK)
- **Elasticsearch:** Log storage and search
- **Logstash:** Log processing and filtering
- **Kibana:** Log visualization

### Key Metrics Monitored
- Database performance (connections, queries, replication)
- Application performance (response time, error rates)
- System resources (CPU, memory, disk)
- Network metrics (latency, throughput)

### Alert Rules
- Critical service downtime
- High error rates (>5%)
- Resource utilization (>80%)
- Database connectivity issues
- Security incidents

## 💾 Backup & Recovery

### Backup Strategy

#### PostgreSQL + TimescaleDB
- **Frequency:** Daily full backup, WAL archiving every 5 minutes
- **Retention:** 30 days local, 90 days in S3
- **Recovery:** Point-in-time recovery supported
- **Script:** `backup/scripts/postgres_backup.sh`

#### MongoDB
- **Frequency:** Daily full backup, oplog every 10 minutes
- **Retention:** 30 days local, 90 days in S3
- **Recovery:** Point-in-time recovery via oplog
- **Script:** `backup/scripts/mongodb_backup.sh`

#### Redis
- **Frequency:** Daily RDB snapshot, AOF continuous
- **Retention:** 7 days local, 30 days in S3
- **Recovery:** Automatic from RDB or AOF
- **Script:** `backup/scripts/redis_backup.sh`

### Point-in-Time Recovery (PITR)
- **PostgreSQL:** WAL archiving with recovery target time
- **MongoDB:** Oplog replay to specific timestamp
- **RPO Target:** < 15 minutes

### Restore Procedures
```bash
# Full restore
./backup/scripts/restore.sh postgres s3://bucket/backup.tar.gz '2024-01-01 12:00:00'

# Database-specific restore
./backup/scripts/restore.sh mongodb /local/backup.tar.gz '2024-01-01 12:00:00'
./backup/scripts/restore.sh redis /local/backup.tar.gz
```

## 🔄 Disaster Recovery

### Recovery Objectives
- **RTO (Recovery Time Objective):** < 1 hour
- **RPO (Recovery Point Objective):** < 15 minutes

### Disaster Recovery Plan
See `docs/disaster_recovery_plan.md` for detailed procedures including:
- Database corruption response
- Infrastructure failure recovery
- Security incident handling
- Communication plans
- Testing procedures

### DR Testing
- **Monthly:** Database recovery tests
- **Quarterly:** Full DR simulation
- **Annually:** Complete business continuity test

## 🔐 Security

### Network Security
- **Network Policies:** Restrict inter-service communication
- **Firewall Rules:** Limit external access
- **SSL/TLS:** Encryption in transit
- **VPN Access:** Secure remote access

### Data Security
- **Encryption at Rest:** Database encryption enabled
- **Encryption in Transit:** TLS for all services
- **Access Control:** Role-based permissions
- **Audit Logging:** Comprehensive audit trail

### Monitoring Security
- **Intrusion Detection:** Security event monitoring
- **Vulnerability Scanning:** Regular security scans
- **Compliance:** GDPR, SOC2, ISO27001 compliance
- **Incident Response:** Automated security response

## 🏃‍♂️ Kubernetes Features

### Autoscaling
- **Horizontal Pod Autoscaler:** Automatic scaling based on metrics
- **Vertical Pod Autoscaler:** Resource optimization
- **Cluster Autoscaler:** Node scaling

### High Availability
- **Pod Disruption Budgets:** Maintain minimum available instances
- **Health Checks:** Liveness and readiness probes
- **Rolling Updates:** Zero-downtime deployments
- **Blue-Green Deployments:** Safe deployment strategy

### Storage
- **Persistent Volumes:** Data persistence across pod restarts
- **Storage Classes:** Different storage tiers
- **Volume Snapshots:** Point-in-time volume backups
- **Dynamic Provisioning:** Automatic volume creation

### Service Mesh (Optional)
- **Istio:** Advanced traffic management
- **Envoy:** Proxy and load balancing
- **Circuit Breaking:** Fault tolerance
- **Observability:** Distributed tracing

## 📈 Performance Optimization

### Database Optimization
- **PostgreSQL:** Connection pooling, query optimization
- **MongoDB:** Indexing, sharding configuration
- **Redis:** Memory management, data structure optimization

### Application Optimization
- **Caching:** Multi-level caching strategy
- **Load Balancing:** Distribute traffic efficiently
- **Database Connections:** Connection pooling
- **Async Processing:** Celery for background tasks

### Monitoring Performance
- **Prometheus:** Metrics collection
- **Grafana:** Real-time dashboards
- **Alerting:** Proactive issue detection
- **Logging:** Structured logging with ELK

## 🔧 Maintenance

### Regular Maintenance Tasks
- **Backup Verification:** Daily backup integrity checks
- **Log Rotation:** Prevent disk space issues
- **Database Maintenance:** VACUUM, reindexing
- **Security Updates:** Regular patch management

### Upgrade Procedures
- **Rolling Updates:** Zero-downtime upgrades
- **Database Migrations:** Version-compatible migrations
- **Configuration Updates:** Hot reload capabilities
- **Monitoring:** Post-upgrade validation

## 🛠️ Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database status
pg_isready -h postgres-timescaledb -p 5432
mongosh --host mongodb --port 27017 --eval "db.adminCommand('ping')"
redis-cli ping
```

#### Service Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Service status
docker-compose ps
kubectl get pods -n threatintel-platform
```

#### Log Analysis
```bash
# View service logs
docker-compose logs -f fastapi-app
kubectl logs -f deployment/threatintel-platform-fastapi -n threatintel-platform

# ELK Stack
# Access Kibana at http://localhost:5601
```

### Performance Issues
- Check resource utilization (CPU, memory, disk)
- Monitor database query performance
- Review application logs for errors
- Verify network connectivity

## 📚 Additional Resources

### Documentation
- [Disaster Recovery Plan](docs/disaster_recovery_plan.md)
- [Backup Strategy](docs/backup_strategy.md)
- [Deployment Guide](docs/deployment_guide.md)

### Configuration Examples
- [Nginx Configuration](config/nginx/)
- [Database Configurations](config/postgres/, config/mongodb/, config/redis/)
- [Monitoring Setup](config/prometheus/, config/grafana/)

### Scripts Reference
- [Deployment Script](scripts/deploy.sh)
- [Backup Scripts](backup/scripts/)
- [Maintenance Scripts](scripts/)

## 🤝 Support

### Getting Help
- **Documentation:** Check docs/ directory
- **Logs:** Check application and system logs
- **Monitoring:** Use Grafana dashboards
- **Community:** GitHub issues for bug reports

### Contributing
1. Fork the repository
2. Create feature branch
3. Follow coding standards
4. Add tests for new features
5. Submit pull request

---

**Version:** 1.0.0  
**Last Updated:** $(date +%Y-%m-%d)  
**Maintained by:** ThreatIntel Platform Team