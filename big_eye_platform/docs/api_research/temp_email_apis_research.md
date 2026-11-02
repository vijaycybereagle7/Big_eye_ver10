# Temporary Email Detection APIs: Debounce, Temp Mail (temp-mail.io), and tempmail.dev — Endpoints, Detection Methods, Response Formats, Domain Coverage, Rate Limits, and Accuracy

## Executive Summary

This report evaluates three services that are frequently referenced in the context of temporary email detection and management: Debounce’s Disposable Detector, Temp Mail (temp-mail.io), and tempmail.dev. Only Debounce’s Disposable Detector is designed specifically to identify disposable emails. Temp Mail (temp-mail.io) is a disposable email generation and inbox management platform; it does not expose a detection API. tempmail.dev could not be assessed due to an outage during research.

Key findings:

- Debounce’s Disposable Detector provides a free endpoint that classifies an email or domain as disposable or not based on a real-time list of disposable domains. The endpoint is callable via a simple GET request, returns a concise JSON payload, and supports cross-origin resource sharing (CORS), enabling client-side use. Rate limits exist but are unspecified in public documentation.[^1][^2][^14]
- Temp Mail (temp-mail.io) offers a full API for programmatic creation of temporary addresses, message retrieval, attachment downloads, domain listing, and rate-limit visibility. Authentication is via API key, rate-limiting is exposed through response headers, and the service is purpose-built for generation and inbox operations—not detection. An official blog announcement confirms API access is available to subscribed users.[^7][^8][^9][^10][^11][^12]
- tempmail.dev was inaccessible (Cloudflare 522 timeout) during the research window, leaving endpoints, detection capabilities, rate limits, and accuracy unknown. A follow-up attempt is required.[^13]

Implications: For disposable email detection, Debounce’s Disposable Detector is the primary option evaluated here. For generating and managing disposable inboxes programmatically, Temp Mail (temp-mail.io) is the appropriate choice. Because tempmail.dev’s status could not be confirmed, engineering teams should plan a re-test and maintain contingency options.

## Scope, Methodology, and Source Quality

Scope. The research focused on official developer documentation, getting-started guides, endpoint references, and rate-limit pages for the three services. For Temp Mail (temp-mail.io), we examined the core endpoints, authentication flow, and rate-limit headers; for Debounce, we examined the Disposable Detector endpoint and public materials on rate limits and FAQs; for tempmail.dev, we attempted direct site access and noted the resulting outage.

Methodology. We prioritized official documentation and product pages. Where available, we extracted concrete specifications (HTTP methods, paths, request/response shapes, authentication modes, and rate-limit signaling). For services that did not publish certain metrics (e.g., disposable domain lists or accuracy statistics), we noted the gaps rather than speculating. All observations reflect documentation and availability as of the time window provided.

Source quality. The strongest documentation quality in this set is from Temp Mail (temp-mail.io), which provides a structured API surface, error model, and rate-limit visibility. Debounce’s Disposable Detector is clearly described with a working endpoint but lacks published rate-limit numbers and an exhaustive domain list. tempmail.dev could not be evaluated due to a connection timeout.[^1][^7][^13]

## API Deep Dive: Debounce Disposable Detector (disposable.debounce.io)

Purpose and positioning. Debounce’s Disposable Detector is a free, public endpoint to check whether a given email address or domain is disposable. It relies on a real-time, maintained list of disposable domains. The service emphasizes easy integration and notes that while daily call and validation speed limits exist, normal usage should not encounter them.[^1][^2][^14]

Endpoint and call pattern. The detector exposes a single GET endpoint at the service root. The only required parameter is “email,” which can be a full address or a domain. A minimal curl example demonstrates the request shape.[^1][^2]

Request and parameters. To illustrate the minimal surface area of the API, Table 1 outlines the request format.

Table 1. Debounce Disposable Detector: Request and parameters

| Field          | Value                         |
|----------------|-------------------------------|
| HTTP method    | GET                           |
| Path           | /                             |
| Required param | email (string; full email or domain) |
| Example call   | curl --request GET "https://disposable.debounce.io/?email=test@example.com" |

Response format. The response is a compact JSON object with a single boolean-like flag indicating disposability. This simplicity eases adoption in client-side forms and server-side validation pipelines.[^1]

Table 2. Debounce Disposable Detector: Response fields

| Field       | Type   | Description                                          | Example       |
|-------------|--------|------------------------------------------------------|---------------|
| disposable  | string | "true" if the input is disposable; otherwise "false" | "true"        |

