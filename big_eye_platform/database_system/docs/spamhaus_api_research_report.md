# Spamhaus Intelligence API (SIA) Research Report

**Research Date:** October 30, 2025  
**Documentation Source:** https://docs.spamhaus.com/sia/docs/

## Executive Summary

The Spamhaus Intelligence API (SIA) provides a comprehensive REST API for real-time access to IP and domain reputation data, with additional URLhaus malware intelligence data (beta). The API offers detailed threat assessment capabilities for automated security systems.

## 1. API Base URL

**Primary Base URL:** `https://api.spamhaus.org`

All API endpoints follow the pattern: `{base_url}/api/intel/v{version}/{endpoint_path}`

## 2. Authentication Method

**Authentication Type:** Bearer Token Authentication

### Login Process
- **Endpoint:** `POST /api/v1/login`
- **Request Format:** JSON
- **Required Fields:**
  - `username`: Email address associated with SIA account
  - `password`: SIA password  
  - `realm`: Always `'intel'` for SIA

### Login Example
```bash
curl -s -d '{"username":"test@example.com","password":"m4g1c","realm":"intel"}' \
https://api.spamhaus.org/api/v1/login
```

### Successful Login Response
```json
{
  "code": 200,
  "token": "AUTH_TOKEN_STRING",
  "expires": 1583252180
}
```

### Token Usage
- **Header Format:** `Authorization: Bearer <AUTH_TOKEN>`
- **Token Validity:** Typically 24 hours
- **Important:** Do NOT request a new token for each API request (penalized)
- **Expiration Handling:** Subsequent requests return 401 Unauthorized

## 3. Rate Limits and Quotas

### Rate Limit Monitoring
**Endpoint:** `GET /api/intel/v1/limits`

### Example Limit Check
```bash
curl -sH 'Authorization: Bearer <AUTH_TOKEN>' \
https://api.spamhaus.org/api/intel/v1/limits
```

### Rate Limit Response Format
```json
{
  "status": 200,
  "account": {
    "sub": "subscription identifier",
    "usr": "account username"
  },
  "limits": {
    "ads": "allowed query datasets (comma separated)",
    "trs": "access level identifier (defaults to 'base')",
    "qms": "max queries per month (soft limit)",
    "qmh": "max queries per month (hard limit)",
    "rl_qph": "enforced rate limits (queries per hour)",
    "rl_qpm": "enforced rate limits (queries per minute)",
    "rl_qps": "enforced rate limits (queries per second)"
  },
  "current": {
    "qpm": "queries performed current month",
    "qpd": "queries performed current day",
    "rl_qph": "rate limit current counter (queries per hour)",
    "rl_qpm": "rate limit current counter (queries per minute)",
    "rl_qps": "rate limit current counter (queries per second)"
  }
}
```

### CIDR Query Counting
- `/32` IPv4 (or `/64` IPv6) = 1 query
- `/24` IPv4 (or `/56` IPv6) = 9 queries  
- **Formula:** `log2(X) + 1` where X is number of distinct resources

### Rate Limit Exceeded Response
- **HTTP Code:** 429 - Too many requests
- **Trigger:** When hard limits (`qmh`) or rate limits (`rl_qpX`) are reached

## 4. Key API Endpoints

### 4.1 IP Reputation Endpoints

#### Search by CIDR
- **Endpoint:** `GET /api/intel/v1/byobject/cidr/<DATASET>/<MODE>/<QTY><IPADDRESS>[/<MASK>]`
- **Response Format:** JSON

**Parameters:**
- `DATASET`: XBL, CSS, BCL, or ALL
- `MODE`: 
  - `listed` - Search submissions contained within netmask
  - `listings` - Search submissions containing netmask (future)
- `QTY`: 
  - `live` - Returns only active listings
  - `history` - Returns any record within time window
- `MASK`: Optional (defaults to 32 for IPv4, 64 for IPv6)

**Query Parameters:**
- `limit`: Max 2000 (default: 500)
- `since`: Unix timestamp (default: 12 months prior)
- `until`: Unix timestamp (default: current)

