# Email Header Analysis for Phishing Detection: Fields, Extraction, Anomalies, and Security Signals

## Executive Summary

Phishing remains one of the most persistent and damaging threats facing organizations today. While detection has diversified to include content analysis, behavior modeling, and user reporting, the email header remains the most reliable, low-friction artifact for quickly assessing sender legitimacy, routing integrity, and authentication posture. In practice, a disciplined review of the From, Return-Path, Received, and Reply-To fields—combined with a structured interpretation of Sender Policy Framework (SPF), DomainKeys Identified Mail (DKIM), and Domain-based Message Authentication, Reporting & Conformance (DMARC)—yields high-signal indicators of phishing and spoofing with minimal complexity.

This report provides a practitioner-focused blueprint for analyzing email headers for phishing detection. It explains which fields matter most, how to extract IPs and domains correctly, how to identify anomalies, and how to operationalize SPF, DKIM, and DMARC signals in detection rules and investigative workflows. It also summarizes what the evidence says about machine learning (ML) models built on header-derived features and presents a step-by-step workflow for triage, plus a pragmatic implementation guide for sustainable detection engineering.

Top actionable recommendations:
- Anchor initial triage on alignment and mismatch checks: compare visible From with envelope sender and DKIM signing domain; assess Reply-To alignment; examine the Received chain for improbable hops, private/public IP anomalies, and HELO mismatches.
- Treat SPF/DKIM/DMARC results as a signal layer, not a verdict: use DMARC failure plus alignment problems as high-severity indicators; use SPF softfail with DKIM pass as a possible forwarding signal; use DKIM pass with misaligned signing domain as medium risk (common in third-party mailers).
- Combine deterministic heuristics with lightweight ML when appropriate: research shows header-only features can support accurate classification of both spam and phishing, with stacked supervised models achieving very high accuracy in benchmarks; consider one-class models for outlier detection in specialized use cases.[^8][^9]
- Enforce disciplined parsing and evidence handling: normalize case and whitespace, reliably extract IPs/domains from Received and authentication headers, and preserve original headers for reproducibility and audit.
- Make header review a standard operating procedure: codify header analysis steps in incident response playbooks and train analysts to leverage provider-specific headers (e.g., Microsoft X-headers) to accelerate investigations.[^2][^6]

The blueprint integrates practical techniques drawn from security vendors, platform documentation, and academic research to give defenders a rigorous, operationally relevant approach.

---

## Email Header Fundamentals and Why Headers Matter for Security

An email’s header is metadata that documents origin, delivery path, and authentication. Unlike the body, which can be manipulated or obscured (for example, via images or obfuscated HTML), header fields are added incrementally by sending and relaying systems. This creates a chain of custody that, when interpreted correctly, provides a high-fidelity picture of how a message moved across the internet and whether its sender identity and content were authenticated. The discipline of header analysis is therefore a foundational security skill for analysts and platform engineers alike.[^1][^2][^3]

Practically, headers matter because:
- Spoofing and business email compromise (BEC) often hinge on mismatches between the visible From and the envelope/return-path, or between the From and Reply-To. Headers expose these mismatches quickly.
- The Received chain reveals anomalies such as improbable routing, private IPs at internet edges, mismatched HELO/EHLO strings, or missing hops—any of which can indicate tampering or compromised infrastructure.
- Authentication-Results, Received-SPF, and vendor X-headers summarize SPF, DKIM, and DMARC verdicts, enabling rapid evaluation of trust signals that complement observed anomalies.[^2][^6]

### Core Fields and Their Semantics

Four fields are especially important in day-to-day phishing triage:

- From: The visible sender address and display name. Easy to spoof, but when combined with envelope and authentication signals, it is highly informative.
- Return-Path: The envelope sender used for bounces and routing; often aligned with SPF’s MAIL FROM. Divergence from From is not inherently malicious but requires context.
- Reply-To: The destination for replies. Divergence from From is a common red flag in phishing and BEC.
- Received: An ordered list of hops showing each server that handled the message, including hostnames, IPs, timestamps, and sometimes HELO/EHLO strings.[^1][^3]

Additional fields such as Message-ID (uniqueness and domain origin), Date (chronology anchor), and X-headers (provider-added metadata) further aid analysis and triage.[^1][^6]

#### Table 1: Core Header Fields and Their Roles

