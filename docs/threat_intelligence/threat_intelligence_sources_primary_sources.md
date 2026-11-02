# Free Threat Intelligence APIs: Integration Blueprint (13 Sources with Primary-Source Validation)

## Executive Summary

Security teams increasingly rely on free threat intelligence sources to augment detections, enrich incidents, and guide triage. This report provides a practical, evidence-based blueprint for integrating 13 widely used, free or freemium sources: VirusTotal, AbuseIPDB, Google Safe Browsing, AlienVault OTX, Shodan, SecurityTrails, URLhaus, PhishTank, MalwareBazaar, ThreatFox, CIRCL hashlookup, Spamhaus, and GreyNoise. It consolidates primary-source documentation into a single reference for security engineers, threat intelligence analysts, detection engineers, and security architects who must balance capability with rate limits, authentication constraints, and compliance.

The analysis focuses on what each source offers, how to call its API using the correct endpoints and formats, how to authenticate, and what rate limits apply. It also provides a robust integration strategy, including normalization, caching, deduplication, and resiliency patterns, with compliance considerations to ensure sustainable and lawful usage.

Key outcomes:

- A precise integration view grounded in official documentation, reducing ambiguity and implementation risk.
- A comparative matrix of authentication models, rate limits, and response formats to guide architectural decisions.
- An actionable blueprint for enriching common SOC workflows across files, URLs, domains, and IP addresses.
- Clear identification of documentation gaps and conservative recommendations where providers do not publish explicit limits.

This blueprint enables teams to quickly stand up connectors that respect provider constraints while maximizing the value of free threat intelligence for detection, response, and threat hunting.[^1][^6][^9][^14][^19][^26][^32][^35][^37][^41][^46][^49][^54]

## Methodology and Validation (Primary Sources First)

The report adheres to a primary-source-first approach. Where official developer documentation was accessible via browser automation, endpoint details, authentication methods, and rate limits were captured directly. Screenshots and structured extractions were used to validate claims and ensure fidelity to the providers’ specifications. Only after exhausting direct documentation attempts did the analysis draw on any secondary summaries, and then strictly to highlight gaps pending confirmation.

- Primary sources are the VirusTotal, AbuseIPDB, Google Safe Browsing, OTX, Shodan, SecurityTrails, URLhaus, PhishTank, MalwareBazaar, ThreatFox, CIRCL hashlookup, Spamhaus, and GreyNoise official documentation pages.
- Where numeric limits were not explicitly documented (e.g., some feeds or community endpoints), the report flags the gap and recommends conservative client-side rate limiting and caching.
- Observed access constraints (e.g., Cloudflare verification prompts or partial pricing pages) are noted, along with their effect on precision.

Table 1. Source access summary: official docs vs. partial/blocked access and validation approach.

| Source | Documentation Status | Access Constraints | Validation Approach |
|---|---|---|---|
| VirusTotal | Full access | None | Direct extraction; screenshots; JSON schemas[^1][^2][^3] |
| AbuseIPDB | Full access | None | Rate-limit tables captured; endpoint examples[^4][^5] |
| Google Safe Browsing | Full access | None | Endpoints, quotas, and usage restrictions captured[^9][^10] |
| AlienVault OTX | Full access | None | API key and endpoint families documented[^14][^16] |
| Shodan | Partial | Cloudflare prompts encountered | Core endpoints verified; credit model documented; pricing partially blocked[^19][^21][^22][^23][^25] |
| SecurityTrails | Full access | Main pricing site partially blocked | API overview, auth, quotas; endpoint families documented[^26][^27][^28] |
| URLhaus | Full access | None | API endpoints, feed frequency; bulk data documented[^32] |
| PhishTank | Full access | None | Endpoint, rate-limit headers, formats documented[^35] |
| MalwareBazaar | Full access | None | Auth-Key requirement; unified POST base; quotas documented[^37][^39] |
| ThreatFox | Full access | None | All endpoints, IOC expiration, auth captured[^41][^42] |
| CIRCL hashlookup | Full access | None | Public endpoints, formats, trust scoring[^46][^47] |
| Spamhaus | Full access | None | API families, token auth, limits endpoint[^49][^51][^53] |
| GreyNoise | Full access | None | Community vs enterprise endpoints; quotas captured[^54][^55][^57] |

## Source-by-Source API Specifications (Primary-Source Grounded)

This section enumerates the base endpoints, authentication, rate limits, key endpoints, response formats, and integration notes for each source, with explicit references to the primary documentation.

### VirusTotal API v3

VirusTotal (VT) provides multi-entity threat intelligence across files, URLs, domains, and IP addresses. API v3 is RESTful and JSON-native, with predictable resource-oriented URLs.[^1] The public API is restricted to 4 requests per minute and 500 per day and must not be used in commercial products or services; premium tiers are required for commercial usage.[^2]

Key integration elements:

- Base URL and endpoints: API v3 resources under the VT domain; core families include files, URLs, domains, and IP addresses.[^1]
- Authentication: API key via request header; use HTTPS only.[^3]
- Rate limits: Public tier: 4 rpm and 500/day; premium tiers have higher quotas.[^2]
- Response format: JSON, including attributes and relationships (e.g., related samples, URLs, domains).[^1]
- Integration considerations: Cache stable metadata (file type, size) and schedule refreshes for dynamic attributes (scan verdicts). Normalize tags and vendor verdicts into a consistent schema.

Table 2. VirusTotal endpoint families and representative paths.

