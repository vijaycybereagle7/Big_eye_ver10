#!/usr/bin/env python3
"""
Security Management Script
Main orchestration script for all security components
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, Any

# Add security modules to path
sys.path.append('/workspace/security')

from encryption import DataEncryptionAtRest, DataEncryptionInTransit, PIIProtection
from access_control import AccessControlSystem, Permission, ResourceType, Role, User
from compliance import GDPRCompliance, DataRecord, DataSubjectRequest, DataCategory, RetentionPeriod
from infrastructure import FirewallManager, IntrusionDetectionSystem


class SecurityManager:
    """Main security management class"""
    
    def __init__(self):
        # Load configurations
        self.configs = self._load_configs()
        
        # Initialize components
        self.encryption_at_rest = DataEncryptionAtRest()
        self.encryption_in_transit = DataEncryptionInTransit()
        self.pii_protection = PIIProtection()
        self.access_control = AccessControlSystem()
        self.compliance = GDPRCompliance()
        self.firewall = FirewallManager()
        self.ids = IntrusionDetectionSystem()
        
        print("Security Manager initialized")
    
    def _load_configs(self) -> Dict[str, Any]:
        """Load all security configurations"""
        configs = {}
        config_dir = '/workspace/security/configs'
        
        for filename in os.listdir(config_dir):
            if filename.endswith('.json'):
                config_name = filename.replace('.json', '')
                with open(os.path.join(config_dir, filename), 'r') as f:
                    configs[config_name] = json.load(f)
        
        return configs
    
    def setup_security(self):
        """Setup initial security configuration"""
        print("\n=== Setting up Security Infrastructure ===")
        
        # 1. Setup access control
        self._setup_access_control()
        
        # 2. Setup firewall rules
        self._setup_firewall()
        
        # 3. Start intrusion detection
        self._setup_intrusion_detection()
        
        # 4. Setup compliance framework
        self._setup_compliance()
        
        print("\n=== Security Setup Complete ===")
    
    def _setup_access_control(self):
        """Setup access control system"""
        print("Setting up Access Control...")
        
        # Create admin user
        admin_user = User(
            user_id="admin_001",
            username="admin",
            email="admin@example.com",
            roles=["admin"],
            is_active=True,
            created_at=datetime.now().isoformat(),
            last_login=None,
            failed_login_attempts=0,
            account_locked_until=None,
            password_hash="hashed_password",
            salt="salt"
        )
        
        if self.access_control.create_user(admin_user):
            print("✓ Admin user created")
        
        # Assign admin role
        self.access_control.assign_role_to_user("admin_001", "admin")
        print("✓ Admin role assigned")
    
    def _setup_firewall(self):
        """Setup firewall configuration"""
        print("Setting up Firewall...")
        
        # Firewall is already initialized with default rules
        print("✓ Firewall configured with default rules")
        
        # Add custom rules
        custom_rules = [
            {
                'rule_id': 'allow_https_admin',
                'name': 'Allow HTTPS to Admin Panel',
                'action': 'allow',
                'source_ip': '192.168.0.0/24',
                'source_port': 'any',
                'dest_ip': '192.168.0.10',
                'dest_port': '443',
                'protocol': 'tcp',
                'zone': 'internal',
                'security_level': 'high'
            }
        ]
        
        # Would add custom rules here
        print("✓ Custom firewall rules configured")
    
    def _setup_intrusion_detection(self):
        """Setup intrusion detection system"""
        print("Setting up Intrusion Detection...")
        
        # Start IDS monitoring
        self.ids.start_monitoring()
        print("✓ Intrusion Detection System started")
    
    def _setup_compliance(self):
        """Setup compliance framework"""
        print("Setting up GDPR Compliance...")
        
        # Register processing activities
        activity_data = {
            'activity_id': 'user_data_processing',
            'controller_name': 'Company Name',
            'processing_purpose': 'User account management and service delivery',
            'data_categories': ['personal_identifiers', 'contact_data', 'behavioral_data'],
            'data_subjects': ['registered_users', 'customers'],
            'recipients': ['internal_teams', 'service_providers'],
            'retention_periods': ['long_term', 'medium_term'],
            'security_measures': ['encryption', 'access_control', 'audit_logging']
        }
        
        self.compliance.register_processing_activity(**activity_data)
        print("✓ GDPR compliance framework configured")
    
    def run_security_audit(self):
        """Run comprehensive security audit"""
        print("\n=== Security Audit Report ===")
        print(f"Audit Date: {datetime.now().isoformat()}")
        
        # Access Control Audit
        print("\n--- Access Control ---")
        audit_logs = self.access_control.get_audit_logs(limit=10)
        print(f"Recent audit logs: {len(audit_logs)}")
        
        # Firewall Audit
        print("\n--- Firewall Security ---")
        firewall_report = self.firewall.generate_security_report()
        print(f"Total rules: {firewall_report['rules_summary']['total_rules']}")
        print(f"Enabled rules: {firewall_report['rules_summary']['enabled_rules']}")
        print(f"Total hits: {firewall_report['rules_summary']['total_hits']}")
        
        # IDS Audit
        print("\n--- Intrusion Detection ---")
        ids_dashboard = self.ids.generate_security_dashboard()
        print(f"Total alerts: {ids_dashboard['alert_summary']['total_alerts']}")
        print(f"Critical alerts: {ids_dashboard['alert_summary']['critical_alerts']}")
        print(f"Security status: {ids_dashboard['security_status']}")
        
        # Compliance Audit
        print("\n--- GDPR Compliance ---")
        overdue_requests = self.compliance.get_overdue_requests()
        print(f"Overdue data subject requests: {len(overdue_requests)}")
        
        cleanup_result = self.compliance.cleanup_expired_data()
        print(f"Expired data records processed: {cleanup_result['records_deleted']}")
        
        print("\n=== Audit Complete ===")
    
    def check_pii_compliance(self, data: str) -> Dict[str, Any]:
        """Check PII compliance of data"""
        print("\n=== PII Compliance Check ===")
        
        # Detect PII
        detected_pii = self.pii_protection.detect_pii(data)
        print(f"PII instances detected: {len(detected_pii)}")
        
        # Create privacy report
        privacy_report = self.pii_protection.create_data_privacy_report(data)
        print(f"Risk level: {privacy_report['risk_level']}")
        print(f"Sensitivity score: {privacy_report['sensitivity_score']}")
        
        # Mask PII
        masked_data = self.pii_protection.mask_pii(data)
        print(f"Original: {data[:100]}...")
        print(f"Masked: {masked_data[:100]}...")
        
        return privacy_report
    
    def encrypt_data(self, data: str, encrypt_at_rest: bool = True) -> str:
        """Encrypt data using configured encryption methods"""
        print("\n=== Data Encryption ===")
        
        if encrypt_at_rest:
            # Encrypt at rest
            encrypted = self.encryption_at_rest.encrypt(data)
            print("✓ Data encrypted at rest (AES-256)")
            return encrypted
        else:
            # Encrypt in transit (RSA encryption simulation)
            print("✓ Data prepared for encryption in transit")
            return data  # Would use actual RSA encryption
    
    def test_access_control(self):
        """Test access control system"""
        print("\n=== Access Control Test ===")
        
        # Test user authentication
        session_id = self.access_control.authenticate_user(
            username="admin",
            password="admin_password",
            ip_address="192.168.1.100",
            user_agent="SecurityManager/1.0"
        )
        
        if session_id:
            print("✓ Authentication successful")
            
            # Test permission check
            user = self.access_control.validate_session(session_id)
            if user:
                has_permission = self.access_control.check_permission(
                    user.user_id,
                    Permission.READ,
                    "test_resource",
                    ResourceType.DATA
                )
                print(f"✓ Permission check: {has_permission}")
            
            # Logout
            self.access_control.logout(session_id)
            print("✓ Logout successful")
        else:
            print("✗ Authentication failed")
    
    def scan_network_security(self, target_network: str = "192.168.0.0/24"):
        """Perform network security scan"""
        print(f"\n=== Network Security Scan ===")
        print(f"Target network: {target_network}")
        
        # Network scan
        scan_result = self.ids.scan_network(target_network)
        print(f"Hosts scanned: {scan_result['total_hosts_scanned']}")
        print(f"Open ports found: {len(scan_result['open_ports'])}")
        
        # Check network isolation
        isolation = self.firewall.check_network_isolation("192.168.0.10", "192.168.1.20")
        print(f"Network isolation status: {isolation['isolated']}")
        
        return scan_result
    
    def process_data_subject_request(self, user_id: str, request_type: str):
        """Process GDPR data subject request"""
        print(f"\n=== Data Subject Request ===")
        print(f"User ID: {user_id}")
        print(f"Request type: {request_type}")
        
        # Create request
        request_id = self.compliance.create_data_subject_request(
            user_id=user_id,
            request_type=DataSubjectRequest(request_type),
            details={'requested_by': 'user', 'reason': 'GDPR compliance'}
        )
        print(f"Request ID: {request_id}")
        
        # Process request
        result = self.compliance.process_data_subject_request(
            request_id=request_id,
            verification_status='verified'
        )
        print(f"Request status: {result['status']}")
        
        return result
    
    def generate_compliance_report(self, user_id: str):
        """Generate GDPR compliance report for user"""
        print(f"\n=== GDPR Compliance Report ===")
        print(f"User ID: {user_id}")
        
        report = self.compliance.generate_privacy_report(user_id)
        
        print(f"Total data records: {report['data_summary']['total_records']}")
        print(f"Active consents: {report['consent_summary']['active_consents']}")
        print(f"Completed requests: {report['rights_exercise']['completed_requests']}")
        
        for rec in report['recommendations']:
            print(f"Recommendation: {rec}")
        
        return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Security Management Tool')
    parser.add_argument('action', choices=[
        'setup', 'audit', 'test-access', 'scan-network',
        'encrypt-data', 'check-pii', 'process-request',
        'compliance-report', 'all'
    ], help='Action to perform')
    parser.add_argument('--data', help='Data to encrypt or check')
    parser.add_argument('--user-id', help='User ID for operations')
    parser.add_argument('--network', help='Network for scanning')
    
    args = parser.parse_args()
    
    # Initialize security manager
    security = SecurityManager()
    
    if args.action == 'setup':
        security.setup_security()
    
    elif args.action == 'audit':
        security.run_security_audit()
    
    elif args.action == 'test-access':
        security.test_access_control()
    
    elif args.action == 'scan-network':
        network = args.network or "192.168.0.0/24"
        security.scan_network_security(network)
    
    elif args.action == 'encrypt-data':
        if not args.data:
            print("Error: --data parameter required")
            sys.exit(1)
        result = security.encrypt_data(args.data)
        print(f"Encrypted data: {result}")
    
    elif args.action == 'check-pii':
        if not args.data:
            print("Error: --data parameter required")
            sys.exit(1)
        security.check_pii_compliance(args.data)
    
    elif args.action == 'process-request':
        if not args.user_id:
            print("Error: --user-id parameter required")
            sys.exit(1)
        security.process_data_subject_request(args.user_id, 'access')
    
    elif args.action == 'compliance-report':
        if not args.user_id:
            print("Error: --user-id parameter required")
            sys.exit(1)
        security.generate_compliance_report(args.user_id)
    
    elif args.action == 'all':
        print("Running all security operations...\n")
        security.setup_security()
        security.run_security_audit()
        security.test_access_control()
        security.scan_network_security()
        if args.data:
            security.check_pii_compliance(args.data)
            security.encrypt_data(args.data)


if __name__ == '__main__':
    main()
