# Shodan API Documentation Research Report

**Research Date:** October 30, 2025  
**Documentation URL:** https://developer.shodan.io/api

## 1. API Base URL

**Base URL:** `https://api.shodan.io`

All REST API methods use this base URL for endpoint calls.

## 2. Authentication Method

**Authentication:** API Key Required

- API keys are required for all API calls
- API keys can be obtained for free by creating a Shodan account at https://account.shodan.io/register
- The API key is passed as a `key` parameter in requests
- Example: `https://api.shodan.io/shodan/host/{ip}?key={YOUR_API_KEY}`

## 3. Rate Limits and Quotas

### Query Credits
- **Search queries** (`/shodan/host/search`): 
  - Consumes 1 query credit if the search query contains a filter
  - Consumes 1 credit for every 100 results past the 1st page
- **Count queries** (`/shodan/host/count`): Does NOT consume query credits (only returns counts and facets)
- **DNS lookups** (`/dns/domain/{domain}`): Uses 1 query credit per lookup

### Scan Credits
- **On-demand scanning** (`/shodan/scan`): Consumes 1 scan credit per IP
- Requires a paid API plan

### Account Information
- Current API plan information available via `/api-info` endpoint
- Returns: `scan_credits`, `query_credits`, `monitored_ips`, `usage_limits`

### Access Restrictions
- Free accounts have limited access
- Enterprise-level features require paid plans or Enterprise Data license
- Internet-wide scanning (`/shodan/scan/internet`) restricted to security researchers and Enterprise license holders

## 4. Key Endpoints

### Search Endpoints
1. **Search Shodan** - `GET /shodan/host/search`
   - Search Shodan using query syntax with facets
   - Parameters: `query`, `facets`, `page`, `minify`
   - Consumes query credits

2. **Count Results** - `GET /shodan/host/count`
   - Returns total count without host results
   - Does not consume query credits
   - Parameters: `query`, `facets`

### Host Endpoints
3. **Host Information** - `GET /shodan/host/{ip}`
   - Returns all services found on given IP
   - Parameters: `ip` (required), `history`, `minify`
   - No credit consumption

4. **List Search Facets** - `GET /shodan/host/search/facets`
   - Returns available facets for searches

5. **List Search Filters** - `GET /shodan/host/search/filters`
   - Returns available search filters

### InternetDB Endpoint
6. **InternetDB Data** - `GET /shodan/data/internetdb`
   - Provides minified database containing network information about all IPs on the Internet
   - Listed under `/shodan/data` dataset section
   - Access pattern: `/shodan/data/{dataset}`

### Utility Endpoints
7. **API Info** - `GET /api-info`
   - Returns current API plan information and usage limits

8. **Ports List** - `GET /shodan/ports`
   - Returns list of ports Shodan crawls

9. **Protocols List** - `GET /shodan/protocols`
   - Returns available protocols for scanning

### Scanning Endpoints
10. **Request Scan** - `POST /shodan/scan`
    - Request Shodan to crawl specific IPs/netblocks
    - Consumes scan credits, requires paid plan

11. **Internet-wide Scan** - `POST /shodan/scan/internet`
    - Crawl Internet for specific port
    - Restricted to Enterprise users

## 5. Request/Response Formats

### Request Format
- **HTTP Methods:** GET, POST, PUT, DELETE
- **Parameters:** Passed as URL query parameters
- **Authentication:** API key in `key` parameter
- **Content-Type:** `application/json` for POST requests

### Response Format
- **Format:** JSON
- **Success:** HTTP 200 with JSON response
- **Error:** Non-200 status codes with JSON error message containing `error` field

### Example Request
```bash
curl -X GET "https://api.shodan.io/shodan/host/8.8.8.8?key={YOUR_API_KEY}"
```

### Example Response Structure
```json
{
    "region_code": null,
    "ip": 134744072,
    "postal_code": null,
    "country_code": "US",
    "city": null,
    "dma_code": null,
    "last_update": "2021-01-22T08:49:35.190817",
    "latitude": 37.751,
    "tags": [],
    "hostnames": ["dns.google"],
    "org": "Google",
    "data": [...],
    "asn": "AS15169",
    "isp": "Google",
    "ports": [53]
}
```

## 6. Pricing Tiers and Features

**Note:** Detailed pricing information was not accessible due to Cloudflare security verification on the billing page.

### General Information
- **Free Tier:** Available with limited query credits and basic features
- **Paid API Plans:** Required for scanning features and higher query limits
- **Enterprise License:** Required for bulk data access, organization management, and internet-wide scanning
- **Billing Page:** https://account.shodan.io/billing
- **API Subscriptions:** https://developer.shodan.io/pricing

### Features by Tier
- **Free:** Basic search and host lookup capabilities
- **Paid:** Scanning credits, higher query limits
- **Enterprise:** Bulk data access, organization management, internet-wide scanning

## 7. Example API Calls

### Host Information Lookup
```bash
curl -X GET "https://api.shodan.io/shodan/host/8.8.8.8?key={YOUR_API_KEY}"
```

### Search Query with Facets
```bash
curl -X GET "https://api.shodan.io/shodan/host/search?key={YOUR_API_KEY}&query=product:nginx&facets=country"
```

### Count Results (No Credits)
```bash
curl -X GET "https://api.shodan.io/shodan/host/count?key={YOUR_API_KEY}&query=port:22&facets=org,os"
```

### Request On-Demand Scan
```bash
curl -X POST "https://api.shodan.io/shodan/scan?key={YOUR_API_KEY}" -d 'ips=8.8.8.8,1.1.1.1'
```

### Get API Information
```bash
curl -X GET "https://api.shodan.io/api-info?key={YOUR_API_KEY}"
```

## 8. Additional Resources

### Client Libraries
- **Python:** `python-shodan` library available
- **CLI:** Shodan command-line tool available
- **Postman Collection:** Available for API testing

### Documentation Links
- **OpenAPI Spec:** https://developer.shodan.io/api/openapi.json
- **Search Filters:** https://www.shodan.io/search/filters
- **Banner Specification:** https://datapedia.shodan.io/
- **Support:** support@shodan.io

### Streaming API
- **Documentation:** https://developer.shodan.io/api/stream
- Provides real-time feed of Shodan's collected data
- Meant for large-scale consumption
- Data cannot be searched or interacted with directly

### Trends API
- **Documentation:** https://developer.shodan.io/api/trends
- Provides trend analysis capabilities

## Summary

The Shodan API provides comprehensive access to internet-connected device information through a RESTful interface. The API uses API key authentication, implements a credit-based system for queries and scans, and offers different access levels from free to enterprise tiers. Key functionality includes searching for devices, getting host information, requesting on-demand scans, and accessing the InternetDB dataset for network information.

**Research Limitations:** Detailed pricing information and specific rate limit numbers were not accessible due to Cloudflare security verification requirements on the billing/pricing pages.