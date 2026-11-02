# Big Eye Security Database API

A comprehensive FastAPI-based Big Eye Security Database validation and threat intelligence platform that provides email, domain, IP, URL, and sender validation with integrated threat intelligence and reputation analysis.

## Features

### 🔐 Authentication & Security
- API Key authentication (X-API-Key or Bearer token)
- Rate limiting with configurable limits per endpoint
- Admin-only endpoints for key management
- Secure HTTP headers and CORS support

### ✅ Validation Services
- **Email Validation**: Syntax, MX records, disposable detection, role accounts
- **Domain Validation**: DNS resolution, WHOIS data, parked domain detection
- **IP Validation**: Format validation, geolocation, proxy/VPN detection
- **URL Validation**: Accessibility checks, safety analysis, reputation
- **Sender Validation**: SPF, DKIM, DMARC authentication checks
- **Bulk Validation**: Process multiple items concurrently

### 🕵️ Reputation Intelligence
- Multi-source reputation aggregation
- VirusTotal, AbuseIPDB, Shodan, GreyNoise, OTX integration
- Weighted confidence scoring
- Real-time and cached results

### 🚨 Threat Intelligence
- Comprehensive threat analysis
- Multiple threat intelligence sources
- Context and relationship analysis
- Historical data and trends
- Threat categorization and severity scoring

### 📊 Admin Dashboard
- Real-time system statistics
- API key management
- System health monitoring
- Cache performance metrics
- Usage analytics and reporting

### 🏗️ Architecture
- PostgreSQL for structured data storage
- MongoDB for logs and flexible documents
- Redis for high-performance caching
- Async/await throughout for scalability
- Microservice-ready architecture

## Quick Start

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd api
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**:
   ```bash
   # PostgreSQL and MongoDB should be running
   # The application will auto-create tables and indexes on startup
   ```

4. **Start the API**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Basic Usage

1. **Get an API Key** (for development):
   ```
   Default keys are pre-configured:
   - Default: default-api-key-123
   - Admin: admin-api-key-456
   ```

2. **Make a Request**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/validate/email" \\
     -H "X-API-Key: default-api-key-123" \\
     -H "Content-Type: application/json" \\
     -d '{"email": "user@example.com"}'
   ```

## API Documentation

### Authentication

All endpoints require authentication using one of these methods:

**Header Method (Recommended)**:
```
X-API-Key: your-api-key-here
```

**Bearer Method**:
```
Authorization: Bearer your-api-key-here
```

### Rate Limits

| Endpoint Type | Requests | Window |
|--------------|----------|--------|
| Standard | 100 | 60 seconds |
| Admin | 1000 | 60 seconds |
| Bulk Operations | 10 | 60 seconds |

### Validation Endpoints

#### Email Validation
```http
POST /api/v1/validate/email
Content-Type: application/json
X-API-Key: your-api-key

{
  "email": "user@example.com",
  "verify_syntax": true,
  "verify_mx_record": true,
  "check_disposable": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Email validation completed",
  "result": {
    "value": "user@example.com",
    "is_valid": true,
    "confidence_score": 0.95,
    "domain_exists": true,
    "mx_record_exists": true,
    "is_disposable": false,
    "is_role_account": false,
    "is_trash": false,
    "suggestions": []
  }
}
```

#### Domain Validation
```http
POST /api/v1/validate/domain
Content-Type: application/json

{
  "domain": "example.com",
  "check_dns": true,
  "check_whois": false,
  "check_reputation": true
}
```

#### IP Validation
```http
POST /api/v1/validate/ip
Content-Type: application/json

{
  "ip_address": "192.168.1.1",
  "check_reputation": true,
  "check_geolocation": true
}
```

#### URL Validation
```http
POST /api/v1/validate/url
Content-Type: application/json

{
  "url": "https://example.com",
  "check_safety": true,
  "check_reputation": true,
  "follow_redirects": true
}
```

#### Sender Validation
```http
POST /api/v1/validate/sender
Content-Type: application/json

{
  "email": "user@example.com",
  "domain": "example.com",
  "check_spf": true,
  "check_dkim": true,
  "check_dmarc": true
}
```

#### Bulk Validation
```http
POST /api/v1/validate/bulk
Content-Type: application/json

{
  "emails": ["user1@example.com", "user2@example.com"],
  "domains": ["example.com", "test.com"],
  "ip_addresses": ["1.1.1.1", "8.8.8.8"]
}
```

### Reputation Endpoints

#### Query Reputation
```http
POST /api/v1/reputation/query
Content-Type: application/json

{
  "value": "8.8.8.8",
  "value_type": "ip",
  "sources": ["virustotal", "abuseipdb"],
  "detailed": true
}
```

#### Batch Reputation
```http
POST /api/v1/reputation/batch
Content-Type: application/json

[
  {"value": "8.8.8.8", "value_type": "ip"},
  {"value": "example.com", "value_type": "domain"}
]
```

### Threat Intelligence Endpoints

#### Query Threat Intelligence
```http
POST /api/v1/threats/query
Content-Type: application/json

{
  "value": "8.8.8.8",
  "query_type": "ip",
  "include_context": true,
  "include_related": true,
  "time_range_days": 30
}
```

#### Search Threat Indicators
```http
POST /api/v1/threats/search
Content-Type: application/json

{
  "query": "malware",
  "filters": {
    "indicator_types": ["ip", "domain"],
    "time_range_days": 30,
    "min_confidence": 0.7
  },
  "page": 1,
  "page_size": 20
}
```

### Admin Endpoints

#### Get Dashboard
```http
GET /api/v1/admin/dashboard
Authorization: Bearer admin-api-key-456
```

#### Create API Key
```http
POST /api/v1/admin/api-keys
Content-Type: application/json

