# Free Threat Intelligence APIs: A Practical Integration Blueprint (VirusTotal, AbuseIPDB, Google Safe Browsing, OTX, Shodan, SecurityTrails, URLhaus, PhishTank, MalwareBazaar, ThreatFox, CIRCL hashlookup, Spamhaus, GreyNoise)

## Executive Summary

Threat intelligence integration can be built rapidly by combining free, well-documented application programming interfaces (APIs) that cover core indicator types—files, URLs, domains, internet protocol (IP) addresses, and network基础设施. This report distills the integration mechanics for thirteen widely used sources: VirusTotal, AbuseIPDB, Google Safe Browsing, AlienVault OTX, Shodan, SecurityTrails, URLhaus, PhishTank, MalwareBazaar, ThreatFox, CIRCL hashlookup, Spamhaus, and GreyNoise. It details the endpoints, request formats, rate limits, authentication, response schemas, and recommended usage patterns to help security engineers design resilient pipelines and practical enrichment workflows.

At a high level, the sources cluster around four core indicator categories:

- Files and hashes: VirusTotal, MalwareBazaar, CIRCL hashlookup.
- URLs and phishing: Google Safe Browsing, URLhaus, PhishTank.
- IPs and infrastructure: AbuseIPDB, Shodan, SecurityTrails, GreyNoise.
- Cross-cutting threat intelligence: AlienVault OTX, ThreatFox, Spamhaus.

These sources collectively enable enrichment for security operations center (SOC) triage, endpoint detection and response (EDR) lookups, phishing triage, firewall and email gateway enforcement, and threat hunting. VirusTotal exposes rich file/URL/domain/IP context and relationships; AbuseIPDB contributes abuse-reported IP evidence; Google Safe Browsing provides URL threat matches against constantly updated lists; OTX supplies community-sourced indicators and pulses; Shodan maps exposed services across the internet; SecurityTrails supplies DNS and domain/IP history; URLhaus and PhishTank offer malware distribution URLs and phishing data; MalwareBazaar and ThreatFox share malware samples and IOCs; CIRCL hashlookup provides fast hash verification; Spamhaus offers both public and commercial access to blocklists and datasets; and GreyNoise adds internet background noise context for IPs to distinguish routine scanning from notable activity.[^1][^6][^9][^14][^19][^26][^28][^32][^35][^37][^41][^43][^46][^49][^50]

Practical recommendations:

- Start with non-authenticated endpoints where available (e.g., Google Safe Browsing, URLhaus, PhishTank, CIRCL hashlookup) to minimize credential management overhead.
- Use API keys for sources that require them (e.g., OTX, Shodan, SecurityTrails, MalwareBazaar, ThreatFox, Spamhaus commercial datasets, GreyNoise Community).
- Respect usage restrictions, quotas, and dataset freshness windows (e.g., Google Safe Browsing; VirusTotal public tier limits; Shodan credits; AbuseIPDB plan caps).
- Architect client-side rate limiting, caching, and backoff to stay within quotas while preserving data quality and timeliness.
- Normalize outputs to a common schema (STIX-like or vendor-agnostic) and deduplicate indicators across sources for consistent downstream usage.

The remainder of this report provides the detailed integration blueprint.

## Methodology and Scope

This report focuses on official documentation and product pages for the listed threat intelligence sources. It emphasizes verifiable endpoints, authentication methods, rate limits, data formats, and practical integration strategies for SOC and detection engineering workflows. Where documentation is explicit, details are reproduced precisely. Where information is not documented or is plan-dependent, we call out the gap and provide prudent integration guidance without speculation.

Limitations include plan-dependent rate limits that may vary over time, rate-limit enforcement nuances (per key vs. per IP), and incomplete schemas in publicly accessible documentation. All usage and integration should conform to the providers’ terms and policies, including constraints on redistribution or commercial usage where applicable.

## Threat Intelligence Source Landscape

The sources can be grouped by the primary indicator types they address and the kind of context they provide. Files/hashes focus on malware samples, hashing, and file reputation; URLs and phishing focus on web-based threats and phishing kits; IPs/infrastructure focus on exposure, reputation, DNS/WHOIS, and internet background noise; and cross-cutting platforms aggregate community indicators and multi-IOC pulses.

To orient the reader, the following categorization summarizes core indicator coverage and community vs. commercial access considerations.

Table 1. Source categorization by primary indicator coverage and access model.

