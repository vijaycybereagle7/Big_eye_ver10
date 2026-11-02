# AbuseIPDB APIv2: Endpoints, Authentication, Rate Limits, Data Model, and Integration Examples

## Executive Summary

AbuseIPDB APIv2 provides programmatic access to a crowd-sourced repository of IP reputation and abuse reports. It enables security engineers and platform architects to check individual IPs or subnets, retrieve and paginate historical reports, fetch blacklists, report abusive activity, upload bulk reports via CSV, and clear an address of reports that originated from one’s own account. The API is versioned, strictly HTTPS-only, and returns JSON by default, with an optional plaintext mode for blacklist retrieval. Authentication is performed via an API key, preferably supplied in a dedicated HTTP header. Usage varies by subscription tier, with daily limits applied per endpoint. Responses include structured fields such as AbuseConfidenceScore, usage type, ISP, domain, hostnames, country codes, and optionally verbose report entries.

For immediate integration, developers typically begin with the CHECK endpoint to obtain an IP’s abuse confidence score, recent activity, and context, then layer in BLACKLIST for bulk filtering and REPORT/REPORTS to contribute and explore history. CHECK-BLOCK expands coverage to CIDR ranges, and BULK-REPORT and CLEAR-ADDRESS support high-volume operations and self-authored cleanup. Because keys are not intended for client-side use and CORS headers are not set, calls should be issued server-side and over HTTPS[^1][^2].



## API Overview and Core Concepts

The base URL for all APIv2 endpoints is https://api.abuseipdb.com/api/v2. All requests must run over HTTPS. If an insecure HTTP request is attempted, the server responds with a redirect to HTTPS. JSON is the default response format; clients may request plaintext output for the blacklist endpoint by setting the appropriate Accept header or a plaintext query parameter. The API is designed for server-to-server integrations; the API key is not intended for client-side exposure, and CORS headers are not set[^1].

Versioning is explicit in the path (v2), and the service maintains backward compatibility within the v2 namespace while deprecating older versions. Historically, v1 was sunset in 2020 in favor of v2, underscoring the importance of migrating integrations to the current API surface[^7].

Authentication is via API key. The recommended approach is to supply the key in the Key HTTP header. Supplying the key as a query parameter is supported but discouraged to avoid inadvertent exposure through logs. API keys are managed in the account portal, where users can provision and rotate keys. Keys should be treated as credentials—rotate on suspicion and store securely[^1][^2][^3].



## Authentication and Security Best Practices

The APIv2 documentation recommends passing the API key in the dedicated Key header for all endpoints. While the key may be provided as a query parameter for convenience, this is discouraged because URL parameters are more likely to be logged by intermediary systems. Because CORS headers are not set and keys are not intended for client-side use, integrations should perform requests from a trusted server environment. Enforce HTTPS for every call; plaintext HTTP requests will be redirected, but redirect handling can vary by client and is best avoided[^1].

Practical measures include:
- Storing keys in a secret manager or an encrypted configuration store.
- Performing server-side requests only; do not embed keys in mobile apps or browsers.
- Rotating keys periodically or immediately upon suspicion of leakage.
- Applying least privilege where multiple keys are used for different services, and scoping monitoring to detect misuse[^1][^3].



## Endpoints

APIv2 exposes seven core endpoints: CHECK, REPORTS, BLACKLIST, REPORT, CHECK-BLOCK, BULK-REPORT, and CLEAR-ADDRESS. Paths, parameters, and typical responses are summarized below, followed by endpoint-specific details[^1].

To orient the reader, Table 1 presents a consolidated endpoint matrix. This is not a substitute for the detailed descriptions that follow; rather, it provides a quick reference for method, path, purpose, parameters, and response structure.

Table 1. Endpoint matrix
- Purpose: Provide a high-level overview of all endpoints, their methods, parameters, and response shape.
- How to use: Scan the table to select the appropriate endpoint, then read the dedicated subsection for field-level details and examples.

