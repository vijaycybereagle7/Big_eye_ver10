"""
Fast-Flux Detector

Detects fast-flux networks commonly used by:
- Botnets
- Malware C&C infrastructure
- Phishing campaigns
- Command and control servers
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import statistics
import logging

from ..algorithms.isolation_forest_detector import IsolationForestDetector
from ..algorithms.autoencoder_detector_simple import AutoencoderDetector

logger = logging.getLogger(__name__)


class FastFluxDetector:
    """Detector for fast-flux network infrastructure."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        model_type = self.config.get('model', 'isolation_forest')
        if model_type == 'isolation_forest':
            self.detector = IsolationForestDetector(self.config.get('isolation_forest_config', {}))
        elif model_type == 'autoencoder':
            self.detector = AutoencoderDetector(self.config.get('autoencoder_config', {}))
        else:
            self.detector = IsolationForestDetector(self.config.get('isolation_forest_config', {}))
        
        self.threshold = self.config.get('threshold', 0.8)
        self.is_fitted = False

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'threshold': 0.8,
            'model': 'isolation_forest',
            'features': [
                'dns_response_time',
                'ip_rotation_rate',
                'ttl_variance',
                'ip_geographic_spread',
                'domain_age',
                'nameserver_count',
                'a_record_count',
                'subdomain_count'
            ],
            'isolation_forest_config': {
                'contamination': 0.1,
                'n_estimators': 150
            },
            'autoencoder_config': {
                'encoding_dim': 16,
                'epochs': 100,
                'batch_size': 32
            }
        }

    def _extract_flux_features(self, domain_data: Dict[str, Any]) -> np.ndarray:
        """Extract features for fast-flux detection from domain data."""
        try:
            features = []
            
            # 1. DNS Response Time
            dns_response_times = domain_data.get('dns_response_times', [])
            if dns_response_times:
                avg_response_time = statistics.mean(dns_response_times)
                response_variance = statistics.variance(dns_response_times) if len(dns_response_times) > 1 else 0
                features.append(min(avg_response_time, 5000))  # Cap at 5 seconds
                features.append(min(response_variance, 1000000))  # Cap variance
            else:
                features.extend([0.0, 0.0])
            
            # 2. IP Rotation Rate
            ip_addresses = domain_data.get('ip_addresses', [])
            time_window_hours = domain_data.get('observation_window_hours', 24)
            if ip_addresses and time_window_hours > 0:
                rotation_rate = len(set(ip_addresses)) / time_window_hours
                features.append(min(rotation_rate, 100))  # Cap at 100 IPs per hour
            else:
                features.append(0.0)
            
            # 3. TTL Variance
            ttl_values = domain_data.get('ttl_values', [])
            if ttl_values:
                ttl_variance = statistics.variance(ttl_values)
                features.append(min(ttl_variance, 86400))  # Cap at 24 hours
            else:
                features.append(0.0)
            
            # 4. IP Geographic Spread
            ip_locations = domain_data.get('ip_locations', [])
            if ip_locations:
                # Calculate geographic spread based on country codes
                unique_countries = len(set(ip_locations))
                features.append(min(unique_countries, 50))  # Cap at 50 countries
            else:
                features.append(0.0)
            
            # 5. Domain Age
            domain_age_days = domain_data.get('domain_age_days', 0)
            features.append(min(domain_age_days, 3650))  # Cap at 10 years
            
            # 6. Nameserver Count
            nameservers = domain_data.get('nameservers', [])
            features.append(min(len(nameservers), 20))  # Cap at 20 nameservers
            
            # 7. A Record Count
            a_records = domain_data.get('a_records', [])
            features.append(min(len(a_records), 100))  # Cap at 100 A records
            
            # 8. Subdomain Count
            subdomains = domain_data.get('subdomains', [])
            features.append(min(len(subdomains), 1000))  # Cap at 1000 subdomains
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting fast-flux features: {str(e)}")
            return np.zeros(len(self.config['features']))

    def _analyze_flux_patterns(self, domain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze fast-flux patterns across domains."""
        try:
            analysis = {
                'botnet_indicators': 0.0,
                'cc_indicators': 0.0,
                'phishing_indicators': 0.0
            }
            
            if not domain_data:
                return analysis
            
            # Aggregate metrics across all domains
            total_ips = set()
            total_response_times = []
            total_ttl_variance = 0
            domain_count = len(domain_data)
            
            for domain in domain_data:
                ips = domain.get('ip_addresses', [])
                total_ips.update(ips)
                
                response_times = domain.get('dns_response_times', [])
                total_response_times.extend(response_times)
                
                ttl_values = domain.get('ttl_values', [])
                if ttl_values and len(ttl_values) > 1:
                    domain_ttl_var = statistics.variance(ttl_values)
                    total_ttl_variance += domain_ttl_var
            
            # Botnet indicators
            if domain_count > 0:
                unique_ip_ratio = len(total_ips) / domain_count
                if unique_ip_ratio > 10:  # Many IPs per domain
                    analysis['botnet_indicators'] += 0.4
                
                avg_ttl_variance = total_ttl_variance / domain_count
                if avg_ttl_variance > 3600:  # High TTL variance
                    analysis['botnet_indicators'] += 0.3
            
            # C&C indicators
            if total_response_times:
                avg_response_time = statistics.mean(total_response_times)
                response_std = statistics.stdev(total_response_times) if len(total_response_times) > 1 else 0
                
                if avg_response_time > 1000:  # Slow responses
                    analysis['cc_indicators'] += 0.3
                
                if response_std > 500:  # High variance in response times
                    analysis['cc_indicators'] += 0.4
            
            # Phishing indicators
            suspicious_tlds = 0
            for domain in domain_data:
                full_domain = domain.get('domain', '').lower()
                if '.' in full_domain:
                    tld = full_domain.split('.')[-1]
                    if tld in ['tk', 'ml', 'cf', 'ga']:  # Free TLDs
                        suspicious_tlds += 1
            
            if domain_count > 0:
                suspicious_ratio = suspicious_tlds / domain_count
                if suspicious_ratio > 0.3:
                    analysis['phishing_indicators'] += 0.5
            
            # Normalize indicators
            for key in analysis:
                analysis[key] = min(analysis[key], 1.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing fast-flux patterns: {str(e)}")
            return {
                'botnet_indicators': 0.0,
                'cc_indicators': 0.0,
                'phishing_indicators': 0.0
            }

    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train the fast-flux detector."""
        try:
            logger.info("Training fast-flux detector...")
            
            feature_matrix = []
            for _, row in training_data.iterrows():
                features = self._extract_flux_features(row.to_dict())
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            self.detector.fit(X)
            self.is_fitted = True
            
            return {
                'status': 'trained',
                'model_type': self.config['model'],
                'features_used': self.config['features'],
                'training_samples': len(X),
                'model_info': self.detector.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"Error training fast-flux detector: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def detect(self, domain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect fast-flux networks."""
        try:
            if not self.is_fitted:
                raise ValueError("Detector must be trained before detection")
            
            feature_matrix = []
            for domain in domain_data:
                features = self._extract_flux_features(domain)
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            if hasattr(self.detector, 'get_anomaly_scores'):
                anomaly_scores = self.detector.get_anomaly_scores(X)
                anomaly_indices = np.where(anomaly_scores > self.threshold)[0].tolist()
                anomalies_detected = len(anomaly_indices) > 0
            else:
                anomaly_indices = []
                anomalies_detected = False
                anomaly_scores = np.zeros(len(X))
            
            # Analyze flux patterns
            pattern_analysis = self._analyze_flux_patterns(domain_data)
            
            return {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomaly_indices),
                'total_domains': len(domain_data),
                'anomaly_rate': len(anomaly_indices) / len(domain_data) if domain_data else 0.0,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': anomaly_scores.tolist(),
                'threshold': self.threshold,
                'pattern_analysis': pattern_analysis,
                'detected_domains': [
                    domain_data[i] for i in anomaly_indices if i < len(domain_data)
                ] if anomaly_indices else []
            }
            
        except Exception as e:
            logger.error(f"Error detecting fast-flux: {str(e)}")
            return {
                'anomalies_detected': False,
                'error': str(e),
                'anomaly_count': 0,
                'total_domains': len(domain_data) if domain_data else 0
            }