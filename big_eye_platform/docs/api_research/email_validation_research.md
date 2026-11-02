# Email Validation and SMTP Verification APIs: IsItARealEmail, Hunter.io, and ZeroBounce

## Executive Summary

Engineering and marketing operations teams rely on email validation to reduce bounces, protect sender reputation, and improve deliverability. This report compares three providers—IsItARealEmail (via its redirect to MailValidation.io/IPQualityScore), Hunter.io, and ZeroBounce—focusing on validation methods, syntax and MX checks, SMTP verification depth, rate limits, and pricing models.

At a high level, Hunter.io offers the most clearly documented verification workflow and result semantics, including explicit MX and SMTP indicators, time-bounded asynchronous verification with polling, and granular rate limits per endpoint. ZeroBounce positions around accuracy, security, and breadth of deliverability tooling (validation, scoring, inbox placement, server tests, blacklist monitoring), but its verification workflow and response codes are not publicly detailed in the reviewed documentation. IsItARealEmail’s direct site was blocked during automated access; however, the service redirects to MailValidation.io/IPQualityScore, which exposes comprehensive validation features and a flexible pricing structure with tiered rate limits.

Hunter’s verification process returns structured signals such as MX record presence, SMTP server connectivity, and catch-all detection, with a 20-second time budget per request and a formal polling mechanism if incomplete. Rate limits are explicit per endpoint, enabling predictable scaling. ZeroBounce emphasizes validation and scoring with strong security and operational claims (Cloudflare protections, owned data center, no third-party storage, encryption), but does not expose verification workflow details or SMTP response semantics in the reviewed docs. For IsItARealEmail, the IPQualityScore (IPQS) integration implies deep checks (DNS/MX/SMTP, disposable/spam trap detection, abuse history) and plan-dependent throughput, though the exact endpoint and response fields were not confirmed from a primary IPQS source in this research set.

Actionable guidance: Use Hunter when you need transparent verification semantics, explicit rate limits, and clear billing via verification credits. Use ZeroBounce for comprehensive deliverability tooling, strong security assurances, and a broad product suite (validation plus scoring, inbox placement, and server tests). Consider IsItARealEmail/IPQualityScore when advanced risk signals (spam traps, abuse history) and configurable SMTP timeouts are critical; confirm endpoint and response details directly with IPQS and IsItARealEmail.

## Scope, Methodology, and Source Reliability

This analysis evaluates validation methods, syntax and MX verification, SMTP verification depth, API features, rate limits, and pricing. Methods include reviewing official documentation, pricing pages, and help center articles. Direct access to IsItARealEmail’s site was blocked by Cloudflare; the service redirects to MailValidation.io/IPQualityScore. Based on observed behavior and documentation flow, this report treats IsItARealEmail as an interface to IPQualityScore’s Email Validation API, with capabilities inferred from the IPQS experience and the redirect context.

Source reliability is strongest where official documentation and pricing pages are public and detailed—Hunter.io and ZeroBounce fall into this category. For IsItARealEmail/IPQualityScore, certain endpoint and rate-limit specifics remain unconfirmed from a primary IPQS source in the reviewed materials; those items are explicitly flagged as gaps for follow-up.

## Provider Deep-Dives

### IsItARealEmail (redirect to MailValidation.io / IPQualityScore)

Observed behavior indicates that IsItARealEmail redirects users to MailValidation.io, which in turn presents the IPQualityScore Email Validation API. During automated access, IsItARealEmail’s site presented Cloudflare challenges, preventing direct extraction. The capabilities below reflect IPQS-style features commonly associated with deep email validation.

![IsItARealEmail redirect to MailValidation.io (IPQualityScore) — main page](browser/screenshots/mailvalidation_io_main_page.png)

Capabilities:
- Syntax and format checks as part of comprehensive validation.
- DNS/MX/SPF/DMARC checks; MX record verification is expected.
- Deep SMTP verification, including mailbox existence checks, catch-all detection, and configurable timeout behavior.
- Risk signals: disposable email detection, spam trap detection, abuse history, and age of email/domain.
- Response schema (general expectations): structured JSON with deliverability indicators and risk scores; exact endpoint and field names not confirmed from a primary IPQS source in the reviewed documentation set.
- Rate limits and throughput: plan-dependent (plan pages reference 20+ verifications per second on paid tiers), not confirmed from IPQS docs here.
- Pricing: tiered plans include Free (1,000 lookups/month, 35/day), Startup, SMB Basic, SMB+, and Enterprise. Pay-as-you-go options may be available; exact rates vary.