| Source | Core Indicators | Community/Commercial Access Notes |
|---|---|---|
| VirusTotal | Files, URLs, domains, IPs | Public (rate-limited) and Premium tiers; non-commercial restriction on Public tier[^2] |
| AbuseIPDB | IP addresses (abuse reports) | Free and paid plans; daily request caps by plan[^4][^5] |
| Google Safe Browsing | URLs | Free usage with quotas and freshness constraints[^9][^10] |
| AlienVault OTX | IOCs, pulses (multi-IOC) | API key required; community-driven[^14][^16] |
| Shodan | IP exposure, services | API key; Streaming API; credits for scans[^19][^23] |
| SecurityTrails | DNS, domain/IP history | API access; plan-based access; paid structure[^26][^27][^28] |
| URLhaus | Malware URLs | Public API; no authentication documented[^32] |
| PhishTank | Phishing URLs | API requires registration; rate limits documented[^35] |
| MalwareBazaar | Malware samples | Auth-Key required; abuse.ch platforms share auth[^37][^39] |
| ThreatFox | IOCs | Auth-Key required; abuse.ch platforms share auth[^41][^42] |
| CIRCL hashlookup | File hashes | Public API; no key required[^46][^47] |
| Spamhaus | Blocklists and datasets | Public DNSBL fair use; commercial APIs for higher limits[^49][^52][^53] |
| GreyNoise | IP background noise | Community API (free); higher-volume paid tiers[^50][^54] |

The table illustrates how integration patterns often span multiple sources. For example, a phishing triage workflow might call Google Safe Browsing for URL matches, cross-check via URLhaus, and then consult OTX pulses and ThreatFox for related IOCs. A file-based incident could check VirusTotal for multi-engine verdicts and relationships, validate hash via CIRCL hashlookup, and look up malware sample availability via MalwareBazaar.

## Cross-Source Comparison and Selection Guide

Selecting sources for enrichment depends on indicator type, required freshness, acceptable rate limits, authentication friction, and output schema fit. The comparison matrix below distills base endpoints, authentication, rate limits, and formats to enable quick selection.

Table 2. Comprehensive comparison of endpoints, auth, rate limits, and formats.

| Source | Base Endpoint | Primary Indicators | Auth | Rate Limits (free/community) | Response Format |
|---|---|---|---|---|---|
| VirusTotal | vt.com domains; API v3 resources | Files, URLs, domains, IPs | API key | Public: 4 rpm, 500/day; non-commercial[^2] | JSON[^1][^3] |
| AbuseIPDB | api.abuseipdb.com; check/report/blacklist | IPs | API key | Free: 1,000 reports/checks/day; webmaster: 3,000/day[^5] | JSON[^4] |
| Google Safe Browsing | safebrowsing.googleapis.com; threatMatches.find | URLs | API key | Client counts per 24h; 500 URLs per POST; freshness constraints[^9][^10] | JSON[^9] |
| AlienVault OTX | otx.alienvault.com/otxapi/... | IOCs, pulses | API key | Not specified in provided docs | JSON[^14] |
| Shodan | api.shodan.io; streaming API | IP exposure/services | API key | Usage resets monthly; scan credits for paid plans[^19][^21] | JSON[^19][^23] |
| SecurityTrails | api.securitytrails.com | DNS, domain/IP/WHOIS | API key | Plan-dependent | JSON[^26][^28] |
| URLhaus | urlhaus.abuse.ch/api/... | Malware URLs | None | Not documented | JSON[^32] |
| PhishTank | phishtank.com API | Phishing URLs | API key (registered) | Request rate limits documented[^35] | XML/JSON (per docs)[^35] |
| MalwareBazaar | mb-api.abuse.ch/api/v1/ | Malware samples | Auth-Key | Not fully documented; abuse.ch requires auth[^37][^39] | JSON[^37] |
| ThreatFox | threatfox.abuse.ch/api/... | IOCs | Auth-Key | Not documented | JSON[^41][^42] |
| CIRCL hashlookup | hashlookup.circl.lu/... | File hashes | None | Not documented | JSON[^46][^47] |
| Spamhaus | Public DNSBL; SIA REST; datasets API; submit API | Blocklists, datasets, submission | Token/API key (commercial/submission) | Limits endpoint for account; fair use policy for public DNSBL[^49][^52][^53] | JSON/datasets (varies)[^49][^52] |
| GreyNoise | api.greynoise.io; community/v3 endpoints | IPs (noise context) | API key | Community API usage guidelines; paid tiers for higher volume[^54][^50] | JSON[^50] |

The table highlights how authentication and rate limits influence design. VirusTotal’s public tier mandates tight throttling; AbuseIPDB’s daily caps shape batch enrichment strategies; Google Safe Browsing enforces freshness windows and client counts; Shodan’s scan credits are plan-gated; and SecurityTrails’ access is structured around paid tiers. When auth friction is low (e.g., OTX, CIRCL hashlookup, URLhaus), integration can be rapid; when auth is stringent or rate-limited, consider batch processing, caching, and prioritization.

## Integration Architecture and Patterns

A robust integration architecture balances low-latency lookups with rate-limit compliance and normalization across heterogeneous schemas. The patterns below are recommended across the sources:

