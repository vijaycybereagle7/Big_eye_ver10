"""
Autoencoder Detector

Implementation of TensorFlow-based autoencoder for deep learning anomaly detection.
Effective for detecting complex patterns and anomalies in high-dimensional data
commonly found in cybersecurity datasets.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib
import logging
import os

logger = logging.getLogger(__name__)


class AutoencoderDetector:
    """
    Autoencoder detector for deep learning-based anomaly detection.
    
    Uses a neural network autoencoder to learn normal data patterns and
    detect anomalies based on reconstruction error.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Autoencoder detector.
        
        Args:
            config: Configuration dictionary with model parameters
        """
        self.config = config or self._get_default_config()
        
        # Initialize the autoencoder model
        self.model = None
        self.encoder = None
        self.decoder = None
        
        # Training parameters
        self.encoding_dim = self.config.get('encoding_dim', 32)
        self.epochs = self.config.get('epochs', 100)
        self.batch_size = self.config.get('batch_size', 32)
        self.validation_split = self.config.get('validation_split', 0.2)
        self.patience = self.config.get('patience', 10)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        
        # Other components
        self.scaler = StandardScaler()
        self.feature_names = []
        self.threshold = self.config.get('threshold', 0.5)
        self.reconstruction_errors = []
        self.is_fitted = False
        
        # Training history
        self.history = None
        
        logger.info("AutoencoderDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for Autoencoder."""
        return {
            'encoding_dim': 32,      # Dimension of the encoded representation
            'epochs': 100,           # Number of epochs to train
            'batch_size': 32,        # Batch size for training
            'validation_split': 0.2, # Fraction of training data for validation
            'patience': 10,          # Early stopping patience
            'learning_rate': 0.001,  # Learning rate for optimizer
            'threshold': 0.5,        # Decision threshold for anomaly detection
            'optimizer': 'adam',     # Optimizer for training
            'loss': 'mse',          # Loss function
            'hidden_layers': [64, 32], # Hidden layer sizes for encoder/decoder
            'activation': 'relu',    # Activation function
            'dropout_rate': 0.2      # Dropout rate for regularization
        }
    
    def _build_autoencoder(self, input_dim: int) -> Tuple[keras.Model, keras.Model, keras.Model]:
        """
        Build the autoencoder architecture.
        
        Args:
            input_dim: Dimension of input features
            
        Returns:
            Tuple of (autoencoder, encoder, decoder) models
        """
        try:
            # Input layer
            input_layer = keras.Input(shape=(input_dim,))
            
            # Encoder layers
            encoded = input_layer
            hidden_layers = self.config.get('hidden_layers', [64, 32])
            
            for i, hidden_dim in enumerate(hidden_layers):
                encoded = layers.Dense(hidden_dim, activation=self.config.get('activation', 'relu'))(encoded)
                if self.config.get('dropout_rate', 0) > 0:
                    encoded = layers.Dropout(self.config.get('dropout_rate'))(encoded)
            
            # Bottleneck layer (encoding)
            bottleneck = layers.Dense(self.encoding_dim, activation='linear')(encoded)
            
            # Decoder layers (reverse of encoder)
            decoded = bottleneck
            for i, hidden_dim in enumerate(reversed(hidden_layers)):
                decoded = layers.Dense(hidden_dim, activation=self.config.get('activation', 'relu'))(decoded)
                if self.config.get('dropout_rate', 0) > 0:
                    decoded = layers.Dropout(self.config.get('dropout_rate'))(decoded)
            
            # Output layer
            output_layer = layers.Dense(input_dim, activation='linear')(decoded)
            
            # Build models
            autoencoder = keras.Model(input_layer, output_layer, name='autoencoder')
            encoder = keras.Model(input_layer, bottleneck, name='encoder')
            
            # Build decoder separately
            decoder_input = keras.Input(shape=(self.encoding_dim,))
            decoder = decoder_input
            
            # Add decoder layers in reverse order
            for i, hidden_dim in enumerate(reversed(hidden_layers)):
                decoder = layers.Dense(hidden_dim, activation=self.config.get('activation', 'relu'))(decoder)
            decoder = layers.Dense(input_dim, activation='linear')(decoder)
            
            decoder = keras.Model(decoder_input, decoder, name='decoder')
            
            # Compile autoencoder
            autoencoder.compile(
                optimizer=self.config.get('optimizer', 'adam'),
                loss=self.config.get('loss', 'mse'),
                metrics=['mae']
            )
            
            logger.info(f"Autoencoder architecture built: {input_dim} -> {self.encoding_dim} -> {input_dim}")
            
            return autoencoder, encoder, decoder
            
        except Exception as e:
            logger.error(f"Error building autoencoder: {str(e)}")
            raise
    
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'AutoencoderDetector':
        """
        Fit the autoencoder detector to training data.
        
        Args:
            X: Training data (n_samples, n_features)
            y: Ignored (not used, present for API consistency)
            
        Returns:
            self: Returns the instance itself
        """
        try:
            # Scale the features
            X_scaled = self.scaler.fit_transform(X)
            
            # Build the autoencoder
            self.model, self.encoder, self.decoder = self._build_autoencoder(X_scaled.shape[1])
            
            # Prepare callbacks for training
            callbacks = []
            
            # Early stopping
            if self.config.get('early_stopping', True):
                early_stopping = keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=self.patience,
                    restore_best_weights=True
                )
                callbacks.append(early_stopping)
            
            # Reduce learning rate on plateau
            if self.config.get('reduce_lr', True):
                reduce_lr = keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=self.patience // 2,
                    min_lr=1e-7,
                    verbose=0
                )
                callbacks.append(reduce_lr)
            
            # Model checkpoint (save best model)
            if self.config.get('save_best', True):
                checkpoint_path = '/tmp/autoencoder_best.h5'
                checkpoint = keras.callbacks.ModelCheckpoint(
                    checkpoint_path,
                    monitor='val_loss',
                    save_best_only=True,
                    save_weights_only=False,
                    verbose=0
                )
                callbacks.append(checkpoint)
            
            # Train the model
            logger.info("Starting autoencoder training...")
            self.history = self.model.fit(
                X_scaled, X_scaled,  # Autoencoder learns to reconstruct input
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=self.validation_split,
                callbacks=callbacks,
                verbose=1,
                shuffle=True
            )
            
            # Load best weights if saved
            if self.config.get('save_best', True) and os.path.exists(checkpoint_path):
                self.model = keras.models.load_model(checkpoint_path)
                os.remove(checkpoint_path)
            
            # Calculate reconstruction errors for training data
            self._calculate_reconstruction_errors(X_scaled)
            
            # Update fitted status
            self.is_fitted = True
            
            # Store feature names if available
            if hasattr(X, 'columns'):
                self.feature_names = X.columns.tolist()
            else:
                self.feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
            logger.info("Autoencoder training completed successfully")
            return self
            
        except Exception as e:
            logger.error(f"Error fitting autoencoder: {str(e)}")
            raise
    
    def _calculate_reconstruction_errors(self, X_scaled: np.ndarray):
        """Calculate reconstruction errors for training data."""
        try:
            # Predict reconstructions
            X_reconstructed = self.model.predict(X_scaled, verbose=0)
            
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
            # Predict reconstructions
            X_reconstructed = self.model.predict(X_scaled, verbose=0)
            
            # Calculate reconstruction errors (MSE for each sample)
            reconstruction_errors = np.mean(np.square(X_scaled - X_reconstructed), axis=1)
            
            return reconstruction_errors
            
        except Exception as e:
            logger.error(f"Error calculating reconstruction errors: {str(e)}")
            return np.zeros(len(X_scaled))
    
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
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Get reconstruction errors
            reconstruction_errors = self._get_reconstruction_errors(X_scaled)
            
            return reconstruction_errors
            
        except Exception as e:
            logger.error(f"Error calculating decision function: {str(e)}")
            return np.zeros(len(X))
    
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
    
    def encode(self, X: np.ndarray) -> np.ndarray:
        """
        Encode data to the bottleneck layer representation.
        
        Args:
            X: Input data
            
        Returns:
            Encoded representation of the data
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before encoding")
        
        try:
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Encode the data
            encoded_data = self.encoder.predict(X_scaled, verbose=0)
            
            return encoded_data
            
        except Exception as e:
            logger.error(f"Error encoding data: {str(e)}")
            return np.zeros((len(X), self.encoding_dim))
    
    def decode(self, encoded_data: np.ndarray) -> np.ndarray:
        """
        Decode encoded data back to original space.
        
        Args:
            encoded_data: Encoded data
            
        Returns:
            Decoded (reconstructed) data
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before decoding")
        
        try:
            # Decode the data
            decoded_data = self.decoder.predict(encoded_data, verbose=0)
            
            return decoded_data
            
        except Exception as e:
            logger.error(f"Error decoding data: {str(e)}")
            return np.zeros((len(encoded_data), len(self.feature_names)))
    
    def get_training_history(self) -> Dict[str, List[float]]:
        """
        Get training history.
        
        Returns:
            Dictionary containing training metrics
        """
        if self.history is None:
            return {}
        
        return {
            'loss': self.history.history.get('loss', []),
            'val_loss': self.history.history.get('val_loss', []),
            'mae': self.history.history.get('mae', []),
            'val_mae': self.history.history.get('val_mae', [])
        }
    
    def save_model(self, filepath: str):
        """Save the trained model to disk."""
        import os
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the autoencoder model
            model_path = filepath.replace('.pkl', '_autoencoder.h5')
            self.model.save(model_path)
            
            # Save additional components
            additional_data = {
                'encoder': self.encoder,
                'decoder': self.decoder,
                'scaler': self.scaler,
                'config': self.config,
                'is_fitted': self.is_fitted,
                'feature_names': self.feature_names,
                'threshold': self.threshold,
                'reconstruction_errors': self.reconstruction_errors,
                'encoding_dim': self.encoding_dim,
                'epochs': self.epochs,
                'batch_size': self.batch_size,
                'validation_split': self.validation_split,
                'patience': self.patience
            }
            
            # Save as joblib file
            joblib.dump(additional_data, filepath)
            
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def load_model(self, filepath: str):
        """Load a trained model from disk."""
        try:
            # Load additional components
            additional_data = joblib.load(filepath)
            
            # Restore components
            self.encoder = additional_data['encoder']
            self.decoder = additional_data['decoder']
            self.scaler = additional_data['scaler']
            self.config = additional_data.get('config', self.config)
            self.is_fitted = additional_data.get('is_fitted', False)
            self.feature_names = additional_data.get('feature_names', [])
            self.threshold = additional_data.get('threshold', self.threshold)
            self.reconstruction_errors = additional_data.get('reconstruction_errors', [])
            self.encoding_dim = additional_data.get('encoding_dim', self.encoding_dim)
            self.epochs = additional_data.get('epochs', self.epochs)
            self.batch_size = additional_data.get('batch_size', self.batch_size)
            self.validation_split = additional_data.get('validation_split', self.validation_split)
            self.patience = additional_data.get('patience', self.patience)
            
            # Load the autoencoder model
            model_path = filepath.replace('.pkl', '_autoencoder.h5')
            self.model = keras.models.load_model(model_path)
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the trained model."""
        info = {
            'model_type': 'Autoencoder',
            'is_fitted': self.is_fitted,
            'encoding_dim': self.encoding_dim,
            'input_dim': len(self.feature_names),
            'epochs_trained': self.epochs,
            'batch_size': self.batch_size,
            'validation_split': self.validation_split,
            'patience': self.patience,
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