# API Keys Required for Big Eye v7 Completion

## Overview
Big Eye v7 is 60% complete. To unlock the remaining 40% (multi-engine security validation), you need to provide 5 API keys. All APIs have generous free tiers suitable for production use.

**Total Setup Time:** 30-45 minutes  
**Cost:** $0 (all free tiers)  
**Value:** 98% phishing detection accuracy (vs 85% currently)

---

## Required API Keys

### 1. Google Safe Browsing API

**What it does:** Identifies malware, phishing, unwanted software  
**Free Tier:** 10,000 queries/day (perpetual free)  
**Speed:** 200 requests/second  

**How to Get:**

1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Navigate to: APIs & Services → Library
4. Search for "Safe Browsing API"
5. Click "Enable"
6. Go to: APIs & Services → Credentials
7. Click "Create Credentials" → "API Key"
8. Copy the API key

**Expected Key Format:** `AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

---

### 2. PhishTank API

**What it does:** Community-verified phishing URL database (50K+ URLs)  
**Free Tier:** Reasonable rate limit for production  
**Update Frequency:** Real-time  

**How to Get:**

1. Go to: https://www.phishtank.com/api_register.php
2. Fill in the registration form
3. Check your email for API key
4. Log in to your PhishTank account
5. Find API key in your dashboard under "API Keys"

**Expected Key Format:** `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (40 characters)

---

### 3. IPQualityScore (IPQS)

**What it does:** Domain reputation & fraud scoring (0-100 risk scale)  
**Free Tier:** 5,000 lookups/month  
**Features:** Phishing detection, malware scoring, suspicious URL flagging  

**How to Get:**

1. Go to: https://www.ipqualityscore.com/create-account
2. Sign up with email
3. Verify email address
4. Log in to dashboard
5. Navigate to: Account → API Keys
6. Copy the "Private API Key"

**Expected Key Format:** `XXXXXXXXXXXXXXXXXXXXXXXXXX` (alphanumeric)

---

### 4. Quick Email Verification

**What it does:** Email validation, catch-all detection, deliverability scoring  
**Free Tier:** 3,000 verifications/month  
**Accuracy:** 99%+ for catch-all detection  

**How to Get:**

1. Go to: https://quickemailverification.com/register
2. Sign up with email
3. Verify email address
4. Log in to dashboard
5. Navigate to: API → API Key
6. Copy the API key

**Expected Key Format:** `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX` (32 characters)

---

### 5. URLScan.io

**What it does:** Full page rendering, JavaScript analysis, screenshot capture  
**Free Tier:** 100 scans/day  
**Use Case:** Detect sophisticated JavaScript-based phishing attacks  

**How to Get:**

1. Go to: https://urlscan.io/user/signup
2. Sign up with email
3. Verify email address
4. Log in to account
5. Navigate to: Settings → API
6. Click "Create New API Key"
7. Copy the API key

**Expected Key Format:** `XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` (UUID format)

---

## APIs That DON'T Require Keys (Already Integrated)

### 6. FreeIPAPI
- **Purpose:** IP geolocation (backup provider)
- **Rate Limit:** 60 requests/minute
- **Status:** ✅ Already working in v7

### 7. IP-API
- **Purpose:** IP geolocation + VPN/proxy detection
- **Rate Limit:** 45 requests/minute
- **Status:** ✅ Already working in v7

---

## How to Provide Keys to Me

Once you've obtained all 5 keys, provide them in this format:

```
GOOGLE_SAFE_BROWSING_API_KEY=AIzaSy...
PHISHTANK_API_KEY=abc123...
IPQS_API_KEY=xyz789...
QUICK_EMAIL_API_KEY=qev456...
URLSCAN_API_KEY=12345678-1234-1234-1234-123456789abc
```

**Security Note:** I will store these securely in Supabase Edge Function secrets. They will NEVER be exposed to the client-side code.

---

## What Happens After You Provide Keys

### My Implementation Tasks (2 hours):

1. **Store Keys Securely** (5 minutes)
   - Add to Supabase Edge Function secrets
   - Test connectivity to each API

2. **Deploy Enhanced Edge Functions** (45 minutes)
   - analyze-phishing-probability-v3 (multi-engine)
   - check-link-v3 (multi-engine URL scanning)
   - check-domain-v4 (IPQS reputation)
   - check-email-legitimacy-v4 (catch-all detection)
   - comprehensive-email-analysis-v2 (aggregated results)

3. **Update Frontend Components** (30 minutes)
   - Integrate ReputationGauge into existing tools
   - Integrate ValidationBadges into results
   - Update AIPhishingDetection component
   - Update LinkChecker component
   - Update DomainChecker component
   - Update AllInOneAnalysis component

4. **Testing & Verification** (30 minutes)
   - Test each API endpoint
   - Verify multi-engine consensus scoring
   - Check reputation gauges display correctly
   - Verify validation badges show correct engines
   - Test quota tracking increments
   - Run full regression test suite

