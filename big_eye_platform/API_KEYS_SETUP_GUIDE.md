# API Keys Guide for Big Eye Platform Enhancement

This document lists all API keys needed for the enhanced Big Eye Platform, organized by priority.

---

## Priority 1: Essential APIs (Strongly Recommended)

These APIs provide core functionality and have generous free tiers.

### 1. Google Safe Browsing API

**Purpose:** Primary phishing and malware detection for URLs  
**Free Tier:** 10,000 queries per day  
**Cost:** Free  

**How to Get:**
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing project
3. Enable "Safe Browsing API"
   - Navigate to "APIs & Services" → "Library"
   - Search for "Safe Browsing API"
   - Click "Enable"
4. Create API Key:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy the API key
5. (Optional) Restrict the API key to only Safe Browsing API for security

**Environment Variable Name:** `GOOGLE_SAFE_BROWSING_API_KEY`

---

### 2. AbuseIPDB API Key

**Purpose:** IP reputation scoring and abuse history  
**Free Tier:** 1,000 checks per day  
**Cost:** Free  

**How to Get:**
1. Go to https://www.abuseipdb.com/register
2. Create a free account
3. Verify your email
4. Log in and go to https://www.abuseipdb.com/account/api
5. Find your API key under "API v2"
6. Copy the API key (starts with a long alphanumeric string)

**Environment Variable Name:** `ABUSEIPDB_API_KEY`

---

### 3. AlienVault OTX API Key

**Purpose:** Threat intelligence and IoC lookup  
**Free Tier:** Unlimited queries  
**Cost:** Completely free  

**How to Get:**
1. Go to https://otx.alienvault.com/
2. Click "Sign Up" (top right)
3. Create a free account
4. Verify your email and log in
5. Go to Settings (click your profile icon → Settings)
6. Navigate to "API Integration" tab
7. Copy your OTX API Key

**Environment Variable Name:** `ALIENVAULT_OTX_API_KEY`

---

## Priority 2: Enhanced APIs (Recommended)

These APIs add advanced features and have reasonable free tiers.

### 4. VirusTotal API Key

**Purpose:** Multi-engine malware scanning (70+ AV engines)  
**Free Tier:** 500 requests per day (4 per minute)  
**Cost:** Free  

**How to Get:**
1. Go to https://www.virustotal.com/gui/join-us
2. Click "Sign up" and create account
3. Verify your email
4. Log in and click your profile icon (top right)
5. Go to "API Key" section
6. Copy your personal API key

**Environment Variable Name:** `VIRUSTOTAL_API_KEY`

**Note:** Free tier has rate limit of 4 requests/minute. Edge function handles this automatically.

---

### 5. PhishTank API Key

**Purpose:** Community-sourced phishing URL verification  
**Free Tier:** Free, no hard limits  
**Cost:** Free  

**How to Get:**
1. Go to https://www.phishtank.com/api_register.php
2. Fill out the registration form
3. Agree to terms of service
4. Submit the form
5. You'll receive your API key in the confirmation email
6. Also available in your dashboard after login

**Environment Variable Name:** `PHISHTANK_API_KEY`

---

### 6. URLScan.io API Key

**Purpose:** Deep URL analysis with screenshots and DOM inspection  
**Free Tier:** 100 scans per day  
**Cost:** Free  

**How to Get:**
1. Go to https://urlscan.io/user/signup
2. Create a free account
3. Verify your email
4. Log in and go to Settings/API
5. Generate or copy your API key

**Environment Variable Name:** `URLSCAN_API_KEY`

**Note:** Scans take ~10 seconds to complete. Free tier is usually sufficient for normal use.

---

## Priority 3: Advanced APIs (Optional)

These provide enhanced features but have lower free tiers or are less critical.

### 7. IPQualityScore API Key

**Purpose:** Advanced fraud scoring and proxy/VPN detection  
**Free Tier:** 5,000 lookups per month  
**Cost:** Free (paid plans available)  

**How to Get:**
1. Go to https://www.ipqualityscore.com/create-account
2. Create a free account
3. Verify your email
4. Log in to dashboard
5. Go to "API" section
6. Copy your Private Key