- REST over HTTPS for all calls; JSON-first where supported.
- API key management in a secure secrets store; rotate keys periodically and apply least privilege.
- Client-side rate limiting, request queuing, and exponential backoff with jitter to avoid bursty traffic.
- Response caching with time-to-live (TTL) tuned to source freshness guidance (e.g., Safe Browsing’s data age constraints).
- Normalization to a vendor-agnostic schema, mapping shared fields like indicator type, value, first seen/last seen, scores/tags, sources, and references.
- Deduplication across sources to minimize redundant enrichment and storage.
- Query planning: use batch endpoints where available (e.g., Safe Browsing POST with up to 500 URLs), aggregate and cache results, and schedule periodic refreshes to respect freshness and rate caps.[^10][^2][^5][^19]

Table 3. Response field mapping: aligning common enrichment fields to vendor-specific outputs.

| Common Field | VirusTotal | AbuseIPDB | Safe Browsing | OTX | Shodan | SecurityTrails | URLhaus | PhishTank | MalwareBazaar | ThreatFox | CIRCL hashlookup | Spamhaus | GreyNoise |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| indicator_type | Resource type (files/urls/domains/ips) | ip | threat type | indicator/pulse metadata | host/service data | domain/ip/dns fields | url | url | file/hash | ioc | hash | dataset/list | ip |
| indicator_value | id or specific field | ipAddress | url | indicator value | ip/hostname | domain/ip | url | url | file hash | ioc value | hash | dnsbl entry | ip |
| first_seen | attributes.first_submission | reportedAt (varies) | list guidance | pulse.created | timestamp | history fields | date_added | submission date | first seen | created | dataset derived | event timestamp | last_seen |
| last_seen | last analysis stats | lastReportedAt | list guidance | modified | timestamp | latest data | lastseen | verification date | last seen | last_seen | dataset derived | updated timestamp | last_seen |
| tags/malware families | tags, engines labels | categories | threat category | pulse tags | product/versions | tags | malware family | phishing kit tag | signature, tag | ioc tag | related tags | blocklist tag | classification tags |
| score/confidence | reputation scores | confidence score | match presence | pulse score | n/a | score fields | threat score | valid flag | confidence via sources | confidence | trust score | advisory | noise score |
| references/source | source | source | list provenance | OTX | Shodan | SecurityTrails | URLhaus | PhishTank | abuse.ch | ThreatFox | CIRCL | Spamhaus | GreyNoise |

This mapping is illustrative and should be refined as each connector is implemented, reflecting actual field names and types in responses. Normalization reduces downstream complexity and enables consistent dashboards, rules, and playbooks.

## Source Deep Dives

### VirusTotal (API v3)

VirusTotal (VT) provides multi-entity context across files, URLs, domains, and IP addresses. API v3 follows REST principles with predictable, resource-oriented URLs and JSON requests and responses.[^1][^3] The public API is limited to 4 requests per minute and 500 per day and must not be used in commercial products or services; premium tiers remove these constraints.[^2]

Key integration elements:

- Authentication: API key carried in headers; always use HTTPS.[^1]
- Core resources and example endpoints:
  - Files: /files/{id} for analysis results; /analyses for submissions.[^1]
  - URLs: /urls for URL scans and /analyses for processing status.[^1]
  - Domains: /domains/{id} for reputation and related entities.[^1]
  - IPs: /ip_addresses/{id} for IP reputation and reports.[^1]
- Rate limits and retry: Public tier mandates strict throttling; implement client-side rate limiting and retry with backoff.
- Schema notes: JSON responses include attributes and relationships across entities (e.g., related samples, URLs, domains).[^1]
- Integration tips: Cache stable attributes (e.g., file size, type), refresh dynamic attributes (e.g., scan results) based on freshness needs; use batch workflows to queue lookups.

Table 4. VirusTotal endpoints by resource and method (representative).

| Resource | Representative Endpoints | Purpose |
|---|---|---|
| Files | /files/{id}; /analyses | Retrieve file reports; submit files for analysis[^1] |
| URLs | /urls; /analyses | Submit URLs and retrieve scan reports[^1] |
| Domains | /domains/{id} | Query domain reputation and relationships[^1] |
| IPs | /ip_addresses/{id} | Query IP reputation and context[^1] |

Table 5. VirusTotal public vs. premium API characteristics.

| Characteristic | Public | Premium |
|---|---|---|
| Rate limits | 4 rpm; 500/day[^2] | Higher, plan-dependent |
| Commercial usage | Not permitted[^2] | Permitted |
| Access scope | Community features, basic context | Full API access, higher quotas |

### AbuseIPDB API