| Resource Family | Representative Endpoint Pattern | Notes |
|---|---|---|
| Files | /files/{id} | Retrieve file analysis by hash or VT ID[^1] |
| Analyses | /analyses | Submit files/URLs and retrieve analysis status[^1] |
| URLs | /urls | Submit and scan URLs; retrieve URL reports[^1] |
| Domains | /domains/{id} | Domain reputation and relationships[^1] |
| IP Addresses | /ip_addresses/{id} | IP reputation and related indicators[^1] |

Table 3. VirusTotal public vs. premium API characteristics.

| Characteristic | Public | Premium |
|---|---|---|
| Quotas | 4 rpm; 500/day[^2] | Higher, plan-dependent |
| Commercial use | Not permitted[^2] | Permitted |
| Scope | Community features, basic context | Full v3 access |

### AbuseIPDB API v2

AbuseIPDB exposes an IP abuse database with endpoints for checking reputation, reporting abuse, retrieving blacklists, and managing reports.[^4][^5] It returns JSON and enforces plan-based daily quotas.

Key integration elements:

- Base URL: api.abuseipdb.com/api/v2/.[^4]
- Authentication: API key via HTTP header (e.g., Key: YOUR_API_KEY).[^4]
- Rate limits: Daily quotas differ by tier. Documentation captured higher-tier quotas (e.g., Basic: 10,000 checks/day; Premium: 50,000 checks/day), and free/webmaster tiers (e.g., 1,000–3,000/day). Always consult current plan tables before implementation.[^4][^5]
- Key endpoints: CHECK, BLACKLIST, REPORT, REPORTS, CHECK-BLOCK, BULK-REPORT, CLEAR-ADDRESS.[^4]
- Response format: JSON with confidence scoring, country data, and optional categories.[^4]
- Integration considerations: Cache repeat lookups; batch checks where possible; handle HTTP 429 via backoff. Strip PII from submissions and never expose API keys client-side.[^4]

Table 4. AbuseIPDB endpoints and daily quotas by tier (as documented).

| Endpoint | Purpose | Example Daily Quotas (Illustrative) |
|---|---|---|
| /check | Reputation lookup | Basic: 10,000/day; Premium: 50,000/day[^4] |
| /blacklist | List reported IPs | Basic: 100/day; Premium: 500/day[^4] |
| /report | Submit abuse | Basic: 5,000/day; Premium: 25,000/day[^4] |

Note: Always verify the current tier table in the official documentation before deployment.[^5]

### Google Safe Browsing API v4

Google Safe Browsing (GSB) checks URLs against lists of unsafe web resources. It provides lookup and update APIs, with strict usage restrictions and freshness requirements.[^9][^10]

Key integration elements:

- Base URL: safebrowsing.googleapis.com/v4/.[^9]
- Authentication: API key (URL parameter or header).[^9]
- Rate limits and freshness: Clients must not use data older than service-specified windows; default quotas are visible in the Google Developer Console; Update API imposes random delays and back-off on errors.[^9][^10]
- Endpoints:
  - threatMatches.find (Lookup): POST up to 500 URLs per request.[^9]
  - threatListUpdates.fetch (Update): Retrieve updates with constraints on call frequency.[^10]
  - fullHashes.find (Update): Full hash matching under specific constraints.[^10]
- Response format: JSON, with threat type, platform type, and match details.[^9]
- Integration considerations: Batch URL checks; cache threat matches within allowed freshness windows; implement backoff when in “back-off mode.”[^10]

Table 5. Safe Browsing request fields and constraints.

| Field | Description |
|---|---|
| client | Client name/version |
| threatTypes[] | Threat categories (e.g., malware, social engineering) |
| platformTypes[] | Platform constraints |
| threatMatches[] | List of URL patterns to match |

Table 6. Quotas and freshness constraints summary.

| Constraint | Guidance |
|---|---|
| Client counts | Quotas per API key (Developer Console)[^9] |
| Batch size | Up to 500 URLs per POST[^9] |
| Data age | Must not exceed service-specified windows[^10] |
| Update API | Random delays; back-off rules[^10] |

### AlienVault OTX

AlienVault Open Threat Exchange (OTX) is a community-driven platform for sharing indicators and pulses. The API uses an API key and returns JSON; endpoints cover pulses, indicators, and direct connect operations.[^14][^16]

Key integration elements:

- Base URL: otx.alienvault.com/otxapi/... (consult official routes).[^14][^16]
- Authentication: API key; pass as a request header or parameter per docs.[^14]
- Rate limits: Not specified in the accessible documentation; design conservatively.
- Response format: JSON; pulses carry tags and indicator lists.[^14]
- Integration considerations: Paginate through pulses; normalize tags and indicator types; treat pulse metadata (author, creation time) as enrichment context.

Table 7. OTX endpoint categories (representative).

| Category | Purpose | Notes |
|---|---|---|
| Pulses | List community pulses | Filter by date, subscriber[^14] |
| Indicators | Query IOCs | Filter by type and value[^14] |
| Direct Connect | Sync indicators | Integration-oriented operations[^16] |

### Shodan API

Shodan maps internet-exposed services and infrastructure. The API requires a key, and certain features consume credits. A Streaming API provides real-time JSON feeds, and InternetDB offers selected network metadata.[^19][^23][^25]

Key integration elements:

