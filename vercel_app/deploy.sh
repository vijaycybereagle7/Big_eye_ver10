#!/bin/bash
# Vercel Deployment Script for Cybersecurity API

set -e  # Exit on any error

echo "🚀 Vercel Deployment Script for Cybersecurity API"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if required tools are installed
echo "🔍 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

if ! command -v pip &> /dev/null; then
    print_error "pip is required but not installed."
    exit 1
fi

if ! command -v vercel &> /dev/null; then
    print_warning "Vercel CLI not found. Installing..."
    npm install -g vercel
fi

print_status "Prerequisites check passed"

# Check environment variables
echo ""
echo "🔧 Checking environment configuration..."

if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    cp .env.example .env
    print_warning "Please update .env file with your configuration before continuing"
    print_warning "Required variables: SUPABASE_URL, SUPABASE_ANON_KEY, SECRET_KEY"
    echo ""
    read -p "Press Enter when you have updated the .env file..."
fi

# Validate environment variables
if ! grep -q "SUPABASE_URL=" .env || grep -q "your-project.supabase.co" .env; then
    print_error "SUPABASE_URL not configured properly in .env file"
    exit 1
fi

if ! grep -q "SUPABASE_ANON_KEY=" .env || grep -q "your-supabase-anon-key" .env; then
    print_error "SUPABASE_ANON_KEY not configured properly in .env file"
    exit 1
fi

if ! grep -q "SECRET_KEY=" .env || grep -q "your-secret-key" .env; then
    print_error "SECRET_KEY not configured properly in .env file"
    exit 1
fi

print_status "Environment configuration validated"

# Test local setup
echo ""
echo "🧪 Testing local setup..."
python3 -c "
import sys
sys.path.append('app')
try:
    from config.settings import settings
    print('✅ Configuration loaded successfully')
    print(f'  - App Name: {settings.APP_NAME}')
    print(f'  - Version: {settings.APP_VERSION}')
    print(f'  - Debug Mode: {settings.DEBUG}')
    print(f'  - Supabase Configured: {bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)}')
    
    # Test Supabase connection
    from database.supabase import get_supabase_client
    client = get_supabase_client()
    print('✅ Supabase client initialized')
except Exception as e:
    print(f'❌ Setup test failed: {e}')
    sys.exit(1)
"

# Run local tests
echo ""
echo "🧪 Running local tests..."
python3 test_api.py

# Install dependencies
echo ""
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Test import
echo ""
echo "🔍 Testing imports..."
python3 -c "
import app.main
import app.services.validation
import app.services.reputation
import app.database.supabase
print('✅ All imports successful')
"

print_status "Local setup verification completed"

# Deploy to Vercel
echo ""
echo "🌐 Deploying to Vercel..."
echo ""

# Check if vercel project exists
if [ -f .vercel/project.json ]; then
    print_status "Existing Vercel project detected"
    read -p "Do you want to redeploy? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 0
    fi
fi

# Deploy
vercel --prod

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls --prod 2>/dev/null | grep "Ready" | head -1 | awk '{print $2}' || echo "")

if [ ! -z "$DEPLOYMENT_URL" ]; then
    print_status "Deployment successful!"
    echo ""
    echo "🌍 Your API is now live at:"
    echo "   https://$DEPLOYMENT_URL"
    echo ""
    echo "📚 API Documentation:"
    echo "   https://$DEPLOYMENT_URL/docs"
    echo ""
    echo "❤️  Health Check:"
    echo "   https://$DEPLOYMENT_URL/health"
    echo ""
    
    # Test deployed API
    echo "🧪 Testing deployed API..."
    
    if curl -f -s "https://$DEPLOYMENT_URL/health" > /dev/null; then
        print_status "Deployed API is responding correctly"
    else
        print_warning "Deployed API health check failed"
    fi
    
    # Provide post-deployment instructions
    echo ""
    echo "🎯 Post-Deployment Checklist:"
    echo "   ☑️  Update API keys in production environment"
    echo "   ☑️  Test all endpoints with your API keys"
    echo "   ☑️  Set up monitoring and alerts"
    echo "   ☑️  Configure custom domain (optional)"
    echo "   ☑️  Review Supabase logs for any issues"
    echo ""
    echo "📖 Next Steps:"
    echo "   1. Test the API with your production API keys"
    echo "   2. Monitor usage in Supabase dashboard"
    echo "   3. Set up automated backups if needed"
    echo "   4. Review and adjust rate limits"
    echo ""
    
else
    print_error "Deployment failed or URL not detected"
    echo "Please check the deployment output above for errors"
    exit 1
fi

print_status "Deployment completed successfully! 🎉"
