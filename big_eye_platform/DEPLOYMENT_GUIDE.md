# Quick Deploy Commands for Big Eye Platform + Database Integration

## Prerequisites
- Node.js installed
- Supabase CLI installed (`npm install -g supabase`)
- Vercel CLI installed (`npm install -g vercel`)

## Deployment Steps (Big Eye v8)

The production frontend is `big_eye_platform/big-eye` (Vite + React). The old
`vercel_app` FastAPI folder is retained for reference, but it is not required
for the Vercel frontend deployment. Supabase Edge Functions remain the secure
backend for live DNS, reputation, and ledger sync.

### 1. Deploy Edge Functions
```bash
cd big_eye_platform
supabase db push
supabase functions deploy analyze-email-security
supabase functions deploy scan-attachment-hash
supabase functions deploy get-provider-catalog
supabase functions deploy database-email-validation
supabase functions deploy database-threat-intelligence
supabase functions deploy database-comprehensive-analysis
```

### 2. Build and Deploy Frontend
```bash
# Build the application from the Vite frontend
cd big-eye
npm run build

# Deploy to Vercel
vercel --prod
```

### 3. Alternative: Use Deployment Scripts

**Linux/Mac:**
```bash
chmod +x deploy-integrated-platform.sh
./deploy-integrated-platform.sh
```

**Windows:**
```cmd
deploy-integrated-platform.bat
```

## What Gets Deployed

### New Supabase Edge Functions:
- `analyze-email-security` - six-engine phishing, malware, auth, link, and platform analysis
- `scan-attachment-hash` - privacy-preserving SHA-256 VirusTotal lookup
- `database-email-validation` - Email validation using Big Eye Security Database
- `database-threat-intelligence` - Threat intelligence querying
- `database-comprehensive-analysis` - Bulk analysis capabilities

### Enhanced React Application:
- Security Operations Command Center
- Attachment & Virus Triage
- Sync & Audit Center (scan ledger, incidents, watchlist, quotas)
- New "Database Analysis" tab (Tool #11)
- All existing tools remain unchanged
- Updated navigation with 12 total tools

## Verification

After deployment, you should see:
1. ✅ All 10 existing tools work normally
2. ✅ New "Database Analysis" tab in navigation
3. ✅ Database Analysis has 3 sub-modes:
   - Email Validation
   - Threat Intelligence
   - Comprehensive Analysis

## Troubleshooting

### Edge Functions Not Working?
```bash
# Redeploy functions
supabase functions deploy database-email-validation --no-verify-jwt
supabase functions deploy database-threat-intelligence --no-verify-jwt
supabase functions deploy database-comprehensive-analysis --no-verify-jwt
```

### Build Errors?
```bash
# Clear cache and rebuild
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Authentication Issues?
- Ensure Supabase auth is properly configured
- Check that user_analytics table exists
- Verify RLS policies are applied

### Vercel environment variables

Set these in the Vercel project for `big_eye_platform/big-eye`:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_REQUIRE_AUTH=true` for production
- `VITE_ALLOW_OFFLINE_FALLBACK=false` if a strict live-only deployment is required

Set these as Supabase Edge Function secrets (never in Vite):

- `SUPABASE_SERVICE_ROLE_KEY`
- `VIRUSTOTAL_API_KEY` (optional hash-only malware enrichment)
- `ABUSEIPDB_API_KEY`, `EMAIL_VALIDATION_API_KEY`, and other provider keys as needed

Run the v8 migration before testing cloud sync. Offline preview mode is
intentional and stores only local browser history until a user signs in.

## Features Added

### Database Analysis Tab:
1. **Email Validation**
   - Syntax verification
   - Domain validation
   - MX record checking
   - Disposable email detection

2. **Threat Intelligence**
   - IP/Domain/URL/Hash analysis
   - Multi-source threat data
   - Related indicators
   - Severity classification

3. **Comprehensive Analysis**
   - Bulk processing (up to 100 items)
   - Multiple analysis types
   - Risk assessment
   - Security recommendations

## Success Indicators

✅ **Deployment Successful When:**
- All 10 original tools work
- Database Analysis tab is accessible
- Edge functions respond without errors
- User authentication works
- Analytics tracking functions

📊 **Total Tools Available: 12**
1. All in One Analysis
2. Email Header Analyzer
3. Domain Checker
4. Email Legitimacy Checker
5. Blacklist Scanner
6. IP Intelligence
7. AI Phishing Detection
8. Temp Email Detector
9. Domain Age Tracker
10. Link Checker
11. **Database Analysis** ⭐ NEW
12. Admin Dashboard
