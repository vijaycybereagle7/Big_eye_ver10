"""
Zero-Day Threat Detector

Detects potential zero-day threats based on:
- File entropy analysis
- API call patterns
- Network behavior anomalies
- Behavioral analysis
- Sandbox execution results
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import hashlib
import re
from collections import Counter
import logging

from ..algorithms.autoencoder_detector_simple import AutoencoderDetector
from ..algorithms.isolation_forest_detector import IsolationForestDetector

logger = logging.getLogger(__name__)


class ZeroDayThreatDetector:
    """Detector for potential zero-day threats using behavioral analysis."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        
        # Initialize ensemble of detectors
        model_type = self.config.get('model', 'ensemble')
        if model_type == 'ensemble':
            self.detectors = {
                'autoencoder': AutoencoderDetector(self.config.get('autoencoder_config', {})),
                'isolation_forest': IsolationForestDetector(self.config.get('isolation_forest_config', {}))
            }
        elif model_type == 'autoencoder':
            self.detectors = {'autoencoder': AutoencoderDetector(self.config.get('autoencoder_config', {}))}
        else:
            self.detectors = {'isolation_forest': IsolationForestDetector(self.config.get('isolation_forest_config', {}))}
        
        self.threshold = self.config.get('threshold', 0.9)
        self.is_fitted = False

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'threshold': 0.9,
            'model': 'ensemble',
            'features': [
                'file_entropy',
                'api_calls',
                'network_behavior',
                'file_size',
                'section_count',
                'import_count',
                'suspicious_strings',
                'packing_indicators',
                'anti_analysis'
            ],
            'autoencoder_config': {
                'encoding_dim': 64,
                'epochs': 200,
                'batch_size': 32
            },
            'isolation_forest_config': {
                'contamination': 0.02,
                'n_estimators': 300
            }
        }

    def _extract_threat_features(self, sample_data: Dict[str, Any]) -> np.ndarray:
        """Extract features from malware sample data."""
        try:
            features = []
            
            # 1. File Entropy
            entropy = sample_data.get('entropy', 0.0)
            features.append(entropy)
            
            # 2. API Calls (suspicious API usage)
            api_calls = sample_data.get('api_calls', [])
            suspicious_apis = ['CreateProcess', 'WriteFile', 'RegSetValue', 'InternetOpen', 'URLDownloadToFile']
            suspicious_count = sum(1 for api in api_calls if any(sa in api.lower() for sa in suspicious_apis))
            features.append(min(suspicious_count / max(len(api_calls), 1), 1.0))
            
            # 3. Network Behavior
            network_indicators = sample_data.get('network_indicators', 0)
            features.append(min(network_indicators, 1.0))
            
            # 4. File Size
            file_size = sample_data.get('file_size', 0)
            features.append(min(file_size, 1000000))  # Cap at 1MB
            
            # 5. Section Count
            section_count = sample_data.get('section_count', 0)
            features.append(min(section_count, 20))
            
            # 6. Import Count
            import_count = sample_data.get('import_count', 0)
            features.append(min(import_count, 100))
            
            # 7. Suspicious Strings
            suspicious_strings = sample_data.get('suspicious_strings', [])
            features.append(min(len(suspicious_strings), 50))
            
            # 8. Packing Indicators
            packing_score = sample_data.get('packing_score', 0.0)
            features.append(packing_score)
            
            # 9. Anti-Analysis Techniques
            anti_analysis = sample_data.get('anti_analysis_count', 0)
            features.append(min(anti_analysis, 10))
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting threat features: {str(e)}")
            return np.zeros(len(self.config['features']))

    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train the zero-day threat detector."""
        try:
            logger.info("Training zero-day threat detector...")
            
            feature_matrix = []
            for _, row in training_data.iterrows():
                features = self._extract_threat_features(row.to_dict())
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Train ensemble
            training_results = {}
            for name, detector in self.detectors.items():
                detector.fit(X)
                training_results[name] = detector.get_model_info()
            
            self.is_fitted = True
            
            return {
                'status': 'trained',
                'model_type': 'ensemble',
                'features_used': self.config['features'],
                'training_samples': len(X),
                'detectors_trained': len(self.detectors),
                'training_results': training_results
            }
            
        except Exception as e:
            logger.error(f"Error training zero-day threat detector: {str(e)}")
            return {'status': 'failed', 'error': str(e)}

    def detect(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect potential zero-day threats."""
        try:
            if not self.is_fitted:
                raise ValueError("Detector must be trained before detection")
            
            feature_matrix = []
            for sample in sample_data:
                features = self._extract_threat_features(sample)
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Ensemble prediction
            all_scores = []
            for name, detector in self.detectors.items():
                if hasattr(detector, 'get_anomaly_scores'):
                    scores = detector.get_anomaly_scores(X)
                    all_scores.append(scores)
            
            if all_scores:
                # Average scores across all detectors
                ensemble_scores = np.mean(all_scores, axis=0)
                anomaly_indices = np.where(ensemble_scores > self.threshold)[0].tolist()
                anomalies_detected = len(anomaly_indices) > 0
            else:
                ensemble_scores = np.zeros(len(X))
                anomaly_indices = []
                anomalies_detected = False
            
            return {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomaly_indices),
                'total_samples': len(sample_data),
                'anomaly_rate': len(anomaly_indices) / len(sample_data) if sample_data else 0.0,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': ensemble_scores.tolist(),
                'threshold': self.threshold,
                'detected_samples': [
                    sample_data[i] for i in anomaly_indices if i < len(sample_data)
                ] if anomaly_indices else []
            }
            
        except Exception as e:
            logger.error(f"Error detecting zero-day threats: {str(e)}")
            return {
                'anomalies_detected': False,
                'error': str(e),
                'anomaly_count': 0,
                'total_samples': len(sample_data) if sample_data else 0
            }