- Base URL: api.shodan.io.[^19]
- Authentication: API key required.[^22]
- Rate limits and credits: Query credits and scan credits vary by plan; some operations require paid plans; count queries do not consume credits.[^19][^21]
- Key endpoints:
  - /shodan/host/search: Query exposed services.[^19]
  - /shodan/host/{ip}: Retrieve host details.[^19]
  - /stream/banners: Real-time banner stream.[^23]
  - /shodan/data/internetdb: Network metadata endpoint (InternetDB).[^25]
- Response format: JSON.[^19][^23]
- Integration considerations: Cache host data; monthly reset cadence affects planning; streaming feeds enable near-real-time detection; prefer count queries for exploration.

Table 8. Shodan endpoints and credit consumption.

| Endpoint | Purpose | Credits |
|---|---|---|
| /shodan/host/search | Filtered search | Query credits (plan-dependent)[^19] |
| /shodan/host/{ip} | Host details | Query credits (plan-dependent)[^19] |
| /stream/banners | Real-time stream | Auth required; stream rules[^23] |
| /shodan/data/internetdb | Metadata | No key; higher rate; weekly updates[^25] |

Table 9. Rate limits and reset behavior by plan.

| Plan Aspect | Behavior |
|---|---|
| Reset cadence | Monthly[^21] |
| Scan operations | Require paid plans; 1 IP consumes 1 scan credit[^19] |
| Count queries | No credits consumed[^19] |

Note: Some pricing and detailed quota tables were inaccessible due to Cloudflare verification; consult the account portal for current plan specifics.[^21]

### SecurityTrails API

SecurityTrails provides DNS, domain, IP, and WHOIS data, with both current and historical visibility. Authentication is via API key, and quotas follow monthly and per-second throttling models.[^26][^27]

Key integration elements:

- Base URL: api.securitytrails.com/v1/.[^26]
- Authentication: API key (header recommended).[^26]
- Rate limits: Monthly quotas with per-second throttling (1-second reset window); plan-dependent.[^26]
- Endpoints: Domain, IP, DNS, and WHOIS families; multiple history and current-data endpoints.[^26]
- Response format: JSON.[^26]
- Integration considerations: Cache historical snapshots; align batch jobs to plan quotas; reconcile current vs. historical records for accurate timelines.

Table 10. SecurityTrails endpoint families and representative paths.

| Family | Representative Pattern | Purpose |
|---|---|---|
| Domain | /domains/{domain}/dns | DNS records (current and history)[^26] |
| IP | /ips/{ip}/ptr | Reverse DNS and metadata[^26] |
| WHOIS | /domains/{domain}/whois | Ownership and registration data[^26] |

Table 11. Quota model overview.

| Model Element | Behavior |
|---|---|
| Monthly quotas | Apply across endpoints[^26] |
| Per-second throttling | 1-second reset; avoid bursts[^26] |

Pricing specifics were partially inaccessible during research; consult SecurityTrails’ product pricing pages for current tiers.[^28]

### URLhaus API

URLhaus shares malware distribution URLs and provides both retrieval and submission endpoints. Public feeds and bulk data are available without authentication; some feed access requires login.[^32]

Key integration elements:

- Base URL: urlhaus.abuse.ch/api/... (consult official routes).[^32]
- Authentication: Not required for public API; feed access may require login.[^32]
- Rate limits: Not explicitly documented; respect feed fetch frequency (do not fetch more often than every 10 minutes).[^32]
- Response format: JSON for API; CSV/JSON for feeds.[^32]
- Bulk data access:
  - Hourly batches: datalake.abuse.ch/urlhaus/hourly/ (1.3MB–148MB/hour).[^32]
  - Daily batches: datalake.abuse.ch/urlhaus/daily/ (645MB–1.6GB/day); password for malware samples is “infected.”[^32]
- Integration considerations: Prefer bulk data for large-scale ingestion; cache API responses; normalize threat tags and families.

Table 12. URLhaus operations and bulk access.

| Operation/Feed | Purpose | Notes |
|---|---|---|
| retrieve | Retrieve recent URLs | Public API; no auth[^32] |
| submit | Contribute URL | Community-driven[^32] |
| Feeds (ASN/Country/TLD) | Categorized lists | 10-minute frequency limit; login required[^32] |
| Hourly/Daily batches | Bulk malware URLs | No auth; large files[^32] |

### PhishTank API

PhishTank provides a phishing URL database with an HTTP POST endpoint and strict rate limiting. Responses can be XML (default), PHP, or JSON. Registration is required for higher rate limits and to obtain an app_key.[^35]

Key integration elements:

- Endpoint: POST /checkurl/ (primary check).[^35]
- Authentication: app_key (query parameter) for higher limits; descriptive User-Agent required (e.g., phishtank/[username]).[^35]
- Rate limits: Strict enforcement; violations return HTTP 509; headers communicate current limits (X-Request-Limit, X-Request-Limit-Interval, X-Request-Count).[^35]
- Response formats: XML (default), PHP, JSON; fields include in_database, phish_id, verified, valid.[^35]
- Integration considerations: Honor rate-limit headers; parse XML/JSON consistently; attribute User-Agent appropriately.

Table 13. PhishTank endpoint and rate-limit headers.

| Element | Value |
|---|---|
| Endpoint | POST /checkurl/ |
| Rate-limit headers | X-Request-Limit; X-Request-Limit-Interval; X-Request-Count |
| Violation behavior | HTTP 509 (Loop Detected) |

### MalwareBazaar API

MalwareBazaar offers malware sample discovery and retrieval. All requests are submitted via HTTP POST to a unified endpoint, with Auth-Key required for most operations. Responses are JSON. Daily download limits apply.[^37][^39]

Key integration elements:

