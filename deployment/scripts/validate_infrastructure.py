#!/usr/bin/env python3
"""
Threat Intelligence Platform Infrastructure Validation Script
Validates that all deployment components are properly configured
"""

import os
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

class InfrastructureValidator:
    def __init__(self, deployment_dir: str = "/workspace/deployment"):
        self.deployment_dir = Path(deployment_dir)
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_checks = 0

    def log_success(self, message: str):
        self.success_count += 1
        print(f"✅ {message}")

    def log_error(self, message: str):
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def validate_directory_structure(self) -> bool:
        """Validate deployment directory structure"""
        self.total_checks += 1
        print("\n📁 Validating Directory Structure...")
        
        required_dirs = [
            "docker",
            "kubernetes",
            "config",
            "backup",
            "docs",
            "scripts"
        ]
        
        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = self.deployment_dir / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
            else:
                self.log_success(f"Directory exists: {dir_name}")
        
        if missing_dirs:
            self.log_error(f"Missing directories: {', '.join(missing_dirs)}")
            return False
        
        return True

    def validate_docker_compose(self) -> bool:
        """Validate docker-compose.yml configuration"""
        self.total_checks += 1
        print("\n🐳 Validating Docker Compose Configuration...")
        
        compose_file = self.deployment_dir / "docker" / "docker-compose.yml"
        
        if not compose_file.exists():
            self.log_error("docker-compose.yml not found")
            return False
        
        try:
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            # Check required services
            required_services = [
                'postgres-timescaledb',
                'mongodb',
                'redis',
                'fastapi-app',
                'celery-worker',
                'celery-beat',
                'nginx',
                'prometheus',
                'grafana',
                'elasticsearch',
                'kibana',
                'logstash',
                'alertmanager',
                'victoria-metrics'
            ]
            
            services = compose_config.get('services', {})
            for service in required_services:
                if service in services:
                    self.log_success(f"Service configured: {service}")
                else:
                    self.log_error(f"Missing service: {service}")
            
            # Check networks
            networks = compose_config.get('networks', {})
            if 'app-network' in networks and 'backend-network' in networks and \
               'database-network' in networks and 'monitoring-network' in networks:
                self.log_success("All required networks configured")
            else:
                self.log_warning("Some networks may be missing")
            
            # Check volumes
            volumes = compose_config.get('volumes', {})
            if len(volumes) >= 8:
                self.log_success(f"Volumes configured: {len(volumes)}")
            else:
                self.log_warning(f"Volume count may be insufficient: {len(volumes)}")
            
            return True
            
        except yaml.YAMLError as e:
            self.log_error(f"Invalid YAML in docker-compose.yml: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error validating docker-compose.yml: {e}")
            return False

    def validate_environment_template(self) -> bool:
        """Validate environment template configuration"""
        self.total_checks += 1
        print("\n🔧 Validating Environment Template...")
        
        env_file = self.deployment_dir / "docker" / ".env.template"
        
        if not env_file.exists():
            self.log_error(".env.template not found")
            return False
        
        required_vars = [
            'POSTGRES_PASSWORD',
            'MONGO_ROOT_PASSWORD',
            'REDIS_PASSWORD',
            'SECRET_KEY',
            'GRAFANA_ADMIN_PASSWORD',
            'VICTORIAMETRICS_RETENTION_PERIOD'
        ]
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        missing_vars = []
        for var in required_vars:
            if var in env_content:
                self.log_success(f"Environment variable: {var}")
            else:
                missing_vars.append(var)
        
        if missing_vars:
            self.log_error(f"Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check for insecure default values
        if 'CHANGE_ME' in env_content:
            self.log_warning("Found 'CHANGE_ME' placeholders - must be replaced in production")
        
        return True

    def validate_kubernetes_config(self) -> bool:
        """Validate Kubernetes configuration"""
        self.total_checks += 1
        print("\n☸️  Validating Kubernetes Configuration...")
        
        helm_dir = self.deployment_dir / "kubernetes" / "helm"
        manifests_dir = self.deployment_dir / "kubernetes" / "manifests"
        
        if not helm_dir.exists():
            self.log_error("Helm charts directory not found")
            return False
        
        # Check Helm chart structure
        chart_yaml = helm_dir / "threatintel-platform" / "Chart.yaml"
        values_yaml = helm_dir / "threatintel-platform" / "values.yaml"
        
        if chart_yaml.exists():
            self.log_success("Helm Chart.yaml exists")
        else:
            self.log_error("Helm Chart.yaml missing")
        
        if values_yaml.exists():
            self.log_success("Helm values.yaml exists")
        else:
            self.log_error("Helm values.yaml missing")
        
        # Check Kubernetes manifests
        if manifests_dir.exists():
            self.log_success("Kubernetes manifests directory exists")
            manifest_files = list(manifests_dir.glob("*.yaml"))
            if len(manifest_files) > 0:
                self.log_success(f"Found {len(manifest_files)} manifest files")
            else:
                self.log_warning("No manifest files found")
        else:
            self.log_warning("Kubernetes manifests directory not found")
        
        return True

    def validate_backup_scripts(self) -> bool:
        """Validate backup scripts"""
        self.total_checks += 1
        print("\n💾 Validating Backup Scripts...")
        
        backup_scripts_dir = self.deployment_dir / "backup" / "scripts"
        
        if not backup_scripts_dir.exists():
            self.log_error("Backup scripts directory not found")
            return False
        
        required_scripts = [
            'postgres_backup.sh',
            'mongodb_backup.sh',
            'redis_backup.sh',
            'restore.sh'
        ]
        
        missing_scripts = []
        for script in required_scripts:
            script_path = backup_scripts_dir / script
            if script_path.exists() and script_path.stat().st_mode & 0o111:
                self.log_success(f"Backup script exists and executable: {script}")
            elif script_path.exists():
                self.log_warning(f"Backup script exists but not executable: {script}")
            else:
                missing_scripts.append(script)
        
        if missing_scripts:
            self.log_error(f"Missing backup scripts: {', '.join(missing_scripts)}")
            return False
        
        return True

    def validate_monitoring_config(self) -> bool:
        """Validate monitoring configuration"""
        self.total_checks += 1
        print("\n📊 Validating Monitoring Configuration...")
        
        config_dir = self.deployment_dir / "config"
        
        # Check Prometheus config
        prometheus_config = config_dir / "prometheus" / "prometheus.yml"
        if prometheus_config.exists():
            self.log_success("Prometheus configuration exists")
        else:
            self.log_error("Prometheus configuration missing")
        
        # Check Grafana provisioning
        grafana_provisioning = config_dir / "grafana" / "provisioning"
        if grafana_provisioning.exists():
            self.log_success("Grafana provisioning directory exists")
        else:
            self.log_warning("Grafana provisioning directory missing")
        
        # Check Alertmanager config
        alertmanager_config = config_dir / "alertmanager" / "alertmanager.yml"
        if alertmanager_config.exists():
            self.log_success("Alertmanager configuration exists")
        else:
            self.log_error("Alertmanager configuration missing")
        
        return True

    def validate_logging_config(self) -> bool:
        """Validate logging configuration"""
        self.total_checks += 1
        print("\n📝 Validating Logging Configuration...")
        
        config_dir = self.deployment_dir / "config"
        
        # Check Elasticsearch config
        elasticsearch_dir = config_dir / "elasticsearch"
        if elasticsearch_dir.exists():
            self.log_success("Elasticsearch configuration directory exists")
        else:
            self.log_warning("Elasticsearch configuration directory missing")
        
        # Check Kibana config
        kibana_dir = config_dir / "kibana"
        if kibana_dir.exists():
            self.log_success("Kibana configuration directory exists")
        else:
            self.log_warning("Kibana configuration directory missing")
        
        # Check Logstash config
        logstash_config = config_dir / "logstash"
        if logstash_config.exists():
            self.log_success("Logstash configuration exists")
            # Check for pipeline and config
            pipeline = logstash_config / "pipeline" / "logstash.conf"
            if pipeline.exists():
                self.log_success("Logstash pipeline configuration exists")
            else:
                self.log_warning("Logstash pipeline configuration missing")
        else:
            self.log_error("Logstash configuration missing")
        
        return True

    def validate_documentation(self) -> bool:
        """Validate documentation completeness"""
        self.total_checks += 1
        print("\n📚 Validating Documentation...")
        
        docs_dir = self.deployment_dir / "docs"
        
        required_docs = [
            "README.md",
            "aws-deployment-guide.md",
            "gcp-deployment-guide.md",
            "azure-deployment-guide.md",
            "production_deployment_guide.md",
            "comprehensive_disaster_recovery_plan.md"
        ]
        
        missing_docs = []
        for doc in required_docs:
            if doc == "README.md":
                # README is in the deployment root
                doc_path = self.deployment_dir / doc
            else:
                # Other docs are in docs directory
                doc_path = docs_dir / doc
            
            if doc_path.exists() and doc_path.stat().st_size > 0:
                self.log_success(f"Documentation exists: {doc}")
            else:
                missing_docs.append(doc)
        
        if missing_docs:
            self.log_error(f"Missing documentation: {', '.join(missing_docs)}")
            return False
        
        return True

    def validate_security_config(self) -> bool:
        """Validate security configuration"""
        self.total_checks += 1
        print("\n🔒 Validating Security Configuration...")
        
        # Check for SSL configuration in nginx
        nginx_config = self.deployment_dir / "config" / "nginx" / "nginx.conf"
        if nginx_config.exists():
            with open(nginx_config, 'r') as f:
                content = f.read()
            
            if 'ssl' in content.lower():
                self.log_success("SSL/TLS configuration found in Nginx")
            else:
                self.log_warning("SSL/TLS configuration may be missing in Nginx")
        
        # Check for network policies in Kubernetes
        k8s_manifests = self.deployment_dir / "kubernetes" / "manifests"
        if k8s_manifests.exists():
            network_policy = k8s_manifests / "network-policy.yaml"
            if network_policy.exists():
                self.log_success("Network policies configured for Kubernetes")
            else:
                self.log_warning("Network policies may be missing for Kubernetes")
        
        return True

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print("="*80)
        print("🔍 THREAT INTELLIGENCE PLATFORM - INFRASTRUCTURE VALIDATION")
        print("="*80)
        
        validations = [
            self.validate_directory_structure,
            self.validate_docker_compose,
            self.validate_environment_template,
            self.validate_kubernetes_config,
            self.validate_backup_scripts,
            self.validate_monitoring_config,
            self.validate_logging_config,
            self.validate_documentation,
            self.validate_security_config
        ]
        
        all_passed = True
        for validation in validations:
            try:
                result = validation()
                if not result:
                    all_passed = False
            except Exception as e:
                self.log_error(f"Validation error: {e}")
                all_passed = False
        
        # Print summary
        print("\n" + "="*80)
        print("📊 VALIDATION SUMMARY")
        print("="*80)
        print(f"✅ Successful Checks: {self.success_count}")
        print(f"❌ Errors: {len(self.errors)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📋 Total Checks: {self.total_checks}")
        
        if all_passed and len(self.errors) == 0:
            print("\n🎉 INFRASTRUCTURE VALIDATION PASSED!")
            print("The deployment is ready for production use.")
        else:
            print("\n⚠️  INFRASTRUCTURE VALIDATION COMPLETED WITH ISSUES")
            if self.errors:
                print("\n❌ ERRORS TO FIX:")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
            
            if self.warnings:
                print("\n⚠️  WARNINGS TO REVIEW:")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
        
        return {
            "success": all_passed and len(self.errors) == 0,
            "success_count": self.success_count,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "total_checks": self.total_checks,
            "errors": self.errors,
            "warnings": self.warnings
        }

def main():
    """Main validation function"""
    validator = InfrastructureValidator()
    results = validator.run_all_validations()
    
    # Exit with appropriate code
    if results["success"]:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