CORS and client-side usage. The endpoint supports CORS for all origins, which enables direct browser calls without a server proxy. While convenient, client-side calls expose the endpoint URL and make rate-limit enforcement more difficult to control; design accordingly.[^1][^2]

Rate limits. Debounce states that limitations exist for calls per day and validation speed, but specific thresholds are not publicly disclosed. The company advises that typical usage should not trigger them, and the FAQ cautions that API concurrency is capped (e.g., references a maximum of concurrent calls), reinforcing that the service is not intended for bulk validations at high throughput.[^1][^14]

Detection method. The service checks the input against a real-time, up-to-date list of disposable domains. No machine learning, heuristics, or third-party signal fusion are described in public docs.[^1][^2]

Accuracy and domain coverage. Public materials assert an up-to-date list and a “robust” endpoint but do not disclose quantitative accuracy metrics (e.g., precision/recall, false positive/negative rates) or a published list of disposable domains. An external review article claims a gap between vendor claims and third-party audit results; because this is not an official metric, it should be treated as anecdotal context rather than a definitive SLA.[^1][^2][^15]

Integration guidance. In production, prefer server-side mediation to centralize rate-limit handling, cache repeated queries, and ensure consistent policy enforcement. Treat “disposable: true” as a strong signal but consider fallbacks or secondary checks for high-risk flows. Monitor for rate-limit responses and build backoff and caching layers even though numeric thresholds are not published.

Pros and cons. Pros include zero cost, simplicity, and CORS-enabled client integration. Cons include undisclosed numeric rate limits, no published domain list, and lack of formal accuracy metrics.

## API Deep Dive: Temp Mail (temp-mail.io) — Disposable Email Generation & Management

Purpose and positioning. Temp Mail (temp-mail.io) is a disposable email service designed for programmatic generation and management of temporary inboxes. Its API supports creating addresses, retrieving messages, downloading attachments, listing domains, and monitoring rate limits. The service is not a disposable email detector; it is a full lifecycle platform for temporary email workflows. API access is available to subscribed (premium) users.[^7][^11][^12]

Base and authentication. All API calls use the base URL https://api.temp-mail.io and are authenticated via an API key in the X-API-Key header. Keys are obtained from the user’s profile section for API access.[^8]

Core endpoints. The API offers a coherent set of operations. To ground the discussion, Table 3 summarizes the primary endpoints, which handle address creation, messaging, and administrative tasks.

Table 3. Temp Mail (temp-mail.io): Core endpoints

| Operation                              | Method | Path                                 | Auth required | Example payload/response excerpt |
|----------------------------------------|--------|--------------------------------------|---------------|----------------------------------|
| Create new temporary email             | POST   | /v1/emails                           | Yes           | Request: headers only; Response: {"email":"user@example.com","ttl":86400} |
| List messages for an email             | GET    | /v1/emails/{email_address}/messages  | Yes           | Response: {"messages":[{"id":"...","from":"\"Service\" ","subject":"Welcome!","created_at":"2023-12-16T10:00:00Z"}]} |
| Get a specific message                 | GET    | /v1/messages/{message_id}            | Yes           | Response: {"id":"...","from":"\"Service\" ","to":"user@example.com","subject":"Welcome!","body_text":"...","body_html":"<p>...</p>","created_at":"...","attachments":[...]} |
| Get message source                     | GET    | /v1/messages/{message_id}/source     | Yes           | Response: raw source content (string) |
| Download attachment                    | GET    | /v1/messages/{message_id}/attachments/{attachment_id} | Yes | Binary download (e.g., file output) |
| Delete specific message                | DELETE | /v1/messages/{message_id}            | Yes           | 200/204 on success               |
| Delete email (and all messages)        | DELETE | /v1/emails/{email_address}           | Yes           | 200/204 on success               |
| List available domains                 | GET    | /v1/domains                          | Yes           | Response: list of domains         |
| Get current rate limit status          | GET    | /v1/rate_limit                       | Yes           | Response: {"limit":..., "remaining":...} |

Response formats and error model. The API uses JSON for all responses. Error responses follow a structured format with “error” and “meta” objects, including a “request_id” field that can expedite support. Standard HTTP status codes communicate success or failure classes.[^8][^9][^10]

