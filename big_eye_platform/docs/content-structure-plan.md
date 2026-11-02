# Content Structure Plan - Big Eye

## 1. Material Inventory

**Application Type:** Cybersecurity web application (phishing detection platform)  
**Structure:** Single-Page Application (SPA) with tab-based tool navigation  
**Framework:** Next.js + TailwindCSS + shadcn/ui  

### Core Features (8 Analysis Tools)
1. Email Header Analyzer
2. Sender Domain Checker
3. Email Address Legitimacy Checker
4. Blacklist & Reputation Scanner
5. Domain/IP Intelligence Dashboard
6. AI-Powered Phishing Probability Engine
7. Temporary Email Detector
8. Email & Domain Age Tracker

### Content Requirements
- **Branding Assets**: Big Eye logo, application icon, security-themed visual identity
- **Tool Descriptions**: Concise explanations for each of the 8 analysis features
- **Example Data**: Sample email headers, domains, IP addresses for demo/documentation
- **Educational Content**: Brief phishing detection guidance, threat level explanations
- **Legal Content**: Privacy policy, terms of service, data handling disclosures
- **Help Documentation**: Feature usage instructions, API documentation (if applicable)

## 2. Website Structure

**Type:** Single-Page Application (SPA)  

**Reasoning:** 
- Matches proven security tool patterns (VirusTotal, IPQualityScore)
- Supports rapid tool switching for security analysts performing multi-faceted analysis
- Maintains analysis context across different detection tools
- Reduces cognitive load with consistent navigation and layout
- Optimizes workflow for SOC environments requiring fast triage
- All 8 tools accessible via tab navigation without page reloads

## 3. Application Layout Structure

### Global Layout (Persistent Elements)

**Header Navigation Bar (64px height)**
- **Logo Section**: Big Eye branding (left-aligned)
- **Universal Search**: Central search bar accepting emails, domains, URLs, IP addresses
- **Utility Controls**: Theme toggle (optional light mode), notifications, user profile/auth
- **Primary CTA**: "Sign Up" or "Dashboard" for authenticated users

**Main Content Area (Dynamic)**
- **Tool Selector Tabs**: Horizontal tab navigation for 8 core features
- **Analysis Input Zone**: Dynamic input interface based on selected tool
- **Results Display**: Tabbed results panel with expandable sections
- **History Sidebar** (collapsible): Recent analysis history with quick re-analysis

**Footer (Minimal)**
- Legal links (Privacy, Terms), documentation link, support/chat access
- Data sharing disclosure (following VirusTotal transparency pattern)

---

### Section Breakdown (SPA Tabs)

#### Landing/Hero Section (Pre-Analysis State)

**Purpose**: Introduction and immediate tool access for first-time users

**Content Mapping:**

| Section | Component Pattern | Content to Display | Visual Asset |
|---------|------------------|-------------------|--------------|
| Hero Banner | Full-width hero (400-500px) | "Big Eye - Advanced Phishing Detection Platform" + tagline | Big Eye logo (large) |
| Value Proposition | 3-column feature grid | Brief descriptions of threat detection capabilities | Security icons (shield, scan, alert) |
| Quick Start | Tool selector cards (8 cards) | Each tool name + 1-sentence description | Tool-specific icons |
| Trust Indicators | Horizontal badge row | "WCAG Compliant", "Industry Standard Algorithms", "Open Source" | Badge icons |

**FORBIDDEN**: Design styling decisions (colors, alignment) - see Design Specification for visual treatment

---

#### Tab 1: Email Header Analyzer

**Purpose**: Parse and analyze email headers for routing, authentication, and spoofing indicators

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Textarea + submit button | User paste input | Raw email headers (multi-line text) | - |
| Authentication Results | Status card grid (3 cards) | Analysis output | SPF, DKIM, DMARC pass/fail status | Authentication icons |
| Routing Timeline | Vertical timeline component | Header parsing | Server hops with IP addresses + timestamps | Server icons |
| Threat Score | Large score card | AI analysis | Phishing probability (0-100) + risk level | Alert badge |
| Header Details | Expandable accordion | Raw headers | Parsed header fields (From, To, Reply-To, Return-Path, etc.) | - |

---

#### Tab 2: Sender Domain Checker

**Purpose**: Validate sender domain reputation, DNS records, and historical security data

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Single-line input + button | User input | Domain name (e.g., example.com) | - |
| Domain Status | Primary status card | DNS/WHOIS lookup | Domain age, registrar, registration date | Domain icon |
| DNS Records | Data table | DNS query results | SPF, DKIM, DMARC, MX records | DNS icon |
| Reputation Score | Gauge chart | Blacklist check | Reputation score + blacklist status | Reputation badge |
| SSL Certificate | Card with certificate details | SSL Labs API | Certificate validity, issuer, grade | Lock icon |

---

#### Tab 3: Email Address Legitimacy Checker

**Purpose**: Validate email address syntax, deliverability, and disposable/temporary status

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Email input + validate button | User input | Email address | - |
| Validation Results | Multi-metric card | Email validation API | Syntax valid, SMTP valid, disposable status, role-based | Checkmark/X icons |
| Deliverability | Status indicator | MX record check | Mailbox exists, catch-all status | Mail icon |
| Risk Indicators | Badge list | Analysis | High-risk flags (disposable, leaked, spam trap) | Warning badges |
| Domain Analysis | Linked card | Cross-reference | Link to Sender Domain Checker for parent domain | Link icon |

---

#### Tab 4: Blacklist & Reputation Scanner

