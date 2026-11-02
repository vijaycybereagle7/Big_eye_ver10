#!/bin/bash

# Big Eye Platform + Big Eye Security Database Deployment Script
# This script deploys the integrated platform with database capabilities

echo "🚀 Starting Big Eye Platform + Big Eye Security Database Deployment"
echo "=================================================================="

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "   npm install -g supabase"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -d "supabase" ]; then
    echo "❌ Please run this script from the big-eye-platform root directory"
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

echo "🔧 Building the application..."
npm run build

echo "🗄️ Deploying Supabase Edge Functions..."
supabase functions deploy database-email-validation
supabase functions deploy database-threat-intelligence  
supabase functions deploy database-comprehensive-analysis

echo "🗃️ Applying database migrations..."
supabase db reset

echo "🌐 Deploying to Vercel..."
if command -v vercel &> /dev/null; then
    vercel --prod
else
    echo "⚠️ Vercel CLI not found. Please install it:"
    echo "   npm install -g vercel"
    echo "   Then run: vercel --prod"
fi

echo ""
echo "✅ Deployment Complete!"
echo "=================================================================="
echo ""
echo "🔗 Your Big Eye Platform now includes:"
echo "   • All 10 existing analysis tools (unchanged)"
echo "   • NEW: Database Analysis with 3 powerful modes"
echo "   • Email validation with comprehensive checks"
echo "   • Threat intelligence querying"
echo "   • Bulk analysis capabilities"
echo ""
echo "📊 Total Tools Available: 12"
echo "   1. All in One Analysis"
echo "   2. Email Header Analyzer"  
echo "   3. Domain Checker"
echo "   4. Email Legitimacy Checker"
echo "   5. Blacklist Scanner"
echo "   6. IP Intelligence"
echo "   7. AI Phishing Detection"
echo "   8. Temp Email Detector"
echo "   9. Domain Age Tracker"
echo "   10. Link Checker"
echo "   11. Database Analysis ⭐ NEW"
echo "   12. Admin Dashboard"
echo ""
echo "🎯 Access the Database Analysis tab to use the new features!"
echo ""
echo "📖 For detailed information, see: BIG_EYE_DATABASE_INTEGRATION_SUMMARY.md"