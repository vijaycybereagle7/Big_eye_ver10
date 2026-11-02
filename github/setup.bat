@echo off
REM Big Eye Security Database - Developer Setup Script (Windows)
REM This script sets up the development environment for the Big Eye Security Database

setlocal enabledelayedexpansion

REM Configuration
set "PYTHON_VERSION=3.9"
set "PROJECT_NAME=big-eye-security-database"
set "GIT_REPO_URL=https://github.com/your-org/big-eye-security-database.git"

echo ============================================
echo Big Eye Security Database - Setup
echo ============================================
echo.

REM Check system requirements
echo [INFO] Checking system requirements...
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git not found. Please install Git and add it to PATH.
    pause
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
    pause
    exit /b 1
)

where pip >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip not found. Please install pip.
    pause
    exit /b 1
)

where docker >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker not found. Some features may not work.
)

where docker-compose >nul 2>&1
if errorlevel 1 (
    echo [WARNING] docker-compose not found. Please install Docker Compose.
)

echo [SUCCESS] Basic system requirements satisfied
echo.

REM Setup project directory
echo [INFO] Setting up project directory...
if not exist "%PROJECT_NAME%" (
    echo [INFO] Cloning repository...
    git clone %GIT_REPO_URL% %PROJECT_NAME%
    cd %PROJECT_NAME%
) else (
    echo [WARNING] Project directory already exists. Updating repository...
    cd %PROJECT_NAME%
    git pull origin main
)

echo [SUCCESS] Project directory ready
echo.

REM Setup Python virtual environment
echo [INFO] Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [SUCCESS] Virtual environment activated and pip upgraded
echo.

REM Install Python dependencies
echo [INFO] Installing Python dependencies...

echo [INFO] Installing main project dependencies...
pip install -r requirements.txt

echo [INFO] Installing API dependencies...
if exist "api\requirements.txt" (
    pip install -r api\requirements.txt
)

echo [INFO] Installing AI/ML dependencies...
if exist "ai_ml\anomaly_detection\requirements.txt" (
    pip install -r ai_ml\anomaly_detection\requirements.txt
)
if exist "ai_ml\nlp\requirements.txt" (
    pip install -r ai_ml\nlp\requirements.txt
)
if exist "ai_ml\pattern_recognition\requirements.txt" (
    pip install -r ai_ml\pattern_recognition\requirements.txt
)

echo [INFO] Installing threat intelligence dependencies...
if exist "threat_intelligence\collection\requirements.txt" (
    pip install -r threat_intelligence\collection\requirements.txt
)

echo [INFO] Installing testing dependencies...
if exist "testing\requirements.txt" (
    pip install -r testing\requirements.txt
)

echo [INFO] Installing development dependencies...
pip install black isort flake8 mypy bandit pytest pytest-cov

echo [SUCCESS] All dependencies installed
echo.

REM Setup configuration files
echo [INFO] Setting up configuration files...

if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo [WARNING] .env file created from template. Please edit with your configuration.
    ) else (
        REM Create basic .env file
        (
            echo # Database Configuration
            echo DATABASE_URL=postgresql://user:password@localhost:5432/cyber_security_db
            echo MONGO_URI=mongodb://localhost:27017/cyber_security
            echo REDIS_URL=redis://localhost:6379/0
            echo.
            echo # Security
            echo SECRET_KEY=your-secret-key-here-change-in-production
            echo ENCRYPTION_KEY=your-encryption-key-here
            echo JWT_SECRET=your-jwt-secret-here
            echo.
            echo # API Configuration
            echo API_HOST=0.0.0.0
            echo API_PORT=8000
            echo API_WORKERS=4
            echo.
            echo # Environment
            echo DEBUG=true
            echo LOG_LEVEL=INFO
            echo ENVIRONMENT=development
            echo.
            echo # Threat Intelligence APIs ^(Add your API keys^)
            echo ABUSEIPDB_API_KEY=your-abuseipdb-key
            echo GREYNOISE_API_KEY=your-greynoise-key
            echo OTX_API_KEY=your-otx-key
            echo VIRUSTOTAL_API_KEY=your-virustotal-key
            echo SHODAN_API_KEY=your-shodan-key
            echo.
            echo # Monitoring
            echo PROMETHEUS_URL=http://localhost:9090
            echo GRAFANA_URL=http://localhost:3000
            echo ELASTICSEARCH_URL=http://localhost:9200
            echo.
            echo # Security ^& Compliance
            echo GDPR_COMPLIANCE=false
            echo AUDIT_LOGGING=true
            echo ENCRYPTION_ENABLED=true
        ) > .env
        echo [WARNING] Basic .env file created. Please update with your configuration.
    )
) else (
    echo [WARNING] .env file already exists
)

REM Setup threat intelligence configuration
if exist "threat_intelligence\collection\threat_intel_config.json.template" (
    if not exist "threat_intelligence\collection\threat_intel_config.json" (
        copy "threat_intelligence\collection\threat_intel_config.json.template" "threat_intelligence\collection\threat_intel_config.json"
        echo [WARNING] Created threat intelligence config. Please update with your API keys.
    )
)

echo [SUCCESS] Configuration files setup complete
echo.