Rate-limiting model and headers. Temp Mail implements rate limiting and exposes headers that convey the ceiling, remaining, used count, and reset timestamp for the current window. Numeric ceilings are not fixed in documentation; the service returns the current state dynamically. To operationalize this, client libraries should read and respect these headers, backing off as needed.[^8][^9][^10]

Table 4. Temp Mail (temp-mail.io): Rate-limit headers

| Header                | Meaning                                                                      | Example       |
|-----------------------|------------------------------------------------------------------------------|---------------|
| X-Ratelimit-Limit     | Maximum number of requests allowed in the current window                     | 100           |
| X-Ratelimit-Remaining | Requests remaining in the current window                                     | 99            |
| X-Ratelimit-Used      | Requests already consumed in the current window                              | 1             |
| X-Ratelimit-Reset     | UTC epoch seconds at which the current window resets                         | 1723886474    |

Domain coverage and listing. The API exposes an endpoint to retrieve available domains at runtime. Rather than publish a static set, the service provides dynamic discovery so integrators can programmatically understand what domains are available when making decisions. Treat this as a runtime “whitelist of service domains” rather than a detector of third-party disposable domains.[^10]

Pricing and availability. According to the vendor’s blog, API access is available to subscribed (premium) users. The public site also differentiates public, premium, and custom domain offerings, which is useful context for engineers deciding how to structure test accounts or privacy-preserving signups.[^11][^12]

Pros and cons. Pros include a complete, well-structured API surface, official client libraries, consistent error model, and explicit rate-limit feedback. The primary limitation for detection use cases is scope: Temp Mail does not provide a disposable detection API; it generates and manages disposable addresses.

## API Deep Dive: tempmail.dev — Inaccessible During Research

Status. The tempmail.dev site timed out during the research window, with a Cloudflare 522 error indicating a connection failure between Cloudflare and the origin server. No documentation, endpoints, rate limits, or accuracy claims could be retrieved.[^13]

What to collect next. If and when the site becomes accessible, priority information includes: detection capabilities (if any), request/response schemas, authentication modes, numeric rate limits, published domain lists (if applicable), and any vendor-stated accuracy metrics. A secondary pass should verify uptime and response-time characteristics.

Contingency plan. In the interim, prefer established alternatives: Debounce’s Disposable Detector for detection, Temp Mail (temp-mail.io) for generation and inbox management. Re-attempt tempmail.dev access after the outage clears and record the outcome.

## Comparative Analysis and Selection Guidance

At a functional level, the services evaluated here are not interchangeable. Debounce’s Disposable Detector is a classification tool built to identify disposable emails. Temp Mail (temp-mail.io) is a service for generating temporary addresses and managing their inboxes programmatically. The outage for tempmail.dev prevented any determination of its scope.

- Detection accuracy and coverage. Debounce asserts it checks inputs against a real-time, maintained list of disposable domains, but does not publish quantitative accuracy or coverage metrics. No public list of disposable domains is provided. An external comparison article mentions a gap between vendor claims and third-party audit results; treat such figures as anecdotal rather than definitive. In contrast, Temp Mail’s API does not offer detection, so accuracy metrics are not applicable.[^1][^2][^15]
- Response formats and developer experience. Debounce returns a single-field JSON object indicating “disposable” status and supports CORS for direct client use. Temp Mail provides a broader JSON API for managing the lifecycle of temporary inboxes, including message bodies, attachments, and source retrieval, plus a structured error model and rate-limit headers.[^1][^8]
- Rate limits and throughput. Debounce does not disclose numeric rate limits; it only indicates that daily call caps and validation speed limits exist, and warns against bulk use. Temp Mail exposes concrete rate-limit headers and a dedicated endpoint for current status, which simplifies client-side backoff. For Mail.tm, which emerged as a reference point for temp-mail APIs, the documentation specifies 8 queries per second per IP.[^1][^9][^14][^4]
- Authentication and security posture. Debounce’s Disposable Detector is free and unauthenticated, with CORS enabled, which is convenient but requires careful client-side throttling and monitoring. Temp Mail uses API-key authentication and returns request IDs for support triage—more appropriate for production integrations where auditability is important.[^1][^8]
- Access constraints. Temp Mail’s API is for subscribed users (premium), according to the vendor’s blog, which has implications for access management and cost modeling. Debounce’s detector is free. tempmail.dev remains an unknown until its outage is resolved.[^11]

Table 5 synthesizes these contrasts to guide selection decisions.

Table 5. Feature comparison: Debounce vs Temp Mail vs tempmail.dev