| Name | Method | Path | Purpose | Key Parameters | Typical Response Fields |
|---|---|---|---|---|---|
| CHECK | GET | /check | Check a single IP for abuse reports | ipAddress (required), maxAgeInDays (1–365, default 30), verbose | data: { ipAddress, isPublic, ipVersion, isWhitelisted, abuseConfidenceScore, countryCode, usageType, isp, domain, hostnames, isTor, totalReports, numDistinctUsers, lastReportedAt, reports[] } |
| REPORTS | GET | /reports | Paginate detailed reports for an IP (Open Beta) | ipAddress, maxAgeInDays, page (default 1), perPage (1–100, default 25) | data: { total, page, count, perPage, lastPage, nextPageUrl, previousPageUrl, results[] } |
| BLACKLIST | GET | /blacklist | Fetch most reported IPs | confidenceMinimum (≥25, default 100; subscriber feature), limit (tier-bound), plaintext, onlyCountries (subscriber), exceptCountries (subscriber), ipVersion | meta, data[] (JSON) or plaintext IPs; headers: X-Generated-At |
| REPORT | POST | /report | Submit a new abuse report | ip (required), categories (required), comment (optional), timestamp (optional) | data: { ipAddress, abuseConfidenceScore } |
| CHECK-BLOCK | GET | /check-block | Check a CIDR subnet for reported IPs | network (CIDR), maxAgeInDays (tier-bound) | data: { networkAddress, netmask, minAddress, maxAddress, numPossibleHosts, addressSpaceDesc, reportedAddress[] } |
| BULK-REPORT | POST | /bulk-report | Upload CSV to report many IPs | csv (multipart/form-data) | data: { savedReports, invalidReports[] } |
| CLEAR-ADDRESS | DELETE | /clear-address | Delete reports you submitted for an IP | ipAddress | data: { numReportsDeleted } |


### CHECK (/check)

Purpose and parameters
- Purpose: Retrieve a single IP’s reputation summary and, optionally, detailed reports.
- Required parameters: ipAddress (a valid IPv4 or IPv6 address; URL-encode IPv6 addresses).
- Optional parameters:
  - maxAgeInDays: Only include reports from the last N days (1–365; default 30).
  - verbose: Include detailed report entries and country name; omitting this flag returns a lighter payload.

Table 2. CHECK parameters
- Purpose: Clarify input constraints and defaults for CHECK.

| Name | Required | Type/Constraints | Default | Notes |
|---|---|---|---|---|
| ipAddress | Yes | IPv4/IPv6 | — | URL-encode IPv6 addresses |
| maxAgeInDays | No | 1–365 | 30 | Filters by recency |
| verbose | No | Flag | — | Adds reports[] and countryName |

Response fields
- The response contains a data object with summary and optional detail. The verbose mode exposes a reports array with report-level attributes.

Table 3. CHECK response fields
- Purpose: Enumerate the fields returned by CHECK and highlight the effect of verbose.

| Field | Type | Presence | Notes |
|---|---|---|---|
| ipAddress | string | Always | Queried IP |
| isPublic | boolean | Always | Whether the address is public |
| ipVersion | integer (4/6) | Always | 4 or 6 |
| isWhitelisted | boolean or null | Always | null may indicate lookup not performed |
| abuseConfidenceScore | integer (0–100) | Always | Aggregated confidence of abuse |
| countryCode | string (ISO 3166 alpha-2) | Always | Country code (e.g., US) |
| countryName | string | verbose | Human-readable country |
| usageType | string | Always | Examples include Data Center/Web Hosting/Transit, Commercial, Mobile ISP, Reserved |
| isp | string | Always | ISP name |
| domain | string | Always | Domain name associated with IP |
| hostnames | array of strings | Always | Hostname hints |
| isTor | boolean | Always | Whether the IP is part of the Tor network |
| totalReports | integer | Always | Total number of reports |
| numDistinctUsers | integer | Always | Count of distinct reporters |
| lastReportedAt | string (ISO 8601) | Always | Most recent report timestamp |
| reports[].reportedAt | string (ISO 8601) | verbose | Per-report timestamp |
| reports[].comment | string | verbose | Report comment (avoid PII) |
| reports[].categories | array of integers | verbose | Abuse category IDs |
| reports[].reporterId | integer | verbose | ID of reporter; 0 if anonymous |
| reports[].reporterCountryCode | string | verbose | Reporter’s country code |
| reports[].reporterCountryName | string | verbose | Reporter’s country name |

Example call
- The example uses the Key header and Accept header as recommended[^1]:

```
curl -G https://api.abuseipdb.com/api/v2/check \
  --data-urlencode "ipAddress=118.25.6.39" \
  -d maxAgeInDays=90 \
  -d verbose \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```