This profile is suitable when teams need advanced risk indicators and SMTP depth beyond basic MX checks. Confirm the IPQualityScore endpoint semantics and rate-limit specifics directly with IPQS before production rollout.[^10][^11][^12][^13][^14]

### Hunter.io

Hunter.io exposes a comprehensive Email Verifier with transparent verification signals, polling semantics, and well-documented rate limits. The platform is credit-based, supporting verification, finder, and domain search workflows.

Validation methods:
- Syntax validation (regexp), disposable and webmail classification, MX record checks, SMTP server connectivity, SMTP check for bounces, catch-all detection, and optional sources when available.
- Asynchronous verification: requests run for up to 20 seconds; if incomplete, the service returns HTTP 202 and expects polling. Each verification is counted once regardless of polling.
- Result semantics: status values include valid, invalid, accept_all, webmail, disposable, unknown. Outputs also include flags such as mx_records, smtp_server, smtp_check, accept_all, and a deliverability score.

API and integration:
- Versioned API (V2) with a clear base path; authentication supports api_key query parameter, X-API-KEY header, or Authorization: Bearer token.
- Response structure separates success (data and meta) from errors, with standard HTTP codes and specific verification codes (e.g., 202 for in-progress, 222 for unexpected SMTP response, 451 for claimed email).
- Wrappers are available for Ruby, Node.js, Python, Laravel, Go, and R. Model Context Protocol (MCP) server support is documented.

Rate limits:
- Email Verifier: 10 requests per second (RPS) and 300 requests per minute.
- Domain Search and Email Finder: 15 RPS and 500 RPM.
- Enrichment endpoints: 15 RPS and 500 RPM.
- Discover: 5 RPS and 50 RPM.

Pricing:
- All-in-one outreach platform plans (monthly or yearly billing) include monthly credits and unlimited users, with discounts for yearly payment.
- Data Platform: credit packs for searches and verifications with explicit example pricing—1,000 search credits ($50) and 1,000 verification credits ($11), totaling $61. Verification consumes 0.5 credits per email; finder and domain search consume 1 credit per email or per up to 10 emails in bulk contexts.[^1][^2][^3][^4][^5][^6][^7][^8][^9]

To illustrate throughput expectations, the following table summarizes rate limits by endpoint:

| Endpoint                 | Per Second (RPS) | Per Minute (RPM) |
|-------------------------|------------------|------------------|
| Email Verifier          | 10               | 300              |
| Domain Search           | 15               | 500              |
| Email Finder            | 15               | 500              |
| Email Enrichment        | 15               | 500              |
| Company Enrichment      | 15               | 500              |
| Combined Enrichment     | 15               | 500              |
| Email Count             | 15               | 500              |
| Discover                | 5                | 50               |

Hunter’s verification status and signals map to operational decisions:

| Field/Status            | Meaning                                                                 |
|-------------------------|-------------------------------------------------------------------------|
| status=valid            | Email is valid and deliverable                                          |
| status=invalid          | Email is not valid                                                      |
| status=accept_all       | Server accepts all addresses (potential uncertainty)                    |
| status=webmail          | Email from a webmail provider                                           |
| status=disposable       | Email from a disposable provider                                        |
| status=unknown          | Verification failed to complete                                         |
| mx_records              | MX records exist for the domain                                         |
| smtp_server             | Connection to SMTP server succeeded                                     |
| smtp_check              | SMTP server indicated no bounce                                         |
| accept_all              | Catch-all detected                                                      |
| deliverability score    | Score indicating deliverability likelihood                              |

Pricing overview:

| Category                 | Plan/Tier            | Credits Included             | Notes                                                          |
|-------------------------|----------------------|------------------------------|----------------------------------------------------------------|
| Outreach Platform       | Free                 | 50/month                     | No credit card required                                        |
| Outreach Platform       | Starter              | 2,000/month                  | Yearly billing discount available                              |
| Outreach Platform       | Growth               | 10,000/month                 | Priority support                                               |
| Outreach Platform       | Scale                | 25,000/month                 | Larger campaign limits                                         |
| Outreach Platform       | Enterprise           | Custom                       | Account manager                                                |
| Data Platform (API)     | Verification credits | Variable packs               | 0.5 credit per verification; example: 1,000 verifications = $11 |
| Data Platform (API)     | Search credits       | Variable packs               | 1 credit per search or per up to 10 emails in bulk contexts    |