- Unified base: POST to https://mb-api.abuse.ch/api/v1/ with a query parameter.[^37]
- Authentication: Auth-Key header; keys are obtained from the abuse.ch authentication portal.[^37]
- Rate limits: Daily download limit for file samples (consult the FAQ for exact numbers); list queries typically default to 100 results with a 1,000 maximum; recent detections endpoint allows hours parameter (0–168, default 48).[^37][^39]
- Key queries:
  - submit: Upload malware sample.
  - get_file: Retrieve a sample by SHA256.
  - get_info: Get sample details.
  - recent_detections: Retrieve recent detections.
  - get_taginfo, get_siginfo, get_file_type: Retrieve metadata by tag, signature, or file type.[^37]
- Response format: JSON with query_status and data fields.[^37]
- Integration considerations: Enforce download quotas; sanitize inputs; extract signatures, tags, and hashes into a normalized schema.

Table 14. MalwareBazaar query types and parameters.

| Query | Purpose | Notes |
|---|---|---|
| submit | Upload sample | Multipart form; JSON metadata[^37] |
| get_file | Download sample | SHA256 required; daily quotas[^39] |
| get_info | Sample details | Hash or multiple identifiers[^37] |
| recent_detections | Recent samples | hours parameter (0–168)[^37] |
| get_taginfo | Tag metadata | Tags and counts[^37] |
| get_siginfo | Signature info | Malware family details[^37] |
| get_file_type | File type info | Type metadata[^37] |

### ThreatFox API

ThreatFox is an open platform for sharing indicators of compromise (IOCs). The API is unified via a POST endpoint, requires an Auth-Key, and returns JSON. All 11 endpoints are documented, including IOC retrieval, search, submission, and metadata lookups.[^41][^42]

Key integration elements:

- Base: POST to https://threatfox-api.abuse.ch/api/v1/ with query parameter.[^41]
- Authentication: Auth-Key header (abuse.ch authentication portal).[^41]
- Rate limits: get_iocs is limited to a 7-day maximum range for performance; default pagination is 100 results (max 1,000). IOCs older than six months are removed from the API but remain visible as expired in the UI.[^41]
- Endpoints:
  - get_iocs, ioc (by ID), search_ioc, search_hash, taginfo, malwareinfo, submit_ioc, get_label, malware_list, types, tag_list.[^41]
- Data license: CC0—permissive for commercial and non-commercial use.[^41]
- Integration considerations: Normalize IOC types (domains, IPs, URLs, hashes); incorporate tag and malware family metadata; track IOC expiration policies.

Table 15. ThreatFox endpoints and typical parameters.

| Endpoint | Purpose | Notes |
|---|---|---|
| get_iocs | Recent IOCs | 7-day range; pagination[^41] |
| ioc | IOC by ID | Direct lookup[^41] |
| search_ioc | Search by value | Free-text IOC search[^41] |
| search_hash | Search by hash | MD5/SHA256[^41] |
| taginfo | Query by tag | Tag metadata[^41] |
| malwareinfo | Query by family | Malware taxonomy[^41] |
| submit_ioc | Submit new IOC | Community sharing[^41] |
| get_label | Correct names | Label normalization[^41] |
| malware_list | Supported families | Reference list[^41] |
| types | Threat types | IOC types[^41] |
| tag_list | Available tags | Tag catalog[^41] |

### CIRCL hashlookup

CIRCL hashlookup is a public hash verification service supporting MD5, SHA-1, and SHA-256, with no authentication required. Responses are JSON, with additional hash types (e.g., SHA-512, SSDEEP, TLSH). A trust score (0–100) indicates legitimacy; multiple data sources are referenced. Rate limits are not explicitly documented.[^46][^47]

Key integration elements:

- Base: hashlookup.circl.lu.[^46]
- Endpoints: lookup by hash (MD5/SHA1/SHA256), bulk search, contextual search, session management, and info endpoints.[^46][^47]
- Response format: JSON; includes multiple hash types and trust indicators.[^47]
- Integration considerations: Use trust scores to validate suspicious files; cache results; treat the service as best-effort without guaranteed SLAs.

Table 16. hashlookup request patterns and outputs.

| Pattern | Purpose | Output |
|---|---|---|
| /hash/{algo}/{hash} | Single-hash lookup | Trust score; additional hashes[^47] |
| /lookup | Bulk search | Multiple entries with metadata[^47] |

### Spamhaus Intelligence APIs and Datasets

Spamhaus provides public DNS blocklists (DNSBL) with fair-use constraints and commercial APIs for structured datasets and reputation queries. Authentication for commercial APIs uses bearer tokens obtained via login. Rate limits are exposed via a limits endpoint and vary by subscription tier.[^49][^52][^53]

Key integration elements:

- Access methods:
  - Public DNSBL: Free for low-volume, non-commercial use; fair use policy governs usage.[^52]
  - Spamhaus Intelligence API (SIA): REST endpoints; bearer token auth with 24-hour validity; expose a limits endpoint showing quotas across windows.[^49]
  - Datasets API: Programmatic access to datasets (IP/domain/URLhaus data); NDJSON/JSON/binary outputs.[^49]
  - URLhaus data (beta): Access to URLhaus events within Spamhaus datasets.[^49]
- Authentication: Token-based; creation via the Spamhaus authentication portal.[^51]
- Rate limits: Tier-based; limits endpoint returns applied quotas (e.g., hourly/minute/second) and current usage.[^49]
- Response format: JSON and NDJSON; error responses include 429 (Too Many Requests) and 504 (Gateway Timeout) for rate limiting and gateway issues.[^49]
- Integration considerations: Respect fair use for DNSBL; monitor quotas via limits; implement backoff for 429/504; consult Spamhaus data access guidance for commercial use.[^53]

