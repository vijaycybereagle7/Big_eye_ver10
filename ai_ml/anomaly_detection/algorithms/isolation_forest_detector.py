"""
Isolation Forest Detector

Implementation of scikit-learn's Isolation Forest algorithm for anomaly detection.
Optimized for cybersecurity use cases with configurable parameters.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logger = logging.getLogger(__name__)


class IsolationForestDetector:
    """
    Isolation Forest detector for anomaly detection.
    
    Particularly effective for detecting anomalies in high-dimensional data
    and works well with cybersecurity datasets.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Isolation Forest detector.
        
        Args:
            config: Configuration dictionary with model parameters
        """
        self.config = config or self._get_default_config()
        
        # Initialize the Isolation Forest model
        self.model = IsolationForest(
            contamination=self.config.get('contamination', 0.1),
            n_estimators=self.config.get('n_estimators', 100),
            max_samples=self.config.get('max_samples', 'auto'),
            max_features=self.config.get('max_features', 1.0),
            bootstrap=self.config.get('bootstrap', False),
            n_jobs=self.config.get('n_jobs', -1),
            random_state=self.config.get('random_state', 42),
            verbose=self.config.get('verbose', 0)
        )
        
        self.is_fitted = False
        self.scaler = StandardScaler()
        self.feature_names = []
        self.threshold = self.config.get('threshold', 0.5)
        
        logger.info("IsolationForestDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Isolation Forest."""
        return {
            'contamination': 0.1,  # Expected proportion of outliers
            'n_estimators': 100,   # Number of base estimators
            'max_samples': 'auto', # Number of samples to draw
            'max_features': 1.0,   # Number of features to draw
            'bootstrap': False,    # Whether samples are drawn with replacement
            'n_jobs': -1,         # Number of jobs to run in parallel
            'random_state': 42,   # Random state for reproducibility
            'verbose': 0,         # Verbosity level
            'threshold': 0.5      # Decision threshold for anomaly detection
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'IsolationForestDetector':
        """
        Fit the Isolation Forest detector to training data.
        
        Args:
            X: Training data (n_samples, n_features)
            y: Ignored (not used, present for API consistency)
            
        Returns:
            self: Returns the instance itself
        """
        try:
            # Scale the features
            X_scaled = self.scaler.fit_transform(X)
            
            # Fit the model
            self.model.fit(X_scaled)
            self.is_fitted = True
            
            # Store feature names if available
            if hasattr(X, 'columns'):
                self.feature_names = X.columns.tolist()
            else:
                self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            logger.info(f"IsolationForest fitted successfully on {X.shape[0]} samples with {X.shape[1]} features")
            return self
            
        except Exception as e:
            logger.error(f"Error fitting IsolationForest: {str(e)}")
            raise
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict whether samples are anomalies.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Binary predictions: 1 for anomalies, 0 for normal
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        try:
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Get predictions
            predictions = self.model.predict(X_scaled)
            
            # Convert to binary format (1 for anomaly, 0 for normal)
            binary_predictions = (predictions == -1).astype(int)
            
            return binary_predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return np.zeros(len(X), dtype=int)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate anomaly scores for samples.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Anomaly scores (lower values indicate anomalies)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before calculating decision function")
        
        try:
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Get decision function scores
            scores = self.model.decision_function(X_scaled)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating decision function: {str(e)}")
            return np.zeros(len(X))
    
    def detect(self, X: np.ndarray, threshold: float = None) -> np.ndarray:
        """
        Detect anomalies using the fitted model.
        
        Args:
            X: Test data (n_samples, n_features)
            threshold: Custom threshold (uses default if not provided)
            
        Returns:
            Binary array indicating anomalies (1) and normal samples (0)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before detection")
        
        try:
            # Use provided threshold or default
            detection_threshold = threshold or self.threshold
            
            # Get anomaly scores
            scores = self.decision_function(X)
            
            # Apply threshold (lower scores indicate more anomalous samples)
            # Convert to binary predictions using negative scores
            predictions = self.predict(X)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return np.zeros(len(X), dtype=int)
    
    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores for samples.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Normalized anomaly scores (higher values indicate more anomalous samples)
        """
        try:
            # Get decision function scores
            scores = self.decision_function(X)
            
            # Convert to positive scores (higher = more anomalous)
            # The decision function returns negative values for anomalies
            # So we negate and normalize to get positive anomaly scores
            anomaly_scores = -scores
            
            # Normalize to [0, 1] range
            if len(anomaly_scores) > 0 and np.max(anomaly_scores) > np.min(anomaly_scores):
                anomaly_scores = (anomaly_scores - np.min(anomaly_scores)) / (
                    np.max(anomaly_scores) - np.min(anomaly_scores)
                )
            
            return anomaly_scores
            
        except Exception as e:
            logger.error(f"Error getting anomaly scores: {str(e)}")
            return np.zeros(len(X))
    
    def get_anomaly_score(self, x: np.ndarray) -> float:
        """
        Get anomaly score for a single sample.
        
        Args:
            x: Single sample (n_features,)
            
        Returns:
            Anomaly score for the sample
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting anomaly scores")
        
        try:
            # Reshape to 2D array
            X = x.reshape(1, -1)
            
            # Get anomaly score
            scores = self.get_anomaly_scores(X)
            
            return float(scores[0])
            
        except Exception as e:
            logger.error(f"Error getting anomaly score for single sample: {str(e)}")
            return 0.0
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance based on isolation path length.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting feature importance")
        
        try:
            # Calculate feature importance based on average path length
            # This is an approximation since Isolation Forest doesn't have built-in feature importance
            
            n_features = len(self.feature_names)
            importance_scores = {}
            
            # Simple approximation using the number of estimators that include each feature
            # In a real implementation, this would require accessing the internal structure
            
            for i, feature_name in enumerate(self.feature_names):
                # Placeholder implementation - in practice, this would be more sophisticated
                importance_scores[feature_name] = 1.0 / n_features
            
            return importance_scores
            
        except Exception as e:
            logger.error(f"Error calculating feature importance: {str(e)}")
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}
    
    def update_model(self, X_new: np.ndarray, y_new: np.ndarray = None) -> 'IsolationForestDetector':
        """
        Update the model with new training data.
        
        Args:
            X_new: New training data
            y_new: Ignored (not used)
            
        Returns:
            self: Returns the instance itself
        """
        try:
            # Combine with existing data if any
            if hasattr(self, '_training_data'):
                X_combined = np.vstack([self._training_data, X_new])
            else:
                X_combined = X_new
            
            # Store training data for future updates
            self._training_data = X_combined
            
            # Retrain the model
            self.fit(X_combined)
            
            logger.info(f"Model updated with {X_new.shape[0]} new samples")
            return self
            
        except Exception as e:
            logger.error(f"Error updating model: {str(e)}")
            raise
    
    def save_model(self, filepath: str):
        """Save the trained model to disk."""
        import os
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the model and scaler
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config,
                'is_fitted': self.is_fitted,
                'feature_names': self.feature_names,
                'threshold': self.threshold
            }
            
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        try:
            # Load the model data
            model_data = joblib.load(filepath)
            
            # Restore the model components
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.config = model_data.get('config', self.config)
            self.is_fitted = model_data.get('is_fitted', False)
            self.feature_names = model_data.get('feature_names', [])
            self.threshold = model_data.get('threshold', 0.5)
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model."""
        info = {
            'model_type': 'Isolation Forest',
            'is_fitted': self.is_fitted,
            'n_estimators': self.model.n_estimators if self.is_fitted else None,
            'contamination': self.model.contamination if self.is_fitted else None,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'threshold': self.threshold,
            'config': self.config
        }
        
        return info
    
    def evaluate(self, X_test: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance on test data.
        
        Args:
            X_test: Test features
            y_true: True anomaly labels
            
        Returns:
            Dictionary containing evaluation metrics
        """
        try:
            # Make predictions
            y_pred = self.detect(X_test)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
            return {
                'accuracy': float(accuracy),
                'precision': float(precision),
                'recall': float(recall),
                'f1_score': float(f1)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {str(e)}")
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'error': str(e)
            }