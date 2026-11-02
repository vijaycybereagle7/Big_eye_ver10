# DNS, Geolocation, and SSL Certificate APIs: Endpoints, Authentication, Data, Rate Limits, and Integration

## Executive Summary and Scope

This report provides a comparative technical analysis and integration guide for three widely used public APIs spanning Domain Name System (DNS) resolution, IP geolocation, and Secure Sockets Layer/Transport Layer Security (SSL/TLS) server assessment. Specifically, it covers Google Public DNS over HTTPS (DoH), ipapi’s IP geolocation services (ipapi.co and ipapi.com), and Qualys SSL Labs Assessment API (SSL Labs v4). For each, it documents authoritative endpoints, request and response formats, authentication models, rate limiting semantics and operational guidance, and practical integration patterns, with security and privacy considerations woven throughout.

Google Public DNS exposes two DoH interfaces: an RFC 8484-compliant binary wire format and a Google JSON API. These endpoints accept GET and, for RFC 8484, POST; they do not require authentication. They return DNS answers in either wire format or JSON and specify detailed redirect and error semantics, including 429 Too Many Requests and mandatory Retry-After handling.[^1] ipapi provides two related services: a free, unauthenticated REST API at ipapi.co that returns rich location fields and signals quota violations via HTTP 429, and a commercial API at ipapi.com that uses a 32-character access_key, offers bulk lookups with per-request caps, and supplies extended objects (time zone, currency, connection, security). The commercial API also defines numbered error codes for invalid parameters, plan restrictions, and usage limits.[^2][^3][^4] The SSL Labs v4 API is free but controlled: clients must register with an organizational email and include that email in a header for most calls. The API is asynchronous and requires polling analyze to completion, with explicit rate-limiting guidance, response headers for concurrent assessment counts, and error codes such as 429, 503, and 529.[^5][^6]

The remainder of the report proceeds as follows. First, it explains the research approach and data validation methods. Then, it analyzes each API in depth—Google Public DNS, ipapi.co, ipapi.com, and SSL Labs—before comparing them across authentication, rate-limiting, and reliability dimensions. The final sections detail recommended integration patterns, error handling, security and privacy practices, and actionable recommendations for production-grade systems.

## Methodology and Data Validation

The analysis prioritizes official, public-facing sources. For Google Public DNS DoH, the authoritative developer documentation was used to verify endpoints, supported methods, content types, maximum message sizes, caching and redirect behavior, and error semantics.[^1] For ipapi, the ipapi.co API reference provided endpoint taxonomy and response fields, while the ipapi.com documentation confirmed authentication (access_key), bulk lookup constraints, JSONP/CORS support, and commercial plan details.[^2][^3][^4] The SSL Labs assessment API was validated using the project overview and the API v4 documentation maintained by Qualys, which specifies registration requirements, headers, endpoints, polling guidance, rate limit headers, and error codes.[^5][^6]

When details were missing, the report calls them out as information gaps. For example, ipapi.co’s documentation confirms 429 signaling but does not enumerate numeric quotas; ipapi.com describes overage pricing and plan entitlements without specifying hard monthly quotas per tier; and SSL Labs enforces limits via headers and behavior rather than publishing a single numerical limit. These uncertainties are flagged in context to guide prudent engineering judgment.

## Google Public DNS over HTTPS (DoH) – API Deep Dive

Google Public DNS offers two distinct DoH APIs: an RFC 8484 endpoint that transports raw DNS messages and a JSON API tailored for web applications. The service is designed for broad compatibility and strong privacy defaults, with explicit guidance on headers, redirects, and error handling.[^1]

To orient implementers, the following table summarizes the endpoints, methods, parameters, and constraints.

Table 1. Google Public DNS DoH endpoints, methods, and constraints

| API variant | Endpoint | Methods | Key request parameters and body | Content-Type | Max message size | Response format | Notes |
|---|---|---|---|---|---|---|---|
| RFC 8484 | dns.google/dns-query | GET, POST | GET: dns=<Base64Url-encoded DNS message>; POST: binary DNS message | application/dns-message (POST) | 512 bytes (for both POST body and Base64Url GET dns) | Binary DNS response; JSON if Accept indicates | HEAD and other methods not supported; GET improves cacheability |
| JSON | dns.google/resolve | GET | Query parameters define name, type, and other DNS fields | N/A (GET only) | N/A | JSON (e.g., Status, Answer, Question) | Simplified for web apps; no authentication |