AbuseIPDB exposes an IP abuse database that supports check, report, and blacklist endpoints. Authentication uses an API key, and responses are JSON.[^4] Rate limits vary by plan: free accounts have 1,000 reports and checks per day; verified webmasters receive 3,000 requests per day.[^5]

Key integration elements:

- Base: api.abuseipdb.com (consult official documentation for exact endpoint paths).[^4]
- Common endpoints: check (reputation), report (submit), blacklist (list of reported IPs).[^4]
- Rate limits: Enforced per account plan; daily caps for free/webmaster tiers.[^5]
- Integration tips: Implement caching to avoid repeat lookups; batch checks where possible; handle 429 rate limit responses via backoff.

Table 6. AbuseIPDB endpoints and parameters (representative).

| Endpoint | Method | Purpose | Notes |
|---|---|---|---|
| /check | GET/POST | IP reputation | Include ipAddress, maxAgeInDays (optional)[^4] |
| /report | POST | Submit abuse report | Include ip, categories, comment[^4] |
| /blacklist | GET | Retrieve blacklist | Filter by age, limit[^4] |

### Google Safe Browsing API (v4)

Google Safe Browsing (GSB) allows client applications to check URLs against lists of unsafe web resources. It is free to use with quotas and strict usage restrictions, including data freshness windows.[^9][^10]

Key integration elements:

- Threat detection: threatMatches.find checks URLs against threat lists.[^9]
- Authentication: API key.
- Request constraints: Up to 500 URLs per POST request; clients must not use data older than specified freshness.[^10]
- Integration tips: Build batch lookup flows; cache threat matches while honoring freshness; implement backoff and quota tracking.

Table 7. Safe Browsing v4 request fields and threat types.

| Field | Description |
|---|---|
| client | Client metadata (name/version) |
| threatTypes[] | e.g., malware, social engineering |
| platformTypes[] | Platform constraints |
| threatMatches[] | List of URL patterns to check |
| requestChecksum | Optional integrity checks[^9] |

Table 8. Quotas and freshness constraints summary.

| Constraint | Guidance |
|---|---|
| Client request counts | Per 24-hour period per API key[^10] |
| URLs per request | Up to 500 per POST[^10] |
| Data age | Must not use data older than service-specified windows[^10] |

### AlienVault OTX

AlienVault Open Threat Exchange (OTX) is a community-driven platform for sharing indicators and pulses. The API uses an API key and returns JSON; it enables synchronizing indicators into security tools.[^14][^16]

Key integration elements:

- Base: otx.alienvault.com; endpoints under otxapi (consult official docs).[^14][^16]
- Common use: Pull subscribed pulses; retrieve indicators; query direct IOC types.
- Rate limits: Not specified in the provided documentation.
- Integration tips: Use pagination and filters; normalize tags, pulse metadata, and indicator types.

Table 9. OTX endpoints for indicators and pulses (representative).

| Endpoint Category | Purpose | Notes |
|---|---|---|
| /otxapi/v1/pulses | List pulses | Filter by subscriber, date[^14] |
| /otxapi/v1/indicators | Query indicators | Filter by type, value[^14] |

### Shodan API

Shodan provides internet-facing exposure data: IP addresses, open ports, services, banners, and certificate metadata. API access requires a key. Streaming API offers real-time JSON feeds.[^19][^23]

Key integration elements:

- Base: api.shodan.io.[^19]
- Endpoints: search, host, stream; internetdb for certain metadata.[^19][^25]
- Authentication: API key; requests per month reset on cadence; scan credits required for certain operations (e.g., scan requests), typically gated to paid plans.[^19][^21]
- Integration tips: Design for monthly reset cycles; cache host data; use streaming feeds for near-real-time detection; consider internetdb for higher rate without key (per blog introduction).[^25]

Table 10. Shodan endpoints and parameters (representative).

| Endpoint | Purpose | Notes |
|---|---|---|
| /shodan/host/{ip} | Retrieve host details | Requires API key; banner data[^19] |
| /shodan/hosts/search | Search across exposure | Query filters and facets[^19] |
| /stream/banners | Real-time stream | JSON; persistent connection[^23] |
| /internetdb | Metadata without key | Higher rate limit; weekly updates[^25] |

Table 11. Rate limit and credit model overview.

| Aspect | Overview |
|---|---|
| Query resets | Monthly cadence[^21] |
| Scan credits | Paid plans required for scans; 1 IP consumes 1 credit[^19] |
| Streaming | Available to authenticated users; real-time JSON[^23] |

### SecurityTrails API

SecurityTrails provides DNS, domain, IP, and WHOIS data with current and historical visibility. Authentication uses an API key; access and limits depend on plan tiers.[^26][^27][^28]

Key integration elements:

- Base: api.securitytrails.com.[^26]
- Endpoint families: Domain (history, current DNS), IP (reverse DNS, geolocation), WHOIS, company data.[^26]
- Rate limits: Plan-dependent; consult product pricing and documentation for quotas.[^28]
- Integration tips: Cache historical snapshots; schedule periodic updates for current data; align queries with plan limits.

Table 12. SecurityTrails endpoint families and representative paths (conceptual).

| Family | Purpose | Representative Path |
|---|---|---|
| Domain | History, records | /domains/{domain}/dns |
| IP | PTR, metadata | /ips/{ip}/ptr |
| WHOIS | Ownership | /domains/{domain}/whois |
| Company | Org data | /companies/{org} |

### URLhaus API

URLhaus shares malware distribution URLs. The public API offers both retrieval and submission without authentication documented.[^32]

Key integration elements:

- Base: urlhaus.abuse.ch/api/... (consult official docs for paths).[^32]
- Common use: Retrieve recent URLs; search by hash, tag, family; submit new URLs (community contribution).
- Rate limits: Not documented in the provided references.
- Integration tips: Cache results and refresh periodically; normalize threat tags and families.

Table 13. URLhaus operations and representative requests.

| Operation | Purpose | Notes |
|---|---|---|
| retrieve | Get recent malware URLs | Filter by tag/family[^32] |
| submit | Contribute new URL | Community-driven[^32] |

### PhishTank API

PhishTank maintains a database of phishing URLs and offers an API with rate limiting and registration requirements.[^35]

Key integration elements:

- Base: phishtank.com API (consult docs for exact paths).[^35]
- Endpoints: check (validate URL), submit (contribute phishing data).[^35]
- Authentication: API key for registered users.
- Rate limits: Request rate limits documented to reduce abuse.[^35]
- Integration tips: Implement retry/backoff; batch checking; track verification status.

Table 14. PhishTank endpoints and usage (representative).

| Endpoint | Purpose | Notes |
|---|---|---|
| /check | Validate URL | Requires key; XML/JSON per docs[^35] |
| /submit | Submit phishing URL | Include URL, verified status[^35] |

### MalwareBazaar (abuse.ch)

MalwareBazaar provides access to malware samples. The API is accessed via HTTP POST to a single endpoint and requires an Auth-Key from abuse.ch authentication; responses are JSON.[^37][^39]

Key integration elements:

- Endpoint: mb-api.abuse.ch/api/v1/.[^37]
- Operations: search, details, sample download; many require Auth-Key.[^37]
- Integration tips: Manage auth keys securely; enforce download quotas and rate-limit guards to avoid abuse; normalize signature and tag fields.

Table 15. MalwareBazaar operations (representative).

| Operation | Purpose | Auth Requirement |
|---|---|---|
| search | Find samples by criteria | Auth-Key[^37] |
| details | Retrieve sample metadata | Auth-Key[^37] |
| download | Fetch sample | Auth-Key; quotas apply[^39] |

### ThreatFox (abuse.ch)

ThreatFox is an open IOC sharing platform. The API requires an Auth-Key from abuse.ch; many endpoints return IOC lists with associated metadata.[^41][^42]

Key integration elements:

- Base: threatfox.abuse.ch/api/... (consult docs).[^41]
- Purpose: Query and consume shared IOCs (multi-type).
- Integration tips: Normalize IOC tags, confidence, first/last seen; enforce auth key management; deduplicate with other abuse.ch sources.

Table 16. ThreatFox IOC query parameters and output schema (representative).

| Field | Description |
|---|---|
| ioc_type | URL, domain, hash, IP, etc. |
| ioc_value | Indicator value |
| confidence | Source-derived confidence score |
| tags | Associated malware/activity tags |

### CIRCL hashlookup

CIRCL hashlookup is a public hash verification service for files, supporting MD5, SHA-1, and SHA-256. It does not require authentication.[^46][^47]

Key integration elements:

- Base: hashlookup.circl.lu.[^46]
- Endpoint pattern: /hash/{algorithm}/{hash} or /lookup.[^47]
- Output: JSON including trust/legitimacy indicators and sources; indicates file presence across datasets.[^47]
- Integration tips: Use trust scores and multi-source presence to validate suspicious files; cache lookup results.

Table 17. hashlookup request patterns and output fields.

| Pattern | Purpose | Output Fields |
|---|---|---|
| /hash/{algo}/{hash} | Verify file hash | trust, sources, legitimacy[^47] |
| /lookup | Bulk lookup | Set of hashes and metadata[^46] |

### Spamhaus

Spamhaus provides blocklists and threat intelligence via public DNSBLs (subject to fair use) and commercial APIs. Public DNSBL usage is free for low-volume, non-commercial use; commercial datasets and the Spamhaus Intelligence API (SIA) offer higher limits and structured JSON/REST interfaces. A submission API is available with token-based authentication.[^48][^49][^52][^53][^51]