Table 17. Spamhaus access methods and limits.

| Access Method | Format | Limits |
|---|---|---|
| Public DNSBL | DNS responses | Fair use policy; non-commercial low-volume[^52] |
| SIA REST | JSON | Tier-based; limits endpoint[^49] |
| Datasets API | JSON/NDJSON/binary | Rate-limited; programmatic access[^49] |
| URLhaus data (beta) | JSON | Beta access with quotas[^49] |
| Submission API | JSON | Token-based; submission quotas[^51] |

### GreyNoise API

GreyNoise contextualizes IP activity by differentiating routine internet background noise from notable scanning. The Community API provides limited free lookups; paid tiers unlock GNQL search, time series, and bulk operations.[^54][^55][^57]

Key integration elements:

- Base URL: api.greynoise.io.[^54]
- Authentication: API key for most endpoints; community lookups have lower limits.[^54]
- Rate limits:
  - Community: Approximately 10/day unauthenticated or 50/week for free accounts (plan-dependent).[^54]
  - Enterprise: Higher limits vary by subscription tier.[^57]
- Endpoints:
  - /v3/ip/{ip}: IP lookup with full context (paid tier).[^55]
  - /v3/community/{ip}: Community IP context (subset of data).[^54]
  - /v3/gnql: Query the NOISE dataset using GNQL.[^57]
  - /v3/noise/ips/{ip}/timeline: Time series for IP activity.[^55]
  - /v3/tags: List tags.[^55]
- Response format: JSON; GNQL returns structured results for time series and tags.[^55][^57]
- Integration considerations: Cache IP classifications; distinguish “noise” from notable activity; use community lookups to triage scans and port probes.

Table 18. GreyNoise endpoints and rate-limit tiers.

| Endpoint | Purpose | Tier |
|---|---|---|
| /v3/ip/{ip} | Full IP context | Paid[^55] |
| /v3/community/{ip} | Community context | Free/Community[^54] |
| /v3/gnql | GNQL query | Paid[^57] |
| /v3/noise/ips/{ip}/timeline | Time series | Paid[^55] |
| /v3/tags | Tag listing | Paid[^55] |

## Cross-Source Comparison and Selection Guide

Selecting the right source depends on indicator type, data freshness, authentication friction, and output schema fit. The following matrix distills base endpoints, authentication models, free-tier rate limits (where documented), and response formats across the 13 sources.

Table 19. Comprehensive comparison of endpoints, auth, rate limits, and formats.

| Source | Base Endpoint(s) | Auth Method | Free/Community Limits (Documented) | Response Format |
|---|---|---|---|---|
| VirusTotal | VT domains; v3 resources | API key header | Public: 4 rpm, 500/day; non-commercial[^2] | JSON[^1] |
| AbuseIPDB | api.abuseipdb.com/api/v2/ | API key header | Tier-based daily quotas (e.g., Basic 10k checks/day; Premium 50k checks/day)[^4] | JSON[^4] |
| Google Safe Browsing | safebrowsing.googleapis.com/v4/ | API key | Quotas per key; batch 500 URLs; freshness windows[^9][^10] | JSON[^9] |
| AlienVault OTX | otx.alienvault.com/otxapi/... | API key | Not documented | JSON[^14] |
| Shodan | api.shodan.io; stream; internetdb | API key | Credits per plan; count queries free; scan credits paid[^19][^21] | JSON[^19][^23] |
| SecurityTrails | api.securitytrails.com/v1/ | API key header | Monthly + per-second throttling (plan-dependent)[^26] | JSON[^26] |
| URLhaus | urlhaus.abuse.ch/api/... | None (public API); login for feeds | Feed frequency ≤10 minutes; bulk batches available[^32] | JSON/CSV[^32] |
| PhishTank | phishtank.com/checkurl/ | app_key; User-Agent | Strict rate limiting; headers show current usage[^35] | XML/JSON/PHP[^35] |
| MalwareBazaar | mb-api.abuse.ch/api/v1/ | Auth-Key header | Daily download limit; list queries 100–1,000 results[^37][^39] | JSON[^37] |
| ThreatFox | threatfox-api.abuse.ch/api/v1/ | Auth-Key header | get_iocs limited to 7 days; default 100 results, max 1,000[^41] | JSON[^41] |
| CIRCL hashlookup | hashlookup.circl.lu | None | Not documented | JSON[^46][^47] |
| Spamhaus | api.spamhaus.org; datasets; submission | Bearer token (SIA); public DNSBL | Tier-based quotas; public DNSBL fair use[^49][^52] | JSON/NDJSON/DNS[^49] |
| GreyNoise | api.greynoise.io | API key | Community: ~10/day or 50/week; enterprise higher[^54][^57] | JSON[^54][^55] |

For rapid triage:

- Files/hashes: VirusTotal, MalwareBazaar, CIRCL hashlookup.
- URLs/phishing: Google Safe Browsing, URLhaus, PhishTank.
- IP infrastructure: AbuseIPDB, Shodan, GreyNoise.
- DNS/WHOIS: SecurityTrails.
- Cross-cutting community indicators: OTX, ThreatFox; Spamhaus for blocklist enforcement and dataset access.

## Integration Architecture and Operational Patterns

