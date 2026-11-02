# Free WHOIS APIs: WhoisXML API, IPWHOIS.io, and WhoisJSON — Endpoints, Auth, Data, Rate Limits, and Integration Examples

## Executive Summary

Three widely used services address overlapping yet distinct needs in the WHOIS/RDAP and IP intelligence landscape: WhoisXML API's WHOIS Web Service focuses on domain registration data and RDAP/WHOIS protocol control; IPWHOIS.io emphasizes IP geolocation with optional security signals and bulk throughput; and WhoisJSON offers a developer-centric, RESTful WHOIS suite with multiple endpoints and standard HTTP rate semantics.

WhoisXML API provides rich domain WHOIS/RDAP responses via a single, flexible endpoint with parameters for domain availability checks, registry-only data, proxy detection, and cache control. It supports both API key and Authorization header authentication and offers 500 free calls to start, with an explicit cache policy and a "hard refresh" option to force fresh results at a higher credit cost[^1][^4]. IPWHOIS.io delivers JSON/XML/CSV IP geolocation data via a simple path-per-IP GET and a bulk endpoint. Its free tier allows up to 10,000 monthly requests but is restricted to non-commercial use. Paid plans unlock features such as threat indicators, response-included rate information, SLA, and the bulk endpoint[^6][^8][^7]. WhoisJSON exposes multiple endpoints for WHOIS, reverse WHOIS from IP, nslookup, SSL certificate checks, random WHOIS, and domain availability. It uses header-based token authentication, returns JSON or XML, and signals rate limits with HTTP 429 while exposing a Remaining-Requests header; free accounts include 1,000 monthly calls and a per-minute throttle[^11][^13][^12].

In practice: use WhoisXML API when you need deep, parsed domain registrant and registration metadata with protocol control; use WhoisJSON for lightweight REST integration across WHOIS-centric tasks with transparent throttling; and use IPWHOIS.io for IP geolocation and security signals rather than WHOIS registrant details. Table 1 summarizes quick facts and constraints.

To illustrate this point, the following table compares provider quick facts: free tier size, rate-limit signals, core focus, and primary endpoint style. This helps orient selection before diving into detailed specifications.

Table 1. Provider quick facts

| Provider            | Free tier (approximate)              | Notable rate-limit signal(s)                     | Primary focus                                 | Endpoint style                            |
|---------------------|--------------------------------------|--------------------------------------------------|-----------------------------------------------|-------------------------------------------|
| WhoisXML API        | 500 free calls to start              | Cache 24–48h; _hardRefresh costs 5 credits       | Domain WHOIS/RDAP and registrant/registration | Single WHOIS endpoint with parameters     |
| IPWHOIS.io          | Up to 10,000 requests/month (non-commercial) | rate=1 returns limit/remaining; 429 not documented here | IP geolocation; optional security indicators  | GET path per IP; bulk POST                |
| WhoisJSON           | 1,000 requests/month; per-minute throttles | HTTP 429; Remaining-Requests header              | Domain/IP WHOIS, nslookup, SSL, availability  | REST paths per function under /api/v1     |

These quick distinctions underscore a pragmatic integration strategy: match the provider to the target data domain (domain vs IP), desired throughput and throttling behavior, and the necessary authentication model.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^4]: Pricing | WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.  
[^7]: IP Geolocation API - Pricing - IPWHOIS.io.  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.

## Methodology and Source Validation

This analysis relies on official provider documentation for functional details, authentication, parameterization, outputs, and integration examples. WhoisXML API's "Making requests" page serves as the canonical reference for its WHOIS service parameters and behavior, supplemented by the vendor's pricing page for entitlements and cache policies[^1][^4]. IPWHOIS.io's documentation describes single and bulk endpoints, response formats, and rate-related options, while the pricing page confirms free tier scope, paid plan features, and network performance claims[^6][^7]. WhoisJSON's documentation, FAQs, and OpenAPI specification collectively define endpoints, auth, HTTP status codes, and throttling indicators[^11][^13][^14].