Hunter is a strong fit when transparent result semantics, explicit rate limits, and predictable credit-based billing are key requirements.[^1][^2][^3][^4][^5][^6][^7][^8][^9]

### ZeroBounce

ZeroBounce focuses on accuracy, security, and a broad deliverability toolkit. It provides email validation and scoring, with optional add-ons like inbox placement tests, email server tests, blacklist monitoring, and DMARC monitoring. The platform highlights a real-time API, bulk validation via file upload, and strong operational protections.

Validation methods (as positioned):
- Syntax validation, server configuration checks, and confirmations that addresses are configured to receive messages; activity confirmation is part of the offering.
- Email scoring provides an additional signal to support decisions, especially for risky or catch-all domains.
- SMTP verification specifics (server response handling, catch-all detection, and detailed codes) are not exposed in the reviewed documentation.

API and operations:
- Real-time validation API with quickstart documentation; bulk validation supports CSV/XLS/XLSX/TXT formats.
- Processing time guidance: approximately 45–60 minutes per 100,000 contacts.
- Security: Cloudflare (Advanced DDoS and Advanced Firewall), encryption for uploaded/downloaded files, owned data center (not using Amazon/Azure), no third-party storage, and deletion of customer data within 30 days or upon request.

Pricing:
- Freemium: 100 monthly credits; credits do not expire; rollover applies to subscriptions.
- ZeroBounce ONE: $99/month including 25,000 validation/scoring credits plus other product usage allowances (finder searches, inbox placement, server tests, blacklist monitors, DMARC monitors, warmup seeds/accounts).
- Pay-as-you-go: minimum purchase of 2,000 credits at $20 ($0.01 per credit); higher tiers and custom volumes available through sales. Email Finder uses 20 credits per successful query.

Pricing summary:

| Plan/Tier                | Cost (Monthly) | Included Credits/Allowances                                  |
|--------------------------|----------------|---------------------------------------------------------------|
| Freemium                 | $0             | 100 validation/scoring credits; limited other tests           |
| ZeroBounce ONE           | $99            | 25,000 validation/scoring credits; 10,000 finder searches; 100 inbox placement tests; 100 server tests; 10 blacklist monitors; 1 DMARC monitor; 250 warmup seeds; 2 warmup accounts |
| Pay-As-You-Go            | From $20       | 2,000 credits minimum; $0.01 per credit                       |
| Custom (ONE Custom)      | $274+          | Custom quantities across validation, scoring, and other tools |

ZeroBounce is well-suited when strong data protection, a wide deliverability toolbox, and bundled product offerings are prioritized. Verification workflow specifics and SMTP response codes should be confirmed directly with the provider’s detailed API reference for fine-grained integration.[^15][^16][^17][^18][^19][^20]

## Comparative Analysis

The three providers differ in transparency of verification semantics, the depth of SMTP handling, and the breadth of deliverability tooling.

- Validation methods: Hunter explicitly documents syntax checks, MX and SMTP signals, and catch-all handling. ZeroBounce positions validation, scoring, and server/activity confirmations but does not publish SMTP response semantics in the reviewed docs. IsItARealEmail/IPQualityScore implies deep validation layers including DNS/MX, SMTP, disposable/spam trap detection, and abuse signals, though endpoint and field specifics remain unconfirmed here.
- SMTP verification: Hunter returns structured fields that reflect SMTP server connectivity and bounce indications and handles asynchronous verification via polling. ZeroBounce states confirmations of server configuration and activity but does not enumerate SMTP response codes in the reviewed content. IsItARealEmail/IPQualityScore is expected to include mailbox existence checks and catch-all detection with configurable timeout behavior.
- MX verification: Hunter exposes mx_records explicitly. ZeroBounce positions server configuration checks without explicit field references in the reviewed pages. IsItARealEmail/IPQualityScore implies MX and broader DNS validations.
- Rate limits: Hunter publishes endpoint-specific RPS/RPM limits, enabling precise throughput planning. ZeroBounce documents operational processing times for bulk tasks but does not publish API rate limits in the reviewed docs. IsItARealEmail/IPQualityScore shows plan-dependent throughput on pricing pages but lacks confirmed, authoritative rate-limit specifications in this research set.
- Pricing models: Hunter uses credits with discounted yearly plans and explicit verification credit pricing via the Data Platform. ZeroBounce offers subscription bundles and pay-as-you-go credits, with one credit per validation and additional credit costs for finder queries. IsItARealEmail/IPQualityScore provides tiered plans with free and paid options and throughput tiers; specifics should be confirmed with IPQS.

