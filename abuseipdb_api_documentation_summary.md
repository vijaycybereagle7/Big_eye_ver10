# AbuseIPDB API Documentation Summary

## Overview
AbuseIPDB APIv2 provides programmatic access to an extensive database of reported abusive IP addresses, enabling users to check IP reputation, retrieve reports, generate blacklists, report new incidents, and manage reported IPs.

## 1. API Base URL
```
https://api.abuseipdb.com/api/v2/
```

## 2. Authentication Method
- **Method**: API Key
- **Primary Method**: HTTP Header `Key: YOUR_OWN_API_KEY`
- **Alternative Method**: Query parameter `?key=YOUR_API_KEY` (less secure)
- **Recommendation**: Always use the HTTP header method for security

### Required Headers:
```
Key: YOUR_OWN_API_KEY
Accept: application/json
```

## 3. Rate Limits and Quotas

### Free Account Limitations
The documentation mentions various subscription tiers but specific free account limits are not clearly stated. Based on the rate limit structure shown:

| Endpoint | Standard | Webmaster | Supporter | Basic | Premium |
|----------|----------|-----------|-----------|--------|---------|
| check | 1,000/day | 3,000/day | 5,000/day | 10,000/day | 50,000/day |
| reports | 100/day | 500/day | 1,000/day | 5,000/day | 25,000/day |
| blacklist | 5/day | 10/day | 20/day | 100/day | 500/day |
| report | 1,000/day | 3,000/day | 1,000/day | 10,000/day | 50,000/day |
| check-block | 100/day | 250/day | 500/day | 1,000/day | 5,000/day |
| bulk-report | 5/day | 10/day | 20/day | 100/day | 500/day |
| clear-address | 5/day | 10/day | 20/day | 100/day | 500/day |

### Rate Limit Headers
When limits are exceeded, the API provides these headers:
- `Retry-After`: Time to wait before retrying
- `X-RateLimit-Limit`: Total daily limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

### Blacklist IP Truncation Limits
| Tier | Max IPs |
|------|---------|
| Standard | 10,000 |
| Basic Subscription | 100,000 |
| Premium Subscription | 500,000 |

### Check-Block Endpoint Limits
| Parameter | Standard | Basic | Premium |
|-----------|----------|-------|---------|
| network size | Up to /24 | Up to /20 | Up to /16 |
| maxAgeInDays | Up to 30 | Up to 60 | Up to 365 |

## 4. Key Endpoints

### 4.1 CHECK Endpoint
**Purpose**: Check a single IPv4/IPv6 address for abuse reports

**Method**: `GET https://api.abuseipdb.com/api/v2/check`

**Parameters**:
- `ipAddress` (required): IP address to check
- `maxAgeInDays` (optional, default: 30): Report age limit (1-365 days)
- `verbose` (optional): Include detailed reports array

**Response Fields**:
```json
{
  "data": {
    "ipAddress": "string",
    "isPublic": boolean,
    "ipVersion": integer,
    "isWhitelisted": boolean|null,
    "abuseConfidenceScore": integer (0-100),
    "countryCode": "string",
    "countryName": "string",
    "usageType": "string",
    "isp": "string",
    "domain": "string",
    "hostnames": ["string"],
    "isTor": boolean,
    "totalReports": integer,
    "numDistinctUsers": integer,
    "lastReportedAt": "string (ISO 8601)",
    "reports": [...] // Only with verbose=true
  }
}
```

### 4.2 BLACKLIST Endpoint
**Purpose**: Get list of abusive IP addresses with filtering options

**Method**: `GET https://api.abuseipdb.com/api/v2/blacklist`

**Parameters**:
- `confidenceMinimum` (subscriber feature, default: 100): Minimum abuse confidence score (25-100)
- `limit` (restricted, default: 10,000): Maximum IPs to return
- `plaintext` (optional): Return newline-separated IPs instead of JSON
- `onlyCountries` (subscriber feature): Comma-separated ISO country codes
- `exceptCountries` (subscriber feature): Exclude these countries
- `ipVersion` (optional, default: mixed): Filter by IP version (4 or 6)

**Response** (JSON format):
```json
{
  "meta": {
    "generatedAt": "string"
  },
  "data": [
    {
      "ipAddress": "string",
      "abuseConfidenceScore": integer,
      "lastReportedAt": "string",
      "countryCode": "string" // With country filtering
    }
  ]
}
```

### 4.3 REPORT Endpoint
**Purpose**: Report an IP address for abusive activity

**Method**: `POST https://api.abuseipdb.com/api/v2/report`

**Parameters**:
- `ip` (required): IPv4/IPv6 address to report
- `categories` (required): Comma-separated category IDs (max 30)
- `comment` (optional): Descriptive text (strip PII)
- `timestamp` (optional): ISO 8601 datetime

**Response**:
```json
{
  "data": {
    "ipAddress": "string",
    "abuseConfidenceScore": integer
  }
}
```

### 4.4 Other Important Endpoints