Limitations and information gaps are noted where vendors do not publish detailed per-endpoint parameters or field-level schemas in the referenced materials (see "Information gaps"). All statements and integration guidance reflect the documentation available as of October 29, 2025.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^4]: Pricing | WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.  
[^7]: IP Geolocation API - Pricing - IPWHOIS.io.  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.  
[^14]: WhoisJSON OpenAPI Specification (validator).

## Provider Deep-Dives

### WhoisXML API — WHOIS Web Service

WhoisXML API's WHOIS Web Service exposes a single, powerful endpoint that can return WHOIS or Registration Data Access Protocol (RDAP) records for domains, IP addresses, or email addresses. The service offers extensive parameterization for domain availability checks, registry-only data, proxy/privacy detection, and cache behavior, and it supports both GET and POST with flexible authentication[^1][^2].

#### Endpoints and HTTP Methods

The service exposes a single WHOIS endpoint that accepts both GET and POST. GET passes parameters as query strings, while POST sends a JSON body. The vendor also provides a Postman collection to bootstrap requests[^1][^17].

- Endpoint: whoisserver/WhoisService  
- Methods: GET, POST  
- Postman collection: preconfigured environment with api_key variable (downloadable from vendor)[^17]

This unified approach simplifies integration: whether you need a quick lookup or a parameterized call, the same endpoint serves both patterns.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^17]: WhoisXML API Postman Collection.

#### Authentication

The service recognizes API keys and bearer tokens, with the apiKey query parameter taking precedence if both methods are used[^1].

- apiKey as a query parameter (preferred when present)  
- Authorization: Bearer <API_KEY_OR_TOKEN> header; ignored if apiKey query parameter is present

Developers should centralize secrets management and consistently pass credentials via query or header depending on architectural constraints.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).

#### Request Parameters and Options

WhoisXML's parameter set allows fine control over data freshness, protocol selection, parsing scope, and output format. Table 2 summarizes the most relevant options.

Before diving into code, the following table catalogs parameters, defaults, and purposes. This inventory clarifies which flags adjust protocol choice, data scope, or output detail.

Table 2. Key request parameters

| Parameter        | Type    | Default | Acceptable values                                         | Purpose / Notes                                                                 |
|------------------|---------|---------|------------------------------------------------------------|----------------------------------------------------------------------------------|
| domainName       | string  | —       | Domain/IP/email                                            | The target to query                                                              |
| outputFormat     | string  | XML     | JSON, XML                                                  | Response format                                                                  |
| rdap             | integer | 0       | 0 (Auto), 1 (RDAP), 2 (WHOIS)                              | Protocol selection; RDAP not supported for all TLDs                              |
| preferFresh      | integer | 0       | 0, 1                                                       | Retrieve latest record even if incomplete                                        |
| da               | integer | 0       | 0, 1 (quick), 2 (accurate)                                 | Domain availability check; populates domainAvailability                          |
| ip               | integer | 0       | 0, 1                                                       | Returns IP(s) associated with the domain                                         |
| ipWhois          | integer | 1       | 0, 1                                                       | Returns WHOIS for hosting IP when domain TLD WHOIS not supported                 |
| checkProxyData   | integer | 0       | 0, 1                                                       | Fetches proxy/WHOIS guard data in privateWhoisProxy                              |
| thinWhois        | integer | 0       | 0, 1                                                       | Returns registry-only data in registryData                                       |
| ignoreRawTexts   | integer | 0       | 0, 1                                                       | Strips raw text from output                                                      |
| callback         | string  | —       | Function name                                              | JSONP callback for JSON output                                                   |
| registryRawText  | string  | —       | Text                                                       | Parser input; requires _parse=1                                                  |
| registrarRawText | string  | —       | Text                                                       | Parser input; requires _parse=1                                                  |
| multiIdIana      | integer | 0       | 0, 1                                                       | Enables multi-ID IANA match for registrarName to obtain registrarIANAID          |
| _parse           | integer | 0       | 0, 1                                                       | Enables parsing for registry/registrar raw texts                                 |
| _hardRefresh     | integer | 0       | 0, 1                                                       | Forces new fetch and cache update; costs 5 credits                               |

These parameters enable specific workflows: domain availability pre-checks, proxy detection, and registry-only thin WHOIS, while the cache semantics and hard refresh flag help control freshness and cost[^1].

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).

