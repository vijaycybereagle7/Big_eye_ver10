"""
Random Forest Classifier for Domain Reputation Scoring

This module implements a Random Forest model to score domain reputation
based on various domain characteristics and metadata.

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import joblib
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, mean_squared_error
from sklearn.feature_selection import SelectKBest, f_classif
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from .feature_extraction import extract_all_features, create_feature_matrix


class DomainReputationClassifier:
    """Random Forest Classifier for domain reputation scoring."""
    
    def __init__(self, model_type: str = 'classification', n_estimators: int = 100, random_state: int = 42):
        """
        Initialize the Domain Reputation Classifier.
        
        Args:
            model_type: 'classification' for categorical reputation or 'regression' for score prediction
            n_estimators: Number of trees in the forest
            random_state: Random state for reproducibility
        """
        self.model_type = model_type
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.is_trained = False
        
        # Initialize model based on type
        if model_type == 'classification':
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                random_state=random_state,
                class_weight='balanced',
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1
            )
            self.reputation_categories = ['Malicious', 'Suspicious', 'Legitimate', 'Trusted']
            self.label_encoder = LabelEncoder()
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                random_state=random_state,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                n_jobs=-1
            )
        
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.feature_names = []
        self.feature_importance = {}
        
    def prepare_training_data(self, domains: List[str], reputation_scores: List[Union[int, float]], 
                            reputation_categories: Optional[List[str]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data with feature extraction and preprocessing.
        
        Args:
            domains: List of domain strings
            reputation_scores: List of reputation scores (0-100 for regression, 0-3 for classification)
            reputation_categories: List of reputation category names (for classification)
            
        Returns:
            Tuple of (X, y) feature matrix and labels
        """
        # Extract features
        X, feature_names = create_feature_matrix(domains, 'domain')
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
        
        # Remove features with zero variance
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        self.feature_names = [name for i, name in enumerate(self.feature_names) if valid_features[i]]
        
        return X, y
    
    def _convert_scores_to_categories(self, scores: List[float]) -> np.ndarray:
        """Convert reputation scores to categories."""
        categories = []
        for score in scores:
            if score <= 25:
                categories.append(0)  # Malicious
            elif score <= 50:
                categories.append(1)  # Suspicious
            elif score <= 75:
                categories.append(2)  # Legitimate
            else:
                categories.append(3)  # Trusted
        return np.array(categories)
    
    def train(self, domains: List[str], reputation_scores: List[Union[int, float]], 
              reputation_categories: Optional[List[str]] = None,
              validation_split: float = 0.2, feature_selection: bool = True) -> Dict[str, float]:
        """
        Train the Random Forest model.
        
        Args:
            domains: List of domain strings
            reputation_scores: List of reputation scores or categories
            reputation_categories: List of reputation category names (optional)
            validation_split: Fraction of data to use for validation
            feature_selection: Whether to perform feature selection
            
        Returns:
            Dictionary of training metrics
        """
        # Prepare data
        X, y = self.prepare_training_data(domains, reputation_scores, reputation_categories)
        
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
            k_best = min(50, len(self.feature_names))
            self.feature_selector = SelectKBest(f_classif, k=k_best)
            X_train_scaled = self.feature_selector.fit_transform(X_train_scaled, y_train)
            X_test_scaled = self.feature_selector.transform(X_test_scaled)
            
            # Update feature names
            selected_indices = self.feature_selector.get_support(indices=True)
            self.feature_names = [self.feature_names[i] for i in selected_indices]
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
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
                metrics['test_auc'] = roc_auc_score(y_test, self.model.predict_proba(X_test_scaled), multi_class='ovr')
        else:
            metrics['test_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
            metrics['test_mae'] = np.mean(np.abs(y_test - y_pred))
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, 
                                   scoring='accuracy' if self.model_type == 'classification' else 'neg_mean_squared_error')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        # Store feature importance
        self.feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        
        self.is_trained = True
        self.X_test = X_test_scaled
        self.y_test = y_test
        self.y_pred = y_pred
        
        return metrics
    
    def predict_reputation(self, domains: List[str]) -> Union[List[int], List[float]]:
        """
        Predict reputation for new domains.
        
        Args:
            domains: List of domains to classify
            
        Returns:
            List of reputation categories (classification) or scores (regression)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract features
        X, _ = create_feature_matrix(domains, 'domain')
        
        # Apply preprocessing steps
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        
        X_scaled = self.scaler.transform(X)
        
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
                category_names = ['Malicious', 'Suspicious', 'Legitimate', 'Trusted']
                return [category_names[pred] for pred in predictions]
        else:
            return predictions
    
    def predict_reputation_probabilities(self, domains: List[str]) -> np.ndarray:
        """Predict reputation probabilities for domains (classification only)."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if self.model_type != 'classification':
            raise ValueError("Probability prediction is only available for classification model")
        
        # Extract and preprocess features
        X, _ = create_feature_matrix(domains, 'domain')
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        
        X_scaled = self.scaler.transform(X)
        
        if self.feature_selector is not None:
            X_scaled = self.feature_selector.transform(X_scaled)
        
        return self.model.predict_proba(X_scaled)
    
    def hyperparameter_tuning(self, domains: List[str], reputation_scores: List[Union[int, float]], 
                            reputation_categories: Optional[List[str]] = None) -> Dict:
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            domains: List of domain strings
            reputation_scores: List of reputation scores or categories
            reputation_categories: List of reputation category names (optional)
            
        Returns:
            Best parameters and score
        """
        # Prepare data
        X, y = self.prepare_training_data(domains, reputation_scores, reputation_categories)
        X_scaled = self.scaler.fit_transform(X)
        
        # Define parameter grid
        if self.model_type == 'classification':
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': ['balanced', None]
            }
            scoring = 'accuracy'
        else:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            scoring = 'neg_mean_squared_error'
        
        # Grid search
        grid_search = GridSearchCV(
            RandomForestClassifier(random_state=self.random_state) if self.model_type == 'classification' 
            else RandomForestRegressor(random_state=self.random_state),
            param_grid,
            cv=5,
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
    
    def evaluate_model(self, test_domains: List[str], test_reputation_scores: List[Union[int, float]], 
                      test_reputation_categories: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Comprehensive model evaluation on test data.
        
        Args:
            test_domains: List of test domain strings
            test_reputation_scores: List of test reputation scores
            test_reputation_categories: List of test reputation category names (optional)
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Get predictions
        predictions = self.predict_reputation(test_domains)
        
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
    
    def save_model(self, filepath: str):
        """Save trained model to file."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
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
        self.feature_selector = model_data['feature_selector']
        self.feature_names = model_data['feature_names']
        self.feature_importance = model_data['feature_importance']
        self.model_type = model_data['model_type']
        self.label_encoder = model_data['label_encoder']
        self.reputation_categories = model_data['reputation_categories']
        self.random_state = model_data['random_state']
        self.is_trained = True
    
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
        
        plt.barh(y_pos, importances)
        plt.yticks(y_pos, features)
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Most Important Features for Domain Reputation')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()