#### IP Search Examples
```bash
# Get active listings for specific IP
curl -s https://api.spamhaus.org/api/intel/v1/byobject/cidr/XBL/listed/live/45.150.206.114 \
  -H 'Authorization: Bearer <AUTH_TOKEN>'

# Get historical data for CIDR range
curl -s https://api.spamhaus.org/api/intel/v1/byobject/cidr/XBL/listed/history/45.150.206.0/24?limit=10 \
  -H 'Authorization: Bearer <AUTH_TOKEN>'

# Get data for specific time range
curl -s 'https://api.spamhaus.org/api/intel/v1/byobject/cidr/XBL/listed/history/45.150.206.0/24?since=1606600000&until=1606750000' \
  -H 'Authorization: Bearer <AUTH_TOKEN>'
```

#### Dataset Download (Enterprise Only)
- **Endpoint:** `GET /api/intel/v1/download/ext/<DATASET>`
- **Response Format:** Binary (tar.gz)
- **Datasets:** bcl, xbl, css

```bash
wget --header="Authorization: Bearer <AUTH_TOKEN>" \
   --output-document=bcl.tgz \
   https://api.spamhaus.org/api/intel/v1/download/ext/bcl
```

### 4.2 Domain Reputation Endpoints

#### Domain Information
- **Endpoint:** `GET /api/intel/v2/byobject/domain/{DOMAIN}`
- **Response:** Detailed domain attributes, reputation score, tags

#### Domain Dimensions
- **Endpoint:** `GET /api/intel/v2/byobject/domain/{DOMAIN}/dimensions`
- **Response:** Individual scores for SMTP, Identity, Infra, Malware, Human

#### Domain Contexts
- **Endpoint:** `GET /api/intel/v2/byobject/domain/{DOMAIN}/contexts`
- **Response:** Contexts where domain was observed (ZRD, OSINT, DKIM header)

#### Domain Listing Status
- **Endpoint:** `GET /api/intel/v2/byobject/domain/{DOMAIN}/listing`
- **Response:** Current DNSBL listing status with timestamps

#### Domain Senders
- **Endpoint:** `GET /api/intel/v2/byobject/domain/{DOMAIN}/senders`
- **Response:** Associated IP addresses with reputation scores
- **Limit:** Maximum 50 IP addresses

#### Infrastructure Analysis
- **Nameservers:** `/api/intel/v2/byobject/domain/{DOMAIN}/ns`
- **A Records:** `/api/intel/v2/byobject/domain/{DOMAIN}/a`
- **Hostnames:** `/api/intel/v2/byobject/domain/{DOMAIN}/hostnames`

#### Extended Access Endpoints (Enterprise)
- **Infrastructure Clusters:** `/api/intel/v2/byobject/hash/infra/{hash-string}`
- **Authentication Clusters:** `/api/intel/v2/byobject/hash/auth/{hash-string}`

### 4.3 URLhaus Endpoints (Beta Release)

#### URL ID Lookup
- **Endpoint:** `POST /api/intel/v2/byobject/url/id`
- **Request:** `{"url": "url_value"}`
- **Response:** `{"id": 123456}`

#### URL Last Status
- **Endpoint:** `POST /api/intel/v2/byobject/url/last`
- **Response:** Most recent status and payload

#### URL History
- **Endpoint:** `POST /api/intel/v2/byobject/url/history`
- **Response:** Last 100 events and observed payloads

#### URL Search Endpoints
- **Base:** `POST /api/intel/v2/byobject/url/search`

**Search Types:**
- **By IP:** `{"ip": "1.2.3.4"}`
- **By Hostname:** `{"host": "www.example.com"}`
- **By ASN:** `{"asn": 13000}`
- **By Malware Family:** `{"malware_family": "mirai"}`
- **By SHA256 Hash:** `{"sha256": "hash_value"}`
- **By Tags:** `{"tags": ["exe", "32"]}`

## 5. Request/Response Formats

### Request Formats
- **Login:** JSON POST requests
- **Data Queries:** GET requests with URL parameters
- **URLhaus:** POST requests with JSON payloads

### Response Formats