#### REPORTS Endpoint
- **Purpose**: Get detailed historical reports for an IP
- **Method**: `GET`
- **Status**: Open Beta

#### CHECK-BLOCK Endpoint
- **Purpose**: Check subnet for reported IPs
- **Method**: `GET`
- **Parameter**: `network` (CIDR notation), `maxAgeInDays`

#### BULK-REPORT Endpoint
- **Purpose**: Report multiple IPs via CSV upload
- **Method**: `POST`

#### CLEAR-ADDRESS Endpoint
- **Purpose**: Delete your own reports for an IP
- **Method**: `DELETE`

## 5. Request/Response Formats

### Request Format
- **Protocol**: HTTPS only (HTTP redirected to HTTPS)
- **Content-Type**: `application/json` for responses
- **Authentication**: `Key` header or `key` query parameter

### Response Format
All responses follow JSON structure with:
- Top-level `data` property containing results
- Error responses include `errors` array following JSON API spec
- HTTP status codes indicate success/failure

### Example Response Structure
```json
{
  "data": {
    // Endpoint-specific data
  }
}
```

## 6. Example API Calls

### Check IP Reputation (cURL)
```bash
curl -G https://api.abuseipdb.com/api/v2/check \
  --data-urlencode "ipAddress=118.25.6.39" \
  -d maxAgeInDays=90 \
  -d verbose \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```

### Get Blacklist (cURL)
```bash
curl -G https://api.abuseipdb.com/api/v2/blacklist \
  -d confidenceMinimum=90 \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```

### Report Abuse (cURL)
```bash
curl --fail 'https://api.abuseipdb.com/api/v2/report' \
  -H 'Accept: application/json' \
  -H 'Key: YOUR_OWN_API_KEY' \
  --data-urlencode 'comment=<matches>' \
  --data-urlencode 'ip=<ip>' \
  --data 'categories=<abuseipdb_category>'
```

### Get Plaintext Blacklist
```bash
curl -G https://api.abuseipdb.com/api/v2/blacklist \
  -d limit=500000 \
  -H "Key: YOUR_API_KEY" \
  -H "Accept: text/plain"
```

### Python Example (Check Endpoint)
```python
import requests
import json

url = 'https://api.abuseipdb.com/api/v2/check'
querystring = {
    'ipAddress': '118.25.6.39',
    'maxAgeInDays': '90'
}
headers = {
    'Accept': 'application/json',
    'Key': 'YOUR_OWN_API_KEY'
}

response = requests.request(method='GET', url=url, headers=headers, params=querystring)
decodedResponse = json.loads(response.text)
print(json.dumps(decodedResponse, sort_keys=True, indent=4))
```

### Testing Rate Limiting
For testing purposes, report IP `127.0.0.2` to simulate rate limiting.

## 7. Pricing Tiers and Limitations

### Available Tiers
1. **Standard** (lowest tier)
2. **Webmaster**
3. **Supporter**
4. **Basic Subscription**
5. **Premium Subscription** (highest tier)

### Tier Features
- **Subscriber Features**: 
  - `confidenceMinimum` parameter on blacklist
  - Country filtering (`onlyCountries`, `exceptCountries`)
  - Higher IP limits for blacklists
  - Larger network ranges for check-block

### Important Limitations
- CORS is not supported (API keys are private)
- All requests must use HTTPS
- API keys should never be used in client-side applications
- Hard minimum of 25% `abuseConfidenceScore` applied to blacklists
- Maximum 10,000 reports included in verbose responses
- Default blacklist limit is 10,000 IPs regardless of subscription

### Getting API Keys
- **Developer Key**: Sign up at https://www.abuseipdb.com/account/api
- **Paid Plans**: Subscribe at https://www.abuseipdb.com/account/plans

## 8. Security Considerations

1. **API Key Security**: Never expose keys in client-side code
2. **HTTPS Only**: All requests must use HTTPS
3. **Header Authentication**: Prefer header over query parameters
4. **PII Removal**: Strip personally identifiable information from reports
5. **Rate Limiting**: Respect daily limits to avoid being blocked
6. **Regular Updates**: Update blacklists regularly as scores decay over time

## 9. Error Handling

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request
- `401`: Unauthorized (invalid API key)
- `402`: Payment Required (exceeded tier limits)
- `429`: Too Many Requests (exceeded daily limit)
- `500`: Internal Server Error

### Error Response Format
```json
{
  "errors": [
    {
      "detail": "Error description",
      "status": "HTTP status code"
    }
  ]
}
```

## 10. Additional Resources

- **Fail2Ban Integration**: https://www.abuseipdb.com/fail2ban.html
- **Abuse Categories Reference**: https://www.abuseipdb.com/categories
- **Confidence Score FAQ**: https://www.abuseipdb.com/faq.html#confidence
- **Bulk Report Form**: https://www.abuseipdb.com/bulk-report
- **IPinfo Geolocation**: https://ipinfo.io/?ref=abuseipdb

---

*Documentation extracted from https://docs.abuseipdb.com/ on 2025-10-30*