The service enforces HTTP semantics rigorously. Clients should be prepared for redirects and must handle errors cleanly.

Table 2. Google DoH HTTP status codes and client actions

| Status | Meaning | Recommended client action |
|---|---|---|
| 200 OK | DNS response returned | Process response; use GET for better cacheability |
| 301/302/307/308 | Redirects | Retry per Location header; cache 301/308 indefinitely; POST retries must remain POST unless new URL specifies GET dns param |
| 400 Bad Request | Invalid request (e.g., malformed dns, no Question, QR=1) | Correct request before retry |
| 413 Payload Too Large | POST body > 512 bytes | Reduce message size |
| 414 URI Too Long | GET dns parameter too large | Reduce size or use POST |
| 415 Unsupported Media Type | Missing/incorrect Content-Type for POST | Set Content-Type: application/dns-message |
| 429 Too Many Requests | Rate limited | Stop and wait per Retry-After header |
| 500 Internal Server Error | Internal error | Retry with backoff |
| 501 Not Implemented | Unsupported HTTP method | Use GET or POST only |
| 502 Bad Gateway | Upstream resolver unreachable | Retry, possibly alternate resolver |

Operational notes and privacy practices

- Do not rely on insecure HTTP. Google Public DNS requires HTTPS for API calls.
- Limit headers. Send only what is necessary (Host, Content-Type for POST, and Accept), and avoid revealing excessive metadata.
- Respect Retry-After on 429 and treat redirects as first-class citizens. Cache permanent redirects as instructed.
- Consider EDNS padding (RFC 8467) to mitigate traffic analysis. Use POST selectively when privacy needs outweigh cacheability and latency costs.[^1]

## ipapi.co – Free IP Geolocation API

ipapi.co provides a straightforward REST API to geolocate IPv4 and IPv6 addresses and to infer the client’s origin IP. Responses are available in JSON, XML, CSV, YAML, and JSONP. The service is free and, in typical usage, does not require authentication, although a 403 Authentication Failed response may be returned in certain conditions. The documentation signals rate limits via HTTP 429, with a structured JSON error payload.[^2]

Endpoints fall into four categories: complete location for a specified IP, single-field retrieval for a specified IP, complete location for the client’s IP, and single-field retrieval for the client’s IP.

Table 3. ipapi.co endpoint matrix

| Function | Method | Path pattern | Formats |
|---|---|---|---|
| Specific IP – complete | GET | /{ip}/{format}/ | json, jsonp, xml, csv, yaml |
| Specific IP – single field | GET | /{ip}/{field}/ | plain text |
| Client IP – complete | GET | /{format}/ | json, jsonp, xml, csv, yaml |
| Client IP – single field | GET | /{field}/ | plain text |

Field catalog and error handling

The complete response includes a broad set of location, identity, and network attributes. The schema uses nulls or empty strings for missing values depending on output format, and 4xx/429 codes to signal client or quota issues.[^2]

Table 4. Key response fields for complete lookups

| Field | Meaning |
|---|---|
| ip, version | Queried IP and version (IPv4/IPv6) |
| city, region, region_code | City and administrative region |
| country_code, country_code_iso3, country_name | Country identifiers and name |
| continent_code | Continent code |
| in_eu | Whether country is in the European Union |
| postal | Postal/ZIP code |
| latitude, longitude, latlong | Geocoordinates and combined form |
| timezone (IANA), utc_offset | Time zone and UTC offset including DST |
| country_calling_code | Dialing code |
| currency, currency_name | Currency code and name |
| languages | Spoken languages (ISO 639 codes) |
| country_area, country_population | Country area and population |
| asn, org | Autonomous system number and organization |
| hostname | Associated host/domain (optional beta add-on) |

Table 5. ipapi.co HTTP errors

| Code | Reason | Typical trigger |
|---|---|---|
| 400 | Bad Request | Malformed request |
| 403 | Authentication Failed | Authentication required in context |
| 404 | URL Not Found | Invalid path |
| 405 | Method Not Allowed | Non-GET request |
| 429 | Rate Limited | Quota exceeded |

Missing values by format: JSON null; CSV empty string; XML empty element; YAML null; plain text field returns None when unavailable.[^2]

## ipapi.com – Commercial IP Geolocation API

The ipapi.com service builds on the same core IP geolocation capabilities but introduces authenticated access, extended data objects, bulk processing, and plan-based entitlements. Authentication uses a 32-character access_key appended to requests, and all communication is over HTTPS. Responses are available in JSON or XML, with optional JSONP callbacks and CORS headers for browser integrations.[^3][^4]

