"""
Compromised Account Detector

Detects compromised user accounts based on:
- Login time patterns
- Location changes
- Action sequences
- Device fingerprinting
- Behavioral anomalies
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import logging

from ..algorithms.dbscan_detector import DBSCANDetector
from ..algorithms.autoencoder_detector_simple import AutoencoderDetector

logger = logging.getLogger(__name__)


class CompromisedAccountDetector:
    """Detector for compromised user accounts."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        model_type = self.config.get('model', 'dbscan')
        if model_type == 'dbscan':
            self.detector = DBSCANDetector(self.config.get('dbscan_config', {}))
        elif model_type == 'autoencoder':
            self.detector = AutoencoderDetector(self.config.get('autoencoder_config', {}))
        else:
            self.detector = DBSCANDetector(self.config.get('dbscan_config', {}))
        
        self.threshold = self.config.get('threshold', 0.75)
        self.is_fitted = False

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'threshold': 0.75,
            'model': 'dbscan',
            'features': [
                'login_time_pattern',
                'location_change',
                'action_sequence',
                'device_fingerprint',
                'session_duration',
                'actions_per_minute',
                'failed_login_ratio',
                'geographic_velocity'
            ],
            'dbscan_config': {
                'eps': 0.5,
                'min_samples': 5
            },
            'autoencoder_config': {
                'encoding_dim': 16,
                'epochs': 100,
                'batch_size': 32
            }
        }

    def _extract_account_features(self, account_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from account activity data."""
        try:
            features = []
            
            # 1. Login Time Pattern (0-1, higher means more anomalous)
            login_hour = account_data.get('login_hour', 12)
            if 9 <= login_hour <= 17:  # Business hours
                features.append(0.1)
            elif 6 <= login_hour <= 22:  # Extended hours
                features.append(0.3)
            else:  # Off-hours
                features.append(0.8)
            
            # 2. Location Change (geographic distance from usual location)
            usual_location = account_data.get('usual_location', [0, 0])
            current_location = account_data.get('current_location', [0, 0])
            distance = self._calculate_distance(usual_location, current_location)
            features.append(min(distance, 1000))  # Cap at 1000 km
            
            # 3. Action Sequence (unusual action patterns)
            action_sequence = account_data.get('action_sequence', [])
            normal_actions = ['view', 'read', 'login', 'search']
            suspicious_actions = [a for a in action_sequence if a not in normal_actions]
            features.append(min(len(suspicious_actions) / max(len(action_sequence), 1), 1.0))
            
            # 4. Device Fingerprint
            usual_device = account_data.get('usual_device', 'unknown')
            current_device = account_data.get('current_device', 'unknown')
            device_match = 1.0 if usual_device == current_device else 0.0
            features.append(device_match)
            
            # 5. Session Duration
            session_duration = account_data.get('session_duration_minutes', 30)
            features.append(min(session_duration, 480))  # Cap at 8 hours
            
            # 6. Actions per Minute
            actions_per_minute = account_data.get('actions_per_minute', 1.0)
            features.append(min(actions_per_minute, 10.0))
            
            # 7. Failed Login Ratio
            total_logins = account_data.get('total_logins', 1)
            failed_logins = account_data.get('failed_logins', 0)
            failed_ratio = failed_logins / max(total_logins, 1)
            features.append(min(failed_ratio, 1.0))
            
            # 8. Geographic Velocity (speed between locations)
            time_diff = account_data.get('time_between_locations_hours', 1)
            distance = self._calculate_distance(usual_location, current_location)
            velocity = distance / max(time_diff, 0.1)
            features.append(min(velocity, 900))  # Cap at 900 km/h (speed of sound)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting account features: {str(e)}")
            return np.zeros(len(self.config['features']))

    def _calculate_distance(self, loc1: List[float], loc2: List[float]) -> float:
        """Calculate distance between two geographic coordinates."""
        try:
            if len(loc1) >= 2 and len(loc2) >= 2:
                # Simplified distance calculation (in degrees, converted to km)
                lat_diff = abs(loc1[0] - loc2[0])
                lon_diff = abs(loc1[1] - loc2[1])
                # Rough conversion: 1 degree ≈ 111 km
                return (lat_diff**2 + lon_diff**2)**0.5 * 111
            return 0.0
        except:
            return 0.0

    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train the compromised account detector."""
        try:
            logger.info("Training compromised account detector...")
            
            feature_matrix = []
            for _, row in training_data.iterrows():
                features = self._extract_account_features(row.to_dict())
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
            logger.error(f"Error training compromised account detector: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def detect(self, account_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect compromised accounts."""
        try:
            if not self.is_fitted:
                raise ValueError("Detector must be trained before detection")
            
            feature_matrix = []
            for account in account_data:
                features = self._extract_account_features(account)
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
            
            return {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomaly_indices),
                'total_accounts': len(account_data),
                'anomaly_rate': len(anomaly_indices) / len(account_data) if account_data else 0.0,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': anomaly_scores.tolist(),
                'threshold': self.threshold,
                'detected_accounts': [
                    account_data[i] for i in anomaly_indices if i < len(account_data)
                ] if anomaly_indices else []
            }
            
        except Exception as e:
            logger.error(f"Error detecting compromised accounts: {str(e)}")
            return {
                'anomalies_detected': False,
                'error': str(e),
                'anomaly_count': 0,
                'total_accounts': len(account_data) if account_data else 0
            }