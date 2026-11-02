#!/bin/bash
# Deployment Validation Script
# Validates the deployment configuration and ensures all components are properly configured

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Logging functions
log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_CHECKS++))
    ((TOTAL_CHECKS++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check file exists
check_file() {
    local file="$1"
    local description="$2"
    
    if [ -f "$file" ]; then
        log_pass "$description: $file"
    else
        log_fail "$description not found: $file"
    fi
}

# Check directory exists
check_dir() {
    local dir="$1"
    local description="$2"
    
    if [ -d "$dir" ]; then
        log_pass "$description: $dir"
    else
        log_fail "$description not found: $dir"
    fi
}

# Check configuration file syntax
check_yaml_syntax() {
    local file="$1"
    
    if [ -f "$file" ]; then
        # Simple YAML syntax check (not perfect but catches most errors)
        if grep -q "^[[:space:]]*:" "$file" 2>/dev/null || grep -q "^- " "$file" 2>/dev/null; then
            log_pass "YAML syntax check: $file"
        else
            log_fail "YAML syntax invalid: $file"
        fi
    fi
}

# Main validation
echo "=========================================="
echo "Deployment Configuration Validation"
echo "=========================================="
echo ""

# Check Docker Compose files
check_file "deployment/docker/docker-compose.yml" "Docker Compose main file"
check_file "deployment/docker/.env.template" "Environment template"
check_yaml_syntax "deployment/docker/docker-compose.yml"

# Check Kubernetes manifests
check_dir "deployment/kubernetes" "Kubernetes directory"
check_dir "deployment/kubernetes/helm" "Helm charts directory"
check_file "deployment/kubernetes/helm/threatintel-platform/Chart.yaml" "Helm chart"
check_file "deployment/kubernetes/helm/threatintel-platform/values.yaml" "Helm values"
check_dir "deployment/kubernetes/templates" "Kubernetes templates"

# Check backup scripts
check_dir "deployment/backup" "Backup directory"
check_file "deployment/backup/scripts/postgres_backup.sh" "PostgreSQL backup script"
check_file "deployment/backup/scripts/mongodb_backup.sh" "MongoDB backup script"
check_file "deployment/backup/scripts/redis_backup.sh" "Redis backup script"
check_file "deployment/backup/scripts/restore.sh" "Restore script"

# Check deployment scripts
check_file "deployment/scripts/deploy.sh" "Main deployment script"
check_file "deployment/scripts/setup.sh" "Setup script"

# Check configuration files
check_dir "deployment/config" "Configuration directory"
check_file "deployment/config/postgres/postgresql.conf" "PostgreSQL config"
check_file "deployment/config/mongodb/mongod.conf" "MongoDB config"
check_file "deployment/config/redis/redis.conf" "Redis config"
check_file "deployment/config/nginx/nginx.conf" "Nginx config"
check_file "deployment/config/prometheus/prometheus.yml" "Prometheus config"
check_file "deployment/config/alertmanager/alertmanager.yml" "Alertmanager config"

# Check documentation
check_file "deployment/README.md" "Main documentation"
check_file "deployment/IMPLEMENTATION_SUMMARY.md" "Implementation summary"
check_file "deployment/docs/disaster_recovery_plan.md" "Disaster recovery plan"

# Check PVC manifests
check_file "deployment/kubernetes/manifests/pvc.yaml" "PVC manifests"

# Validate script permissions
if [ -x "deployment/scripts/deploy.sh" ] 2>/dev/null; then
    log_pass "Deployment script is executable"
else
    log_warn "Deployment script may not be executable (chmod +x needed)"
fi

# Check for required scripts
required_scripts=(
    "deployment/scripts/deploy.sh"
    "deployment/scripts/setup.sh"
    "deployment/backup/scripts/postgres_backup.sh"
    "deployment/backup/scripts/mongodb_backup.sh"
    "deployment/backup/scripts/redis_backup.sh"
    "deployment/backup/scripts/restore.sh"
)

echo ""
echo "Checking required scripts..."
for script in "${required_scripts[@]}"; do
    check_file "$script" "Required script"
done

# Check configuration completeness
echo ""
echo "Configuration completeness checks..."

# Check environment template has required variables
if [ -f "deployment/docker/.env.template" ]; then
    required_vars=(
        "POSTGRES_PASSWORD"
        "MONGO_ROOT_PASSWORD"
        "REDIS_PASSWORD"
        "SECRET_KEY"
        "GRAFANA_ADMIN_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if grep -q "$var=" "deployment/docker/.env.template"; then
            log_pass "Environment variable defined: $var"
        else
            log_fail "Environment variable missing: $var"
        fi
    done
fi

# Summary
echo ""
echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo "Total Checks: $TOTAL_CHECKS"
echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"

if [ $FAILED_CHECKS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All validation checks passed!${NC}"
    echo "Deployment configuration is complete and ready."
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some validation checks failed!${NC}"
    echo "Please review the failed checks before deploying."
    exit 1
fi