| Field         | Typical Content                                   | Role in Security Analysis                                         |
|---------------|----------------------------------------------------|-------------------------------------------------------------------|
| From          | Display Name <local-part@domain>                   | Visible sender; compare with envelope and auth domains.           |
| Return-Path   | <local-part@domain>                                | Envelope/bounce path; used in SPF checks.                         |
| Reply-To      | <local-part@domain>                                | Reply destination; misalignment suggests phishing/BEC.            |
| Received      | Hop-by-hop chain with host/IP/date/protocol        | Trace routing; detect anomalies and tampering.                    |
| Message-ID    | Globally unique identifier                         | Correlate logs; detect mass-mail patterns or anomalies.           |
| Date          | Original send time                                 | Chronology anchor; time drift and mismatches are suspicious.      |
| Authentication-Results | SPF/DKIM/DMARC verdicts               | Summarizes trust signals for triage and rule logic.               |
| X-Headers     | Vendor-specific metadata                           | Adds context (antivirus, spam verdict, policy applied).           |

In practice, received headers are listed newest to oldest. Analysts should parse and sequence them to reconstruct the journey, while recognizing that some headers may be missing or rewritten by intermediaries.[^1][^3]

### Header Structure and Folding

Headers follow “Field: Value” lines and may span multiple lines via folding (subsequent lines begin with whitespace). Normalization—lowercasing domain names and trimming whitespace—reduces false positives during automated comparison. The Received chain is the most structured header and frequently contains bracketed IPs, HELO/EHLO strings, and timestamps. Mail providers often add X-headers that vary by environment; awareness of these differences prevents misinterpretation.[^1][^3][^6]

### Operational Context: How Headers are Added

Headers are added by both the sender and each relaying server. The sender generates early headers (From, Return-Path, Message-ID, Date), while each hop appends a Received line. Some systems add X-headers to document spam verdicts, anti-malware scans, and policy outcomes. Understanding this progression helps investigators trace origin, judge whether a path is plausible, and identify where anomalies were introduced.[^1][^2][^6]

---

## How to Access and Parse Headers in Common Platforms

Before analysis, analysts must reliably access full headers. Methods vary by client and are well-documented by vendors and community guides.[^1][^3][^6]

#### Table 2: Client-to-Action Mapping for Header Access

| Client/Platform           | Action to View Full Headers                                   |
|---------------------------|---------------------------------------------------------------|
| Gmail (web)               | Open message → More (⋮) → Show original → Copy to file.       |
| Outlook (web)             | Open message → More actions (⋯) → View message source.        |
| Outlook (desktop)         | Open message → File → Properties → Internet headers.          |
| EML file (general)        | Open in text editor; header appears at top of file.           |
| MSG file (Outlook)        | File → Properties → Internet headers.                         |

Provider analyzers can accelerate triage by parsing and highlighting key fields. For example, Microsoft’s Message Header Analyzer and comparable tools visualize the hops and authentication results, making anomalies and verdicts immediately apparent.[^6]

---

## Extracting IPs and Domains from Headers

Extracting the right IPs and domains is the cornerstone of header-based triage. The goal is to identify the sending infrastructure (first public IP), intermediate hops, and relevant domains for alignment and reputation checks.

Key strategies:
- Use the first public IP in the Received chain as the sending IP, while validating with reverse DNS (PTR) and FCRDNS when available.
- Extract domains from From, Reply-To, Return-Path, DKIM d= header, and Authentication-Results fields; normalize to lowercase.
- Validate extracted IPs via WHOIS/ASN and check reputation; beware masked IPs in webmail contexts and the reliability caveats of X-Originating-IP.[^3][^4][^5][^6]

#### Table 3: Extraction Sources and Purpose

| Source/Field            | What to Extract                                | Purpose                                                  |
|-------------------------|-------------------------------------------------|----------------------------------------------------------|
| Received (first public) | Sending IP, HELO/EHLO, hostname                 | Origin assessment; SPF context; HELO mismatch checks.    |
| Received (subsequent)   | Intermediate IPs and hostnames                  | Path plausibility; anomaly detection.                    |
| From                    | Domain and local-part                            | Visible sender; alignment checks with auth domains.      |
| Return-Path             | Domain                                           | Envelope sender; SPF MAIL FROM context.                  |
| Reply-To                | Domain                                           | Reply alignment; BEC patterns.                           |
| DKIM-Signature          | d= domain, s= selector                          | Signing domain; reputation and alignment.                |
| Authentication-Results  | spf/dkim/dmarc verdicts, smtp.mailfrom, header.d | Authentication posture and alignment evidence.           |
| X-Originating-IP        | IP (if present)                                 | Clue only; treat with caution due to masking and unreliability. |

#### Table 4: Common IP/Domain Regex Patterns and Validation Notes

