#!/bin/bash
# Quick Setup Script for Threat Intelligence Platform
# Prepares the environment for deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"
}

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if running as appropriate user
check_user() {
    if [ "$EUID" -eq 0 ]; then
        log_warning "Running as root. Consider running as a non-root user."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    local dirs=(
        "/opt/data/postgres_timescaledb"
        "/opt/data/mongodb"
        "/opt/data/redis"
        "/opt/data/prometheus"
        "/opt/data/grafana"
        "/opt/data/elasticsearch"
        "/opt/data/kibana"
        "/opt/data/logstash"
        "/opt/backups/postgres"
        "/opt/backups/mongodb"
        "/opt/backups/redis"
        "/var/log/nginx"
        "/etc/ssl/certs"
        "/etc/ssl/private"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir" 2>/dev/null || sudo mkdir -p "$dir"
            log_success "Created directory: $dir"
        else
            log "Directory already exists: $dir"
        fi
    done
}

# Set proper permissions
set_permissions() {
    log "Setting proper permissions..."
    
    # Data directories should be owned by the user
    chown -R $(whoami):$(whoami) /opt/data/* /opt/backups/* /var/log/nginx 2>/dev/null || \
        log_warning "Could not set ownership for data directories. Run with appropriate permissions."
    
    # SSL directories need specific permissions
    chmod 755 /etc/ssl/certs
    chmod 700 /etc/ssl/private
    
    # Make scripts executable
    chmod +x "$SCRIPT_DIR/deploy.sh" 2>/dev/null || \
        log_warning "Could not make deploy.sh executable"
    
    chmod +x "$SCRIPT_DIR/backup/scripts/"*.sh 2>/dev/null || \
        log_warning "Could not make backup scripts executable"
    
    log_success "Permissions set"
}

# Generate environment file
setup_environment() {
    local env_file="$PROJECT_ROOT/docker/.env"
    
    if [ ! -f "$env_file" ]; then
        log "Creating environment file..."
        
        if [ -f "$PROJECT_ROOT/docker/.env.template" ]; then
            cp "$PROJECT_ROOT/docker/.env.template" "$env_file"
            
            # Generate secure passwords
            local postgres_pwd=$(openssl rand -base64 32 2>/dev/null || echo "secure_postgres_password_here")
            local mongo_pwd=$(openssl rand -base64 32 2>/dev/null || echo "secure_mongo_password_here")
            local redis_pwd=$(openssl rand -base64 32 2>/dev/null || echo "secure_redis_password_here")
            local secret_key=$(openssl rand -base64 48 2>/dev/null || echo "your_very_secure_secret_key_here_minimum_32_characters")
            local grafana_pwd=$(openssl rand -base64 16 2>/dev/null || echo "secure_grafana_password_here")
            
            # Update the environment file with generated values
            sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$postgres_pwd/" "$env_file"
            sed -i.bak "s/MONGO_ROOT_PASSWORD=.*/MONGO_ROOT_PASSWORD=$mongo_pwd/" "$env_file"
            sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$redis_pwd/" "$env_file"
            sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$secret_key/" "$env_file"
            sed -i.bak "s/GRAFANA_ADMIN_PASSWORD=.*/GRAFANA_ADMIN_PASSWORD=$grafana_pwd/" "$env_file"
            
            rm -f "$env_file.bak"
            
            log_success "Environment file created with secure passwords"
            log_warning "Please review and update $env_file with your specific configuration"
        else
            log_error "Environment template not found: $PROJECT_ROOT/docker/.env.template"
            return 1
        fi
    else
        log "Environment file already exists: $env_file"
    fi
}

# Generate SSL certificates
setup_ssl() {
    if [ ! -f "/etc/ssl/certs/threatintel.crt" ] || [ ! -f "/etc/ssl/private/threatintel.key" ]; then
        log "Generating self-signed SSL certificates..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "/etc/ssl/private/threatintel.key" \
            -out "/etc/ssl/certs/threatintel.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=threatintel.local" \
            2>/dev/null || {
                log_warning "Could not generate SSL certificates. You may need to run as root or install openssl."
                return 0
            }
        
        chmod 600 "/etc/ssl/private/threatintel.key"
        chmod 644 "/etc/ssl/certs/threatintel.crt"
        
        log_success "SSL certificates generated"
        log_warning "Replace with proper certificates for production use"
    else
        log "SSL certificates already exist"
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    local missing_deps=()
    
    # Check required commands
    for cmd in docker docker-compose; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install Docker and Docker Compose"
        return 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        log_info "Please start Docker daemon"
        return 1
    fi
    
    # Check available disk space (minimum 10GB)
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        log_warning "Insufficient disk space. Required: 10GB, Available: $(($available_space / 1048576))GB"
    fi
    
    log_success "Prerequisites check passed"
}

# Create quick start script
create_quick_start() {
    local script_file="$PROJECT_ROOT/quick_start.sh"
    
    cat > "$script_file" << 'EOF'
#!/bin/bash
# Quick Start Script for Threat Intelligence Platform

set -euo pipefail

cd "$(dirname "$0")/deployment"

# Deploy with Docker Compose
./scripts/deploy.sh --type docker-compose --env development
EOF
    
    chmod +x "$script_file" 2>/dev/null || true
    
    log_success "Quick start script created: $script_file"
    log_info "Run './quick_start.sh' to deploy the platform"
}

# Show next steps
show_next_steps() {
    log_success "Setup completed successfully!"
    
    echo ""
    echo "=== Next Steps ==="
    echo ""
    echo "1. Review configuration:"
    echo "   cat $PROJECT_ROOT/docker/.env"
    echo ""
    echo "2. Deploy the platform:"
    echo "   cd $PROJECT_ROOT/deployment"
    echo "   ./scripts/deploy.sh --type docker-compose --env development"
    echo ""
    echo "   Or use the quick start script:"
    echo "   ./quick_start.sh"
    echo ""
    echo "3. Access the services:"
    echo "   - Application: http://localhost"
    echo "   - API Documentation: http://localhost/docs"
    echo "   - Grafana: http://localhost:3000"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Kibana: http://localhost:5601"
    echo ""
    echo "4. For Kubernetes deployment:"
    echo "   ./scripts/deploy.sh --type kubernetes --env production"
    echo ""
    echo "5. Setup backups:"
    echo "   ./backup/scripts/postgres_backup.sh"
    echo "   ./backup/scripts/mongodb_backup.sh"
    echo "   ./backup/scripts/redis_backup.sh"
    echo ""
    echo "=== Documentation ==="
    echo "- Deployment Guide: $PROJECT_ROOT/deployment/README.md"
    echo "- Disaster Recovery: $PROJECT_ROOT/deployment/docs/disaster_recovery_plan.md"
    echo ""
}

# Main setup function
main() {
    echo "======================================"
    echo "Threat Intelligence Platform Setup"
    echo "======================================"
    echo ""
    
    # Check prerequisites
    check_prerequisites || exit 1
    
    # Check user
    check_user
    
    # Create directories
    create_directories
    
    # Set permissions
    set_permissions
    
    # Setup environment
    setup_environment
    
    # Setup SSL
    setup_ssl
    
    # Create quick start script
    create_quick_start
    
    # Show next steps
    show_next_steps
}

# Execute main function
main "$@"