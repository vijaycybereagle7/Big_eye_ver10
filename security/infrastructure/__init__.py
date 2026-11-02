"""
Infrastructure Security Module
Implements firewall rules, network segmentation, and intrusion detection
"""

import os
import json
import re
import time
import socket
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ipaddress
import subprocess
import sqlite3


class SecurityLevel(Enum):
    """Security levels for rules"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(Enum):
    """Firewall rule actions"""
    ALLOW = "allow"
    DENY = "deny"
    LOG = "log"
    DROP = "drop"
    REJECT = "reject"


class NetworkZone(Enum):
    """Network zones for segmentation"""
    EXTERNAL = "external"  # Public internet
    DMZ = "dmz"  # Demilitarized zone
    INTERNAL = "internal"  # Internal network
    SECURE = "secure"  # High security zone
    MANAGEMENT = "management"  # Management network


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IntrusionType(Enum):
    """Types of intrusions"""
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    MALWARE = "malware"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    DDoS = "ddos"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class FirewallRule:
    """Firewall rule definition"""
    rule_id: str
    name: str
    description: str
    action: RuleAction
    source_ip: str
    source_port: str
    dest_ip: str
    dest_port: str
    protocol: str
    zone: NetworkZone
    security_level: SecurityLevel
    enabled: bool
    created_at: str
    last_modified: str
    hit_count: int
    logging_enabled: bool
    
    def matches(self, source_ip: str, dest_ip: str, 
                source_port: str, dest_port: str, protocol: str) -> bool:
        """Check if rule matches network traffic"""
        if not self.enabled:
            return False
        
        # Check protocol
        if self.protocol.lower() != protocol.lower() and self.protocol != "any":
            return False
        
        # Check source IP
        if not self._ip_matches(source_ip, self.source_ip):
            return False
        
        # Check destination IP
        if not self._ip_matches(dest_ip, self.dest_ip):
            return False
        
        # Check ports (simplified matching)
        if self.source_port != "any" and source_port != self.source_port:
            return False
        
        if self.dest_port != "any" and dest_port != self.dest_port:
            return False
        
        return True
    
    def _ip_matches(self, ip: str, rule_ip: str) -> bool:
        """Check if IP matches rule pattern"""
        if rule_ip == "any" or rule_ip == "0.0.0.0/0":
            return True
        
        try:
            ip_addr = ipaddress.ip_address(ip)
            rule_addr = ipaddress.ip_network(rule_ip, strict=False)
            return ip_addr in rule_addr
        except:
            return ip == rule_ip


@dataclass
class NetworkSegment:
    """Network segment definition"""
    segment_id: str
    name: str
    zone: NetworkZone
    network_range: str
    gateway: str
    allowed_services: List[str]
    restricted_services: List[str]
    security_level: SecurityLevel
    isolation_level: int  # 1-10 (10 being most isolated)
    
    def contains_ip(self, ip: str) -> bool:
        """Check if IP is in this segment"""
        try:
            ip_addr = ipaddress.ip_address(ip)
            network = ipaddress.ip_network(self.network_range, strict=False)
            return ip_addr in network
        except:
            return False


@dataclass
class IntrusionAlert:
    """Intrusion detection alert"""
    alert_id: str
    alert_type: IntrusionType
    severity: AlertSeverity
    source_ip: str
    dest_ip: str
    timestamp: str
    description: str
    evidence: Dict[str, Any]
    status: str  # new, investigating, resolved, false_positive
    resolved_at: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FirewallManager:
    """Manages firewall rules and network access control"""
    
    def __init__(self, db_path: str = '/workspace/security/infrastructure/firewall.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
        self._create_default_rules()
    
    def _init_database(self):
        """Initialize firewall database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Firewall rules table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS firewall_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    action TEXT NOT NULL,
                    source_ip TEXT NOT NULL,
                    source_port TEXT NOT NULL,
                    dest_ip TEXT NOT NULL,
                    dest_port TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_modified TEXT NOT NULL,
                    hit_count INTEGER DEFAULT 0,
                    logging_enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Traffic logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS traffic_logs (
                    log_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    source_ip TEXT NOT NULL,
                    source_port TEXT NOT NULL,
                    dest_ip TEXT NOT NULL,
                    dest_port TEXT NOT NULL,
                    protocol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    rule_id TEXT,
                    bytes_transferred INTEGER DEFAULT 0,
                    FOREIGN KEY (rule_id) REFERENCES firewall_rules (rule_id)
                )
            ''')
            
            # Network segments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_segments (
                    segment_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    network_range TEXT NOT NULL,
                    gateway TEXT NOT NULL,
                    allowed_services TEXT NOT NULL,
                    restricted_services TEXT NOT NULL,
                    security_level TEXT NOT NULL,
                    isolation_level INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _create_default_rules(self):
        """Create default firewall rules"""
        default_rules = [
            FirewallRule(
                rule_id="allow_internal_http",
                name="Allow Internal HTTP",
                description="Allow HTTP traffic within internal network",
                action=RuleAction.ALLOW,
                source_ip="192.168.0.0/16",
                source_port="any",
                dest_ip="192.168.0.0/16",
                dest_port="80",
                protocol="tcp",
                zone=NetworkZone.INTERNAL,
                security_level=SecurityLevel.MEDIUM,
                enabled=True,
                created_at=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat(),
                hit_count=0,
                logging_enabled=True
            ),
            FirewallRule(
                rule_id="deny_external_ssh",
                name="Deny External SSH",
                description="Deny SSH from external networks",
                action=RuleAction.DENY,
                source_ip="0.0.0.0/0",
                source_port="any",
                dest_ip="192.168.0.0/16",
                dest_port="22",
                protocol="tcp",
                zone=NetworkZone.EXTERNAL,
                security_level=SecurityLevel.HIGH,
                enabled=True,
                created_at=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat(),
                hit_count=0,
                logging_enabled=True
            ),
            FirewallRule(
                rule_id="allow_https_external",
                name="Allow HTTPS External",
                description="Allow HTTPS from external networks",
                action=RuleAction.ALLOW,
                source_ip="0.0.0.0/0",
                source_port="any",
                dest_ip="192.168.1.0/24",
                dest_port="443",
                protocol="tcp",
                zone=NetworkZone.DMZ,
                security_level=SecurityLevel.MEDIUM,
                enabled=True,
                created_at=datetime.now().isoformat(),
                last_modified=datetime.now().isoformat(),
                hit_count=0,
                logging_enabled=True
            )
        ]
        
        for rule in default_rules:
            self.add_firewall_rule(rule)
    
    def add_firewall_rule(self, rule: FirewallRule) -> bool:
        """Add new firewall rule"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO firewall_rules (
                            rule_id, name, description, action, source_ip, source_port,
                            dest_ip, dest_port, protocol, zone, security_level, enabled,
                            created_at, last_modified, hit_count, logging_enabled
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        rule.rule_id, rule.name, rule.description, rule.action.value,
                        rule.source_ip, rule.source_port, rule.dest_ip, rule.dest_port,
                        rule.protocol, rule.zone.value, rule.security_level.value,
                        rule.enabled, rule.created_at, rule.last_modified,
                        rule.hit_count, rule.logging_enabled
                    ))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.IntegrityError:
                return False
    
    def get_firewall_rule(self, rule_id: str) -> Optional[FirewallRule]:
        """Get firewall rule by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM firewall_rules WHERE rule_id = ?', (rule_id,))
            row = cursor.fetchone()
            
            if row:
                return FirewallRule(
                    rule_id=row[0], name=row[1], description=row[2],
                    action=RuleAction(row[3]), source_ip=row[4], source_port=row[5],
                    dest_ip=row[6], dest_port=row[7], protocol=row[8],
                    zone=NetworkZone(row[9]), security_level=SecurityLevel(row[10]),
                    enabled=bool(row[11]), created_at=row[12], last_modified=row[13],
                    hit_count=row[14], logging_enabled=bool(row[15])
                )
        return None
    
    def check_access(self, source_ip: str, source_port: str, 
                    dest_ip: str, dest_port: str, protocol: str) -> Tuple[RuleAction, Optional[str]]:
        """
        Check if traffic is allowed by firewall rules
        
        Returns:
            Tuple of (action, rule_id)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM firewall_rules WHERE enabled = 1 ORDER BY security_level DESC')
            
            for row in cursor.fetchall():
                rule = FirewallRule(
                    rule_id=row[0], name=row[1], description=row[2],
                    action=RuleAction(row[3]), source_ip=row[4], source_port=row[5],
                    dest_ip=row[6], dest_port=row[7], protocol=row[8],
                    zone=NetworkZone(row[9]), security_level=SecurityLevel(row[10]),
                    enabled=bool(row[11]), created_at=row[12], last_modified=row[13],
                    hit_count=row[14], logging_enabled=bool(row[15])
                )
                
                if rule.matches(source_ip, dest_ip, source_port, dest_port, protocol):
                    # Update hit count
                    rule.hit_count += 1
                    self._update_rule_hit_count(rule.rule_id, rule.hit_count)
                    
                    # Log traffic
                    self._log_traffic(source_ip, source_port, dest_ip, dest_port, 
                                    protocol, rule.action.value, rule.rule_id)
                    
                    return rule.action, rule.rule_id
            
            # Default deny
            return RuleAction.DENY, None
    
    def _update_rule_hit_count(self, rule_id: str, hit_count: int):
        """Update rule hit count"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE firewall_rules SET hit_count = ? WHERE rule_id = ?
            ''', (hit_count, rule_id))
            conn.commit()
    
    def _log_traffic(self, source_ip: str, source_port: str, 
                    dest_ip: str, dest_port: str, protocol: str, 
                    action: str, rule_id: Optional[str]):
        """Log network traffic"""
        import secrets
        
        log_id = secrets.token_urlsafe(16)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO traffic_logs (
                    log_id, timestamp, source_ip, source_port, dest_ip, dest_port,
                    protocol, action, rule_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (log_id, datetime.now().isoformat(), source_ip, source_port,
                  dest_ip, dest_port, protocol, action, rule_id))
            conn.commit()
    
    def get_traffic_logs(self, start_time: Optional[str] = None, 
                        end_time: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get traffic logs with filtering"""
        query = "SELECT * FROM traffic_logs WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'log_id': row[0], 'timestamp': row[1], 'source_ip': row[2],
                    'source_port': row[3], 'dest_ip': row[4], 'dest_port': row[5],
                    'protocol': row[6], 'action': row[7], 'rule_id': row[8],
                    'bytes_transferred': row[9]
                })
            
            return logs
    
    def add_network_segment(self, segment: NetworkSegment) -> bool:
        """Add network segment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO network_segments (
                        segment_id, name, zone, network_range, gateway,
                        allowed_services, restricted_services, security_level,
                        isolation_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    segment.segment_id, segment.name, segment.zone.value,
                    segment.network_range, segment.gateway,
                    json.dumps(segment.allowed_services),
                    json.dumps(segment.restricted_services),
                    segment.security_level.value, segment.isolation_level
                ))
                
                conn.commit()
                return True
                
        except sqlite3.IntegrityError:
            return False
    
    def get_network_segment(self, ip_address: str) -> Optional[NetworkSegment]:
        """Get network segment containing IP address"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM network_segments')
            
            for row in cursor.fetchall():
                segment = NetworkSegment(
                    segment_id=row[0], name=row[1], zone=NetworkZone(row[2]),
                    network_range=row[3], gateway=row[4],
                    allowed_services=json.loads(row[5]),
                    restricted_services=json.loads(row[6]),
                    security_level=SecurityLevel(row[7]), isolation_level=row[8]
                )
                
                if segment.contains_ip(ip_address):
                    return segment
            
            return None
    
    def generate_security_report(self) -> Dict[str, Any]:
        """Generate firewall security report"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get rule statistics
            cursor.execute('SELECT COUNT(*) FROM firewall_rules')
            total_rules = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM firewall_rules WHERE enabled = 1')
            enabled_rules = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(hit_count) FROM firewall_rules')
            total_hits = cursor.fetchone()[0] or 0
            
            # Get traffic statistics
            cursor.execute('SELECT COUNT(*) FROM traffic_logs WHERE timestamp >= ?', 
                          ((datetime.now() - timedelta(days=1)).isoformat(),))
            daily_traffic = cursor.fetchone()[0]
            
            # Get most active rules
            cursor.execute('''
                SELECT rule_id, name, hit_count FROM firewall_rules 
                WHERE enabled = 1 ORDER BY hit_count DESC LIMIT 5
            ''')
            top_rules = [{'rule_id': row[0], 'name': row[1], 'hits': row[2]} 
                        for row in cursor.fetchall()]
            
            return {
                'report_date': datetime.now().isoformat(),
                'rules_summary': {
                    'total_rules': total_rules,
                    'enabled_rules': enabled_rules,
                    'disabled_rules': total_rules - enabled_rules,
                    'total_hits': total_hits
                },
                'traffic_summary': {
                    'daily_traffic_count': daily_traffic
                },
                'top_rules': top_rules,
                'recommendations': self._get_security_recommendations()
            }
    
    def _get_security_recommendations(self) -> List[str]:
        """Get security recommendations"""
        recommendations = []
        
        # Analyze firewall configuration
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for overly permissive rules
            cursor.execute('''
                SELECT COUNT(*) FROM firewall_rules 
                WHERE source_ip = '0.0.0.0/0' AND action = 'allow'
            ''')
            permissive_rules = cursor.fetchone()[0]
            
            if permissive_rules > 0:
                recommendations.append(f"Review {permissive_rules} rules allowing traffic from any source")
            
            # Check for disabled critical rules
            cursor.execute('''
                SELECT COUNT(*) FROM firewall_rules 
                WHERE security_level = 'critical' AND enabled = 0
            ''')
            disabled_critical = cursor.fetchone()[0]
            
            if disabled_critical > 0:
                recommendations.append(f"Enable {disabled_critical} disabled critical security rules")
        
        return recommendations


