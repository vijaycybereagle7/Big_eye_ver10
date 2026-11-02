# Complete Vercel Deployment Guide

## Table of Contents
1. [Account Setup](#1-account-setup)
2. [Connecting GitHub Repository](#2-connecting-github-repository)
3. [Environment Variables Configuration](#3-environment-variables-configuration)
4. [Supabase Database Setup](#4-supabase-database-setup)
5. [Deploying API Endpoints](#5-deploying-api-endpoints)
6. [Testing Deployment](#6-testing-deployment)
7. [Custom Domain Setup](#7-custom-domain-setup)
8. [Troubleshooting Common Issues](#8-troubleshooting-common-issues)

---

## 1. Account Setup

### Step 1: Create a Vercel Account

1. **Visit Vercel Homepage**
   - Go to [https://vercel.com](https://vercel.com)
   - Click the "Sign Up" button in the top-right corner

2. **Choose Authentication Method**
   - **Option A: GitHub (Recommended)**
     - Click "Continue with GitHub"
     - This enables seamless integration with your repositories
   
   - **Option B: Email**
     - Enter your email address
     - Create a strong password
     - Verify your email

### Step 2: Account Verification

1. **Verify GitHub Account (if applicable)**
   - You'll be redirected to GitHub
   - Authorize Vercel to access your repositories
   - Grant necessary permissions

2. **Complete Profile Setup**
   - Add your name and organization (optional)
   - Choose your use case (Personal, Company, Student, etc.)

### Step 3: Understanding Your Dashboard

**Screenshot Description:** The Vercel dashboard displays:
- Left sidebar: Navigation menu with Projects, Deployments, Analytics, etc.
- Main area: Empty state with "Create Project" button
- Top bar: Search functionality and account menu
- Project cards area: Shows your deployed projects

**Key Areas to Know:**
- **Projects**: All your deployed applications
- **Deployments**: Individual deployment instances
- **Analytics**: Performance metrics
- **Settings**: Project and account configuration

---

## 2. Connecting GitHub Repository

### Step 1: Import Project from GitHub

1. **Click "Add New" Button**
   - Located in the top-right corner
   - Select "Project" from the dropdown

2. **GitHub Integration**
   - Vercel will scan your GitHub repositories
   - You'll see a list of your public and private repositories

### Step 2: Select Your Repository

1. **Repository List**
   - **Screenshot Description:** Shows a list of repositories with:
     - Repository name
     - Language indicator
     - Last updated timestamp
     - Private/Public badge

2. **Choose the Right Repository**
   - Select the repository containing your web application
   - Look for `package.json` or `vercel.json` for easy detection

3. **Search and Filter**
   - Use the search bar to find specific repositories
   - Filter by language using the dropdown

### Step 3: Configure Project Settings

1. **Project Name**
   - Auto-filled from repository name
   - Can be customized (e.g., "my-awesome-app")
   - This will be part of your deployment URL

2. **Framework Preset**
   - **Auto-detected** (Vercel detects: Next.js, React, Vue, Nuxt, etc.)
   - Manual selection if auto-detection fails
   - Options: Next.js, React, Vue, Angular, Svelte, Gatsby, Node.js, etc.

3. **Root Directory** (if applicable)
   - Leave blank if project is in root
   - Specify subdirectory if app is in `/app` or `/frontend`

4. **Build Command** (auto-filled, but customizable)
   - Next.js: `npm run build` or `yarn build`
   - React: `npm run build`
   - Custom: Your specific build command

5. **Output Directory** (auto-filled, but customizable)
   - Next.js: `.next`
   - React: `build`
   - CRA: `build`
   - Custom: Your build output directory

6. **Install Command** (auto-filled, but customizable)
   - `npm install`
   - `yarn install`
   - `pnpm install`

### Step 4: Deploy

1. **Click "Deploy" Button**
   - Vercel will start the deployment process
   - You'll see real-time logs of the build process

2. **Initial Build Process**
   - **Screenshot Description:** Shows a deployment log with:
     - Cloning repository
     - Installing dependencies
     - Building application
     - Uploading files
     - Ready status

3. **Successful Deployment**
   - After 1-3 minutes, you'll see "Ready" status
   - A default domain like `https://your-project-name.vercel.app` is created

---

## 3. Environment Variables Configuration

### Step 1: Access Environment Variables Settings

1. **Go to Project Dashboard**
   - Click on your project from the main dashboard
   - Navigate to "Settings" tab

2. **Navigate to Environment Variables**
   - In the left sidebar, click "Environment Variables"
   - You'll see a list of existing variables (if any)

### Step 2: Add Environment Variables

1. **Click "Add New" Button**
   - Located at the top of the environment variables section

2. **Configure Variable**
   
   **Field: Name**
   - Enter the variable name (e.g., `API_KEY`, `DATABASE_URL`)
   - Must match the variable name in your code
   
   **Field: Value**
   - Enter the actual value
   - For sensitive data, ensure it's encrypted
   - Example: `https://your-api.com/v1/data`
   
   **Field: Environment**
   - Select where this variable should be available:
     - ✅ Production
     - ✅ Preview
     - ✅ Development

3. **Click "Save"**
   - Variable is encrypted and stored securely

### Step 3: Common Environment Variables Examples

**API Configuration:**
```env
API_BASE_URL=https://api.example.com
API_KEY=your_secret_api_key
NODE_ENV=production
```

**Database Configuration:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
```

**Third-Party Services:**
```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
SENDGRID_API_KEY=SG....
```

**Authentication:**
```env
JWT_SECRET=your_jwt_secret
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=https://your-domain.com
```

### Step 4: Environment Variable Management

1. **Import/Export Variables**
   - Use "Import" to bulk add variables
   - Use "Export" to download all variables (excluding values)

2. **Variable Encryption**
   - All sensitive values are encrypted at rest
   - Only accessible to authorized team members

3. **Preview Variables**
   - Add variables specifically for preview deployments
   - Different from production variables

---

## 4. Supabase Database Setup

### Step 1: Create Supabase Project

1. **Sign Up for Supabase**
   - Go to [https://supabase.com](https://supabase.com)
   - Click "Start your project"
   - Sign up with GitHub or email

2. **Create New Project**
   - Click "New Project"
   - Choose your organization
   - Enter project details:
     - **Name**: Your app name
     - **Database Password**: Strong password (save it!)
     - **Region**: Choose closest to your users

3. **Wait for Setup**
   - Project creation takes 1-2 minutes
   - You'll get a confirmation email

### Step 2: Get Supabase Credentials

1. **Access Project Settings**
   - Go to Project Settings → API
   - **Screenshot Description:** Shows:
     - Project URL
     - Anon/Public key
     - Service Role key (secret)

2. **Copy Important Values**
   - **Project URL**: `https://your-project-id.supabase.co`
   - **Anon/Public Key**: `eyJ...` (safe for client-side)
   - **Service Role Key**: `eyJ...` (keep secret, server-side only)

### Step 3: Configure Supabase Client

1. **Create Supabase Client File**

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

2. **Set Environment Variables in Vercel**

Add these to your Vercel environment variables:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Step 4: Database Schema Setup

1. **Access SQL Editor**
   - In Supabase dashboard, go to "SQL Editor"
   - Create new query

2. **Run Initial Schema**

```sql
-- Example: Users table
CREATE TABLE users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Public profiles are viewable by everyone" ON users
  FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile" ON users
  FOR INSERT WITH CHECK (auth.uid() = id);
```

### Step 5: Enable Authentication

1. **Go to Authentication Settings**
   - Navigate to Authentication → Settings

2. **Configure Providers**
   - **Email**: Enable email/password auth
   - **Social Providers**: Enable GitHub, Google, etc.
   - Set redirect URLs for production

3. **Set Auth Variables in Vercel**
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

---

## 5. Deploying API Endpoints

### Step 1: Create API Endpoints (Next.js Example)

1. **Create API Route Directory**
   - In your project, create `pages/api/` (or `app/api/` for App Router)

2. **Simple API Endpoint**

```typescript
// pages/api/hello.ts (Pages Router)
import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  res.status(200).json({ message: 'Hello from Vercel!' })
}
```

3. **API with Database Integration**

```typescript
// pages/api/users.ts
import type { NextApiRequest, NextApiResponse } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'GET') {
    const { data, error } = await supabase
      .from('users')
      .select('*')
    
    if (error) {
      return res.status(500).json({ error: error.message })
    }
    
    return res.status(200).json({ users: data })
  }
  
  if (req.method === 'POST') {
    const { email, name } = req.body
    
    const { data, error } = await supabase
      .from('users')
      .insert([{ email, name }])
      .select()
    
    if (error) {
      return res.status(500).json({ error: error.message })
    }
    
    return res.status(201).json({ user: data[0] })
  }
  
  res.setHeader('Allow', ['GET', 'POST'])
  res.status(405).end(`Method ${req.method} Not Allowed`)
}
```

### Step 2: Configure API Route Settings

1. **Create vercel.json** (if needed)

```json
{
  "functions": {
    "pages/api/**/*.ts": {
      "runtime": "nodejs18.x"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    }
  ]
}
```

### Step 3: Deploy API Endpoints

1. **Push Changes to GitHub**
   ```bash
   git add .
   git commit -m "Add API endpoints"
   git push origin main
   ```

2. **Automatic Deployment**
   - Vercel detects the change
   - Deploys automatically
   - Builds API routes

3. **Manual Redeploy** (if needed)
   - Go to "Deployments" tab
   - Click "Redeploy" on latest deployment

### Step 4: Serverless Functions (Alternative)

1. **Create Function in api Directory**

```typescript
// api/hello.ts
export default async function handler(req: Request) {
  return new Response(
    JSON.stringify({ message: 'Hello from Serverless Function!' }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  )
}
```

---

## 6. Testing Deployment

### Step 1: Test via Vercel URL

1. **Get Your Deployment URL**
   - Format: `https://your-project-name.vercel.app`
   - Or custom domain if configured

2. **Test Basic Routes**

```bash
# Test homepage
curl https://your-project-name.vercel.app/

# Test API endpoint
curl https://your-project-name.vercel.app/api/hello
```

### Step 2: API Testing with curl Examples

**Example 1: GET Request**
```bash
curl -X GET \
  https://your-project-name.vercel.app/api/users \
  -H 'Content-Type: application/json'
```

**Expected Response:**
```json
{
  "users": [
    {
      "id": "uuid-here",
      "email": "user@example.com",
      "name": "John Doe"
    }
  ]
}
```

**Example 2: POST Request**
```bash
curl -X POST \
  https://your-project-name.vercel.app/api/users \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "newuser@example.com",
    "name": "Jane Smith"
  }'
```

**Expected Response:**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "newuser@example.com",
    "name": "Jane Smith",
    "created_at": "2025-10-30T10:11:24.000Z"
  }
}
```

**Example 3: Error Handling**
```bash
curl -X POST \
  https://your-project-name.vercel.app/api/users \
  -H 'Content-Type: application/json' \
  -d '{}'
```

**Expected Response:**
```json
{
  "error": "Missing required fields: email, name"
}
```

### Step 3: Environment-Specific Testing

1. **Production URL**
   - `https://your-project-name.vercel.app`
   - Uses production environment variables

2. **Preview Deployment**
   - Get URL from Deployments tab
   - Example: `https://your-project-git-branch.vercel.app`
   - Uses preview environment variables

3. **Testing with Authentication**

```bash
# Test with API key
curl -X GET \
  https://your-project-name.vercel.app/api/protected \
  -H 'Authorization: Bearer your-api-key'
```

### Step 4: Automated Testing

1. **Create Test Script**

```bash
#!/bin/bash
# test-deployment.sh

BASE_URL="https://your-project-name.vercel.app"

echo "Testing homepage..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL)
if [ $response -eq 200 ]; then
  echo "✅ Homepage OK"
else
  echo "❌ Homepage Failed: $response"
fi

echo "Testing API..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/hello)
if [ $response -eq 200 ]; then
  echo "✅ API OK"
else
  echo "❌ API Failed: $response"
fi

echo "Testing database..."
response=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/users)
if [ $response -eq 200 ]; then
  echo "✅ Database connection OK"
else
  echo "❌ Database connection Failed: $response"
fi
```

2. **Run Test**
```bash
chmod +x test-deployment.sh
./test-deployment.sh
```

### Step 5: Performance Testing

1. **Response Time Test**
```bash
curl -w "@curl-format.txt" -o /dev/null -s $BASE_URL/api/hello
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

---

## 7. Custom Domain Setup

### Step 1: Purchase Domain (if needed)

1. **Domain Registrars**
   - Namecheap
   - GoDaddy
   - Google Domains
   - Cloudflare
   - Or purchase directly through Vercel

2. **Recommended: Use Cloudflare**
   - Better performance and security
   - Free SSL certificates
   - Easy DNS management

### Step 2: Add Domain in Vercel

1. **Access Project Settings**
   - Go to your project dashboard
   - Click "Settings" tab

2. **Navigate to Domains**
   - In left sidebar, click "Domains"

3. **Add Domain**
   - Click "Add Domain"
   - Enter your domain: `example.com`
   - Click "Add"

4. **Domain Verification**
   - **Screenshot Description:** Shows domain status:
     - Domain added
     - Verification status
     - SSL certificate status

### Step 3: Configure DNS Records

**Option A: Using Vercel DNS (Recommended)**

1. **Use Vercel DNS**
   - Select "Use Vercel DNS" option
   - Vercel provides nameservers
   - Update your domain registrar to use these nameservers

2. **Required DNS Records**
   ```
   Type    Name    Value
   A       @       76.76.21.21
   CNAME   www     cname.vercel-dns.com
   ```

**Option B: External DNS Provider**

1. **Add CNAME Record**
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

2. **Add A Record (for root domain)**
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   ```

### Step 4: SSL Certificate Setup

1. **Automatic SSL**
   - Vercel provides free SSL certificates
   - Automatically issued via Let's Encrypt
   - No manual configuration needed

2. **SSL Verification**
   - **Screenshot Description:** Shows SSL status:
     - ✅ Ready status
     - Certificate details
     - Expiration date

3. **Force HTTPS**
   - Enabled by default
   - Redirects HTTP to HTTPS automatically

### Step 5: Domain Configuration

1. **Domain Redirects**
   - Configure www to non-www (or vice versa)
   - Set up redirect rules in Vercel dashboard

2. **Environment Variables Update**
   ```env
   # Update these with your custom domain
   NEXT_PUBLIC_SITE_URL=https://example.com
   NEXTAUTH_URL=https://example.com
   ```

3. **Update Code References**
   ```typescript
   // Update any hardcoded URLs
   const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://example.com'
   ```

### Step 6: Testing Custom Domain

1. **Verify DNS Propagation**
   ```bash
   # Check DNS resolution
   nslookup example.com
   dig example.com

   # Test SSL certificate
   openssl s_client -connect example.com:443 -servername example.com
   ```

2. **Test Website**
   ```bash
   curl -I https://example.com
   curl -I http://example.com  # Should redirect to HTTPS
   ```

3. **Cross-Browser Testing**
   - Test in Chrome, Firefox, Safari
   - Check mobile browsers
   - Verify SSL certificate is valid

---

## 8. Troubleshooting Common Issues

### Issue 1: Build Failures

**Symptoms:**
- Build process fails during deployment
- Error logs show compilation issues

**Common Causes & Solutions:**

1. **Dependency Issues**
   ```
   Error: Cannot find module 'some-package'
   ```
   
   **Solution:**
   ```bash
   # Update package.json with correct version
   npm install some-package@latest
   
   # Clear npm cache
   npm cache clean --force
   
   # Delete node_modules and reinstall
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Build Command Errors**
   ```
   Error: Build command failed
   ```
   
   **Solution:**
   - Check build command in Vercel settings
   - Verify build command works locally:
     ```bash
     npm run build
     ```
   - Update vercel.json:
     ```json
     {
       "buildCommand": "npm run build",
       "outputDirectory": "dist"
     }
     ```

3. **Memory Issues**
   ```
   JavaScript heap out of memory
   ```
   
   **Solution:**
   ```json
   {
     "functions": {
       "app/**/*.js": {
         "memory": 3008
       }
     }
   }
   ```

### Issue 2: Environment Variables Not Working

**Symptoms:**
- Environment variables are undefined
- API calls fail with authentication errors

**Solutions:**

1. **Check Variable Names**
   - Ensure exact match between code and Vercel
   - Case sensitivity matters
   ```typescript
   // ✅ Correct
   const apiKey = process.env.NEXT_PUBLIC_API_KEY
   
   // ❌ Wrong (extra spaces, different case)
   const apiKey = process.env['NEXT_PUBLIC_API_key']
   ```

2. **Verify Environment Selection**
   - Ensure variable is added to correct environment
   - Check Production, Preview, Development tabs

3. **Redeploy After Adding Variables**
   - Environment variables require redeployment
   - Go to Deployments → Click "Redeploy"

4. **Client-Side vs Server-Side**
   ```typescript
   // ✅ Client-side accessible (NEXT_PUBLIC_ prefix)
   const clientVar = process.env.NEXT_PUBLIC_API_URL
   
   // ❌ Server-side only (no NEXT_PUBLIC_ prefix)
   const serverVar = process.env.DATABASE_URL
   ```

### Issue 3: API Routes Return 404

**Symptoms:**
- `/api/*` endpoints return 404 Not Found
- Direct URL access fails

**Solutions:**

1. **File Structure Check**
   ```
   project/
   ├── pages/
   │   └── api/
   │       ├── hello.ts       ✅ Correct
   │       └── users/
   │           └── index.ts   ✅ Correct
   ├── api/
   │   └── hello.ts           ❌ Wrong (if using Pages Router)
   ```

2. **Route Handler Syntax**
   ```typescript
   // ✅ Correct (Pages Router)
   export default function handler(req, res) {
     res.status(200).json({ message: 'OK' })
   }
   
   // ❌ Wrong (missing export)
   function handler(req, res) {
     res.status(200).json({ message: 'OK' })
   }
   ```

3. **Check vercel.json Configuration**
   ```json
   {
     "rewrites": [
       {
         "source": "/api/(.*)",
         "destination": "/api/$1"
       }
     ]
   }
   ```

### Issue 4: Database Connection Errors

**Symptoms:**
- Supabase connection fails
- "Invalid API key" errors
- Connection timeout

**Solutions:**

1. **Verify Supabase Credentials**
   ```bash
   # Test connection locally
   curl -X GET \
     'https://your-project.supabase.co/rest/v1/users' \
     -H "apikey: YOUR_ANON_KEY" \
     -H "Authorization: Bearer YOUR_ANON_KEY"
   ```

2. **Check RLS Policies**
   ```sql
   -- Verify table has proper RLS policies
   SELECT * FROM pg_policies WHERE tablename = 'users';
   
   -- Add policy if missing
   CREATE POLICY "Enable read access for all users" ON users
     FOR SELECT USING (true);
   ```

3. **Environment Variables in Vercel**
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://xyz.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   ```

4. **Test Supabase Client**
   ```typescript
   import { createClient } from '@supabase/supabase-js'
   
   const supabase = createClient(
     process.env.NEXT_PUBLIC_SUPABASE_URL!,
     process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
   )
   
   // Test connection
   const { data, error } = await supabase.from('users').select('count')
   console.log({ data, error })
   ```

### Issue 5: Custom Domain Not Working

**Symptoms:**
- Domain doesn't resolve
- SSL certificate errors
- Redirect loops

**Solutions:**

1. **Check DNS Propagation**
   ```bash
   # Check if DNS is pointing to Vercel
   nslookup example.com
   
   # Should return Vercel's IP: 76.76.21.21
   ```

2. **Verify DNS Records**
   - Root domain (example.com): A record → 76.76.21.21
   - WWW subdomain (www.example.com): CNAME → cname.vercel-dns.com

3. **Wait for Propagation**
   - DNS changes can take 24-48 hours
   - Usually resolves within 1-2 hours

4. **Check Domain Status in Vercel**
   - Go to Project → Settings → Domains
   - Status should show ✅ Ready

### Issue 6: Slow Loading Times

**Symptoms:**
- Pages take long to load
- Poor Core Web Vitals scores

**Solutions:**

1. **Enable Image Optimization**
   ```typescript
   // next.config.js
   module.exports = {
     images: {
       domains: ['your-cdn-domain.com'],
       formats: ['image/webp', 'image/avif'],
     },
   }
   ```

2. **Implement Code Splitting**
   ```typescript
   // Use dynamic imports
   const DynamicComponent = dynamic(() => import('../components/HeavyComponent'))
   ```

3. **Optimize Bundle Size**
   ```bash
   # Analyze bundle
   npm install --save-dev @next/bundle-analyzer
   ```

4. **Enable Compression**
   - Vercel enables compression by default
   - Verify with: `curl -H "Accept-Encoding: gzip" -I https://your-domain.com`

### Issue 7: Deployment Stuck/Timeout

**Symptoms:**
- Deployment stays in "Building" state
- Timeout errors

**Solutions:**

1. **Check Build Logs**
   - Go to Deployments tab
   - Click on deployment
   - Review logs for errors

2. **Reduce Build Time**
   - Optimize build process
   - Use incremental builds
   - Cache dependencies

3. **Manual Redeploy**
   - Trigger fresh deployment
   - Go to Deployments → Click "Redeploy"

4. **Contact Support**
   - If issue persists
   - Use Vercel support chat

### Issue 8: CORS Errors

**Symptoms:**
- "Access to fetch blocked by CORS policy"
- API requests fail from frontend

**Solutions:**

1. **Configure CORS Headers**
   ```typescript
   export default function handler(req, res) {
     // Set CORS headers
     res.setHeader('Access-Control-Allow-Credentials', 'true')
     res.setHeader('Access-Control-Allow-Origin', 'https://your-frontend-domain.com')
     res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT')
     res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version')
   
     if (req.method === 'OPTIONS') {
       res.status(200).end()
       return
     }
   
     // Your API logic
   }
   ```

2. **Use Supabase Client for CORS**
   - Supabase handles CORS automatically
   - No additional configuration needed

### Getting Help

1. **Vercel Documentation**
   - [docs.vercel.com](https://docs.vercel.com)
   - Comprehensive guides and API reference

2. **Community Support**
   - [GitHub Discussions](https://github.com/vercel/vercel/discussions)
   - Stack Overflow with `vercel` tag

3. **Vercel Support**
   - Available for Pro/Enterprise plans
   - Access via dashboard chat

---

## Quick Reference Checklist

### Pre-Deployment
- [ ] GitHub repository connected
- [ ] Environment variables configured
- [ ] Database credentials set
- [ ] Build command verified
- [ ] Dependencies up to date

### Post-Deployment
- [ ] Homepage loads correctly
- [ ] API endpoints respond
- [ ] Database connections work
- [ ] Environment variables accessible
- [ ] SSL certificate valid

### Custom Domain
- [ ] DNS records configured
- [ ] Domain verified in Vercel
- [ ] SSL certificate issued
- [ ] Force HTTPS enabled
- [ ] Redirects configured

### Monitoring
- [ ] Set up Vercel Analytics
- [ ] Monitor Core Web Vitals
- [ ] Check error logs regularly
- [ ] Set up alerts for downtime

---

## Additional Resources

- **Vercel CLI**: `npm i -g vercel`
- **GitHub Integration**: Auto-deploy on push
- **Preview Deployments**: Test changes before production
- **Analytics**: Monitor performance and errors
- **Edge Functions**: Serverless functions at the edge

---

*Last Updated: October 30, 2025*