| Pattern Type | Example Pattern                                  | Notes                                                          |
|--------------|---------------------------------------------------|----------------------------------------------------------------|
| IPv4         | \b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b | Validate octet ranges; avoid ports and trailing punctuation.   |
| IPv6         | \b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b   | Normalize case; handle dual-stack contexts.                    |
| Domain       | \b([A-Za-z0-9-]+\.)+[A-Za-z]{2,}\b               | Lowercase; strip surrounding brackets/parentheses if present. |
| Email        | <([A-Za-z0-9._%+-]+)@(([A-Za-z0-9-]+\.)+[A-Za-z]{2,})> | Capture local-part and domain separately for alignment checks. |
| DKIM d=      | d=([A-Za-z0-9.-]+\.[A-Za-z]{2,})                 | Use for signing domain; align with visible From when possible.|
| DKIM s=      | s=([A-Za-z0-9._-]+)                              | Selector value for troubleshooting and reputation checks.      |

As a rule, always validate IPs using WHOIS to determine ownership, ASN classification, and geography; perform PTR and FCRDNS to establish hostname consistency. Be cautious with X-Originating-IP—it can be spoofed or omitted by webmail providers, and reliance on it without corroboration increases false positive risk.[^3][^4][^5]

### Reliable IP Extraction from Received Headers

Parsing Received lines requires extracting bracketed IPs, hostnames, dates, and HELO/EHLO strings. The first public IP encountered typically represents the sending infrastructure. Identify private or reserved IPs (e.g., RFC1918 ranges) in internet-facing hops as suspicious, especially when combined with visible sender claims of enterprise origin. HELO/EHLO mismatches—where the HELO string does not align with reverse DNS or the receiving server’s expectations—can indicate misconfiguration or spoofing.[^3][^4][^6]

#### Table 5: Example Received Fields and Extracted Elements

| Example Fragment                                                                 | Hostname                     | IP            | Protocol     | Timestamp                           | HELO/EHLO            |
|----------------------------------------------------------------------------------|------------------------------|---------------|--------------|-------------------------------------|----------------------|
| Received: from mail-ej1-f68.google.com (mail-ej1-f68.google.com [209.85.218.68]) | mail-ej1-f68.google.com      | 209.85.218.68 | ESMTPS       | Tue, 15 Jun 2021 09:45:33 -0700     | (from Google)       |
| Received: from edge01.example.net (10.0.0.1) by mx.recipient-domain.com ...      | edge01.example.net           | 10.0.0.1      | SMTP         | Tue, 15 Jun 2021 09:46:00 -0700     | edge01.example.net   |
| Received: from client.example.com (192.168.1.100) by smtp.example.org ...        | client.example.com           | 192.168.1.100 | SMTP         | Tue, 15 Jun 2021 09:47:00 -0700     | client.example.com   |

In this illustrative sequence, the first hop shows a Google infrastructure IP (typical for webmail), the second shows an internal private IP—plausible as a last-hop edge device—but the third hop’s private IP indicates caution when interpreted alongside the visible From and authentication results. Always corroborate with SPF/DKIM/DMARC and reputation checks before escalating.[^2][^4][^6]

### Domain Extraction from From/Reply-To/Return-Path and DKIM

Normalize domains by lowercasing and removing bracketing or surrounding whitespace. Alignment checks compare visible From with:
- The envelope/Return-Path domain (MAIL FROM), which informs SPF.
- The DKIM d= signing domain.
- The domains present in Authentication-Results (smtp.mailfrom and header.d).[^2][^6]

Reply-To misalignment (domain differs from From) is a common BEC tactic, and DKIM signatures by third-party mailers may legitimately differ from the visible From domain, but warrant heightened scrutiny in enterprise contexts.[^2][^3]

---

## Anomaly Detection Methods Using Header Signals

Header-derived anomaly detection balances deterministic heuristics (rules) with statistical methods (ML). Rules catch obvious issues and provide explainable logic; ML adds scalability and generalization, particularly when content or language features are unavailable. A practical approach is to encode features directly from headers (e.g., counts, comparisons, missingness) and train classifiers or outlier detectors on labeled or unlabeled data. Research demonstrates that header-only features can achieve high accuracy on both spam and phishing classification tasks.[^8][^9]

### Rule-Based Heuristics

Heuristics focus on alignment and mismatch indicators:
- From vs Return-Path (envelope) mismatch, especially with weak authentication.
- Reply-To divergence from From.
- DKIM signing domain misaligned with From.
- SPF softfail/fail with DKIM pass, often associated with forwarding or mailing lists (contextualize before escalating).
- Private or reserved IP at the first public hop, especially with brand impersonation claims.
- Chronology anomalies in the Received chain (out-of-order timestamps, improbable latency).
- HELO/EHLO mismatch with reverse DNS or sender claims.[^1][^3][^5][^10]

