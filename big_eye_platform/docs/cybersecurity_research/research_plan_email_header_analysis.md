# Email Header Analysis for Phishing Detection: A Technical Blueprint

## Executive Summary

Phishing remains the most common vector for cyberattacks because it exploits the weakest link in the email ecosystem: humans. Technical controls—gateway filtering, secure mail gateways, and endpoint protections—reduce exposure but often fail to catch sophisticated campaigns that subtly abuse email conventions. Header analysis is a foundational detective control that inspects the truthful elements of a message’s journey and cryptographic posture to expose forgery, redirection, and trust abuse. When codified into rules and signals, header-based analysis provides a high-signal feed for both automated detection and analyst triage, improving both precision and time-to-containment.

This blueprint distills how to interpret key header fields—From, Return-Path, Received, and Reply-To—how to extract infrastructure indicators such as IP addresses and domains, and how to detect anomalies that correlate with phishing. It also translates authentication results from Sender Policy Framework (SPF), DomainKeys Identified Mail (DKIM), and Domain-based Message Authentication, Reporting, and Conformance (DMARC) into actionable signals and risk scores. While the field values and syntax follow well-known standards, operational realities—such as forwarding, mailing lists, and third-party senders—introduce ambiguity. Therefore, this report emphasizes careful normalization, trust boundaries, and adaptive scoring rather than brittle thresholds.

The outcome is a pragmatic framework:
- Clear parsing and normalization patterns for the most relevant headers.
- A scoring rubric that combines header anomalies with SPF/DKIM/DMARC evidence.
- A rule library with severity and confidence ratings to drive detection engineering.
- Triage and response guidance for analysts, and a roadmap to iteratively improve detection coverage.

Because ground-truth datasets and policy details vary widely across environments, this blueprint avoids one-size-fits-all thresholds. It provides a detection philosophy and concrete patterns that security engineers can tune for their organization’s mail ecosystem and risk tolerance.

### Key Findings at a Glance

- High-signal header checks: mismatches between the From display name and the RFC5322-MailFrom domain; inconsistencies among Return-Path, From, and Reply-To; anomalous Received chains (missing hops, reversed chronology, private IPs at the edge, mismatched HELO/EHLO); and weak or contradictory authentication results across SPF, DKIM, and DMARC.
- Robust parsing rules: normalize all domains to lowercase and punycode where applicable; extract IP addresses from Received headers with regex and validate ranges; unify header folding; redact personally identifiable information (PII) in logs to reduce risk.
- Security feature signals: SPF pass with a mismatched From domain often indicates forwarding; DKIM-Signature with a selector referencing an unrelated domain reduces trust; DMARC failures (especially with rejecting policies) strongly indicate spoofing, whereas DMARC passes with relaxed alignment can still be abused via lookalike domains.
- Scoring guidance: assign higher severity to header inconsistencies accompanied by DMARC failure and evidence of domain mismatch. Weight SPF/DKIM/DMARC outcomes by alignment and reputation. Treat Received anomalies as moderate-to-high risk when coinciding with suspicious message characteristics (HTML-only body, urgency language, credential prompts).
- Implementation tips: canonicalize headers, deduplicate Received chains, handle forwarding and mailing list footers, and build a reputation-backed whitelist with time-based decay. Incorporate robust logging, evidence preservation, and periodic rule audits to adapt to attacker tradecraft.

## Objectives and Scope

The goal is to build a defensible set of header-based detections that surface phishing risk without flooding operations with false positives. This document focuses on four header fields—From, Return-Path, Received, and Reply-To—and the trio of email security features—SPF, DKIM, and DMARC. It excludes deep content analysis of message bodies and attachments, though the outputs of header analysis can be combined with content and behavior signals in downstream models.

The scope covers:
- Header semantics and interdependencies.
- IP and domain extraction from Received and other headers.
- Anomaly categories and detection heuristics.
- Security feature signals, their failure modes, and how to weigh them.
- Signal aggregation and a practical scoring rubric.
- Triage workflows, implementation notes, and a rule catalog.

