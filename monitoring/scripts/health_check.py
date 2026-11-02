#!/usr/bin/env python3
"""
Health Check Script for Monitoring Stack
Checks the health of all monitoring components
"""

import requests
import psycopg2
import pymongo
import redis
import json
import sys
from datetime import datetime

class MonitoringHealthCheck:
    def __init__(self):
        self.services = {
            'prometheus': 'http://localhost:9090/-/healthy',
            'grafana': 'http://localhost:3000/api/health',
            'alertmanager': 'http://localhost:9093/-/healthy',
            'elasticsearch': 'http://localhost:9200/_cluster/health',
            'kibana': 'http://localhost:5601/api/status',
            'node_exporter': 'http://localhost:9100/metrics',
            'cadvisor': 'http://localhost:8080/healthz',
            'postgres_exporter': 'http://localhost:9187/metrics',
            'mongodb_exporter': 'http://localhost:9216/metrics',
            'redis_exporter': 'http://localhost:9121/metrics',
            'victoriametrics': 'http://localhost:8428/health'
        }
        
        self.databases = {
            'postgresql': {
                'host': 'localhost',
                'port': 5432,
                'database': 'cybersecurity_api',
                'user': 'api_user',
                'password': 'api_password'
            },
            'mongodb': {
                'host': 'localhost',
                'port': 27017,
                'database': 'admin',
                'user': 'admin',
                'password': 'mongodb_password'
            },
            'redis': {
                'host': 'localhost',
                'port': 6379,
                'password': 'redis_password'
            }
        }
    
    def check_service_health(self, service_name, url):
        """Check the health of a service"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
            else:
                return {'status': 'unhealthy', 'status_code': response.status_code}
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'error': str(e)}
    
    def check_database_health(self, db_type, config):
        """Check the health of a database"""
        try:
            if db_type == 'postgresql':
                conn = psycopg2.connect(**config)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                return {'status': 'healthy'}
                
            elif db_type == 'mongodb':
                client = pymongo.MongoClient(
                    f"mongodb://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
                )
                client.admin.command('ping')
                client.close()
                return {'status': 'healthy'}
                
            elif db_type == 'redis':
                client = redis.Redis(
                    host=config['host'],
                    port=config['port'],
                    password=config['password'],
                    decode_responses=True
                )
                client.ping()
                client.close()
                return {'status': 'healthy'}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def run_health_checks(self):
        """Run all health checks"""
        print("🔍 Monitoring Stack Health Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()
        
        # Check services
        print("📊 Services:")
        healthy_count = 0
        total_count = len(self.services)
        
        for service_name, url in self.services.items():
            health = self.check_service_health(service_name, url)
            status = health['status']
            
            if status == 'healthy':
                print(f"  ✅ {service_name:20} - Healthy (response: {health.get('response_time', 'N/A')}s)")
                healthy_count += 1
            elif status == 'unhealthy':
                print(f"  ❌ {service_name:20} - Unhealthy (status: {health.get('status_code', 'N/A')})")
            else:
                print(f"  🚫 {service_name:20} - Error ({health.get('error', 'Unknown error')})")
        
        print()
        
        # Check databases
        print("🗄️ Databases:")
        for db_type, config in self.databases.items():
            health = self.check_database_health(db_type, config)
            status = health['status']
            
            if status == 'healthy':
                print(f"  ✅ {db_type:15} - Healthy")
                healthy_count += 1
            else:
                print(f"  🚫 {db_type:15} - Error ({health.get('error', 'Unknown error')})")
            
            total_count += 1
        
        print()
        print("📈 Summary:")
        print(f"  Healthy: {healthy_count}/{total_count}")
        print(f"  Health Score: {(healthy_count/total_count)*100:.1f}%")
        
        # Recommendations
        print()
        print("💡 Recommendations:")
        if healthy_count < total_count * 0.8:
            print("  - Several services are not healthy, check logs for details")
            print("  - Verify Docker containers are running: docker-compose ps")
        elif healthy_count < total_count:
            print("  - Some services need attention, but core functionality is working")
        else:
            print("  - All services are healthy! 🎉")
        
        return healthy_count == total_count

if __name__ == '__main__':
    health_check = MonitoringHealthCheck()
    success = health_check.run_health_checks()
    sys.exit(0 if success else 1)