{
  "name": "Production Service",
  "is_admin": false,
  "rate_limit": 500
}
```

#### System Health
```http
GET /api/v1/admin/health
Authorization: Bearer admin-api-key-456
```

## Configuration

### Environment Variables

```bash
# Application
APP_NAME="Cybersecurity Validation API"
APP_VERSION="1.0.0"
DEBUG=false
SECRET_KEY="your-secret-key"

# Database
POSTGRESQL_URL="postgresql://user:password@localhost/cybersec_db"
MONGODB_URL="mongodb://localhost:27017"
MONGODB_DATABASE="cybersec_db"

# Redis
REDIS_URL="redis://localhost:6379/0"

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
RATE_LIMIT_ADMIN_REQUESTS=1000

# External API Keys
VIRUSTOTAL_API_KEY="your-virustotal-key"
ABUSEIPDB_API_KEY="your-abuseipdb-key"
SHODAN_API_KEY="your-shodan-key"
GREYNOISE_API_KEY="your-greynoise-key"
OTX_API_KEY="your-otx-key"
SECURITYTRAILS_API_KEY="your-securitytrails-key"

# Cache Settings
CACHE_ENABLED=true
CACHE_TTL_DEFAULT=300
CACHE_TTL_SHORT=60
CACHE_TTL_LONG=86400
```

### API Key Management

**Default API Keys**:
- **Default Key**: `default-api-key-123` (Standard user)
- **Admin Key**: `admin-api-key-456` (Full access)

**Creating New Keys** (Admin only):
```http
POST /api/v1/admin/api-keys
Authorization: Bearer admin-api-key-456

{
  "name": "My Application",
  "is_admin": false,
  "rate_limit": 1000
}
```

**Response**:
```json
{
  "success": true,
  "message": "API key created successfully",
  "api_key": "generated-api-key-here",
  "key_info": {
    "key_id": "key_20231201_143022",
    "name": "My Application",
    "is_admin": false,
    "created_at": "2023-12-01T14:30:22Z",
    "rate_limit": 1000
  }
}
```

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "success": false,
  "message": "Error description",
  "error": {
    "error_code": "ERROR_CODE",
    "error_message": "Human-readable error message",
    "details": {
      "additional_context": "optional details"
    }
  },
  "timestamp": "2023-12-01T14:30:22Z"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `HTTP_401` | 401 | Authentication required |
| `HTTP_403` | 403 | Insufficient permissions |
| `HTTP_429` | 429 | Rate limit exceeded |
| `VALIDATION_ERROR` | 422 | Invalid request parameters |
| `INTERNAL_ERROR` | 500 | Internal server error |

## Caching Strategy

The API implements a multi-tier caching strategy:

### Cache Levels
1. **Redis Cache**: Frequently accessed data (default TTL: 5 minutes)
2. **Short-term Cache**: Quick lookups (TTL: 1 minute)
3. **Long-term Cache**: Expensive operations (TTL: 24 hours)

### Cache Keys
- Validation: `cybersec:email:hash` 
- Reputation: `cybersec:reputation:type:value`
- Threat Intel: `cybersec:threat_intel:type:value`

### Cache Headers
```http
X-Cache-Status: HIT|MISS
X-Cache-TTL: 300
```

## Performance Considerations

### Async Operations
- All validation operations are async
- Concurrent external API calls
- Non-blocking database operations

### Rate Limiting
- Per-API key rate limiting
- Burst protection
- Sliding window algorithm

### Connection Pooling
- PostgreSQL connection pooling
- Redis connection pooling
- HTTP connection pooling for external APIs

## Monitoring and Logging

### Structured Logging
```json
{
  "timestamp": "2023-12-01T14:30:22Z",
  "level": "INFO",
  "logger": "api.routers.validation",
  "message": "Email validation completed",
  "api_key": "key_123",
  "endpoint": "/validate/email",
  "processing_time_ms": 250,
  "success": true
}
```

### Metrics
- Request/response times
- Cache hit rates
- External API performance
- Database query performance
- Rate limiting statistics

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - POSTGRESQL_URL=postgresql://postgres:password@postgres:5432/cybersec_db
      - MONGODB_URL=mongodb://mongo:27017
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - mongo
      - redis

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=cybersec_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  mongo:
    image: mongo:6
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  mongo_data:
  redis_data:
```

### Production Deployment

1. **Environment Setup**:
   ```bash
   export DEBUG=false
   export SECRET_KEY="your-production-secret"
   export DATABASE_URLS="your-production-urls"
   ```

2. **Database Migration**:
   ```bash
   alembic upgrade head
   ```

3. **Run with Gunicorn**:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Categories

- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing  
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- **Type Hints**: All functions should have type hints
- **Docstrings**: Comprehensive docstrings for all functions
- **Error Handling**: Proper exception handling and logging
- **Testing**: Unit tests for new features
- **Documentation**: Update documentation for changes

### Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Add changelog entry
4. Request review from maintainers

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Support

- **Documentation**: Available at `/docs` endpoint
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Security**: Report security issues privately

## Roadmap

### Upcoming Features
- [ ] GraphQL API support
- [ ] WebSocket real-time updates  
- [ ] Machine learning threat detection
- [ ] Advanced analytics dashboard
- [ ] Multi-tenancy support
- [ ] Plugin architecture
- [ ] Kubernetes deployment manifests
- [ ] Monitoring and alerting integration

### Version History
- **v1.0.0**: Initial release with core validation and reputation features
- **v1.1.0**: Added threat intelligence and advanced admin features
- **v1.2.0**: Performance improvements and expanded threat feeds