Constraints are deliberate: phishing can be detected through many avenues, but this blueprint remains anchored to headers and authentication, allowing teams to layer detection depth without needing full content parsing initially.

### Audience and Use Cases

This guide is written for security researchers, detection engineers, email security administrators, and incident responders responsible for building and operating phishing detections. It is designed to:
- Inform detection engineering when authoring rules and features.
- Guide triage workflows for SOC analysts and incident responders.
- Support platform architects in configuring pipelines, logging, and evidence preservation.
- Provide email administrators with operational heuristics to tune gateways and policies.

## Email Header Fundamentals

Email headers are key-value pairs that describe message metadata, routing, and authentication. They provide the most reliable trail of how a message moved through infrastructure and which domains or mail transfer agents (MTAs) asserted responsibility for delivery. Understanding header fields and their typical content is essential to distinguishing benign oddities from signals of malicious intent.

To illustrate common fields and their roles, Table 1 summarizes the key headers covered in this report.

### Table 1: Key Header Fields and Typical Content

| Header Field      | Typical Content/Structure                                  | Example (sanitized)                         | Function/Purpose                                               |
|-------------------|-------------------------------------------------------------|----------------------------------------------|----------------------------------------------------------------|
| From              | Display Name <local-part@domain>                            | "Accounts" <notice@contoso.com>              | Who the message appears to be from; presented to recipients.   |
| Return-Path       | Bounce address <local-part@domain>                          | <bounce@contoso.com>                         | Bounce-handling path; often aligns with RFC5322-MailFrom.      |
| Reply-To          | Alternate reply address <local-part@domain>                 | <reply@mailer-support.net>                   | Where replies are directed; can differ from From.              |
| Received          | Chain entries from each MTA hop: date, host, protocol, IP   | from edge01.example.net (10.0.0.1) by ...    | Reveals routing, latency, and infrastructure characteristics.  |
| Authentication-Results / Received-SPF | MTA verdict summary: SPF/DKIM/DMARC results | spf=fail; dkim=pass; dmarc=quarantine        | Encodes authentication outcomes for downstream processing.     |
| Message-ID        | Unique identifier, often domain-based                       | <12345@contoso.com>                          | Optional; can help correlate logs or detect anomalies.         |
| MIME-Version      | Indicates MIME support                                       | 1.0                                          | Formatting context; rarely used directly for detection.        |
| Content-Type      | Message body structure and encoding                          | text/html; charset="UTF-8"                   | Used in conjunction with body analysis; header-only context.   |
| Date              | Original message send time                                   | Wed, 29 Oct 2025 11:03:56 +0000              | Chronology anchor; helps identify time anomalies.              |

The presence of these fields and their values often interrelate. For example, Return-Path and the envelope-from (not always directly visible) inform SPF checks, while DKIM signs specific headers and body components. DMARC evaluates alignment between From and these authenticated identities.

### Header Syntax and Folding

Headers follow structured lines with name-value pairs. Long values may be folded across multiple lines that begin with whitespace, which parsers must concatenate into a single logical value. While domain names are typically case-insensitive, safe normalization is to lowercase and trim whitespace. This ensures consistent matching for domain comparisons and authentication alignment.

Parsers should also handle rare characters, encoded words (e.g., base64 or quoted-printable in display names), and nested angle brackets. Robust parsing reduces false positives that stem from formatting quirks rather than substantive anomalies.

### RFC5322-MailFrom vs. From

A frequent source of confusion is the envelope sender (RFC5322-MailFrom or Return-Path) and the visible From header. The envelope sender is used by MTAs for delivery and bounce routing. The visible From is what recipients see. In benign scenarios, they may differ (for example, on behalf of a mailing list). In phishing, mismatches across these identities are red flags when unaligned with trusted services.

### Mailing Lists and Forwarding

Mailing list footers and the presence of List-Unsubscribe headers often explain mismatches and Received anomalies. Forwarding can modify SPF results because the forwarder may not be authorized to send on behalf of the original domain, resulting in SPF softfail or fail while DKIM remains valid. These scenarios require adaptive rules that do not over-penalize common forwarding behaviors.

