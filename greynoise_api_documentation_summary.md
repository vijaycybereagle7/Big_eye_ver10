# GreyNoise API Documentation Summary

## Overview
GreyNoise provides threat intelligence data by collecting and analyzing Internet-wide scan and attack traffic. Their API allows users to query IP addresses for context about malicious or benign activity.

## 1. API Base URL
**Base URL:** `https://api.greynoise.io`

## 2. Authentication Method
- **Authentication:** API Key required for most endpoints
- **Implementation:** API key passed in request headers
- **Community API:** Available without authentication for basic lookups
- **Enterprise API:** Requires API key associated with valid subscription

## 3. Rate Limits and Quotas

### Community API (Free Tier)
- **Unauthenticated users:** 10 IP lookups per day
- **Free-level accounts (with API key):** 50 searches per week
  - Combined metric between Community API and GreyNoise Visualizer

### Enterprise/Paid Tiers
- **Rate limiting enforced:** HTTP 429 response when limits exceeded
- **Specific limits vary by subscription tier**
- **Higher limits available for paid subscriptions**

## 4. Key Endpoints

### 4.1 IP Lookup API
- **Endpoint:** `GET https://api.greynoise.io/v3/ip/{ip}`
- **Purpose:** Comprehensive IP intelligence lookup
- **Tiers:** Enterprise/Research users
- **Parameters:**
  - `ip` (path): IP address to query (required)
  - `quick` (query): Boolean, returns subset of fields if true

### 4.2 GNQL Query API
- **Endpoint:** `GET https://api.greynoise.io/v3/gnql`
- **Purpose:** Complex custom queries against GreyNoise dataset
- **Tiers:** Enterprise and Research users
- **Parameters:**
  - `querystring`: GNQL query string (required)
  - `size`: Number of results per page (1-10,000, default 10,000)
  - `scroll`: Scroll token for pagination
  - `quick`: Boolean, quick response mode

### 4.3 Community API
- **Endpoint:** `GET https://api.greynoise.io/v3/community/{ip}`
- **Purpose:** Basic IP classification for community users
- **Tiers:** Community/Free users
- **Features:** Basic noise/riot classification

### 4.4 IP Timeline API
- **Endpoint:** `GET https://api.greynoise.io/v3/noise/ips/{ip}/timeline`
- **Purpose:** Time series data for IP activity
- **Tiers:** Requires additional subscription license
- **Parameters:**
  - `ip`: IPv4 address to analyze
  - `field`: Activity breakdown field (classification, source_asns, etc.)
  - `days`: Number of days to analyze (default 1)
  - `granularity`: Time bucket size (1h-24h or 1d-90d)

### 4.5 Tags API
- **Endpoint:** `GET https://api.greynoise.io/v3/tags`
- **Purpose:** Retrieve list of GreyNoise tags and metadata
- **Tiers:** Requires API authentication
- **Parameters:** Filter by name, slug, or CVE

## 5. Request/Response Formats

### Request Format
```bash
# Basic structure
curl --request GET \
     --url https://api.greynoise.io/v3/{endpoint} \
     --header 'accept: application/json'
     --header 'key: YOUR_API_KEY'  # For authenticated endpoints
```

### Response Status Codes
- **200 OK:** Request successful
- **206 Partial Content:** Request partially successful due to plan limitations
- **400 Bad Request:** Invalid request syntax
- **401 Unauthorized:** Invalid API key
- **403 Forbidden:** Not authorized due to API key or plan limitations
- **429 Too Many Requests:** Rate limit exceeded
- **404 Not Found:** IP not found in GreyNoise data
- **500 Internal Server Error:** Server error

### Response Format
```json
{
  "ip": "8.8.8.8",
  "business_service_intelligence": {
    "found": true,
    "category": "hosting",
    "name": "example.com",
    "description": "example.com",
    "trust_level": "benign"
  },
  "internet_scanner_intelligence": {
    "seen": true,
    "classification": "benign",
    "first_seen": "2018-01-28",
    "last_seen": "2018-02-28",
    "actor": "Example Actor",
    "tags": ["tag1", "tag2"],
    "metadata": {
      "country": "United States",
      "asn": "AS12345"
    }
  }
}
```

## 6. Example API Calls

