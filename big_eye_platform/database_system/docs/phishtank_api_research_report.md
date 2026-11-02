# PhishTank API Documentation Research Report

**Research Date:** October 30, 2025  
**Source URL:** https://www.phishtank.com/api_info.php  
**Author:** MiniMax Agent

## Executive Summary

The PhishTank API provides programmatic access to PhishTank's database of verified phishing URLs. The API is operated by Cisco Talos Intelligence Group and is designed primarily for checking URLs against known phishing threats.

## 1. API Base URL

**Primary Endpoint:** `http://checkurl.phishtank.com/checkurl/`

This is the main API endpoint for all URL verification requests.

## 2. Authentication Method

### API Key (App Key)
- **Method:** Optional `app_key` parameter in POST requests
- **Purpose:** Significantly increases rate limits when provided
- **Registration Required:** Yes, for obtaining an app_key

### User-Agent Header
- **Required:** Yes, must be descriptive
- **Format:** `phishtank/[username]` or similar descriptive string
- **Risk:** Generic or blank User-Agents may trigger increased rate limiting or security checks

## 3. Rate Limits and Quotas

### Rate Limiting Behavior
- **Enforcement:** Strict rate limiting to prevent abuse
- **Exceeding Limits:** HTTP 509 error or potential firewall blocking
- **Alternative:** Consider downloading local copy of database for frequent lookups

### Rate Limit Headers
The API provides rate limit information in response headers:

| Header | Description |
|--------|-------------|
| `X-Request-Limit-Interval` | Time period for rate limit (e.g., '300 Seconds') |
| `X-Request-Limit` | Maximum requests allowed in interval |
| `X-Request-Count` | Requests already made in current interval |
| **Remaining Requests** | `X-Request-Limit - X-Request-Count` |

### Limit Improvements
- **Without App Key:** Lower rate limits
- **With App Key:** Significantly higher rate limits
- **Recommendation:** Register for app_key if making frequent requests

## 4. Key Endpoints

### Check URL Endpoint
- **Method:** HTTP POST
- **Path:** `/checkurl/`
- **Full URL:** `http://checkurl.phishtank.com/checkurl/`
- **Purpose:** Check if a URL exists in the PhishTank database

### Submit Endpoint
- **Note:** Only checking functionality was documented; submission requires community contribution through the main website

## 5. Request/Response Formats

### Request Parameters
| Parameter | Required | Description | Encoding |
|-----------|----------|-------------|----------|
| `url` | Yes | URL to check | URL-encoded or base64 |
| `format` | No | Response format (xml/php/json) | Default: XML |
| `app_key` | No | API key for higher limits | N/A |

### Request Headers
```
User-Agent: phishtank/[username]  # Required, descriptive
```

### Response Formats Supported
1. **XML** (default)
2. **PHP** (serialized array)
3. **JSON**

### Sample XML Response
```xml
<response>
    <meta>
        ...
    </meta>
    <results>
        <url0>
            <url>https://www.example.org/</url>
            <in_database>true</in_database>
            <phish_id>11728</phish_id>
            <phish_detail_page>
                http://www.phishtank.com/phish_detail.php?phish_id=11728
            </phish_detail_page>
            <verified>true</verified>
            <verified_at>2006-10-01T02:32:23+00:00</verified_at>
            <valid>true</valid>
            <submitted_at>2006-10-01T02:28:46+00:00</submitted_at>
        </url0>
    </results>
</response>
```

### Sample PHP Response Format
```php
array('results' => array('url' => 'https://www.example.org/',
                         'in_database' => true,
                         'phish_id' => 11728,
                         'phish_detail_page' => 'http://www.phishtank.com/phish_detail.php?phish_id=11728',
                         'verified' => 'y',
                         'verified_at' => '2006-10-01T02:32:23+00:00',
                         'valid' => 'y'
                        )
)
```

### Response Fields
| Field | Description |
|-------|-------------|
| `url` | The checked URL |
| `in_database` | Boolean indicating if URL is in database |
| `phish_id` | Unique identifier for the phishing site |
| `phish_detail_page` | Link to detailed information page |
| `verified` | Whether the phishing report has been verified |
| `verified_at` | Timestamp when verified |
| `valid` | Whether the URL is currently active as phishing |
| `submitted_at` | When the URL was initially submitted |

## 6. Registration Requirements

### App Key Registration
- **Status:** Required for higher rate limits
- **Registration URL:** https://www.phishtank.com/api_register.php
- **Access:** Requires account creation and login
- **Management:** Applications can be managed via PhishTank website

### Account Requirements
- User account creation required
- Application registration for API key
- Descriptive User-Agent string required

**Note:** During research, the registration page required authentication, suggesting active account management is needed.

## 7. Example API Calls

### Basic Check Request
```bash
POST http://checkurl.phishtank.com/checkurl/
Content-Type: application/x-www-form-urlencoded

url=https://www.example.com/phishing-site
format=json
app_key=YOUR_API_KEY_HERE
```

### cURL Example
```bash
curl -X POST \
  http://checkurl.phishtank.com/checkurl/ \
  -H "User-Agent: phishtank/myappname" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "url=https://www.example.com/phishing-site&format=json&app_key=YOUR_API_KEY"
```

### Python Example
```python
import requests
import urllib.parse

api_url = "http://checkurl.phishtank.com/checkurl/"
url_to_check = "https://www.example.com/phishing-site"

data = {
    'url': urllib.parse.quote(url_to_check),  # URL encode
    'format': 'json',
    'app_key': 'YOUR_API_KEY_HERE'  # Optional
}

headers = {
    'User-Agent': 'phishtank/your-app-name'
}

response = requests.post(api_url, data=data, headers=headers)
result = response.json()
print(result)
```

## Important Notes

1. **Designed for Low Volume:** The API is designed for "a few lookups per day"
2. **URL Encoding:** The `url` parameter must be either URL-encoded or base64 encoded
3. **Local Database:** For high-volume applications, consider downloading local copies of the database
4. **Rate Limit Monitoring:** Always check response headers for rate limit information
5. **Security:** Generic User-Agents may trigger security measures

## Related Links

- **API Registration:** https://www.phishtank.com/api_register.php
- **Developer Info:** https://www.phishtank.com/developer_info.php
- **PhishTank Main Site:** https://www.phishtank.com/
- **Cisco Talos Intelligence:** https://talosintelligence.com/
- **Mailing Lists:** https://www.phishtank.com/mailing_lists.php

## Screenshots Captured

1. `phishtank_api_main_page.png` - Full page overview of API documentation
2. `phishtank_api_rate_limits_section.png` - Rate limiting information section
3. `phishtank_api_response_format_section.png` - Response format examples
4. `phishtank_api_bottom_section.png` - Footer with additional links
5. `phishtank_registration_access.png` - Registration page access requirements

---

**Research Methodology:** Direct navigation to official documentation, comprehensive content extraction, and visual documentation through screenshots.