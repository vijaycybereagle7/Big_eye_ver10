#!/usr/bin/env python3
"""
Security Monitoring Script
Real-time monitoring and alerting for security events
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.append('/workspace/security')

from access_control import AccessControlSystem
from infrastructure import IntrusionDetectionSystem
from compliance import GDPRCompliance


class SecurityMonitor:
    """Real-time security monitoring system"""
    
    def __init__(self):
        self.access_control = AccessControlSystem()
        self.ids = IntrusionDetectionSystem()
        self.compliance = GDPRCompliance()
        self.monitoring_active = False
        self.alert_handlers = []
        
    def add_alert_handler(self, handler):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
    
    def start_monitoring(self, interval: int = 60):
        """Start continuous monitoring"""
        print(f"Starting security monitoring (interval: {interval}s)")
        self.monitoring_active = True
        
        # Start monitoring threads
        threading.Thread(target=self._monitor_failed_logins, daemon=True).start()
        threading.Thread(target=self._monitor_intrusion_alerts, daemon=True).start()
        threading.Thread(target=self._monitor_compliance, daemon=True).start()
        threading.Thread(target=self._monitor_audit_logs, daemon=True).start()
        
        # Main monitoring loop
        while self.monitoring_active:
            time.sleep(interval)
            self._generate_monitoring_report()
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        print("Security monitoring stopped")
    
    def _monitor_failed_logins(self):
        """Monitor failed login attempts"""
        while self.monitoring_active:
            try:
                # Check recent audit logs for failed logins
                recent_logs = self.access_control.get_audit_logs(
                    start_date=(datetime.now() - timedelta(hours=1)).isoformat(),
                    limit=100
                )
                
                failed_logins = [log for log in recent_logs 
                               if log['action'] == 'LOGIN_FAILED']
                
                if failed_logins:
                    self._send_alert({
                        'type': 'failed_logins',
                        'count': len(failed_logins),
                        'sources': list(set(log['user_id'] for log in failed_logins)),
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'high' if len(failed_logins) > 10 else 'medium'
                    })
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Failed login monitoring error: {e}")
    
    def _monitor_intrusion_alerts(self):
        """Monitor intrusion detection alerts"""
        while self.monitoring_active:
            try:
                # Get new alerts
                alerts = self.ids.get_alerts(status='new', limit=10)
                
                for alert in alerts:
                    self._send_alert({
                        'type': 'intrusion_alert',
                        'alert_id': alert['alert_id'],
                        'severity': alert['severity'],
                        'description': alert['description'],
                        'source_ip': alert['source_ip'],
                        'timestamp': alert['timestamp']
                    })
                
                # Check for critical alerts
                critical_alerts = self.ids.get_alerts(
                    severity='critical',
                    limit=5
                )
                
                if critical_alerts:
                    self._send_alert({
                        'type': 'critical_security_alert',
                        'count': len(critical_alerts),
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'critical'
                    })
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"IDS monitoring error: {e}")
    
    def _monitor_compliance(self):
        """Monitor GDPR compliance status"""
        while self.monitoring_active:
            try:
                # Check for overdue data subject requests
                overdue = self.compliance.get_overdue_requests()
                
                if overdue:
                    self._send_alert({
                        'type': 'compliance_violation',
                        'description': f'{len(overdue)} overdue data subject requests',
                        'count': len(overdue),
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'high'
                    })
                
                # Check for expired data
                cleanup_result = self.compliance.cleanup_expired_data()
                if cleanup_result['records_deleted'] > 0:
                    self._send_alert({
                        'type': 'data_cleanup',
                        'description': f'Auto-deleted {cleanup_result["records_deleted"]} expired records',
                        'count': cleanup_result['records_deleted'],
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'info'
                    })
                
                time.sleep(3600)  # Check every hour
                
            except Exception as e:
                print(f"Compliance monitoring error: {e}")
    
    def _monitor_audit_logs(self):
        """Monitor audit logs for suspicious activities"""
        while self.monitoring_active:
            try:
                # Check recent audit logs
                recent_logs = self.access_control.get_audit_logs(
                    start_date=(datetime.now() - timedelta(minutes=30)).isoformat(),
                    limit=50
                )
                
                # Check for permission denied events
                denied_events = [log for log in recent_logs 
                               if log['action'] == 'PERMISSION_DENIED']
                
                if denied_events:
                    # Group by user
                    users_deny_count = {}
                    for log in denied_events:
                        user = log['user_id']
                        users_deny_count[user] = users_deny_count.get(user, 0) + 1
                    
                    # Alert if user has many denied attempts
                    for user, count in users_deny_count.items():
                        if count > 5:
                            self._send_alert({
                                'type': 'suspicious_activity',
                                'user_id': user,
                                'denied_attempts': count,
                                'timestamp': datetime.now().isoformat(),
                                'severity': 'medium'
                            })
                
                # Check for role changes
                role_changes = [log for log in recent_logs 
                              if log['action'] in ['ROLE_ASSIGNED', 'ROLE_REVOKED']]
                
                if role_changes:
                    self._send_alert({
                        'type': 'role_change',
                        'changes': len(role_changes),
                        'timestamp': datetime.now().isoformat(),
                        'severity': 'medium'
                    })
                
                time.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                print(f"Audit monitoring error: {e}")
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Send alert to all handlers"""
        print(f"ALERT [{alert['severity'].upper()}]: {alert['type']} - {alert.get('description', '')}")
        
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                print(f"Alert handler error: {e}")
    
    def _generate_monitoring_report(self):
        """Generate monitoring report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'access_control': {
                    'recent_logs': len(self.access_control.get_audit_logs(
                        start_date=(datetime.now() - timedelta(hours=1)).isoformat()
                    ))
                },
                'intrusion_detection': self.ids.generate_security_dashboard(),
                'compliance': {
                    'overdue_requests': len(self.compliance.get_overdue_requests())
                }
            }
            
            # Save report
            report_path = f"/workspace/security/logs/monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
        except Exception as e:
            print(f"Report generation error: {e}")


def console_alert_handler(alert: Dict[str, Any]):
    """Console alert handler"""
    timestamp = alert['timestamp']
    severity = alert['severity'].upper()
    
    if severity == 'CRITICAL':
        print(f"\n🚨 CRITICAL ALERT [{timestamp}]: {alert['type']}")
        print(f"   {alert.get('description', '')}\n")
    elif severity == 'HIGH':
        print(f"\n⚠️  HIGH ALERT [{timestamp}]: {alert['type']}")
        print(f"   {alert.get('description', '')}\n")


def file_alert_handler(alert: Dict[str, Any]):
    """File alert handler"""
    log_path = "/workspace/security/logs/security_alerts.log"
    
    with open(log_path, 'a') as f:
        f.write(f"{json.dumps(alert)}\n")


def main():
    """Main entry point"""
    monitor = SecurityMonitor()
    
    # Add alert handlers
    monitor.add_alert_handler(console_alert_handler)
    monitor.add_alert_handler(file_alert_handler)
    
    print("Security Monitor Started")
    print("Press Ctrl+C to stop")
    
    try:
        # Start monitoring
        monitor.start_monitoring(interval=60)
    except KeyboardInterrupt:
        print("\nStopping security monitoring...")
        monitor.stop_monitoring()


if __name__ == '__main__':
    main()