### REPORTS (/reports) – Open Beta

Purpose and parameters
- Purpose: Retrieve detailed, paginated report history for a single IP.
- Required parameters: ipAddress.
- Optional parameters: maxAgeInDays (1–365, default 30), page (default 1), perPage (1–100, default 25).
- Status: Open Beta; fields and semantics may evolve.

Table 4. REPORTS pagination parameters and meta fields
- Purpose: Explain pagination controls and meta fields in responses.

| Name | Required | Type/Constraints | Default | Notes |
|---|---|---|---|---|
| ipAddress | Yes | IPv4/IPv6 | — | URL-encode IPv6 |
| maxAgeInDays | No | 1–365 | 30 | Recency filter |
| page | No | ≥1 | 1 | Page number |
| perPage | No | 1–100 | 25 | Results per page |

| Meta Field | Meaning |
|---|---|
| total | Total number of reports matching the query |
| page | Current page index |
| count | Number of results on the current page |
| perPage | Items per page |
| lastPage | Last available page number |
| nextPageUrl | URL to fetch next page (may be null) |
| previousPageUrl | URL to fetch previous page (may be null) |

Response shape
- The results array mirrors the structure of the reports field from the CHECK endpoint, including reportedAt, comment, categories, reporterId, and reporter country fields when available.

Example call
```
curl -G https://api.abuseipdb.com/api/v2/reports \
  --data-urlencode "ipAddress=176.111.173.242" \
  -d page=5 \
  -d perPage=25 \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```


### BLACKLIST (/blacklist)

Purpose and parameters
- Purpose: Retrieve a list of the most reported IP addresses. This is frequently used to feed blocklists or initial triage filters.
- Optional parameters:
  - confidenceMinimum: Minimum abuse confidence score (default 100; minimum enforced at 25). Values below 25 are not considered performant or useful. Subscribers may customize this threshold; non-subscribers receive a simple blacklist.
  - limit: Cap on the number of IP addresses (tier-bound).
  - plaintext: If present, returns newline-separated IPs; also controllable via the Accept header.
  - onlyCountries and exceptCountries: ISO 3166 alpha-2 country filters (subscriber features).
  - ipVersion: Filter by IP version (4 or 6).

Table 5. BLACKLIST parameters and constraints
- Purpose: Clarify blacklist filtering options and subscriber-only features.

| Name | Required | Type/Constraints | Default | Notes |
|---|---|---|---|---|
| confidenceMinimum | No | 25–100 | 100 | ≥25 enforced; subscriber-configurable |
| limit | No | 1 to tier limit | 10000 | Standard 10k; higher for Basic and Premium |
| plaintext | No | Flag | — | Accept: text/plain also works |
| onlyCountries | No | CSV of ISO 3166 alpha-2 | — | Subscriber feature |
| exceptCountries | No | CSV of ISO 3166 alpha-2 | — | Subscriber feature |
| ipVersion | No | 4 or 6 | 4 and 6 | Filter by version |

Response formats
- JSON response includes a meta.generatedAt timestamp and data entries with ipAddress, abuseConfidenceScore, lastReportedAt, and possibly countryCode when country filtering is used.
- Plaintext responses return newline-separated IPs, with X-Generated-At indicating generation time[^1].

Examples
- JSON:
```
curl -G https://api.abuseipdb.com/api/v2/blacklist \
  -d confidenceMinimum=90 \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```
- Plaintext:
```
curl -G https://api.abuseipdb.com/api/v2/blacklist \
  -d confidenceMinimum=90 \
  -d plaintext \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: text/plain"
```


### REPORT (/report)

Purpose and parameters
- Purpose: Submit a new abuse report for a given IP.
- Required parameters: ip, categories (comma-separated integers; up to 30).
- Optional parameters: comment (avoid personally identifiable information), timestamp (ISO 8601; default is current time).

Table 6. REPORT parameters
- Purpose: Specify inputs and validation constraints for submissions.

| Name | Required | Type/Constraints | Default | Notes |
|---|---|---|---|---|
| ip | Yes | IPv4/IPv6 | — | Address to report |
| categories | Yes | Comma-separated integers (max 30) | — | See category IDs |
| comment | No | Free text | — | Avoid PII |
| timestamp | No | ISO 8601 | Now | Time of attack/observation |

