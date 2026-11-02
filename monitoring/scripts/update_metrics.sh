#!/bin/bash
# Metrics Collection Update Script
# Updates Prometheus scrape configuration and restarts services

set -e

MONITORING_DIR="/workspace/monitoring"
COMPOSE_FILE="$MONITORING_DIR/docker-compose.yml"
PROMETHEUS_CONFIG="$MONITORING_DIR/prometheus/prometheus.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

validate_config() {
    log_info "Validating Prometheus configuration..."
    
    if command -v promtool &> /dev/null; then
        if promtool check config "$PROMETHEUS_CONFIG"; then
            log_info "Prometheus configuration is valid"
            return 0
        else
            log_error "Prometheus configuration validation failed"
            return 1
        fi
    else
        log_warning "promtool not found, skipping validation"
        return 0
    fi
}

reload_prometheus() {
    log_info "Reloading Prometheus configuration..."
    
    # Send SIGHUP to reload configuration
    docker kill --signal=HUP prometheus 2>/dev/null || log_warning "Could not reload Prometheus configuration"
    
    # Alternative: restart the service
    if [ "$1" == "--restart" ]; then
        log_info "Restarting Prometheus service..."
        docker-compose -f "$COMPOSE_FILE" restart prometheus
    fi
}

add_new_targets() {
    local service_name=$1
    local port=$2
    local metrics_path=${3:-"/metrics"}
    
    log_info "Adding new target: $service_name on port $port"
    
    # This would update the prometheus.yml file
    # For now, we'll just log the action
    echo "Would add: - job_name: '$service_name'" >> /tmp/prometheus_updates.yml
    echo "    static_configs:" >> /tmp/prometheus_updates.yml
    echo "      - targets: ['$service_name:$port']" >> /tmp/prometheus_updates.yml
    echo "    metrics_path: '$metrics_path'" >> /tmp/prometheus_updates.yml
    echo "    scrape_interval: 15s" >> /tmp/prometheus_updates.yml
    echo "" >> /tmp/prometheus_updates.yml
}

backup_config() {
    local backup_file="$PROMETHEUS_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    log_info "Creating backup: $backup_file"
    cp "$PROMETHEUS_CONFIG" "$backup_file"
}

update_config() {
    log_info "Updating Prometheus configuration..."
    
    # Create a temporary updated config
    # This would include your actual configuration updates
    
    # For demonstration, we'll just check if we can write to the file
    if [ -w "$PROMETHEUS_CONFIG" ]; then
        log_info "Configuration file is writable"
    else
        log_error "Cannot write to configuration file"
        return 1
    fi
}

test_targets() {
    log_info "Testing Prometheus targets..."
    
    # Wait for Prometheus to be available
    sleep 10
    
    # Query the targets endpoint
    if curl -sf http://localhost:9090/api/v1/targets > /dev/null; then
        log_info "Prometheus targets are accessible"
        curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length' || echo "Failed to parse targets"
    else
        log_error "Prometheus targets are not accessible"
    fi
}

show_status() {
    log_info "Prometheus status:"
    docker-compose -f "$COMPOSE_FILE" ps prometheus
    
    log_info "Recent Prometheus logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=20 prometheus
}

main() {
    echo "🔄 Metrics Collection Update Script"
    echo "===================================="
    
    case "${1:-}" in
        "validate")
            validate_config
            ;;
        "reload")
            validate_config && reload_prometheus
            ;;
        "restart")
            validate_config && reload_prometheus --restart
            ;;
        "add")
            if [ -z "$2" ] || [ -z "$3" ]; then
                echo "Usage: $0 add <service_name> <port> [metrics_path]"
                exit 1
            fi
            backup_config
            add_new_targets "$2" "$3" "$4"
            log_info "Configuration updates prepared. Please review and apply manually."
            ;;
        "backup")
            backup_config
            ;;
        "status")
            show_status
            ;;
        "test")
            test_targets
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  validate  - Validate Prometheus configuration"
            echo "  reload    - Reload Prometheus configuration"
            echo "  restart   - Restart Prometheus service"
            echo "  add       - Add new targets (requires service_name and port)"
            echo "  backup    - Create configuration backup"
            echo "  status    - Show Prometheus status"
            echo "  test      - Test Prometheus targets"
            echo "  help      - Show this help"
            ;;
        *)
            log_info "Available commands:"
            echo "  $0 validate  - Validate configuration"
            echo "  $0 reload    - Reload configuration"
            echo "  $0 status    - Check status"
            echo "  $0 help      - Show full help"
            ;;
    esac
}

main "$@"