"""
Model Trainer

Utilities for training, validating, and managing anomaly detection models
across different use cases and algorithms.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Comprehensive model training utilities for anomaly detection.
    
    Provides methods for:
    - Cross-validation
    - Hyperparameter tuning
    - Model comparison
    - Training history tracking
    - Model persistence
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the model trainer.
        
        Args:
            config: Configuration dictionary with training parameters
        """
        self.config = config or self._get_default_config()
        
        # Training history and results storage
        self.training_history = {}
        self.model_comparisons = {}
        self.best_models = {}
        
        logger.info("ModelTrainer initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for model training."""
        return {
            'test_size': 0.2,
            'validation_size': 0.2,
            'cross_validation_folds': 5,
            'early_stopping': True,
            'model_save_path': 'models/',
            'hyperparameter_tuning': {
                'enabled': True,
                'cv_folds': 3,
                'scoring': 'f1'
            },
            'model_comparison': {
                'enabled': True,
                'metrics': ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
            }
        }

    def train_single_model(self, 
                          model, 
                          X: np.ndarray, 
                          y: np.ndarray = None,
                          model_name: str = "model") -> Dict[str, Any]:
        """
        Train a single model with validation.
        
        Args:
            model: The model to train
            X: Feature matrix
            y: Target labels (optional for unsupervised learning)
            model_name: Name identifier for the model
            
        Returns:
            Dictionary containing training results and metrics
        """
        try:
            logger.info(f"Training model: {model_name}")
            
            # Split data if labels are provided
            if y is not None:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=self.config['test_size'], 
                    random_state=42, stratify=y
                )
            else:
                # For unsupervised learning, split without labels
                X_train, X_test = train_test_split(
                    X, test_size=self.config['test_size'], random_state=42
                )
                y_train, y_test = None, None
            
            # Train the model
            start_time = datetime.now()
            
            if y is not None:
                # Supervised learning
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                metrics = self._calculate_metrics(y_test, y_pred, model, X_test)
            else:
                # Unsupervised learning
                model.fit(X_train)
                if hasattr(model, 'predict'):
                    y_pred = model.predict(X_test)
                    metrics = {'status': 'unsupervised'}
                else:
                    y_pred = None
                    metrics = {'status': 'fitted'}
            
            training_time = (datetime.now() - start_time).total_seconds()
            
            # Store training results
            result = {
                'model_name': model_name,
                'status': 'trained',
                'training_time_seconds': training_time,
                'train_size': len(X_train),
                'test_size': len(X_test),
                'metrics': metrics,
                'model_info': self._get_model_info(model)
            }
            
            # Perform cross-validation if labels are available
            if y is not None and self.config.get('cross_validation_folds', 0) > 0:
                cv_scores = cross_val_score(
                    model, X, y, 
                    cv=self.config['cross_validation_folds'],
                    scoring='f1'
                )
                result['cross_validation'] = {
                    'scores': cv_scores.tolist(),
                    'mean_score': float(np.mean(cv_scores)),
                    'std_score': float(np.std(cv_scores))
                }
            
            self.training_history[model_name] = result
            logger.info(f"Model {model_name} trained successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Error training model {model_name}: {str(e)}")
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e)
            }

    def hyperparameter_tuning(self, 
                             model_class, 
                             param_grid: Dict[str, List],
                             X: np.ndarray, 
                             y: np.ndarray,
                             model_name: str = "tuned_model") -> Dict[str, Any]:
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            model_class: Model class to instantiate
            param_grid: Parameter grid for tuning
            X: Feature matrix
            y: Target labels
            model_name: Name identifier for the tuned model
            
        Returns:
            Dictionary containing tuning results and best parameters
        """
        try:
            if not self.config['hyperparameter_tuning']['enabled']:
                logger.info("Hyperparameter tuning disabled, skipping...")
                return {'status': 'disabled'}
            
            logger.info(f"Starting hyperparameter tuning for {model_name}")
            
            # Create base model
            base_model = model_class()
            
            # Setup GridSearchCV
            cv_folds = self.config['hyperparameter_tuning']['cv_folds']
            scoring = self.config['hyperparameter_tuning']['scoring']
            
            grid_search = GridSearchCV(
                estimator=base_model,
                param_grid=param_grid,
                cv=cv_folds,
                scoring=scoring,
                n_jobs=-1,
                verbose=1
            )
            
            # Fit grid search
            start_time = datetime.now()
            grid_search.fit(X, y)
            tuning_time = (datetime.now() - start_time).total_seconds()
            
            # Get best model and parameters
            best_model = grid_search.best_estimator_
            best_params = grid_search.best_params_
            best_score = grid_search.best_score_
            
            # Train the best model on full dataset
            best_model.fit(X, y)
            
            # Calculate final metrics
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.config['test_size'], 
                random_state=42, stratify=y
            )
            y_pred = best_model.predict(X_test)
            metrics = self._calculate_metrics(y_test, y_pred, best_model, X_test)
            
            result = {
                'model_name': model_name,
                'status': 'tuned',
                'tuning_time_seconds': tuning_time,
                'best_parameters': best_params,
                'best_cv_score': float(best_score),
                'final_metrics': metrics,
                'model_info': self._get_model_info(best_model),
                'grid_results': {
                    'best_index': int(grid_search.best_index_),
                    'best_score': float(grid_search.best_score_),
                    'scorer': grid_search.scorer_
                }
            }
            
            self.training_history[f"{model_name}_tuned"] = result
            logger.info(f"Hyperparameter tuning completed for {model_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in hyperparameter tuning for {model_name}: {str(e)}")
            return {
                'model_name': model_name,
                'status': 'failed',
                'error': str(e)
            }

    def compare_models(self, 
                      models: Dict[str, Any], 
                      X: np.ndarray, 
                      y: np.ndarray = None) -> Dict[str, Any]:
        """
        Compare multiple models and select the best one.
        
        Args:
            models: Dictionary of model_name -> model_instance
            X: Feature matrix
            y: Target labels (optional)
            
        Returns:
            Dictionary containing model comparison results
        """
        try:
            if not self.config['model_comparison']['enabled']:
                logger.info("Model comparison disabled, skipping...")
                return {'status': 'disabled'}
            
            logger.info("Starting model comparison...")
            
            comparison_results = {}
            for name, model in models.items():
                logger.info(f"Evaluating model: {name}")
                result = self.train_single_model(model, X, y, name)
                comparison_results[name] = result
            
            # Determine best model based on metrics
            best_model_name = self._select_best_model(comparison_results)
            
            # Compile comparison results
            comparison = {
                'status': 'completed',
                'models_evaluated': len(models),
                'best_model': best_model_name,
                'comparison_results': comparison_results,
                'evaluation_timestamp': datetime.now().isoformat()
            }
            
            # Add detailed comparison if labels are available
            if y is not None:
                comparison['detailed_metrics'] = self._create_detailed_comparison(comparison_results)
            
            self.model_comparisons[f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = comparison
            logger.info(f"Model comparison completed. Best model: {best_model_name}")
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error in model comparison: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray, model: Any, X_test: np.ndarray) -> Dict[str, float]:
        """Calculate comprehensive evaluation metrics."""
        try:
            metrics = {
                'accuracy': float(accuracy_score(y_true, y_pred)),
                'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
                'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
            }
            
            # Add ROC AUC if probability predictions are available
            if hasattr(model, 'predict_proba'):
                try:
                    y_proba = model.predict_proba(X_test)[:, 1]
                    metrics['roc_auc'] = float(roc_auc_score(y_true, y_proba))
                except:
                    pass  # ROC AUC calculation failed
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {'error': str(e)}

    def _get_model_info(self, model: Any) -> Dict[str, Any]:
        """Get comprehensive model information."""
        try:
            info = {
                'model_type': type(model).__name__,
                'parameters': {}
            }
            
            # Get model parameters
            if hasattr(model, 'get_params'):
                info['parameters'] = model.get_params()
            
            # Get model-specific information
            if hasattr(model, 'n_estimators'):
                info['n_estimators'] = model.n_estimators
            elif hasattr(model, 'n_clusters'):
                info['n_clusters'] = model.n_clusters
            elif hasattr(model, 'encoding_dim'):
                info['encoding_dim'] = model.encoding_dim
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting model info: {str(e)}")
            return {'error': str(e)}

    def _select_best_model(self, results: Dict[str, Dict]) -> str:
        """Select the best model based on F1 score."""
        best_score = -1
        best_model = None
        
        for name, result in results.items():
            if result.get('status') == 'trained' and 'metrics' in result:
                f1_score = result['metrics'].get('f1_score', 0)
                if f1_score > best_score:
                    best_score = f1_score
                    best_model = name
        
        return best_model or "no_suitable_model"

    def _create_detailed_comparison(self, results: Dict[str, Dict]) -> Dict[str, Any]:
        """Create detailed comparison of model performance."""
        detailed = {
            'models': {},
            'summary': {}
        }
        
        # Compile metrics for each model
        for name, result in results.items():
            if result.get('status') == 'trained' and 'metrics' in result:
                detailed['models'][name] = result['metrics']
        
        # Calculate summary statistics
        if detailed['models']:
            metric_names = ['accuracy', 'precision', 'recall', 'f1_score']
            for metric in metric_names:
                values = [model_metrics.get(metric, 0) 
                         for model_metrics in detailed['models'].values()]
                detailed['summary'][metric] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values))
                }
        
        return detailed

    def save_training_results(self, filepath: str):
        """Save training results to file."""
        try:
            results = {
                'training_history': self.training_history,
                'model_comparisons': self.model_comparisons,
                'config': self.config,
                'timestamp': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Training results saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving training results: {str(e)}")

    def load_training_results(self, filepath: str):
        """Load training results from file."""
        try:
            with open(filepath, 'r') as f:
                results = json.load(f)
            
            self.training_history = results.get('training_history', {})
            self.model_comparisons = results.get('model_comparisons', {})
            
            logger.info(f"Training results loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading training results: {str(e)}")

    def get_training_summary(self) -> Dict[str, Any]:
        """Get a summary of all training activities."""
        summary = {
            'total_models_trained': len(self.training_history),
            'total_comparisons': len(self.model_comparisons),
            'training_history': self.training_history,
            'recent_comparisons': list(self.model_comparisons.keys())[-5:]  # Last 5 comparisons
        }
        
        return summary