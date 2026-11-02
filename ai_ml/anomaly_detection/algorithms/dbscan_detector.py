"""
DBSCAN Detector

Implementation of scikit-learn's DBSCAN algorithm for density-based anomaly detection.
Effective for detecting anomalies in data with varying density and for finding outliers
in cybersecurity datasets.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import joblib
import logging

logger = logging.getLogger(__name__)


class DBSCANDetector:
    """
    DBSCAN detector for density-based anomaly detection.
    
    Particularly effective for detecting anomalies in data with varying densities
    and for identifying outliers in cybersecurity patterns.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the DBSCAN detector.
        
        Args:
            config: Configuration dictionary with model parameters
        """
        self.config = config or self._get_default_config()
        
        # Initialize the DBSCAN model
        self.model = DBSCAN(
            eps=self.config.get('eps', 0.5),
            min_samples=self.config.get('min_samples', 5),
            metric=self.config.get('metric', 'euclidean'),
            algorithm=self.config.get('algorithm', 'auto'),
            leaf_size=self.config.get('leaf_size', 30),
            n_jobs=self.config.get('n_jobs', -1)
        )
        
        self.is_fitted = False
        self.scaler = StandardScaler()
        self.feature_names = []
        self.eps = self.config.get('eps', 0.5)
        self.min_samples = self.config.get('min_samples', 5)
        
        # Store clustering results
        self.cluster_labels_ = None
        self.core_sample_indices_ = None
        
        logger.info("DBSCANDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for DBSCAN."""
        return {
            'eps': 0.5,          # Maximum distance between two samples
            'min_samples': 5,    # Minimum samples in neighborhood for core point
            'metric': 'euclidean', # Distance metric
            'algorithm': 'auto', # Algorithm for nearest neighbors
            'leaf_size': 30,     # Leaf size for tree-based algorithms
            'n_jobs': -1,        # Number of jobs to run in parallel
            'threshold': 0.5     # Decision threshold (mainly for compatibility)
        }
    
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'DBSCANDetector':
        """
        Fit the DBSCAN detector to training data.
        
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
            
            # Store clustering results
            self.cluster_labels_ = self.model.labels_
            self.core_sample_indices_ = self.model.core_sample_indices_
            
            # Store feature names if available
            if hasattr(X, 'columns'):
                self.feature_names = X.columns.tolist()
            else:
                self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            # Log clustering results
            n_clusters = len(set(self.cluster_labels_)) - (1 if -1 in self.cluster_labels_ else 0)
            n_noise = list(self.cluster_labels_).count(-1)
            
            logger.info(f"DBSCAN fitted successfully: {n_clusters} clusters, {n_noise} noise points (outliers)")
            logger.info(f"Training data: {X.shape[0]} samples with {X.shape[1]} features")
            
            return self
            
        except Exception as e:
            logger.error(f"Error fitting DBSCAN: {str(e)}")
            raise
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict whether samples are anomalies using fitted clusters.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Binary predictions: 1 for anomalies (noise points), 0 for normal
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        try:
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Predict cluster labels for new samples
            cluster_labels = self.model.fit_predict(X_scaled)
            
            # Convert to binary predictions (noise points are anomalies)
            binary_predictions = (cluster_labels == -1).astype(int)
            
            return binary_predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {str(e)}")
            # For new samples that can't be clustered, consider them anomalies
            return np.ones(len(X), dtype=int)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate distance-based anomaly scores.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Anomaly scores based on distance to nearest cluster center
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before calculating decision function")
        
        try:
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Calculate distance to nearest cluster center
            scores = self._calculate_distance_scores(X_scaled)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating decision function: {str(e)}")
            return np.ones(len(X))
    
    def _calculate_distance_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate anomaly scores based on distance to nearest cluster.
        
        Args:
            X: Scaled test data
            
        Returns:
            Distance-based anomaly scores
        """
        scores = np.zeros(len(X))
        
        for i, sample in enumerate(X):
            # Find the minimum distance to any core sample
            if len(self.core_sample_indices_) > 0:
                # Get core sample points
                core_samples = X[self.core_sample_indices_]
                
                # Calculate distances to core samples
                distances = np.linalg.norm(core_samples - sample, axis=1)
                min_distance = np.min(distances)
                
                # Score based on distance (higher distance = higher anomaly score)
                scores[i] = min_distance
            
            else:
                # No core samples found, consider all points as anomalies
                scores[i] = self.eps * 2
        
        return scores
    
    def detect(self, X: np.ndarray, threshold: float = None) -> np.ndarray:
        """
        Detect anomalies using DBSCAN clustering.
        
        Args:
            X: Test data (n_samples, n_features)
            threshold: Not used for DBSCAN (included for API compatibility)
            
        Returns:
            Binary array indicating anomalies (1) and normal samples (0)
        """
        try:
            # Use DBSCAN prediction (noise points are anomalies)
            predictions = self.predict(X)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return np.ones(len(X), dtype=int)  # Consider all as anomalies on error
    
    def get_anomaly_scores(self, X: np.ndarray) -> np.ndarray:
        """
        Get anomaly scores for samples.
        
        Args:
            X: Test data (n_samples, n_features)
            
        Returns:
            Normalized anomaly scores (higher values indicate more anomalous samples)
        """
        try:
            # Get distance-based scores
            scores = self.decision_function(X)
            
            # Normalize scores to [0, 1] range
            if len(scores) > 0 and np.max(scores) > np.min(scores):
                scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error getting anomaly scores: {str(e)}")
            return np.ones(len(X))
    
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
            return 1.0  # Return maximum anomaly score on error
    
    def get_cluster_info(self) -> Dict[str, Any]:
        """
        Get information about the discovered clusters.
        
        Returns:
            Dictionary containing cluster information
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before getting cluster info")
        
        try:
            n_clusters = len(set(self.cluster_labels_)) - (1 if -1 in self.cluster_labels_ else 0)
            n_noise = list(self.cluster_labels_).count(-1)
            
            # Calculate cluster sizes
            unique_labels = set(self.cluster_labels_)
            cluster_sizes = {}
            for label in unique_labels:
                if label != -1:  # Ignore noise points
                    cluster_sizes[f'cluster_{label}'] = int(np.sum(self.cluster_labels_ == label))
            
            return {
                'n_clusters': int(n_clusters),
                'n_noise_points': int(n_noise),
                'cluster_sizes': cluster_sizes,
                'total_samples': len(self.cluster_labels_),
                'noise_ratio': float(n_noise / len(self.cluster_labels_)),
                'eps': self.eps,
                'min_samples': self.min_samples
            }
            
        except Exception as e:
            logger.error(f"Error getting cluster info: {str(e)}")
            return {}
    
    def estimate_eps_parameter(self, X: np.ndarray, k: int = 4) -> float:
        """
        Estimate optimal epsilon parameter using k-distance graph.
        
        Args:
            X: Training data
            k: Number of nearest neighbors (default: min_samples)
            
        Returns:
            Estimated epsilon value
        """
        try:
            # Scale the features
            X_scaled = self.scaler.fit_transform(X)
            
            # Use k-nearest neighbors to find distances
            n_neighbors = min(k, len(X) - 1)
            if n_neighbors < 1:
                return self.eps
            
            # Fit nearest neighbors
            nbrs = NearestNeighbors(n_neighbors=n_neighbors)
            nbrs.fit(X_scaled)
            
            # Find distances to k-th nearest neighbor
            distances, _ = nbrs.kneighbors(X_scaled)
            k_distances = distances[:, k-1]  # k-th nearest neighbor distances
            
            # Sort distances in descending order
            k_distances = np.sort(k_distances)[::-1]
            
            # Find the "elbow" point in the k-distance graph
            # This is a simple heuristic - in practice, more sophisticated methods exist
            n_points = len(k_distances)
            if n_points < 10:
                return self.eps
            
            # Calculate the second derivative to find the elbow
            first_derivatives = np.diff(k_distances)
            second_derivatives = np.diff(first_derivatives)
            
            # Find the point with maximum curvature (second derivative)
            if len(second_derivatives) > 0:
                elbow_index = np.argmax(np.abs(second_derivatives)) + 2
                if elbow_index < len(k_distances):
                    estimated_eps = k_distances[elbow_index]
                    return float(estimated_eps)
            
            # Fallback: use the average of the k-distances
            return float(np.mean(k_distances))
            
        except Exception as e:
            logger.error(f"Error estimating eps parameter: {str(e)}")
            return self.eps
    
    def update_model(self, X_new: np.ndarray, y_new: np.ndarray = None) -> 'DBSCANDetector':
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
                'eps': self.eps,
                'min_samples': self.min_samples,
                'cluster_labels_': self.cluster_labels_,
                'core_sample_indices_': self.core_sample_indices_
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
            self.eps = model_data.get('eps', self.eps)
            self.min_samples = model_data.get('min_samples', self.min_samples)
            self.cluster_labels_ = model_data.get('cluster_labels_', None)
            self.core_sample_indices_ = model_data.get('core_sample_indices_', None)
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model."""
        info = {
            'model_type': 'DBSCAN',
            'is_fitted': self.is_fitted,
            'eps': self.eps,
            'min_samples': self.min_samples,
            'metric': self.model.metric,
            'n_features': len(self.feature_names),
            'feature_names': self.feature_names,
            'config': self.config
        }
        
        if self.is_fitted:
            cluster_info = self.get_cluster_info()
            info.update(cluster_info)
        
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