| Dimension                    | Debounce Disposable Detector                | Temp Mail (temp-mail.io)                                | tempmail.dev                |
|-----------------------------|---------------------------------------------|--------------------------------------------------------|-----------------------------|
| Primary function            | Disposable detection                        | Temporary email generation and inbox management        | Unknown (site inaccessible) |
| Detection method            | Real-time list of disposable domains        | Not applicable                                         | Unknown                     |
| Endpoint/paths              | GET /                                       | /v1/emails, /v1/emails/{email}/messages, /v1/messages/{id}, /v1/messages/{id}/source, /v1/messages/{id}/attachments/{id}, /v1/domains, /v1/rate_limit | Unknown                     |
| Auth                        | None (public free endpoint)                 | API key (X-API-Key header)                             | Unknown                     |
| Response format             | {"disposable":"true"|"false"}               | JSON (messages, bodies, attachments, domains)          | Unknown                     |
| CORS                        | Enabled                                     | Not highlighted                                        | Unknown                     |
| Domain coverage list        | Not publicly enumerated                     | Dynamic list via /v1/domains                           | Unknown                     |
| Rate limits                 | Undisclosed (daily cap, speed limits)       | X-Ratelimit-* headers + /v1/rate_limit                 | Unknown                     |
| Accuracy metrics published  | No                                          | Not applicable (no detection endpoint)                 | Unknown                     |
| Pricing/access              | Free                                        | Subscribed (premium) users per vendor blog             | Unknown                     |
| Best fit                    | Inline disposable detection                 | Programmatic temp inbox automation                     | To be determined            |

Decision framework. If the requirement is to detect disposable emails at sign-up or during list hygiene, Debounce’s Disposable Detector is the only evaluated option that fits. If the requirement is to programmatically generate disposable inboxes, retrieve messages, and manage attachments, Temp Mail (temp-mail.io) is the clear choice. For tempmail.dev, defer judgment until the service stabilizes.

## Implementation Playbook: Detection Pipeline and Client Design

Detection pipeline with Debounce. A practical detection layer typically includes:

- Request shaping. Accept an email address and normalize it (trim whitespace, lower-case domain). Optionally accept a bare domain to reduce normalization complexity.
- Primary classification. Call Debounce’s Disposable Detector with the email or domain. Cache results for domains to amortize cost and rate-limit exposure (e.g., TTL of several hours to a day).
- Fallback policy. Treat “disposable: true” as a strong positive. For borderline or ambiguous cases, consider secondary heuristics (e.g., known free-provider allowlists/denylists) and risk-based flows (step-up verification).
- Client throttling. Implement exponential backoff and honor any implicit throttling. Because numeric thresholds are not published, monitor for error signals and self-throttle to a conservative baseline in client-side scenarios.

Client design for Temp Mail (temp-mail.io). For disposable inbox workflows:

- Auth and headers. Store API keys securely, rotate as needed, and pass them via X-API-Key.
- Rate-limit handling. After every request, inspect X-Ratelimit-Limit, X-Ratelimit-Remaining, X-Ratelimit-Used, and X-Ratelimit-Reset. When remaining requests approach zero, pause until reset. The /v1/rate_limit endpoint can be polled proactively to make scheduling decisions.[^8][^9][^10]
- Domain selection. Query /v1/domains at the start of a workflow to enumerate available domains; select one that fits your test constraints or branding requirements.[^10]
- Resilience. Use the structured error object and request_id when contacting support. For attachment downloads, stream to disk and verify sizes/content types. Consider message source retrieval for deeper inspection or debugging.[^8]

Security, privacy, and compliance. Treat API keys as secrets and route all traffic over TLS. In client-side contexts, avoid exposing detection services in a way that invites bypass or abuse. For rate-limit headers and request IDs, record only what is necessary for operational diagnostics and retain per your data policies.

Testing and monitoring. Create unit and integration tests that exercise both success and error paths. For detection, build a small fixture set of known disposable and permanent domains. For Temp Mail, simulate attachment retrieval and deletion. Track rate-limit headroom over time to calibrate concurrency.

Table 6 offers a practical backoff plan based on headers exposed by Temp Mail.

Table 6. Recommended backoff schedule aligned to rate-limit headers