Feature comparison matrix:

| Capability                     | IsItARealEmail/IPQS | Hunter.io                         | ZeroBounce                              |
|-------------------------------|---------------------|-----------------------------------|-----------------------------------------|
| Syntax checking               | Implied             | Documented (regexp)               | Positioned (validation)                 |
| MX record verification        | Implied             | Documented (mx_records)           | Positioned (server configuration)       |
| SMTP server connectivity      | Implied             | Documented (smtp_server)          | Not detailed in reviewed docs           |
| SMTP bounce check             | Implied             | Documented (smtp_check)           | Not detailed in reviewed docs           |
| Catch-all detection           | Implied             | Documented (accept_all flag/status)| Positioned (scoring/finder), not verified in docs |
| Asynchronous verification     | Not confirmed       | Documented (202 + polling)        | Not documented                          |
| Result semantics (status/flag)| Expected, unconfirmed| Clearly documented                | Not publicly detailed in reviewed docs  |
| Rate limits                   | Plan-dependent      | Per-endpoint RPS/RPM              | Not published in reviewed docs          |
| Bulk processing guidance      | Available via CSV/API| Bulk via API                      | 45–60 min per 100k contacts             |
| Security/privacy              | Standard expectations| Not a focus of docs               | Cloudflare, owned DC, encryption, purge |

Rate limits summary:

| Provider               | RPS (if available)        | RPM (if available)      | Notes                                         |
|------------------------|---------------------------|-------------------------|-----------------------------------------------|
| IsItARealEmail/IPQS    | Plan-dependent (20+/sec on some tiers, unconfirmed) | Not publicly documented here | Confirm with IPQS                             |
| Hunter.io              | 5–15 RPS by endpoint      | 50–500 RPM by endpoint  | Verifier: 10/300; Finder/Domain: 15/500       |
| ZeroBounce             | Not documented            | Not documented          | Bulk processing time guidance available       |

Pricing comparison:

| Provider               | Model                      | Example Costs                                   |
|------------------------|----------------------------|-------------------------------------------------|
| IsItARealEmail/IPQS    | Tiered plans               | Free: 1,000/mo; Startup/SMB/SMB+/Enterprise tiers |
| Hunter.io              | Credits (verification 0.5; search 1) | Example: 1,000 verifications = $11; 1,000 searches = $50 |
| ZeroBounce             | Subscriptions + pay-as-you-go | Freemium: 100 credits; ONE: $99/mo with 25k credits; PAYG: $20 for 2k credits ($0.01/credit) |

For teams prioritizing transparent verification mechanics and clear throughput guarantees, Hunter is the most operationally explicit. ZeroBounce offers broader deliverability tooling and strong security posture, but verification-specific workflow details and rate limits should be confirmed. IsItARealEmail/IPQualityScore appears optimized for deep risk assessment and configurable SMTP behavior, warranting endpoint verification and rate-limit confirmation before production.

## Integration and Implementation Considerations

Real-time form validation requires careful handling of asynchronous verification and user experience. Hunter implements a 20-second verification window; if the check cannot complete in time, the service returns HTTP 202 and provides a polling mechanism. Clients should implement bounded retries with exponential backoff, surface interim states to users, and ultimately count the verification once per request regardless of polling.[^1][^2]

Bulk processing differs by provider. ZeroBounce supports CSV/XLS/XLSX/TXT uploads, with a processing time of roughly 45–60 minutes per 100,000 contacts and encrypted result packages delivered post-processing. For large-scale backfills or periodic list hygiene, this batch-oriented approach can be integrated into ETL workflows with notifications upon completion. IsItARealEmail/IPQualityScore also supports bulk CSV processing via dashboard and API, consistent with IPQS practices, though the specific workflow and throughput characteristics should be confirmed with IPQS.[^18][^14]