## Header Fields to Analyze

Header fields are interdependent; a single inconsistency is rarely sufficient to declare fraud, but patterns across multiple fields can be highly indicative. This section details what to check and why, focusing on From, Return-Path, Received, and Reply-To.

### From

The From header combines a display name and an email address. It is the most visible identity presented to users, making it a prime target for spoofing. Detectors should:
- Parse and separate the display name from the email address.
- Compare the domain in From to authentication-aligned identities (Return-Path or SPF-aligned domain; DKIM d= domain).
- Detect encoded words and homoglyphs in display names that mimic brand terms.
- Identify unusual local-parts (for example, administrative terms like “security,” “support,” or “billing”) that induce urgency.

To highlight common anomalies, Table 2 catalogs the typical patterns.

#### Table 2: From Header Anomalies and Indicators

| Anomaly Type                           | Indicator Description                                             | Rationale                                                  |
|----------------------------------------|-------------------------------------------------------------------|------------------------------------------------------------|
| Display name/domain mismatch           | Display name implies brand, domain is unrelated or dynamic        | Brand impersonation; possible third-party misuse.          |
| Punycode/homoglyph domain              | Domain contains non-ASCII or lookalike characters                 | Visual spoofing to deceive users.                          |
| Public mail provider in business role  | From uses generic consumer mail provider for corporate context    | Weak legitimacy; often abused in phishing.                 |
| Near-colliding domain (typosquatting)  | Domain closely resembles a known brand with subtle differences    | Impersonation through lookalikes.                          |
| Local-part indicating urgency          | admin, support, security, billing, payroll, etc.                  | Social engineering to prompt quick action.                 |
| Excessive encoding/obfuscation         | Heavy base64/quoted-printable in display name or address          | Obfuscation to evade simple filters.                       |

### Return-Path

The Return-Path indicates the bounce address and often aligns with the envelope sender. It is crucial for routing error messages and is central to SPF. Discrepancies between Return-Path and From are not inherently malicious, but certain patterns increase risk, especially when combined with weak authentication.

#### Table 3: Return-Path Anomaly Patterns

| Pattern                                       | Indicator Description                                             | Rationale                                                  |
|-----------------------------------------------|-------------------------------------------------------------------|------------------------------------------------------------|
| Return-Path domain ≠ From domain              | Envelope sender differs from visible From                         | Requires alignment context; common in marketing and lists. |
| Dynamic/randomized subdomain                  | Envelope domain includes auto-generated or transient subdomains   | Potential bulk sending or obfuscation.                     |
| Public provider mismatch                      | Return-Path uses consumer mail provider while From is corporate   | Common in compromise; lower trust posture.                 |
| SPF failing while From claims reputable brand | Authentication mismatch with branding                             | Stronger indicator of spoofing when DMARC also fails.      |

### Received

The Received chain documents each hop, including the sending host, receiving host, protocol, timestamp, and sometimes an IP address. It is invaluable for detecting tampering and anomalous routing. Parsing should deduplicate the chain and verify chronological ordering.

#### Table 4: Received Fields to Parse and Typical Anomalies

| Parsed Element   | Examples                                  | Anomaly Indicators                                          |
|------------------|--------------------------------------------|-------------------------------------------------------------|
| Hostname         | mx01.example.net, edge01.example.net       | Missing or private IP at edge; inconsistent HELO/EHLO.     |
| IP Address       | IPv4/IPv6 within hop                        | Private/reserved IP at internet-facing hop; sudden changes. |
| Protocol         | ESMTP, SMTP                                 | Protocol inconsistencies or downgrade patterns.            |
| Timestamp        | RFC-compliant date/time                     | Chronology reversal; impossible latency between hops.       |
| HELO/EHLO        | helo=mailer.example.net                     | HELO mismatch with reverse DNS; reused HELO strings.       |
| ID               | id=ABC12345                                 | Missing IDs or copied IDs across distant hops (tampering). |

Anomalies can indicate forwarding, a compromised relay, or crafting designed to confuse manual review. Private IPs at the edge of the internet-facing path often reflect misconfiguration or mobile/network address translation (NAT), but paired with brand impersonation and content cues, they raise risk.