#### Table 6: Anomaly Types, Indicators, and Example Checks

| Anomaly Type                       | Indicator/Check                                                  | Rationale                                           |
|-----------------------------------|------------------------------------------------------------------|-----------------------------------------------------|
| From ↔ Return-Path mismatch       | Visible From domain differs from envelope domain                 | Common in phishing; assess SPF/DKIM/DMARC posture.  |
| From ↔ Reply-To mismatch          | Reply-To domain differs from From                                | Classic BEC pattern for redirection.                |
| DKIM d= misalignment              | DKIM signing domain differs from From                            | Third-party mailer or spoofing; elevate risk.       |
| SPF fail with DKIM pass           | SPF softfail/fail; DKIM pass                                     | Forwarding or mailing list; moderate suspicion.     |
| Private IP at edge                | First public hop shows private/reserved IP                       | Potential spoofing or misconfiguration.             |
| Received chronology anomalies     | Timestamps out-of-order; improbable latency                      | Tampering or forged hops.                           |
| HELO/EHLO mismatch                | HELO string not matching reverse DNS                             | Misconfiguration or spoofing.                       |
| Timezone mismatch                 | Date timezone inconsistent with IP geography                     | Possible masked origin; cross-validate.             |
| X-Originating-IP missing/stripped | Header absent or sanitized                                       | Webmail masking; corroborate with other signals.    |

Interpret anomalies in combination; isolated oddities can be benign, but two or more together often indicate elevated risk.

### Machine Learning on Header Features

Header-derived ML commonly uses features that do not require language understanding, making them language-agnostic and resilient to content obfuscation. Categories include missingness, counts, value checks, and cross-field comparisons. Reported performance on public datasets indicates that header-only features can support highly accurate spam and phishing detection, especially under supervised settings; one-class methods can also be effective when labeled anomalous data are scarce.[^8][^9]

To visualize feature relationships and evaluation outcomes in the referenced research, consider the following figures:

![Figure (arXiv 2203.10408): Illustrative visualization related to header-based features/modeling](.pdf_temp/viewrange_chunk_1_1_5_1761707369/images/lh07jr.jpg)

![Figure (arXiv 2203.10408): Example/result visualization from email anomaly detection study](.pdf_temp/viewrange_chunk_2_6_10_1761707380/images/iie80y.jpg)

The figures above, adapted from the academic study, illustrate the role of header-derived features and comparative model performance. In practice, the most consistently useful features include: the number of Received hops, domain matching across From/Return-Path/Message-ID/DKIM d=, timezone presence in Date, content-type checks (for HTML), and comparison features that test whether consecutive Received hops have coherent from/by domain relationships.[^8]

#### Table 7: Header Feature Categories with Examples

| Category                 | Example Feature                                                  | Notes                                                       |
|--------------------------|------------------------------------------------------------------|-------------------------------------------------------------|
| Missing-based            | Message-ID present (0) or missing (1)                            | Missingness itself can be informative.                      |
| Counting-based           | Number of Received hops; number of recipients                    | Path length and recipient breadth can indicate campaigns.   |
| Header value-based       | Date timezone; Content-Type is text/html; Message-ID domain      | Directly extract and normalize field values.                |
| Comparison-based         | From domain vs Return-Path domain; From vs DKIM d=; Received hop domain continuity | High signal for spoofing and routing anomalies.             |
| External lookup-based    | IP legality; presence of blacklisted SMTP servers (where feasible) | Often excluded due to data staleness; useful when current.  |

Supervised classifiers (Random Forest, SVM, MLP, KNN) consistently perform well; stacked ensembles slightly improve metrics. One-Class SVMs (trained on ham only) are valuable in contexts where phishing exemplars are limited or concept drift is expected.[^8][^9]

#### Table 8: Reported Accuracy from Referenced Studies (Header-only/Header-centric)

| Study                                                  | Task                  | Best Reported Accuracy | Notes                                         |
|--------------------------------------------------------|-----------------------|------------------------|-----------------------------------------------|
| Beaman & Isah (arXiv:2203.10408)                       | Ham vs Spam           | ~99%                   | Stacked RF+MLP+kNN achieved ~99.7% accuracy.  |
| Beaman & Isah (arXiv:2203.10408)                       | Ham vs Phishing       | ~97–98%                | Stacked SVM+GBRT+MLP achieved ~98.6% accuracy.|
| IEEE Conf. Paper (Doc 10912024)                        | Spam/Phishing         | 99.69%/99.12%          | NB/MLP/RF with feature selection (GA/SA).     |

