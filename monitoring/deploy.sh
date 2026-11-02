#!/bin/bash
# Deployment script for Cybersecurity API Monitoring Stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="cybersecurity-monitoring"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available memory
    MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$MEMORY_GB" -lt 8 ]; then
        log_warning "Less than 8GB RAM detected. Elasticsearch may not perform optimally."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    log_success "Prerequisites check passed"
}

create_env_file() {
    log_info "Creating environment configuration file..."
    
    cat > "$ENV_FILE" << EOF
# Cybersecurity API Monitoring Stack Configuration

# Database Configuration
POSTGRES_DB=cybersecurity_api
POSTGRES_USER=api_user
POSTGRES_PASSWORD=api_password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MongoDB Configuration
MONGODB_USER=admin
MONGODB_PASSWORD=mongodb_password
MONGODB_DATABASE=cybersecurity_api
MONGODB_HOST=mongo
MONGODB_PORT=27017

# Redis Configuration
REDIS_PASSWORD=redis_password
REDIS_HOST=redis
REDIS_PORT=6379

# Grafana Configuration
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123

# Threat Intelligence API Keys (Please update with your actual keys)
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
ABUSEIPDB_API_KEY=your_abuseipdb_api_key_here
GREYNOISE_API_KEY=your_greynoise_api_key_here
SHODAN_API_KEY=your_shodan_api_key_here
OTX_API_KEY=your_otx_api_key_here
SPAMHAUS_API_KEY=your_spamhaus_api_key_here
PHISHTANK_API_KEY=your_phishtank_api_key_here
SAFE_BROWSING_API_KEY=your_safe_browsing_api_key_here
SECURITYTRAILS_API_KEY=your_securitytrails_api_key_here

# Email Configuration for Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@your-domain.com
SMTP_PASSWORD=your_email_password

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Elasticsearch Configuration
ELASTIC_PASSWORD=elastic_password

# Kibana Configuration
KIBANA_ENCRYPTION_KEY=your_32_character_encryption_key_here
KIBANA_REPORTING_KEY=your_reporting_key_here

# Project Configuration
PROJECT_NAME=$PROJECT_NAME
COMPOSE_PROJECT_NAME=$PROJECT_NAME
EOF

    log_success "Environment file created: $ENV_FILE"
    log_warning "Please update the API keys in $ENV_FILE with your actual values"
}

setup_directories() {
    log_info "Setting up required directories..."
    
    # Create additional directories for data persistence
    mkdir -p prometheus/data
    mkdir -p alertmanager/data
    mkdir -p grafana/data
    mkdir -p elasticsearch/data
    mkdir -p logstash/data
    mkdir -p kibana/data
    mkdir -p kafka/data
    mkdir -p victoriametrics/data
    mkdir -p logs
    
    # Set appropriate permissions
    chmod 755 prometheus/data alertmanager/data grafana/data
    chmod 755 elasticsearch/data logstash/data kibana/data
    chmod 755 kafka/data victoriametrics/data
    
    log_success "Directories created"
}

validate_configuration() {
    log_info "Validating configuration..."
    
    # Check if docker-compose.yml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Validate Docker Compose configuration
    if ! docker-compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        log_error "Docker Compose configuration validation failed"
        exit 1
    fi
    
    log_success "Configuration validation passed"
}

start_services() {
    log_info "Starting monitoring services..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services started"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for Prometheus
    log_info "Waiting for Prometheus..."
    timeout=60
    while ! curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout-5))
        if [ "$timeout" -le 0 ]; then
            log_error "Prometheus failed to start"
            exit 1
        fi
    done
    
    # Wait for Grafana
    log_info "Waiting for Grafana..."
    timeout=60
    while ! curl -sf http://localhost:3000/api/health > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout-5))
        if [ "$timeout" -le 0 ]; then
            log_error "Grafana failed to start"
            exit 1
        fi
    done
    
    # Wait for Elasticsearch
    log_info "Waiting for Elasticsearch..."
    timeout=120
    while ! curl -sf http://localhost:9200/_cluster/health > /dev/null 2>&1; do
        sleep 10
        timeout=$((timeout-10))
        if [ "$timeout" -le 0 ]; then
            log_error "Elasticsearch failed to start"
            exit 1
        fi
    done
    
    # Wait for Kibana
    log_info "Waiting for Kibana..."
    timeout=60
    while ! curl -sf http://localhost:5601/api/status > /dev/null 2>&1; do
        sleep 5
        timeout=$((timeout-5))
        if [ "$timeout" -le 0 ]; then
            log_error "Kibana failed to start"
            exit 1
        fi
    done
    
    log_success "All services are ready"
}

import_dashboards() {
    log_info "Importing Grafana dashboards..."
    
    # This would be implemented to automatically import dashboards
    # For now, we provide instructions
    log_warning "Please import the dashboard JSON files manually in Grafana:"
    echo "  1. Go to http://localhost:3000"
    echo "  2. Navigate to Dashboards -> Import"
    echo "  3. Import the following files:"
    echo "     - grafana/dashboards/overview.json"
    echo "     - grafana/dashboards/database.json"
    echo "     - grafana/dashboards/threat-intelligence.json"
}

show_service_status() {
    log_info "Checking service status..."
    
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "Service URLs:"
    echo "  Prometheus:     http://localhost:9090"
    echo "  Grafana:        http://localhost:3000 (admin/admin123)"
    echo "  Alertmanager:   http://localhost:9093"
    echo "  Elasticsearch:  http://localhost:9200"
    echo "  Kibana:         http://localhost:5601"
    echo "  Node Exporter:  http://localhost:9100"
    echo "  cAdvisor:       http://localhost:8080"
    echo ""
    log_success "Monitoring stack deployment completed!"
}

show_next_steps() {
    log_info "Next steps:"
    echo "  1. Update API keys in $ENV_FILE"
    echo "  2. Import Grafana dashboards"
    echo "  3. Configure alert notifications in Alertmanager"
    echo "  4. Set up log shipping from your applications"
    echo "  5. Monitor the dashboards for system health"
    echo ""
    log_info "For help and troubleshooting, see README.md"
}

# Main execution
main() {
    echo "========================================"
    echo "  Cybersecurity API Monitoring Stack"
    echo "         Deployment Script"
    echo "========================================"
    echo ""
    
    check_prerequisites
    create_env_file
    setup_directories
    validate_configuration
    start_services
    wait_for_services
    import_dashboards
    show_service_status
    show_next_steps
}

# Handle script arguments
case "${1:-}" in
    "start")
        main
        ;;
    "stop")
        log_info "Stopping monitoring services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting monitoring services..."
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "Services restarted"
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        ;;
    "update")
        log_info "Updating monitoring stack..."
        docker-compose -f "$COMPOSE_FILE" pull
        docker-compose -f "$COMPOSE_FILE" up -d
        log_success "Stack updated"
        ;;
    "cleanup")
        log_warning "This will remove all monitoring data!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f "$COMPOSE_FILE" down -v
            docker system prune -f
            log_success "Cleanup completed"
        else
            log_info "Cleanup cancelled"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Deploy the monitoring stack (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status"
        echo "  logs      - Show service logs"
        echo "  update    - Update and restart services"
        echo "  cleanup   - Remove all services and data"
        echo "  help      - Show this help message"
        ;;
    *)
        main
        ;;
esac