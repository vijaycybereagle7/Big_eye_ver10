#!/usr/bin/env python3
"""
Security Monitor
Monitors security events and threats
"""

import time
import json
import logging
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Counter, Gauge, Histogram
import redis
import psycopg2
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus metrics for security monitoring
security_events_total = Counter('security_events_total', 'Total security events', ['event_type', 'severity'])
failed_login_attempts_total = Counter('failed_login_attempts_total', 'Failed login attempts', ['source', 'user'])
suspicious_api_requests_total = Counter('suspicious_api_requests_total', 'Suspicious API requests', ['endpoint', 'reason'])
malicious_ip_detections_total = Counter('malicious_ip_detections_total', 'Malicious IP detections', ['source', 'threat_type'])
rate_limit_violations_total = Counter('rate_limit_violations_total', 'Rate limit violations', ['endpoint'])
authentication_failures_total = Counter('authentication_failures_total', 'Authentication failures', ['method'])
security_scan_detections_total = Counter('security_scan_detections_total', 'Security scan detections', ['scan_type'])
sql_injection_attempts_total = Counter('sql_injection_attempts_total', 'SQL injection attempts', ['endpoint'])
xss_attempts_total = Counter('xss_attempts_total', 'XSS attempts', ['endpoint'])
malware_detection_total = Counter('malware_detection_total', 'Malware detections', ['malware_type', 'source'])

# Gauges for current security state
active_threats = Gauge('active_threats', 'Number of active threats', ['threat_category'])
security_level = Gauge('security_level', 'Current security level (1-5)', [])

class SecurityMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.db_connection = self.init_database()
        self.threat_ip_list = set()
        self.load_blocked_ips()
        
    def init_database(self):
        """Initialize database connection"""
        try:
            conn = psycopg2.connect(
                host='postgres',
                database='cybersecurity_api',
                user='api_user',
                password='api_password'
            )
            logger.info("Database connection established")
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def load_blocked_ips(self):
        """Load blocked IP addresses from database"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT ip_address FROM blocked_ips WHERE active = true")
                blocked_ips = cursor.fetchall()
                self.threat_ip_list = {ip[0] for ip in blocked_ips}
                cursor.close()
                logger.info(f"Loaded {len(self.threat_ip_list)} blocked IPs")
        except Exception as e:
            logger.error(f"Error loading blocked IPs: {e}")
    
    def check_failed_login_patterns(self):
        """Check for patterns in failed login attempts"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                # Check for brute force attempts
                cursor.execute("""
                    SELECT 
                        source_ip,
                        COUNT(*) as attempt_count,
                        MAX(timestamp) as last_attempt
                    FROM authentication_logs 
                    WHERE success = false 
                      AND timestamp > NOW() - INTERVAL '1 hour'
                    GROUP BY source_ip
                    HAVING COUNT(*) > 10
                """)
                
                brute_force_attempts = cursor.fetchall()
                for source_ip, count, last_attempt in brute_force_attempts:
                    failed_login_attempts_total.labels(source=source_ip, user='unknown').inc(count)
                    security_events_total.labels(event_type='brute_force', severity='high').inc()
                    
                    logger.warning(f"Potential brute force attack from {source_ip}: {count} attempts")
                    
                    # Add IP to threat list
                    self.threat_ip_list.add(source_ip)
                    
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error checking failed login patterns: {e}")
    
    def detect_suspicious_api_activity(self):
        """Detect suspicious API activity patterns"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                # Check for rapid API requests
                cursor.execute("""
                    SELECT 
                        client_ip,
                        endpoint,
                        COUNT(*) as request_count,
                        AVG(response_time) as avg_response_time
                    FROM api_logs 
                    WHERE timestamp > NOW() - INTERVAL '5 minutes'
                    GROUP BY client_ip, endpoint
                    HAVING COUNT(*) > 50
                """)
                
                rapid_requests = cursor.fetchall()
                for client_ip, endpoint, count, avg_time in rapid_requests:
                    suspicious_api_requests_total.labels(
                        endpoint=endpoint, 
                        reason='rapid_requests'
                    ).inc(count)
                    
                    rate_limit_violations_total.labels(endpoint=endpoint).inc()
                    security_events_total.labels(event_type='rapid_requests', severity='medium').inc()
                    
                    logger.warning(f"Suspicious API activity from {client_ip} to {endpoint}: {count} requests")
                
                # Check for unusual request patterns
                cursor.execute("""
                    SELECT 
                        client_ip,
                        user_agent,
                        COUNT(*) as unique_endpoints
                    FROM api_logs 
                    WHERE timestamp > NOW() - INTERVAL '10 minutes'
                    GROUP BY client_ip, user_agent
                    HAVING COUNT(DISTINCT endpoint) > 20
                """)
                
                unusual_patterns = cursor.fetchall()
                for client_ip, user_agent, unique_endpoints in unusual_patterns:
                    suspicious_api_requests_total.labels(
                        endpoint='multiple', 
                        reason='unusual_pattern'
                    ).inc(unique_endpoints)
                    
                    security_events_total.labels(event_type='unusual_pattern', severity='medium').inc()
                    
                    logger.warning(f"Unusual request pattern from {client_ip}: {unique_endpoints} different endpoints")
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error detecting suspicious API activity: {e}")
    
    def check_malicious_indicators(self):
        """Check for malicious indicators in requests"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                # Check for SQL injection patterns
                sql_patterns = [
                    "union select",
                    "drop table",
                    "insert into",
                    "update set",
                    "delete from",
                    "alter table",
                    "create table"
                ]
                
                for pattern in sql_patterns:
                    cursor.execute("""
                        SELECT 
                            client_ip,
                            endpoint,
                            COUNT(*) as attempt_count
                        FROM api_logs 
                        WHERE request_body ILIKE %s
                          AND timestamp > NOW() - INTERVAL '1 hour'
                        GROUP BY client_ip, endpoint
                    """, (f"%{pattern}%",))
                    
                    sql_attempts = cursor.fetchall()
                    for client_ip, endpoint, count in sql_attempts:
                        sql_injection_attempts_total.labels(endpoint=endpoint).inc(count)
                        security_events_total.labels(event_type='sql_injection', severity='critical').inc()
                        
                        logger.warning(f"SQL injection attempt from {client_ip} to {endpoint}: {pattern}")
                
                # Check for XSS patterns
                xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]
                
                for pattern in xss_patterns:
                    cursor.execute("""
                        SELECT 
                            client_ip,
                            endpoint,
                            COUNT(*) as attempt_count
                        FROM api_logs 
                        WHERE request_body ILIKE %s
                          AND timestamp > NOW() - INTERVAL '1 hour'
                        GROUP BY client_ip, endpoint
                    """, (f"%{pattern}%",))
                    
                    xss_attempts = cursor.fetchall()
                    for client_ip, endpoint, count in xss_attempts:
                        xss_attempts_total.labels(endpoint=endpoint).inc(count)
                        security_events_total.labels(event_type='xss_attempt', severity='high').inc()
                        
                        logger.warning(f"XSS attempt from {client_ip} to {endpoint}: {pattern}")
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error checking malicious indicators: {e}")
    
    def monitor_threat_feeds(self):
        """Monitor external threat feeds for new threats"""
        try:
            # This would integrate with your threat intelligence feeds
            # For demonstration, we'll simulate threat feed monitoring
            
            # Simulate threat feed results
            test_threats = [
                {'ip': '192.168.1.100', 'type': 'malicious_ip', 'source': 'abuseipdb'},
                {'ip': '10.0.0.50', 'type': 'botnet', 'source': 'virustotal'},
                {'ip': '172.16.0.25', 'type': 'suspicious_ip', 'source': 'greynoise'}
            ]
            
            for threat in test_threats:
                if threat['ip'] not in self.threat_ip_list:
                    malicious_ip_detections_total.labels(
                        source=threat['source'], 
                        threat_type=threat['type']
                    ).inc()
                    
                    self.threat_ip_list.add(threat['ip'])
                    security_events_total.labels(
                        event_type='threat_detected', 
                        severity='high'
                    ).inc()
                    
                    logger.warning(f"New threat detected: {threat['ip']} ({threat['type']}) from {threat['source']}")
            
        except Exception as e:
            logger.error(f"Error monitoring threat feeds: {e}")
    
    def calculate_security_level(self):
        """Calculate overall security level based on recent events"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                # Get recent high-severity events
                cursor.execute("""
                    SELECT 
                        COUNT(*) as event_count
                    FROM security_events 
                    WHERE severity IN ('high', 'critical')
                      AND timestamp > NOW() - INTERVAL '1 hour'
                """)
                
                result = cursor.fetchone()
                high_severity_events = result[0] if result else 0
                
                # Calculate security level (1-5 scale)
                if high_severity_events == 0:
                    level = 1
                elif high_severity_events <= 5:
                    level = 2
                elif high_severity_events <= 15:
                    level = 3
                elif high_severity_events <= 30:
                    level = 4
                else:
                    level = 5
                
                security_level.set(level)
                
                # Set threat category gauges
                cursor.execute("""
                    SELECT 
                        threat_category,
                        COUNT(*) as active_count
                    FROM active_threats
                    WHERE last_seen > NOW() - INTERVAL '1 hour'
                    GROUP BY threat_category
                """)
                
                threat_counts = cursor.fetchall()
                for category, count in threat_counts:
                    active_threats.labels(threat_category=category).set(count)
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error calculating security level: {e}")
    
    def block_threat_ips(self):
        """Automatically block IPs with high threat scores"""
        try:
            # Add IPs with multiple security events to blocked list
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                cursor.execute("""
                    SELECT 
                        source_ip,
                        COUNT(*) as event_count
                    FROM security_events 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                      AND source_ip NOT IN (SELECT ip_address FROM blocked_ips WHERE active = true)
                    GROUP BY source_ip
                    HAVING COUNT(*) >= 5
                """)
                
                ips_to_block = cursor.fetchall()
                for source_ip, event_count in ips_to_block:
                    cursor.execute("""
                        INSERT INTO blocked_ips (ip_address, reason, active, created_at)
                        VALUES (%s, %s, true, NOW())
                    """, (source_ip, f'Automated block: {event_count} security events'))
                    
                    logger.warning(f"Automatically blocked IP {source_ip} due to {event_count} security events")
                
                self.db_connection.commit()
                cursor.close()
                
                # Reload blocked IPs
                self.load_blocked_ips()
                
        except Exception as e:
            logger.error(f"Error blocking threat IPs: {e}")
    
    def monitor_security_events(self):
        """Main security monitoring loop"""
        logger.info("Starting security monitoring...")
        
        while True:
            try:
                logger.info("Running security monitoring cycle...")
                
                # Check for various security threats
                self.check_failed_login_patterns()
                self.detect_suspicious_api_activity()
                self.check_malicious_indicators()
                self.monitor_threat_feeds()
                
                # Calculate security metrics
                self.calculate_security_level()
                
                # Auto-block high-threat IPs
                self.block_threat_ips()
                
                logger.info("Security monitoring cycle completed")
                
            except Exception as e:
                logger.error(f"Error in security monitoring: {e}")
            
            # Wait before next monitoring cycle
            time.sleep(60)  # Check every minute
    
    def run(self):
        """Start the security monitor"""
        # Start Prometheus metrics server
        start_http_server(9090)
        logger.info("Prometheus metrics server started on port 9090")
        
        # Start monitoring
        self.monitor_security_events()

def main():
    """Main function"""
    monitor = SecurityMonitor()
    monitor.run()

if __name__ == '__main__':
    main()