#### Response Format and Data Fields

WhoisXML can return JSON or XML, with optional JSONP via callback. Output composition is controlled by parameters: registryData for thinWhois=1, privateWhoisProxy for checkProxyData=1, domainAvailability for da=1, and ip fields for ip=1. The structure is designed for parsed, programmatic consumption rather than raw text reliance[^1][^2].

Developers should treat optional components as nullable fields and rely on parameter-driven inclusion rather than attempting to parse free-form raw text.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^2]: Output | Documentation - WHOIS API (WhoisXML).

#### Rate Limits, Credits, and Caching

The service grants 500 complimentary calls upon registration. WHOIS/RDAP records are cached for 24–48 hours based on audit.updatedDate. Using _hardRefresh=1 forces a fresh fetch and update, costing 5 credits. Table 3 summarizes typical cache and refresh behaviors[^1][^4].

To illustrate cache behavior, the following table outlines default vs forced refresh impacts on credits and data freshness.

Table 3. Cache behavior and credit costs

| Scenario                 | Cache window       | Credit cost | Freshness implication                                          |
|--------------------------|--------------------|-------------|-----------------------------------------------------------------|
| Default (no _hardRefresh)| 24–48 hours        | 1           | Returns cached record if within window                          |
| _hardRefresh=1           | Bypasses/updates   | 5           | Forces new fetch and updates cache                              |

When to use hard refresh: shortly after known registrar updates, for critical workflows that cannot tolerate stale data, or when processing high-value changes that justify the extra credits[^1][^4].

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^4]: Pricing | WHOIS API (WhoisXML).

#### Integration Examples

- GET with apiKey (query parameter):

```
curl --location \
  'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey=API_KEY&domainName=google.com'
```

- POST with JSON body:

```
curl --location 'https://www.whoisxmlapi.com/whoisserver/WhoisService' \
  --header 'Content-Type: application/json' \
  --data '{ "domainName": "google.com", "apiKey": "API_KEY" }'
```

- Authorization header:

```
curl --location 'https://www.whoisxmlapi.com/whoisserver/WhoisService?domainName=google.com' \
  --header 'Authorization: Bearer ACCESS_TOKEN'
```

- Postman collection: import the vendor's preconfigured collection and set api_key in the environment[^17].

These patterns cover key-based and token-based auth, GET and POST, and environment-based testing.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^17]: WhoisXML API Postman Collection.

### IPWHOIS.io — IP Geolocation API

IPWHOIS.io provides IP geolocation data with flexible output formats, localization options, optional security indicators, and a bulk endpoint for higher throughput. It is purpose-built for geolocation and network context rather than WHOIS registrant records, and its free tier is non-commercial[^6][^7].

#### Endpoints and HTTP Methods

- Single IP Lookup: GET https://ipwho.is/{ip}  
  - If {ip} is omitted, the service returns data for the requester's IP.  
  - HTTPS is supported[^6].
- Bulk IP Lookup: POST https://ipwhois.pro/bulk?key=API_KEY  
  - Accepts up to 100 IPs per request. Requires API key[^6].

The single-IP path favors simplicity, while the bulk endpoint supports batch workflows.