Free APIs demand disciplined client engineering. This blueprint recommends:

- REST over HTTPS for all endpoints; JSON-first parsing; strict schema validation.
- Secure API key storage in a secrets manager; rotate regularly; never embed keys in client-side code.
- Client-side rate limiting aligned to published quotas; request queuing with exponential backoff and jitter to minimize bursts.
- Caching strategies tuned to each provider’s freshness guidance (e.g., Safe Browsing data age constraints; OTX pulse updates; SecurityTrails historical records).
- Normalization: map outputs to a common schema capturing indicator type, value, first/last seen, tags/families, scores, and source provenance.
- Deduplication: unify indicators across sources to reduce redundant lookups and storage.
- Batch endpoints and feed usage:
  - Safe Browsing supports up to 500 URLs per POST.[^9]
  - URLhaus bulk hourly/daily batches are ideal for large-scale ingestion.[^32]
  - PhishTank returns XML by default; standardize parsing across XML/JSON.[^35]
- Error handling:
  - HTTP 429: back off and retry with jitter; reduce request rate.
  - HTTP 509 (PhishTank): back off and respect headers indicating current limit/interval/count.[^35]
  - Spamhaus 429/504: back off and consult the limits endpoint to adjust request pacing.[^49]

Table 20. Normalized response field mapping (conceptual).

| Common Field | Representative Mapping |
|---|---|
| indicator_type | VT: resource type; AbuseIPDB: ip; GSB: threat type; OTX: indicator; Shodan: host/service; SecurityTrails: domain/ip; URLhaus/PhishTank: url; MalwareBazaar/ThreatFox: file/IOC; CIRCL: hash; Spamhaus: dataset/list; GreyNoise: ip |
| indicator_value | Resource id or specific value field |
| first_seen/last_seen | Source-specific timestamps or derived from event data |
| tags/families | VT tags; OTX pulse tags; MalwareBazaar signatures; ThreatFox tags/malwareinfo |
| scores/confidence | AbuseIPDB confidence; CIRCL trust score; GreyNoise classification; Spamhaus advisory |
| provenance | Source field and link/reference where provided |

## Security, Compliance, and Terms of Use

Providers impose terms that directly affect productization:

- VirusTotal public API is non-commercial and rate-limited; premium is required for commercial use.[^2]
- Spamhaus DNSBL is free for low-volume, non-commercial use under fair use; commercial datasets and SIA require licensing.[^52][^53]
- GreyNoise community tiers are designed for limited use; paid tiers expand capabilities and quotas.[^54][^57]
- AbuseIPDB requires HTTPS and prohibits client-side key exposure; PII stripping is recommended for reports.[^4]
- Google Safe Browsing enforces freshness windows and usage restrictions; proper attribution and user protection notices are mandated.[^10]

Table 21. Terms and usage restrictions by source (high-level).

| Source | Key Terms |
|---|---|
| VirusTotal | Public non-commercial; strict rpm/day limits[^2] |
| Spamhaus | DNSBL fair use; commercial APIs require tokens and licensing[^52][^53] |
| GreyNoise | Community vs enterprise gating; paid tiers increase limits[^54][^57] |
| AbuseIPDB | HTTPS only; never expose keys client-side; PII stripping[^4] |
| Google Safe Browsing | Freshness windows; quotas; attribution and user protection[^10] |

## Use-Case Playbooks (End-to-End Workflows)

This section translates API mechanics into SOC-ready workflows.

1) Phishing triage:
- Step 1: Google Safe Browsing threatMatches.find to detect matches against known threat lists; batch up to 500 URLs per POST; cache results per freshness windows.[^9][^10]
- Step 2: URLhaus retrieve recent URLs to corroborate malicious distribution infrastructure; consider bulk hourly/daily ingestion for large volumes.[^32]
- Step 3: PhishTank /checkurl/ to verify phishing status; honor rate-limit headers and parse XML/JSON consistently.[^35]
- Step 4: OTX pulses to identify related indicators and campaigns; normalize tags for correlation.[^14]
- Decision points: Treat URL matches with high confidence and corroborating evidence as malicious; escalate for user notification and blocklist updates.

2) Malware analysis:
- Step 1: VirusTotal /files/{id} to obtain multi-engine verdicts and relationships; cache stable metadata; schedule dynamic refresh.[^1]
- Step 2: CIRCL hashlookup to validate file hash across multiple sources and retrieve trust scores; treat high trust as indicative of legitimacy.[^46][^47]
- Step 3: MalwareBazaar recent_detections and get_info for samples sharing tags/signature; download samples within daily quotas.[^37][^39]
- Step 4: ThreatFox search_hash and taginfo to discover related IOCs and campaigns; note six-month IOC expiration for API-visible entries.[^41]
- Decision points: Combine engine consensus (VT), trust scoring (CIRCL), and IOC relationships (MalwareBazaar/ThreatFox) to prioritize containment and analysis.

3) IP infrastructure triage:
- Step 1: GreyNoise /v3/community/{ip} to classify background noise vs. notable scanning; cache results to reduce repeat calls.[^54]
- Step 2: AbuseIPDB /check for reputation and confidence scoring; respect daily quotas and strip PII from submissions.[^4]
- Step 3: Shodan /shodan/host/{ip} for exposed services and banners; consider count queries for exploration; streaming feeds for real-time detection.[^19][^23]
- Step 4: SecurityTrails IP and DNS endpoints to map historical PTR and domain associations; cache historical snapshots.[^26]
- Decision points: Use GreyNoise to filter noise; abuse reports (AbuseIPDB) and exposed services (Shodan) to inform firewall or EDR policies; DNS history (SecurityTrails) to surface infrastructure linkages.