These results indicate that header-centric signals can deliver robust detection without content analysis—useful in environments where content is unavailable or privacy constraints limit use of body text.[^8][^9]

#### Table 9: Algorithm Quick Reference

| Algorithm            | Typical Use-Case                             | Strengths                                  | Caveats                                  |
|---------------------|-----------------------------------------------|--------------------------------------------|-------------------------------------------|
| Random Forest       | General classification on mixed header features | Robust, handles missingness well           | Can overfit without careful tuning        |
| SVM                 | High-dimensional feature spaces                | Strong margin generalization                | Sensitive to feature scaling              |
| MLP (Neural Net)    | Complex non-linear patterns                    | Captures interactions across features       | Requires careful regularization           |
| KNN                 | Similarity-based classification                | Simple, effective on well-scaled features   | Sensitive to feature scales and noise     |
| One-Class SVM       | Outlier detection (ham-only training)          | Useful when anomalies are rare              | Requires careful kernel/hyperparameter    |

---

## Security Features: SPF, DKIM, and DMARC

Authentication mechanisms provide essential trust signals. Their outcomes must be interpreted carefully—passing one check while failing another does not automatically imply phishing, but the combination with alignment and observed anomalies determines risk.

#### Table 10: Authentication Outcomes Matrix

| SPF        | DKIM       | DMARC     | Typical Cause                                 | Phishing Implication                         |
|------------|------------|-----------|-----------------------------------------------|----------------------------------------------|
| Pass       | Pass       | Pass      | Legitimate, aligned sender                     | Low risk; monitor for lookalike domains.     |
| Pass       | Fail       | Fail/None | Broken DKIM or body/header tampering           | Moderate to high if combined with mismatches.|
| Fail       | Pass       | Fail      | SPF misuse; DKIM legitimate by third-party     | High; likely spoofing or unauthorized use.   |
| Softfail   | Pass       | Pass/Fail | Forwarding or mailing lists                     | Moderate; contextualize and monitor.         |
| Fail       | Fail       | Fail      | Explicit spoofing; weak/no policy               | High risk; consider quarantine/reject.       |
| Pass       | Pass       | Fail      | Misaligned DMARC or policy misconfiguration     | Investigate; uncommon but possible.          |

Interpretation hinges on alignment:
- DMARC checks alignment between the visible From and at least one authenticated identity (SPF-aligned MAIL FROM or DKIM d=).
- A DKIM pass with a signing domain unrelated to From can be legitimate (third-party mailers) but merits caution; in enterprise contexts, policies often restrict this to reduce risk.[^2][^6]

Composite authentication (compauth) and reason codes provided by certain platforms offer additional nuance—for example, distinguishing explicit from implicit authentication and documenting intra-organizational scenarios or trusted ARC overrides. Reason codes such as 000 (explicit failure with policy enforcement), 100–104 (alignment passes), and 130 (trusted ARC override) help explain why a message passed or failed authentication.[^6]

### SPF

SPF validates whether the sending IP is authorized for the domain in the MAIL FROM/envelope. Failures can stem from forwarding, third-party senders, or misconfiguration. Practical indicators include:
- Pass: Sending IP matches published SPF policy.
- Fail/Softfail: Unauthorized sender; softfail indicates a weaker policy (~all).
- Neutral/None: No conclusive evaluation; often indicative of missing or ambiguous records.
- Temperror/Permerror: DNS or parsing issues requiring remediation.[^2][^6]

### DKIM

DKIM attaches a cryptographic signature to selected headers and body content. Verifiers check the signature using the public key published under the selector (s=) in DNS for the signing domain (d=). Failures indicate tampering or misconfiguration; unsigned messages increase suspicion, particularly when paired with domain mismatches.[^2][^3][^6]

### DMARC

DMARC enforces alignment and specifies policy actions when authentication fails. When DMARC fails with a reject or quarantine policy—especially alongside From misalignment—it is a strong indicator of spoofing. When DMARC passes, defenders should still watch for lookalike domains, third-party mailer signatures, and relaxed alignment patterns that attackers can abuse.[^2][^6]

---

## Use Cases and Scenarios

The following scenarios demonstrate how header checks and authentication signals combine to produce actionable detections.

#### Table 11: Scenario-to-Header Features Mapping