REM Setup pre-commit hooks
echo [INFO] Setting up pre-commit hooks...

REM Install pre-commit
pip install pre-commit

REM Install pre-commit hooks if .pre-commit-config.yaml exists
if exist ".pre-commit-config.yaml" (
    pre-commit install
    echo [SUCCESS] Pre-commit hooks installed
) else (
    REM Create basic pre-commit config
    (
        echo repos:
        echo   - repo: https://github.com/psf/black
        echo     rev: 23.3.0
        echo     hooks:
        echo       - id: black
        echo         language_version: python3
        echo.
        echo   - repo: https://github.com/pycqa/isort
        echo     rev: 5.12.0
        echo     hooks:
        echo       - id: isort
        echo.
        echo   - repo: https://github.com/pycqa/flake8
        echo     rev: 6.0.0
        echo     hooks:
        echo       - id: flake8
        echo.
        echo   - repo: https://github.com/pycqa/bandit
        echo     rev: 1.7.5
        echo     hooks:
        echo       - id: bandit
        echo         args: ['-r', '.', '--exclude', 'testing', 'venv']
        echo.
        echo   - repo: https://github.com/pre-commit/mirrors-mypy
        echo     rev: v1.3.0
        echo     hooks:
        echo       - id: mypy
    ) > .pre-commit-config.yaml
    pre-commit install
    echo [SUCCESS] Pre-commit hooks created and installed
)

echo.

REM Create development scripts
echo [INFO] Creating development scripts...

REM Create start script
(
echo @echo off
echo REM Start development environment
echo.
echo call venv\Scripts\activate.bat
echo.
echo echo Starting Cybersecurity Database System in development mode...
echo.
echo REM Start services
echo if exist docker-compose.dev.yml ^(
echo     docker-compose -f docker-compose.dev.yml up -d
echo ^) else if exist docker-compose.yml ^(
echo     docker-compose -f docker-compose.yml up -d
echo ^)
echo.
echo REM Start API server
echo uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
echo.
echo pause
) > start_dev.bat

REM Create test script
(
echo @echo off
echo REM Run tests
echo.
echo call venv\Scripts\activate.bat
echo.
echo echo Running tests...
echo.
echo if exist testing ^(
echo     python -m pytest testing/ -v --cov=app --cov=ai_ml --cov=threat_intelligence --cov-report=html --cov-report=term
echo ^) else (
echo     echo No tests directory found
echo ^)
echo.
echo echo Tests completed. Coverage report generated in htmlcov/ if tests were run.
echo.
echo pause
) > run_tests.bat

REM Create lint script
(
echo @echo off
echo REM Lint and format code
echo.
echo call venv\Scripts\activate.bat
echo.
echo echo Formatting code...
echo black *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
echo isort *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
echo.
echo echo Linting code...
echo flake8 *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
echo mypy *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
echo.
echo echo Security scan...
echo bandit -r api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
echo.
echo pause
) > lint.bat

REM Create activate script
(
echo @echo off
echo REM Activate virtual environment
echo call venv\Scripts\activate.bat
echo echo Virtual environment activated
echo echo Run 'deactivate' to exit
) > activate.bat

echo [SUCCESS] Development scripts created
echo.

REM Optional steps
echo.
set /p choice="Do you want to start development services now? (y/N): "
if /i "!choice!"=="y" (
    echo [INFO] Starting development services...
    
    REM Start development services
    if exist "docker-compose.dev.yml" (
        docker-compose -f docker-compose.dev.yml up -d
    ) else if exist "docker-compose.yml" (
        docker-compose -f docker-compose.yml up -d
    ) else (
        echo [WARNING] No docker-compose file found. Please start services manually.
    )
    
    REM Wait for services
    echo [INFO] Waiting for services to start...
    timeout /t 10 /nobreak >nul
    
    REM Initialize database
    if exist "scripts\init_database.py" (
        echo [INFO] Initializing database...
        python scripts\init_database.py
    ) else if exist "scripts\initialize_system.py" (
        echo [INFO] Initializing system...
        python scripts\initialize_system.py
    )
    
    REM Run tests
    if exist "testing" (
        echo [INFO] Running tests...
        python -m pytest testing/ -v --tb=short
    )
    
    echo [SUCCESS] Development services started and initialized
)

echo.
echo ============================================
echo Setup completed successfully!
echo ============================================
echo.
echo [INFO] Next steps:
echo 1. Edit .env file with your configuration
echo 2. Update threat_intelligence\collection\threat_intel_config.json with API keys
echo 3. Run 'start_dev.bat' to start the development server
echo 4. Open http://localhost:8000/docs for API documentation
echo 5. Run 'run_tests.bat' to execute tests
echo 6. Run 'lint.bat' to format and lint code
echo 7. Run 'activate.bat' to activate virtual environment
echo.
echo [INFO] Available commands:
echo - start_dev.bat    : Start development server
echo - run_tests.bat    : Run tests with coverage
echo - lint.bat         : Format and lint code
echo - activate.bat     : Activate virtual environment
echo.
echo [INFO] Documentation:
echo - API Docs: http://localhost:8000/docs
echo - ReDoc: http://localhost:8000/redoc
echo.
echo Happy coding! 🚀
echo.
pause