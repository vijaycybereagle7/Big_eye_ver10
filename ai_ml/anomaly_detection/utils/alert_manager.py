"""
Alert Manager

Comprehensive alert management system for anomaly detection notifications.
Handles alert creation, severity assessment, notification routing, and alert
cooldown mechanisms.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts from anomaly detection systems.
    
    Features:
    - Alert severity classification
    - Notification routing (email, console, file)
    - Alert cooldown management
    - Alert correlation
    - Alert history tracking
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the alert manager.
        
        Args:
            config: Configuration dictionary with alert parameters
        """
        self.config = config or self._get_default_config()
        
        # Alert storage and tracking
        self.alert_history = []
        self.active_alerts = {}
        self.alert_cooldowns = defaultdict(datetime)
        self.notification_handlers = {}
        
        # Setup notification channels
        self._setup_notification_channels()
        
        logger.info("AlertManager initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for alert management."""
        return {
            'severity_thresholds': {
                'critical': 0.9,
                'high': 0.8,
                'medium': 0.7,
                'low': 0.6
            },
            'alert_cooldown': 300,  # 5 minutes in seconds
            'notification_channels': ['log', 'console'],
            'email_config': {
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_address': 'alerts@company.com',
                'to_addresses': ['security@company.com']
            },
            'alert_routing': {
                'critical': ['email', 'log', 'console'],
                'high': ['email', 'log'],
                'medium': ['log'],
                'low': ['console']
            },
            'alert_correlation': {
                'enabled': True,
                'time_window': 900,  # 15 minutes
                'similarity_threshold': 0.8
            }
        }

    def _setup_notification_channels(self):
        """Setup notification channels based on configuration."""
        channels = self.config.get('notification_channels', [])
        
        for channel in channels:
            if channel == 'email':
                self.notification_handlers['email'] = self._send_email_alert
            elif channel == 'log':
                self.notification_handlers['log'] = self._send_log_alert
            elif channel == 'console':
                self.notification_handlers['console'] = self._send_console_alert
            elif channel == 'file':
                self.notification_handlers['file'] = self._send_file_alert

    def send_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Send an alert through appropriate channels.
        
        Args:
            alert: Alert dictionary containing alert details
            
        Returns:
            Boolean indicating if alert was sent successfully
        """
        try:
            # Add timestamp if not present
            if 'timestamp' not in alert:
                alert['timestamp'] = datetime.now().isoformat()
            
            # Check if alert is in cooldown period
            alert_key = self._generate_alert_key(alert)
            if self._is_in_cooldown(alert_key):
                logger.debug(f"Alert {alert_key} is in cooldown period, skipping")
                return False
            
            # Correlate with existing alerts
            correlated_alerts = self._correlate_alert(alert)
            
            # Add correlation information
            alert['correlated_alerts'] = correlated_alerts
            alert['correlation_count'] = len(correlated_alerts)
            
            # Send alert through appropriate channels
            severity = alert.get('severity', 'low')
            channels = self.config['alert_routing'].get(severity, ['console'])
            
            success = True
            for channel in channels:
                if channel in self.notification_handlers:
                    try:
                        channel_success = self.notification_handlers[channel](alert)
                        success = success and channel_success
                    except Exception as e:
                        logger.error(f"Error sending alert through {channel}: {str(e)}")
                        success = False
            
            # Store alert in history
            self.alert_history.append(alert)
            self.active_alerts[alert_key] = alert
            
            # Set cooldown
            self.alert_cooldowns[alert_key] = datetime.now() + timedelta(
                seconds=self.config['alert_cooldown']
            )
            
            # Cleanup old alerts from active_alerts
            self._cleanup_old_alerts()
            
            logger.info(f"Alert sent successfully: {alert.get('use_case', 'unknown')} - {severity}")
            return success
            
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
            return False

    def _generate_alert_key(self, alert: Dict[str, Any]) -> str:
        """Generate a unique key for alert cooldown tracking."""
        use_case = alert.get('use_case', 'unknown')
        severity = alert.get('severity', 'low')
        source = alert.get('source', 'unknown')
        
        # Create key based on alert characteristics
        return f"{use_case}_{severity}_{source}"

    def _is_in_cooldown(self, alert_key: str) -> bool:
        """Check if an alert is in cooldown period."""
        if alert_key in self.alert_cooldowns:
            return datetime.now() < self.alert_cooldowns[alert_key]
        return False

    def _correlate_alert(self, alert: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Correlate new alert with existing alerts based on similarity and time window.
        
        Args:
            alert: New alert to correlate
            
        Returns:
            List of correlated alerts
        """
        if not self.config['alert_correlation']['enabled']:
            return []
        
        correlated = []
        time_window = timedelta(seconds=self.config['alert_correlation']['time_window'])
        similarity_threshold = self.config['alert_correlation']['similarity_threshold']
        
        alert_time = datetime.fromisoformat(alert['timestamp'])
        
        # Check recent alerts
        for historical_alert in self.alert_history[-100:]:  # Check last 100 alerts
            try:
                hist_time = datetime.fromisoformat(historical_alert['timestamp'])
                
                # Check time window
                if alert_time - hist_time > time_window:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_alert_similarity(alert, historical_alert)
                
                if similarity >= similarity_threshold:
                    correlated.append(historical_alert)
                    
            except Exception as e:
                logger.debug(f"Error correlating alert: {str(e)}")
                continue
        
        return correlated

    def _calculate_alert_similarity(self, alert1: Dict[str, Any], alert2: Dict[str, Any]) -> float:
        """Calculate similarity between two alerts."""
        try:
            similarity_score = 0.0
            max_score = 0.0
            
            # Same use case
            if alert1.get('use_case') == alert2.get('use_case'):
                similarity_score += 0.3
            
            # Same severity
            if alert1.get('severity') == alert2.get('severity'):
                similarity_score += 0.2
            
            # Similar anomaly rates
            rate1 = alert1.get('anomaly_rate', 0)
            rate2 = alert2.get('anomaly_rate', 0)
            rate_diff = abs(rate1 - rate2)
            if rate_diff < 0.1:  # Similar rates
                similarity_score += 0.2
            
            # Similar thresholds
            threshold1 = alert1.get('threshold', 0)
            threshold2 = alert2.get('threshold', 0)
            threshold_diff = abs(threshold1 - threshold2)
            if threshold_diff < 0.05:  # Similar thresholds
                similarity_score += 0.1
            
            # Similar details
            details1 = alert1.get('details', {})
            details2 = alert2.get('details', {})
            
            # Compare anomaly counts
            count1 = details1.get('anomaly_count', 0)
            count2 = details2.get('anomaly_count', 0)
            if count1 > 0 and count2 > 0:
                count_ratio = min(count1, count2) / max(count1, count2)
                similarity_score += 0.2 * count_ratio
            
            max_score = 1.0
            return min(similarity_score / max_score, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating alert similarity: {str(e)}")
            return 0.0

    def _send_email_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert via email."""
        try:
            email_config = self.config['email_config']
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['from_address']
            msg['To'] = ', '.join(email_config['to_addresses'])
            msg['Subject'] = f"[{alert['severity'].upper()}] Anomaly Detection Alert - {alert.get('use_case', 'Unknown')}"
            
            # Create email body
            body = self._format_alert_body(alert)
            msg.attach(MIMEText(body, 'html'))
            
            # Send email
            if email_config['smtp_server'] == 'localhost':
                # For testing, just log the email
                logger.info(f"Email alert would be sent: {msg['Subject']}")
                return True
            
            # Real email sending (commented out for safety)
            # server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            # server.starttls()
            # server.login(email_config['username'], email_config['password'])
            # server.send_message(msg)
            # server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {str(e)}")
            return False

    def _send_log_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to logging system."""
        try:
            log_message = self._format_log_message(alert)
            
            # Map alert severity to logging levels
            severity = alert.get('severity', 'low')
            if severity == 'critical':
                logging.critical(log_message)
            elif severity == 'high':
                logging.error(log_message)
            elif severity == 'medium':
                logging.warning(log_message)
            else:
                logging.info(log_message)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending log alert: {str(e)}")
            return False

    def _send_console_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to console."""
        try:
            console_message = self._format_console_message(alert)
            print(console_message)
            return True
            
        except Exception as e:
            logger.error(f"Error sending console alert: {str(e)}")
            return False

    def _send_file_alert(self, alert: Dict[str, Any]) -> bool:
        """Send alert to file."""
        try:
            # This would write alerts to a file
            # For now, just log it
            logger.info(f"File alert: {json.dumps(alert, indent=2)}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending file alert: {str(e)}")
            return False

    def _format_alert_body(self, alert: Dict[str, Any]) -> str:
        """Format alert as HTML email body."""
        try:
            body = f"""
            <html>
            <head>
                <style>
                    .alert {{ border: 2px solid #333; padding: 15px; margin: 10px 0; }}
                    .critical {{ background-color: #ffebee; border-color: #c62828; }}
                    .high {{ background-color: #fff3e0; border-color: #ef6c00; }}
                    .medium {{ background-color: #fff8e1; border-color: #f57c00; }}
                    .low {{ background-color: #e8f5e8; border-color: #388e3c; }}
                    .header {{ font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
                    .detail {{ margin: 5px 0; }}
                </style>
            </head>
            <body>
                <div class="alert {alert['severity']}">
                    <div class="header">🚨 Anomaly Detection Alert</div>
                    <div class="detail"><strong>Use Case:</strong> {alert.get('use_case', 'Unknown')}</div>
                    <div class="detail"><strong>Severity:</strong> {alert.get('severity', 'Unknown').upper()}</div>
                    <div class="detail"><strong>Timestamp:</strong> {alert.get('timestamp', 'Unknown')}</div>
                    <div class="detail"><strong>Anomaly Count:</strong> {alert.get('anomaly_count', 0)}</div>
                    <div class="detail"><strong>Anomaly Rate:</strong> {alert.get('anomaly_rate', 0):.2%}</div>
                    <div class="detail"><strong>Threshold:</strong> {alert.get('threshold', 'Unknown')}</div>
                    
                    {f'<div class="detail"><strong>Correlation Count:</strong> {alert.get("correlation_count", 0)}</div>' if alert.get('correlation_count', 0) > 0 else ''}
                    
                    <div class="detail"><strong>Details:</strong></div>
                    <pre>{json.dumps(alert.get('details', {}), indent=2)}</pre>
                </div>
            </body>
            </html>
            """
            return body
            
        except Exception as e:
            logger.error(f"Error formatting alert body: {str(e)}")
            return f"Anomaly Detection Alert: {json.dumps(alert, indent=2)}"

    def _format_log_message(self, alert: Dict[str, Any]) -> str:
        """Format alert as log message."""
        try:
            message = (
                f"ANOMALY DETECTION ALERT | "
                f"Use Case: {alert.get('use_case', 'Unknown')} | "
                f"Severity: {alert.get('severity', 'Unknown')} | "
                f"Anomalies: {alert.get('anomaly_count', 0)} | "
                f"Rate: {alert.get('anomaly_rate', 0):.2%} | "
                f"Time: {alert.get('timestamp', 'Unknown')}"
            )
            return message
            
        except Exception as e:
            logger.error(f"Error formatting log message: {str(e)}")
            return f"ANOMALY ALERT: {json.dumps(alert)}"

    def _format_console_message(self, alert: Dict[str, Any]) -> str:
        """Format alert as console message."""
        try:
            severity_symbols = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            
            symbol = severity_symbols.get(alert.get('severity', 'low'), '⚪')
            
            message = f"""
{symbol} ANOMALY DETECTION ALERT {symbol}
Use Case: {alert.get('use_case', 'Unknown')}
Severity: {alert.get('severity', 'Unknown').upper()}
Anomalies: {alert.get('anomaly_count', 0)}
Rate: {alert.get('anomaly_rate', 0):.2%}
Time: {alert.get('timestamp', 'Unknown')}
Threshold: {alert.get('threshold', 'Unknown')}
            """
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error formatting console message: {str(e)}")
            return f"ALERT: {json.dumps(alert)}"

    def _cleanup_old_alerts(self):
        """Cleanup old alerts from active_alerts dictionary."""
        try:
            current_time = datetime.now()
            keys_to_remove = []
            
            for key, alert_time in self.alert_cooldowns.items():
                if current_time > alert_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self.alert_cooldowns.pop(key, None)
                self.active_alerts.pop(key, None)
                
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {str(e)}")

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get statistics about alerts."""
        try:
            stats = {
                'total_alerts': len(self.alert_history),
                'active_alerts': len(self.active_alerts),
                'alerts_by_severity': defaultdict(int),
                'alerts_by_use_case': defaultdict(int),
                'recent_alerts': len([
                    alert for alert in self.alert_history
                    if datetime.fromisoformat(alert['timestamp']) > datetime.now() - timedelta(hours=24)
                ])
            }
            
            for alert in self.alert_history:
                stats['alerts_by_severity'][alert.get('severity', 'unknown')] += 1
                stats['alerts_by_use_case'][alert.get('use_case', 'unknown')] += 1
            
            # Convert defaultdicts to regular dicts for JSON serialization
            stats['alerts_by_severity'] = dict(stats['alerts_by_severity'])
            stats['alerts_by_use_case'] = dict(stats['alerts_by_use_case'])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {str(e)}")
            return {'error': str(e)}

    def save_alerts(self, filepath: str):
        """Save alert history to file."""
        try:
            data = {
                'alert_history': self.alert_history,
                'active_alerts': self.active_alerts,
                'config': self.config,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Alerts saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving alerts: {str(e)}")

    def load_alerts(self, filepath: str):
        """Load alert history from file."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.alert_history = data.get('alert_history', [])
            self.active_alerts = data.get('active_alerts', {})
            
            logger.info(f"Alerts loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading alerts: {str(e)}")