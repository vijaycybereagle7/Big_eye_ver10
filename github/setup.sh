#!/bin/bash

# Big Eye Security Database - Developer Setup Script
# This script sets up the development environment for the Big Eye Security Database

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION="3.9"
PROJECT_NAME="big-eye-security-database"
GIT_REPO_URL="https://github.com/your-org/big-eye-security-database.git"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    local missing_deps=()
    
    # Check for required commands
    for cmd in git python3 python3-pip docker docker-compose; do
        if ! command_exists $cmd; then
            missing_deps+=($cmd)
        fi
    done
    
    # Check Python version
    if command_exists python3; then
        python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        if [ "$(printf '%s\n' "3.9" "$python_version" | sort -V | head -n1)" != "3.9" ]; then
            print_warning "Python version $python_version detected. Python 3.9+ is recommended."
        else
            print_success "Python $python_version found"
        fi
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    print_success "All system requirements satisfied"
}

# Create project directory
setup_project_directory() {
    print_status "Setting up project directory..."
    
    if [ ! -d "$PROJECT_NAME" ]; then
        print_status "Cloning repository..."
        git clone $GIT_REPO_URL $PROJECT_NAME
        cd $PROJECT_NAME
    else
        print_warning "Project directory already exists. Updating repository..."
        cd $PROJECT_NAME
        git pull origin main
    fi
    
    print_success "Project directory ready"
}

# Setup Python virtual environment
setup_python_environment() {
    print_status "Setting up Python virtual environment..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment activated and pip upgraded"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install main dependencies
    print_status "Installing main project dependencies..."
    pip install -r requirements.txt
    
    # Install API dependencies
    print_status "Installing API dependencies..."
    pip install -r api/requirements.txt
    
    # Install AI/ML dependencies
    print_status "Installing AI/ML dependencies..."
    if [ -f "ai_ml/anomaly_detection/requirements.txt" ]; then
        pip install -r ai_ml/anomaly_detection/requirements.txt
    fi
    if [ -f "ai_ml/nlp/requirements.txt" ]; then
        pip install -r ai_ml/nlp/requirements.txt
    fi
    if [ -f "ai_ml/pattern_recognition/requirements.txt" ]; then
        pip install -r ai_ml/pattern_recognition/requirements.txt
    fi
    
    # Install threat intelligence dependencies
    print_status "Installing threat intelligence dependencies..."
    if [ -f "threat_intelligence/collection/requirements.txt" ]; then
        pip install -r threat_intelligence/collection/requirements.txt
    fi
    
    # Install testing dependencies
    print_status "Installing testing dependencies..."
    if [ -f "testing/requirements.txt" ]; then
        pip install -r testing/requirements.txt
    fi
    
    # Install development dependencies
    print_status "Installing development dependencies..."
    pip install black isort flake8 mypy bandit pytest pytest-cov
    
    print_success "All dependencies installed"
}

# Setup configuration files
setup_configuration() {
    print_status "Setting up configuration files..."
    
    # Create .env file from template
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your configuration"
        else
            # Create basic .env file
            cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/cyber_security_db
MONGO_URI=mongodb://localhost:27017/cyber_security
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ENCRYPTION_KEY=your-encryption-key-here
JWT_SECRET=your-jwt-secret-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Environment
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# Threat Intelligence APIs (Add your API keys)
ABUSEIPDB_API_KEY=your-abuseipdb-key
GREYNOISE_API_KEY=your-greynoise-key
OTX_API_KEY=your-otx-key
VIRUSTOTAL_API_KEY=your-virustotal-key
SHODAN_API_KEY=your-shodan-key

# Monitoring
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
ELASTICSEARCH_URL=http://localhost:9200

# Security & Compliance
GDPR_COMPLIANCE=false
AUDIT_LOGGING=true
ENCRYPTION_ENABLED=true
EOF
            print_warning "Basic .env file created. Please update with your configuration."
        fi
    else
        print_warning ".env file already exists"
    fi
    
    # Setup threat intelligence configuration
    if [ -f "threat_intelligence/collection/threat_intel_config.json.template" ]; then
        if [ ! -f "threat_intelligence/collection/threat_intel_config.json" ]; then
            cp threat_intelligence/collection/threat_intel_config.json.template \
               threat_intelligence/collection/threat_intel_config.json
            print_warning "Created threat intelligence config. Please update with your API keys."
        fi
    fi
    
    print_success "Configuration files setup complete"
}

# Setup pre-commit hooks
setup_pre_commit() {
    print_status "Setting up pre-commit hooks..."
    
    source venv/bin/activate
    
    # Install pre-commit
    pip install pre-commit
    
    # Install pre-commit hooks if .pre-commit-config.yaml exists
    if [ -f ".pre-commit-config.yaml" ]; then
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        # Create basic pre-commit config
        cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
  
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', '.', '--exclude', 'testing', 'venv']
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
EOF
        pre-commit install
        print_success "Pre-commit hooks created and installed"
    fi
}

