# Cybersecurity API - Monitoring & Observability Stack

A comprehensive monitoring and observability solution for cybersecurity APIs, featuring real-time metrics collection, alerting, log aggregation, and security event monitoring.

## 🏗️ Architecture Overview

The monitoring stack consists of the following components:

### Metrics Collection & Storage
- **Prometheus**: Time-series database for metrics collection
- **VictoriaMetrics**: Long-term metrics storage and retention
- **Node Exporter**: System-level metrics collection
- **Database Exporters**: PostgreSQL, MongoDB, Redis monitoring

### Visualization & Dashboards
- **Grafana**: Multi-dashboard visualization platform
- **Pre-built Dashboards**: API overview, database monitoring, threat intelligence
- **Alert Management**: Integrated alerting with Alertmanager

### Log Management (ELK Stack)
- **Elasticsearch**: Distributed search and analytics engine
- **Logstash**: Log processing and transformation pipeline
- **Kibana**: Log visualization and analysis interface
- **Filebeat**: Log shipping and collection agent

### Application Monitoring
- **Custom Metrics Collector**: Application-specific metrics
- **Threat Intelligence Monitor**: External threat feed monitoring
- **Security Monitor**: Security event detection and response
- **Kafka**: Message queue for high-volume log processing

### Alerting & Notification
- **Alertmanager**: Alert routing and notification management
- **Multiple Notification Channels**: Email, Slack, PagerDuty integration
- **Custom Alert Rules**: Database, application, security, and business alerts

## 📊 Dashboard Overview

### 1. System Overview Dashboard
- Real-time service status
- API request rates and response times
- Database connection metrics
- System resource utilization
- Active alerts overview

### 2. Database Monitoring Dashboard
- PostgreSQL instance status and connections
- MongoDB operations and performance
- Query performance metrics
- Disk usage and storage metrics
- Replication lag monitoring
- Connection pool utilization

### 3. Threat Intelligence Dashboard
- Threat feed status and health
- API quota usage tracking
- Detection rate monitoring
- Feed response times
- Validation throughput metrics
- Security event tracking

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM (for Elasticsearch)
- Network access for external APIs

### Installation

1. **Clone and navigate to monitoring directory:**
   ```bash
   cd monitoring/
   ```

2. **Update configuration files:**
   - Edit `configs/threat-feeds.yml` with your API keys
   - Modify database connection strings in docker-compose.yml
   - Update Alertmanager configuration in `alertmanager/alertmanager.yml`

3. **Start the monitoring stack:**
   ```bash
   docker-compose up -d
   ```

4. **Access the dashboards:**
   - Grafana: http://localhost:3000 (admin/admin123)
   - Prometheus: http://localhost:9090
   - Alertmanager: http://localhost:9093
   - Elasticsearch: http://localhost:9200
   - Kibana: http://localhost:5601

### Configuration

#### Prometheus Configuration
- **Location**: `prometheus/prometheus.yml`
- **Alert Rules**: `prometheus/rules.yml`
- **Targets**: Configured for automatic service discovery

#### Alertmanager Configuration
- **Location**: `alertmanager/alertmanager.yml`
- **Notification Channels**: Email, Slack, PagerDuty
- **Routing**: Severity-based alert routing

#### Grafana Dashboards
- **Location**: `grafana/dashboards/`
- **Data Sources**: `grafana/datasources/`
- **Auto-provisioning**: Dashboard configuration in `dashboard-config.yml`

#### ELK Stack
- **Elasticsearch**: `elk/elasticsearch/elasticsearch.yml`
- **Logstash**: `elk/logstash/logstash.conf` and `elk/logstash/logstash.yml`
- **Kibana**: `elk/kibana/kibana.yml`
- **Filebeat**: `elk/filebeat/filebeat.yml`

## 📈 Metrics Collected

### System Metrics
- CPU, Memory, Disk utilization
- Network traffic and error rates
- Process and service status

### Database Metrics
- PostgreSQL: Connections, query performance, replication lag
- MongoDB: Operations, connections, replica set health
- Redis: Memory usage, key operations, slow queries

### Application Metrics
- API request rates and response times
- Error rates by endpoint and status code
- Validation throughput and success rates
- Custom business metrics

### Security Metrics
- Failed login attempts and patterns
- Suspicious API activity detection
- Threat intelligence feed status
- Security event tracking and correlation

### Threat Intelligence Metrics
- Feed health and response times
- API quota usage monitoring
- Threat detection rates
- Feed freshness and updates

## 🔔 Alert Rules

### Critical Alerts
- Database instance down
- High API error rates (>5%)
- Security breaches detected
- Threat feed failures

### Warning Alerts
- High database connection usage (>80%)
- API response time degradation
- Low disk space
- Threat feed staleness

### Business Alerts
- API quota usage thresholds
- Unusual traffic patterns
- Performance degradation

## 🔧 Customization

### Adding New Metrics
1. Update `scripts/metrics_collector.py`
2. Add Prometheus metrics definitions
3. Update Prometheus scrape configuration
4. Create Grafana dashboard panels

### Adding New Alert Rules
1. Edit `prometheus/rules.yml`
2. Define alert conditions and thresholds
3. Add alert annotations and labels
4. Update Alertmanager routing if needed

### Adding New Threat Feeds
1. Update `configs/threat-feeds.yml`
2. Implement feed integration in `scripts/threat_intel_monitor.py`
3. Add monitoring metrics for the feed
4. Update dashboards with new visualizations

## 📊 Log Analysis

### Kibana Dashboards
- **Security Events**: Authentication failures, suspicious activities
- **API Logs**: Request patterns, error analysis
- **Threat Intelligence**: Feed logs, detection events
- **System Logs**: Application and infrastructure logs

### Log Patterns
- Structured JSON logging with consistent fields
- Geolocation enrichment for IP addresses
- Security event tagging and categorization
- Threat intelligence correlation

## 🔒 Security Considerations

### Access Control
- Grafana authentication and authorization
- Elasticsearch security features
- Prometheus basic authentication (optional)
- Network isolation via Docker networks

### Data Protection
- Encrypted communication between components
- Secure credential management
- Log sanitization and data masking
- Audit trail maintenance

### Monitoring Security
- API rate limiting monitoring
- Suspicious activity detection
- Automated IP blocking for threats
- Security event correlation

## 🛠️ Maintenance

### Regular Tasks
- Monitor disk usage and cleanup old data
- Update threat feed API keys
- Review and tune alert thresholds
- Backup Prometheus and Grafana data

### Performance Tuning
- Elasticsearch heap size adjustment
- Prometheus retention period optimization
- Log rotation and compression settings
- Database connection pool tuning

### Health Checks
- Automated service health monitoring
- Feed status verification
- Database performance monitoring
- Alert delivery confirmation

## 📚 Resources

### Documentation
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Logstash Reference](https://www.elastic.co/guide/en/logstash/)

### API Integration
- Configure threat intelligence API keys
- Set up custom application metrics
- Implement log shipping from applications
- Enable alerting integrations

## 🤝 Support

For issues and questions:
1. Check component-specific logs
2. Review configuration files
3. Consult component documentation
4. Contact monitoring team

## 📄 License

This monitoring stack is provided as-is for cybersecurity API monitoring purposes.

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Maintained by**: Cybersecurity Team