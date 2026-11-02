# Troubleshooting Reference Card

## 🚀 Quick Diagnostics

### Check Deployment Status
```bash
# Vercel CLI
vercel ls
vercel logs <deployment-url>

# Web interface
# Go to: https://vercel.com/dashboard → Your Project → Deployments
```

### Test API Endpoints
```bash
# Basic test
curl -X GET https://your-app.vercel.app/api/endpoint

# With headers
curl -H "Authorization: Bearer <token>" https://your-app.vercel.app/api/protected

# POST request
curl -X POST -H "Content-Type: application/json" \
  -d '{"key":"value"}' \
  https://your-app.vercel.app/api/endpoint
```

---

## ❌ Common Error Messages & Solutions

### Build Errors

#### `Cannot find module 'package-name'`
**Cause:** Missing or incorrect dependency version
**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Update package.json with correct version
npm install package-name@latest

# Rebuild
npm run build
```

#### `Build command failed`
**Cause:** Build script is incorrect or failing
**Solution:**
- Verify build command in `vercel.json` or project settings
- Test locally: `npm run build`
- Check build logs for specific errors
- Update build script if needed

#### `JavaScript heap out of memory`
**Cause:** Build process requires more memory
**Solution:**
```json
{
  "functions": {
    "pages/api/**/*.ts": {
      "memory": 3008
    }
  }
}
```

#### `Module not found`
**Cause:** Incorrect import path or file doesn't exist
**Solution:**
- Verify file path is correct
- Check case sensitivity
- Ensure file has correct extension
- Clear Next.js cache: `rm -rf .next`

---

### Runtime Errors

#### `404 - Page Not Found`
**Cause:** Route doesn't exist or API structure is wrong
**Solution:**
```
Project structure:
✅ pages/api/hello.ts (correct)
❌ api/hello.ts (wrong for Pages Router)
```

#### `500 - Internal Server Error`
**Cause:** Code error in API route or page
**Solution:**
- Check function logs: `vercel logs <deployment-url>`
- Review error in browser console
- Test locally: `vercel dev`
- Add error handling

```typescript
export default async function handler(req, res) {
  try {
    // Your code
  } catch (error) {
    console.error(error)
    res.status(500).json({ error: 'Internal server error' })
  }
}
```

#### `API route returned 404`
**Cause:** Missing API route or incorrect configuration
**Solution:**
```typescript
// pages/api/users.ts (not app/api/users.ts)
export default function handler(req, res) {
  res.status(200).json({ message: 'OK' })
}
```

---

### Environment Variables

#### `undefined` values or `Cannot read property 'X' of undefined`
**Cause:** Environment variable not set or named incorrectly
**Solution:**
1. **Check variable exists:**
```typescript
const apiKey = process.env.YOUR_API_KEY
if (!apiKey) {
  throw new Error('Missing YOUR_API_KEY environment variable')
}
```

2. **Verify in Vercel:**
- Go to Project → Settings → Environment Variables
- Check variable name matches exactly (case-sensitive)
- Ensure it's added to correct environment (Production/Preview/Development)
- Redeploy after adding variables

3. **Client vs Server:**
```typescript
// ✅ Client-side (prefixed with NEXT_PUBLIC_)
const clientVar = process.env.NEXT_PUBLIC_API_URL

// ❌ Server-side only (no prefix)
const serverVar = process.env.SECRET_KEY
```

---

### Database Connection Issues

#### `Invalid API key` or `401 Unauthorized`
**Cause:** Incorrect Supabase credentials or expired key
**Solution:**
```typescript
// Verify credentials
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

console.log('URL:', supabaseUrl?.substring(0, 20) + '...')
console.log('Key:', supabaseKey?.substring(0, 20) + '...')
```

**Check:**
- URL format: `https://xxx.supabase.co`
- Key starts with `eyJ`
- Variable names match exactly
- Variable added to Vercel

#### `Row Level Security policy violation`
**Cause:** RLS policies blocking access
**Solution:**
```sql
-- Check existing policies
SELECT * FROM pg_policies WHERE tablename = 'your_table';

-- Add read policy (temporary)
CREATE POLICY "Enable read for all users" ON your_table
  FOR SELECT USING (true);

-- Or add authenticated policy
CREATE POLICY "Enable read for authenticated users" ON your_table
  FOR SELECT USING (auth.role() = 'authenticated');
```