**Purpose**: Check email/domain/IP against major blacklists and reputation databases

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Multi-type input (email/domain/IP) | User input | Target to scan | - |
| Blacklist Status | Grid of status cards (6-8 cards) | Blacklist APIs | Individual blacklist results (Spamhaus, SURBL, etc.) | Database icons |
| Overall Reputation | Large score display | Aggregated score | Composite reputation (0-100) with color coding | Shield icon |
| Detection Summary | Summary card | Blacklist hits | "Listed on X of Y blacklists" + severity | Alert icon |
| Historical Data | Line chart (optional) | Time-series data | Reputation trend over time | Chart visualization |

---

#### Tab 5: Domain/IP Intelligence Dashboard

**Purpose**: Comprehensive intelligence on domains and IP addresses including geolocation, ASN, and threat data

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Dual input (domain OR IP) | User input | Domain or IP address | - |
| Geolocation Map | Interactive map component | IP geolocation API | Country, region, city, coordinates | Map visualization |
| Network Information | Data card | WHOIS/ASN lookup | ISP, ASN, network range, organization | Network icon |
| Threat Intelligence | Threat indicator cards | Threat feeds | Known malicious activity, abuse reports | Threat icons |
| DNS History | Timeline component | Passive DNS data | Historical DNS records and changes | Timeline visualization |
| Port Scan Results | Table (if applicable) | Port scan data | Open ports, services detected | Port icon |

---

#### Tab 6: AI-Powered Phishing Probability Engine

**Purpose**: Machine learning analysis combining all signals for comprehensive phishing assessment

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Multi-field form | User input | Email address, domain, headers, sender info | - |
| AI Confidence Score | Large prominent score (0-100) | ML model output | Phishing probability percentage | AI brain icon |
| Risk Breakdown | Horizontal bar chart | Feature importance | Contributing factors (domain age, blacklist, headers, etc.) | Chart visualization |
| Decision Recommendation | Action card | Threshold logic | "Block", "Review", "Allow" with rationale | Decision badge |
| Similar Threats | Card carousel | Threat database | Previously detected similar phishing attempts | Threat cards |
| Explainability | Collapsible details panel | ML interpretation | Why the AI assigned this score (transparency) | Info icon |

---

#### Tab 7: Temporary Email Detector

**Purpose**: Identify disposable/temporary email addresses and services

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Email input + check button | User input | Email address | - |
| Detection Result | Large status card | Temp email database | Temporary/disposable status (boolean) | Temp mail icon |
| Service Information | Info card | Database lookup | Known temp email service name (e.g., Guerrilla Mail) | Service icon |
| Domain Patterns | Data list | Pattern analysis | Domain patterns indicating temp services | Pattern icon |
| Lifetime Estimate | Duration indicator | Service data | Estimated email lifespan (if known) | Clock icon |
| Alternative Detection | Cross-check results | Multiple detection methods | Confirmation from multiple sources | Checkmark icons |

---

#### Tab 8: Email & Domain Age Tracker

**Purpose**: Historical analysis of email addresses and domains to detect recently created threats

**Content Mapping:**

| Section | Component Pattern | Data Source | Content to Extract | Visual Asset |
|---------|------------------|-------------|-------------------|--------------|
| Input Panel | Email/domain input | User input | Email address or domain | - |
| Age Display | Large metric card | WHOIS/registration data | Domain age (days/months/years) | Calendar icon |
| Registration Details | Info card | WHOIS lookup | Registration date, registrar, last updated | Registration icon |
| Risk Assessment | Age-based risk indicator | Age analysis | "Newly registered" warning if <30 days | Warning badge |
| Historical Changes | Timeline | WHOIS history | Ownership/registrar changes over time | Timeline visualization |
| Email First Seen | Data point | Email intelligence | First appearance in databases (if available) | First seen icon |

---

### Cross-Tool Features (Shared Components)

**Analysis History Panel** (Collapsible Sidebar)
- Recent queries list with timestamps
- Quick re-run button
- Export history feature
- Clear history option

**Results Export**
- JSON download option
- PDF report generation
- Share analysis link (if implementing)

**Help/Documentation Access**
- Contextual help icons per tool
- Link to full documentation
- Tooltips for technical terms

---

## 4. Content Analysis

**Information Density:** High
- 8 distinct analysis tools with specialized data displays
- Multiple data sources per tool (APIs, databases, ML models)
- Real-time analysis requiring dynamic content updates
- Technical security data requiring careful presentation

**Content Balance:**
- **Data Visualizations:** 40% (charts, maps, timelines, gauges)
- **Structured Data Tables:** 30% (DNS records, blacklist results, headers)
- **Status Indicators:** 20% (badges, scores, threat levels)
- **Instructional Text:** 10% (tool descriptions, help text, guidance)

**Content Type:** Data-driven / Dashboard-focused
- Primary focus: Real-time threat analysis results
- Secondary: Educational guidance on phishing detection
- Tertiary: Legal/compliance disclosures

**User Flow:**
1. Land on hero/tool selection
2. Select analysis tool via tab navigation
3. Input target (email/domain/IP)
4. Submit for analysis
5. Review color-coded results with expandable details
6. Export or save to history
7. Switch to different tool for additional analysis (maintain context)

**Key Design Considerations:**
- Instant feedback on analysis progress (loading states)
- Clear threat-level visualization (red/yellow/green coding)
- Progressive disclosure for technical details
- Accessibility for both technical and non-technical users
- Mobile-responsive for on-the-go security checks