class IntrusionDetectionSystem:
    """Intrusion Detection System (IDS)"""
    
    def __init__(self, db_path: str = '/workspace/security/infrastructure/ids.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
        self.active_connections = {}  # Track active connections
        self.failed_attempts = {}  # Track failed login attempts
        self.monitoring_active = False
    
    def _init_database(self):
        """Initialize IDS database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Intrusion alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intrusion_alerts (
                    alert_id TEXT PRIMARY KEY,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    source_ip TEXT NOT NULL,
                    dest_ip TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    description TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    resolved_at TEXT
                )
            ''')
            
            # Network scan logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_scans (
                    scan_id TEXT PRIMARY KEY,
                    source_ip TEXT NOT NULL,
                    target_range TEXT NOT NULL,
                    port_scan_type TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    ports_scanned TEXT NOT NULL,
                    severity_score INTEGER DEFAULT 0
                )
            ''')
            
            # Anomaly detection logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anomalies (
                    anomaly_id TEXT PRIMARY KEY,
                    anomaly_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    auto_resolved BOOLEAN DEFAULT 0
                )
            ''')
            
            conn.commit()
    
    def start_monitoring(self):
        """Start intrusion detection monitoring"""
        self.monitoring_active = True
        
        # Start background monitoring threads
        threading.Thread(target=self._port_scan_detection, daemon=True).start()
        threading.Thread(target=self._brute_force_detection, daemon=True).start()
        threading.Thread(target=self._anomaly_detection, daemon=True).start()
    
    def stop_monitoring(self):
        """Stop intrusion detection monitoring"""
        self.monitoring_active = False
    
    def _port_scan_detection(self):
        """Detect port scanning activities"""
        scan_threshold = 10  # ports scanned within time window
        time_window = 60  # seconds
        
        while self.monitoring_active:
            try:
                # This would integrate with actual network monitoring
                # For demo, simulate scan detection
                time.sleep(10)
                
            except Exception as e:
                print(f"Port scan detection error: {e}")
    
    def _brute_force_detection(self):
        """Detect brute force attacks"""
        failure_threshold = 5  # failed attempts
        time_window = 300  # 5 minutes
        
        while self.monitoring_active:
            try:
                # Check for failed attempts
                current_time = time.time()
                for source_ip, attempts in list(self.failed_attempts.items()):
                    # Remove old attempts
                    self.failed_attempts[source_ip] = [
                        attempt_time for attempt_time in attempts 
                        if current_time - attempt_time < time_window
                    ]
                    
                    # Check if threshold exceeded
                    if len(self.failed_attempts[source_ip]) >= failure_threshold:
                        self._create_intrusion_alert(
                            source_ip=source_ip,
                            alert_type=IntrusionType.BRUTE_FORCE,
                            severity=AlertSeverity.HIGH,
                            description=f"Brute force attack detected from {source_ip}",
                            evidence={'failed_attempts': len(self.failed_attempts[source_ip])}
                        )
                        
                        # Reset counter
                        del self.failed_attempts[source_ip]
                
                time.sleep(30)
                
            except Exception as e:
                print(f"Brute force detection error: {e}")
    
    def _anomaly_detection(self):
        """Detect network anomalies"""
        while self.monitoring_active:
            try:
                # This would implement statistical anomaly detection
                # For demo, simulate anomaly detection
                time.sleep(60)
                
            except Exception as e:
                print(f"Anomaly detection error: {e}")
    
    def log_failed_attempt(self, source_ip: str):
        """Log failed authentication attempt"""
        if source_ip not in self.failed_attempts:
            self.failed_attempts[source_ip] = []
        
        self.failed_attempts[source_ip].append(time.time())
    
    def _create_intrusion_alert(self, source_ip: str, alert_type: IntrusionType,
                               severity: AlertSeverity, description: str,
                               evidence: Dict[str, Any], dest_ip: str = "unknown"):
        """Create intrusion detection alert"""
        import secrets
        
        alert_id = secrets.token_urlsafe(16)
        alert = IntrusionAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            source_ip=source_ip,
            dest_ip=dest_ip,
            timestamp=datetime.now().isoformat(),
            description=description,
            evidence=evidence,
            status="new",
            resolved_at=None
        )
        
        self.save_alert(alert)
    
    def save_alert(self, alert: IntrusionAlert):
        """Save alert to database"""
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO intrusion_alerts (
                        alert_id, alert_type, severity, source_ip, dest_ip,
                        timestamp, description, evidence, status, resolved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.alert_id, alert.alert_type.value, alert.severity.value,
                    alert.source_ip, alert.dest_ip, alert.timestamp,
                    alert.description, json.dumps(alert.evidence),
                    alert.status, alert.resolved_at
                ))
                
                conn.commit()
    
    def get_alerts(self, status: Optional[str] = None, 
                  severity: Optional[AlertSeverity] = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        """Get intrusion alerts with filtering"""
        query = "SELECT * FROM intrusion_alerts WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if severity:
            query += " AND severity = ?"
            params.append(severity.value)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    'alert_id': row[0], 'alert_type': row[1], 'severity': row[2],
                    'source_ip': row[3], 'dest_ip': row[4], 'timestamp': row[5],
                    'description': row[6], 'evidence': json.loads(row[7]),
                    'status': row[8], 'resolved_at': row[9]
                })
            
            return alerts
    
    def resolve_alert(self, alert_id: str, status: str = "resolved") -> bool:
        """Resolve intrusion alert"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE intrusion_alerts SET status = ?, resolved_at = ?
                WHERE alert_id = ?
            ''', (status, datetime.now().isoformat() if status == "resolved" else None, alert_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            return False
    
    def detect_sql_injection(self, request_data: str) -> bool:
        """Detect SQL injection patterns"""
        sql_injection_patterns = [
            r"(\bor\b|\band\b)\s+['\"].*['\"]",
            r"(union|select|insert|update|delete|drop|create|alter)",
            r"('|(\-\-)|(;)|(\|)|(\*))",
            r"(exec(\s|\+)+(s|x)p\w+)"
        ]
        
        for pattern in sql_injection_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                return True
        
        return False
    
    def detect_xss(self, request_data: str) -> bool:
        """Detect XSS patterns"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, request_data, re.IGNORECASE):
                return True
        
        return False
    
    def scan_network(self, target_network: str, ports: List[int] = None) -> Dict[str, Any]:
        """Perform network security scan"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 443, 993, 995]  # Common ports
        
        open_ports = {}
        network = ipaddress.ip_network(target_network)
        
        for ip in network.hosts():
            ip_str = str(ip)
            for port in ports:
                if self._check_port(ip_str, port):
                    if ip_str not in open_ports:
                        open_ports[ip_str] = []
                    open_ports[ip_str].append(port)
        
        return {
            'target_network': target_network,
            'scan_date': datetime.now().isoformat(),
            'open_ports': open_ports,
            'total_hosts_scanned': min(254, network.num_addresses - 2)
        }
    
    def _check_port(self, ip: str, port: int, timeout: int = 1) -> bool:
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def generate_security_dashboard(self) -> Dict[str, Any]:
        """Generate security dashboard summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Alert statistics
            cursor.execute('SELECT COUNT(*) FROM intrusion_alerts')
            total_alerts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM intrusion_alerts WHERE status = "new"')
            new_alerts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM intrusion_alerts WHERE severity = "critical"')
            critical_alerts = cursor.fetchone()[0]
            
            # Recent alerts
            cursor.execute('''
                SELECT alert_type, severity, COUNT(*) FROM intrusion_alerts 
                WHERE timestamp >= ? 
                GROUP BY alert_type, severity
            ''', ((datetime.now() - timedelta(days=7)).isoformat(),))
            
            alert_breakdown = {}
            for row in cursor.fetchall():
                key = f"{row[0]}_{row[1]}"
                alert_breakdown[key] = row[2]
            
            return {
                'dashboard_date': datetime.now().isoformat(),
                'alert_summary': {
                    'total_alerts': total_alerts,
                    'new_alerts': new_alerts,
                    'critical_alerts': critical_alerts
                },
                'alert_breakdown': alert_breakdown,
                'security_status': 'SECURE' if critical_alerts == 0 else 'WARNING'
            }


class NetworkSegmentation:
    """Network segmentation management"""
    
    def __init__(self, firewall_manager: FirewallManager):
        self.firewall = firewall_manager
        self.segments = self._load_segments()
    
    def _load_segments(self) -> Dict[str, NetworkSegment]:
        """Load network segments"""
        segments = {}
        
        # Define standard network segments
        default_segments = [
            NetworkSegment(
                segment_id="internal_lan",
                name="Internal LAN",
                zone=NetworkZone.INTERNAL,
                network_range="192.168.0.0/16",
                gateway="192.168.0.1",
                allowed_services=["http", "https", "dns", "dhcp"],
                restricted_services=["ssh", "telnet", "ftp"],
                security_level=SecurityLevel.MEDIUM,
                isolation_level=5
            ),
            NetworkSegment(
                segment_id="dmz_zone",
                name="DMZ Zone",
                zone=NetworkZone.DMZ,
                network_range="192.168.1.0/24",
                gateway="192.168.1.1",
                allowed_services=["http", "https", "smtp"],
                restricted_services=["ssh", "database"],
                security_level=SecurityLevel.HIGH,
                isolation_level=8
            ),
            NetworkSegment(
                segment_id="management_network",
                name="Management Network",
                zone=NetworkZone.MANAGEMENT,
                network_range="10.0.0.0/24",
                gateway="10.0.0.1",
                allowed_services=["ssh", "snmp", "rdp"],
                restricted_services=["http", "https"],
                security_level=SecurityLevel.CRITICAL,
                isolation_level=10
            )
        ]
        
        for segment in default_segments:
            self.firewall.add_network_segment(segment)
            segments[segment.segment_id] = segment
        
        return segments
    
    def check_network_isolation(self, source_ip: str, dest_ip: str) -> Dict[str, Any]:
        """Check if source and destination are properly isolated"""
        source_segment = self.firewall.get_network_segment(source_ip)
        dest_segment = self.firewall.get_network_segment(dest_ip)
        
        if not source_segment or not dest_segment:
            return {
                'isolated': False,
                'reason': 'Unknown network segments',
                'source_segment': source_segment.segment_id if source_segment else 'unknown',
                'dest_segment': dest_segment.segment_id if dest_segment else 'unknown'
            }
        
        # Check if cross-zone communication is allowed
        allowed_zones = {
            NetworkZone.EXTERNAL: [NetworkZone.DMZ],
            NetworkZone.DMZ: [NetworkZone.EXTERNAL, NetworkZone.INTERNAL],
            NetworkZone.INTERNAL: [NetworkZone.DMZ],
            NetworkZone.SECURE: [],
            NetworkZone.MANAGEMENT: []
        }
        
        source_zone = source_segment.zone
        dest_zone = dest_segment.zone
        
        isolation_status = {
            'source_segment': source_segment.segment_id,
            'dest_segment': dest_segment.segment_id,
            'source_zone': source_zone.value,
            'dest_zone': dest_zone.value,
            'isolated': True,
            'reason': 'Zones are properly isolated'
        }
        
        # Check if communication should be blocked
        if dest_zone not in allowed_zones.get(source_zone, []):
            isolation_status['isolated'] = False
            isolation_status['reason'] = f'Communication from {source_zone.value} to {dest_zone.value} not allowed'
        
        return isolation_status