| Scenario                                | Header Features Observed                                        | Likely Indicators                                   | Recommended Action                        |
|-----------------------------------------|------------------------------------------------------------------|-----------------------------------------------------|-------------------------------------------|
| Brand impersonation (From spoofing)     | From mismatch vs Return-Path; DKIM d≠ From; DMARC fail          | High-confidence phishing                             | Quarantine; user notification; takedown.  |
| Forwarding-induced SPF fail             | SPF softfail/fail; DKIM pass; List headers present               | Benign forwarding                                    | Allow; monitor; whitelist with decay.     |
| Third-party marketing mail              | From brand; Return-Path differs; DKIM pass; DMARC pass           | Low-to-moderate risk if alignment loose              | Allow; brand policy enforcement; suppress.|
| Compromised internal host               | Private IP edge; anomalous Received chain; SPF/DKIM fail         | Potential compromise                                 | Block; incident response; remediation.    |
| Lookalike domain phishing               | From with typosquat; Reply-To redirection; weak alignment        | High suspicion                                       | Quarantine; user notification; takedown.  |

In each case, authentication outcomes alone are insufficient. Analysts must weigh them alongside observed header mismatches and routing anomalies to avoid false positives and false negatives.[^1][^2][^10]

---

## Operationalization: Detection Engineering Workflow

A reliable detection pipeline transforms raw headers into explainable signals and actionable alerts. The stages below emphasize consistency, reproducibility, and continuous improvement.

#### Table 12: Pipeline Stages and Validation Checks

| Stage             | Actions                                                                 | Validation Checks                                           |
|-------------------|-------------------------------------------------------------------------|-------------------------------------------------------------|
| Ingestion         | Collect raw headers and essential metadata                              | Schema validation; complete header preservation             |
| Parsing/Normalization | Unfold headers; lowercase domains; trim whitespace; extract fields   | Unit tests for field parsing; consistent case handling      |
| Extraction        | Extract IPs/domains from Received, From/Reply-To/Return-Path, DKIM     | Regex validation; DNS/PTR checks; WHOIS/ASN enrichment      |
| Scoring           | Apply rule weights; combine auth outcomes with anomalies               | Cross-field consistency checks; avoid brittle thresholds    |
| Alerting          | Thresholding; suppression for known-good senders                       | Deduplication; provider-specific exception handling         |
| Analyst Review    | Triage; enrich with threat intel; document decisions                   | Evidence logging; consistent triage paths                   |
| Feedback          | Track false positives/negatives; adjust rules; whitelist decay         | Periodic audits; drift detection; retraining where applicable |

ML integration is natural once features are codified: supervised models can classify spam/phishing, and one-class models can surface outliers. Feedback loops (analyst labels, user reports) should drive rule tuning and model updates to mitigate concept drift.[^8][^9]

---

## Triage and Response Playbook

Analysts need a structured workflow that prioritizes evidence gathering and consistent decisions. The following decision tree table maps steps to observed evidence and priority outcomes.

#### Table 13: Triage Decision Tree and Priority Mapping

| Step                            | Evidence to Check                                      | Decision Path                                       | Priority     |
|---------------------------------|--------------------------------------------------------|-----------------------------------------------------|--------------|
| Confirm anomalies               | From/Return-Path/Reply-To mismatches; Received anomalies | If absent → low priority; if present → continue      | P3 → P2      |
| Evaluate authentication         | SPF/DKIM/DMARC verdicts; alignment; compauth reason    | DMARC fail + mismatch → escalate; DKIM pass → moderate | P2 → P1      |
| Assess infrastructure reputation| ASN classification; IP/domain reputation                | Poor reputation → escalate                           | Maintain/elevate |
| Contextualize                   | Mailing lists; forwarding patterns; provider-specific X-headers | Benign context → downgrade                           | Downgrade if justified |
| Decide action                   | Quarantine, block, allow, monitor                      | Document evidence and route                          | Assign owner |

Documentation standards should require preservation of original headers, parsed artifacts, and enrichment outputs for reproducibility and audit. Provider-specific headers (e.g., Microsoft’s X-Forefront-Antispam-Report, X-Microsoft-Antispam, Authentication-Results, compauth reason codes) should be explicitly captured and referenced in case notes to support policy alignment and escalations.[^2][^6][^10]

---

## Implementation Notes and Edge Cases

Header analysis must accommodate common operational realities without compromising signal quality. The strategies below help reduce false positives while improving resilience.

#### Table 14: Edge Case Handling Strategies

