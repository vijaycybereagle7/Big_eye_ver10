"""
Email Volume Anomaly Detector

Detects abnormal email sending patterns that may indicate:
- Compromised accounts
- Spam campaigns  
- Phishing attacks
- Botnet activity
- Business email compromise (BEC)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import logging

from ..algorithms.isolation_forest_detector import IsolationForestDetector
from ..algorithms.autoencoder_detector_simple import AutoencoderDetector
from ..algorithms.dbscan_detector import DBSCANDetector

logger = logging.getLogger(__name__)


class EmailVolumeDetector:
    """
    Detector for abnormal email volume patterns.
    
    Analyzes email sending patterns to identify potentially malicious
    or suspicious email activity.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the email volume detector.
        
        Args:
            config: Configuration dictionary with detector parameters
        """
        self.config = config or self._get_default_config()
        
        # Initialize the underlying detection algorithm
        model_type = self.config.get('model', 'isolation_forest')
        if model_type == 'isolation_forest':
            self.detector = IsolationForestDetector(self.config.get('isolation_forest_config', {}))
        elif model_type == 'autoencoder':
            self.detector = AutoencoderDetector(self.config.get('autoencoder_config', {}))
        elif model_type == 'dbscan':
            self.detector = DBSCANDetector(self.config.get('dbscan_config', {}))
        else:
            self.detector = IsolationForestDetector(self.config.get('isolation_forest_config', {}))
        
        self.threshold = self.config.get('threshold', 0.8)
        self.is_fitted = False
        
        logger.info("EmailVolumeDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for email volume detection."""
        return {
            'threshold': 0.8,
            'model': 'isolation_forest',
            'features': [
                'email_count',
                'recipient_diversity',
                'attachment_rate',
                'hour_of_day_score',
                'size_variance',
                'unique_domains',
                'failed_delivery_rate',
                'bounce_rate',
                'reply_rate',
                'bulk_indicator'
            ],
            'isolation_forest_config': {
                'contamination': 0.05,
                'n_estimators': 200
            }
        }
    
    def _extract_email_features(self, email_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from email activity data.
        
        Args:
            email_data: Dictionary containing email activity information
            
        Returns:
            Feature vector as numpy array
        """
        try:
            features = []
            
            # Extract basic email metrics
            email_count = email_data.get('email_count', 0)
            recipient_list = email_data.get('recipients', [])
            attachment_count = email_data.get('attachments', 0)
            timestamp = email_data.get('timestamp')
            email_size = email_data.get('email_size', 0)
            
            # 1. Email Count (normalized)
            features.append(min(email_count, 1000))  # Cap at 1000
            
            # 2. Recipient Diversity
            if isinstance(recipient_list, list):
                unique_recipients = len(set(recipient_list))
                total_recipients = max(len(recipient_list), 1)
                diversity_ratio = unique_recipients / total_recipients
                features.append(diversity_ratio)
            else:
                features.append(0.0)
            
            # 3. Attachment Rate
            if email_count > 0:
                attachment_rate = attachment_count / email_count
                features.append(min(attachment_rate, 1.0))
            else:
                features.append(0.0)
            
            # 4. Hour of Day Score (time-based anomaly detection)
            hour_score = self._calculate_time_anomaly_score(timestamp)
            features.append(hour_score)
            
            # 5. Size Variance (check for unusual email sizes)
            size_list = email_data.get('email_sizes', [])
            if size_list:
                size_variance = np.var(size_list) if len(size_list) > 1 else 0.0
                features.append(min(size_variance, 1000000))  # Cap variance
            else:
                features.append(0.0)
            
            # 6. Unique Domains
            domains = email_data.get('recipient_domains', [])
            if isinstance(domains, list):
                unique_domains = len(set(domains))
                features.append(min(unique_domains, 100))  # Cap at 100
            else:
                features.append(0.0)
            
            # 7. Failed Delivery Rate
            failed_deliveries = email_data.get('failed_deliveries', 0)
            if email_count > 0:
                failure_rate = failed_deliveries / email_count
                features.append(min(failure_rate, 1.0))
            else:
                features.append(0.0)
            
            # 8. Bounce Rate
            bounced_emails = email_data.get('bounced_emails', 0)
            if email_count > 0:
                bounce_rate = bounced_emails / email_count
                features.append(min(bounce_rate, 1.0))
            else:
                features.append(0.0)
            
            # 9. Reply Rate
            replies = email_data.get('replies', 0)
            if email_count > 0:
                reply_rate = replies / email_count
                features.append(min(reply_rate, 1.0))
            else:
                features.append(0.0)
            
            # 10. Bulk Indicator
            bulk_score = self._calculate_bulk_score(email_data)
            features.append(bulk_score)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting email features: {str(e)}")
            # Return zeros as fallback
            return np.zeros(len(self.config['features']))
    
    def _calculate_time_anomaly_score(self, timestamp) -> float:
        """Calculate anomaly score based on time of email activity."""
        try:
            if not timestamp:
                return 0.5  # Neutral score for missing timestamp
            
            # Convert to datetime if needed
            if isinstance(timestamp, str):
                dt = pd.to_datetime(timestamp)
            else:
                dt = timestamp
            
            hour = dt.hour
            day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
            
            # Normal business hours (9 AM - 5 PM, Monday-Friday)
            is_business_hour = 9 <= hour <= 17 and day_of_week < 5
            
            # Score based on typical email patterns
            if is_business_hour:
                return 0.1  # Normal business hours - low anomaly score
            elif 6 <= hour <= 22 and day_of_week < 5:
                return 0.3  # Extended business hours - medium score
            elif day_of_week >= 5:
                return 0.4  # Weekend - medium score
            else:
                return 0.8  # Late night/early morning - high score
                
        except Exception as e:
            logger.error(f"Error calculating time anomaly score: {str(e)}")
            return 0.5
    
    def _calculate_bulk_score(self, email_data: Dict[str, Any]) -> float:
        """Calculate bulk email indicator score."""
        try:
            bulk_indicators = 0
            total_indicators = 3
            
            # 1. High recipient count
            recipients = email_data.get('recipients', [])
            if isinstance(recipients, list) and len(recipients) > 50:
                bulk_indicators += 1
            
            # 2. Similar email sizes (batch sending pattern)
            sizes = email_data.get('email_sizes', [])
            if sizes:
                size_variance = np.var(sizes)
                if size_variance < 1000:  # Low variance indicates similar emails
                    bulk_indicators += 1
            
            # 3. High failed delivery rate (indicator of spam)
            failed_deliveries = email_data.get('failed_deliveries', 0)
            email_count = email_data.get('email_count', 1)
            if email_count > 0 and failed_deliveries / email_count > 0.2:
                bulk_indicators += 1
            
            return min(bulk_indicators / total_indicators, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating bulk score: {str(e)}")
            return 0.0
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the email volume detector.
        
        Args:
            training_data: DataFrame containing email activity data
            
        Returns:
            Training results and metrics
        """
        try:
            logger.info("Training email volume detector...")
            
            # Extract features from training data
            feature_matrix = []
            for _, row in training_data.iterrows():
                features = self._extract_email_features(row.to_dict())
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Train the underlying detector
            self.detector.fit(X)
            self.is_fitted = True
            
            # Get model information
            model_info = self.detector.get_model_info()
            
            logger.info("Email volume detector training completed")
            return {
                'status': 'trained',
                'model_type': self.config['model'],
                'features_used': self.config['features'],
                'training_samples': len(X),
                'feature_dimensions': X.shape[1],
                'model_info': model_info
            }
            
        except Exception as e:
            logger.error(f"Error training email volume detector: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def analyze_single_activity(self, activity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single email activity and provide detailed analysis results.
        
        Args:
            activity: Dictionary containing single email activity data
            
        Returns:
            Detailed analysis results including sender, anomaly score, feature breakdown, and risk assessment
        """
        try:
            # Extract basic information
            sender = activity.get('sender', 'unknown')
            timestamp = activity.get('timestamp')
            
            # Extract features for this activity
            features = self._extract_email_features(activity)
            
            # Get anomaly score if detector is fitted
            anomaly_score = 0.0
            is_anomaly = False
            
            if self.is_fitted:
                # Reshape for single sample prediction
                features_reshaped = features.reshape(1, -1)
                
                # Get anomaly score from underlying detector
                if hasattr(self.detector, 'get_anomaly_scores'):
                    scores = self.detector.get_anomaly_scores(features_reshaped)
                    anomaly_score = float(scores[0])
                    is_anomaly = anomaly_score > self.threshold
                else:
                    # Fallback: use simple threshold on bulk indicators
                    bulk_score = self._calculate_bulk_score(activity)
                    anomaly_score = bulk_score * 0.5  # Scale down for fallback
                    is_anomaly = bulk_score > 0.7  # Higher threshold for fallback
            
            # Calculate individual feature scores for breakdown
            feature_breakdown = {}
            feature_names = self.config.get('features', [
                'email_count', 'recipient_diversity', 'attachment_rate', 
                'hour_of_day_score', 'size_variance', 'unique_domains',
                'failed_delivery_rate', 'bounce_rate', 'reply_rate', 'bulk_indicator'
            ])
            
            # Map feature values to names
            if len(features) >= len(feature_names):
                for i, name in enumerate(feature_names):
                    feature_breakdown[name] = {
                        'value': float(features[i]),
                        'contribution': features[i] / np.sum(features) if np.sum(features) > 0 else 0.0
                    }
            
            # Perform risk assessment
            risk_factors = []
            risk_level = "low"
            
            # Check various risk indicators
            email_count = activity.get('email_count', 0)
            if email_count > 500:
                risk_factors.append("High email volume")
            
            if not timestamp:
                risk_factors.append("Missing timestamp")
            
            failed_deliveries = activity.get('failed_deliveries', 0)
            if email_count > 0 and failed_deliveries / email_count > 0.3:
                risk_factors.append("High failure rate")
            
            bounced_emails = activity.get('bounced_emails', 0)
            if email_count > 0 and bounced_emails / email_count > 0.2:
                risk_factors.append("High bounce rate")
            
            recipients = activity.get('recipients', [])
            if isinstance(recipients, list) and len(recipients) > 100:
                risk_factors.append("Large recipient list")
            
            attachments = activity.get('attachments', 0)
            if email_count > 0 and attachments / email_count > 0.8:
                risk_factors.append("High attachment rate")
            
            # Determine overall risk level
            if is_anomaly and anomaly_score > 0.9:
                risk_level = "critical"
            elif is_anomaly and anomaly_score > 0.8:
                risk_level = "high"
            elif is_anomaly or len(risk_factors) >= 2:
                risk_level = "medium"
            
            # Compile detailed analysis result
            analysis_result = {
                'sender': sender,
                'timestamp': timestamp,
                'is_anomaly': is_anomaly,
                'anomaly_score': anomaly_score,
                'threshold': self.threshold,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'features': feature_breakdown,
                'feature_count': len(features),
                'analysis_timestamp': datetime.now().isoformat(),
                'model_used': self.config.get('model', 'unknown'),
                'email_count': email_count,
                'recipient_count': len(recipients) if isinstance(recipients, list) else 0,
                'attachment_count': activity.get('attachments', 0),
                'activity_summary': {
                    'has_timeline': bool(timestamp),
                    'bulk_indicator': self._calculate_bulk_score(activity),
                    'time_anomaly': self._calculate_time_anomaly_score(timestamp),
                    'failed_rate': failed_deliveries / max(email_count, 1),
                    'bounce_rate': bounced_emails / max(email_count, 1)
                }
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing single activity: {str(e)}")
            return {
                'sender': activity.get('sender', 'unknown'),
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'risk_level': 'unknown',
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

    def detect(self, email_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect anomalies in email volume patterns.
        
        Args:
            email_data: List of email activity data
            
        Returns:
            Detection results including anomaly scores and details
        """
        try:
            if not self.is_fitted:
                raise ValueError("Detector must be trained before detection")
            
            # Extract features for all email activities
            feature_matrix = []
            for activity in email_data:
                features = self._extract_email_features(activity)
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Perform detection using the underlying algorithm
            if hasattr(self.detector, 'get_anomaly_scores'):
                anomaly_scores = self.detector.get_anomaly_scores(X)
                anomaly_indices = np.where(anomaly_scores > self.threshold)[0].tolist()
                anomalies_detected = len(anomaly_indices) > 0
            else:
                # Fallback for detectors without get_anomaly_scores
                anomaly_indices = []
                anomalies_detected = False
                anomaly_scores = np.zeros(len(X))
            
            # Compile results
            result = {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomaly_indices),
                'total_emails': len(email_data),
                'anomaly_rate': len(anomaly_indices) / len(email_data) if email_data else 0.0,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': anomaly_scores.tolist() if hasattr(anomaly_scores, 'tolist') else [],
                'threshold': self.threshold,
                'detected_activities': [
                    email_data[i] for i in anomaly_indices if i < len(email_data)
                ] if anomaly_indices else []
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting email anomalies: {str(e)}")
            return {
                'anomalies_detected': False,
                'error': str(e),
                'anomaly_count': 0,
                'total_emails': len(email_data) if email_data else 0
            }