Response
- Returns a data object containing ipAddress and abuseConfidenceScore.
- For testing short-term rate limits, submitting a report for 127.0.0.2 is allowed and is treated as a benign test vector[^1][^6].

Example call
```
curl https://api.abuseipdb.com/api/v2/report \
  --data-urlencode "ip=127.0.0.1" \
  -d categories=18,22 \
  --data-urlencode "comment=SSH login attempts with user root." \
  --data-urlencode "timestamp=2023-10-18T11:25:11-04:00" \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```


### CHECK-BLOCK (/check-block)

Purpose and parameters
- Purpose: Analyze an entire subnet (CIDR) to identify reported IPs within the range.
- Required parameters: network (CIDR; URL-encode the value).
- Optional parameters: maxAgeInDays (limits vary by tier).

Tier-dependent constraints and 402 handling
- Network size and maxAgeInDays caps vary by subscription. If a request exceeds the tier’s network-size or maxAgeInDays limit, the API responds with HTTP 402 Payment Required.

Table 7. CHECK-BLOCK tier constraints (examples)
- Purpose: Illustrate how network size and age limits scale with tiers.

| Tier | Max Network Size | maxAgeInDays cap |
|---|---|---|
| Standard | /24 | 30 |
| Basic | /20 | 60 |
| Premium | /16 | 365 |

Response fields
- The response provides subnet metadata and a list of reported addresses within the range.

Table 8. CHECK-BLOCK response fields
- Purpose: Detail the subnet-level payload returned.

| Field | Type | Meaning |
|---|---|---|
| networkAddress | string | Base address of the network |
| netmask | string | Netmask of the network |
| minAddress | string | First address in range |
| maxAddress | string | Last address in range |
| numPossibleHosts | integer | Host count in range |
| addressSpaceDesc | string | Descriptive label |
| reportedAddress[].ipAddress | string | Reported IP within the subnet |
| reportedAddress[].numReports | integer | Number of reports |
| reportedAddress[].mostRecentReport | string (ISO 8601) | Latest report time |
| reportedAddress[].abuseConfidenceScore | integer | Confidence score |
| reportedAddress[].countryCode | string | Country code |

Example call
```
curl -G https://api.abuseipdb.com/api/v2/check-block \
  --data-urlencode "network=127.0.0.1/24" \
  -d maxAgeInDays=15 \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```


### BULK-REPORT (/bulk-report)

Purpose and parameters
- Purpose: Upload a CSV file containing multiple IP reports in a single operation.
- Parameters: csv (multipart/form-data; the file must be supplied as form-data under the csv field).

Table 9. BULK-REPORT request format
- Purpose: Clarify how to submit a CSV upload.

| Field | Type | Required | Notes |
|---|---|---|---|
| csv | multipart/form-data | Yes | Standard file upload field |

Response fields
- Returns savedReports and invalidReports. Each invalid entry includes an error code (e.g., Duplicate IP, Invalid IP, Invalid Category), the problematic input, and the row number.

Table 10. BULK-REPORT response fields
- Purpose: Explain validation outcomes after CSV ingestion.

| Field | Type | Notes |
|---|---|---|
| savedReports | integer | Count of reports successfully saved |
| invalidReports[].error | string | Error classification |
| invalidReports[].input | string | The row input that failed |
| invalidReports[].rowNumber | integer | CSV row index |

Example call
```
curl https://api.abuseipdb.com/api/v2/bulk-report \
  -F csv=@report.csv \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```

Operational considerations
- Use CSV templates and pre-validate IPs and category IDs to reduce invalid submissions. The API provides explicit feedback per row to streamline remediation[^1][^9].


### CLEAR-ADDRESS (/clear-address)

Purpose and parameters
- Purpose: Remove reports that your account has submitted for a specified IP.
- Required parameters: ipAddress.

Table 11. CLEAR-ADDRESS parameters and response
- Purpose: Outline usage and expected response.

| Name | Required | Type | Notes |
|---|---|---|---|
| ipAddress | Yes | IPv4/IPv6 | Address to clear |

| Response Field | Type | Meaning |
|---|---|---|
| numReportsDeleted | integer | Count of reports removed |

