# GreyNoise API Technical Reference

## API Base URL
```
https://api.greynoise.io
```

## Authentication Headers
```bash
# For authenticated endpoints
key: YOUR_API_KEY
accept: application/json
```

## Endpoint Specifications

### 1. Community IP Lookup
**Method:** GET  
**Endpoint:** `https://api.greynoise.io/v3/community/{ip}`  
**Authentication:** Optional  
**Rate Limits:** 10/day (unauth), 50/week (free account)

#### Request Parameters
- `ip` (path): IPv4 address to query

#### Response Schema
```json
{
  "ip": "string",
  "noise": "boolean",
  "riot": "boolean", 
  "classification": "string",
  "name": "string",
  "link": "string",
  "last_seen": "ISO8601 timestamp",
  "message": "string"
}
```

### 2. IP Lookup (Enterprise)
**Method:** GET  
**Endpoint:** `https://api.greynoise.io/v3/ip/{ip}`  
**Authentication:** Required  
**Rate Limits:** Varies by subscription tier

#### Request Parameters
- `ip` (path): IPv4 address to query (required)
- `quick` (query): boolean, default false

#### Response Schema
```json
{
  "ip": "string",
  "business_service_intelligence": {
    "found": "boolean",
    "category": "string",
    "name": "string",
    "description": "string",
    "trust_level": "string"
  },
  "internet_scanner_intelligence": {
    "seen": "boolean",
    "classification": "string",
    "first_seen": "date",
    "last_seen": "date",
    "actor": "string",
    "tags": ["string"],
    "bot": "boolean",
    "spoofable": "boolean",
    "tor": "boolean",
    "vpn": "boolean",
    "vpn_service": "string",
    "metadata": {
      "country": "string",
      "source_country": "string"
    }
  }
}
```

### 3. GNQL Query
**Method:** GET  
**Endpoint:** `https://api.greynoise.io/v3/gnql`  
**Authentication:** Required  
**Rate Limits:** Varies by subscription tier

#### Request Parameters
- `querystring` (query): GNQL query string (required)
- `size` (query): integer, 1-10000, default 10000
- `scroll` (query): string for pagination
- `quick` (query): boolean, default false

#### Response Schema
```json
{
  "request_metadata": {
    "complete": "boolean",
    "scroll": "string",
    "query": "string",
    "count": "integer",
    "message": "string",
    "restricted_fields": ["string"]
  },
  "data": [
    {
      "ip": "string",
      "internet_scanner_intelligence": {},
      "business_service_intelligence": {}
    }
  ]
}
```

### 4. IP Timeline
**Method:** GET  
**Endpoint:** `https://api.greynoise.io/v3/noise/ips/{ip}/timeline`  
**Authentication:** Required + Additional License  
**Rate Limits:** Subscription dependent

#### Request Parameters
- `ip` (path): IPv4 address (required)
- `field` (query): breakdown field (classification, source_asns, tag_ids)
- `days` (query): number of days (default 1)
- `granularity` (query): time bucket (1h-24h, 1d-90d)

#### Response Schema
```json
{
  "results": [
    {
      "data": "integer",
      "label": "string",
      "timestamp": "ISO8601"
    }
  ],
  "metadata": {
    "ip": "string",
    "field": "string",
    "first_seen": "date",
    "start": "timestamp",
    "end": "timestamp",
    "granularity": "string",
    "metric": "string"
  }
}
```

### 5. List Tags
**Method:** GET  
**Endpoint:** `https://api.greynoise.io/v3/tags`  
**Authentication:** Required  
**Rate Limits:** Subscription dependent

#### Request Parameters
- `name` (query): partial name match
- `slug` (query): exact slug match
- `cve` (query): associated CVE

#### Response Schema
```json
[
  {
    "id": "string",
    "label": "string",
    "slug": "string",
    "name": "string",
    "category": "string",
    "intention": "string",
    "description": "string",
    "references": ["string"],
    "recommend_block": "boolean",
    "cves": ["string"],
    "created": "date",
    "related_tags": ["string"]
  }
]
```

## HTTP Status Codes
- `200` - Success
- `206` - Partial Content (plan limitations)
- `400` - Bad Request (invalid syntax)
- `401` - Unauthorized (invalid API key)
- `403` - Forbidden (plan limitations)
- `404` - Not Found (IP not in dataset)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

## Error Response Format
```json
{
  "message": "Error description"
}
```

## GNQL Field Reference

### Basic Fields
```
ip, classification, first_seen, last_seen, actor, tags, spoofable, 
vpn, vpn_service, cve, bot, single_destination
```

### Metadata Fields
```
metadata.category, metadata.carrier, metadata.country, 
metadata.country_code, metadata.datacenter, metadata.domain,
metadata.sensor_hits, metadata.sensor_count, metadata.city,
metadata.region, metadata.organization, metadata.rdns,
metadata.asn, metadata.tor, metadata.destination_cities,
metadata.destination_asns, metadata.destination_countries,
metadata.latitude, metadata.longitude, metadata.rdns_parent,
metadata.rdns_validated, metadata.source_country_code
```

### Raw Data Fields
```
raw_data.scan.port, raw_data.scan.protocol, raw_data.web.paths,
raw_data.web.useragents, raw_data.ja3.fingerprint, raw_data.ja3.port,
raw_data.hassh.fingerprint, raw_data.hassh.port, raw_data.http.md5,
raw_data.http.cookie_keys, raw_data.http.request_authorization,
raw_data.http.request_cookie, raw_data.http.request_header,
raw_data.http.request_method, raw_data.http.request_origin,
raw_data.tls.cipher, raw_data.ssh.key
```

## Example cURL Commands

### Community API
```bash
curl --request GET \
     --url https://api.greynoise.io/v3/community/8.8.8.8 \
     --header 'accept: application/json'
```

### IP Lookup (Quick)
```bash
curl --request GET \
     --url 'https://api.greynoise.io/v3/ip/8.8.8.8?quick=true' \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY'
```

### GNQL Query
```bash
curl --request GET \
     --url 'https://api.greynoise.io/v3/gnql?querystring=last_seen:today&size=100' \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY'
```

### Multi-IP Lookup
```bash
curl --request GET \
     --url 'https://api.greynoise.io/v3/multi/ip' \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY' \
     --data '["8.8.8.8", "1.1.1.1", "208.67.222.222"]'
```

### IP Timeline
```bash
curl --request GET \
     --url 'https://api.greynoise.io/v3/noise/ips/8.8.8.8/timeline?field=classification&days=7&granularity=1d' \
     --header 'accept: application/json' \
     --header 'key: YOUR_API_KEY'
```

## Rate Limit Headers
When rate limits are in place, the following headers may be present:
- `X-RateLimit-Limit`: Request limit per time period
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time when limit resets

## SDK and Libraries
- **Python SDK:** `pip install greynoise`
- **Command Line Tool:** Available via installation documentation
- **Postman Collection:** Available in documentation

## Best Practices
1. Use API key authentication for all paid endpoints
2. Implement exponential backoff for rate limit handling
3. Use quick mode for basic lookups when detailed data isn't needed
4. Leverage multi-IP endpoints for bulk operations
5. Cache results to minimize API calls
6. Monitor usage through GreyNoise Visualizer
7. Handle all HTTP status codes appropriately
8. Use GNQL for complex queries instead of multiple individual lookups