| Condition                                                    | Action                                                 |
|--------------------------------------------------------------|--------------------------------------------------------|
| X-Ratelimit-Remaining > 50% of Limit                         | Continue at normal concurrency                         |
| 20% < X-Ratelimit-Remaining ≤ 50%                            | Reduce concurrency by 50%; increase polling interval   |
| X-Ratelimit-Remaining ≤ 20% or X-Ratelimit-Reset within 60s  | Pause new requests; resume after X-Ratelimit-Reset     |
| HTTP 429 or request failure with rate-limit-related error    | Exponential backoff (e.g., 1s, 2s, 4s, max 30s)        |
| Repeated 429s over multiple windows                          | Escalate to queueing or downscale workload             |

## Risks, Limitations, and Open Questions

- Unknown numeric rate limits for Debounce. While Debounce signals that caps exist (including concurrency), the lack of published numbers complicates capacity planning. Mitigate with caching, server-side mediation, and conservative client behavior.[^1][^14]
- No official accuracy metrics for Debounce. Absent formal precision/recall or false positive/negative rates, teams should validate detector behavior against their own test sets and monitor outcomes over time.[^1][^2]
- tempmail.dev outage. The 522 timeout blocked any evaluation. Defer any dependencies until the site is reachable and docs are available; maintain alternatives in the meantime.[^13]
- API scope mismatch. Debounce is not an inbox platform; Temp Mail is not a detector. Selecting the right tool for the job prevents architectural mismatches and integration debt.
- Data currency. Disposable domains emerge and retire quickly. Even with a “real-time list,” false negatives can occur. Plan for periodic validation and layered defenses in high-risk flows.[^1][^2]

## Appendices

Appendix A: Debounce Disposable Detector — Sample request/response
- Request (curl): curl --request GET "https://disposable.debounce.io/?email=test@example.com"
- Response (JSON): {"disposable":"true"}

Appendix B: Temp Mail (temp-mail.io) — Endpoint summary and key headers
- Auth header: X-API-Key: YOUR_API_KEY
- Rate-limit headers: X-Ratelimit-Limit, X-Ratelimit-Remaining, X-Ratelimit-Used, X-Ratelimit-Reset
- Example message response fields: id, from, to, subject, body_text, body_html, created_at, attachments
- Example domain listing response: array of domain objects

Appendix C: Mail.tm — Rate limit note for context
- Mail.tm documents a general quota limit of 8 queries per second (QPS) per IP. While not directly comparable to Temp Mail or Debounce, it provides a useful baseline for temp-mail API throughput expectations.[^4][^5]

## Information Gaps

- tempmail.dev: No accessible documentation or endpoints due to a 522 Cloudflare timeout; all details unknown.[^13]
- Debounce Disposable Detector: No published quantitative accuracy metrics, no exhaustive list of disposable domains, and no explicit numeric rate limits disclosed.[^1][^2]
- Temp Mail (temp-mail.io): Numeric rate-limit values are not specified in documentation and are returned dynamically at runtime; API access is available to subscribed users, but pricing tiers and limits are not detailed in the retrieved docs.[^8][^9][^11]

## References

[^1]: Disposable Detector - Debounce API. https://developers.debounce.io/api-reference/endpoint/free/disposible-detector  
[^2]: Disposable Email Detector - Debounce API Documentation. https://debounce.readme.io/reference/disposable-email-detector  
[^3]: Free & Powerful API for Detecting Disposable Email Addresses - DeBounce. https://debounce.io/free-disposable-check-api/  
[^4]: Mail.tm API Documentation: Temp Mail API. https://docs.mail.tm/  
[^5]: Mail.tm OpenAPI Specification. https://api.mail.tm/docs.jsonld  
[^6]: Mercure Documentation. https://mercure.rocks/  
[^7]: Temp Mail API. https://docs.temp-mail.io/  
[^8]: Authentication - Temp Mail API. https://docs.temp-mail.io/docs/getting-started  
[^9]: Get rate limit status - Temp Mail API. https://docs.temp-mail.io/docs/get-rate-limit-v-1  
[^10]: Show available domains - Temp Mail API. https://docs.temp-mail.io/docs/list-domains-v-1  
[^11]: Official public API is here! - Temp Mail Blog. https://temp-mail.io/blog/official-api-is-here  
[^12]: Domains | Help Center - Temp Mail. https://temp-mail.io/help/domains  
[^13]: tempmail.dev (522 Connection Timeout during research). https://tempmail.dev  
[^14]: Frequently Asked Questions - DeBounce. https://debounce.io/faq/  
[^15]: QuickEmailVerification Vs DeBounce Comparison - List Cleaning Advice. https://listcleaningadvice.com/vendor-compare/quickemailverification/debounce