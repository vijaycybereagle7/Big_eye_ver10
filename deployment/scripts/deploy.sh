#!/bin/bash
# Comprehensive Deployment Script for Threat Intelligence Platform
# Supports Docker Compose and Kubernetes deployments

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/var/log/threatintel_deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local message="$1"
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    cleanup
    exit 1
}

cleanup() {
    # Remove temporary files
    find /tmp -name "threatintel_*" -type d -exec rm -rf {} + 2>/dev/null || true
}

trap cleanup EXIT

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check required commands
    for cmd in docker docker-compose kubectl helm aws curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error_exit "Missing required dependencies: ${missing_deps[*]}"
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running"
    fi
    
    # Check Docker Compose version
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [[ "$(printf '%s\n' "1.29.0" "$compose_version" | sort -V | head -n1)" != "1.29.0" ]]; then
        error_exit "Docker Compose version must be >= 1.29.0 (found: $compose_version)"
    fi
    
    # Check available disk space (minimum 10GB)
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        error_exit "Insufficient disk space. Required: 10GB, Available: $(($available_space / 1048576))GB"
    fi
    
    log_success "Prerequisites check passed"
}

# Parse command line arguments
parse_args() {
    DEPLOYMENT_TYPE=""
    ENVIRONMENT=""
    SKIP_BACKUP=""
    SKIP_TESTS=""
    FORCE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP="true"
                shift
                ;;
            --skip-tests)
                SKIP_TESTS="true"
                shift
                ;;
            --force)
                FORCE="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Validate deployment type
    if [ -z "$DEPLOYMENT_TYPE" ]; then
        DEPLOYMENT_TYPE="docker-compose"  # Default
    fi
    
    if [[ ! "$DEPLOYMENT_TYPE" =~ ^(docker-compose|kubernetes)$ ]]; then
        error_exit "Invalid deployment type: $DEPLOYMENT_TYPE. Must be 'docker-compose' or 'kubernetes'"
    fi
    
    # Validate environment
    if [ -z "$ENVIRONMENT" ]; then
        ENVIRONMENT="development"  # Default
    fi
    
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        error_exit "Invalid environment: $ENVIRONMENT. Must be 'development', 'staging', or 'production'"
    fi
    
    log_info "Deployment type: $DEPLOYMENT_TYPE"
    log_info "Environment: $ENVIRONMENT"
}

show_help() {
    cat << EOF
Threat Intelligence Platform Deployment Script

Usage: $0 [OPTIONS]

Options:
  --type TYPE           Deployment type: docker-compose (default) or kubernetes
  --env ENV            Environment: development (default), staging, or production
  --skip-backup        Skip backup before deployment
  --skip-tests         Skip post-deployment tests
  --force              Force deployment without confirmation
  --help               Show this help message

Examples:
  $0 --type docker-compose --env development
  $0 --type kubernetes --env production
  $0 --type docker-compose --env staging --skip-backup

EOF
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    local dirs=(
        "/opt/data/postgres_timescaledb"
        "/opt/data/mongodb"
        "/opt/data/redis"
        "/opt/data/prometheus"
        "/opt/data/grafana"
        "/opt/data/elasticsearch"
        "/opt/data/kibana"
        "/opt/data/logstash"
        "/opt/backups"
        "/var/log/nginx"
        "/etc/ssl/certs"
        "/etc/ssl/private"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir" || error_exit "Failed to create directory: $dir"
        chmod 755 "$dir"
    done
    
    log_success "Directories created successfully"
}

# Setup environment variables
setup_environment() {
    log_info "Setting up environment variables..."
    
    local env_file="$SCRIPT_DIR/docker/.env"
    
    if [ ! -f "$env_file" ]; then
        if [ -f "$SCRIPT_DIR/docker/.env.template" ]; then
            cp "$SCRIPT_DIR/docker/.env.template" "$env_file"
            log_warning "Environment file created from template. Please update $env_file with your values."
        else
            error_exit "Environment file not found: $env_file"
        fi
    fi
    
    # Load environment variables
    if [ -f "$env_file" ]; then
        source "$env_file"
    fi
    
    # Generate secure passwords if not set
    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
        export POSTGRES_PASSWORD=$(openssl rand -base64 32)
        log_warning "Generated PostgreSQL password"
    fi
    
    if [ -z "${MONGO_ROOT_PASSWORD:-}" ]; then
        export MONGO_ROOT_PASSWORD=$(openssl rand -base64 32)
        log_warning "Generated MongoDB root password"
    fi
    
    if [ -z "${REDIS_PASSWORD:-}" ]; then
        export REDIS_PASSWORD=$(openssl rand -base64 32)
        log_warning "Generated Redis password"
    fi
    
    if [ -z "${SECRET_KEY:-}" ]; then
        export SECRET_KEY=$(openssl rand -base64 48)
        log_warning "Generated application secret key"
    fi
    
    if [ -z "${GRAFANA_ADMIN_PASSWORD:-}" ]; then
        export GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)
        log_warning "Generated Grafana admin password"
    fi
    
    log_success "Environment variables configured"
}

