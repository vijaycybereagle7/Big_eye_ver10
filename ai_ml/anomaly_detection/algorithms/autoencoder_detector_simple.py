"""
Autoencoder Detector (Simplified version)

A simplified version of autoencoder for anomaly detection without TensorFlow dependency.
Uses scikit-learn based autoencoder approximation for demonstration purposes.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.neural_network import MLPRegressor
import joblib
import logging

logger = logging.getLogger(__name__)


class AutoencoderDetector:
    """
    Simplified Autoencoder detector for anomaly detection.
    
    Uses PCA and MLPRegressor as a simplified approximation of autoencoder.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the simplified autoencoder detector.
        
        Args:
            config: Configuration dictionary with model parameters
        """
        self.config = config or self._get_default_config()
        
        # Training parameters
        self.encoding_dim = self.config.get('encoding_dim', 32)
        self.max_iter = self.config.get('max_iter', 500)
        
        # Components (initialized lazily during fit)
        self.scaler = StandardScaler()
        self.encoder = None
        self.decoder = MLPRegressor(
            hidden_layer_sizes=(self.encoding_dim,),
            max_iter=self.max_iter,
            random_state=42,
            alpha=0.01
        )
        
        self.feature_names = []
        self.threshold = self.config.get('threshold', 0.5)
        self.reconstruction_errors = []
        self.is_fitted = False
        
        logger.info("Simplified AutoencoderDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for simplified autoencoder."""
        return {
            'encoding_dim': 32,      # Dimension of the encoded representation
            'max_iter': 500,         # Maximum iterations for MLP
            'threshold': 0.5,        # Decision threshold for anomaly detection
            'alpha': 0.01,          # Regularization parameter
            'hidden_layer_sizes': (32,)
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'AutoencoderDetector':
        """
        Fit the simplified autoencoder detector to training data.
        
        Args:
            X: Training data (n_samples, n_features)
            y: Ignored (not used, present for API consistency)
            
        Returns:
            self: Returns the instance itself
        """
        try:
            # Store feature names if available
            if hasattr(X, 'columns'):
                self.feature_names = X.columns.tolist()
            else:
                self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            # Handle small datasets
            n_samples, n_features = X.shape
            max_components = min(n_samples - 1, n_features, 10)  # Limit components
            encoding_dim = min(self.encoding_dim, max_components)
            
            if encoding_dim < 1:
                # For very small datasets, use a simpler approach
                logger.warning(f"Dataset too small for autoencoder (n_samples={n_samples}, n_features={n_features}). Using Isolation Forest fallback.")
                from ..algorithms.isolation_forest_detector import IsolationForestDetector
                self.fallback_detector = IsolationForestDetector({'contamination': 0.1})
                self.fallback_detector.fit(X)
                self.is_fitted = True
                return self
            
            # Update encoder with appropriate dimensions
            self.encoder = PCA(n_components=encoding_dim)
            
            # Scale the features
            X_scaled = self.scaler.fit_transform(X)
            
            # Encode using PCA
            encoded_data = self.encoder.fit_transform(X_scaled)
            
            # Train decoder to reconstruct original data from encoded representation
            self.decoder.fit(encoded_data, X_scaled)
            
            # Calculate reconstruction errors for training data
            self._calculate_reconstruction_errors(X_scaled)
            
            # Update fitted status
            self.is_fitted = True
            
            logger.info("Simplified autoencoder training completed successfully")
            return self
            
        except Exception as e:
            logger.error(f"Error fitting simplified autoencoder: {str(e)}")
            raise
    
    def _calculate_reconstruction_errors(self, X_scaled: np.ndarray):
        """Calculate reconstruction errors for training data."""
        try:
            # Encode
            encoded_data = self.encoder.transform(X_scaled)
            
            # Decode (reconstruct)
            X_reconstructed = self.decoder.predict(encoded_data)
            
            # Calculate reconstruction errors (MSE for each sample)
            reconstruction_errors = np.mean(np.square(X_scaled - X_reconstructed), axis=1)
            self.reconstruction_errors = reconstruction_errors
            
            logger.info(f"Calculated reconstruction errors: mean={np.mean(reconstruction_errors):.4f}, std={np.std(reconstruction_errors):.4f}")
            
        except Exception as e:
            logger.error(f"Error calculating reconstruction errors: {str(e)}")
            self.reconstruction_errors = []
    
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
            # Use fallback detector if available
            if hasattr(self, 'fallback_detector'):
                predictions = self.fallback_detector.predict(X)
                return predictions
            
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Get reconstruction errors
            reconstruction_errors = self._get_reconstruction_errors(X_scaled)
            
            # Apply threshold
            threshold = self._get_threshold()
            predictions = (reconstruction_errors > threshold).astype(int)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            return np.zeros(len(X), dtype=int)
    
    def _get_reconstruction_errors(self, X_scaled: np.ndarray) -> np.ndarray:
        """Calculate reconstruction errors for test data."""
        try:
            # Encode
            encoded_data = self.encoder.transform(X_scaled)
            
            # Decode (reconstruct)
            X_reconstructed = self.decoder.predict(encoded_data)
            
            # Calculate reconstruction errors (MSE for each sample)
            reconstruction_errors = np.mean(np.square(X_scaled - X_reconstructed), axis=1)
            
            return reconstruction_errors
            
        except Exception as e:
            logger.error(f"Error calculating reconstruction errors: {str(e)}")
            return np.zeros(len(X_scaled))
    
    def _get_threshold(self) -> float:
        """Get the anomaly detection threshold."""
        if len(self.reconstruction_errors) > 0:
            # Use percentile-based threshold
            percentile = self.config.get('threshold_percentile', 95)
            threshold = np.percentile(self.reconstruction_errors, percentile)
        else:
            # Fallback to default threshold
            threshold = self.threshold
        
        return threshold
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate anomaly scores based on reconstruction error.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Anomaly scores (higher values indicate more anomalous samples)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before calculating decision function")
        
        try:
            # Use fallback detector if available
            if hasattr(self, 'fallback_detector'):
                scores = self.fallback_detector.decision_function(X)
                return -scores  # Convert to anomaly scores
            
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Get reconstruction errors
            reconstruction_errors = self._get_reconstruction_errors(X_scaled)
            
            return reconstruction_errors
            
        except Exception as e:
            logger.error(f"Error calculating decision function: {str(e)}")
            return np.zeros(len(X))
    
    def detect(self, X: np.ndarray, threshold: float = None) -> np.ndarray:
        """
        Detect anomalies using reconstruction error.
        
        Args:
            X: Test data (n_samples, n_features)
            threshold: Custom threshold (uses calculated threshold if not provided)
            
        Returns:
            Binary array indicating anomalies (1) and normal samples (0)
        """
        try:
            if threshold is not None:
                # Use custom threshold
                reconstruction_errors = self._get_reconstruction_errors(X)
                predictions = (reconstruction_errors > threshold).astype(int)
            else:
                # Use standard prediction method
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
            # Get reconstruction errors
            reconstruction_errors = self._get_reconstruction_errors(X)
            
            # Normalize scores to [0, 1] range
            if len(reconstruction_errors) > 0 and np.max(reconstruction_errors) > np.min(reconstruction_errors):
                min_error = np.min(reconstruction_errors)
                max_error = np.max(reconstruction_errors)
                normalized_scores = (reconstruction_errors - min_error) / (max_error - min_error)
            else:
                normalized_scores = reconstruction_errors
            
            return normalized_scores
            
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
        try:
            # Reshape to 2D array
            X = x.reshape(1, -1)
            
            # Get anomaly score
            scores = self.get_anomaly_scores(X)
            
            return float(scores[0])
            
        except Exception as e:
            logger.error(f"Error getting anomaly score for single sample: {str(e)}")
            return 0.0
    
    def save_model(self, filepath: str):
        """Save the trained model to disk."""
        import os
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the components
            model_data = {
                'encoder': self.encoder,
                'decoder': self.decoder,
                'scaler': self.scaler,
                'config': self.config,
                'is_fitted': self.is_fitted,
                'feature_names': self.feature_names,
                'threshold': self.threshold,
                'reconstruction_errors': self.reconstruction_errors,
                'encoding_dim': self.encoding_dim,
                'max_iter': self.max_iter
            }
            
            # Save as joblib file
            joblib.dump(model_data, filepath)
            
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        try:
            # Load model data
            model_data = joblib.load(filepath)
            
            # Restore components
            self.encoder = model_data['encoder']
            self.decoder = model_data['decoder']
            self.scaler = model_data['scaler']
            self.config = model_data.get('config', self.config)
            self.is_fitted = model_data.get('is_fitted', False)
            self.feature_names = model_data.get('feature_names', [])
            self.threshold = model_data.get('threshold', self.threshold)
            self.reconstruction_errors = model_data.get('reconstruction_errors', [])
            self.encoding_dim = model_data.get('encoding_dim', self.encoding_dim)
            self.max_iter = model_data.get('max_iter', self.max_iter)
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model."""
        info = {
            'model_type': 'Simplified Autoencoder (PCA + MLP)',
            'is_fitted': self.is_fitted,
            'encoding_dim': self.encoding_dim,
            'input_dim': len(self.feature_names),
            'max_iter': self.max_iter,
            'threshold': self.threshold,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'config': self.config
        }
        
        if self.is_fitted and len(self.reconstruction_errors) > 0:
            info.update({
                'reconstruction_error_mean': float(np.mean(self.reconstruction_errors)),
                'reconstruction_error_std': float(np.std(self.reconstruction_errors)),
                'reconstruction_error_min': float(np.min(self.reconstruction_errors)),
                'reconstruction_error_max': float(np.max(self.reconstruction_errors))
            })
        
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