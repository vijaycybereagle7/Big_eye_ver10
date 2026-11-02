# Quick Setup Checklist

## Pre-Deployment Setup
- [ ] Create Vercel account (GitHub login recommended)
- [ ] Prepare GitHub repository with code
- [ ] Prepare environment variables list
- [ ] Create Supabase account (if using database)
- [ ] Prepare custom domain (optional)

## Deployment Steps
- [ ] Connect GitHub repository to Vercel
- [ ] Configure project settings (framework, build command)
- [ ] Add environment variables
- [ ] Click "Deploy"
- [ ] Verify deployment successful

## Post-Deployment
- [ ] Test homepage loads
- [ ] Test API endpoints
- [ ] Test database connections
- [ ] Configure custom domain (if applicable)
- [ ] Set up monitoring/analytics

## Environment Variables Checklist
**Required:**
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY
- [ ] SUPABASE_SERVICE_ROLE_KEY (for admin operations)
- [ ] NEXT_PUBLIC_SITE_URL (for production)

**Optional:**
- [ ] NEXTAUTH_SECRET
- [ ] NEXTAUTH_URL
- [ ] API keys for external services
- [ ] Other configuration variables

## Custom Domain Checklist
- [ ] Purchase domain from registrar
- [ ] Add domain in Vercel project settings
- [ ] Configure DNS records (A and CNAME)
- [ ] Wait for DNS propagation (1-48 hours)
- [ ] Verify SSL certificate issued
- [ ] Test domain accessibility
- [ ] Update any hardcoded URLs in code

## Testing Checklist
- [ ] All pages load without errors
- [ ] API endpoints return correct data
- [ ] Database CRUD operations work
- [ ] Authentication flows function
- [ ] Form submissions succeed
- [ ] Images load properly
- [ ] Mobile responsiveness verified
- [ ] Performance is acceptable

## Common Issues Quick Fixes
| Issue | Quick Fix |
|-------|-----------|
| Build fails | Check `package.json` dependencies |
| API 404 errors | Verify file structure (`pages/api/`) |
| Env vars not working | Check variable names, redeploy |
| Database connection fails | Verify Supabase credentials |
| Custom domain not working | Wait 24-48hrs for DNS propagation |
| CORS errors | Add CORS headers to API routes |

---
*Quick reference card for Vercel deployment*