Example call
```
curl -X DELETE https://api.abuseipdb.com/api/v2/clear-address \
  --data-urlencode "ipAddress=118.25.6.39" \
  -H "Key: YOUR_OWN_API_KEY" \
  -H "Accept: application/json"
```

Notes
- This operation affects only reports authored by your account and cannot remove third-party submissions[^1].



## Rate Limits, Tiers, and Quotas

The API enforces per-day quotas per endpoint, and the caps vary by subscription tier. Standard (free) users have a baseline set of limits. Higher tiers—Webmaster, Supporter, Basic, and Premium—offer progressively larger quotas and broader capabilities. The docs indicate the presence of rate-limit headers and a X-RateLimit-Reset epoch timestamp; however, detailed semantics (e.g., per-minute vs per-day, and the full set of headers beyond X-RateLimit-Reset) are not explicitly documented and should be treated as an information gap[^1][^4].

Table 12 summarizes daily quotas by tier and endpoint to guide capacity planning.

Table 12. Daily quota matrix by tier and endpoint
- Purpose: Compare maximum daily request volumes across tiers.

| Tier | CHECK | REPORTS | BLACKLIST | REPORT | CHECK-BLOCK | BULK-REPORT | CLEAR-ADDRESS | BLACKLIST IP Limit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Standard (free) | 1,000 | 100 | 5 | 1,000 | 100 | 5 | 5 | 10,000 |
| Webmaster | 3,000 | 500 | 10 | 3,000 | 250 | 10 | 10 | — |
| Supporter | 5,000 | 1,000 | 20 | 1,000 | 500 | 20 | 20 | — |
| Basic | 10,000 | 5,000 | 100 | 10,000 | 1,000 | 100 | 100 | 100,000 |
| Premium | 50,000 | 25,000 | 500 | 50,000 | 5,000 | 500 | 500 | 500,000 |

Table 13 focuses on CHECK-BLOCK constraints, which are often the most relevant for network-level analysis.

Table 13. CHECK-BLOCK constraints by tier
- Purpose: Highlight network size and recency limits for subnet checks.

| Tier | Network Size Cap | maxAgeInDays Cap |
|---|---|---|
| Standard | /24 | 30 |
| Basic | /20 | 60 |
| Premium | /16 | 365 |

Graceful degradation and error handling
- Exceeding CHECK-BLOCK limits returns HTTP 402 Payment Required. This provides a clear signal to either reduce scope (e.g., split the CIDR) or upgrade the plan[^1].
- BLACKLIST requests for non-subscribers return a simple blacklist when custom filtering is requested; the confidenceMinimum parameter is enforced at a minimum of 25 for performance reasons[^1].

Daily limit tracking
- The API includes a X-RateLimit-Reset header with an epoch timestamp for monitoring daily resets. The documentation does not enumerate additional headers (e.g., per-day or per-minute quotas). Treat this as an implementation detail to confirm empirically during integration[^1].



## Request and Response Formats

HTTP methods
- GET endpoints: CHECK, REPORTS, BLACKLIST, CHECK-BLOCK.
- POST endpoints: REPORT (form-urlencoded), BULK-REPORT (multipart/form-data).
- DELETE endpoint: CLEAR-ADDRESS.

Content types and headers
- Default response: JSON (Accept: application/json).
- BLACKLIST can return plaintext: set Accept: text/plain or include plaintext as a query parameter.
- Authentication: pass the API key using the Key header (recommended). A query parameter named key is supported but discouraged[^1][^2].

Error model
- The API uses standard HTTP status codes to indicate outcome. Error payloads follow a JSON API-style structure: an errors array containing objects with detail (message), status (HTTP code), and source (optionally referencing the problematic parameter). When rate limits are exceeded, the service returns 429 Too Many Requests[^1][^10].

Table 14. Parameter passing conventions by endpoint
- Purpose: Clarify where to place parameters for each endpoint.

| Endpoint | Method | Parameter Location |
|---|---|---|
| CHECK | GET | Query parameters (URL encoded) |
| REPORTS | GET | Query parameters |
| BLACKLIST | GET | Query parameters; plaintext via Accept header or flag |
| REPORT | POST | form-urlencoded body |
| CHECK-BLOCK | GET | Query parameters |
| BULK-REPORT | POST | multipart/form-data file upload |
| CLEAR-ADDRESS | DELETE | Query parameters |