### Community API Example
```bash
# Basic community lookup
curl --request GET \
     --url https://api.greynoise.io/v3/community/8.8.8.8 \
     --header 'accept: application/json'
```

### IP Lookup Example
```bash
# Full IP lookup with API key
curl --request GET \
     --url https://api.greynoise.io/v3/ip/8.8.8.8 \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY'
```

### GNQL Query Example
```bash
# Query for malicious IPs from Belgium
curl --request GET \
     --url 'https://api.greynoise.io/v3/gnql?querystring=classification:malicious%20metadata.country:Belgium' \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY'
```

### GNQL Example Queries
```
# Recent activity
last_seen:today

# Specific tags
tags:Mirai

# Malicious IPs from specific country
classification:malicious metadata.country:Belgium

# Port-based searches
(raw_data.scan.port:445 and raw_data.scan.protocol:TCP) metadata.os:Windows*

# CVE-based searches
cve:CVE-2021-30461

# Excluding specific organizations
-metadata.organization:Google raw_data.web.useragents:GoogleBot

# JA3 fingerprint searches
raw_data.ja3.fingerprint:795bc7ce13f60d61e9ac03611dd36d90

# IP range searches
8.0.0.0/8
```

## 7. Community vs Enterprise Features

### Community API Features
- **Cost:** Free
- **Authentication:** Optional (unauthenticated access available)
- **Rate Limits:** 10/day (unauthenticated) or 50/week (with free account)
- **Data Returned:**
  - IP address
  - Noise status (boolean)
  - RIOT status (boolean)
  - Classification (benign/malicious/unknown)
  - Organization name
  - Link to GreyNoise Visualizer
  - Last seen timestamp

### Enterprise/Research Features
- **Cost:** Paid subscription
- **Authentication:** API key required
- **Rate Limits:** Higher limits, varies by tier
- **Data Returned:**
  - All Community API data PLUS:
  - Detailed metadata (ASN, reverse DNS, country)
  - Associated actors
  - Activity tags
  - Raw port scan data
  - Web request information
  - CVEs
  - VPN/TOR indicators
  - Bot detection
  - Business service intelligence
  - Time series data (via Timeline API)
  - Complex queries (GNQL)
  - Multi-IP lookups (up to 10,000 IPs)

### Advanced Enterprise Features
- **GNQL Querying:** Complex custom searches with pagination
- **IP Timeline:** Time series analysis of IP activity
- **Multi-IP Lookups:** Bulk IP analysis
- **Tag Management:** Full access to GreyNoise tags and metadata
- **Higher Rate Limits:** Significantly more requests per time period
- **Priority Support:** Enterprise support and SLAs

## 8. GreyNoise Query Language (GNQL)

GNQL is a domain-specific language built on Lucene for searching GreyNoise data.

### Searchable Fields
**Basic Fields:**
- `ip`, `classification`, `first_seen`, `last_seen`, `actor`, `tags`, `spoofable`, `vpn`, `vpn_service`, `cve`, `bot`

**Metadata Fields:**
- `metadata.category`, `metadata.carrier`, `metadata.country`, `metadata.country_code`, `metadata.datacenter`, `metadata.domain`, `metadata.organization`, `metadata.asn`, `metadata.city`, `metadata.region`

**Raw Data Fields:**
- `raw_data.scan.port`, `raw_data.scan.protocol`, `raw_data.web.paths`, `raw_data.web.useragents`, `raw_data.ja3.fingerprint`, `raw_data.tls.cipher`

### GNQL Features
- Facets can be subtracted using minus prefix
- Data refreshes once per hour
- Keyword `interesting` finds interesting hosts
- Keyword `today` can be used with `first_seen` and `last_seen`

## 9. Additional Resources
- **GreyNoise Visualizer:** https://viz.greynoise.io
- **API Key Management:** https://viz.greynoise.io/account/api-key
- **Pricing:** https://greynoise.io/pricing
- **Python SDK:** Available via pip install greynoise
- **Command Line Tool:** Available via installation guides

## Rate Limit Management
- Monitor usage through GreyNoise Visualizer
- Upgrade subscription for higher limits
- Use quick mode for basic lookups when speed is priority
- Implement proper error handling for 429 responses
- Consider batch operations for multiple IP lookups