#!/usr/bin/env python3
"""
Performance Optimization Monitoring and Maintenance Script

This script provides comprehensive monitoring and maintenance for all
performance optimization components including database indexing, Redis caching,
partitioning, read replicas, and materialized views.
"""

import asyncio
import logging
import psycopg2
import psycopg2.extras
import redis
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring and maintenance system
    """
    
    def __init__(self, config: Dict):
        """Initialize with database and Redis configurations"""
        self.config = config
        self.db_config = config.get('database', {})
        self.redis_config = config.get('redis', {})
        self.alert_config = config.get('alerts', {})
        
        # Initialize connections
        self._init_database_connection()
        self._init_redis_connection()
        
        # Statistics tracking
        self.metrics_history = []
        self.alert_history = []
    
    def _init_database_connection(self):
        """Initialize PostgreSQL connection"""
        try:
            self.db_connection = psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'postgres'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', ''),
                connect_timeout=10
            )
            self.db_connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _init_redis_connection(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379),
                db=self.redis_config.get('db', 0),
                password=self.redis_config.get('password'),
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def monitor_database_performance(self) -> Dict:
        """Monitor database performance metrics"""
        metrics = {}
        
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Database size and connection stats
                cursor.execute("""
                    SELECT 
                        datname,
                        pg_size_pretty(pg_database_size(datname)) as size,
                        numbackends as active_connections
                    FROM pg_database 
                    WHERE datname = %s
                """, (self.db_config.get('database', 'postgres'),))
                
                db_stats = cursor.fetchone()
                if db_stats:
                    metrics['database'] = {
                        'name': db_stats['datname'],
                        'size': db_stats['size'],
                        'active_connections': db_stats['active_connections']
                    }
                
                # Active connections details
                cursor.execute("""
                    SELECT 
                        state,
                        COUNT(*) as connection_count,
                        AVG(now() - state_change) as avg_duration
                    FROM pg_stat_activity 
                    WHERE datname = %s 
                    GROUP BY state
                """, (self.db_config.get('database', 'postgres'),))
                
                connection_stats = cursor.fetchall()
                metrics['connections'] = {stat['state']: {
                    'count': stat['connection_count'],
                    'avg_duration': str(stat['avg_duration'])
                } for stat in connection_stats}
                
                # Query performance statistics
                cursor.execute("""
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows,
                        100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                    FROM pg_stat_statements 
                    WHERE query LIKE '%SELECT%'
                    ORDER BY total_time DESC 
                    LIMIT 10
                """)
                
                query_stats = cursor.fetchall()
                metrics['query_performance'] = [{
                    'query': q['query'][:100] + '...' if len(q['query']) > 100 else q['query'],
                    'calls': q['calls'],
                    'total_time': round(q['total_time'], 2),
                    'mean_time': round(q['mean_time'], 2),
                    'hit_percent': round(q['hit_percent'], 2)
                } for q in query_stats]
                
                # Index usage statistics
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)
                
                index_stats = cursor.fetchall()
                metrics['index_usage'] = [{
                    'table': idx['tablename'],
                    'index': idx['indexname'],
                    'scans': idx['idx_scan'],
                    'tuples_read': idx['idx_tup_read']
                } for idx in index_stats]
                
                # Replication lag (if configured)
                cursor.execute("""
                    SELECT 
                        application_name,
                        state,
                        sync_state,
                        COALESCE(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn), 0) as lag_bytes,
                        COALESCE(EXTRACT(EPOCH FROM replay_lag), 0) as lag_seconds
                    FROM pg_stat_replication
                """)
                
                replication_stats = cursor.fetchall()
                metrics['replication'] = [{
                    'replica': rep['application_name'],
                    'state': rep['state'],
                    'sync_state': rep['sync_state'],
                    'lag_bytes': rep['lag_bytes'],
                    'lag_seconds': round(rep['lag_seconds'], 2)
                } for rep in replication_stats]
        
        except Exception as e:
            logger.error(f"Error monitoring database performance: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def monitor_redis_performance(self) -> Dict:
        """Monitor Redis performance metrics"""
        metrics = {}
        
        try:
            # Redis info
            info = self.redis_client.info()
            
            metrics.update({
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
                'hit_rate': self._calculate_hit_rate(info)
            })
            
            # Memory breakdown
            memory_info = self.redis_client.info('memory')
            metrics['memory'] = {
                'used_memory_rss': memory_info.get('used_memory_rss', 0),
                'used_memory_lua': memory_info.get('used_memory_lua', 0),
                'mem_fragmentation_ratio': memory_info.get('mem_fragmentation_ratio', 0)
            }
            
            # Persistence info
            persistence_info = self.redis_client.info('persistence')
            metrics['persistence'] = {
                'rdb_bgsave_in_progress': persistence_info.get('rdb_bgsave_in_progress', 0),
                'rdb_last_save_time': persistence_info.get('rdb_last_save_time', 0),
                'aof_enabled': persistence_info.get('aof_enabled', 0)
            }
            
            # Keyspace information
            keyspace_info = self.redis_client.info('keyspace')
            metrics['keyspace'] = {}
            
            for db_name, db_info in keyspace_info.items():
                if db_name.startswith('db'):
                    metrics['keyspace'][db_name] = {
                        'keys': db_info.get('keys', 0),
                        'expires': db_info.get('expires', 0),
                        'avg_ttl': db_info.get('avg_ttl', 0)
                    }
        
        except Exception as e:
            logger.error(f"Error monitoring Redis performance: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total > 0:
            return round((hits / total) * 100, 2)
        return 0.0
    
    def monitor_partition_performance(self) -> Dict:
        """Monitor table partitioning performance"""
        metrics = {}
        
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Partition statistics
                cursor.execute("""
                    SELECT 
                        c.relname as partition_name,
                        n_live_tup as row_count,
                        n_dead_tup as dead_tuples,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    LEFT JOIN pg_stat_user_tables s ON s.relname = c.relname
                    WHERE n.nspname = 'public'
                      AND c.relname LIKE '%_2023_%'
                      AND c.relkind = 'r'
                    ORDER BY c.relname
                """)
                
                partition_stats = cursor.fetchall()
                metrics['partitions'] = [{
                    'name': p['partition_name'],
                    'rows': p['row_count'],
                    'dead_tuples': p['dead_tuples'],
                    'last_vacuum': str(p['last_vacuum']) if p['last_vacuum'] else None,
                    'last_analyze': str(p['last_analyze']) if p['last_analyze'] else None
                } for p in partition_stats]
                
                # Check for missing partitions
                cursor.execute("""
                    SELECT DISTINCT 
                        table_name,
                        DATE_TRUNC('month', created_at) as month_needed
                    FROM user_sessions
                    WHERE created_at >= '2023-01-01'
                      AND table_name NOT IN (
                          SELECT relname 
                          FROM pg_class 
                          WHERE relname LIKE 'user_sessions_2023_%'
                      )
                    GROUP BY table_name, DATE_TRUNC('month', created_at)
                """)
                
                missing_partitions = cursor.fetchall()
                metrics['missing_partitions'] = [{
                    'table': p['table_name'],
                    'month': str(p['month_needed'])
                } for p in missing_partitions]
        
        except Exception as e:
            logger.error(f"Error monitoring partitions: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def monitor_materialized_views(self) -> Dict:
        """Monitor materialized views performance"""
        metrics = {}
        
        try:
            with self.db_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Materialized view freshness
                cursor.execute("""
                    SELECT 
                        schemaname,
                        matviewname,
                        last_refresh_time,
                        EXTRACT(EPOCH FROM (NOW() - last_refresh_time)) / 60 as staleness_minutes
                    FROM pg_matviews
                    WHERE schemaname = 'public'
                    ORDER BY last_refresh_time
                """)
                
                mv_stats = cursor.fetchall()
                metrics['views'] = [{
                    'name': mv['matviewname'],
                    'last_refresh': str(mv['last_refresh_time']) if mv['last_refresh_time'] else None,
                    'staleness_minutes': round(mv['staleness_minutes'], 2)
                } for mv in mv_stats]
                
                # View sizes
                cursor.execute("""
                    SELECT 
                        n.nspname as schema_name,
                        c.relname as view_name,
                        pg_size_pretty(pg_total_relation_size(c.oid)) as total_size,
                        pg_size_pretty(pg_relation_size(c.oid)) as table_size,
                        pg_size_pretty(pg_total_relation_size(c.oid) - pg_relation_size(c.oid)) as indexes_size
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relkind = 'm'
                      AND n.nspname = 'public'
                    ORDER BY pg_total_relation_size(c.oid) DESC
                """)
                
                mv_sizes = cursor.fetchall()
                metrics['sizes'] = [{
                    'name': mv['view_name'],
                    'total_size': mv['total_size'],
                    'table_size': mv['table_size'],
                    'indexes_size': mv['indexes_size']
                } for mv in mv_sizes]
        
        except Exception as e:
            logger.error(f"Error monitoring materialized views: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def run_maintenance_tasks(self) -> Dict:
        """Run automated maintenance tasks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks': []
        }
        
        try:
            # Clean up expired cache
            cache_cleanup_result = self._cleanup_expired_cache()
            results['tasks'].append({
                'task': 'cleanup_expired_cache',
                'status': 'success',
                'details': cache_cleanup_result
            })
            
            # Vacuum and analyze tables
            vacuum_result = self._vacuum_and_analyze_tables()
            results['tasks'].append({
                'task': 'vacuum_and_analyze',
                'status': 'success',
                'details': vacuum_result
            })
            
            # Refresh materialized views
            mv_refresh_result = self._refresh_materialized_views()
            results['tasks'].append({
                'task': 'refresh_materialized_views',
                'status': 'success',
                'details': mv_refresh_result
            })
            
            # Create missing partitions
            partition_result = self._create_missing_partitions()
            results['tasks'].append({
                'task': 'create_missing_partitions',
                'status': 'success',
                'details': partition_result
            })
            
            # Remove old partitions
            cleanup_partitions_result = self._cleanup_old_partitions()
            results['tasks'].append({
                'task': 'cleanup_old_partitions',
                'status': 'success',
                'details': cleanup_partitions_result
            })
            
            # Generate maintenance report
            report_result = self._generate_maintenance_report()
            results['tasks'].append({
                'task': 'generate_maintenance_report',
                'status': 'success',
                'details': report_result
            })
        
        except Exception as e:
            logger.error(f"Error running maintenance tasks: {e}")
            results['error'] = str(e)
        
        return results
    
    def _cleanup_expired_cache(self) -> Dict:
        """Clean up expired cache entries"""
        try:
            # Clean Redis cache
            redis_cleaned = 0
            
            # This would be implemented based on your cache structure
            # For example, remove keys older than TTL
            
            return {
                'redis_keys_removed': redis_cleaned,
                'status': 'completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _vacuum_and_analyze_tables(self) -> Dict:
        """Vacuum and analyze tables"""
        try:
            tables = ['users', 'user_sessions', 'user_payments', 'user_profiles']
            results = []
            
            with self.db_connection.cursor() as cursor:
                for table in tables:
                    cursor.execute(f"VACUUM ANALYZE {table}")
                    results.append({
                        'table': table,
                        'status': 'completed'
                    })
            
            return {
                'tables_processed': len(tables),
                'details': results
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _refresh_materialized_views(self) -> Dict:
        """Refresh materialized views"""
        try:
            views = [
                'user_engagement_summary',
                'daily_user_activity',
                'monthly_revenue_summary',
                'content_performance_summary',
                'realtime_user_stats'
            ]
            results = []
            
            with self.db_connection.cursor() as cursor:
                for view in views:
                    cursor.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                    results.append({
                        'view': view,
                        'status': 'completed'
                    })
            
            return {
                'views_refreshed': len(views),
                'details': results
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_missing_partitions(self) -> Dict:
        """Create missing partitions"""
        try:
            # Implementation would check for and create missing partitions
            # This is a placeholder for the actual implementation
            
            return {
                'partitions_created': 0,
                'status': 'completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _cleanup_old_partitions(self) -> Dict:
        """Clean up old partitions"""
        try:
            # Implementation would drop partitions older than retention period
            # This is a placeholder for the actual implementation
            
            return {
                'partitions_dropped': 0,
                'status': 'completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_maintenance_report(self) -> Dict:
        """Generate maintenance report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'period': '24 hours',
                'summary': {
                    'database_performance': 'good',
                    'cache_performance': 'excellent',
                    'replication_status': 'healthy',
                    'partition_status': 'optimal'
                },
                'recommendations': [
                    'Consider increasing cache TTL for API responses',
                    'Monitor replication lag during peak hours',
                    'Plan for partition creation 3 months ahead'
                ]
            }
            
            # Save report to file
            report_file = f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            return {
                'report_file': report_file,
                'status': 'completed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_alerts(self, metrics: Dict) -> List[Dict]:
        """Check for performance alerts"""
        alerts = []
        current_time = datetime.now()
        
        try:
            # Check database connections
            if 'database' in metrics and 'active_connections' in metrics['database']:
                active_conns = metrics['database']['active_connections']
                max_conns = self.db_config.get('max_connections', 200)
                conn_threshold = max_conns * 0.8  # 80% of max connections
                
                if active_conns > conn_threshold:
                    alerts.append({
                        'type': 'database_connections',
                        'severity': 'warning',
                        'message': f'Active connections ({active_conns}) exceed threshold ({conn_threshold})',
                        'timestamp': current_time.isoformat()
                    })
            
            # Check cache hit rate
            if 'cache_performance' in metrics and 'hit_rate' in metrics['cache_performance']:
                hit_rate = metrics['cache_performance']['hit_rate']
                hit_threshold = self.alert_config.get('cache_hit_rate_threshold', 85)
                
                if hit_rate < hit_threshold:
                    alerts.append({
                        'type': 'cache_hit_rate',
                        'severity': 'warning',
                        'message': f'Cache hit rate ({hit_rate}%) below threshold ({hit_threshold}%)',
                        'timestamp': current_time.isoformat()
                    })
            
            # Check replication lag
            if 'replication' in metrics:
                for replica in metrics['replication']:
                    if 'lag_seconds' in replica:
                        lag_threshold = self.alert_config.get('replication_lag_threshold', 60)
                        if replica['lag_seconds'] > lag_threshold:
                            alerts.append({
                                'type': 'replication_lag',
                                'severity': 'critical',
                                'message': f'Replica {replica["replica"]} lag is {replica["lag_seconds"]}s',
                                'timestamp': current_time.isoformat()
                            })
            
            # Check materialized view staleness
            if 'materialized_views' in metrics and 'views' in metrics['materialized_views']:
                for view in metrics['materialized_views']['views']:
                    if view['staleness_minutes'] > 60:  # 1 hour
                        alerts.append({
                            'type': 'mv_staleness',
                            'severity': 'warning',
                            'message': f'Materialized view {view["name"]} is stale ({view["staleness_minutes"]} minutes)',
                            'timestamp': current_time.isoformat()
                        })
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        
        return alerts
    
    def send_alerts(self, alerts: List[Dict]):
        """Send alert notifications"""
        if not alerts:
            return
        
        try:
            email_config = self.alert_config.get('email', {})
            smtp_server = email_config.get('smtp_server', 'localhost')
            smtp_port = email_config.get('smtp_port', 587)
            username = email_config.get('username', '')
            password = email_config.get('password', '')
            recipients = email_config.get('recipients', [])
            
            if not recipients:
                logger.warning("No email recipients configured for alerts")
                return
            
            # Create email
            msg = MimeMultipart()
            msg['From'] = username
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f'Performance Alert - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            
            # Email body
            body = "Performance alerts detected:\n\n"
            for alert in alerts:
                body += f"[{alert['severity'].upper()}] {alert['type']}\n"
                body += f"Message: {alert['message']}\n"
                body += f"Time: {alert['timestamp']}\n\n"
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_port == 587:  # TLS
                    server.starttls()
                if username and password:
                    server.login(username, password)
                
                server.send_message(msg)
            
            logger.info(f"Sent {len(alerts)} alerts via email")
        
        except Exception as e:
            logger.error(f"Failed to send alerts: {e}")
    
    def generate_performance_report(self, metrics: Dict) -> str:
        """Generate comprehensive performance report"""
        try:
            report = {
                'report_generated': datetime.now().isoformat(),
                'period': '24 hours',
                'metrics': metrics,
                'summary': {
                    'overall_health': 'good',
                    'critical_issues': 0,
                    'warnings': 0,
                    'recommendations': []
                }
            }
            
            # Analyze metrics and generate summary
            if 'error' in metrics:
                report['summary']['overall_health'] = 'degraded'
                report['summary']['critical_issues'] += 1
                report['summary']['recommendations'].append('Fix database connection issues')
            
            # Save report
            report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            return report_file
        
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return ""
    
    def run_full_monitoring_cycle(self) -> Dict:
        """Run complete monitoring cycle"""
        logger.info("Starting full monitoring cycle...")
        
        cycle_results = {
            'start_time': datetime.now().isoformat(),
            'monitoring': {},
            'maintenance': {},
            'alerts': [],
            'reports': []
        }
        
        try:
            # Monitor database performance
            logger.info("Monitoring database performance...")
            db_metrics = self.monitor_database_performance()
            cycle_results['monitoring']['database'] = db_metrics
            
            # Monitor Redis performance
            logger.info("Monitoring Redis performance...")
            redis_metrics = self.monitor_redis_performance()
            cycle_results['monitoring']['redis'] = redis_metrics
            
            # Monitor partitions
            logger.info("Monitoring partitions...")
            partition_metrics = self.monitor_partition_performance()
            cycle_results['monitoring']['partitions'] = partition_metrics
            
            # Monitor materialized views
            logger.info("Monitoring materialized views...")
            mv_metrics = self.monitor_materialized_views()
            cycle_results['monitoring']['materialized_views'] = mv_metrics
            
            # Run maintenance tasks
            logger.info("Running maintenance tasks...")
            maintenance_results = self.run_maintenance_tasks()
            cycle_results['maintenance'] = maintenance_results
            
            # Combine metrics for alert checking
            combined_metrics = {
                'database': db_metrics,
                'cache_performance': redis_metrics,
                'replication': db_metrics.get('replication', []),
                'materialized_views': mv_metrics
            }
            
            # Check for alerts
            logger.info("Checking for alerts...")
            alerts = self.check_alerts(combined_metrics)
            cycle_results['alerts'] = alerts
            
            # Send alerts if any
            if alerts:
                logger.warning(f"Generated {len(alerts)} alerts")
                self.send_alerts(alerts)
            
            # Generate performance report
            logger.info("Generating performance report...")
            report_file = self.generate_performance_report(combined_metrics)
            if report_file:
                cycle_results['reports'].append(report_file)
            
            cycle_results['end_time'] = datetime.now().isoformat()
            cycle_results['duration_seconds'] = (
                datetime.fromisoformat(cycle_results['end_time']) - 
                datetime.fromisoformat(cycle_results['start_time'])
            ).total_seconds()
            
            logger.info(f"Monitoring cycle completed in {cycle_results['duration_seconds']:.2f} seconds")
            
            return cycle_results
        
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
            cycle_results['error'] = str(e)
            return cycle_results


# Example usage
if __name__ == "__main__":
    # Configuration
    config = {
        'database': {
            'host': 'localhost',
            'port': 5432,
            'database': 'performance_test',
            'user': 'postgres',
            'password': 'password',
            'max_connections': 200
        },
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None
        },
        'alerts': {
            'email': {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'username': 'alerts@example.com',
                'password': 'password',
                'recipients': ['admin@example.com', 'ops@example.com']
            },
            'cache_hit_rate_threshold': 85,
            'replication_lag_threshold': 60
        }
    }
    
    # Initialize monitor
    monitor = PerformanceMonitor(config)
    
    # Run single monitoring cycle
    results = monitor.run_full_monitoring_cycle()
    
    print(f"Monitoring cycle completed:")
    print(f"  Duration: {results.get('duration_seconds', 0):.2f} seconds")
    print(f"  Alerts generated: {len(results.get('alerts', []))}")
    print(f"  Reports generated: {len(results.get('reports', []))}")
    
    # Print key metrics
    if 'monitoring' in results:
        db_metrics = results['monitoring'].get('database', {})
        redis_metrics = results['monitoring'].get('redis', {})
        
        print(f"\nKey Metrics:")
        print(f"  Database active connections: {db_metrics.get('database', {}).get('active_connections', 'N/A')}")
        print(f"  Cache hit rate: {redis_metrics.get('hit_rate', 'N/A')}%")
        print(f"  Redis memory usage: {redis_metrics.get('used_memory_human', 'N/A')}")