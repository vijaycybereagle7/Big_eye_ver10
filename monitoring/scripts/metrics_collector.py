#!/usr/bin/env python3
"""
Application Metrics Collector for Cybersecurity API
Collects custom application metrics and exposes them to Prometheus
"""

import time
import json
import logging
from datetime import datetime
from flask import Flask, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import redis
import psycopg2
import pymongo
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': app
})

# Prometheus metrics
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint'])
api_active_connections = Gauge('api_active_connections', 'Active API connections')
validation_throughput = Counter('validation_throughput_total', 'Total validations processed', ['validation_type', 'status'])
threats_detected_total = Counter('threats_detected_total', 'Total threats detected', ['feed_name', 'threat_type', 'severity'])
malicious_ip_detections_total = Counter('malicious_ip_detections_total', 'Malicious IP detections', ['source'])
api_quota_usage_percentage = Gauge('api_quota_usage_percentage', 'API quota usage percentage', ['provider'])
threat_feed_status = Gauge('threat_feed_status', 'Threat feed status', ['feed_name'])
threat_feed_response_time = Gauge('threat_feed_response_time_seconds', 'Threat feed response time', ['feed_name'])
threat_feed_last_update = Gauge('threat_feed_last_update', 'Threat feed last update timestamp', ['feed_name'])
api_rate_limit_exceeded_total = Counter('api_rate_limit_exceeded_total', 'API rate limit exceeded', ['provider'])
suspicious_activity_detections_total = Counter('suspicious_activity_detections_total', 'Suspicious activity detections', ['activity_type'])
failed_login_attempts_total = Counter('failed_login_attempts_total', 'Failed login attempts', ['source'])
suspicious_api_requests_total = Counter('suspicious_api_requests_total', 'Suspicious API requests', ['endpoint'])
validations_processed_total = Counter('validations_processed_total', 'Validations processed', ['validation_type'])
api_usage_quota_percentage = Gauge('api_usage_quota_percentage', 'API usage quota percentage', ['provider'])

# Database connections
db_connections = {}
redis_client = None

def init_database_connections():
    """Initialize database connections"""
    global redis_client, db_connections
    
    try:
        # Redis connection
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        redis_client.ping()
        logger.info("Redis connection established")
        
        # PostgreSQL connection
        db_connections['postgresql'] = psycopg2.connect(
            host='postgres',
            database='cybersecurity_api',
            user='api_user',
            password='api_password'
        )
        logger.info("PostgreSQL connection established")
        
        # MongoDB connection
        db_connections['mongodb'] = pymongo.MongoClient('mongodb://mongo:27017/')
        db_connections['mongodb'].admin.command('ping')
        logger.info("MongoDB connection established")
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")

def collect_api_metrics():
    """Collect API-related metrics"""
    try:
        # This would be replaced with actual API monitoring
        # For now, we'll simulate some metrics
        
        # Simulate API request metrics
        api_requests_total.labels(method='GET', endpoint='/api/v1/status', status='200').inc()
        api_requests_total.labels(method='POST', endpoint='/api/v1/validate', status='200').inc()
        api_requests_total.labels(method='GET', endpoint='/api/v1/threats', status='200').inc()
        
        # Simulate request duration
        api_request_duration.labels(endpoint='/api/v1/status').observe(0.05)
        api_request_duration.labels(endpoint='/api/v1/validate').observe(0.12)
        api_request_duration.labels(endpoint='/api/v1/threats').observe(0.08)
        
        # Simulate active connections
        api_active_connections.set(15)
        
        # Simulate validation throughput
        validations_processed_total.labels(validation_type='url_validation').inc(5)
        validations_processed_total.labels(validation_type='hash_validation').inc(3)
        validations_processed_total.labels(validation_type='ip_validation').inc(7)
        
    except Exception as e:
        logger.error(f"Error collecting API metrics: {e}")

def collect_database_metrics():
    """Collect database-related metrics"""
    try:
        # PostgreSQL metrics
        if 'postgresql' in db_connections:
            cursor = db_connections['postgresql'].cursor()
            
            # Active connections
            cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
            active_connections = cursor.fetchone()[0]
            logger.info(f"Active PostgreSQL connections: {active_connections}")
            
            cursor.close()
        
        # MongoDB metrics
        if 'mongodb' in db_connections:
            db = db_connections['mongodb'].admin
            db_stats = db.command("dbStats")
            logger.info(f"MongoDB data size: {db_stats['dataSize']}")
            
    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")

def collect_threat_intelligence_metrics():
    """Collect threat intelligence metrics"""
    try:
        # Simulate threat detection metrics
        threats_detected_total.labels(
            feed_name='virustotal', 
            threat_type='malware', 
            severity='high'
        ).inc(5)
        
        threats_detected_total.labels(
            feed_name='abuseipdb',
            threat_type='malicious_ip',
            severity='medium'
        ).inc(12)
        
        threats_detected_total.labels(
            feed_name='greynoise',
            threat_type='suspicious_ip',
            severity='low'
        ).inc(8)
        
        # Simulate feed status
        threat_feed_status.labels(feed_name='virustotal').set(1)
        threat_feed_status.labels(feed_name='abuseipdb').set(1)
        threat_feed_status.labels(feed_name='greynoise').set(1)
        
        # Simulate response times
        threat_feed_response_time.labels(feed_name='virustotal').set(0.45)
        threat_feed_response_time.labels(feed_name='abuseipdb').set(0.12)
        threat_feed_response_time.labels(feed_name='greynoise').set(0.08)
        
        # Simulate last update times
        threat_feed_last_update.labels(feed_name='virustotal').set(time.time())
        threat_feed_last_update.labels(feed_name='abuseipdb').set(time.time())
        threat_feed_last_update.labels(feed_name='greynoise').set(time.time())
        
        # Simulate API quota usage
        api_usage_quota_percentage.labels(provider='virustotal').set(65.5)
        api_usage_quota_percentage.labels(provider='abuseipdb').set(23.1)
        api_usage_quota_percentage.labels(provider='greynoise').set(8.7)
        
    except Exception as e:
        logger.error(f"Error collecting threat intelligence metrics: {e}")

def collect_security_metrics():
    """Collect security-related metrics"""
    try:
        # Simulate security events
        malicious_ip_detections_total.labels(source='virustotal').inc(3)
        malicious_ip_detections_total.labels(source='abuseipdb').inc(7)
        
        suspicious_activity_detections_total.labels(activity_type='rapid_requests').inc(2)
        suspicious_activity_detections_total.labels(activity_type='unusual_pattern').inc(1)
        
        # Simulate failed login attempts
        failed_login_attempts_total.labels(source='api').inc(5)
        
        # Simulate suspicious API requests
        suspicious_api_requests_total.labels(endpoint='/api/v1/admin').inc(1)
        
    except Exception as e:
        logger.error(f"Error collecting security metrics: {e}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'metrics_collector': 'running'
    })

@app.route('/health/metrics')
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    try:
        # Collect metrics periodically
        collect_api_metrics()
        collect_database_metrics()
        collect_threat_intelligence_metrics()
        collect_security_metrics()
        
        # Generate and return metrics
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
        
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    """Main metrics endpoint for Prometheus"""
    return metrics_endpoint()

if __name__ == '__main__':
    logger.info("Starting metrics collector...")
    
    # Initialize database connections
    init_database_connections()
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8000, debug=False)