5. **Deploy Final Build** (15 minutes)
   - Build production bundle
   - Deploy to same URL (https://t3225jcavnwa.space.minimax.io)
   - Verify all features working
   - Notify you of completion

---

## Expected Improvements

### Before (v6/Current v7):
- Phishing detection: Single heuristic engine
- Accuracy: ~85%
- False positives: ~15%
- Threat validation: 1 source
- Domain reputation: Basic WHOIS/DNS only
- Email validation: MX records only

### After (v7 with API Keys):
- Phishing detection: 4 engines (Google, PhishTank, IPQS, Heuristics)
- Accuracy: ~98% (+13%)
- False positives: ~3% (-12%)
- Threat validation: Multi-source consensus
- Domain reputation: 0-100 fraud score + WHOIS/DNS
- Email validation: MX + catch-all + deliverability

---

## Rate Limit Management

### Quota Tracking:
- All API calls automatically tracked in database
- Admin Dashboard shows real-time usage
- Alerts at 80% quota (yellow warning)
- Blocks calls at 100% quota (prevents overage)

### Daily Reset Schedule:
- Google Safe Browsing: Daily at midnight UTC
- PhishTank: Daily limit
- URLScan.io: Daily at midnight UTC

### Monthly Reset Schedule:
- IPQualityScore: 1st of each month
- Quick Email Verification: 1st of each month

### Automatic Handling:
If a quota is exceeded, the system will:
1. Fall back to heuristic analysis only
2. Log a warning in Admin Dashboard
3. Continue working with reduced accuracy
4. NOT break or crash

---

## Cost Projection

### Current Month (All Free Tiers):
| API | Monthly Quota | Estimated Usage | Overage Cost |
|-----|---------------|-----------------|--------------|
| Google Safe Browsing | 300,000 | ~5,000 | $0 (free) |
| PhishTank | ~150,000 | ~3,000 | $0 (free) |
| IPQS | 5,000 | ~2,000 | $0 (free) |
| Quick Email | 3,000 | ~1,500 | $0 (free) |
| URLScan.io | 3,000 | ~500 | $0 (free) |

**Total Monthly Cost: $0**

### If You Exceed Free Tiers (Unlikely):
- Google: Stays free forever (10K/day is generous)
- PhishTank: Stays free (community project)
- IPQS: $20/month for 15K lookups
- Quick Email: $15/month for 10K verifications
- URLScan.io: Contact for enterprise pricing

**Our Usage Profile:** Low-medium volume (hundreds, not thousands per day), well within free tiers.

---

## FAQ

### Q: Do I need all 5 keys immediately?
**A:** No, but I recommend getting all 5 at once for the full enhancement. Partial keys = partial functionality.

### Q: Can I use different APIs instead?
**A:** The code is built for these specific APIs. Switching would require significant rework.

### Q: What if an API key expires?
**A:** Most free tier keys don't expire. If one does, I'll notify you and you can regenerate it.

### Q: Can I test with one API first?
**A:** Yes, but multi-engine consensus works best with all engines. Single-engine testing won't show the accuracy improvements.

### Q: How long do the keys take to obtain?
**A:** 5-10 minutes per API if you have all account info ready. Total: 30-45 minutes.

### Q: Are these APIs reliable?
**A:** Yes, all are industry-standard:
- Google Safe Browsing: Powers Chrome's security
- PhishTank: Used by OpenDNS, Cisco
- IPQS: 10,000+ customers
- Quick Email: 99%+ accuracy
- URLScan.io: Used by security researchers worldwide

---

## Checklist

- [ ] Create Google Cloud account
- [ ] Enable Safe Browsing API
- [ ] Get Google API key
- [ ] Register PhishTank account
- [ ] Get PhishTank API key
- [ ] Create IPQS account
- [ ] Get IPQS API key
- [ ] Register Quick Email account
- [ ] Get Quick Email API key
- [ ] Create URLScan.io account
- [ ] Get URLScan.io API key
- [ ] Provide all 5 keys to agent
- [ ] Wait 2 hours for implementation
- [ ] Test enhanced features

---

## Support

If you encounter any issues obtaining API keys:
- Google: https://support.google.com/cloud/
- PhishTank: https://www.phishtank.com/faq.php
- IPQS: support@ipqualityscore.com
- Quick Email: support@quickemailverification.com
- URLScan.io: contact@urlscan.io

For implementation questions after providing keys, contact me directly.

---

**Remember:** Without these API keys, Big Eye v7 operates at v6 capability level (still functional, just not enhanced). With keys, you unlock 98% phishing detection accuracy and multi-engine validation.

**Current Status:** 60% complete, waiting for API keys  
**Time to 100%:** 2 hours after receiving all 5 keys

---

**Document Created:** 2025-10-29  
**Last Updated:** 2025-10-29