Endpoints and capabilities

- Standard lookup: look up an IPv4/IPv6 address or domain.
- Bulk lookup: submit up to 50 IPs per request; available on business-tier plans.
- Origin (check): infer the client’s public IP.

Table 6. ipapi.com endpoints and key parameters

| Function | Method | Base + path | Key parameters |
|---|---|---|---|
| Standard lookup | GET | https://api.ipapi.com/api/{ip_or_domain} | access_key (required); fields; hostname; security; language; callback; output |
| Bulk lookup | GET | https://api.ipapi.com/api/{ip1,ip2,…} | access_key (required); up to 50 IPs; fields; hostname; security; language; callback; output |
| Origin (check) | GET | https://api.ipapi.com/api/check | access_key (required); fields; hostname; security; language; callback; output |

Response depth varies by plan. The “all plans” dataset contains general information and location; Standard and higher add time zone, currency, and connection data; Business Pro adds security objects such as proxy/TOR/crawler indicators.[^3]

Table 7. Plan features (illustrative, per documentation)

| Plan | Monthly calls | Overage per call | Notable inclusions |
|---|---|---|---|
| Starter | 5,000 | $0.002796 | Core location data |
| Standard | 50,000 | $0.0005196 | Adds time zone, currency, connection |
| Business | 500,000 | $0.00023996 | Adds bulk lookup |
| Business Pro | 2,000,000 | $0.00009999 | Adds security data |

Error handling and parameters

ipapi.com uses HTTP status codes and numbered error codes to distinguish missing or invalid parameters, plan restrictions, and quota exhaustion.

Table 8. ipapi.com error codes

| Code | Meaning | Resolution |
|---|---|---|
| 101 | Missing or invalid access_key | Supply valid key |
| 102 | Inactive user | Check account status |
| 103 | Invalid API function | Use correct path |
| 104 | Usage limit reached | Upgrade or wait for reset; overage applies |
| 105 | Function access restricted | Upgrade plan to unlock |
| 301 | Invalid fields | Correct fields parameter |
| 302 | Too many IPs | Reduce bulk list to ≤50 |
| 303 | Batch not supported on plan | Upgrade to Business/Business Pro |

Selected response objects

The following table highlights commonly used objects and fields to inform schema design and downstream processing.[^3]

Table 9. Selected ipapi.com response objects

| Object | Selected fields | Notes |
|---|---|---|
| ip, type | ip, type (“IPv4”/“IPv6”) | Canonical identifiers |
| location | geoname_id, capital, languages[], country_flag, calling_code, is_eu | Rich locale metadata |
| time_zone | id, current_time, gmt_offset, code, is_daylight_saving | Availability varies by plan |
| currency | code, name, plural, symbol, symbol_native | Plan-dependent |
| connection | asn, isp, sld, tld, carrier, home, organization_type, isic_code, naics_code | Plan-dependent |
| security | is_proxy, proxy_type, is_crawler, is_tor, threat_level, threat_types, anonymizer_status, proxy_level, vpn_service, hosting_facility | Business Pro and above |

Security and integration notes

- Access keys are private; do not expose them in client-side code. Use server-side orchestration for browser-heavy apps, leveraging CORS safely.
- JSONP callbacks are supported for legacy integrations; prefer modern CORS-protected patterns where possible.
- The fields parameter can be used to reduce payload size; the hostname and security flags slightly increase latency when enabled.[^3][^4]

## SSL Labs (Qualys) – Assessment API v4

SSL Labs exposes a powerful, asynchronous API for assessing the SSL/TLS posture of public servers. The API is free to use but controlled via registration and an email header requirement. Clients initiate assessments and then poll for completion, adhering to published concurrency and rate-limiting guidance.[^5][^6]

Protocol and base URLs

- Main API: https://api.ssllabs.com/api/v4/
- Development API: https://api.dev.ssllabs.com/api/v4/
- Availability check: https://api.ssllabs.com/api/v4/info

Authentication

- Registration is required. Clients call register (POST) with firstName, lastName, email, and organization. Organizational email is required; consumer email providers are not allowed.
- After registration, include email in the header for analyze and getEndpointData calls.[^6]

Endpoints and request patterns

Table 10. SSL Labs endpoints summary