# Start development services
start_services() {
    print_status "Starting development services..."
    
    # Check if docker-compose is available
    if command_exists docker-compose; then
        docker-compose_version="docker-compose"
    elif command_exists docker; then
        docker-compose_version="docker compose"
    else
        print_error "Docker Compose not found"
        return 1
    fi
    
    # Start development services
    if [ -f "docker-compose.dev.yml" ]; then
        print_status "Starting development services with docker-compose.dev.yml..."
        $docker-compose_version -f docker-compose.dev.yml up -d
    elif [ -f "docker-compose.yml" ]; then
        print_status "Starting services with docker-compose.yml..."
        $docker-compose_version -f docker-compose.yml up -d
    else
        print_warning "No docker-compose file found. Please start services manually."
        return 1
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 10
    
    # Check if services are running
    if $docker-compose_version ps | grep -q "Up"; then
        print_success "Development services started successfully"
    else
        print_error "Some services may not have started properly"
        $docker-compose_version ps
    fi
}

# Initialize database
initialize_database() {
    print_status "Initializing database..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run database initialization script if it exists
    if [ -f "scripts/init_database.py" ]; then
        python scripts/init_database.py
        print_success "Database initialized"
    elif [ -f "scripts/initialize_system.py" ]; then
        python scripts/initialize_system.py
        print_success "System initialized"
    else
        print_warning "No database initialization script found"
    fi
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run basic tests
    if [ -d "testing" ]; then
        python -m pytest testing/ -v --tb=short || print_warning "Some tests failed"
    fi
    
    print_success "Tests completed"
}

# Create development scripts
setup_dev_scripts() {
    print_status "Creating development scripts..."
    
    # Create start script
    cat > start_dev.sh << 'EOF'
#!/bin/bash
# Start development environment

source venv/bin/activate

echo "Starting Cybersecurity Database System in development mode..."

# Start services
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.dev.yml up -d
elif docker compose version >/dev/null 2>&1; then
    docker compose -f docker-compose.dev.yml up -d
fi

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

EOF

    chmod +x start_dev.sh
    
    # Create test script
    cat > run_tests.sh << 'EOF'
#!/bin/bash
# Run tests

source venv/bin/activate

echo "Running tests..."

# Run all tests
python -m pytest testing/ -v --cov=app --cov=ai_ml --cov=threat_intelligence --cov-report=html --cov-report=term

echo "Tests completed. Coverage report generated in htmlcov/"

EOF

    chmod +x run_tests.sh
    
    # Create lint script
    cat > lint.sh << 'EOF'
#!/bin/bash
# Lint and format code

source venv/bin/activate

echo "Formatting code..."
black *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
isort *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/

echo "Linting code..."
flake8 *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/
mypy *.py api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/

echo "Security scan..."
bandit -r api/ threat_intelligence/ ai_ml/ security/ database/ performance/ monitoring/ testing/

EOF

    chmod +x lint.sh
    
    print_success "Development scripts created"
}

# Print next steps
print_next_steps() {
    echo
    print_success "============================================"
    print_success "Setup completed successfully!"
    print_success "============================================"
    echo
    print_status "Next steps:"
    echo "1. Edit .env file with your configuration"
    echo "2. Update threat_intelligence/collection/threat_intel_config.json with API keys"
    echo "3. Run './start_dev.sh' to start the development server"
    echo "4. Open http://localhost:8000/docs for API documentation"
    echo "5. Run './run_tests.sh' to execute tests"
    echo "6. Run './lint.sh' to format and lint code"
    echo
    print_status "Available commands:"
    echo "- ./start_dev.sh    : Start development server"
    echo "- ./run_tests.sh    : Run tests with coverage"
    echo "- ./lint.sh         : Format and lint code"
    echo "- source venv/bin/activate : Activate virtual environment"
    echo
    print_status "Documentation:"
    echo "- API Docs: http://localhost:8000/docs"
    echo "- ReDoc: http://localhost:8000/redoc"
    echo
    print_success "Happy coding! 🚀"
}

# Main setup function
main() {
    echo "============================================"
    echo "Cybersecurity Database System - Setup"
    echo "============================================"
    echo
    
    check_requirements
    setup_project_directory
    setup_python_environment
    install_dependencies
    setup_configuration
    setup_pre_commit
    setup_dev_scripts
    
    # Optional steps (ask user)
    echo
    read -p "Do you want to start development services now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        initialize_database
        run_tests
    fi
    
    print_next_steps
}

# Run main function
main "$@"