Table 15. Error schema (illustrative)
- Purpose: Explain typical fields returned in error responses.

| Field | Type | Presence | Notes |
|---|---|---|---|
| errors[].detail | string | Always | Human-readable message |
| errors[].status | integer | Always | HTTP status code |
| errors[].source.parameter | string | Sometimes | Name of the invalid parameter |



## Data Model and Field Reference

Core fields
- AbuseConfidenceScore: Integer from 0 to 100 indicating the aggregated confidence that an IP is abusive. Scores are computed from crowd-sourced reports and contextual signals[^5].
- Country code and country name: ISO 3166 alpha-2 country codes (e.g., US, CA). countryName is present only in verbose mode or specific endpoints[^1].
- IP metadata: ipVersion (4 or 6), isPublic, isWhitelisted (may be null), isTor, ISP, domain, hostnames, usageType. Country, ISP, and domain context are sourced from IPinfo[^1][^8].
- Activity totals and timestamps: totalReports, numDistinctUsers, lastReportedAt. Per-report timestamps are exposed in verbose reports arrays[^1].

UsageType values
- Examples include Data Center/Web Hosting/Transit, Commercial, Mobile ISP, and Reserved. These labels describe the nature of the IP’s hosting or assignment, which can be useful in risk models (e.g., deprioritizing consumer mobile ISPs or treating data center IPs with heightened scrutiny)[^1].

Report-level fields
- When verbose is enabled, the CHECK endpoint and the REPORTS endpoint return an array of report objects, each containing reportedAt, comment, categories (integer IDs), reporterId (0 if anonymous), and optional reporter country fields[^1][^6].

BLACKLIST fields
- JSON responses include ipAddress, abuseConfidenceScore, lastReportedAt, and optionally countryCode when country filtering is used. Plaintext responses are newline-delimited and include X-Generated-At metadata in headers[^1].

Table 16. Field dictionary (selected)
- Purpose: Provide a concise reference for the most-used fields.

| Field | Type | Typical Values | Notes |
|---|---|---|---|
| abuseConfidenceScore | integer (0–100) | 0–100 | Higher implies more reports and confidence |
| countryCode | string | ISO 3166 alpha-2 | e.g., US, CN, DE |
| countryName | string | Country name | Verbose/endpoint-dependent |
| usageType | string | Data Center/Web Hosting/Transit; Commercial; Mobile ISP; Reserved | Heuristic label |
| isp | string | Operator name | From IPinfo |
| domain | string | e.g., example.net | From IPinfo |
| hostnames | array<string> | e.g., host.example.tld | May be empty |
| isTor | boolean | true/false | Tor exit detection |
| totalReports | integer | ≥0 | Aggregate count |
| numDistinctUsers | integer | ≥0 | Unique reporters |
| lastReportedAt | ISO 8601 | e.g., 2025-09-15T12:34:56Z | Most recent report |
| reports[].categories | array<int> | See categories | Abuse category IDs |
| reports[].reporterId | integer | 0 for anonymous | Verbose-only |
| reports[].comment | string | Free text | Avoid PII |



## Integration Patterns and Examples

Single-IP check (quick triage)
- Use CHECK with maxAgeInDays set to a manageable window (e.g., 30–90 days). If abuseConfidenceScore exceeds your threshold or totalReports is notably high, escalate to verbose mode to review recent reports. This pattern supports fast pre-filtering before any runtime decision.

Subnet analysis ( CHECK-BLOCK )
- For broader visibility, use CHECK-BLOCK to inspect a CIDR range. Compare reportedAddress entries against internal telemetry to validate incidents. If you need larger ranges than your tier allows, consider segmenting the space (e.g., break a /16 into /20s for Basic). Observe the HTTP 402 response as a clear upgrade signal if your network scope exceeds policy[^1].

Blacklist ingestion ( BLACKLIST )
- For bulk ingestion, query BLACKLIST with a confidenceMinimum aligned to your risk tolerance. Non-subscribers receive a simple blacklist; subscribers can tune confidenceMinimum and apply country filters. Store X-Generated-At to monitor staleness and to coordinate refresh cadence. For downstream systems that accept plaintext, request text/plain for efficient processing[^1].

