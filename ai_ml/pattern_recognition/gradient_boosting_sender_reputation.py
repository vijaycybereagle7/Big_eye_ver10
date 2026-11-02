"""
Gradient Boosting Classifier for Sender Reputation Prediction

This module implements a Gradient Boosting model to predict sender reputation
based on email sender characteristics and metadata analysis.

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import joblib
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, PolynomialFeatures
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, mean_squared_error
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from .feature_extraction import extract_all_features, create_feature_matrix


class SenderReputationPredictor:
    """Gradient Boosting Classifier for sender reputation prediction."""
    
    def __init__(self, model_type: str = 'classification', n_estimators: int = 100, 
                 max_depth: int = 5, learning_rate: float = 0.1, random_state: int = 42):
        """
        Initialize the Sender Reputation Predictor.
        
        Args:
            model_type: 'classification' for categorical reputation or 'regression' for score prediction
            n_estimators: Number of boosting stages
            max_depth: Maximum depth of trees
            learning_rate: Learning rate for boosting
            random_state: Random state for reproducibility
        """
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.is_trained = False
        
        # Initialize model based on type
        if model_type == 'classification':
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=random_state,
                subsample=0.8,
                min_samples_split=20,
                min_samples_leaf=10
            )
            self.reputation_categories = ['Spammer', 'Suspicious', 'Legitimate', 'Trusted']
            self.label_encoder = LabelEncoder()
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=random_state,
                subsample=0.8,
                min_samples_split=20,
                min_samples_leaf=10
            )
        
        self.scaler = StandardScaler()
        self.polynomial_features = None
        self.feature_selector = None
        self.feature_names = []
        self.feature_importance = {}
        
    def prepare_training_data(self, sender_data: List[Union[str, Dict[str, str]]], 
                            reputation_scores: List[Union[int, float]], 
                            reputation_categories: Optional[List[str]] = None,
                            use_polynomial_features: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data with feature extraction and preprocessing.
        
        Args:
            sender_data: List of email addresses or sender metadata dictionaries
            reputation_scores: List of reputation scores (0-100 for regression, 0-3 for classification)
            reputation_categories: List of reputation category names (for classification)
            use_polynomial_features: Whether to create polynomial features
            
        Returns:
            Tuple of (X, y) feature matrix and labels
        """
        all_features = []
        all_feature_names = set()
        
        # Process each sender data point
        for data in sender_data:
            if isinstance(data, str):
                # Email address
                features = extract_all_features(data, 'email')
            elif isinstance(data, dict):
                # Metadata dictionary
                features = extract_all_features(data, 'metadata')
            else:
                raise ValueError("sender_data must contain strings (emails) or dictionaries (metadata)")
            
            all_features.append(features)
            all_feature_names.update(features.keys())
        
        # Convert to feature matrix
        feature_names = sorted(list(all_feature_names))
        X = np.array([[features.get(name, 0) for name in feature_names] for features in all_features])
        
        self.feature_names = feature_names
        
        # Prepare labels
        if self.model_type == 'classification':
            if reputation_categories is not None:
                # Use categorical labels
                y = self.label_encoder.fit_transform(reputation_categories)
            else:
                # Convert numeric scores to categories
                y = self._convert_scores_to_categories(reputation_scores)
        else:
            # Use regression scores directly
            y = np.array(reputation_scores)
        
        # Create polynomial features if requested
        if use_polynomial_features and X.shape[1] > 1:
            self.polynomial_features = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
            X = self.polynomial_features.fit_transform(X)
            
            # Generate polynomial feature names
            poly_feature_names = self.polynomial_features.get_feature_names_out(self.feature_names)
            self.feature_names = list(poly_feature_names)
        
        # Remove features with zero variance
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        
        if self.polynomial_features is None:
            self.feature_names = [name for i, name in enumerate(self.feature_names) if valid_features[i]]
        else:
            # For polynomial features, just update the count
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]
        
        return X, y
    
    def _convert_scores_to_categories(self, scores: List[float]) -> np.ndarray:
        """Convert reputation scores to categories."""
        categories = []
        for score in scores:
            if score <= 20:
                categories.append(0)  # Spammer
            elif score <= 50:
                categories.append(1)  # Suspicious
            elif score <= 80:
                categories.append(2)  # Legitimate
            else:
                categories.append(3)  # Trusted
        return np.array(categories)
    
    def train(self, sender_data: List[Union[str, Dict[str, str]]], 
              reputation_scores: List[Union[int, float]], 
              reputation_categories: Optional[List[str]] = None,
              validation_split: float = 0.2, feature_selection: bool = True,
              polynomial_features: bool = False) -> Dict[str, float]:
        """
        Train the Gradient Boosting model.
        
        Args:
            sender_data: List of email addresses or sender metadata dictionaries
            reputation_scores: List of reputation scores or categories
            reputation_categories: List of reputation category names (optional)
            validation_split: Fraction of data to use for validation
            feature_selection: Whether to perform feature selection
            polynomial_features: Whether to create polynomial features
            
        Returns:
            Dictionary of training metrics
        """
        # Prepare data
        X, y = self.prepare_training_data(sender_data, reputation_scores, reputation_categories, 
                                        use_polynomial_features=polynomial_features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=validation_split, random_state=self.random_state,
            stratify=y if self.model_type == 'classification' else None
        )
        
        # Feature scaling
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Feature selection
        if feature_selection and len(self.feature_names) > 20:
            if self.model_type == 'classification':
                selector = SelectKBest(f_classif, k=min(30, len(self.feature_names)))
            else:
                from sklearn.feature_selection import SelectKBest, f_regression
                selector = SelectKBest(f_regression, k=min(30, len(self.feature_names)))
            
            self.feature_selector = selector
            X_train_scaled = selector.fit_transform(X_train_scaled, y_train)
            X_test_scaled = selector.transform(X_test_scaled)
        
        # Train model with early stopping
        self.model.fit(
            X_train_scaled, y_train,
            monitor=self._early_stopping_monitor if hasattr(self, '_early_stopping_monitor') else None
        )
        
        # Calculate training metrics
        train_score = self.model.score(X_train_scaled, y_train)
        
        # Predictions and metrics
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'train_accuracy': train_score,
            'test_accuracy': self.model.score(X_test_scaled, y_test)
        }
        
        if self.model_type == 'classification':
            metrics['test_precision'] = np.mean(y_pred == y_test)
            
            if len(np.unique(y_test)) > 1:  # Avoid issues with single class
                if hasattr(self.model, 'predict_proba'):
                    metrics['test_auc'] = roc_auc_score(y_test, self.model.predict_proba(X_test_scaled), multi_class='ovr')
                else:
                    metrics['test_auc'] = 0.0
        else:
            metrics['test_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
            metrics['test_mae'] = np.mean(np.abs(y_test - y_pred))
        
        # Cross-validation
        if self.model_type == 'classification':
            cv_scorer = 'accuracy'
        else:
            cv_scorer = 'neg_mean_squared_error'
        
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring=cv_scorer)
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        # Store feature importance
        if hasattr(self.model, 'feature_importances_'):
            self.feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        
        self.is_trained = True
        self.X_test = X_test_scaled
        self.y_test = y_test
        self.y_pred = y_pred
        
        return metrics
    
    def _early_stopping_monitor(self, i, self_model, train_score, test_score):
        """Monitor for early stopping (placeholder for custom implementation)."""
        return False
    
    def hyperparameter_tuning(self, sender_data: List[Union[str, Dict[str, str]]], 
                            reputation_scores: List[Union[int, float]], 
                            reputation_categories: Optional[List[str]] = None) -> Dict:
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            sender_data: List of email addresses or sender metadata dictionaries
            reputation_scores: List of reputation scores or categories
            reputation_categories: List of reputation category names (optional)
            
        Returns:
            Best parameters and score
        """
        # Prepare data
        X, y = self.prepare_training_data(sender_data, reputation_scores, reputation_categories)
        X_scaled = self.scaler.fit_transform(X)
        
        # Define parameter grid
        if self.model_type == 'classification':
            param_grid = {
                'n_estimators': [50, 100, 150],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.05, 0.1, 0.15],
                'subsample': [0.8, 0.9, 1.0]
            }
            scoring = 'accuracy'
        else:
            param_grid = {
                'n_estimators': [50, 100, 150],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.05, 0.1, 0.15],
                'subsample': [0.8, 0.9, 1.0]
            }
            scoring = 'neg_mean_squared_error'
        
        # Grid search with reduced parameter space for efficiency
        simplified_grid = {
            'n_estimators': [100, 150],
            'max_depth': [5, 7],
            'learning_rate': [0.1, 0.15]
        }
        
        grid_search = GridSearchCV(
            GradientBoostingClassifier(random_state=self.random_state) if self.model_type == 'classification'
            else GradientBoostingRegressor(random_state=self.random_state),
            simplified_grid,
            cv=3,  # Reduced CV for efficiency
            scoring=scoring,
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X_scaled, y)
        
        # Update model with best parameters
        self.model = grid_search.best_estimator_
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_
        }
    
    def predict_reputation(self, sender_data: List[Union[str, Dict[str, str]]]) -> Union[List[int], List[float]]:
        """
        Predict reputation for new senders.
        
        Args:
            sender_data: List of email addresses or sender metadata dictionaries
            
        Returns:
            List of reputation categories (classification) or scores (regression)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract and preprocess features
        all_features = []
        for data in sender_data:
            if isinstance(data, str):
                features = extract_all_features(data, 'email')
            elif isinstance(data, dict):
                features = extract_all_features(data, 'metadata')
            else:
                raise ValueError("sender_data must contain strings (emails) or dictionaries (metadata)")
            all_features.append(features)
        
        # Create feature matrix
        X = np.array([[features.get(name, 0) for name in self.feature_names[:len(self.scaler.mean_)]] 
                      for features in all_features])
        
        # Apply polynomial features if they were used during training
        if self.polynomial_features is not None:
            X = self.polynomial_features.transform(X)
        
        # Apply scaling
        X_scaled = self.scaler.transform(X)
        
        # Apply feature selection
        if self.feature_selector is not None:
            X_scaled = self.feature_selector.transform(X_scaled)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        
        if self.model_type == 'classification':
            # Convert back to category names
            if hasattr(self, 'label_encoder'):
                return self.label_encoder.inverse_transform(predictions)
            else:
                # Convert numeric predictions to category names
                category_names = ['Spammer', 'Suspicious', 'Legitimate', 'Trusted']
                return [category_names[pred] for pred in predictions]
        else:
            return predictions
    
    def predict_reputation_probabilities(self, sender_data: List[Union[str, Dict[str, str]]]) -> np.ndarray:
        """Predict reputation probabilities for senders (classification only)."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if self.model_type != 'classification':
            raise ValueError("Probability prediction is only available for classification model")
        
        if not hasattr(self.model, 'predict_proba'):
            raise ValueError("Model does not support probability prediction")
        
        # Extract and preprocess features
        all_features = []
        for data in sender_data:
            if isinstance(data, str):
                features = extract_all_features(data, 'email')
            elif isinstance(data, dict):
                features = extract_all_features(data, 'metadata')
            else:
                raise ValueError("sender_data must contain strings (emails) or dictionaries (metadata)")
            all_features.append(features)
        
        # Create feature matrix
        X = np.array([[features.get(name, 0) for name in self.feature_names[:len(self.scaler.mean_)]] 
                      for features in all_features])
        
        # Apply polynomial features if they were used during training
        if self.polynomial_features is not None:
            X = self.polynomial_features.transform(X)
        
        # Apply scaling
        X_scaled = self.scaler.transform(X)
        
        # Apply feature selection
        if self.feature_selector is not None:
            X_scaled = self.feature_selector.transform(X_scaled)
        
        return self.model.predict_proba(X_scaled)
    
    def evaluate_model(self, test_sender_data: List[Union[str, Dict[str, str]]], 
                      test_reputation_scores: List[Union[int, float]], 
                      test_reputation_categories: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Comprehensive model evaluation on test data.
        
        Args:
            test_sender_data: List of test email addresses or sender metadata dictionaries
            test_reputation_scores: List of test reputation scores
            test_reputation_categories: List of test reputation category names (optional)
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Get predictions
        predictions = self.predict_reputation(test_sender_data)
        
        # Prepare true labels
        if self.model_type == 'classification':
            if test_reputation_categories is not None:
                y_true = self.label_encoder.transform(test_reputation_categories) if hasattr(self, 'label_encoder') else test_reputation_categories
            else:
                y_true = self._convert_scores_to_categories(test_reputation_scores)
            
            # Convert predictions to numeric for metrics
            if isinstance(predictions[0], str):
                pred_labels = self.label_encoder.transform(predictions) if hasattr(self, 'label_encoder') else predictions
            else:
                pred_labels = predictions
                
        else:
            y_true = np.array(test_reputation_scores)
            pred_labels = np.array(predictions)
        
        # Calculate metrics
        evaluation_results = {}
        
        if self.model_type == 'classification':
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            evaluation_results = {
                'accuracy': accuracy_score(y_true, pred_labels),
                'precision': precision_score(y_true, pred_labels, average='weighted'),
                'recall': recall_score(y_true, pred_labels, average='weighted'),
                'f1_score': f1_score(y_true, pred_labels, average='weighted')
            }
        else:
            from sklearn.metrics import mean_absolute_error, r2_score
            
            evaluation_results = {
                'rmse': np.sqrt(mean_squared_error(y_true, pred_labels)),
                'mae': mean_absolute_error(y_true, pred_labels),
                'r2_score': r2_score(y_true, pred_labels)
            }
        
        return evaluation_results
    
    def plot_feature_importance(self, top_n: int = 20, save_path: Optional[str] = None):
        """Plot feature importance."""
        if not self.feature_importance:
            raise ValueError("No feature importance available. Train the model first.")
        
        # Sort features by importance
        sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:top_n]
        features, importances = zip(*sorted_features)
        
        # Create plot
        plt.figure(figsize=(12, 8))
        y_pos = np.arange(len(features))
        
        colors = ['darkgreen' if imp > 0.15 else 'green' if imp > 0.1 else 'orange' if imp > 0.05 else 'red' for imp in importances]
        plt.barh(y_pos, importances, color=colors)
        plt.yticks(y_pos, features)
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Most Important Features for Sender Reputation')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_model(self, filepath: str):
        """Save trained model to file."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'polynomial_features': self.polynomial_features,
            'feature_selector': self.feature_selector,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'model_type': self.model_type,
            'label_encoder': getattr(self, 'label_encoder', None),
            'reputation_categories': getattr(self, 'reputation_categories', None),
            'random_state': self.random_state
        }
        
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model from file."""
        model_data = joblib.load(filepath)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.polynomial_features = model_data['polynomial_features']
        self.feature_selector = model_data['feature_selector']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.model_type = model_data['model_type']
        self.label_encoder = model_data['label_encoder']
        self.reputation_categories = model_data['reputation_categories']
        self.random_state = model_data['random_state']
        self.is_trained = True


def create_sample_sender_data(n_samples: int = 1500) -> Tuple[List[str], List[float], List[str]]:
    """Create sample sender reputation data for testing."""
    import random
    
    sender_emails = []
    reputation_scores = []
    reputation_categories = []
    
    # Trusted sender patterns
    trusted_emails = [
        'ceo@company.com', 'admin@organization.org', 'support@enterprise.net',
        'billing@corporation.com', 'hr@business.com', 'sales@enterprise.net'
    ]
    
    # Legitimate sender patterns
    legitimate_emails = [
        'john.doe@gmail.com', 'jane.smith@yahoo.com', 'mike.wilson@hotmail.com',
        'sarah.jones@outlook.com', 'david.brown@icloud.com', 'lisa.white@aol.com'
    ]
    
    # Suspicious sender patterns
    suspicious_emails = [
        'noreply@domain.tk', 'no-reply@suspicious.ml', 'admin@random-server.biz',
        'support@unknown-domain.info', 'system@temp-mail.ga', 'bot@fake-company.cf'
    ]
    
    # Spammer patterns
    spammer_emails = [
        'viagra@spammer.ru', 'lottery@scam.ml', 'urgent@phishing.tk',
        'winner@lottery-scam.ga', 'credit@bad-credit.cf', 'loan@payday-today.biz'
    ]
    
    # Generate sample data
    for i in range(n_samples):
        sender_type = random.choices(
            ['trusted', 'legitimate', 'suspicious', 'spammer'],
            weights=[0.1, 0.6, 0.25, 0.05]  # Skewed distribution
        )[0]
        
        if sender_type == 'trusted':
            email = random.choice(trusted_emails)
            score = random.uniform(85, 100)
            category = 'Trusted'
        elif sender_type == 'legitimate':
            email = random.choice(legitimate_emails)
            score = random.uniform(50, 85)
            category = 'Legitimate'
        elif sender_type == 'suspicious':
            email = random.choice(suspicious_emails)
            score = random.uniform(20, 55)
            category = 'Suspicious'
        else:  # spammer
            email = random.choice(spammer_emails)
            score = random.uniform(0, 25)
            category = 'Spammer'
        
        sender_emails.append(email)
        reputation_scores.append(score)
        reputation_categories.append(category)
    
    return sender_emails, reputation_scores, reputation_categories


if __name__ == "__main__":
    # Example usage
    print("Sender Reputation Predictor - Example Usage")
    
    # Create sample data
    sender_emails, scores, categories = create_sample_sender_data(1500)
    
    # Initialize predictor (classification mode)
    predictor = SenderReputationPredictor(model_type='classification')
    
    # Train model
    metrics = predictor.train(sender_emails, scores, categories)
    print("Training Metrics:", metrics)
    
    # Hyperparameter tuning
    print("\nPerforming hyperparameter tuning...")
    tuning_results = predictor.hyperparameter_tuning(sender_emails, scores, categories)
    print("Best parameters:", tuning_results['best_params'])
    print("Best CV score:", tuning_results['best_score'])
    
    # Make predictions
    test_senders = [
        'ceo@company.com',
        'viagra@spammer.ru',
        'john.doe@gmail.com',
        'noreply@suspicious.tk'
    ]
    
    predictions = predictor.predict_reputation(test_senders)
    probabilities = predictor.predict_reputation_probabilities(test_senders)
    
    print(f"\nPredictions for test senders:")
    for sender, pred, probs in zip(test_senders, predictions, probabilities):
        print(f"{sender}: {pred} (probabilities: {dict(zip(predictor.reputation_categories, probs))})")
    
    # Plot feature importance
    print("\nPlotting feature importance...")
    predictor.plot_feature_importance(top_n=15)
    
    # Test with metadata instead of emails
    print("\nTesting with metadata...")
    metadata_senders = [
        {'name': 'John Doe', 'email': 'john@company.com', 'domain': 'company.com', 'ip': '192.168.1.1'},
        {'name': 'System Admin', 'email': 'admin@unknown.net', 'domain': 'unknown.net', 'ip': '10.0.0.1'}
    ]
    
    metadata_predictions = predictor.predict_reputation(metadata_senders)
    print("Metadata predictions:", metadata_predictions)