### Reply-To

Reply-To directs where replies go. Attackers manipulate it to redirect responses to adversary-controlled mailboxes. Legitimate services can set Reply-To differently for mailings or transactional messages, so alignment checks should be contextual.

#### Table 5: Reply-To Red Flags

| Red Flag                          | Indicator Description                                        | Rationale                                                 |
|-----------------------------------|--------------------------------------------------------------|-----------------------------------------------------------|
| Domain differs from From          | Reply-To domain not aligned with From                        | Common in phishing; less common for routine business.     |
| Public provider mismatch          | From corporate, Reply-To consumer provider                   | Weak legitimacy; potential compromise or impersonation.   |
| Near-colliding domain             | Small typo in Reply-To domain                                | Lookalike redirection to adversary-controlled mailbox.    |
| Excessive URL shorteners          | Indirection via shorteners present in links in body          | Often accompanies Reply-To misuse (body signal).          |

## Extracting IPs and Domains from Headers

Consistent extraction underpins reliable detection. IP addresses and domains are scattered across Received, From, Return-Path, DKIM signatures, and authentication headers. Normalization and validation are essential to avoid false positives and to create reliable signals.

### Table 6: Regex Patterns Catalog for IP/Domain Extraction

| Pattern Category      | Example Pattern (indicative)                 | Notes on Usage                                           |
|----------------------|-----------------------------------------------|----------------------------------------------------------|
| IPv4                 | \b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b | Validate octet ranges; avoid matching port numbers.      |
| IPv6                 | \b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b | Normalize case; handle dual-stack contexts.              |
| Domain               | \b([A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b            | Lowercase; handle punycode and internationalized domains. |
| Punycode prefix      | \bxn--[A-Za-z0-9-]+\b                         | Convert punycode to Unicode for display; keep original.  |
| Email                | <([A-Za-z0-9._%+-]+)@(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})> | Capture local-part and domain separately.                |
| DKIM d= domain       | d=([A-Za-z0-9.-]+\.[A-Za-z]{2,})              | Extract signing domain; apply alignment checks.          |
| DKIM s= selector     | s=([A-Za-z0-9._-]+)                           | Used for troubleshooting and reputation checks.          |

Parsing should avoid over-matching by anchoring patterns and excluding obvious ports or brackets used for other purposes. For example, an IP embedded within a larger token should not be treated as a peer hop unless it appears in a Received field.

### Validation and Enrichment

Raw matches are insufficient; validation adds confidence and context:
- Reverse DNS (PTR) checks and forward-confirmed reverse DNS (FCRDNS) validate that an IP maps to the declared hostname and back.
- Autonomous System Number (ASN) lookup classifies infrastructure (for example, cloud providers, hosting, broadband), informing reputation.
- Reputation services (both internal and external) can score IPs and domains; whitelists with time-based decay reduce false positives from known-good senders.
- Known mail provider ranges (for example, mass-mail platforms) should be handled carefully to avoid penalizing legitimate bulk mail.

## Anomaly Detection Methods

Anomaly detection in headers spans syntax anomalies, identity misalignment, routing oddities, and behavioral inconsistencies. The most effective approach uses layered heuristics that escalate risk when multiple indicators appear together.

### Rule-Based Heuristics

Deterministic rules catch obvious issues and establish baseline coverage:
- Display-name/domain mismatch for From relative to brand expectations.
- Alignment checks between From, Return-Path (or envelope), DKIM d= domain, and any SPF-aligned domain.
- Private or reserved IPs at the edge of the internet-facing path.
- Chronology anomalies in Received (out-of-order timestamps, impossible latencies).
- Unusual HELO/EHLO behavior (mismatched reverse DNS, repeated strings across unrelated hops).

### Statistical/NLP Signals

Lightweight heuristics complement rules:
- Header token frequency analysis across campaigns (for example, repeated use of urgent terms or administrative roles in local-parts).
- Similarity scoring on domains to identify lookalikes and typosquats in From and Reply-To.
- Clustering header patterns by source infrastructure to surface outlier groups.

These methods should be tuned to avoid overfitting and must respect operational variability across business communications.

### Composite Scoring

A practical aggregation method weights anomalies by severity and confidence:
- Base score: start from zero and assign points for each anomaly.
- Severity multipliers: combine DMARC failure with domain mismatch to boost severity; escalate private IP at edge if coupled with brand impersonation.
- Authentication weighting: SPF/DKIM pass with strong alignment reduces suspicion; SPF fail with DKIM pass may indicate forwarding (moderate penalty).
- Reputational context: subtract points if infrastructure belongs to trusted providers and historical patterns are benign; decay whitelist trust over time.

False positive mitigation requires contextual exceptions:
- Mailing lists: detect footers and List-* headers; reduce scoring for Return-Path and SPF mismatches.
- Forwarding: acknowledge SPF softfail with DKIM pass; do not over-penalize.
- Known business workflows: whitelisted third-party senders that legitimately send on behalf of brands should not trigger repeated alerts.

## Security Features: SPF, DKIM, DMARC

SPF, DKIM, and DMARC provide cryptographic and policy evidence about sender legitimacy. Properly interpreting their outcomes—especially in the presence of forwarding or mailing lists—allows detectors to extract high-signal indicators.

### Table 7: Authentication Outcomes Matrix and Phishing Implications

| SPF Result | DKIM Result | DMARC Result     | Typical Cause                                | Phishing Implication                             |
|------------|-------------|------------------|----------------------------------------------|--------------------------------------------------|
| Pass       | Pass        | Pass             | Message from authorized sender; aligned       | Low risk; monitor for sophisticated lookalikes.  |
| Pass       | Pass        | Fail             | Policy misconfiguration; misalignment         | Rare; investigate; potential parser error.       |
| Pass       | Fail        | Fail             | DKIM broken/unsigned; SPF authorized relay    | Moderate; forwarding or compromise scenarios.    |
| Fail       | Pass        | Fail             | SPF misused; DKIM genuine from unrelated domain | High; likely spoofing or unauthorized use.      |
| Fail       | Fail        | Pass             | Misaligned DMARC policy or relaxed alignment  | Uncommon; cautiously escalate based on context.  |
| Softfail   | Pass        | Pass/Fail        | Forwarding or mailing list present            | Moderate; examine Received chain and alignment.  |

The key is to weigh outcomes against identity alignment and routing context. DMARC failing with evidence of domain mismatch and Reply-To redirection is a strong phishing signal. Conversely, SPF fail with DKIM pass and mailing list headers may be benign.

### SPF

SPF verifies whether the sending IP is permitted by the domain’s policy published in DNS TXT records. Failures can occur due to forwarding, third-party senders, or simple misconfiguration. Indicators include:
- SPF softfail indicating the IP is not in the allowed set but not explicitly disallowed.
- SPF fail with DKIM pass, often seen with forwarding services.
- Permissive SPF policies that allow many networks, diluting the strength of a pass result.

Parsing Authentication-Results and Received-SPF headers ensures reliable extraction of SPF status.

### DKIM

DKIM attaches a digital signature to message headers and optionally parts of the body using a selector (s=) and signing domain (d=). Verifiers check the signature with the public key published in DNS. Critical analysis points:
- DKIM pass with d= domain not aligned to From suggests the message is legitimately signed by a third-party sender; this can be acceptable for transactional mail but risky for business communications lacking explicit approval.
- DKIM fail due to tampering or unsigned headers indicates potential compromise or manipulation.
- Selector (s=) and domain (d=) values should be recorded for reputation and troubleshooting.

### DMARC

DMARC ties SPF and DKIM together, enforcing alignment between the From domain and at least one authenticated identity. It also declares a policy (none, quarantine, reject) and can provide reporting. Useful signals include:
- DMARC pass with alignment, usually a strong legitimacy indicator.
- DMARC fail withreject policy, particularly when From mismatch exists—high-confidence phishing.
- DMARC none with SPF/DKIM inconsistencies—moderate risk, needing context such as forwarding or reputable third-party providers.

## Detection Engineering Playbook

To translate the above principles into operational detection, implement a pipeline with clear steps, quality controls, and feedback loops.

### Table 8: Pipeline Stages and Validation Checks

| Stage                      | Actions                                                           | Validation Checks                                               |
|----------------------------|-------------------------------------------------------------------|-----------------------------------------------------------------|
| Ingestion                  | Collect raw headers and metadata                                  | Schema validation; ensure full header preservation              |
| Parsing                    | Normalize, unfold, extract fields and tokens                      | Consistent case; proper handling of encoded words               |
| Enrichment                 | DNS/PTR, ASN, reputation lookup                                   | Timeout handling; cached results; whitelists with decay        |
| Scoring                    | Apply rule weights and confidence; aggregate signals              | Unit tests for rule interactions; cross-field consistency       |
| Alerting                   | Thresholding and suppression logic                                | Tuning per provider; deduplication across campaigns             |
| Analyst Review             | Triage, enrichment, decisions                                     | Clear evidence logging; PI1/P2/P3 routing                       |
| Feedback                   | False positive/negative tracking; model/rule updates              | Periodic review; trend analysis; decay of old whitelists        |

Quality assurance underpins stability: unit tests validate parsing and scoring logic; periodic audits keep rules aligned with evolving attacker behaviors; documentation ensures institutional knowledge persists as teams change.

## Use Cases and Scenarios

Applying the framework to real-world scenarios demonstrates how signals combine to produce actionable detections.

### Table 9: Scenario-to-Header Features Mapping

| Scenario                              | Header Features Observed                                 | Likely Indicators                                           | Recommended Action                                          |
|---------------------------------------|-----------------------------------------------------------|-------------------------------------------------------------|-------------------------------------------------------------|
| Brand impersonation via From spoofing | From mismatch; DMARC fail; Reply-To redirection           | High-confidence phishing                                    | Quarantine; user notification; takedown request            |
| Forwarding-induced SPF fail           | SPF softfail/fail; DKIM pass; mailing list footers        | Moderate suspicion; benign forwarding                       | Allow; monitor; whitelist time-decay                       |
| Third-party marketing mail            | From brand; Return-Path differs; DKIM pass; DMARC pass    | Low-to-moderate suspicion if alignment loose                | Allow; apply brand policy; suppression lists if undesired  |
| Compromised internal host             | Private IP edge hop; anomalous Received chain; SPF/DKIM fail | High suspicion; potential compromise                        | Block; incident response; infrastructure remediation       |
| Lookalike domain phishing             | From with typosquat; Reply-To redirection; weak alignment | High suspicion                                              | Quarantine; user notification; takedown request            |

## Operationalization: Alert Triage and Response

Clear, consistent triage reduces mean time to detect and respond. Analysts should follow a standard workflow, preserving evidence and documenting decisions.

### Table 10: Triage Decision Tree and Priority Mapping

| Step                                    | Evidence to Check                                       | Decision Path                                           | Priority                |
|-----------------------------------------|----------------------------------------------------------|---------------------------------------------------------|-------------------------|
| Confirm header anomalies                | From/Return-Path/Reply-To mismatch; Received anomalies   | If none: low priority; If present: continue             | P3 → P2                 |
| Evaluate authentication                 | SPF/DKIM/DMARC outcomes; alignment                       | DMARC fail + mismatch: escalate; SPF/DKIM pass: moderate | P2 → P1                 |
| Assess infrastructure reputation        | ASN classification; IP/domain reputation                 | Poor reputation: escalate                               | Maintain or elevate     |
| Check context                           | Mailing list footers; forwarding patterns                | Benign context: reduce priority                          | Downgrade if justified  |
| Decide action                           | Quarantine, block, allow, monitor                        | Document in case notes; notify users as needed           | Assign owner            |

Evidence preservation is non-negotiable: store original headers, parsed artifacts, and a minimal set of indicators required for reproducibility. Maintain logs with privacy controls to redact PII where appropriate.

## Implementation Notes and Edge Cases

Operational realities complicate header-based detection. Strategies to handle these complexities reduce false positives and improve resilience.

### Table 11: Edge Case Handling Strategies

| Edge Case                       | Strategy                                                | Notes                                                 |
|---------------------------------|---------------------------------------------------------|-------------------------------------------------------|
| Mailing lists                   | Detect List-* headers and footers; reduce penalties     | Prioritize alignment checks and DKIM pass             |
| Forwarding (SPF softfail)       | Weight DKIM pass; adjust scoring lower                  | Maintain provider-level allowlists with decay         |
| Third-party senders             | Whitelist trusted senders; require alignment            | Periodic audits; policy documentation                 |
| IPv6/IPv4 dual-stack            | Normalize IPs; consider both paths                      | Validate reverse DNS for both protocols               |
| Private/reserved IPs at edge    | Combine with content signals before escalation          | Often benign; context is decisive                     |
| Encoded words and obfuscation   | Decode and normalize; flag heavy encoding               | Avoid over-reliance on exact string matches           |
| Rare header fields              | Extend parser schema flexibly                           | Maintain compatibility with optional fields           |
| Non-standard folding            | Respect RFC whitespace rules for concatenation          | Test parser on a variety of message samples           |

## Limitations and Risks

Header analysis has boundaries. Sophisticated phishers can craft messages that pass basic checks by leveraging legitimate services or precise alignment. Conversely, strict rules without context can overwhelm teams with false positives.

### Table 12: Limitation-to-Mitigation Mapping

| Limitation/Risk                                  | Impact                                               | Mitigation                                                   |
|--------------------------------------------------|------------------------------------------------------|--------------------------------------------------------------|
| Phishers abusing trusted services                | False negatives if rules over-trust providers        | Strong alignment checks; reputation-backed thresholds        |
| Forwarding and mailing lists                     | False positives if penalizing benign mismatches      | Context detection; adaptive scoring; whitelists with decay   |
| Overfitting to specific infrastructures          | Brittle detections; loss of generality               | Periodic audits; rule generalization; trend monitoring       |
| Insufficient ground-truth labels                 | Uncertain performance metrics                        | Targeted data collection; analyst feedback loops             |
| Ambiguity from partial header visibility         | Incomplete picture of Received chain                 | Collaborative data sharing; gateway visibility improvements  |
| No protocol-level guidance in this blueprint     | Potential misconceptions about routing nuances       | Reference canonical documents and MTA configurations         |
| Lack of specific DMARC policy implementations    | Policy-level tuning may be imprecise                 | Verify organizational policy details before deployment       |

Detectors must continuously evolve. The most effective programs combine header-based signals with content and behavior analytics, and they iterate rapidly as attacker tradecraft changes.

## Conclusion

Email header analysis is a proven, high-signal approach to phishing detection when implemented with nuance. By systematically parsing and normalizing headers, weighing authentication outcomes, and layering heuristics with contextual exceptions, organizations can build detections that scale and adapt. The strategy outlined here provides an immediate path to operational value while laying the groundwork for future improvements across data collection, feature engineering, and rule tuning.

## Appendices

### A. Glossary of Terms

| Term                        | Definition                                                                                           | Relevance                                               |
|----------------------------|------------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| SPF (Sender Policy Framework) | DNS-based policy that authorizes sending IP addresses for a domain.                                  | Detects unauthorized sending; can fail due to forwarding. |
| DKIM (DomainKeys Identified Mail) | Cryptographic signature scheme that signs headers/body to verify domain ownership and integrity. | Strong indicator of legitimate origin when aligned.     |
| DMARC (Domain-based Message Authentication, Reporting, and Conformance) | Policy layer that enforces alignment between From and SPF/DKIM identities.                         | High-confidence authenticity signal; policy-driven.     |
| RFC5322-MailFrom           | Envelope sender address used for bounces and routing.                                                | Often differs from visible From; central to SPF.        |
| HELO/EHLO                  | SMTP handshake identifiers by sending host.                                                          | Mismatches can indicate misconfiguration or spoofing.   |
| ASN (Autonomous System Number) | Numeric identifier for network ownership and routing.                                               | Informs reputation and source classification.           |
| PTR/FCRDNS                 | Reverse DNS pointer records; forward-confirmed reverse DNS validate IP-hostname mapping.            | Enhances trust in Received chain infrastructure.        |

### B. Sample Parsed Header Artifacts (Structure Only)

Note: The following examples are illustrative structures, not live data. They demonstrate how parsed artifacts might appear for downstream scoring.

#### Table 13: Parsed Header Artifacts

| Field              | Example Structure (sanitized)                     | Notes                                              |
|--------------------|---------------------------------------------------|----------------------------------------------------|
| From               | displayName="Accounts Team"; addr="notice@brand.com" | Display name and domain extracted separately.      |
| Return-Path        | "bounce@mailer.example.net"                       | Bounce address aligned to envelope sender.         |
| Reply-To           | "reply@mailer-support.net"                        | Redirect target parsed for domain alignment.       |
| Received (hop 1)   | host="edge01.example.net"; ip="203.0.113.5"; helo="edge01.example.net"; ts="2025-10-29T11:03:56Z" | Edge hop with public IP and HELO.                 |
| Received (hop 2)   | host="mx01.brand.com"; ip="198.51.100.10"; helo="mx01.brand.com"; ts="2025-10-29T11:04:01Z" | Internal hop with DMARC enforcement gateway.       |
| SPF                | "softfail (domain of transitioning bounce@mailer.example.net does not designate 203.0.113.5 as permitted sender)" | Forwarding indication; moderate risk.              |
| DKIM               | "pass (signature verified) d=mailer.example.net; s=selector1" | Third-party signing; alignment check required.     |
| DMARC              | "fail (p=reject) header.from=brand.com; d=mailer.example.net" | Strong phishing signal with misalignment.          |

### C. Rule Catalog Index

The table below indexes key rule families and references to sections where logic is described. Use it as a checklist during detection engineering and audits.

#### Table 14: Rule Catalog Index

| Rule ID  | Description                                   | Section Reference                         |
|----------|-----------------------------------------------|-------------------------------------------|
| HR-FROM-01 | Detect display-name/domain mismatch          | From → Table 2                            |
| HR-FROM-02 | Identify punycode/homoglyph domains          | From → Table 2                            |
| HR-RET-01  | Flag Return-Path ≠ From domain                | Return-Path → Table 3                     |
| HR-RET-02  | Detect dynamic/randomized subdomains          | Return-Path → Table 3                     |
| HR-RCV-01  | Private/reserved IP at edge                   | Received → Table 4                        |
| HR-RCV-02  | Chronology anomalies and impossible latency   | Received → Table 4                        |
| HR-RCV-03  | HELO/EHLO mismatches                          | Received → Table 4                        |
| HR-RPL-01  | Reply-To misalignment                         | Reply-To → Table 5                        |
| HR-RPL-02  | Reply-To lookalike domains                    | Reply-To → Table 5                        |
| AUTH-SPF-01 | SPF fail + DKIM pass (forwarding heuristic) | SPF section                               |
| AUTH-DKIM-01 | DKIM pass with unaligned d= domain         | DKIM section                              |
| AUTH-DMARC-01 | DMARC fail + misalignment                  | DMARC section                             |
| AGG-SCOR-01 | Composite scoring rubric                     | Composite Scoring section                 |

### D. Change Log and Maintenance Guidance

- Initial version: Incorporate foundational header parsing and anomaly rules; establish composite scoring; define triage workflow and rule catalog.
- Quarterly reviews: Audit rule performance, refresh whitelists, adjust weights based on false positive trends, and update detection for new phishing patterns.
- Ongoing improvements: Add new heuristics for emerging infrastructures; refine context detection for mailing lists and forwarding; strengthen alignment checks; improve logging and evidence preservation for reproducibility.

## References

No external references were used. This blueprint is based on widely known email header semantics and operational detection practices. Canonical specifications and provider implementations should be consulted for deployment-specific details and to confirm policy outcomes.