Table 22. Workflow step mapping with primary endpoints and normalization targets.

| Workflow | Step | API Endpoint | Normalization Target |
|---|---|---|---|
| Phishing triage | 1 | GSB threatMatches.find | URL threat type; match indicators |
|  | 2 | URLhaus retrieve | URL indicators; tags/families |
|  | 3 | PhishTank /checkurl/ | Phishing verification status |
|  | 4 | OTX pulses | IOC lists; tags; pulse metadata |
| Malware analysis | 1 | VT /files/{id} | Multi-engine verdicts; relations |
|  | 2 | CIRCL hashlookup | Trust score; multi-source hash |
|  | 3 | MalwareBazaar recent_detections/get_info | Sample metadata; signatures |
|  | 4 | ThreatFox search_hash/taginfo | IOC relationships; families |
| IP triage | 1 | GreyNoise /v3/community/{ip} | Noise classification |
|  | 2 | AbuseIPDB /check | Confidence; categories |
|  | 3 | Shodan /shodan/host/{ip} | Services; banners |
|  | 4 | SecurityTrails IP/DNS | Historical associations |

## Appendix A: Endpoint Quick Reference

This appendix consolidates the base URLs and representative endpoint routes for rapid developer reference.

Table 23. Consolidated endpoint cheat sheet with auth requirements.

| Source | Base URL | Representative Routes | Auth Requirement |
|---|---|---|---|
| VirusTotal | VT domain (v3) | /files/{id}; /analyses; /urls; /domains/{id}; /ip_addresses/{id} | API key header[^1][^3] |
| AbuseIPDB | api.abuseipdb.com/api/v2/ | /check; /blacklist; /report; /reports; /check-block; /bulk-report; /clear-address | API key header[^4] |
| Google Safe Browsing | safebrowsing.googleapis.com/v4/ | threatMatches.find; threatListUpdates.fetch; fullHashes.find | API key[^9][^10] |
| AlienVault OTX | otx.alienvault.com/otxapi/... | /pulses; /indicators; Direct Connect operations | API key[^14][^16] |
| Shodan | api.shodan.io | /shodan/host/search; /shodan/host/{ip}; /stream/banners; /shodan/data/internetdb | API key[^19][^22][^23][^25] |
| SecurityTrails | api.securitytrails.com/v1/ | /domains/{domain}/dns; /ips/{ip}/ptr; /domains/{domain}/whois | API key header[^26] |
| URLhaus | urlhaus.abuse.ch/api/... | retrieve; submit; feeds; hourly/daily bulk batches | None (public); feed login[^32] |
| PhishTank | phishtank.com/checkurl/ | POST /checkurl/ | app_key; descriptive User-Agent[^35] |
| MalwareBazaar | mb-api.abuse.ch/api/v1/ | query=submit; query=get_file; query=get_info; query=recent_detections; get_taginfo; get_siginfo; get_file_type | Auth-Key header[^37] |
| ThreatFox | threatfox-api.abuse.ch/api/v1/ | get_iocs; ioc; search_ioc; search_hash; taginfo; malwareinfo; submit_ioc; get_label; malware_list; types; tag_list | Auth-Key header[^41] |
| CIRCL hashlookup | hashlookup.circl.lu | /hash/{algo}/{hash}; /lookup; contextual and session endpoints | None[^46][^47] |
| Spamhaus | api.spamhaus.org; datasets; submission | SIA endpoints; datasets API; URLhaus data; submission API | Bearer token; public DNSBL fair use[^49][^51][^52] |
| GreyNoise | api.greynoise.io | /v3/ip/{ip}; /v3/community/{ip}; /v3/gnql; /v3/noise/ips/{ip}/timeline; /v3/tags | API key[^54][^55][^57] |

## Appendix B: Rate Limit and Error Code Matrix

Table 24. Rate-limit and error code matrix with recommended client behavior.

| Source | Rate-Limit Behavior | Error Codes | Recommended Behavior |
|---|---|---|---|
| VirusTotal | Public: 4 rpm; 500/day | 429 on exceed | Client-side throttle; queue lookups; backoff[^2] |
| AbuseIPDB | Tier-based daily quotas | 429 | Track daily budgets; batch; backoff[^4][^5] |
| Google Safe Browsing | Quotas per key; Update API constraints | 429; back-off mode | Batch POST; respect freshness; backoff[^9][^10] |
| AlienVault OTX | Not documented | — | Conservative pacing; cache pulses[^14] |
| Shodan | Plan-based credits; monthly reset | — | Track credits; prefer count queries; streaming[^19][^21][^23] |
| SecurityTrails | Monthly + per-second throttling | — | Align batch jobs; avoid bursts[^26] |
| URLhaus | Feed frequency ≤10 min; no explicit API rate | — | Prefer bulk batches; cache responses[^32] |
| PhishTank | Strict rate limiting | 509 on violation | Honor rate-limit headers; backoff[^35] |
| MalwareBazaar | Daily download limits; list pagination | — | Enforce quotas; paginate; cache[^37][^39] |
| ThreatFox | get_iocs 7-day limit; default 100, max 1,000 | — | Short date ranges; paginate; cache[^41] |
| CIRCL hashlookup | Not documented | — | Best-effort; cache lookups[^46][^47] |
| Spamhaus | Tier-based quotas; limits endpoint | 429; 504 | Monitor limits; backoff; dataset scheduling[^49] |
| GreyNoise | Community limits (~10/day; 50/week) | — | Cache; triage critical IPs; upgrade for volume[^54][^57] |