Key integration elements:

- Public DNSBL: Use via DNS queries; fair use policy applies; not an HTTP API.[^52]
- SIA REST: Limits endpoint provides account limits and usage; JSON outputs.[^49]
- Datasets API: Programmatic access to datasets; quotas enforced; 429/504 errors per usage.[^49]
- Submission API: Token creation via auth portal; POST submissions for blocklist consideration.[^51]
- Integration tips: Use HTTP APIs where quotas and structured outputs are required; adhere to fair use; design backoff around 429/504 responses.

Table 18. Spamhaus access methods vs. limits and output formats.

| Access Method | Output Format | Limits |
|---|---|---|
| Public DNSBL | DNS responses | Fair use; non-commercial low-volume[^52] |
| SIA REST (Intelligence) | JSON | Account-based limits; check via limits endpoint[^49] |
| Datasets API | JSON/datasets | Programmatic access; rate limiting with 429/504[^49] |
| Submission API | JSON | Token required; submission limits apply[^51] |

### GreyNoise

GreyNoise contextualizes IPs by differentiating routine internet background noise from notable activity. The Community API provides free, quick IP lookups; paid tiers support higher volume and additional features (e.g., GNQL search).[^54][^50]

Key integration elements:

- Base: api.greynoise.io.[^50]
- Endpoints: community IP lookup, v3 IP lookup, GNQL search for NOISE dataset.[^50]
- Authentication: API key; premium plans unlock higher throughput.
- Integration tips: Use community lookups to flag IPs that are commonly seen scanning the internet; cross-reference with AbuseIPDB and OTX for corroboration; cache results.

Table 19. GreyNoise endpoints and parameters (representative).

| Endpoint | Purpose | Notes |
|---|---|---|
| /v3/community/ip | Quick IP context | Free; subset of full data[^50] |
| /v3/ip/{ip} | Full IP context | Paid tier; richer signals[^50] |
| GNQL search | Query NOISE dataset | Paid access; richer analytics[^54] |

## Operational Guidance: Rate Limiting, Caching, and Reliability

API rate limits vary widely across providers, and enforcement strategies often depend on account tier and endpoint type. Client-side patterns should enforce conservative pacing and handle standard HTTP errors gracefully.

Key principles:

- Detect throttling: Treat HTTP 429 as rate limit exceeded; slow down and retry with exponential backoff plus jitter.
- Monitor quotas: Track per-source quotas and enforce internal caps to avoid bursts; e.g., AbuseIPDB daily caps, VT public rpm/day limits, Safe Browsing client counts, Shodan monthly credits, SecurityTrails plan quotas.[^2][^5][^10][^19][^28]
- Cache selectively: Align TTLs to source freshness guidance; avoid unnecessary refetches where data changes slowly (e.g., DNS history).
- Fallback behavior: When throttled, queue requests and prioritize critical lookups; persist minimal context locally to avoid repeat calls for the same indicator.
- Respect restrictions: Adhere to non-commercial constraints (e.g., VT Public) and fair use policies (e.g., Spamhaus DNSBL).[^2][^52]

Table 20. Rate limits and retry/backoff matrix per source.

| Source | Rate Limit/Quota (free/community) | Retry/Backoff Guidance |
|---|---|---|
| VirusTotal | Public: 4 rpm, 500/day[^2] | Client-side throttle; queue lookups; backoff on 429 |
| AbuseIPDB | Free: 1,000/day; webmaster: 3,000/day[^5] | Batch checks; daily budget tracking; backoff on 429 |
| Safe Browsing | Client counts; 500 URLs per POST; freshness windows[^10] | Batch POST; track client counts; cache matches per freshness |
| OTX | Not documented | Conservative pacing; pagination; cache pulses |
| Shodan | Monthly resets; scan credits for paid plans[^19][^21] | Track monthly usage; cache host data; backoff on rate errors |
| SecurityTrails | Plan-dependent[^28] | Align batch jobs to plan limits; pre-fetch commonly used datasets |
| URLhaus | Not documented | Cache; periodic refresh; backoff on errors |
| PhishTank | Rate limited[^35] | Implement backoff; respect verification statuses |
| MalwareBazaar | Auth required; quotas implied[^37][^39] | Enforce download caps; backoff on 429 |
| ThreatFox | Auth required; not documented[^41] | Conservative rate; cache IOC lists |
| CIRCL hashlookup | Not documented | Cache hash verification results |
| Spamhaus | Limits endpoint for accounts; DNSBL fair use[^49][^52] | Use limits endpoint; backoff on 429/504 |
| GreyNoise | Community API guidelines[^54] | Cache IP context; prioritize critical lookups |

## Security, Compliance, and Terms of Use

Security and compliance considerations are integral to integration:

- Protect API keys: Store secrets in a secure vault; restrict usage to least privilege; rotate keys periodically and monitor for anomalous use.
- Respect terms: Avoid commercial usage where prohibited (e.g., VirusTotal Public tier); honor Spamhaus DNSBL fair use; comply with dataset licensing for Spamhaus commercial APIs; and apply rate-limit and freshness constraints (e.g., Safe Browsing).[^2][^52][^49][^10]
- Data handling: Implement retention policies aligned to provider terms; track provenance and attribution; sanitize PII where required; and apply policy controls for sharing sensitive outputs.

Table 21. Terms and compliance summary by source.

| Source | Key Terms/Restrictions |
|---|---|
| VirusTotal | Public API non-commercial; strict rate limits; key security required[^2][^1] |
| AbuseIPDB | Daily caps vary by plan; key management; appropriate use of blacklist[^5][^4] |
| Safe Browsing | Freshness windows; client counts; no stale usage[^10] |
| OTX | API key required; community data use; tags/metadata handling[^14] |
| Shodan | API key required; credits/resets; streaming usage[^19][^23] |
| SecurityTrails | Paid access; plan limits; data licensing[^28] |
| URLhaus | Public API; community submission; rate policies[^32] |
| PhishTank | Registration; rate limits; data verification handling[^35] |
| MalwareBazaar | Auth-Key; download quotas; abuse prevention[^37][^39] |
| ThreatFox | Auth-Key; IOC sharing; attribution handling[^41][^42] |
| CIRCL hashlookup | Public API; trust indicators; attribution[^46][^47] |
| Spamhaus | DNSBL fair use; commercial dataset licensing; API quotas[^52][^49] |
| GreyNoise | Community API usage; paid tier gating; data licensing[^54][^50] |

## Implementation Checklist

A disciplined implementation approach improves reliability and compliance:

- Provision credentials: Obtain API keys/tokens where required; record access scopes and expiration policies; store secrets in a secure vault.
- Implement clients: Build idempotent, retryable clients with throttling, backoff, and circuit breaker patterns; validate request/response schemas; add instrumentation for metrics and logs.
- Normalize and deduplicate: Map fields to a common schema; deduplicate indicators across sources; enrich metadata (tags, families, confidence).
- Validate and monitor: Unit test enrichments; load test against rate limits; deploy telemetry for API usage, error rates, and quota consumption; define alerting for throttling and anomalous patterns.

Table 22. Integration checklist with acceptance criteria and validation steps.

| Step | Acceptance Criteria | Validation |
|---|---|---|
| Credential setup | Keys stored in vault; rotation policy defined | Secrets audit; access control review |
| Client build | Rate limiting, backoff, circuit breaker | Unit tests; throttling simulations |
| Schema mapping | Common fields mapped; dedup strategy | Sample ingestion with multiple sources |
| Compliance | Terms reviewed; retention policies set | Legal/compliance sign-off |
| Monitoring | Usage metrics captured; alerts configured | Load tests; dashboard reviews |

## Appendix: Endpoint Cheat Sheet

This cheat sheet consolidates endpoint patterns and auth requirements for quick reference. Paths are representative and may require consultation of official documentation for exact routes and parameters.

Table 23. Endpoint cheat sheet: base, representative paths, auth, and format.

| Source | Base | Representative Paths | Auth | Format |
|---|---|---|---|---|
| VirusTotal | VT domains | /files/{id}; /analyses; /urls; /domains/{id}; /ip_addresses/{id} | API key | JSON[^1] |
| AbuseIPDB | api.abuseipdb.com | /check; /report; /blacklist | API key | JSON[^4] |
| Safe Browsing | safebrowsing.googleapis.com | /v4/threatMatches:find | API key | JSON[^9] |
| OTX | otx.alienvault.com | /otxapi/v1/pulses; /otxapi/v1/indicators | API key | JSON[^14] |
| Shodan | api.shodan.io | /shodan/hosts/search; /shodan/host/{ip}; /stream/banners; /internetdb | API key | JSON[^19][^23][^25] |
| SecurityTrails | api.securitytrails.com | /domains/{domain}/dns; /ips/{ip}/ptr; /domains/{domain}/whois | API key | JSON[^26] |
| URLhaus | urlhaus.abuse.ch/api | retrieve; submit | None | JSON[^32] |
| PhishTank | phishtank.com/api | check; submit | API key | XML/JSON[^35] |
| MalwareBazaar | mb-api.abuse.ch/api/v1 | search; details; download | Auth-Key | JSON[^37] |
| ThreatFox | threatfox.abuse.ch/api | query IOCs; browse | Auth-Key | JSON[^41] |
| CIRCL hashlookup | hashlookup.circl.lu | /hash/{algo}/{hash}; /lookup | None | JSON[^46][^47] |
| Spamhaus | docs.spamhaus.com; spamhaus.org | SIA limits; datasets API; DNSBL queries; submit API | Token/API key (commercial/submission) | JSON/DNS[^49][^52][^51] |
| GreyNoise | api.greynoise.io | /v3/community/ip; /v3/ip/{ip}; GNQL search | API key | JSON[^50][^54] |