#### `Connection timeout`
**Cause:** Database connection issue or network problem
**Solution:**
- Check database is active
- Verify Supabase project status
- Test connection locally
- Check RLS policies

---

### Custom Domain Issues

#### Domain not resolving
**Cause:** DNS not configured or propagation not complete
**Solution:**
```bash
# Check DNS
nslookup your-domain.com
dig your-domain.com

# Should return Vercel's IP: 76.76.21.21
```

**DNS Configuration:**
```
Root domain (example.com):
  Type: A
  Name: @
  Value: 76.76.21.21

WWW subdomain (www.example.com):
  Type: CNAME
  Name: www
  Value: cname.vercel-dns.com
```

**Wait:** DNS changes can take 24-48 hours (usually 1-2 hours)

#### `SSL certificate error`
**Cause:** Domain not verified or SSL still provisioning
**Solution:**
1. **Check domain status in Vercel:**
   - Go to Project → Settings → Domains
   - Should show "Ready" with green checkmark

2. **Wait for SSL issuance:**
   - Automatic via Let's Encrypt
   - Usually completes within 1 hour

3. **Force HTTPS:**
   - Add to `vercel.json`:
   ```json
   {
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/$1",
         "status": 301,
         "headers": { "Location": "https://$1" }
       }
     ]
   }
   ```

---

### CORS Errors

#### `Access to fetch blocked by CORS policy`
**Cause:** Missing CORS headers
**Solution:**
```typescript
export default function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }
  
  // Your code here
}
```

---

### Performance Issues

#### Slow page loads
**Solution:**
1. **Enable image optimization:**
```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['your-domain.com'],
    formats: ['image/webp', 'image/avif'],
  },
}
```

2. **Implement code splitting:**
```typescript
const DynamicComponent = dynamic(() => import('../components/Heavy'))
```

3. **Check bundle size:**
```bash
npm install --save-dev @next/bundle-analyzer
# Run analyze script
```

4. **Enable compression:**
- Vercel enables Gzip/Brotli by default
- Verify: `curl -H "Accept-Encoding: gzip" -I https://your-domain.com`

---

## 🔍 Debugging Commands

### Check Environment
```bash
# List all environment variables (local)
vercel env ls

# Pull env vars locally
vercel env pull .env.local

# Check current deployment
vercel inspect <deployment-url>
```

### Test Locally
```bash
# Run development server
vercel dev

# Build and test production
vercel build
vercel start

# Test specific deployment
vercel inspect <deployment-url>
```

### Monitor Logs
```bash
# Real-time logs
vercel logs --follow <deployment-url>

# Function logs only
vercel logs --function=api/hello <deployment-url>
```

---

## 📞 Get Help

1. **Vercel Documentation:**
   - [docs.vercel.com](https://docs.vercel.com)
   - [vercel.com/support](https://vercel.com/support)

2. **Community:**
   - [GitHub Discussions](https://github.com/vercel/vercel/discussions)
   - Stack Overflow: tag `vercel`

3. **Vercel Support:**
   - Available for Pro/Enterprise plans
   - Dashboard chat (bottom-right)

4. **Common Solutions:**
   - Check build logs first
   - Test locally with `vercel dev`
   - Verify environment variables
   - Clear browser cache
   - Try incognito mode

---

## 📋 Pre-Flight Checklist Before Asking for Help

- [ ] Checked deployment logs for errors
- [ ] Tested locally with `vercel dev`
- [ ] Verified environment variables
- [ ] Confirmed all dependencies are installed
- [ ] Checked GitHub repository has latest code
- [ ] Reviewed this troubleshooting guide
- [ ] Searched existing issues on GitHub

---

**Remember:** Most issues are related to:
1. Missing environment variables (30%)
2. Build configuration errors (25%)
3. Incorrect API route structure (20%)
4. Database connection issues (15%)
5. DNS/custom domain problems (10%)

---
*Quick troubleshooting reference for Vercel deployment*