## Information Gaps and Mitigation Strategies

Some documentation gaps remain:

- Shodan: Detailed pricing and precise quota numbers were partially inaccessible (Cloudflare prompts). Mitigation: use the account portal and blog announcements to confirm current credit models; implement conservative client-side rate limiting.[^21][^25]
- SecurityTrails: Quotas are documented as monthly and per-second throttles, but precise tier tables were not fully captured. Mitigation: start with conservative per-second pacing and adjust based on observed responses; consult pricing pages for current tiers.[^26][^28]
- AlienVault OTX: Rate limits are not explicitly specified. Mitigation: implement dynamic backoff and caching; avoid burst pagination.[^14][^16]
- PhishTank: Explicit numeric per-minute or per-day limits are not stated in the captured docs. Mitigation: rely on rate-limit headers; back off on 509; consider registering for app_key.[^35]
- URLhaus: API rate limits are not documented; only feed frequency is specified. Mitigation: cache aggressively; prefer bulk batches; contact project maintainers if needed.[^32]
- Spamhaus: Public (non-commercial) numeric limits are not explicit beyond fair use. Mitigation: use the SIA limits endpoint; adopt conservative client-side throttling; consult sales for dataset licensing.[^49][^52][^53]
- CIRCL hashlookup: No formal rate-limit policy. Mitigation: treat as best-effort; cache results; monitor for transient errors.[^46][^47]
- GreyNoise: Community API quotas are documented at a high level; enterprise quotas vary. Mitigation: design for low-volume usage; upgrade to paid tiers for bulk operations.[^54][^57]
- MalwareBazaar and ThreatFox: Comprehensive rate-limit policies are not fully enumerated. Mitigation: enforce client-side caps; paginate and cache; monitor daily download quotas for MalwareBazaar.[^37][^39][^41]

These gaps are documented to ensure transparent risk management. They do not prevent integration but do require careful operational tuning.

## References

[^1]: VirusTotal API v3 Overview. https://docs.virustotal.com/reference/overview  
[^2]: Public vs Premium API - VirusTotal documentation. https://docs.virustotal.com/reference/public-vs-premium-api  
[^3]: VirusTotal API Overview. https://docs.virustotal.com/docs/api-overview  
[^4]: AbuseIPDB APIv2 Documentation. https://docs.abuseipdb.com/  
[^5]: AbuseIPDB API Documentation. https://www.abuseipdb.com/api.html  
[^9]: Overview | Safe Browsing APIs (v4) - Google for Developers. https://developers.google.com/safe-browsing/v4  
[^10]: Usage Restrictions | Safe Browsing APIs (v4). https://developers.google.com/safe-browsing/v4/usage-limits  
[^14]: OTX DirectConnect API - LevelBlue. https://otx.alienvault.com/api  
[^16]: LevelBlue External API documentation - AlienVault OTX. https://otx.alienvault.com/assets/static/external_api.html  
[^19]: API Reference - Shodan Developer. https://developer.shodan.io/api  
[^21]: Choose Your Plan - Shodan Account. https://account.shodan.io/billing  
[^22]: API key - Shodan Developer. https://developer.shodan.io/api/requirements  
[^23]: Streaming API Documentation - Shodan. https://developer.shodan.io/api/stream  
[^25]: Introducing the InternetDB API - Shodan Blog. http://blog.shodan.io/introducing-the-internetdb-api/  
[^26]: SecurityTrails API - Overview. https://docs.securitytrails.com/docs/overview  
[^27]: SecurityTrails API · Apiary. https://securitytrailsrestapi.docs.apiary.io/  
[^28]: SecurityTrails Pricing. https://securitytrails.com/corp/pricing  
[^32]: URLhaus | API - Abuse.ch. https://urlhaus.abuse.ch/api/  
[^35]: PhishTank > API Information. https://www.staging.phishtank.com/api_info.php  
[^37]: MalwareBazaar | API - Abuse.ch. https://bazaar.abuse.ch/api/  
[^39]: FAQ - MalwareBazaar - Abuse.ch. https://bazaar.abuse.ch/faq/  
[^41]: ThreatFox | API - Abuse.ch. https://threatfox.abuse.ch/api/  
[^42]: ThreatFox - Abuse.ch. https://threatfox.abuse.ch/  
[^46]: CIRCL hashlookup. https://hashlookup.circl.lu/  
[^47]: CIRCL Hash Lookup - CIRCL. https://www.circl.lu/services/hashlookup/  
[^49]: Spamhaus Intelligence REST API. https://docs.spamhaus.com/sia/docs/source/10-API-Interface/110-API.html  
[^51]: API Documentation - The Spamhaus Project (Submission API). https://submit.spamhaus.org/api/  
[^52]: The Spamhaus Don't Route Or Peer Lists - Fair Use Policy. https://www.spamhaus.org/blocklists/drop-fair-use-policy/  
[^53]: Data access | abuse.ch API - Spamhaus Technology. https://www.spamhaus.com/data-access/abusech-api/  
[^54]: Using the GreyNoise Community API. https://docs.greynoise.io/docs/using-the-greynoise-community-api  
[^55]: IP Lookup - GreyNoise. https://docs.greynoise.io/reference/v3ip  
[^57]: Using the GreyNoise v3 API (GNQL). https://docs.greynoise.io/docs/using-the-greynoise-api