## Information Gaps

Several plan-dependent or undocumented parameters require confirmation during implementation:

- SecurityTrails: Exact free/community rate limits not documented; plan-specific quotas vary by product tier.[^28]
- AlienVault OTX: Rate limits not specified in the provided documentation.[^14][^16]
- PhishTank: Specific numeric per-day/per-minute limits are not stated in the provided materials; only rate-limiting is documented.[^35]
- URLhaus: Numeric rate limits are not documented.[^32]
- Spamhaus: Public API (non-commercial) numeric rate limits are not explicitly documented beyond fair use policy and dataset-specific constraints.[^52][^49]
- CIRCL hashlookup: Formal rate limits and error codes are not specified in the accessible documentation.[^46][^47]
- GreyNoise: Exact Community API numeric rate limits are not detailed; gated behaviors are described conceptually.[^54][^50]
- Shodan: Free vs. paid query credit specifics for certain endpoints depend on plan; monthly reset behavior is described, but quotas vary by plan tier.[^19][^21][^22]
- MalwareBazaar and ThreatFox: Comprehensive endpoint catalogs and formal rate-limit policies are not fully captured in the provided snippets.[^37][^41]
- MalwareBazaar sample download quotas: While community references cite per-IP/day constraints, the precise official limits should be confirmed against abuse.ch documentation.[^39]

## References

[^1]: API Overview - VirusTotal documentation. https://docs.virustotal.com/docs/api-overview  
[^2]: Public vs Premium API - VirusTotal documentation. https://docs.virustotal.com/reference/public-vs-premium-api  
[^3]: VirusTotal API v3 Overview. https://docs.virustotal.com/reference/overview  
[^4]: AbuseIPDB APIv2 Documentation. https://docs.abuseipdb.com/  
[^5]: API Documentation - AbuseIPDB. https://www.abuseipdb.com/api.html  
[^6]: API Plans & Pricing - AbuseIPDB. https://www.abuseipdb.com/pricing  
[^9]: Overview | Safe Browsing APIs (v4) - Google for Developers. https://developers.google.com/safe-browsing/v4  
[^10]: Usage Restrictions | Safe Browsing APIs (v4) - Google for Developers. https://developers.google.com/safe-browsing/v4/usage-limits  
[^14]: OTX DirectConnect API - LevelBlue - Open Threat Exchange. https://otx.alienvault.com/api  
[^16]: LevelBlue External API documentation - AlienVault OTX. https://otx.alienvault.com/assets/static/external_api.html  
[^19]: API Reference - Shodan Developer. https://developer.shodan.io/api  
[^21]: Choose Your Plan - Shodan Account. https://account.shodan.io/billing  
[^22]: API key - Shodan Developer. https://developer.shodan.io/api/requirements  
[^23]: Streaming API Documentation - Shodan Developer. https://developer.shodan.io/api/stream  
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
[^43]: CIRCL hashlookup. https://hashlookup.circl.lu/  
[^46]: hashlookup CIRCL API - CIRCL. https://www.circl.lu/services/hashlookup/  
[^47]: Spamhaus Intelligence REST API. https://docs.spamhaus.com/sia/docs/source/10-API-Interface/110-API.html  
[^48]: FAQs on data available for commercial use via Spamhaus APIs. https://www.spamhaus.org/faqs/commercial-data/  
[^49]: The Spamhaus Don't Route Or Peer Lists - Fair Use Policy. https://www.spamhaus.org/blocklists/drop-fair-use-policy/  
[^50]: Community API - GreyNoise. https://docs.greynoise.io/reference/get_v3-community-ip  
[^51]: API Documentation - The Spamhaus Project (Submission API). https://submit.spamhaus.org/api/  
[^52]: FAQs | How you can use the free Spamhaus Blocklists. https://www.spamhaus.org/faqs/dnsbl-usage/  
[^53]: Data access | abuse.ch API - Spamhaus Technology. https://www.spamhaus.com/data-access/abusech-api/  
[^54]: Using the GreyNoise Community API. https://docs.greynoise.io/docs/using-the-greynoise-community-api

---

This blueprint is designed to be immediately actionable for SOC engineers, threat intelligence analysts, detection engineers, and security architects who need to integrate and operationalize free threat intelligence APIs. By combining precise endpoint mechanics with disciplined rate-limit handling and normalization, teams can build scalable, resilient enrichment pipelines that improve detection fidelity and incident response outcomes.