# Create SSL certificates for production
create_ssl_certificates() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log_info "Setting up SSL certificates for production..."
        
        local cert_file="/etc/ssl/certs/threatintel.crt"
        local key_file="/etc/ssl/private/threatintel.key"
        
        if [ ! -f "$cert_file" ] || [ ! -f "$key_file" ]; then
            log_warning "SSL certificates not found. Generating self-signed certificates..."
            log_warning "Replace with proper certificates for production use."
            
            # Create self-signed certificate (for testing only)
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$key_file" \
                -out "$cert_file" \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=threatintel.local" \
                2>/dev/null || log_warning "Failed to generate SSL certificates"
            
            chmod 600 "$key_file"
            chmod 644 "$cert_file"
        fi
        
        log_success "SSL certificates configured"
    fi
}

# Pre-deployment backup
pre_deployment_backup() {
    if [ "$SKIP_BACKUP" = "true" ]; then
        log_info "Skipping pre-deployment backup"
        return
    fi
    
    if [ "$ENVIRONMENT" = "production" ] && [ -z "$FORCE" ]; then
        log_warning "Production deployment detected. A backup is strongly recommended."
        read -p "Do you want to create a backup before deployment? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Creating pre-deployment backup..."
            ./backup/scripts/postgres_backup.sh || log_warning "PostgreSQL backup failed"
            ./backup/scripts/mongodb_backup.sh || log_warning "MongoDB backup failed"
            ./backup/scripts/redis_backup.sh || log_warning "Redis backup failed"
            log_success "Pre-deployment backup completed"
        else
            log_warning "Skipping pre-deployment backup"
        fi
    fi
}

# Docker Compose deployment
deploy_docker_compose() {
    log_info "Starting Docker Compose deployment..."
    
    cd "$SCRIPT_DIR/docker"
    
    # Build and start services
    log_info "Building Docker images..."
    docker-compose build --no-cache || error_exit "Docker build failed"
    
    log_info "Starting services..."
    docker-compose up -d || error_exit "Docker Compose up failed"
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Health checks
    if [ "$SKIP_TESTS" != "true" ]; then
        run_health_checks
    fi
    
    log_success "Docker Compose deployment completed"
}

# Kubernetes deployment
deploy_kubernetes() {
    log_info "Starting Kubernetes deployment..."
    
    # Check kubectl context
    if ! kubectl cluster-info &> /dev/null; then
        error_exit "kubectl is not configured or cluster is not accessible"
    fi
    
    # Create namespace
    local namespace="threatintel-platform"
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    log_info "Creating Kubernetes secrets..."
    kubectl create secret generic "$namespace-secrets" \
        --from-literal=postgres-password="$POSTGRES_PASSWORD" \
        --from-literal=mongo-root-password="$MONGO_ROOT_PASSWORD" \
        --from-literal=redis-password="$REDIS_PASSWORD" \
        --from-literal=secret-key="$SECRET_KEY" \
        --from-literal=grafana-admin-password="$GRAFANA_ADMIN_PASSWORD" \
        --dry-run=client -o yaml | kubectl apply -f - || log_warning "Secret creation failed"
    
    # Deploy with Helm
    local helm_chart="$PROJECT_ROOT/kubernetes/helm/threatintel-platform"
    local helm_values="$helm_chart/values-$ENVIRONMENT.yaml"
    
    if [ ! -f "$helm_values" ]; then
        # Use default values file
        helm_values="$helm_chart/values.yaml"
    fi
    
    log_info "Deploying with Helm..."
    helm upgrade --install threatintel-platform "$helm_chart" \
        --namespace "$namespace" \
        --create-namespace \
        --values "$helm_values" \
        --timeout 600s \
        --wait || error_exit "Helm deployment failed"
    
    # Wait for deployments to be ready
    log_info "Waiting for deployments to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment -l app.kubernetes.io/instance=threatintel-platform -n "$namespace"
    
    if [ "$SKIP_TESTS" != "true" ]; then
        run_health_checks
    fi
    
    log_success "Kubernetes deployment completed"
}