| Edge Case                    | Strategy                                                     | Notes                                                   |
|------------------------------|--------------------------------------------------------------|---------------------------------------------------------|
| Mailing lists                | Detect List-* headers; relax penalties for Return-Path/SPF   | Prioritize alignment checks and DKIM pass               |
| Forwarding (SPF softfail)    | Weight DKIM pass; lower suspicion                            | Maintain provider allowlists with time-based decay      |
| Third-party senders          | Whitelist trusted senders; require alignment                 | Regular audits; documented policy                       |
| Private/reserved IP at edge  | Combine with content signals before escalation               | Often benign; context is decisive                       |
| Encoded words/obfuscation    | Decode and normalize; flag heavy encoding                    | Avoid overreliance on exact string matches              |
| IPv6/IPv4 dual-stack         | Normalize IPs; validate both paths                           | Reverse DNS checks for both protocols                   |
| X-Originating-IP unreliability | Use as a clue only; corroborate with other signals          | Webmail often masks or strips this header               |
| Rare/unusual headers         | Extend schema flexibly; log unknowns for analysis            | Maintain optional fields for provider diversity         |

Forwarding and mailing lists frequently produce SPF softfail and Return-Path mismatches; avoid penalizing these when DKIM passes and alignment is otherwise sound. Conversely, third-party mailers that sign with unrelated domains warrant scrutiny in enterprise contexts—policy should specify acceptable scenarios and enforcement levels.[^3][^4][^6]

---

## Limitations and Risks

Header-based detection, while powerful, has boundaries. Attackers can abuse trusted services or carefully align domains to pass superficial checks; conversely, strict rules without context can overwhelm operations with false positives.

#### Table 15: Limitation-to-Mitigation Mapping

| Limitation/Risk                          | Impact                              | Mitigation                                                 |
|------------------------------------------|-------------------------------------|------------------------------------------------------------|
| Attackers abusing trusted services       | False negatives                     | Strong alignment checks; reputation-backed thresholds      |
| Forwarding and mailing lists             | False positives                     | Context detection; adaptive scoring; whitelists with decay |
| Overfitting to infrastructure            | Brittle detections                  | Periodic audits; generalization; trend monitoring          |
| Ground-truth dataset scarcity            | Uncertain metrics                   | Targeted data collection; analyst feedback loops           |
| Partial header visibility                | Incomplete chain                    | Improve gateway visibility; collaborate with providers     |
| Lack of canonical protocol guidance here | Ambiguity in edge routing behavior  | Reference RFCs and provider docs for implementation details|

A layered defense—combining header signals with content and behavior analytics—remains best practice. Continual rule tuning and ML model refresh are necessary to keep pace with attacker tradecraft.[^8][^9]

---

## Appendices

### A. Glossary

#### Table 16: Glossary of Terms

| Term                        | Definition                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------|
| SPF (Sender Policy Framework) | DNS record specifying authorized sending IPs for a domain; evaluated against the envelope (MAIL FROM) sender. |
| DKIM (DomainKeys Identified Mail) | Cryptographic signature scheme that signs headers/body to verify integrity and domain ownership.             |
| DMARC (Domain-based Message Authentication, Reporting & Conformance) | Policy layer enforcing alignment between the visible From and an SPF or DKIM identity.                      |
| RFC5322-MailFrom           | Envelope sender used for routing and bounces; primary input to SPF evaluation.                              |
| HELO/EHLO                  | SMTP handshake identifiers by the sending host; used in Received and spam verdicts.                         |
| ASN (Autonomous System Number) | Identifier for network ownership and routing; useful for reputation and classification.                   |
| PTR/FCRDNS                 | Reverse DNS pointer records; forward-confirmed reverse DNS validates IP-hostname mapping.                   |
| ARC (Authenticated Received Chain) | Protocol that preserves authentication results across forwarding; may override DMARC failure in some cases. |

### B. Sample Parsed Header Artifacts (Illustrative)

The following structures illustrate typical parsed outputs without real-world data. They demonstrate where signals originate and how downstream scoring uses them.

#### Table 17: Parsed Header Artifacts

| Field               | Example Structure (sanitized)                                           |
|---------------------|--------------------------------------------------------------------------|
| From                | displayName="Accounts"; addr="notice@brand.com"                          |
| Return-Path         | "bounce@mailer.example.net"                                             |
| Reply-To            | "reply@mailer-support.net"                                              |
| Received (hop 1)    | host="edge01.example.net"; ip="203.0.113.5"; helo="edge01.example.net"; ts="2025-10-29T11:03:56Z" |
| Received (hop 2)    | host="mx01.brand.com"; ip="198.51.100.10"; helo="mx01.brand.com"; ts="2025-10-29T11:04:01Z"         |
| SPF                 | "softfail (domain of transitioning bounce@mailer.example.net does not designate 203.0.113.5)"       |
| DKIM                | "pass (signature verified) d=mailer.example.net; s=selector1"                           |
| DMARC               | "fail (p=reject) header.from=brand.com; d=mailer.example.net"                            |

