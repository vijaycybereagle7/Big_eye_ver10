"""
Core Anomaly Detection Engine

Main orchestration engine that coordinates different anomaly detection algorithms
and use case specific detectors for comprehensive cybersecurity monitoring.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from ..algorithms.isolation_forest_detector import IsolationForestDetector
from ..algorithms.dbscan_detector import DBSCANDetector
from ..algorithms.autoencoder_detector_simple import AutoencoderDetector
from ..use_cases.domain_registration import DomainRegistrationDetector
from ..use_cases.email_volume import EmailVolumeDetector
from ..use_cases.zero_day_threats import ZeroDayThreatDetector
from ..use_cases.compromised_accounts import CompromisedAccountDetector
from ..use_cases.dga_detection import DGADetector
from ..use_cases.fast_flux import FastFluxDetector
from ..utils.model_trainer import ModelTrainer
from ..utils.alert_manager import AlertManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetectionEngine:
    """
    Main anomaly detection engine that coordinates multiple detection algorithms
    and use case specific detectors for comprehensive cybersecurity monitoring.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the anomaly detection engine.
        
        Args:
            config: Configuration dictionary containing model parameters and thresholds
        """
        self.config = config or self._get_default_config()
        
        # Initialize detection algorithms
        self.detectors = {
            'isolation_forest': IsolationForestDetector(self.config['isolation_forest']),
            'dbscan': DBSCANDetector(self.config['dbscan']),
            'autoencoder': AutoencoderDetector(self.config['autoencoder'])
        }
        
        # Initialize use case specific detectors
        self.use_case_detectors = {
            'domain_registration': DomainRegistrationDetector(self.config['domain_registration']),
            'email_volume': EmailVolumeDetector(self.config['email_volume']),
            'zero_day_threats': ZeroDayThreatDetector(self.config['zero_day_threats']),
            'compromised_accounts': CompromisedAccountDetector(self.config['compromised_accounts']),
            'dga_detection': DGADetector(self.config['dga_detection']),
            'fast_flux': FastFluxDetector(self.config['fast_flux'])
        }
        
        # Initialize supporting utilities
        self.model_trainer = ModelTrainer(self.config['training'])
        self.alert_manager = AlertManager(self.config['alerts'])
        
        # Initialize scalers
        self.scaler = StandardScaler() if self.config['scaler'] == 'standard' else MinMaxScaler()
        
        # Model storage
        self.trained_models = {}
        self.model_metadata = {}
        
        logger.info("AnomalyDetectionEngine initialized successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for all components."""
        return {
            'scaler': 'standard',
            'isolation_forest': {
                'contamination': 0.1,
                'n_estimators': 100,
                'random_state': 42,
                'n_jobs': -1
            },
            'dbscan': {
                'eps': 0.5,
                'min_samples': 5,
                'metric': 'euclidean',
                'n_jobs': -1
            },
            'autoencoder': {
                'encoding_dim': 32,
                'epochs': 100,
                'batch_size': 32,
                'validation_split': 0.2,
                'patience': 10
            },
            'domain_registration': {
                'threshold': 0.7,
                'features': ['registration_age', 'domains_per_registrar', 'domain_length'],
                'model': 'autoencoder'
            },
            'email_volume': {
                'threshold': 0.8,
                'features': ['email_count', 'recipient_diversity', 'attachment_rate'],
                'model': 'isolation_forest'
            },
            'zero_day_threats': {
                'threshold': 0.9,
                'features': ['file_entropy', 'api_calls', 'network_behavior'],
                'model': 'ensemble'
            },
            'compromised_accounts': {
                'threshold': 0.75,
                'features': ['login_time_pattern', 'location_change', 'action_sequence'],
                'model': 'dbscan'
            },
            'dga_detection': {
                'threshold': 0.85,
                'features': ['char_frequency', 'n_gram_analysis', 'domain_structure'],
                'model': 'autoencoder'
            },
            'fast_flux': {
                'threshold': 0.8,
                'features': ['dns_response_time', 'ip_rotation_rate', 'ttl_variance'],
                'model': 'isolation_forest'
            },
            'training': {
                'test_size': 0.2,
                'cross_validation_folds': 5,
                'early_stopping': True,
                'model_save_path': 'models/'
            },
            'alerts': {
                'severity_thresholds': {
                    'critical': 0.9,
                    'high': 0.8,
                    'medium': 0.7,
                    'low': 0.6
                },
                'alert_cooldown': 300,  # 5 minutes
                'notification_channels': ['log', 'console']
            }
        }
    
    def train_models(self, training_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Train all detection models using provided training data.
        
        Args:
            training_data: Dictionary containing training data for each use case
            
        Returns:
            Dictionary containing training results and model performance metrics
        """
        training_results = {}
        
        logger.info("Starting model training process...")
        
        for use_case, data in training_data.items():
            if use_case not in self.use_case_detectors:
                logger.warning(f"No detector found for use case: {use_case}")
                continue
                
            logger.info(f"Training model for {use_case}...")
            
            # Get the detector and configuration
            detector = self.use_case_detectors[use_case]
            config = self.config.get(use_case, {})
            
            # Train the model
            if isinstance(detector, DomainRegistrationDetector):
                # Special handling for domain registration
                result = detector.train(data)
            elif isinstance(detector, EmailVolumeDetector):
                result = detector.train(data)
            elif isinstance(detector, ZeroDayThreatDetector):
                result = detector.train(data)
            elif isinstance(detector, CompromisedAccountDetector):
                result = detector.train(data)
            elif isinstance(detector, DGADetector):
                result = detector.train(data)
            elif isinstance(detector, FastFluxDetector):
                result = detector.train(data)
            else:
                # Use generic training approach
                result = self._train_generic_detector(detector, data, config)
            
            training_results[use_case] = result
            
        # Train ensemble models
        ensemble_results = self._train_ensemble_models(training_data)
        training_results['ensemble'] = ensemble_results
        
        logger.info("Model training completed successfully")
        return training_results
    
    def _train_generic_detector(self, detector, data: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Train a generic detector with standard preprocessing."""
        # Prepare features
        features = config.get('features', data.columns.tolist())
        
        # Check if features exist in data columns
        available_features = [f for f in features if f in data.columns]
        if not available_features:
            # If no specified features are available, use all numeric columns
            available_features = [col for col in data.columns if data[col].dtype in ['int64', 'float64']]
        
        if not available_features:
            return {
                'status': 'failed',
                'error': 'No valid features found in data',
                'model_type': config.get('model', 'unknown'),
                'features_used': []
            }
        
        X = data[available_features].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train based on the specified model type
        model_type = config.get('model', 'isolation_forest')
        
        try:
            if model_type == 'isolation_forest':
                detector.fit(X_scaled)
            elif model_type == 'dbscan':
                detector.fit(X_scaled)
            elif model_type == 'autoencoder':
                detector.fit(X_scaled)
            
            return {
                'status': 'trained',
                'model_type': model_type,
                'features_used': available_features,
                'data_shape': X_scaled.shape
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e),
                'model_type': model_type,
                'features_used': available_features
            }
    
    def _train_ensemble_models(self, training_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Train ensemble models combining multiple algorithms."""
        ensemble_results = {}
        
        for use_case, data in training_data.items():
            config = self.config.get(use_case, {})
            
            # Combine predictions from multiple models
            predictions = {}
            probabilities = {}
            
            for detector_name, detector in self.detectors.items():
                try:
                    # Prepare features
                    features = config.get('features', data.columns.tolist())
                    X = data[features].fillna(0)
                    X_scaled = self.scaler.fit_transform(X)
                    
                    # Get predictions
                    if hasattr(detector, 'predict'):
                        pred = detector.predict(X_scaled)
                        predictions[detector_name] = pred
                    
                    if hasattr(detector, 'decision_function'):
                        prob = detector.decision_function(X_scaled)
                        probabilities[detector_name] = prob
                        
                except Exception as e:
                    logger.error(f"Error training {detector_name} for {use_case}: {str(e)}")
                    continue
            
            # Store ensemble predictions
            ensemble_results[use_case] = {
                'predictions': predictions,
                'probabilities': probabilities,
                'status': 'ensemble_trained'
            }
        
        return ensemble_results
    
    def detect_anomalies(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """
        Detect anomalies across all use cases.
        
        Args:
            data: Dictionary containing data for each use case
            
        Returns:
            Dictionary containing detection results for each use case
        """
        detection_results = {}
        
        logger.info("Starting anomaly detection process...")
        
        for use_case, data_df in data.items():
            if use_case not in self.use_case_detectors:
                logger.warning(f"No detector found for use case: {use_case}")
                continue
            
            try:
                # Get detector and configuration
                detector = self.use_case_detectors[use_case]
                config = self.config.get(use_case, {})
                
                # Perform detection
                result = self._perform_detection(detector, data_df, config, use_case)
                detection_results[use_case] = result
                
                # Generate alerts for detected anomalies
                if result.get('anomalies_detected', False):
                    self._generate_alerts(use_case, result, config)
                    
            except Exception as e:
                logger.error(f"Error detecting anomalies for {use_case}: {str(e)}")
                detection_results[use_case] = {
                    'error': str(e),
                    'anomalies_detected': False
                }
        
        logger.info(f"Anomaly detection completed. Found anomalies in {len([k for k, v in detection_results.items() if v.get('anomalies_detected', False)])} use cases")
        return detection_results
    
    def _perform_detection(self, detector, data: pd.DataFrame, config: Dict[str, Any], use_case: str) -> Dict[str, Any]:
        """Perform detection using a specific detector."""
        # Prepare features
        features = config.get('features', data.columns.tolist())
        
        # Check if features exist in data columns
        available_features = [f for f in features if f in data.columns]
        if not available_features:
            # If no specified features are available, use all numeric columns
            available_features = [col for col in data.columns if data[col].dtype in ['int64', 'float64']]
        
        if not available_features:
            return {
                'anomalies_detected': False,
                'anomaly_count': 0,
                'total_records': len(data),
                'anomaly_rate': 0.0,
                'anomaly_indices': [],
                'anomaly_scores': [],
                'error': 'No valid features found in data',
                'features_used': []
            }
        
        X = data[available_features].fillna(0)
        
        # Scale features if needed
        try:
            X_scaled = self.scaler.transform(X)
        except:
            # If scaler not fitted, fit and transform
            X_scaled = self.scaler.fit_transform(X)
        
        # Perform detection based on detector type
        if isinstance(detector, AutoencoderDetector):
            # Autoencoder specific detection
            anomalies = detector.detect(X_scaled)
            anomaly_scores = detector.get_anomaly_scores(X_scaled)
        elif isinstance(detector, IsolationForestDetector):
            # Isolation Forest specific detection
            anomalies = detector.detect(X_scaled)
            anomaly_scores = detector.get_anomaly_scores(X_scaled)
        elif isinstance(detector, DBSCANDetector):
            # DBSCAN specific detection
            anomalies = detector.detect(X_scaled)
            anomaly_scores = detector.get_anomaly_scores(X_scaled)
        else:
            # Generic detection approach
            try:
                if hasattr(detector, 'predict'):
                    anomalies = detector.predict(X_scaled)
                    if hasattr(detector, 'decision_function'):
                        anomaly_scores = detector.decision_function(X_scaled)
                    else:
                        anomaly_scores = np.zeros(len(X_scaled))
                else:
                    anomalies = np.zeros(len(X_scaled), dtype=int)
                    anomaly_scores = np.zeros(len(X_scaled))
            except Exception as e:
                logger.error(f"Detection error for {use_case}: {str(e)}")
                anomalies = np.zeros(len(X_scaled), dtype=int)
                anomaly_scores = np.zeros(len(X_scaled))
        
        # Apply threshold
        threshold = config.get('threshold', 0.7)
        if hasattr(anomaly_scores, '__len__') and len(anomaly_scores) > 0:
            anomalies = (anomaly_scores > threshold).astype(int)
        
        # Compile results
        result = {
            'anomalies_detected': np.sum(anomalies) > 0,
            'anomaly_count': int(np.sum(anomalies)),
            'total_records': len(X_scaled),
            'anomaly_rate': float(np.sum(anomalies) / len(X_scaled)) if len(X_scaled) > 0 else 0.0,
            'anomaly_indices': np.where(anomalies == 1)[0].tolist(),
            'anomaly_scores': anomaly_scores.tolist() if hasattr(anomaly_scores, 'tolist') else anomaly_scores,
            'threshold_used': threshold,
            'features_used': available_features
        }
        
        return result
    
    def _generate_alerts(self, use_case: str, detection_result: Dict[str, Any], config: Dict[str, Any]):
        """Generate alerts for detected anomalies."""
        threshold = detection_result.get('threshold', 0.7)
        anomaly_rate = detection_result.get('anomaly_rate', 0.0)
        
        # Determine severity based on anomaly rate
        if anomaly_rate >= self.config['alerts']['severity_thresholds']['critical']:
            severity = 'critical'
        elif anomaly_rate >= self.config['alerts']['severity_thresholds']['high']:
            severity = 'high'
        elif anomaly_rate >= self.config['alerts']['severity_thresholds']['medium']:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Create alert
        alert = {
            'timestamp': datetime.now().isoformat(),
            'use_case': use_case,
            'severity': severity,
            'anomaly_count': detection_result.get('anomaly_count', 0),
            'anomaly_rate': anomaly_rate,
            'threshold': threshold,
            'details': {
                'total_records': detection_result.get('total_records', 0),
                'anomaly_indices': detection_result.get('anomaly_indices', [])
            }
        }
        
        # Send alert through alert manager
        self.alert_manager.send_alert(alert)
    
    def evaluate_model(self, test_data: Dict[str, pd.DataFrame], ground_truth: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """
        Evaluate model performance against ground truth labels.
        
        Args:
            test_data: Test data for each use case
            ground_truth: Ground truth labels for each use case
            
        Returns:
            Evaluation metrics for each use case
        """
        evaluation_results = {}
        
        for use_case, data in test_data.items():
            if use_case not in ground_truth:
                continue
                
            # Perform detection
            detection_result = self.detect_anomalies({use_case: data})
            predictions = detection_result.get(use_case, {}).get('anomaly_indices', [])
            
            # Create binary prediction array
            y_pred = np.zeros(len(data))
            for idx in predictions:
                if idx < len(y_pred):
                    y_pred[idx] = 1
            
            # Get ground truth
            y_true = ground_truth[use_case]
            
            # Calculate metrics
            try:
                accuracy = accuracy_score(y_true, y_pred)
                precision = precision_score(y_true, y_pred, zero_division=0)
                recall = recall_score(y_true, y_pred, zero_division=0)
                f1 = f1_score(y_true, y_pred, zero_division=0)
                
                evaluation_results[use_case] = {
                    'accuracy': float(accuracy),
                    'precision': float(precision),
                    'recall': float(recall),
                    'f1_score': float(f1)
                }
            except Exception as e:
                logger.error(f"Error evaluating {use_case}: {str(e)}")
                evaluation_results[use_case] = {
                    'error': str(e)
                }
        
        return evaluation_results
    
    def save_models(self, path: str = 'models/'):
        """Save trained models to disk."""
        import os
        
        os.makedirs(path, exist_ok=True)
        
        # Save detector configurations
        for use_case, detector in self.use_case_detectors.items():
            try:
                if hasattr(detector, 'save_model'):
                    detector.save_model(f"{path}{use_case}_model.pkl")
            except Exception as e:
                logger.error(f"Error saving model for {use_case}: {str(e)}")
        
        # Save scaler
        import pickle
        with open(f"{path}scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save configuration
        with open(f"{path}config.json", 'w') as f:
            json.dump(self.config, f, indent=2)
        
        logger.info(f"Models saved to {path}")
    
    def load_models(self, path: str = 'models/'):
        """Load trained models from disk."""
        import os
        import pickle
        
        # Load scaler
        scaler_path = f"{path}scaler.pkl"
        if os.path.exists(scaler_path):
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
        
        # Load configuration
        config_path = f"{path}config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        
        logger.info(f"Models loaded from {path}")
    
    def get_real_time_detection(self, data_point: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform real-time anomaly detection on a single data point.
        
        Args:
            data_point: Single data point to analyze
            
        Returns:
            Detection results for the data point
        """
        results = {}
        
        for use_case, detector in self.use_case_detectors.items():
            try:
                config = self.config.get(use_case, {})
                features = config.get('features', [])
                
                # Extract relevant features
                feature_vector = [data_point.get(feature, 0) for feature in features]
                feature_array = np.array([feature_vector])
                
                # Scale features
                try:
                    scaled_features = self.scaler.transform(feature_array)
                except:
                    scaled_features = feature_array
                
                # Perform detection
                if isinstance(detector, AutoencoderDetector):
                    anomaly_score = detector.get_anomaly_score(scaled_features[0])
                    is_anomaly = anomaly_score > config.get('threshold', 0.7)
                elif hasattr(detector, 'decision_function'):
                    anomaly_score = detector.decision_function(scaled_features)[0]
                    is_anomaly = anomaly_score > config.get('threshold', 0.7)
                else:
                    anomaly_score = 0.0
                    is_anomaly = False
                
                results[use_case] = {
                    'is_anomaly': is_anomaly,
                    'anomaly_score': float(anomaly_score),
                    'threshold': config.get('threshold', 0.7),
                    'severity': self._calculate_severity(anomaly_score, config.get('threshold', 0.7))
                }
                
            except Exception as e:
                logger.error(f"Error in real-time detection for {use_case}: {str(e)}")
                results[use_case] = {
                    'is_anomaly': False,
                    'error': str(e)
                }
        
        return results
    
    def _calculate_severity(self, anomaly_score: float, threshold: float) -> str:
        """Calculate severity based on anomaly score and threshold."""
        if anomaly_score >= threshold * 1.5:
            return 'critical'
        elif anomaly_score >= threshold * 1.2:
            return 'high'
        elif anomaly_score >= threshold:
            return 'medium'
        else:
            return 'low'