Contributing reports ( REPORT and BULK-REPORT )
- To improve coverage, submit high-quality reports using REPORT with precise categories and anonymized comments. For volume, prepare a CSV and submit via BULK-REPORT. The API returns row-level validation errors for invalid IPs, duplicate entries, or unsupported categories; integrate this feedback to iteratively improve data quality[^1][^6][^9].

Clearing your own reports ( CLEAR-ADDRESS )
- If you need to retract your own submissions—e.g., after mitigating a misconfiguration—invoke CLEAR-ADDRESS with the relevant IP. This only affects your contributions[^1].

Operational guidance
- Use cURL examples as templates in scripts. Detect and log X-RateLimit-Reset to plan retries and daily budget adherence. Centralize API key management in a secure store and enforce server-only usage. For environment-specific testing, use harmless test IPs such as 127.0.0.1 or the documented test vector (127.0.0.2) without risk of collateral impact[^1].



## Known Constraints and Caveats

- HTTPS-only: All requests must be over TLS; HTTP requests are redirected. Plan to use direct HTTPS to avoid redirect handling nuances[^1].
- Keys are server-side only: The API does not set CORS headers and keys are not intended for client-side exposure. Embedding keys in browser or mobile apps risks credential leakage[^1].
- REPORTS is Open Beta: Pagination fields and semantics may evolve; design clients to be resilient to minor changes[^1].
- Network size and maxAgeInDays for CHECK-BLOCK are tier-bound; exceeding caps yields HTTP 402. Enforce checks client-side before issuing requests to prevent avoidable errors[^1].
- ConfidenceMinimum constraints: The API enforces a minimum of 25 for BLACKLIST confidenceMinimum; lower values are not considered performant or useful, and custom filtering is reserved for subscribers[^1].
- v1 deprecation: APIv1 was officially deprecated in 2020; ensure all integrations target v2[^7].



## Appendix

Category IDs and reporting taxonomy
- Abuse categories define the type of abuse being reported and are supplied as integer IDs in REPORT and BULK-REPORT. Consult the official category list for authoritative IDs and descriptions[^6].

API key management
- Obtain and manage API keys via the account portal. Keys can be rotated, and new keys invalidate previous ones immediately. Treat keys as secrets, rotate periodically, and monitor for misuse[^3].

Subscription tiers and feature access
- Paid plans expand daily quotas, relax CHECK-BLOCK constraints, and enable advanced BLACKLIST filtering (confidenceMinimum tuning and country filters). See the plans page for current offerings and pricing[^4].

Legacy v1 vs v2 highlights
- v1 was sunset in early 2020. v2 adds structured endpoints (including REPORTS and CHECK-BLOCK), a consistent JSON API error model, and more explicit rate-limit and quota documentation[^7].

External data sources
- IP geolocation, ISP, and domain context are sourced from IPinfo, which helps explain why some fields (country, domain, ISP) align with IPinfo’s dataset[^8].

Information gaps to note
- The documentation references X-RateLimit-Reset for daily limit tracking but does not fully enumerate all rate-limit headers and semantics (e.g., per-minute quotas or additional headers). Pricing and full plan details vary; confirm on the plans page. Category definitions should be sourced directly from the categories page. Endpoints may evolve; the REPORTS endpoint is explicitly marked Open Beta, and its semantics could change. Treat these as verification points during implementation[^1][^4][^6].



## References

[^1]: AbuseIPDB APIv2 Documentation — https://docs.abuseipdb.com/
[^2]: AbuseIPDB API Overview — https://www.abuseipdb.com/api.html
[^3]: AbuseIPDB Account & API Key Management — https://www.abuseipdb.com/account/api
[^4]: AbuseIPDB Subscription Plans — https://www.abuseipdb.com/account/plans
[^5]: AbuseIPDB FAQ: Abuse Confidence Score — https://www.abuseipdb.com/faq.html#confidence
[^6]: AbuseIPDB Category IDs — https://www.abuseipdb.com/categories
[^7]: AbuseIPDB APIv1 Deprecation Notice — https://www.abuseipdb.com/api.html (noted as v1 sunset)
[^8]: IPinfo (Data Source Referenced by AbuseIPDB) — https://ipinfo.io/?ref=abuseipdb
[^9]: AbuseIPDB Bulk Report Guide — https://www.abuseipdb.com/bulk-report
[^10]: JSON API Error Format — http://jsonapi.org/format/#errors