Caching and deduplication reduce costs and improve responsiveness. Hunter’s credit policy counts repeated searches and verifications once per calendar month, which encourages caching month-to-date results to avoid redundant calls. Disposable email handling should be consistent across systems; Hunter automatically skips disposable emails and does not count credits, enabling upfront filtering without cost.[^7][^9]

Risk mitigation for catch-all domains should combine signals. In Hunter, accept_all status indicates server-level acceptance of all addresses; SMTP and mx_records flags provide additional context. For ZeroBounce, email scoring adds a quantitative signal; combined with internal reputation data, this can help decide whether to accept, review, or reject. For IsItARealEmail/IPQualityScore, abuse history and spam trap signals are valuable for identifying risky contacts that should be quarantined or excluded.

Finally, align rate-limit handling with provider semantics. Hunter’s per-endpoint limits allow fine-grained throttling. For providers without published rate limits, implement adaptive backoff based on HTTP errors and response latencies, and confirm throughput expectations through sales or support channels.

## Recommendations and Use-Case Fit

- Hunter.io: Best fit for engineering teams that require transparent verification semantics, explicit rate limits, and predictable credit costs. The structured output (status, mx_records, smtp_server, smtp_check, accept_all) and polling behavior make it straightforward to implement robust real-time validation and batch workflows with clear SLAs.[^1][^2][^3]
- ZeroBounce: Recommended when a comprehensive deliverability stack is important—validation and scoring paired with inbox placement tests, email server tests, blacklist monitoring, DMARC monitoring, and warmup tools. The strong security stance (Cloudflare protections, owned data center, encryption, strict data purge) is advantageous for enterprises with stringent governance requirements.[^16][^17][^18][^20]
- IsItARealEmail/IPQualityScore: Consider when advanced risk signals (spam traps, abuse history, email age) and deeper SMTP verification are critical. This stack is suited for fraud prevention, high-risk verticals, and contexts where catch-all domain handling must be informed by multiple risk dimensions. Confirm IPQS endpoint details, response fields, and rate limits with the provider before large-scale adoption.[^10][^11][^12]

To aid decision-making, the following matrix maps common use-cases to provider strengths:

| Use-Case                                 | Hunter.io                               | ZeroBounce                                     | IsItARealEmail/IPQS                         |
|------------------------------------------|-----------------------------------------|------------------------------------------------|---------------------------------------------|
| Real-time form validation                | Clear polling, explicit signals         | API available; security-focused                | Likely suitable; confirm with IPQS          |
| Bulk list cleaning (100k+)               | Credits model with endpoint limits      | Batch upload with defined processing time      | CSV/API; throughput tiers; confirm          |
| Catch-all domain handling                | accept_all + SMTP/MX signals            | Scoring signal                                 | Catch-all + risk signals                    |
| Compliance-heavy environments            | Standard API practices                  | Strong security and data purge assurances      | Confirm IPQS security stance                |
| Fraud prevention and risk scoring        | Good baseline signals                   | Scoring plus deliverability tooling            | Deep risk indicators (spam traps, abuse)    |

## Appendices

### Appendix A: Hunter.io API Error and Status Codes

| Code | Meaning                                  | Notes                                                         |
|------|------------------------------------------|---------------------------------------------------------------|
| 200  | OK                                       | Request succeeded                                             |
| 201  | Created                                  | Resource created                                              |
| 204  | No content                               | Success without body                                          |
| 400  | Bad request                              | Missing or invalid parameters                                 |
| 401  | Unauthorized                             | Invalid API key                                               |
| 403  | Forbidden                                | Rate limit reached                                            |
| 404  | Not found                                | Resource does not exist                                       |
| 422  | Unprocessable entity                     | Request valid but creation failed                             |
| 429  | Too many requests                        | Usage limit reached                                           |
| 5XX  | Server errors                            | Provider-side failure                                         |
| 202  | Verification in progress                 | Poll for result                                               |
| 222  | Unexpected SMTP response                 | Retry later                                                   |
| 451  | Claimed email                            | Owner requested no processing                                 |

### Appendix B: Hunter.io Email Verifier Status and Signal Fields

