# Example Configuration Files

## 1. vercel.json

```json
{
  "version": 2,
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "devCommand": "npm run dev",
  "functions": {
    "pages/api/**/*.ts": {
      "runtime": "nodejs18.x",
      "memory": 1024,
      "maxDuration": 10
    },
    "app/api/**/*.ts": {
      "runtime": "nodejs18.x"
    }
  },
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ],
  "rewrites": [
    {
      "source": "/sitemap.xml",
      "destination": "/api/sitemap"
    }
  ]
}
```

## 2. next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // Environment variables
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },
  
  // Image optimization
  images: {
    domains: [
      'your-domain.com',
      'supabase.co',
      'example.com'
    ],
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 60,
  },
  
  // Redirects
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ]
  },
  
  // Rewrites
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: '/api/:path*',
      },
    ]
  },
  
  // Headers
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ]
  },
  
  // webpack configuration
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Add custom webpack configuration
    return config
  },
  
  // Experimental features
  experimental: {
    appDir: true, // Enable App Router
  },
}

module.exports = nextConfig
```

## 3. Environment Variables Template

```env
# ===========================================
# VERCEL DEPLOYMENT ENVIRONMENT VARIABLES
# ===========================================

# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Site Configuration
NEXT_PUBLIC_SITE_URL=https://your-domain.com
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your_random_secret_string

# External APIs
NEXT_PUBLIC_API_URL=https://api.example.com
API_KEY=your_api_key_here

# Authentication Providers (if using NextAuth)
GITHUB_ID=your_github_oauth_client_id
GITHUB_SECRET=your_github_oauth_client_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Payment Processing
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Service
SENDGRID_API_KEY=SG...
RESEND_API_KEY=re_...

# Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=phc_...

# Database (if not using Supabase)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Application Settings
NODE_ENV=production
LOG_LEVEL=info

# ===========================================
# DEVELOPMENT ENVIRONMENT VARIABLES
# ===========================================
# Copy to .env.local for local development
```

## 4. API Route Example with Error Handling

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
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  // Handle preflight request
  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  try {
    if (req.method === 'GET') {
      // Fetch users
      const { data, error } = await supabase
        .from('users')
        .select('id, email, name, avatar_url, created_at')
        .order('created_at', { ascending: false })

      if (error) {
        console.error('Database error:', error)
        return res.status(500).json({ error: 'Database error occurred' })
      }

      return res.status(200).json({ users: data })
    }

    if (req.method === 'POST') {
      // Create user
      const { email, name } = req.body

      if (!email || !name) {
        return res.status(400).json({ error: 'Email and name are required' })
      }

      const { data, error } = await supabase
        .from('users')
        .insert([{ email, name }])
        .select()
        .single()

      if (error) {
        console.error('Insert error:', error)
        return res.status(500).json({ error: 'Failed to create user' })
      }

      return res.status(201).json({ user: data })
    }

    // Method not allowed
    res.setHeader('Allow', ['GET', 'POST'])
    return res.status(405).json({ error: `Method ${req.method} Not Allowed` })

  } catch (error) {
    console.error('Server error:', error)
    return res.status(500).json({ error: 'Internal server error' })
  }
}
```

## 5. Supabase Client Setup

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import { Database } from './database.types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// Server-side client with service role (admin operations)
export const supabaseAdmin = createClient<Database>(
  supabaseUrl,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  {
    auth: {
      autoRefreshToken: false,
      persistSession: false
    }
  }
)
```

## 6. Custom Domain DNS Configuration

### For Cloudflare DNS:

```
Type    Name    Content              Proxy status
A       @       76.76.21.21         Proxied (orange cloud)
CNAME   www     cname.vercel-dns.com Proxied (orange cloud)
```

### For Namecheap DNS:

```
Type    Host    Value                 TTL
A       @       76.76.21.21           Automatic
CNAME   www     cname.vercel-dns.com  Automatic
```

### For GoDaddy DNS:

```
Type    Name    Value                 TTL
A       @       76.76.21.21           1 Hour
CNAME   www     cname.vercel-dns.com  1 Hour
```

## 7. package.json Scripts

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "analyze": "cross-env ANALYZE=true next build",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:ci": "jest --ci"
  },
  "devDependencies": {
    "@next/bundle-analyzer": "^13.0.0",
    "@types/jest": "^29.0.0",
    "cross-env": "^7.0.0",
    "jest": "^29.0.0",
    "typescript": "^5.0.0"
  }
}
```

## 8. Test Script Example

```bash
#!/bin/bash
# test-deployment.sh

set -e

BASE_URL="${DEPLOYMENT_URL:-https://your-app.vercel.app}"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Testing deployment at: $BASE_URL"
echo "================================"

# Test 1: Homepage
echo "1. Testing homepage..."
status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL")
if [ "$status" = "200" ]; then
  echo -e "${GREEN}✓ Homepage OK${NC}"
else
  echo -e "${RED}✗ Homepage failed (HTTP $status)${NC}"
  exit 1
fi

# Test 2: API endpoint
echo "2. Testing API endpoint..."
response=$(curl -s "$BASE_URL/api/health")
if [[ "$response" == *"ok"* ]]; then
  echo -e "${GREEN}✓ API endpoint OK${NC}"
else
  echo -e "${RED}✗ API endpoint failed${NC}"
  exit 1
fi

# Test 3: Environment variables
echo "3. Testing environment variables..."
env_check=$(curl -s "$BASE_URL/api/env-check")
if [[ "$env_check" == *"success"* ]]; then
  echo -e "${GREEN}✓ Environment variables OK${NC}"
else
  echo -e "${RED}✗ Environment variables issue${NC}"
  exit 1
fi

echo "================================"
echo -e "${GREEN}All tests passed!${NC}"
```

## 9. Troubleshooting Commands

```bash
# Check Vercel CLI version
vercel --version

# Login to Vercel CLI
vercel login

# Link project locally
vercel link

# Pull environment variables
vercel env pull .env.local

# Deploy without Git integration
vercel --prod

# View deployment logs
vercel logs <deployment-url>

# Inspect deployment
vercel inspect <deployment-url>

# Check build logs locally
vercel build

# Test production build locally
vercel dev

# Check DNS resolution
nslookup your-domain.com
dig your-domain.com

# Test SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

---
*Example configuration files for Vercel deployment*