# Run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    local max_attempts=30
    local attempt=0
    
    # Check PostgreSQL
    log_info "Checking PostgreSQL..."
    while [ $attempt -lt $max_attempts ]; do
        if pg_isready -h localhost -p 5432 -U threatintel_user &> /dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "PostgreSQL health check failed"
    fi
    
    # Check MongoDB
    log_info "Checking MongoDB..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if mongosh --host localhost --port 27017 --eval "db.adminCommand('ping')" --quiet &> /dev/null; then
            log_success "MongoDB is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "MongoDB health check failed"
    fi
    
    # Check Redis
    log_info "Checking Redis..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if redis-cli ping &> /dev/null; then
            log_success "Redis is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Redis health check failed"
    fi
    
    # Check FastAPI
    log_info "Checking FastAPI application..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "FastAPI application is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "FastAPI application health check failed"
    fi
    
    # Check monitoring services
    log_info "Checking monitoring services..."
    if curl -f http://localhost:9090/-/healthy &> /dev/null; then
        log_success "Prometheus is ready"
    else
        log_warning "Prometheus health check failed"
    fi
    
    if curl -f http://localhost:3000/api/health &> /dev/null; then
        log_success "Grafana is ready"
    else
        log_warning "Grafana health check failed"
    fi
    
    log_success "Health checks completed"
}

# Show deployment summary
show_summary() {
    log_info "=== Deployment Summary ==="
    
    if [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        echo "Deployment Type: Docker Compose"
        echo "Environment: $ENVIRONMENT"
        echo "Services:"
        docker-compose ps
        
        echo ""
        echo "Access URLs:"
        echo "- Application: http://localhost"
        echo "- API Documentation: http://localhost/docs"
        echo "- Prometheus: http://localhost:9090"
        echo "- Grafana: http://localhost:3000"
        echo "- Kibana: http://localhost:5601"
        
    elif [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        echo "Deployment Type: Kubernetes"
        echo "Environment: $ENVIRONMENT"
        echo "Namespace: threatintel-platform"
        echo "Services:"
        kubectl get services -n threatintel-platform
        
        echo ""
        echo "To access services:"
        echo "kubectl port-forward -n threatintel-platform svc/threatintel-platform-fastapi 8000:8000"
        echo "kubectl port-forward -n threatintel-platform svc/threatintel-platform-grafana 3000:3000"
        echo "kubectl port-forward -n threatintel-platform svc/threatintel-platform-prometheus-server 9090:9090"
    fi
    
    echo ""
    echo "Log file: $LOG_FILE"
    echo "Deployment completed successfully!"
}

# Main deployment function
main() {
    log_info "Starting Threat Intelligence Platform deployment..."
    
    # Parse command line arguments
    parse_args "$@"
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_directories
    
    # Setup environment
    setup_environment
    
    # Create SSL certificates for production
    create_ssl_certificates
    
    # Pre-deployment backup
    pre_deployment_backup
    
    # Deploy based on type
    if [ "$DEPLOYMENT_TYPE" = "docker-compose" ]; then
        deploy_docker_compose
    elif [ "$DEPLOYMENT_TYPE" = "kubernetes" ]; then
        deploy_kubernetes
    fi
    
    # Show summary
    show_summary
    
    log_success "Deployment completed successfully!"
}

# Execute main function
main "$@"