| Field/Status            | Description                                                              |
|-------------------------|--------------------------------------------------------------------------|
| status                  | valid, invalid, accept_all, webmail, disposable, unknown                 |
| deliverability score    | Likelihood score of deliverability                                       |
| regexp                  | Syntax check via regular expression                                      |
| gibberish               | Indicates automatically generated email                                  |
| disposable              | True if from a disposable service                                        |
| webmail                 | True if from a webmail service                                           |
| mx_records              | True if MX records exist                                                 |
| smtp_server             | True if SMTP connection succeeded                                        |
| smtp_check              | True if SMTP indicates no bounce                                         |
| accept_all              | True if server accepts all emails (catch-all)                            |
| block                   | True if SMTP server blocked the check                                    |
| sources                 | URLs where email was found (limited to 20)                               |

### Appendix C: Rate Limits and Throughput Planning

| Provider               | Endpoint               | RPS      | RPM      | Planning Note                                   |
|------------------------|------------------------|----------|----------|-------------------------------------------------|
| Hunter.io              | Email Verifier         | 10       | 300      | Use queueing to avoid bursts                    |
| Hunter.io              | Domain Search          | 15       | 500      | Batch filtering                                  |
| Hunter.io              | Email Finder           | 15       | 500      | Favor staggered runs                            |
| Hunter.io              | Enrichment             | 15       | 500      | Throttle per service                            |
| Hunter.io              | Discover               | 5        | 50       | Reserve for targeted queries                    |
| ZeroBounce             | API (general)          | N/A      | N/A      | Not documented; design with adaptive backoff    |
| IsItARealEmail/IPQS    | API (general)          | Tiered   | Tiered   | Confirm limits with IPQS                        |

### Appendix D: Pricing Example Calculations

| Provider               | Scenario                              | Calculation                                  | Cost/Credit Implication                      |
|------------------------|----------------------------------------|----------------------------------------------|----------------------------------------------|
| Hunter.io              | 10,000 verifications                   | 10,000 × 0.5 credits                          | 5,000 verification credits                   |
| Hunter.io              | 10,000 searches (Domain/Finder)        | 10,000 × 1 credit                             | 10,000 search credits                        |
| Hunter.io (example)    | 1,000 verifications + 1,000 searches   | 1,000 × 0.5 + 1,000 × 1                       | $11 + $50 = $61 total                        |
| ZeroBounce             | 10,000 validations (PAYG)              | 10,000 × $0.01                                | $100                                          |
| ZeroBounce             | Freemium monthly                       | 100 credits                                   | $0                                            |
| IsItARealEmail/IPQS    | 10,000 lookups (SMB Basic tier)        | Included in plan                              | Verify plan limits and overage fees          |

## Information Gaps and Next Steps

- IsItARealEmail: Direct automated access to the site was blocked by Cloudflare. Confirm primary documentation, API endpoint paths, explicit rate limits, and SMTP response codes. Map the redirect flow to the IPQualityScore Email Validation API and obtain authoritative endpoint and response schema details.[^10][^11][^12][^13][^14]
- ZeroBounce: Verification workflow details (e.g., SMTP handshake behavior and specific error codes) are not present in the reviewed documentation; consult the full API reference. Rate limits were not published in the materials reviewed; confirm with the provider.[^17][^18][^19]
- Hunter.io: Pricing tiers change over time; validate the latest outreach plan limits and Data Platform credit pricing directly with the provider or recent pricing pages.[^3][^7]

## References

[^1]: Hunter.io API Reference V2.  
[^2]: Hunter Email Verifier API Endpoint.  
[^3]: Hunter Pricing.  
[^4]: Hunter API Overview.  
[^5]: Hunter Help: API Overview.  
[^6]: Hunter Help: Request per Second Limit.  
[^7]: Hunter Help: What is a Credit and How is it Counted.  
[^8]: Hunter Help: Billing & Subscriptions.  
[^9]: Hunter.io Homepage.  
[^10]: IsItARealEmail.com (MailValidation.io redirect).  
[^11]: MailValidation.io (IPQS redirect) Homepage.  
[^12]: IPQualityScore Email Validation API (via MailValidation.io subdomain).  
[^13]: IPQualityScore Email Validation Pricing (via MailValidation.io subdomain).  
[^14]: MailValidation.io Bulk CSV Validation Documentation.  
[^15]: ZeroBounce Homepage.  
[^16]: ZeroBounce Email Validation Pricing.  
[^17]: ZeroBounce Docs (Getting Started).  
[^18]: ZeroBounce Email Validation API Quickstart.  
[^19]: ZeroBounce Members Pricing (Account Billing).  
[^20]: ZeroBounce Email Deliverability Guide.