| Endpoint | Method | Purpose | Notes |
|---|---|---|---|
| register | POST | Obtain API access | Requires organizational email |
| info | GET | Check API availability and engine metadata | Returns maxAssessments, currentAssessments, cool-off, messages |
| analyze | GET | Initiate and monitor assessments | Supports startNew, fromCache, all, publish, ignoreMismatch, maxAge |
| getEndpointData | GET | Retrieve endpoint details for host and IP | Use for deep inspection of a single resolved endpoint |
| getStatusCodes | GET | Status code translations | Map codes to human-readable messages |
| getRootCertsRaw | GET | Retrieve root certificate bundle | Query param trustStore selects Mozilla/Apple/Android/Java/Windows |

Rate limiting, concurrency, and polling

The API uses headers to communicate limits and current load, and defines specific errors for overload and misuse. Assessments are intentionally slow (≥60 seconds) to avoid harming target infrastructure.[^6]

Table 11. SSL Labs rate limit headers and behaviors

| Header | Meaning |
|---|---|
| X-Max-Assessments | Maximum concurrent assessments allowed for the client |
| X-Current-Assessments | Current number of active assessments |

Table 12. SSL Labs error codes and recommended actions

| Code | Meaning | Recommended action |
|---|---|---|
| 429 | Too many requests or too many new assessments | Reduce submission rate and concurrency |
| 529 | Service overloaded | Wait 15+ minutes, then retry |
| 503 | Service unavailable (maintenance) | Wait 15+ minutes, then retry |
| 500 | Internal error | Retry with backoff |
| 400 | Invalid parameters | Correct inputs |
| 441 | Unauthorized | Register and include email header |

Polling strategy

- Poll analyze every 5 seconds until the status transitions to IN_PROGRESS, then every 10 seconds until READY or ERROR.
- Use fromCache and maxAge to leverage cached reports when appropriate, balancing freshness with load and time to result.
- Keep concurrency low; test one hostname at a time if not urgent.[^6]

## Comparative Analysis and Decision Matrix

Although these APIs serve different purposes, several integration decisions hinge on common factors: authentication model, rate-limit transparency, data richness, and stability of the interface. The following matrix summarizes key differences that typically influence service selection and architecture.

Table 13. Cross-API comparison

| Dimension | Google Public DNS (DoH) | ipapi.co (Free) | ipapi.com (Commercial) | SSL Labs v4 |
|---|---|---|---|---|
| Primary function | DNS resolution over HTTPS | IP geolocation (free) | IP geolocation (commercial, extended) | SSL/TLS server assessment |
| Endpoints | /dns-query (RFC 8484), /resolve (JSON) | /{ip}/{format}/, /{ip}/{field}/, /{format}/, /{field}/ | /api/{ip_or_domain}, /api/{bulk}, /api/check | /api/v4/register, /info, /analyze, /getEndpointData, /getStatusCodes, /getRootCertsRaw |
| Authentication | None | Typically none; 403 in some contexts | access_key (32 chars) | Registration + email header |
| Response formats | Wire DNS or JSON | JSON/XML/CSV/YAML/JSONP | JSON/XML (+JSONP, CORS) | JSON |
| Rate limiting | 429 with Retry-After | 429 with structured error | Plan-based quotas, numbered error codes; overage billed | Headers X-Max-Assessments, X-Current-Assessments; 429/529/503 |
| Typical usage | Programmatic DNS resolution | Lightweight location inference | Production-grade geolocation, security, and bulk | Scheduled or on-demand TLS posture checks |

Trade-offs and selection guidance

- Google DoH is ideal for DNS where no credentials are desired and strong privacy posture is a requirement; however, clients must implement robust redirect and Retry-After handling and observe the 512-byte limit.[^1]
- ipapi.co is suitable for simple geolocation needs and prototyping without credentials; its lack of published numeric quotas means clients should implement defensive backoff on 429.[^2]
- ipapi.com is fit for production geolocation at scale, especially when security objects, time zone/currency, and bulk lookups are needed; plan entitlements and overage costs are explicit, enabling predictable budgeting.[^3]
- SSL Labs v4 is unmatched for comprehensive TLS assessments, but the asynchronous workflow, header-based concurrency, and registration requirements mean clients must be engineered for polling and throttling from day one.[^5][^6]

## Integration Playbooks (Step-by-Step)

The following playbooks outline reliable patterns that respect each API’s constraints. They emphasize idempotency, retries, and rate-limit courtesy.

Google DoH

