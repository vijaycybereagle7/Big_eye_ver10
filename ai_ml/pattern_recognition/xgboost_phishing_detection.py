"""
XGBoost Classifier for Phishing URL Detection

This module implements an XGBoost model to detect phishing URLs
based on URL characteristics and content analysis.

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import joblib
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from .feature_extraction import extract_all_features, create_feature_matrix


class PhishingURLDetector:
    """XGBoost Classifier for detecting phishing URLs."""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.1, 
                 random_state: int = 42):
        """
        Initialize the Phishing URL Detector.
        
        Args:
            n_estimators: Number of boosting rounds
            max_depth: Maximum depth of trees
            learning_rate: Learning rate for boosting
            random_state: Random state for reproducibility
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state
        self.is_trained = False
        
        # Initialize XGBoost classifier
        self.model = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            random_state=random_state,
            eval_metric='logloss',
            use_label_encoder=False,
            n_jobs=-1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1
        )
        
        self.scaler = StandardScaler()
        self.feature_selector = None
        self.feature_names = []
        self.feature_importance = {}
        
    def prepare_training_data(self, urls: List[str], labels: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data with feature extraction and preprocessing.
        
        Args:
            urls: List of URL strings
            labels: List of labels (0=legitimate, 1=phishing)
            
        Returns:
            Tuple of (X, y) feature matrix and labels
        """
        # Extract features
        X, feature_names = create_feature_matrix(urls, 'url')
        self.feature_names = feature_names
        
        # Convert labels to numpy array
        y = np.array(labels)
        
        # Remove features with zero variance
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        self.feature_names = [name for i, name in enumerate(self.feature_names) if valid_features[i]]
        
        return X, y
    
    def train(self, urls: List[str], labels: List[int], validation_split: float = 0.2, 
              feature_selection: bool = True, early_stopping: bool = True) -> Dict[str, float]:
        """
        Train the XGBoost model.
        
        Args:
            urls: List of URL strings
            labels: List of labels (0=legitimate, 1=phishing)
            validation_split: Fraction of data to use for validation
            feature_selection: Whether to perform feature selection
            early_stopping: Whether to use early stopping
            
        Returns:
            Dictionary of training metrics
        """
        # Prepare data
        X, y = self.prepare_training_data(urls, labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=validation_split, random_state=self.random_state, stratify=y
        )
        
        # Feature scaling
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Feature selection
        if feature_selection and len(self.feature_names) > 30:
            k_best = min(50, len(self.feature_names))
            self.feature_selector = SelectKBest(mutual_info_classif, k=k_best)
            X_train_scaled = self.feature_selector.fit_transform(X_train_scaled, y_train)
            X_test_scaled = self.feature_selector.transform(X_test_scaled)
            
            # Update feature names
            selected_indices = self.feature_selector.get_support(indices=True)
            self.feature_names = [self.feature_names[i] for i in selected_indices]
        
        # Prepare eval_set for early stopping
        eval_set = [(X_test_scaled, y_test)] if early_stopping else None
        
        # Train model
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=eval_set,
            early_stopping_rounds=20 if early_stopping else None,
            verbose=False
        )
        
        # Calculate training metrics
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        # Predictions and probabilities
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        metrics = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'test_auc': roc_auc_score(y_test, y_pred_proba)
        }
        
        # Calculate precision, recall, f1
        from sklearn.metrics import precision_score, recall_score, f1_score
        metrics.update({
            'test_precision': precision_score(y_test, y_pred),
            'test_recall': recall_score(y_test, y_pred),
            'test_f1': f1_score(y_test, y_pred)
        })
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5, scoring='roc_auc')
        metrics['cv_auc_mean'] = cv_scores.mean()
        metrics['cv_auc_std'] = cv_scores.std()
        
        # Store feature importance
        self.feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
        
        self.is_trained = True
        self.X_test = X_test_scaled
        self.y_test = y_test
        self.y_pred = y_pred
        self.y_pred_proba = y_pred_proba
        
        return metrics
    
    def hyperparameter_tuning(self, urls: List[str], labels: List[int], 
                            param_grid: Optional[Dict] = None) -> Dict:
        """
        Perform hyperparameter tuning using GridSearchCV.
        
        Args:
            urls: List of URL strings
            labels: List of labels
            param_grid: Custom parameter grid (optional)
            
        Returns:
            Best parameters and score
        """
        # Prepare data
        X, y = self.prepare_training_data(urls, labels)
        X_scaled = self.scaler.fit_transform(X)
        
        # Default parameter grid
        if param_grid is None:
            param_grid = {
                'n_estimators': [50, 100, 200],
                'max_depth': [4, 6, 8, 10],
                'learning_rate': [0.05, 0.1, 0.15],
                'subsample': [0.7, 0.8, 0.9],
                'colsample_bytree': [0.7, 0.8, 0.9],
                'reg_alpha': [0, 0.1, 0.5],
                'reg_lambda': [0, 0.1, 0.5]
            }
        
        # Grid search with smaller parameter set for efficiency
        simplified_grid = {
            'n_estimators': [100, 200],
            'max_depth': [6, 8],
            'learning_rate': [0.1, 0.15],
            'subsample': [0.8, 0.9],
            'colsample_bytree': [0.8, 0.9]
        }
        
        grid_search = GridSearchCV(
            xgb.XGBClassifier(random_state=self.random_state, eval_metric='logloss', use_label_encoder=False),
            simplified_grid,
            cv=3,  # Reduced CV for efficiency
            scoring='roc_auc',
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
    
    def detect_phishing(self, urls: List[str]) -> Tuple[List[int], List[float]]:
        """
        Detect phishing URLs.
        
        Args:
            urls: List of URLs to classify
            
        Returns:
            Tuple of (predictions, probabilities)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract and preprocess features
        X, _ = create_feature_matrix(urls, 'url')
        feature_variances = np.var(X, axis=0)
        valid_features = feature_variances > 1e-6
        X = X[:, valid_features]
        
        X_scaled = self.scaler.transform(X)
        
        if self.feature_selector is not None:
            X_scaled = self.feature_selector.transform(X_scaled)
        
        # Make predictions
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        return predictions.tolist(), probabilities.tolist()
    
    def get_risk_score(self, urls: List[str]) -> List[float]:
        """
        Get phishing risk scores for URLs.
        
        Args:
            urls: List of URLs to analyze
            
        Returns:
            List of risk scores (0-1, higher = more likely to be phishing)
        """
        _, probabilities = self.detect_phishing(urls)
        return probabilities
    
    def evaluate_model(self, test_urls: List[str], test_labels: List[int]) -> Dict[str, float]:
        """
        Comprehensive model evaluation on test data.
        
        Args:
            test_urls: List of test URL strings
            test_labels: List of test labels
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Get predictions
        predictions, probabilities = self.detect_phishing(test_urls)
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
        
        y_true = np.array(test_labels)
        y_pred = np.array(predictions)
        
        evaluation_results = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred),
            'recall': recall_score(y_true, y_pred),
            'f1_score': f1_score(y_true, y_pred),
            'auc': roc_auc_score(y_true, probabilities)
        }
        
        # Confusion matrix analysis
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        evaluation_results.update({
            'true_negatives': tn,
            'false_positives': fp,
            'false_negatives': fn,
            'true_positives': tp,
            'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0,
            'false_positive_rate': fp / (fp + tn) if (fp + tn) > 0 else 0,
            'false_negative_rate': fn / (fn + tp) if (fn + tp) > 0 else 0
        })
        
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
        
        colors = ['green' if imp > 0.1 else 'orange' if imp > 0.05 else 'red' for imp in importances]
        plt.barh(y_pos, importances, color=colors)
        plt.yticks(y_pos, features)
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Most Important Features for Phishing Detection')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_precision_recall_curve(self, save_path: Optional[str] = None):
        """Plot Precision-Recall curve."""
        if not self.is_trained:
            raise ValueError("Model must be trained first.")
        
        from sklearn.metrics import precision_recall_curve
        
        precision, recall, thresholds = precision_recall_curve(self.y_test, self.y_pred_proba)
        
        plt.figure(figsize=(10, 8))
        plt.plot(recall, precision, linewidth=2, label='XGBoost Model')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve for Phishing Detection')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
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
            'feature_selector': self.feature_selector,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
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
        self.random_state = model_data['random_state']
        self.is_trained = True


def create_sample_phishing_data(n_samples: int = 2000) -> Tuple[List[str], List[int]]:
    """Create sample phishing URL data for testing."""
    import random
    
    urls = []
    labels = []
    
    # Legitimate URLs
    legitimate_urls = [
        'https://www.google.com/search?q=machine+learning',
        'https://github.com/microsoft/vscode',
        'https://stackoverflow.com/questions/123456',
        'https://www.amazon.com/product/abc123',
        'https://www.wikipedia.org/wiki/Artificial_Intelligence',
        'https://www.youtube.com/watch?v=abc123',
        'https://www.linkedin.com/in/john-doe',
        'https://www.reddit.com/r/programming/',
        'https://news.ycombinator.com/item?id=123',
        'https://www.imdb.com/title/tt1234567/'
    ]
    
    # Phishing URLs with various patterns
    phishing_patterns = [
        'http://login-secure-update.com/account/verify',
        'https://banking-secure-login.net/confirm-identity',
        'http://account-verify.info/paypal-security',
        'https://secure-update-portal.org/urgent-verification',
        'http://support-helpdesk.net/password-reset',
        'https://login-authentication.com/verify-account',
        'http://bank-security.org/confirm-details',
        'https://account-security.net/validate-login',
        'http://www.paypal-secure-update.tk/verify',
        'https://www.google-login-security.ml/account'
    ]
    
    # Generate samples
    for i in range(n_samples):
        if random.random() < 0.6:  # 60% legitimate
            url = random.choice(legitimate_urls)
            # Add some variations to legitimate URLs
            if random.random() < 0.3:
                url += f"?ref={random.randint(1000, 9999)}"
            labels.append(0)
        else:  # 40% phishing
            url = random.choice(phishing_patterns)
            # Add some variations to phishing URLs
            if random.random() < 0.5:
                url += f"?session={random.randint(1000, 9999)}"
            labels.append(1)
        
        urls.append(url)
    
    return urls, labels


if __name__ == "__main__":
    # Example usage
    print("Phishing URL Detector - Example Usage")
    
    # Create sample data
    urls, labels = create_sample_phishing_data(2000)
    
    # Initialize detector
    detector = PhishingURLDetector(n_estimators=100)
    
    # Train model
    metrics = detector.train(urls, labels)
    print("Training Metrics:", metrics)
    
    # Hyperparameter tuning
    print("\nPerforming hyperparameter tuning...")
    tuning_results = detector.hyperparameter_tuning(urls, labels)
    print("Best parameters:", tuning_results['best_params'])
    print("Best CV score:", tuning_results['best_score'])
    
    # Make predictions
    test_urls = [
        'https://www.google.com/search?q=test',
        'http://login-secure-update.com/phishing',
        'https://www.amazon.com/product/123'
    ]
    
    predictions, probabilities = detector.detect_phishing(test_urls)
    
    print(f"\nPredictions for test URLs:")
    for url, pred, prob in zip(test_urls, predictions, probabilities):
        status = "Phishing" if pred == 1 else "Legitimate"
        print(f"{url}: {status} (confidence: {prob:.3f})")
    
    # Plot feature importance
    print("\nPlotting feature importance...")
    detector.plot_feature_importance(top_n=15)
    
    # Plot precision-recall curve
    print("\nPlotting precision-recall curve...")
    detector.plot_precision_recall_curve()