#### JSON Response Structure (Standard)
```json
{
  "code": 200,
  "results": [
    {
      "dataset": "XBL",
      "ipaddress": "74.77.66.227",
      "asn": "11351",
      "cc": "US",
      "listed": 1583252180,
      "seen": 1583252180,
      "valid_until": 1583338580,
      "rule": "01a400d5",
      "botname": "unknown",
      "detection": "SMTP impersonation",
      "dstport": "25",
      "helo": "outlook.com",
      "heuristic": "IMPERSONATE",
      "lat": "43.0505",
      "lon": "-78.853",
      "srcip": "74.77.66.227"
    }
  ]
}
```

#### NDJSON Format (URLhaus)
Multiple JSON objects, one per line, for bulk data responses.

#### Binary Format (Dataset Downloads)
Tar and gzip compressed files (.tgz extension)

## 6. Free vs Paid Tiers

**Note:** Specific pricing and tier information is not publicly available in the documentation.

### Access Levels Mentioned
- **Base Access:** Default tier with basic limits
- **Extended Access:** Required for cluster analysis endpoints
- **Enterprise Access:** Required for dataset downloads

### Tier Limitations
- Rate limits vary by subscription tier
- Dataset access controlled by tier level
- Advanced features require higher tiers

**Recommendation:** Contact Spamhaus sales team for specific pricing and tier information.

## 7. Example API Calls

### Complete Authentication Flow
```bash
# Step 1: Authenticate and get token
TOKEN=$(curl -s -d '{"username":"your-email@domain.com","password":"your-password","realm":"intel"}' \
https://api.spamhaus.org/api/v1/login | jq -r '.token')

# Step 2: Use token in subsequent requests
curl -sH "Authorization: Bearer $TOKEN" \
https://api.spamhaus.org/api/intel/v1/limits
```

### IP Reputation Check
```bash
# Check if IP is listed
curl -s https://api.spamhaus.org/api/intel/v1/byobject/cidr/XBL/listed/live/8.8.8.8 \
  -H 'Authorization: Bearer <AUTH_TOKEN>' | jq '.'
```

### Domain Reputation Analysis
```bash
# Get comprehensive domain information
curl -s https://api.spamhaus.org/api/intel/v2/byobject/domain/example.com \
  -H 'Authorization: Bearer <AUTH_TOKEN>' | jq '.'
```

### URLhaus Malware Lookup
```bash
# Search URLs by IP address
curl -sH 'Authorization: Bearer <AUTH_TOKEN>' \
https://api.spamhaus.org/api/intel/v2/byobject/url/search \
-X POST -d '{"ip":"1.2.3.4"}'
```

## 8. Error Codes

- **200** - Found (Success)
- **400** - Bad Request
- **401** - Unauthorized (invalid/expired token)
- **403** - Forbidden
- **404** - Not found
- **405** - Method not allowed
- **408** - Request Timeout
- **429** - Too many requests (rate limit exceeded)

## 9. Key Features and Capabilities

### Data Types
1. **IP Reputation Data** (XBL, CSS, BCL datasets)
2. **Domain Reputation Data** (comprehensive domain analysis)
3. **URLhaus Data** (malware URLs and hashes - beta)

### Advanced Features
- Historical data queries (up to 12 months)
- Real-time threat intelligence
- Infrastructure correlation analysis
- Malware family classification
- Geographic location data
- Autonomous System Number (ASN) information

### Integration Benefits
- REST API for easy integration
- JSON responses for structured data
- Rate limiting for fair usage
- Comprehensive threat assessment
- Multiple data formats and delivery mechanisms

## Screenshots Documentation

1. **Main API Documentation:** `spamhaus_api_docs_main.png`
2. **IP Endpoint Documentation:** `spamhaus_ip_api_endpoint.png`
3. **Domain Endpoint Documentation:** `spamhaus_domain_api_endpoint.png`
4. **URLhaus Endpoint Documentation:** `spamhaus_urlhaus_api_endpoint.png`
5. **Main Documentation Index:** `spamhaus_docs_main_index.png`
6. **Spamhaus Website:** `spamhaus_main_website.png`

## Conclusion

The Spamhaus Intelligence API provides a robust, well-documented interface for accessing comprehensive threat intelligence data. While specific pricing information requires contacting sales, the API offers flexible access levels from basic reputation checking to enterprise-level threat analysis and dataset downloads. The documentation is comprehensive and includes practical examples for each endpoint type.