These examples show a forwarding-like scenario: SPF softfail with DKIM pass and DMARC fail due to alignment issues. Depending on policy and context, the alert may be suppressed (forwarding) or escalated (spoofing).[^2][^6]

### C. Rule Catalog Index

#### Table 18: Rule Catalog Index

| Rule ID     | Description                                        | Section Reference                |
|-------------|----------------------------------------------------|----------------------------------|
| HR-FROM-01  | Detect display-name/domain mismatch                | From → Table 6                   |
| HR-FROM-02  | Identify punycode/homoglyph domains                | From → Table 6                   |
| HR-RET-01   | Flag Return-Path ≠ From domain                     | Return-Path → Table 6            |
| HR-RET-02   | Detect dynamic/randomized subdomains               | Return-Path → Table 6            |
| HR-RCV-01   | Private/reserved IP at edge                        | Received → Table 6               |
| HR-RCV-02   | Chronology anomalies; impossible latency           | Received → Table 6               |
| HR-RCV-03   | HELO/EHLO mismatch                                 | Received → Table 6               |
| HR-RPL-01   | Reply-To misalignment                              | Reply-To → Table 6               |
| HR-RPL-02   | Reply-To lookalike domains                         | Reply-To → Table 6               |
| AUTH-SPF-01 | SPF fail + DKIM pass (forwarding heuristic)        | SPF section                      |
| AUTH-DKIM-01| DKIM pass with unaligned d= domain                 | DKIM section                     |
| AUTH-DMARC-01| DMARC fail + misalignment                         | DMARC section                    |
| AGG-SCOR-01 | Composite scoring rubric                           | Operationalization               |

### D. Maintenance Guidance

- Quarterly rule audits: review false positives/negatives, adjust rule weights and contexts (forwarding/mailing lists), and update whitelists with decay.
- ML refresh: retrain models periodically with new data, monitor drift, and incorporate analyst feedback labels.
- Documentation: maintain a changelog for rule updates and a playbook for triage edge cases to preserve institutional knowledge.

---

## References

[^1]: What Is an Email Header? A Guide for Security Teams — Abnormal AI. https://abnormal.ai/blog/what-is-an-email-header

[^2]: Anti-spam message headers — Microsoft Defender for Office 365. https://learn.microsoft.com/en-us/defender-office-365/message-headers-eop-mdo

[^3]: Email Header Analysis for Forensics: A Developer's Guide — Mail7. https://mail7.app/blog/email-header-analysis-forensics-developers-guide

[^4]: How to Detect Masked IP Address in Email Headers — MockCertified. https://blog.mockcertified.com/detect-masked-ip-address-in-email-headers/

[^5]: Email Header Analysis with Python — Sujay Sundar Raj. https://sujaysraj.com/posts/email-header-analysis/

[^6]: How to Do Phishing Email Header Analysis? — Keepnet Labs. https://keepnetlabs.com/blog/how-to-do-phishing-email-header-analysis

[^7]: Mail Header Analyzer: The Ultimate Tool for Email Security and Spam Detection — DMARCreport. https://dmarcreport.com/blog/mail-header-analyzer-email-security-spam-detection-ultimate-tool-guide/

[^8]: Anomaly Detection in Emails using Machine Learning and Header Information — arXiv. https://arxiv.org/pdf/2203.10408

[^9]: Leveraging Memetic Algorithm and Machine Learning Methods for Email-Based Spam Detection — IEEE Xplore. https://ieeexplore.ieee.org/document/10912024/

[^10]: Advanced Phishing Email Forensics Tools and Techniques — Medium. https://medium.com/@thecybersploit/advanced-phishing-email-forensics-tools-and-techniques-cf092d9a9ecf

---

## Acknowledged Information Gaps

- No ground-truth dataset or labeled examples are provided in this report; teams must curate their own for tuning and evaluation.
- Organization-specific DMARC policies and enforcement practices (p=none/quarantine/reject) are not specified and must be verified before policy-driven detection changes.
- Canonical RFC references for SMTP/email headers are not exhaustively linked here; implementers should consult relevant RFCs (e.g., RFC 5322, RFC 7001) alongside vendor documentation.
- No environment-specific SIEM field mappings are included; mapping requires local schema knowledge.