[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

#### Authentication

- Single IP: No key required; identification by IP address and Referer header for the free tier[^6].  
- Bulk endpoint: API key passed as a URL parameter key=YOUR_API_KEY[^6].

This split encourages lightweight experimentation for single-IP use while gating bulk usage.

[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

#### Request Parameters and Options

The API supports output format selection, field filtering, JSONP callback, localization, and optional features for rate and security signals. Table 4 catalogs these options.

To clarify supported controls, the following table lists parameters, options, and plan dependencies.

Table 4. Single-IP parameters

| Parameter  | Type    | Options                                       | Notes                                                      |
|------------|---------|-----------------------------------------------|------------------------------------------------------------|
| output     | string  | json (default), xml, csv                      | Response format                                            |
| fields     | string  | Comma-separated field names                   | Restricts results to selected fields                       |
| callback   | string  | Function name                                 | JSONP callback                                             |
| lang       | string  | en (default), ru, de, es, pt-BR, fr, zh-CN, ja| Localization for city, region, country, capital, continent |
| security   | integer | 1                                             | Returns security indicators; Business/Premium plans        |
| rate       | integer | 1                                             | Returns rate limit info (limit, remaining); paid plans     |

Localization and field filtering reduce payload size; security and rate options require specific plans[^6].

[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

#### Response Data Fields

The JSON response includes IP metadata (ip, success, type), location (continent, country, region, city, latitude/longitude, postal), country flag assets, connection details (ASN, organization, ISP, domain), timezone (id, abbreviation, is_dst, offset, utc, current_time), currency (name, code, symbol, plural, exchange_rate), and optional security indicators and rate info[^6].

Security indicators (anonymous, proxy, vpn, tor, hosting) are available when security=1; rate information (limit, remaining) is available when rate=1 and the plan supports it[^6].

[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

#### Rate Limits and Plans

- Free tier: up to 10,000 requests/month; non-commercial use; identification by IP and Referer[^7][^6].  
- Paid plans include Basic, Business, and Premium with increasing request volumes, 99.9% SLA, fast network (19 Points of Presence), priority support, currency data, security data, and bulk endpoint[^7].  
- Average response time up to 90 ms[^7].

Table 5 summarizes plan signals and features.

To make plan selection tangible, the following table contrasts free vs paid tiers.

Table 5. Plan comparison (selected features)

| Plan     | Requests/month | SLA     | Bulk endpoint | Security indicators | Rate info in response | Notes                                     |
|----------|-----------------|---------|---------------|---------------------|-----------------------|-------------------------------------------|
| Free     | < 10,000        | —       | No            | No                  | Not documented        | Non-commercial; identified by IP/Referer  |
| Basic    | 250,000         | 99.9%   | Yes           | Yes                 | Yes                   | Fast network (19 PoPs), priority support  |
| Business | 1,500,000       | 99.9%   | Yes           | Yes                 | Yes                   | Higher throughput                         |
| Premium  | 6,500,000       | 99.9%   | Yes           | Yes                 | Yes                   | Highest throughput                        |

Paid plans add operational guarantees and features required for production-grade workloads.

[^7]: IP Geolocation API - Pricing - IPWHOIS.io.  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

#### Integration Examples

Single-IP lookup (PHP):

```php
$ip = '8.8.4.4';
$ch = curl_init('http://ipwho.is/'.$ip);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HEADER, false);
$ipwhois = json_decode(curl_exec($ch), true);
curl_close($ch);
echo $ipwhois['country'] . ' ' . $ipwhois['flag']['emoji']; // United States 🇺🇸
```

Bulk lookup (PHP):

```php
$ips = array('8.8.4.4','1.1.1.1','2c0f:fb50:4003::');
$endpoint = 'http://ipwhois.pro/bulk?key=YOUR_API_KEY';
$options = array(
  'http' => array(
    'method' => 'POST',
    'header' => 'Content-Type: application/json',
    'content' => json_encode($ips)
  )
);
$response = json_decode(file_get_contents($endpoint, false, stream_context_create($options)), true);
foreach ($response as $ipwhois) {
  echo $ipwhois['ip'] . ' - ' . $ipwhois['country'] . ' ' . $ipwhois['flag']['emoji'] . "\n";
}
```

These patterns highlight the minimal client code needed to query single IPs or submit small batches.

[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

### WhoisJSON API — WHOIS and Related Services

WhoisJSON offers a RESTful suite with multiple endpoints across WHOIS, reverse WHOIS, nslookup, SSL certificate checks, random WHOIS, and domain availability. The API emphasizes developer-friendly integration, header-based authentication, and standard HTTP signals for throttling[^11][^13].

#### Base URL, Version, and Endpoints

- Base URL: https://whoisjson.com/api/v1  
- API version: 1.0.0  
- Response formats: JSON, XML  
- OpenAPI spec: available for schema validation[^11][^14]

Table 6 lists the principal endpoints and purposes.

To ground endpoint selection, the following table maps paths to functions.

Table 6. Endpoint catalog

| Method | Path               | Purpose                             |
|--------|--------------------|-------------------------------------|
| GET    | /whois             | Retrieve WHOIS data                 |
| GET    | /reverseWhois      | Reverse WHOIS from an IP            |
| GET    | /nslookup          | DNS records for a domain            |
| GET    | /ssl-cert-check    | SSL certificate details             |
| GET    | /randomWhois       | Random WHOIS (batch sampling)       |
| GET    | /domain-availability | Domain availability check         |

These endpoints cover common WHOIS-centric tasks and adjacent utilities like nslookup and SSL checks.

[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^14]: WhoisJSON OpenAPI Specification (validator).

#### Authentication

- Header-based token: Authorization: TOKEN=<your_token>  
- Requires validated developer account[^11].

This approach aligns with modern API security practices and simplifies client construction.

[^11]: Complete API Reference & Integration Guide - WhoisJson API.

#### Response Formats and Status Codes

- Formats: JSON or XML[^11].  
- HTTP status codes: 200 (Success), 400 (Bad Request), 401 (Unauthorized), 403 (Access Denied), 429 (Limit Exceeded), 500 (Internal error)[^11].

Developers should implement robust handling for 429 and backoff, as the service explicitly signals limit exceeded via HTTP status.

[^11]: Complete API Reference & Integration Guide - WhoisJson API.

#### Rate Limits and Headers

- Free plan: 1,000 requests/month; 20 requests/minute (RPM) throttle[^13].  
- Higher plan throttles (e.g., 40 RPM for Professional) and enterprise custom limits are available[^13].  
- Rate signaling:  
  - HTTP 429 on limit exceeded  
  - Remaining-Requests header indicates remaining quota[^11][^13]

Table 7 summarizes throttling signals.

To make runtime handling explicit, the following table lists limit indicators and how to read them.

Table 7. Rate-limit signaling

| Signal                 | Description                             | How to use in clients                          |
|------------------------|-----------------------------------------|------------------------------------------------|
| HTTP 429               | Usage/Rate limit exceeded               | Backoff and retry after delay                  |
| Remaining-Requests     | Header with remaining requests          | Monitor and throttle client to avoid 429       |

The combination of headers and HTTP status enables straightforward quota-aware clients.

[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.

#### Integration Examples

Python (example pattern using requests):

```python
import requests

headers = {"Authorization": "TOKEN=<your_token>"}
resp = requests.get("https://whoisjson.com/api/v1/whois", headers=headers, params={"domain": "example.com"})
if resp.status_code == 200:
    data = resp.json()
elif resp.status_code == 429:
    remaining = resp.headers.get("Remaining-Requests", "0")
    # Implement backoff based on remaining count and/or time
else:
    # Handle other statuses per API spec
```

PHP (example pattern with cURL):

```php
<?php
$headers = ["Authorization: TOKEN=<your_token>"];
$ch = curl_init("https://whoisjson.com/api/v1/whois?domain=example.com");
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($http_code == 200) {
    $data = json_decode($response, true);
} elseif ($http_code == 429) {
    $remaining = 0;
    foreach ($http_response_header as $h) {
        if (stripos($h, 'Remaining-Requests:') === 0) {
            $remaining = (int)trim(substr($h, strlen('Remaining-Requests:')));
        }
    }
    // Implement backoff strategy
} else {
    // Handle 400/401/403/500 as needed
}
?>
```

These examples demonstrate header-based auth, basic parameterization, and explicit handling of HTTP 429 with remaining quota signals.

[^11]: Complete API Reference & Integration Guide - WhoisJson API.

## Comparative Analysis and Selection Guidance

Selecting the right provider hinges on the target data domain (domain vs IP), the required metadata depth, authentication preferences, and throughput constraints.

- Data domains and WHOIS/RDAP coverage: WhoisXML API delivers domain registration details with options for availability, registry-only data, and proxy indicators. It can select RDAP vs WHOIS and returns parsed fields rather than raw text. WhoisJSON complements this with a RESTful set of endpoints including reverse WHOIS from IP and SSL certificate checks. IPWHOIS.io is IP geolocation-focused, with optional security indicators and bulk processing, but is not designed for domain registrant WHOIS[^1][^2][^6][^11].

- Authentication styles: WhoisXML supports both query-parameter apiKey and Authorization header; WhoisJSON uses a token header; IPWHOIS.io requires an API key for bulk but not for single-IP free lookups[^1][^6][^11].

- Rate-limit signaling and enforcement: WhoisXML uses a cache window and credits, with _hardRefresh=1 costing more. WhoisJSON exposes HTTP 429 and Remaining-Requests headers. IPWHOIS.io allows response-included rate info (limit, remaining) on paid plans and documents free-tier constraints and paid SLAs, but does not explicitly document 429 behavior in the referenced materials[^1][^4][^6][^7][^11][^13].

- Free tier suitability: WhoisXML's 500 calls suit initial development and small tests, with credit-based model scalability. IPWHOIS.io's free tier supports non-commercial, low-volume geolocation; paid plans unlock production features. WhoisJSON's 1,000 calls and per-minute throttles enable controlled testing and early-stage integration[^1][^4][^6][^7][^11][^13].

- Commercial usage and SLA: IPWHOIS.io's free tier is non-commercial and paid plans include a 99.9% SLA. WhoisXML and WhoisJSON require consultation of their Terms of Service for definitive commercial usage specifics; both offer paid plans with operational guarantees[^4][^7][^13].

To crystallize these comparisons, Table 8 presents a side-by-side matrix of capabilities, and Table 9 compares free tiers and rate-limit enforcement.

Before selecting a provider, the following matrices summarize functional and policy differences to guide due diligence.

Table 8. Feature comparison matrix

| Capability                     | WhoisXML API                      | IPWHOIS.io                         | WhoisJSON                         |
|--------------------------------|-----------------------------------|------------------------------------|-----------------------------------|
| Target domain                  | Domain/IP/email WHOIS/RDAP        | IP geolocation                     | Domain/IP WHOIS, nslookup, SSL    |
| Primary endpoint style         | Single WHOIS endpoint + params    | GET path per IP; bulk POST         | Multiple REST paths               |
| Output formats                 | JSON, XML (JSONP)                 | JSON, XML, CSV                     | JSON, XML                         |
| Domain availability check      | Yes (da parameter)                | No                                 | Yes (/domain-availability)        |
| Registry-only data (thin WHOIS)| Yes (thinWhois)                   | N/A                                | Not explicitly documented         |
| Proxy/privacy detection        | Yes (checkProxyData)              | N/A                                | Not explicitly documented         |
| RDAP vs WHOIS selection        | Yes (rdap param)                  | N/A                                | Not documented                    |
| Security indicators (IP)       | N/A                               | Yes (security=1; paid)             | Not documented                    |
| Rate info in response          | Cache/credits; no rate header     | Yes (rate=1; paid)                 | Remaining-Requests header         |
| Bulk endpoint                  | Not documented in refs            | Yes (up to 100 IPs; paid)          | Not documented in refs            |
| Client libraries               | Not listed in refs                | Not listed in refs                 | PHP, Python, Node                 |

This matrix demonstrates functional specialization: WhoisXML is best for domain WHOIS/RDAP depth; IPWHOIS.io excels in IP geolocation with security signals; WhoisJSON provides a developer-oriented REST suite with straightforward rate signaling.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^2]: Output | Documentation - WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.

Table 9. Free tier and rate-limit comparison

| Provider     | Free tier size              | Per-minute throttle     | Enforcement mechanism             | Notes                                  |
|--------------|-----------------------------|-------------------------|-----------------------------------|-----------------------------------------|
| WhoisXML API | 500 calls                   | Not documented here     | Cache 24–48h; _hardRefresh costs 5 credits | Credit-based model; cache semantics     |
| IPWHOIS.io   | < 10,000 requests/month     | Not documented here     | Non-commercial free; paid plans add rate info and SLA | No explicit 429 behavior documented here |
| WhoisJSON    | 1,000 requests/month        | 20 RPM (free)           | HTTP 429; Remaining-Requests header | Higher tiers (e.g., 40 RPM) available   |

Pragmatically, teams needing domain registrant data with protocol choice should start with WhoisXML; those needing IP geolocation can trial IPWHOIS.io non-commercially and upgrade for SLA and bulk; and developers preferring REST plus explicit per-minute throttles may prefer WhoisJSON.

[^4]: Pricing | WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.  
[^7]: IP Geolocation API - Pricing - IPWHOIS.io.  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.

## Integration Playbooks and Best Practices

- Respect rate limits and plan for graceful degradation:
  - Cache results and honor cache windows to reduce calls (WhoisXML's 24–48-hour window is particularly useful for domain polling at modest intervals).
  - Detect and handle rate-limit indicators: WhoisJSON's 429 and Remaining-Requests header; IPWHOIS.io's rate=1 response payload (on paid plans).
  - Implement exponential backoff and circuit breakers to avoid cascading failures[^1][^11][^13].

- Optimize protocol selection and data freshness:
  - Use WhoisXML's rdap parameter to choose RDAP or WHOIS; when freshness is critical, consider _hardRefresh=1, mindful of the 5-credit cost[^1].
  - Use WhoisJSON domain-availability endpoint to triage before WHOIS lookups, reducing unnecessary calls[^11].

- Secure credentials and minimize exposure:
  - Centralize token storage; prefer environment variables and secret managers.
  - Do not expose API keys in front-end code or client-side contexts; IPWHOIS bulk requires server-side key handling, and WhoisJSON requires header-based tokens[^6][^11].

- Bulk considerations:
  - IPWHOIS bulk supports up to 100 IPs per request with a key; use batching, retry with jitter, and monitor rate info when available[^6].
  - For WhoisXML, consider credit budgeting and whether hard refreshes are justified per workload.

- Test and monitor with production-like constraints:
  - Use Postman collections (WhoisXML) to validate request schemas and auth flows under controlled environments[^17].
  - Instrument clients to log response codes, remaining quotas, and cache hits/misses to tune polling frequency and reduce costs[^1][^11][^13].

These practices minimize operational surprises while controlling cost and latency in production.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^13]: WhoisJSON API FAQs.  
[^17]: WhoisXML API Postman Collection.

## Security, Privacy, and Compliance Considerations

- Commercial usage and terms: IPWHOIS.io explicitly restricts the free tier to non-commercial use; paid plans include a 99.9% SLA. WhoisXML and WhoisJSON require consulting Terms of Service for definitive commercial policies and usage boundaries[^4][^7][^13].

- Data minimization: Request only required fields (IPWHOIS fields parameter) and enable minimal output (WhoisXML ignoreRawTexts) to limit exposure and reduce payload sizes[^1][^6].

- Privacy: WHOIS records can include personal data. Ensure handling complies with applicable privacy laws and registrar policies; use registry-only (thinWhois) or proxy detection (checkProxyData) thoughtfully where appropriate[^1].

- Resilience and SLA alignment: Use bulk endpoints where available and ensure monitoring aligns with provider SLAs; IPWHOIS.io's 99.9% SLA on paid tiers and global network PoPs signal production-grade posture[^7].

Document and periodically review compliance posture, especially as free tiers and entry-level plans may carry stricter non-commercial constraints or throttles.

[^4]: Pricing | WHOIS API (WhoisXML).  
[^7]: IP Geolocation API - Pricing - IPWHOIS.io.  
[^13]: WhoisJSON API FAQs.  
[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.

## Appendix — Endpoint Cheat Sheets and Snippet Index

### Endpoint quick reference

Table 10. Endpoint quick reference

| Provider     | Method | URL                                 | Key params (examples)                                           | Auth                           |
|--------------|--------|-------------------------------------|------------------------------------------------------------------|--------------------------------|
| WhoisXML     | GET    | /whoisserver/WhoisService           | domainName, outputFormat, rdap, da, thinWhois, checkProxyData, _hardRefresh | apiKey or Authorization header |
| WhoisXML     | POST   | /whoisserver/WhoisService           | JSON body: domainName, apiKey                                   | apiKey or Authorization header |
| IPWHOIS.io   | GET    | https://ipwho.is/{ip}               | output, fields, lang, security, rate                            | None for single-IP (free)      |
| IPWHOIS.io   | POST   | https://ipwhois.pro/bulk?key=API_KEY| JSON array of IPs                                                | key=API_KEY                    |
| WhoisJSON    | GET    | https://whoisjson.com/api/v1/whois  | domain (example)                                                | Authorization: TOKEN=...       |
| WhoisJSON    | GET    | .../api/v1/reverseWhois             | ip (example)                                                    | Authorization: TOKEN=...       |
| WhoisJSON    | GET    | .../api/v1/nslookup                 | domain                                                          | Authorization: TOKEN=...       |
| WhoisJSON    | GET    | .../api/v1/ssl-cert-check           | domain                                                          | Authorization: TOKEN=...       |
| WhoisJSON    | GET    | .../api/v1/randomWhois              | —                                                                | Authorization: TOKEN=...       |
| WhoisJSON    | GET    | .../api/v1/domain-availability      | domain                                                          | Authorization: TOKEN=...       |

This cheat sheet provides an at-a-glance reference for typical request forms and authentication patterns.

[^1]: Making requests | Documentation - WHOIS API (WhoisXML).  
[^6]: IP Lookup API and IP Geolocation Documentation - IPWHOIS.io.  
[^11]: Complete API Reference & Integration Guide - WhoisJson API.  
[^14]: WhoisJSON OpenAPI Specification (validator).  
[^17]: WhoisXML API Postman Collection.

### Snippet index

- WhoisXML API:
  - GET with apiKey query parameter  
  - POST with JSON body  
  - Authorization header usage[^1][^17]

- IPWHOIS.io:
  - Single-IP lookup (PHP)  
  - Bulk lookup (PHP)[^6]

- WhoisJSON:
  - GET with Authorization header (Python/PHP)  
  - Handling HTTP 429 and Remaining-Requests header[^11][^13]

### Note on scope

This report focuses on WHOIS/RDAP domain data (WhoisXML, WhoisJSON) and IP geolocation/security (IPWHOIS.io). Other providers (e.g., RDAP-only services or IP geolocation vendors) are out of scope unless cited.

## Information Gaps

The following details were not available in the referenced materials and should be confirmed directly with providers before production deployment:

- WhoisJSON per-endpoint parameter details and field-level response schemas (OpenAPI link present; schema specifics not included here)[^11][^14].  
- WhoisJSON paid plan pricing and monthly caps beyond free-tier limits[^13].  
- WhoisXML beyond free credits: per-minute throttles, burst behavior, and explicit HTTP rate-limit headers (cache semantics and hard refresh documented; rate-limit headers not detailed here)[^1][^4].  
- IPWHOIS.io enforcement mechanics for free-tier identification beyond monthly caps; whether HTTP 429 is used and how resets work (response-included rate info documented; HTTP 429 not confirmed in the referenced documentation)[^6][^7].  
- Commercial usage policies: definitive statements for WhoisJSON and WhoisXML free tiers (IPWHOIS free is explicitly non-commercial)[^4][^7][^13].

## Conclusion

The landscape of free WHOIS APIs offers diverse capabilities across domain registration data and IP intelligence. WhoisXML API stands out for comprehensive domain WHOIS/RDAP functionality with flexible parameters and clear caching policies, making it ideal for applications requiring detailed registrant and registration information. IPWHOIS.io excels in IP geolocation and security analysis, though its free tier restricts commercial use and requires paid plans for advanced features. WhoisJSON provides a developer-friendly REST API with reasonable free quotas and clear rate limiting mechanisms, suitable for integration into applications requiring WHOIS data access.

For organizations planning to integrate WHOIS APIs, the key considerations include:
- Balancing free tier capabilities with commercial usage requirements
- Understanding authentication mechanisms and implementing proper security measures
- Developing robust error handling for rate limits and API availability
- Planning for scalability beyond free tiers as application usage grows

The comprehensive documentation and examples provided by all three providers facilitate integration, though some gaps in detailed specifications warrant direct provider consultation for production implementations. Overall, these APIs provide solid foundations for applications requiring WHOIS and IP intelligence data, with clear upgrade paths for increased usage and advanced features.