- Choose the right variant. Use JSON for web apps needing simple structures; use RFC 8484 for fidelity to DNS wire format and protocol-level control.
- Build requests correctly. For GET RFC 8484, Base64Url-encode the DNS message and pass in the dns parameter; for POST, send binary DNS with Content-Type: application/dns-message. Stay under 512 bytes for both.
- Implement redirects and backoff. Cache 301/308 permanently as instructed. On 429, stop and wait per Retry-After. On 500/502, retry with exponential backoff.
- Minimize headers. Send only Host, Accept, and Content-Type (for POST) unless debugging requires User-Agent.
- Consider privacy. Use EDNS padding (RFC 8467) to reduce traffic analysis. Use POST judiciously to reduce cacheability if stronger privacy is required.[^1]

ipapi.co

- Use straightforward REST paths for specific or client IP lookups. Select JSON/XML/CSV/YAML/JSONP formats per integration needs.
- Validate inputs. Handle invalid IP or reserved IP via JSON error responses; map missing values by format semantics.
- Implement 429 backoff. On quota exceeded, back off and resume when allowed. Since quotas are not published, design adaptive retry windows and monitor error frequency.
- Plan for missing values. Use format-appropriate nulls/empty strings and avoid downstream NPEs.[^2]

ipapi.com

- Store access_key securely server-side. Never embed it in client code. For browser-based apps, route requests through your backend to avoid key exposure; leverage CORS only when appropriate.
- Control payload size with fields. Use fields to shape responses and reduce parsing overhead; enable hostname or security only when needed.
- Respect bulk constraints. Limit to 50 IPs per bulk request; handle 302 “too many IPs” and 303 “batch not supported on plan” by adjusting request size or plan tier.
- Handle numbered error codes. Treat 101 (authentication), 104 (usage limit reached), and plan restrictions (105) as hard stops; implement backoff or upgrade logic as appropriate.
- Use JSONP sparingly. Prefer CORS for modern integrations and secure callback handling.[^3][^4]

SSL Labs v4

- Register first. Submit organization details via register; use the resulting email in subsequent API calls as an HTTP header.
- Start assessments prudently. Use analyze with startNew only when you need a fresh run; otherwise, prefer fromCache with maxAge to reduce load and latency.
- Poll with backoff. Begin at 5-second intervals, then 10 seconds, until status is READY or ERROR. Track X-Max-Assessments and X-Current-Assessments to regulate concurrency.
- Respect overload signals. On 429, reduce concurrency and submission rate; on 529/503, wait at least 15 minutes before retrying.
- Plan a single-hostname cadence when not urgent. The service is intentionally slow to protect target sites; design batch pipelines accordingly.[^6]

## Error Handling, Backoff, and Reliability Engineering

Robust clients treat rate limits and service unavailability as normal operating conditions. The playbook below consolidates cross-API practices and specific error semantics.

Table 14. Unified error playbook

| API | Error | Meaning | Strategy |
|---|---|---|---|
| Google DoH | 429 Too Many Requests | Rate limited | Stop and wait per Retry-After; implement jittered backoff on subsequent retries |
| Google DoH | 500/502 | Server/intermediate failure | Exponential backoff with cap; alternate resolver only if appropriate |
| Google DoH | 413/414/415 | Request malformation | Fix encoding/size/Content-Type; never retry without correction |
| ipapi.co | 429 | Quota exceeded | Exponential backoff; consider migrating to ipapi.com for production |
| ipapi.co | 403/400/404/405 | Client errors | Correct request/path/method; supply credentials where required |
| ipapi.com | 101 | Missing/invalid key | Supply valid key; rotate if compromised |
| ipapi.com | 104 | Usage limit reached | Implement backoff; consider plan upgrade or overage if acceptable |
| ipapi.com | 302/303 | Bulk limits or plan restriction | Reduce bulk list; upgrade plan if bulk is required |
| SSL Labs | 429 | Too many new assessments | Reduce concurrency and submission rate; respect headers |
| SSL Labs | 529/503 | Overload/maintenance | Wait ≥15 minutes; randomize retry delays to avoid thundering herds |
| SSL Labs | 400/441 | Invalid params/unauthorized | Correct inputs; ensure registration and email header present |

Idempotency and caching

- DNS and TLS assessments benefit from caching: use fromCache and maxAge in SSL Labs; use GET in DoH to improve cacheability. Cache permanent redirects indefinitely per Google’s guidance.[^1][^6]
- Deduplicate requests in batch pipelines. For geolocation, cache resolved results per IP and refresh based on acceptable staleness.