def create_sample_data(n_samples: int = 1000) -> Tuple[List[str], List[float], List[str]]:
    """Create sample domain reputation data for testing."""
    import random
    
    domains = []
    reputation_scores = []
    reputation_categories = []
    
    # Common legitimate domains
    legitimate_domains = [
        'google.com', 'microsoft.com', 'amazon.com', 'facebook.com', 'apple.com',
        'twitter.com', 'linkedin.com', 'youtube.com', 'github.com', 'stackoverflow.com'
    ]
    
    # Suspicious domain patterns
    suspicious_domains = [
        'login-secure-update.com', 'account-verify.info', 'support-portal.net',
        'secure-login-auth.com', 'banking-verify.org', 'payment-secure.biz'
    ]
    
    # Malicious domain patterns
    malicious_domains = [
        'malware-server.ru', 'phishing-site.tk', 'scam-website.ml',
        'virus-download.ga', 'fake-bank.cf', 'malicious-link.tk'
    ]
    
    # Generate sample data
    for i in range(n_samples):
        domain_type = random.choice(['legitimate', 'suspicious', 'malicious', 'trusted'])
        
        if domain_type == 'legitimate':
            domain = random.choice(legitimate_domains)
            score = random.uniform(60, 85)
            category = 'Legitimate'
        elif domain_type == 'trusted':
            domain = f"www.{random.choice(['company', 'org', 'institution'])}.com"
            score = random.uniform(85, 100)
            category = 'Trusted'
        elif domain_type == 'suspicious':
            domain = random.choice(suspicious_domains)
            score = random.uniform(25, 55)
            category = 'Suspicious'
        else:  # malicious
            domain = random.choice(malicious_domains)
            score = random.uniform(0, 30)
            category = 'Malicious'
        
        domains.append(domain)
        reputation_scores.append(score)
        reputation_categories.append(category)
    
    return domains, reputation_scores, reputation_categories


if __name__ == "__main__":
    # Example usage
    print("Domain Reputation Classifier - Example Usage")
    
    # Create sample data
    domains, scores, categories = create_sample_data(1000)
    
    # Initialize classifier (classification mode)
    classifier = DomainReputationClassifier(model_type='classification')
    
    # Train model
    metrics = classifier.train(domains, scores, categories)
    print("Training Metrics:", metrics)
    
    # Hyperparameter tuning
    print("\nPerforming hyperparameter tuning...")
    tuning_results = classifier.hyperparameter_tuning(domains, scores, categories)
    print("Best parameters:", tuning_results['best_params'])
    print("Best CV score:", tuning_results['best_score'])
    
    # Make predictions
    test_domains = ['google.com', 'malware-server.ru', 'support-portal.net']
    predictions = classifier.predict_reputation(test_domains)
    probabilities = classifier.predict_reputation_probabilities(test_domains)
    
    print(f"\nPredictions for {test_domains}:")
    for domain, pred, probs in zip(test_domains, predictions, probabilities):
        print(f"{domain}: {pred} (probabilities: {dict(zip(classifier.reputation_categories, probs))})")
    
    # Plot feature importance
    print("\nPlotting feature importance...")
    classifier.plot_feature_importance(top_n=15)