**Environment Variable Name:** `IPQUALITYSCORE_API_KEY`

---

### 8. CrowdSec API Key

**Purpose:** Community threat intelligence for IP addresses  
**Free Tier:** 50 queries per day  
**Cost:** Free (paid plans available)  

**How to Get:**
1. Go to https://www.crowdsec.net/
2. Click "Sign Up" and create account
3. Verify your email
4. Log in to CrowdSec Console
5. Go to "CTI API" section
6. Generate an API key

**Environment Variable Name:** `CROWDSEC_API_KEY`

---

## Summary

### Must Have (Priority 1):
- ✅ Google Safe Browsing API Key
- ✅ AbuseIPDB API Key
- ✅ AlienVault OTX API Key

**With these 3 keys, you get:**
- Comprehensive phishing detection
- IP reputation analysis
- Threat intelligence lookups
- ~95% of enhanced functionality

### Should Have (Priority 2):
- ✅ VirusTotal API Key
- ✅ PhishTank API Key
- ✅ URLScan.io API Key

**Adding these gives you:**
- Multi-engine malware scanning
- Community phishing verification
- Deep URL analysis with screenshots
- 100% enhanced functionality

### Nice to Have (Priority 3):
- IPQualityScore API Key
- CrowdSec API Key

**These provide:**
- Advanced fraud detection
- Enhanced proxy/VPN detection
- Additional community intelligence

---

## How to Provide API Keys

Once you have the API keys, provide them in the following format:

```
GOOGLE_SAFE_BROWSING_API_KEY=your_key_here
ABUSEIPDB_API_KEY=your_key_here
ALIENVAULT_OTX_API_KEY=your_key_here
VIRUSTOTAL_API_KEY=your_key_here
PHISHTANK_API_KEY=your_key_here
URLSCAN_API_KEY=your_key_here
IPQUALITYSCORE_API_KEY=your_key_here
CROWDSEC_API_KEY=your_key_here
```

**Security Note:** These keys will be stored as Supabase secrets and never exposed in client-side code.

---

## Platform Functionality Without API Keys

The Big Eye Platform will still work without any API keys, using:
- IP-API (no key needed)
- Who-Dat WHOIS (no key needed)
- HackerTarget DNS (no key needed)
- Verify Email (no key needed)
- EmailRep.io basic (no key needed)
- Local analysis and heuristics

However, advanced features like multi-engine phishing detection, comprehensive threat intelligence, and multi-AV scanning require the API keys above.

---

## Rate Limit Summary

| API | Free Tier Limit | Sufficient For |
|-----|----------------|----------------|
| Google Safe Browsing | 10,000/day | ~400 URLs/hour |
| AbuseIPDB | 1,000/day | ~40 IPs/hour |
| AlienVault OTX | Unlimited | Any volume |
| VirusTotal | 500/day, 4/min | ~20/hour (throttled) |
| PhishTank | Free | ~100 URLs/hour |
| URLScan.io | 100/day | ~4 URLs/hour |
| IPQualityScore | 5,000/month | ~160/day |
| CrowdSec | 50/day | ~2 IPs/hour |

**Note:** The platform implements intelligent caching to minimize API calls and maximize the value of free tiers.

---

## API Key Security

- **Never commit API keys to version control**
- **Store only in Supabase secrets/environment variables**
- **Rotate keys quarterly**
- **Use separate keys for dev/staging/production if possible**
- **Monitor usage through provider dashboards**
- **Set up alerts for unusual usage patterns**

---

## Total Setup Time

- Priority 1 APIs: ~15 minutes
- Priority 2 APIs: ~15 minutes
- Priority 3 APIs: ~10 minutes

**Total Time: 30-40 minutes to get all API keys**

---

## Support & Troubleshooting

If you encounter issues:

1. **Check API key format** - Copy-paste exactly, no extra spaces
2. **Verify email** - Most services require email verification
3. **Check rate limits** - Some APIs have signup verification periods
4. **Review provider docs** - Links to official documentation provided above

---

**Last Updated:** 2025-10-30  
**Document Version:** 1.0