## Security and Privacy Considerations

These APIs expose metadata that can be sensitive in aggregate. The following practices minimize risk and ensure compliance with service terms.

- Authentication secrets. Store ipapi.com access_key server-side; never embed in client code. Enforce least privilege and rotate keys if compromised.[^3]
- SSL Labs registration. Use organizational email per policy and include the email header on all applicable calls. Do not share registration credentials across teams without approval.[^6]
- Privacy in DoH. Limit headers to essentials (Host, Accept, Content-Type for POST). Consider EDNS padding (RFC 8467) to hinder traffic analysis. Prefer POST only when privacy needs justify the cacheability and latency trade-offs.[^1]
- TLS trust and cert hygiene. Use the SSL Labs endpoint getRootCertsRaw to retrieve root certificate bundles and align trust stores across environments. This supports consistency in validation logic and troubleshooting.[^6]
- Consumer email restrictions. For SSL Labs, organizational emails are mandatory; consumer email domains are not allowed.[^6]
- CORS and JSONP. For ipapi.com, use CORS thoughtfully and JSONP only when necessary. Avoid exposing keys via browser-accessible endpoints; proxy through your backend if you need browser-initiated requests.[^3][^4]

## Recommendations and Next Steps

1) Choose the right API for the job.  
- DNS-only use cases without credentials: Google Public DNS DoH.  
- Free geolocation for prototypes or low volume: ipapi.co.  
- Production geolocation at scale, especially with security or bulk needs: ipapi.com.  
- Comprehensive TLS posture: SSL Labs v4.

2) Implement an integration checklist.  
- Endpoints: Confirm base URLs and paths; validate method support (GET vs POST).  
- Authentication: None (DoH), access_key (ipapi.com), registration and email header (SSL Labs).  
- Data formats: Wire DNS and JSON (DoH); JSON/XML/CSV/YAML/JSONP (ipapi); JSON/XML (ipapi.com); JSON (SSL Labs).  
- Rate limits: Respect Retry-After (DoH); implement 429 backoff (ipapi); plan entitlements and overage (ipapi.com); monitor X-Max-Assessments/X-Current-Assessments and adhere to 429/529/503 semantics (SSL Labs).  
- Error semantics: Map and handle 4xx/5xx codes, redirect behavior, and service-specific error payloads.

3) Engineer for resilience.  
- Apply adaptive backoff for 429/529/503 and timeouts; randomize retry jitter to avoid synchronized bursts.  
- Cache aggressively where permitted: GET in DoH and cached reports in SSL Labs.  
- Shape payloads via fields and disable optional features (hostname/security) when not needed.

4) Close known gaps.  
- If numeric quotas are required for ipapi.co, contact the provider or instrument empirically with cautious backoff.  
- If SSL Labs concurrency ceilings are critical, consult current values via info and monitor rate-limit headers in production.  
- Keep DoH library and RFC compliance current; revisit documentation periodically for changes.

These steps will help teams maintain reliability while meeting privacy and compliance requirements, and will reduce operational surprises as traffic scales.

## Information Gaps and Assumptions

- ipapi.co does not publish numeric quota values; only 429 signaling is documented.  
- ipapi.com documentation describes plan quotas and overage pricing but does not provide hard monthly limits per plan tier beyond the stated numbers for included calls.  
- Google Public DNS DoH specifies 429 behavior and Retry-After but does not publish specific numeric rate limits.  
- SSL Labs API v4 uses rate limit headers and behavior; no single numerical limit is provided in the analyzed sources.  
- Complete endpoint and response schemas for SSL Labs are extensive; this report references the v4 documentation directly for full details.[^1][^2][^3][^5][^6]

## References

[^1]: DNS-over-HTTPS (DoH) | Public DNS – Google for Developers. https://developers.google.com/speed/public-dns/docs/doh  
[^2]: ipapi.co API Reference. https://ipapi.co/api/  
[^3]: ipapi.com API Documentation. https://ipapi.com/documentation  
[^4]: ipapi – IP Address Lookup and Geolocation API. https://ipapi.co/  
[^5]: SSL Labs APIs – Projects. https://www.ssllabs.com/projects/ssllabs-apis/index.html  
[^6]: SSL Labs API v4 Documentation (GitHub). https://github.com/ssllabs/ssllabs-scan/blob/master/ssllabs-api-docs.md