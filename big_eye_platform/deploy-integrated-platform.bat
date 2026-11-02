@echo off
:: Big Eye Platform + Big Eye Security Database Deployment Script for Windows
:: This script deploys the integrated platform with database capabilities

echo 🚀 Starting Big Eye Platform + Big Eye Security Database Deployment
echo ==================================================================

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js first
    exit /b 1
)

:: Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Please run this script from the big-eye-platform root directory
    exit /b 1
)

if not exist "supabase" (
    echo ❌ Supabase directory not found. Please run from the correct directory
    exit /b 1
)

echo 📦 Installing dependencies...
call npm install

echo 🔧 Building the application...
call npm run build

echo 🗄️ Deploying Supabase Edge Functions...
call supabase functions deploy database-email-validation
call supabase functions deploy database-threat-intelligence
call supabase functions deploy database-comprehensive-analysis

echo 🗃️ Applying database migrations...
call supabase db reset

echo 🌐 Deploying to Vercel...
where vercel >nul 2>&1
if %errorlevel% equ 0 (
    call vercel --prod
) else (
    echo ⚠️ Vercel CLI not found. Please install it:
    echo    npm install -g vercel
    echo    Then run: vercel --prod
)

echo.
echo ✅ Deployment Complete!
echo ==================================================================
echo.
echo 🔗 Your Big Eye Platform now includes:
echo    • All 10 existing analysis tools (unchanged)
echo    • NEW: Database Analysis with 3 powerful modes
echo    • Email validation with comprehensive checks
echo    • Threat intelligence querying
echo    • Bulk analysis capabilities
echo.
echo 📊 Total Tools Available: 12
echo    1. All in One Analysis
echo    2. Email Header Analyzer
echo    3. Domain Checker
echo    4. Email Legitimacy Checker
echo    5. Blacklist Scanner
echo    6. IP Intelligence
echo    7. AI Phishing Detection
echo    8. Temp Email Detector
echo    9. Domain Age Tracker
echo    10. Link Checker
echo    11. Database Analysis ⭐ NEW
echo    12. Admin Dashboard
echo.
echo 🎯 Access the Database Analysis tab to use the new features!
echo.
echo 📖 For detailed information, see: BIG_EYE_DATABASE_INTEGRATION_SUMMARY.md

pause