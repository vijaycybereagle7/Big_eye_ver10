# Big Eye Security Database

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Build Status](https://github.com/your-org/cybersecurity-database-system/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/cybersecurity-database-system/actions)
[![Security Rating](https://img.shields.io/badge/security-A+-green.svg)](https://github.com/your-org/cybersecurity-database-system/security)

A comprehensive, enterprise-grade cybersecurity database system that aggregates, analyzes, and correlates threat intelligence from multiple sources. This system provides real-time threat detection, anomaly detection, and intelligent security analysis for modern cybersecurity operations.

## 🚀 Features

### Core Capabilities
- **Multi-Source Threat Intelligence**: Integrates with 12+ threat intelligence sources including AbuseIPDB, GreyNoise, OTX, VirusTotal, Shodan, and more
- **Real-Time Data Processing**: Stream processing for real-time threat detection and alerting
- **Advanced Analytics**: Machine learning-powered anomaly detection, pattern recognition, and NLP processing
- **Scalable Architecture**: Built for high-availability, horizontally scalable cloud deployments
- **RESTful API**: FastAPI-based API with comprehensive endpoints for all operations
- **Database Flexibility**: Support for PostgreSQL, MongoDB, and Redis for different data needs
- **Security Compliance**: GDPR, CCPA, and SOC2 compliant data handling
- **Monitoring & Observability**: Built-in monitoring, alerting, and performance metrics

### Threat Intelligence Sources
- **AbuseIPDB**: IP reputation and abuse reports
- **GreyNoise**: Internet-wide scan detection and noise filtering
- **OTX (AlienVault)**: Open threat intelligence sharing
- **VirusTotal**: File, URL, domain, and IP analysis
- **Shodan**: Internet-connected device search engine
- **SecurityTrails**: DNS, IP, and domain intelligence
- **PhishTank**: Phishing database
- **URLhaus**: Malware URL database
- **Spamhaus**: Anti-spam and threat intelligence
- **Safe Browsing**: Google's phishing/malware protection
- **MalwareBazaar**: Malware sample database
- **CIRCL Hash Lookup**: File hash analysis

### AI/ML Components
- **Anomaly Detection**: Statistical and ML-based anomaly detection for threat identification
- **Pattern Recognition**: Advanced pattern matching for threat correlation
- **NLP Processing**: Natural language processing for security logs and reports
- **Reputation Scoring**: ML-powered reputation scoring for IPs, domains, and files

### Security & Compliance
- **Encryption**: End-to-end encryption for data at rest and in transit
- **Access Control**: Role-based access control (RBAC) with fine-grained permissions
- **Audit Logging**: Comprehensive audit trails for all system operations
- **Data Protection**: GDPR, CCPA, and SOC2 compliant data handling
- **Vulnerability Management**: Automated vulnerability scanning and remediation tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                        │
├─────────────────────────────────────────────────────────────┤
│  FastAPI REST API  │  WebSocket  │  GraphQL  │  Prometheus │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Threat Intelligence  │  AI/ML Engine  │  Security Engine  │
│      Collectors       │     (NLP, ML)    │  (Compliance)     │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  MongoDB  │  Redis  │  Elasticsearch  │ Neo4j │
│ (Structured) │(Documents)│ (Cache) │   (Logs)        │ (Graph)│
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                      │
├─────────────────────────────────────────────────────────────┤
│  Docker    │  Kubernetes  │  Cloud Services  │ Monitoring  │
│   Stack    │     Orch     │   (AWS/Azure)    │ & Alerting  │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- Docker and Docker Compose
- PostgreSQL 14+ / MongoDB 5.0+
- Redis 6.0+
- Git

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/your-org/cybersecurity-database-system.git
cd cybersecurity-database-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start with Docker Compose**
```bash
docker-compose up -d
```

6. **Initialize the database**
```bash
python scripts/init_database.py
```

7. **Run the application**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Manual Installation

#### Database Setup

**PostgreSQL:**
```bash
# Create database
createdb cyber_security_db

# Run migrations
python database/postgresql/migrate.py
```

**MongoDB:**
```bash
# Start MongoDB service
sudo systemctl start mongod

# Initialize collections
python scripts/init_mongodb.py
```

**Redis:**
```bash
# Start Redis
redis-server
```

#### Application Setup

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
pip install -r api/requirements.txt
pip install -r ai_ml/anomaly_detection/requirements.txt
pip install -r ai_ml/nlp/requirements.txt
pip install -r ai_ml/pattern_recognition/requirements.txt
```

2. **Install threat intelligence collector dependencies**
```bash
pip install -r threat_intelligence/collection/requirements.txt
```

3. **Configure API keys**
```bash
# Copy template configuration
cp threat_intelligence/collection/threat_intel_config.json.template \
   threat_intelligence/collection/threat_intel_config.json

# Edit with your API keys
vim threat_intelligence/collection/threat_intel_config.json
```

4. **Initialize the system**
```bash
python scripts/initialize_system.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/cyber_security_db
MONGO_URI=mongodb://localhost:27017/cyber_security
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET=your-jwt-secret

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Threat Intelligence APIs
ABUSEIPDB_API_KEY=your-abuseipdb-key
GREYNOISE_API_KEY=your-greynoise-key
OTX_API_KEY=your-otx-key
VIRUSTOTAL_API_KEY=your-virustotal-key
SHODAN_API_KEY=your-shodan-key
SECURITYTRAILS_API_KEY=your-securitytrails-key

# Monitoring
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ELASTICSEARCH_URL=http://localhost:9200

# Security & Compliance
GDPR_COMPLIANCE=true
AUDIT_LOGGING=true
ENCRYPTION_ENABLED=true

# Development
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### API Configuration

Configure API endpoints and rate limits in `api/config/settings.py`:

```python
class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Cybersecurity Database System"
    
    # Database settings
    DATABASE_URL: str = "postgresql://..."
    MONGO_URI: str = "mongodb://..."
    REDIS_URL: str = "redis://..."
    
    # Security settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Threat intelligence
    ABUSEIPDB_API_KEY: Optional[str] = None
    GREYNOISE_API_KEY: Optional[str] = None
    # ... other API keys
```

## 📚 Usage Examples

### Basic API Usage

#### Start Threat Intelligence Collection

```python
import asyncio
from threat_intelligence.collection.threat_intel_manager import ThreatIntelligenceManager

async def collect_threats():
    manager = ThreatIntelligenceManager()
    await manager.initialize()
    
    # Collect from all sources
    results = await manager.collect_all_sources()
    print(f"Collected {len(results)} threat indicators")

asyncio.run(collect_threats())
```

#### Query Threat Intelligence

```python
import requests

# Query IP reputation
response = requests.get(
    "http://localhost:8000/api/v1/threat-intel/ip/192.168.1.1",
    headers={"Authorization": "Bearer your-token"}
)
print(response.json())

# Query domain reputation
response = requests.get(
    "http://localhost:8000/api/v1/threat-intel/domain/malicious-domain.com",
    headers={"Authorization": "Bearer your-token"}
)
print(response.json())
```

#### Anomaly Detection

```python
from ai_ml.anomaly_detection.example_usage import AnomalyDetector

# Initialize detector
detector = AnomalyDetector()

# Detect anomalies in network traffic
traffic_data = {
    "src_ip": "192.168.1.100",
    "dst_ip": "8.8.8.8",
    "protocol": "TCP",
    "port": 80,
    "bytes_sent": 1024000,
    "duration": 300
}

anomalies = detector.detect(traffic_data)
print(f"Detected {len(anomalies)} anomalies")
```

#### NLP Processing

```python
from ai_ml.nlp.nlp_processor import SecurityNLPProcessor

# Initialize NLP processor
nlp = SecurityNLPProcessor()

# Process security log text
log_text = "Suspicious login attempt from IP 192.168.1.100, failed authentication"
result = nlp.analyze_security_text(log_text)
print(result)
# Output: {'entities': [...], 'sentiment': 'negative', 'severity': 'high'}
```

### Advanced Usage

#### Custom Threat Intelligence Collector

```python
from threat_intelligence.collection.base_collector import BaseCollector

class CustomCollector(BaseCollector):
    def __init__(self):
        super().__init__("custom_api")
        self.api_key = "your-api-key"
    
    async def collect_indicators(self):
        # Custom collection logic
        data = await self.fetch_from_api()
        return self.normalize_data(data)
    
    def normalize_data(self, data):
        # Normalize to standard format
        return {
            "indicator_type": "ip",
            "value": data["ip"],
            "reputation_score": data["score"],
            "source": "custom_api",
            "tags": data.get("tags", []),
            "timestamp": datetime.utcnow()
        }

# Use the custom collector
collector = CustomCollector()
results = await collector.collect_indicators()
```

#### Real-time Threat Monitoring

```python
import asyncio
import websockets

async def monitor_threats():
    uri = "ws://localhost:8000/ws/threats"
    
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"action": "subscribe", "type": "high_severity"}))
        
        while True:
            threat = await websocket.recv()
            print(f"New high-severity threat: {threat}")
            # Process threat (alert, block, etc.)

asyncio.run(monitor_threats())
```

#### Database Operations

```python
from database.postgresql.connection import get_db_connection

async def query_threats():
    conn = await get_db_connection()
    
    # Query recent high-severity threats
    results = await conn.fetch("""
        SELECT indicator_type, value, severity_score, first_seen, last_seen
        FROM threat_indicators 
        WHERE severity_score > 7
        ORDER BY last_seen DESC
        LIMIT 100
    """)
    
    for row in results:
        print(f"{row['indicator_type']}: {row['value']} (Score: {row['severity_score']})")

asyncio.run(query_threats())
```

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r testing/requirements.txt

# Run all tests
python -m pytest testing/ -v

# Run with coverage
python -m pytest testing/ --cov=app --cov=ai_ml --cov=threat_intelligence

# Generate HTML coverage report
python -m pytest testing/ --cov=app --cov=ai_ml --cov=threat_intelligence --html=reports/coverage.html
```

### Run Specific Test Categories

```bash
# Unit tests
python -m pytest testing/unit/ -v

# Integration tests
python -m pytest testing/integration/ -v

# Load tests
python -m pytest testing/load/ -v

# Run performance tests
python -m pytest testing/performance/ -v
```

### Custom Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = testing
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=app
    --cov=ai_ml
    --cov=threat_intelligence
    --cov-report=term-missing
    --cov-report=html:reports/coverage
    --cov-report=xml:reports/coverage.xml
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    load: marks tests as load tests
    unit: marks tests as unit tests
```

## 🚢 Deployment

### Docker Deployment

#### Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Scale services
docker-compose -f docker-compose.dev.yml up -d --scale api=3
```

#### Production

```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# With TLS
docker-compose -f docker-compose.prod.yml -f docker-compose.tls.yml up -d
```

### Kubernetes Deployment

```bash
# Apply all manifests
kubectl apply -f deployment/kubernetes/manifests/

# Deploy with Helm
helm install cybersecurity-db deployment/kubernetes/helm/

# Scale deployments
kubectl scale deployment api --replicas=5
```

### Cloud Deployment

#### AWS

```bash
# Deploy to AWS EKS
./deployment/scripts/deploy-aws.sh production

# With monitoring
./deployment/scripts/deploy-aws.sh production --monitoring
```

#### Azure

```bash
# Deploy to Azure AKS
./deployment/scripts/deploy-azure.sh production

# With security
./deployment/scripts/deploy-azure.sh production --security
```

#### GCP

```bash
# Deploy to GCP GKE
./deployment/scripts/deploy-gcp.sh production

# With compliance
./deployment/scripts/deploy-gcp.sh production --compliance
```

### Monitoring Setup

```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.yml up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# AlertManager: http://localhost:9093
# Kibana: http://localhost:5601
```

## 📊 API Documentation

### Interactive API Docs

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core API Endpoints

#### Threat Intelligence

- `GET /api/v1/threat-intel/ip/{ip}` - Get IP reputation
- `GET /api/v1/threat-intel/domain/{domain}` - Get domain reputation
- `GET /api/v1/threat-intel/hash/{hash}` - Get file hash reputation
- `POST /api/v1/threat-intel/bulk` - Bulk reputation check
- `GET /api/v1/threat-intel/sources` - List available sources
- `POST /api/v1/threat-intel/sources/{source}/collect` - Trigger collection

#### Validation

- `POST /api/v1/validate/email` - Validate email address
- `POST /api/v1/validate/url` - Validate URL
- `POST /api/v1/validate/ip` - Validate IP address
- `POST /api/v1/validate/hash` - Validate file hash
- `POST /api/v1/validate/phone` - Validate phone number

#### Reputation

- `GET /api/v1/reputation/ip/{ip}` - Get IP reputation score
- `GET /api/v1/reputation/domain/{domain}` - Get domain reputation
- `GET /api/v1/reputation/email/{email}` - Get email reputation
- `GET /api/v1/reputation/file/{hash}` - Get file reputation

#### Analytics

- `POST /api/v1/analytics/anomaly-detect` - Detect anomalies
- `POST /api/v1/analytics/pattern-match` - Pattern matching
- `POST /api/v1/analytics/nlp-analyze` - NLP analysis
- `GET /api/v1/analytics/reports` - Generate reports

#### Admin

- `GET /api/v1/admin/health` - System health check
- `GET /api/v1/admin/metrics` - System metrics
- `POST /api/v1/admin/config` - Update configuration
- `GET /api/v1/admin/logs` - Access logs

### API Authentication

All API endpoints require authentication using JWT tokens:

```python
import requests

# Login to get token
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "your-username",
    "password": "your-password"
})
token = response.json()["access_token"]

# Use token in requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/threat-intel/ip/1.1.1.1", headers=headers)
```

## 🔒 Security

### Security Features

- **Encryption**: AES-256 encryption for data at rest and TLS 1.3 for data in transit
- **Authentication**: JWT-based authentication with refresh tokens
- **Authorization**: Role-based access control (RBAC) with fine-grained permissions
- **Rate Limiting**: Configurable rate limiting per user/IP
- **Input Validation**: Comprehensive input validation and sanitization
- **Audit Logging**: Complete audit trails for all operations
- **Vulnerability Scanning**: Automated security vulnerability scanning
- **Container Security**: Hardened Docker containers with security scanning

### Security Best Practices

1. **Environment Variables**: Never commit API keys or secrets to version control
2. **Network Security**: Use VPCs, security groups, and firewalls
3. **Database Security**: Enable SSL connections and use connection pooling
4. **API Security**: Implement rate limiting and request validation
5. **Monitoring**: Monitor for suspicious activities and security events
6. **Updates**: Keep all dependencies updated and patched
7. **Backup**: Regular encrypted backups of all critical data

### Security Compliance

This system implements security controls for:
- **GDPR**: General Data Protection Regulation compliance
- **CCPA**: California Consumer Privacy Act compliance
- **SOC2**: Service Organization Control 2 compliance
- **ISO 27001**: Information Security Management
- **NIST**: Cybersecurity Framework alignment

## 📈 Performance

### Performance Features

- **Caching**: Multi-level caching with Redis
- **Database Optimization**: Query optimization and indexing strategies
- **Horizontal Scaling**: Kubernetes-based auto-scaling
- **Load Balancing**: Nginx load balancing
- **CDN Integration**: CloudFlare CDN for static assets
- **Asynchronous Processing**: Async/await for I/O operations
- **Connection Pooling**: Database connection pooling

### Performance Tuning

```python
# Database connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30

# Redis caching configuration
REDIS_POOL_SIZE = 10
REDIS_MAX_CONNECTIONS = 100

# API rate limiting
RATE_LIMIT_REQUESTS = 1000
RATE_LIMIT_WINDOW = 60  # seconds
```

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues

```bash
# Check database connectivity
python scripts/test_db_connection.py

# Reset database connections
python scripts/reset_db_connections.py

# Check database status
sudo systemctl status postgresql
sudo systemctl status mongod
sudo systemctl status redis
```

#### API Issues

```bash
# Check API logs
docker-compose logs -f api

# Test API endpoints
curl -X GET http://localhost:8000/health

# Check authentication
curl -H "Authorization: Bearer your-token" http://localhost:8000/admin/metrics
```

#### Performance Issues

```bash
# Monitor system resources
htop
iotop
nethogs

# Check database performance
python scripts/check_db_performance.py

# Analyze slow queries
python scripts/analyze_slow_queries.py
```

### Log Analysis

```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log

# Search for specific errors
grep "ERROR" logs/app.log | head -20

# Monitor in real-time
tail -f logs/app.log | grep -E "(ERROR|WARN|CRITICAL)"
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
# Set debug environment
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and follow our code of conduct.

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python -m pytest testing/`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Development Guidelines

#### Code Style

- **Python**: Follow PEP 8 with Black formatter
- **Documentation**: Comprehensive docstrings for all functions
- **Type Hints**: Use type hints for all functions
- **Testing**: Write tests for all new features
- **Security**: Follow security best practices

```bash
# Format code
black *.py ai_ml/ api/ threat_intelligence/
isort *.py ai_ml/ api/ threat_intelligence/

# Lint code
flake8 *.py ai_ml/ api/ threat_intelligence/
mypy *.py ai_ml/ api/ threat_intelligence/

# Security scan
bandit -r *.py ai_ml/ api/ threat_intelligence/
```

#### Commit Messages

Follow conventional commits:

```
type(scope): description

feat(api): add new threat intelligence endpoint
fix(database): resolve connection pooling issue
docs(readme): update installation instructions
test(ml): add unit tests for anomaly detection
security(api): implement rate limiting
```

#### Pull Request Process

1. Update documentation for any new features
2. Add tests for new functionality
3. Ensure all tests pass
4. Update the CHANGELOG.md
5. Request review from maintainers

### Contribution Areas

We especially welcome contributions in:

- **New Threat Intelligence Sources**: Add integrations with additional threat feeds
- **Machine Learning Models**: Improve AI/ML capabilities
- **Security Enhancements**: Strengthen security controls
- **Performance Optimization**: Improve system performance
- **Documentation**: Enhance documentation and examples
- **Testing**: Expand test coverage
- **User Interface**: Build web dashboard and visualization tools

### Code Review Process

All contributions undergo:
1. **Automated Testing**: CI/CD pipeline runs all tests
2. **Security Review**: Automated security scanning
3. **Code Review**: Maintainers review code quality
4. **Documentation Review**: Check documentation completeness
5. **Performance Review**: Evaluate performance impact

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Threat intelligence providers: AbuseIPDB, GreyNoise, OTX, VirusTotal, Shodan
- Open source libraries: FastAPI, SQLAlchemy, PyMongo, Redis, Pandas, Scikit-learn
- Community contributors and security researchers

## 📞 Support

### Getting Help

- **Documentation**: [https://cybersecurity-db.readthedocs.io](https://cybersecurity-db.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/your-org/cybersecurity-database-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/cybersecurity-database-system/discussions)
- **Security**: Email security@yourorg.com for security-related issues

### Professional Support

For enterprise support, training, and consulting:
- Email: enterprise@yourorg.com
- Website: https://yourorg.com/cybersecurity
- Documentation: https://docs.yourorg.com/cybersecurity

## 📋 Roadmap

### Upcoming Features

#### Short Term (3-6 months)
- [ ] Web dashboard for threat visualization
- [ ] Additional threat intelligence sources integration
- [ ] Enhanced ML models for threat prediction
- [ ] Real-time alerting system
- [ ] Graph database integration (Neo4j)

#### Medium Term (6-12 months)
- [ ] Machine learning pipeline automation
- [ ] Advanced correlation engine
- [ ] Multi-tenant architecture
- [ ] API rate limiting and throttling
- [ ] Enhanced compliance reporting

#### Long Term (12+ months)
- [ ] Cloud-native deployment options
- [ ] Advanced threat hunting capabilities
- [ ] Integration with SIEM systems
- [ ] Mobile applications
- [ ] Advanced analytics and reporting

### Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history and updates.

---

**Made with ❤️ by the Cybersecurity Team**

*For security updates and announcements, please watch this repository and subscribe to our security mailing list.*