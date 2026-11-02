# Vercel-Optimized Big Eye Security Database API

A serverless-optimized version of the comprehensive Big Eye Security Database validation system, designed for deployment on Vercel with Supabase integration.

## Features

### ✅ Implemented Components

- **Email Validation**: Syntax, domain, MX records, disposable detection
- **Domain Validation**: Format, DNS resolution, WHOIS data, suspicious TLD detection
- **IP Validation**: Format, type detection, private/reserved IP identification
- **URL Validation**: Format, protocol checking, suspicious pattern detection
- **Reputation Analysis**: Multi-source threat intelligence with scoring
- **Threat Intelligence**: Basic threat lookup and statistics
- **Supabase Integration**: Replaces PostgreSQL/MongoDB for data storage
- **Serverless Optimization**: Optimized for Vercel's serverless constraints

### ⚠️ Removed Components (Serverless Constraints)

- PostgreSQL database (replaced with Supabase)
- MongoDB database (replaced with Supabase) 
- Redis caching (replaced with Supabase-based caching)
- Celery background workers (removed - not suitable for serverless)
- Complex rate limiting (simplified for serverless)
- Heavy ML/AI processing (removed for performance)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Serverless                       │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   FastAPI App   │  │   API Handlers  │                   │
│  │   (Serverless)  │  │                 │                   │
│  └─────────────────┘  └─────────────────┘                   │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Supabase Database                      │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │validation_  │ │reputation_  │ │   api_      │   │   │
│  │  │   logs      │ │   logs      │ │   cache     │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             External APIs (Optional)                │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │VirusTotal  │ │ AbuseIPDB   │ │   Other     │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Guide

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Supabase Account**: Sign up at [supabase.com](https://supabase.com)
3. **API Keys**: Prepare API keys for optional external services

### 1. Supabase Setup

1. Create a new Supabase project
2. Get your project URL and anon key from Settings > API
3. Create the required tables in your Supabase database:

```sql
-- Create cache table
CREATE TABLE api_cache (
    cache_key TEXT PRIMARY KEY,
    cached_data JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_api_cache_expires_at ON api_cache(expires_at);

-- Create validation logs table
CREATE TABLE validation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create reputation logs table
CREATE TABLE reputation_logs (
    id BIGSERIAL PRIMARY KEY,
    endpoint TEXT NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    processing_time_ms FLOAT NOT NULL,
    api_key TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. Environment Variables

Configure these environment variables in Vercel:

**Required:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anon/public key
- `SECRET_KEY`: Secret key for API authentication

**Optional (Enhanced Features):**
- `VIRUSTOTAL_API_KEY`: For enhanced threat intelligence
- `ABUSEIPDB_API_KEY`: For IP reputation data
- `SHODAN_API_KEY`: For network scanning data
- `GREYNOISE_API_KEY`: For threat hunting
- `OTX_API_KEY`: For threat intelligence feeds

### 3. Deploy to Vercel

#### Method 1: Vercel CLI
```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project directory
cd vercel_app

# Deploy
vercel

# Follow the prompts to configure your project
```

#### Method 2: Git Integration
1. Push your code to GitHub/GitLab/Bitbucket
2. Connect your repository to Vercel
3. Configure environment variables in Vercel dashboard
4. Deploy automatically

### 4. API Key Configuration

Update the `VALID_API_KEYS` configuration in `app/config/settings.py`:

```python
VALID_API_KEYS: Dict[str, Dict[str, Any]] = {
    "default": {"key": "your-api-key-here", "name": "Default API Key", "admin": False},
    "admin": {"key": "your-admin-key-here", "name": "Admin API Key", "admin": True}
}
```

## API Usage

### Base URL
```
https://your-app.vercel.app/
```

### Authentication
Include your API key in the request header:
```
Authorization: Bearer your-api-key-here
```

### Endpoints

#### Validation Endpoints

**Email Validation**
```bash
POST /api/v1/validate/email
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "email": "user@example.com",
  "verify_syntax": true,
  "verify_mx_record": false,
  "check_disposable": true
}
```

**Domain Validation**
```bash
POST /api/v1/validate/domain
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "domain": "example.com"
}
```

**IP Validation**
```bash
POST /api/v1/validate/ip
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "ip": "8.8.8.8"
}
```

**URL Validation**
```bash
POST /api/v1/validate/url
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "url": "https://example.com"
}
```

**Bulk Validation**
```bash
POST /api/v1/validate/bulk
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "items": ["user@example.com", "test@domain.com"],
  "validation_type": "email",
  "async_mode": false
}
```

#### Reputation Endpoints

**Query Reputation**
```bash
POST /api/v1/reputation/query
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "value": "8.8.8.8",
  "value_type": "ip"
}
```

**Get Reputation (GET)**
```bash
GET /api/v1/reputation/ip/8.8.8.8
Authorization: Bearer your-api-key
```

#### Threat Intelligence Endpoints

**Search Threats**
```bash
GET /api/v1/threats/search?query=8.8.8.8&type=ip&limit=10
Authorization: Bearer your-api-key
```

**Recent Threats**
```bash
GET /api/v1/threats/recent?limit=20
Authorization: Bearer your-api-key
```

**Threat Statistics**
```bash
GET /api/v1/threats/stats
Authorization: Bearer your-api-key
```

#### Health Check
```bash
GET /health
```

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Validation completed",
  "result": {
    "value": "user@example.com",
    "is_valid": true,
    "score": 0.9,
    "confidence": "high",
    "checks": {
      "syntax": {"valid": true},
      "disposable": {"valid": true}
    }
  },
  "timestamp": "2025-10-30T10:11:24Z"
}
```

### Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "error_code": "VALIDATION_ERROR",
    "error_message": "Invalid email format",
    "details": {"validation_errors": [...]}
  },
  "timestamp": "2025-10-30T10:11:24Z"
}
```

## Performance Considerations

### Serverless Limitations
- **Execution Time**: Limited to ~10 seconds (Vercel limit)
- **Memory**: Limited to ~1GB
- **Cold Starts**: May occur on first request
- **Background Tasks**: Not supported

### Optimization Features
- **Supabase Caching**: Reduces database queries
- **Async Operations**: Non-blocking I/O
- **Error Handling**: Robust error recovery
- **Request Validation**: Input sanitization
- **Rate Limiting**: Basic protection against abuse

## Monitoring & Logging

### Supabase Integration
All API usage is automatically logged to Supabase:
- Validation requests and results
- Reputation queries and responses
- Processing times and success rates
- Error tracking and debugging

### Health Monitoring
- `/health` endpoint for uptime monitoring
- Supabase connection status
- Response time tracking

## Security Features

### Authentication
- Bearer token API key authentication
- Multiple API key support
- Admin key capabilities

### Input Validation
- Pydantic request validation
- SQL injection prevention (via Supabase)
- XSS protection

### Rate Limiting
- Basic rate limiting (100 requests/minute)
- Configurable limits per API key
- Request tracking and logging

## Troubleshooting

### Common Issues

**1. Supabase Connection Errors**
```bash
# Check environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Verify table existence in Supabase dashboard
```

**2. API Key Authentication Fails**
```bash
# Verify API key format
curl -H "Authorization: Bearer your-key" https://your-app.vercel.app/health
```

**3. Timeout Errors**
- Large bulk requests may timeout
- Reduce batch size or enable async processing
- Check external API rate limits

**4. Missing Dependencies**
```bash
# Ensure all packages are in requirements.txt
pip install -r requirements.txt
```

### Debug Mode
Set `DEBUG=true` in environment variables to enable:
- Detailed error messages
- Request/response logging
- OpenAPI documentation access

## Development

### Local Testing
```bash
# Start local development server
cd vercel_app
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest
```

### Testing API Endpoints
```bash
# Test email validation
curl -X POST http://localhost:8000/api/v1/validate/email \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer default-api-key-123" \
  -d '{"email": "test@example.com"}'
```

## Production Checklist

- [ ] Supabase project created and configured
- [ ] Database tables created with proper indexes
- [ ] Environment variables configured in Vercel
- [ ] API keys generated and configured
- [ ] Domain DNS configured (if custom domain)
- [ ] SSL certificate configured
- [ ] Monitoring alerts set up
- [ ] Rate limits configured appropriately
- [ ] Backup strategy implemented
- [ ] Security audit completed

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Supabase logs for database issues
3. Check Vercel function logs for serverless errors
4. Verify environment variable configuration

## License

MIT License - see LICENSE file for details.
