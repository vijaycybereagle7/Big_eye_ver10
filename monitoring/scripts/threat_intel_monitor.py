#!/usr/bin/env python3
"""
Threat Intelligence Monitor
Monitors threat intelligence feeds and API health
"""

import time
import json
import requests
import logging
from datetime import datetime, timedelta
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import redis
import psycopg2
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Threat feed configuration
THREAT_FEEDS = {
    'virustotal': {
        'url': 'https://www.virustotal.com/vtapi/v2/url/report',
        'api_key': 'YOUR_VIRUSTOTAL_API_KEY',
        'rate_limit': 4,  # requests per minute
        'enabled': True
    },
    'abuseipdb': {
        'url': 'https://api.abuseipdb.com/api/v2/check',
        'api_key': 'YOUR_ABUSEIPDB_API_KEY',
        'rate_limit': 100,  # requests per minute
        'enabled': True
    },
    'greynoise': {
        'url': 'https://api.greynoise.io/v3/community/ip/',
        'api_key': 'YOUR_GREYNOISE_API_KEY',
        'rate_limit': 1000,  # requests per minute
        'enabled': True
    },
    'shodan': {
        'url': 'https://api.shodan.io/shodan/host/',
        'api_key': 'YOUR_SHODAN_API_KEY',
        'rate_limit': 100,  # requests per minute
        'enabled': True
    },
    'otx': {
        'url': 'https://otx.alienvault.com/api/v1/indicators/IPv4/',
        'api_key': 'YOUR_OTX_API_KEY',
        'rate_limit': 1000,  # requests per minute
        'enabled': True
    }
}

# Prometheus metrics
threat_feed_status = Gauge('threat_feed_status', 'Threat feed status', ['feed_name'])
threat_feed_response_time = Gauge('threat_feed_response_time_seconds', 'Threat feed response time', ['feed_name'])
threat_feed_last_update = Gauge('threat_feed_last_update', 'Threat feed last update timestamp', ['feed_name'])
threat_feed_api_calls_total = Counter('threat_feed_api_calls_total', 'Total API calls', ['feed_name', 'status'])
threat_feed_api_errors_total = Counter('threat_feed_api_errors_total', 'Total API errors', ['feed_name', 'error_type'])
threat_feed_quota_usage = Gauge('threat_feed_quota_usage', 'API quota usage percentage', ['feed_name'])

class ThreatIntelligenceMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.db_connection = self.init_database()
        self.rate_limiters = {}
        
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
    
    def check_feed_health(self, feed_name, feed_config):
        """Check the health of a threat intelligence feed"""
        try:
            if not feed_config['enabled']:
                logger.info(f"Feed {feed_name} is disabled")
                threat_feed_status.labels(feed_name=feed_name).set(0)
                return
            
            start_time = time.time()
            
            # Make test API call
            headers = {
                'User-Agent': 'Cybersecurity-API-Monitor/1.0'
            }
            
            if feed_name == 'virustotal':
                # Test with a known benign URL
                test_url = "google.com"
                params = {
                    'apikey': feed_config['api_key'],
                    'resource': test_url
                }
                response = requests.get(feed_config['url'], params=params, timeout=10)
                
            elif feed_name == 'abuseipdb':
                # Test with a known IP
                test_ip = "8.8.8.8"
                headers['Key'] = feed_config['api_key']
                headers['Accept'] = 'application/json'
                params = {
                    'ipAddress': test_ip,
                    'maxAgeInDays': 90
                }
                response = requests.get(feed_config['url'], headers=headers, params=params, timeout=10)
                
            elif feed_name == 'greynoise':
                # Test with a known IP
                test_ip = "8.8.8.8"
                headers['key'] = feed_config['api_key']
                response = requests.get(f"{feed_config['url']}{test_ip}", headers=headers, timeout=10)
                
            else:
                # Generic test for other feeds
                response = requests.get(feed_config['url'], timeout=10)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                threat_feed_status.labels(feed_name=feed_name).set(1)
                threat_feed_response_time.labels(feed_name=feed_name).set(response_time)
                threat_feed_last_update.labels(feed_name=feed_name).set(time.time())
                threat_feed_api_calls_total.labels(feed_name=feed_name, status='success').inc()
                
                logger.info(f"Feed {feed_name} is healthy (response time: {response_time:.2f}s)")
            else:
                threat_feed_status.labels(feed_name=feed_name).set(0)
                threat_feed_api_calls_total.labels(feed_name=feed_name, status='error').inc()
                threat_feed_api_errors_total.labels(feed_name=feed_name, error_type='http_error').inc()
                
                logger.warning(f"Feed {feed_name} returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            threat_feed_status.labels(feed_name=feed_name).set(0)
            threat_feed_api_errors_total.labels(feed_name=feed_name, error_type='timeout').inc()
            logger.error(f"Feed {feed_name} timed out")
            
        except requests.exceptions.ConnectionError:
            threat_feed_status.labels(feed_name=feed_name).set(0)
            threat_feed_api_errors_total.labels(feed_name=feed_name, error_type='connection_error').inc()
            logger.error(f"Feed {feed_name} connection error")
            
        except Exception as e:
            threat_feed_status.labels(feed_name=feed_name).set(0)
            threat_feed_api_errors_total.labels(feed_name=feed_name, error_type='unknown').inc()
            logger.error(f"Feed {feed_name} error: {str(e)}")
    
    def check_api_quota(self, feed_name, feed_config):
        """Check API quota usage for threat feeds"""
        try:
            # This would be implemented based on specific API quota checking
            # For now, we'll simulate quota usage
            
            import random
            quota_usage = random.uniform(10, 90)  # Simulate 10-90% usage
            threat_feed_quota_usage.labels(feed_name=feed_name).set(quota_usage)
            
            if quota_usage > 80:
                logger.warning(f"Feed {feed_name} quota usage is at {quota_usage:.1f}%")
                
        except Exception as e:
            logger.error(f"Error checking quota for {feed_name}: {e}")
    
    def monitor_threat_feeds(self):
        """Main monitoring loop for threat feeds"""
        logger.info("Starting threat intelligence monitoring...")
        
        while True:
            try:
                for feed_name, feed_config in THREAT_FEEDS.items():
                    logger.info(f"Checking health of {feed_name}...")
                    self.check_feed_health(feed_name, feed_config)
                    self.check_api_quota(feed_name, feed_config)
                    
                    # Rate limiting - wait between feed checks
                    time.sleep(2)
                
                logger.info("Threat feed monitoring cycle completed")
                
            except Exception as e:
                logger.error(f"Error in threat feed monitoring: {e}")
            
            # Wait before next monitoring cycle
            time.sleep(300)  # Check every 5 minutes
    
    def collect_threat_intelligence_metrics(self):
        """Collect and store threat intelligence metrics"""
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                
                # Get recent threat detections
                cursor.execute("""
                    SELECT 
                        feed_name, 
                        threat_type, 
                        severity, 
                        COUNT(*) as threat_count,
                        MAX(detected_at) as last_detection
                    FROM threat_detections 
                    WHERE detected_at > NOW() - INTERVAL '1 hour'
                    GROUP BY feed_name, threat_type, severity
                """)
                
                results = cursor.fetchall()
                for row in results:
                    feed_name, threat_type, severity, count, last_detection = row
                    # Here you would update Prometheus metrics based on the data
                    logger.info(f"Threat metrics: {feed_name}, {threat_type}, {severity}, count: {count}")
                
                cursor.close()
                
        except Exception as e:
            logger.error(f"Error collecting threat intelligence metrics: {e}")
    
    def run(self):
        """Start the threat intelligence monitor"""
        # Start Prometheus metrics server
        start_http_server(9090)
        logger.info("Prometheus metrics server started on port 9090")
        
        # Start monitoring
        self.monitor_threat_feeds()

def main():
    """Main function"""
    monitor = ThreatIntelligenceMonitor()
    monitor.run()

if __name__ == '__main__':
    main()