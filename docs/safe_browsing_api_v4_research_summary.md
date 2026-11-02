# Google Safe Browsing API v4 - Research Summary

## Research Overview
This document contains comprehensive information extracted from the Google Safe Browsing API v4 documentation, covering all requested technical specifications and usage guidelines.

## 1. API Base URL
**Base URL:** `https://safebrowsing.googleapis.com/v4/`

## 2. Authentication Method
**API Key Authentication:** The API uses Google API keys for authentication, passed as a URL parameter in HTTP requests.

**Example format:** `https://safebrowsing.googleapis.com/v4/...?key=API_KEY`

## 3. Rate Limits and Quotas

### Usage Quotas
- **Default Quota:** Allocated to developers upon enabling the API
- **Monitoring:** Current allocation and usage can be viewed in the Google Developer Console
- **Increased Quotas:** Additional quota can be requested through the Developer Console's Quota interface
- **Cost:** No cost for API usage
- **Contact Requirement:** Requests for increased quota require contacting Google to ensure service availability

### Request Frequency Restrictions (Update API only)
**For Update API methods (`threatListUpdates.fetch` and `fullHashes.find`):**

1. **Initial Request:** Must occur at a random interval between 0 and 1 minute after client starts or wakes up

2. **Minimum Wait Duration:** 
   - Clients must respect `minimumWaitDuration` field provided in API responses
   - If `minimumWaitDuration` is not set, clients can update as frequently as desired
   - If set (e.g., 1 hour), no requests should be made during that duration

3. **Back-off Mode:** Upon receiving any unsuccessful HTTP response (non-200 OK):
   - Must use formula: `MIN((2^N - 1 * 15 minutes) * (RAND + 1), 24 hours)`
   - Where N = number of consecutive unsuccessful requests (starting with N=1)
   - RAND = random number between 0 and 1
   - Exit back-off mode upon receiving successful response

## 4. Key Endpoints

### Lookup API
1. **`threatMatches.find`** - Primary endpoint for checking URLs against Safe Browsing lists
   - Purpose: Check URLs against Google's threat lists
   - HTTP Method: POST

### Update API  
2. **`threatListUpdates.fetch`** - Updates local Safe Browsing database
   - Purpose: Download hash prefixes for local storage
   - HTTP Method: POST

3. **`fullHashes.find`** - Verifies potential threats
   - Purpose: Verify hash prefix collisions against full hashes
   - HTTP Method: POST

## 5. Request/Response Formats

### Lookup API - threatMatches.find

**Request Format:**
```json
POST https://safebrowsing.googleapis.com/v4/threatMatches:find?key=API_KEY HTTP/1.1
Content-Type: application/json

{
  "client": {
    "clientId": "yourcompanyname",
    "clientVersion": "1.5.2"
  },
  "threatInfo": {
    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
    "platformTypes": ["WINDOWS"],
    "threatEntryTypes": ["URL"],
    "threatEntries": [
      {"url": "http://www.urltocheck1.org/"},
      {"url": "http://www.urltocheck2.org/"},
      {"url": "http://www.urltocheck3.com/"}
    ]
  }
}
```

**Response Format:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "matches": [
    {
      "threatType": "MALWARE",
      "platformType": "WINDOWS", 
      "threatEntryType": "URL",
      "threat": {"url": "http://www.urltocheck1.org/"},
      "threatEntryMetadata": {
        "entries": [
          {"key": "malware_threat_type", "value": "landing"}
        ]
      },
      "cacheDuration": "300.000s"
    }
  ]
}
```

### Update API - threatListUpdates.fetch & fullHashes.find
- Both use similar JSON structure with `client` identification and `threatInfo` or `listUpdateRequests`
- `fullHashes.find` uses base64-encoded hash prefixes in `threatEntries`
- Responses include `minimumWaitDuration`, `cacheDuration`, and `negativeCacheDuration` for caching

## 6. Usage Restrictions and Guidelines

### Permitted Use
- **Non-commercial use only** (not for sale or revenue-generating purposes)
- **Commercial applications** should use Web Risk API instead

### User Warning Requirements
- Must use qualifying terms: "suspected," "potentially," "possible," or "may be"
- Include attribution: "Advisory provided by Google" with link to Safe Browsing Advisory
- Provide educational links:
  - Social Engineering: antiphishing.org
  - Malware: Google Search Central  
  - Unwanted Software: Unwanted Software Policy
- Only show warnings if data is current and cached responses are valid

### User Protection Notice
- Must inform users that protection is not perfect
- Acknowledge possibility of false positives and false negatives

## 7. Example API Calls

### Complete Lookup API Example
**Request:**
```bash
POST https://safebrowsing.googleapis.com/v4/threatMatches:find?key=YOUR_API_KEY HTTP/1.1
Content-Type: application/json

{
  "client": {
    "clientId": "mycompanyname",
    "clientVersion": "1.0.0"
  },
  "threatInfo": {
    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING"],
    "platformTypes": ["WINDOWS"],
    "threatEntryTypes": ["URL"],
    "threatEntries": [
      {"url": "http://malicious-site.com/"},
      {"url": "http://phishing-site.com/"}
    ]
  }
}
```

**Response:**
```json
{
  "matches": [
    {
      "threatType": "MALWARE",
      "platformType": "WINDOWS",
      "threatEntryType": "URL", 
      "threat": {"url": "http://malicious-site.com/"},
      "cacheDuration": "3600.000s"
    }
  ]
}
```

### Complete Update API Example
**threatListUpdates.fetch:**
```bash
POST https://safebrowsing.googleapis.com/v4/threatListUpdates:fetch?key=YOUR_API_KEY HTTP/1.1
Content-Type: application/json

{
  "client": {
    "clientId": "mycompanyname", 
    "clientVersion": "1.0.0"
  },
  "listUpdateRequests": [
    {
      "threatType": "MALWARE",
      "platformType": "WINDOWS",
      "threatEntryType": "URL",
      "state": "previous_client_state",
      "constraints": {
        "maxUpdateEntries": 10000,
        "maxDatabaseEntries": 1000000,
        "supportedCompressions": ["RAW"]
      }
    }
  ]
}
```

## Summary

The Google Safe Browsing API v4 provides two distinct APIs: the **Lookup API** for simple server-side URL checks and the **Update API** for local database management. The API requires API key authentication, has adjustable quotas, and enforces specific request frequency rules for the Update API. The service is exclusively for non-commercial use and requires specific user warning protocols.

## Screenshots Captured
1. `safe_browsing_overview.png` - Overview page
2. `safe_browsing_get_started.png` - Get Started section with API key setup
3. `safe_browsing_lookup_api.png` - Lookup API endpoint documentation
4. `safe_browsing_response_example.png` - Response format examples
5. `safe_browsing_request_frequency.png` - Request frequency guidelines
6. `safe_browsing_usage_limits.png` - Usage restrictions and quotas
7. `safe_browsing_update_api.png` - Update API overview

## Extracted Content Files
- `browser/extracted_content/safe_browsing_api_v4_overview.json`
- `browser/extracted_content/safe_browsing_v4_get_started_setup.json`
- `browser/extracted_content/safe_browsing_lookup_api_v4.json`
- `browser/extracted_content/safe_browsing_request_frequency.json`
- `browser/extracted_content/safe_browsing_v4_usage_limits.json`
- `browser/extracted_content/safe_browsing_update_api_v4_info.json`
