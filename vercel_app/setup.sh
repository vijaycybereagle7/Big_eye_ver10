#!/bin/bash
# Setup script for Vercel Cybersecurity API

echo "🚀 Setting up Vercel Cybersecurity Validation API"
echo "================================================"

# Check if required tools are installed
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration before deploying"
else
    echo "✅ .env file already exists"
fi

# Test local setup
echo "🧪 Testing local setup..."
python3 -c "
import sys
sys.path.append('app')
from config.settings import settings
print('✅ Configuration loaded successfully')
print(f'  - App Name: {settings.APP_NAME}')
print(f'  - Version: {settings.APP_VERSION}')
print(f'  - Debug Mode: {settings.DEBUG}')
print(f'  - Supabase Configured: {bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)}')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your Supabase credentials"
echo "2. Create Supabase tables (see README.md)"
echo "3. Configure API keys in app/config/settings.py"
echo "4. Deploy to Vercel: vercel"
echo ""
echo "For local testing:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "For deployment:"
echo "  vercel"
echo ""
