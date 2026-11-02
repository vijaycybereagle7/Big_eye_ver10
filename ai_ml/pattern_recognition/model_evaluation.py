"""
Model Evaluation Module for Pattern Recognition Models

This module provides comprehensive evaluation utilities for:
- Domain Reputation Classifier
- Phishing URL Detector  
- Sender Reputation Predictor

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score, roc_curve,
    precision_recall_curve, average_precision_score,
    mean_absolute_error, mean_squared_error, r2_score,
    cohen_kappa_score, matthews_corrcoef
)
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ModelEvaluator:
    """Comprehensive model evaluation framework."""
    
    def __init__(self, model_name: str, model_type: str):
        """
        Initialize the Model Evaluator.
        
        Args:
            model_name: Name of the model being evaluated
            model_type: Type of model ('classification' or 'regression')
        """
        self.model_name = model_name
        self.model_type = model_type
        self.evaluation_results = {}
        self.comparative_results = {}
        
    def evaluate_classification_model(self, y_true: np.ndarray, y_pred: np.ndarray, 
                                    y_pred_proba: Optional[np.ndarray] = None,
                                    class_names: Optional[List[str]] = None) -> Dict[str, float]:
        """
        Comprehensive evaluation for classification models.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_pred_proba: Predicted probabilities (optional)
            class_names: Names of classes for multi-class problems
            
        Returns:
            Dictionary of evaluation metrics
        """
        results = {}
        
        # Basic metrics
        results['accuracy'] = accuracy_score(y_true, y_pred)
        results['precision'] = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        results['recall'] = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        results['f1_score'] = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        # Advanced metrics
        results['cohen_kappa'] = cohen_kappa_score(y_true, y_pred)
        results['matthews_corr'] = matthews_corrcoef(y_true, y_pred)
        
        # AUC metrics (if probabilities available)
        if y_pred_proba is not None:
            if len(np.unique(y_true)) == 2:  # Binary classification
                results['auc_roc'] = roc_auc_score(y_true, y_pred_proba)
                results['auc_pr'] = average_precision_score(y_true, y_pred_proba)
            else:  # Multi-class
                results['auc_roc_ovr'] = roc_auc_score(y_true, y_pred_proba, multi_class='ovr')
                results['auc_roc_ovo'] = roc_auc_score(y_true, y_pred_proba, multi_class='ovo')
        
        # Per-class metrics
        if class_names:
            precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
            recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
            f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
            
            for i, class_name in enumerate(class_names):
                results[f'{class_name}_precision'] = precision_per_class[i]
                results[f'{class_name}_recall'] = recall_per_class[i]
                results[f'{class_name}_f1'] = f1_per_class[i]
        
        return results
    
    def evaluate_regression_model(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Comprehensive evaluation for regression models.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            
        Returns:
            Dictionary of evaluation metrics
        """
        results = {}
        
        # Basic regression metrics
        results['mae'] = mean_absolute_error(y_true, y_pred)
        results['mse'] = mean_squared_error(y_true, y_pred)
        results['rmse'] = np.sqrt(results['mse'])
        results['r2_score'] = r2_score(y_true, y_pred)
        
        # Additional metrics
        results['mean_error'] = np.mean(y_pred - y_true)
        results['median_error'] = np.median(y_pred - y_true)
        results['max_error'] = np.max(np.abs(y_pred - y_true))
        
        # Percentage errors
        mape = np.mean(np.abs((y_true - y_pred) / np.where(y_true != 0, y_true, 1))) * 100
        results['mape'] = mape
        
        # Explained variance
        results['explained_variance'] = 1 - (np.var(y_true - y_pred) / np.var(y_true))
        
        return results
    
    def plot_confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray, 
                            class_names: Optional[List[str]] = None,
                            save_path: Optional[str] = None, show_plot: bool = True):
        """
        Plot confusion matrix.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Names of classes
            save_path: Path to save the plot
            show_plot: Whether to display the plot
        """
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(10, 8))
        
        if class_names:
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                       xticklabels=class_names, yticklabels=class_names)
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
        else:
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.xlabel('Predicted')
            plt.ylabel('Actual')
        
        plt.title(f'Confusion Matrix - {self.model_name}')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_roc_curve(self, y_true: np.ndarray, y_pred_proba: np.ndarray,
                      save_path: Optional[str] = None, show_plot: bool = True):
        """
        Plot ROC curve for binary classification.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            save_path: Path to save the plot
            show_plot: Whether to display the plot
        """
        if len(np.unique(y_true)) != 2:
            raise ValueError("ROC curve is only for binary classification")
        
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        auc_score = roc_auc_score(y_true, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {auc_score:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {self.model_name}')
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_precision_recall_curve(self, y_true: np.ndarray, y_pred_proba: np.ndarray,
                                  save_path: Optional[str] = None, show_plot: bool = True):
        """
        Plot Precision-Recall curve.
        
        Args:
            y_true: True labels
            y_pred_proba: Predicted probabilities
            save_path: Path to save the plot
            show_plot: Whether to display the plot
        """
        if len(np.unique(y_true)) != 2:
            raise ValueError("Precision-Recall curve is only for binary classification")
        
        precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
        avg_precision = average_precision_score(y_true, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, linewidth=2, label=f'PR Curve (AP = {avg_precision:.3f})')
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title(f'Precision-Recall Curve - {self.model_name}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_prediction_distribution(self, y_true: np.ndarray, y_pred: np.ndarray,
                                   save_path: Optional[str] = None, show_plot: bool = True):
        """
        Plot distribution of predictions vs actual values.
        
        Args:
            y_true: True values
            y_pred: Predicted values
            save_path: Path to save the plot
            show_plot: Whether to display the plot
        """
        if self.model_type == 'classification':
            # For classification, plot class distribution
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            unique_true, counts_true = np.unique(y_true, return_counts=True)
            plt.bar(unique_true, counts_true, alpha=0.7, label='Actual')
            plt.xlabel('Class')
            plt.ylabel('Count')
            plt.title('Actual Class Distribution')
            plt.legend()
            
            plt.subplot(1, 2, 2)
            unique_pred, counts_pred = np.unique(y_pred, return_counts=True)
            plt.bar(unique_pred, counts_pred, alpha=0.7, label='Predicted')
            plt.xlabel('Class')
            plt.ylabel('Count')
            plt.title('Predicted Class Distribution')
            plt.legend()
            
        else:
            # For regression, plot scatter plot and residuals
            plt.figure(figsize=(15, 5))
            
            plt.subplot(1, 3, 1)
            plt.scatter(y_true, y_pred, alpha=0.6)
            plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
            plt.xlabel('Actual')
            plt.ylabel('Predicted')
            plt.title('Actual vs Predicted')
            
            plt.subplot(1, 3, 2)
            residuals = y_pred - y_true
            plt.scatter(y_pred, residuals, alpha=0.6)
            plt.axhline(y=0, color='r', linestyle='--')
            plt.xlabel('Predicted')
            plt.ylabel('Residuals')
            plt.title('Residual Plot')
            
            plt.subplot(1, 3, 3)
            plt.hist(residuals, bins=30, alpha=0.7)
            plt.xlabel('Residuals')
            plt.ylabel('Frequency')
            plt.title('Residual Distribution')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def plot_feature_importance_comparison(self, feature_importance_dict: Dict[str, float],
                                         top_n: int = 20, save_path: Optional[str] = None,
                                         show_plot: bool = True):
        """
        Plot feature importance comparison.
        
        Args:
            feature_importance_dict: Dictionary of feature importances
            top_n: Number of top features to show
            save_path: Path to save the plot
            show_plot: Whether to display the plot
        """
        if not feature_importance_dict:
            raise ValueError("No feature importance data provided")
        
        # Sort features by importance
        sorted_features = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
        features, importances = zip(*sorted_features)
        
        plt.figure(figsize=(12, 8))
        y_pos = np.arange(len(features))
        
        # Color coding based on importance levels
        colors = []
        for imp in importances:
            if imp > 0.2:
                colors.append('darkgreen')
            elif imp > 0.1:
                colors.append('green')
            elif imp > 0.05:
                colors.append('orange')
            else:
                colors.append('red')
        
        plt.barh(y_pos, importances, color=colors)
        plt.yticks(y_pos, features)
        plt.xlabel('Feature Importance')
        plt.title(f'Top {top_n} Most Important Features - {self.model_name}')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        if show_plot:
            plt.show()
        else:
            plt.close()
    
    def compare_models(self, model_results: Dict[str, Dict[str, Any]], 
                      metric_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Compare multiple models based on evaluation metrics.
        
        Args:
            model_results: Dictionary mapping model names to their evaluation results
            metric_names: List of specific metrics to compare
            
        Returns:
            DataFrame with model comparison
        """
        if not model_results:
            raise ValueError("No model results provided")
        
        # Extract common metrics
        all_metrics = set()
        for results in model_results.values():
            all_metrics.update(results.keys())
        
        # Filter metrics if specified
        if metric_names:
            all_metrics = all_metrics.intersection(set(metric_names))
        
        # Create comparison DataFrame
        comparison_data = []
        for model_name, results in model_results.items():
            row = {'Model': model_name}
            for metric in sorted(all_metrics):
                row[metric] = results.get(metric, np.nan)
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        
        # Calculate rank for each metric (higher is better for most metrics)
        for metric in all_metrics:
            if metric not in ['mae', 'mse', 'rmse', 'mean_error', 'median_error', 'max_error', 'mape']:
                comparison_df[f'{metric}_Rank'] = comparison_df[metric].rank(ascending=False)
            else:
                comparison_df[f'{metric}_Rank'] = comparison_df[metric].rank(ascending=True)
        
        return comparison_df
    
    def generate_classification_report(self, y_true: np.ndarray, y_pred: np.ndarray,
                                     class_names: Optional[List[str]] = None,
                                     save_path: Optional[str] = None) -> str:
        """
        Generate detailed classification report.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            class_names: Names of classes
            save_path: Path to save the report
            
        Returns:
            Classification report as string
        """
        report = classification_report(y_true, y_pred, target_names=class_names, zero_division=0)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(f"Classification Report - {self.model_name}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(report)
        
        return report
    
    def generate_evaluation_report(self, model_results: Dict[str, Any], 
                                 additional_info: Optional[Dict[str, Any]] = None,
                                 save_path: Optional[str] = None) -> str:
        """
        Generate comprehensive evaluation report.
        
        Args:
            model_results: Model evaluation results
            additional_info: Additional information to include
            save_path: Path to save the report
            
        Returns:
            Evaluation report as string
        """
        report_lines = [
            f"Model Evaluation Report - {self.model_name}",
            "=" * 50,
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Model Type: {self.model_type}",
            ""
        ]
        
        # Add model results
        report_lines.append("Model Performance Metrics:")
        report_lines.append("-" * 30)
        for metric, value in model_results.items():
            if isinstance(value, float):
                report_lines.append(f"{metric.replace('_', ' ').title()}: {value:.4f}")
            else:
                report_lines.append(f"{metric.replace('_', ' ').title()}: {value}")
        
        report_lines.append("")
        
        # Add additional information if provided
        if additional_info:
            report_lines.append("Additional Information:")
            report_lines.append("-" * 30)
            for key, value in additional_info.items():
                report_lines.append(f"{key.replace('_', ' ').title()}: {value}")
            report_lines.append("")
        
        # Add interpretation
        report_lines.append("Interpretation:")
        report_lines.append("-" * 30)
        
        if self.model_type == 'classification':
            if 'accuracy' in model_results:
                accuracy = model_results['accuracy']
                if accuracy > 0.9:
                    report_lines.append("• Excellent classification performance")
                elif accuracy > 0.8:
                    report_lines.append("• Good classification performance")
                elif accuracy > 0.7:
                    report_lines.append("• Fair classification performance")
                else:
                    report_lines.append("• Poor classification performance")
            
            if 'f1_score' in model_results:
                f1 = model_results['f1_score']
                if f1 > 0.9:
                    report_lines.append("• Excellent balance between precision and recall")
                elif f1 > 0.8:
                    report_lines.append("• Good balance between precision and recall")
                else:
                    report_lines.append("• Poor balance between precision and recall")
        
        else:  # regression
            if 'r2_score' in model_results:
                r2 = model_results['r2_score']
                if r2 > 0.9:
                    report_lines.append("• Excellent prediction performance")
                elif r2 > 0.8:
                    report_lines.append("• Good prediction performance")
                elif r2 > 0.7:
                    report_lines.append("• Fair prediction performance")
                else:
                    report_lines.append("• Poor prediction performance")
            
            if 'rmse' in model_results:
                report_lines.append("• RMSE indicates the model's prediction error magnitude")
        
        report_text = "\n".join(report_lines)
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report_text)
        
        return report_text
    
    def save_evaluation_results(self, results: Dict[str, Any], 
                              comparison_df: Optional[pd.DataFrame] = None,
                              save_dir: str = "evaluation_results"):
        """
        Save evaluation results to files.
        
        Args:
            results: Evaluation results dictionary
            comparison_df: Model comparison DataFrame
            save_dir: Directory to save results
        """
        import os
        os.makedirs(save_dir, exist_ok=True)
        
        # Save individual results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save results as JSON
        import json
        results_file = os.path.join(save_dir, f"{self.model_name}_results_{timestamp}.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save comparison DataFrame if provided
        if comparison_df is not None:
            comparison_file = os.path.join(save_dir, f"{self.model_name}_comparison_{timestamp}.csv")
            comparison_df.to_csv(comparison_file, index=False)
        
        print(f"Evaluation results saved to {save_dir}")


class CrossValidator:
    """Cross-validation utility for model evaluation."""
    
    def __init__(self, cv_folds: int = 5, random_state: int = 42):
        """
        Initialize Cross Validator.
        
        Args:
            cv_folds: Number of cross-validation folds
            random_state: Random state for reproducibility
        """
        self.cv_folds = cv_folds
        self.random_state = random_state
    
    def cross_validate_model(self, model, X: np.ndarray, y: np.ndarray, 
                           model_type: str = 'classification') -> Dict[str, Any]:
        """
        Perform cross-validation on a model.
        
        Args:
            model: Model to cross-validate
            X: Feature matrix
            y: Target values
            model_type: Type of model ('classification' or 'regression')
            
        Returns:
            Cross-validation results
        """
        from sklearn.model_selection import cross_validate
        
        # Define scoring metrics
        if model_type == 'classification':
            scoring = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
            if hasattr(model, 'predict_proba'):
                scoring.append('roc_auc')
        else:
            scoring = ['neg_mean_absolute_error', 'neg_mean_squared_error', 'r2']
        
        # Perform cross-validation
        cv_results = cross_validate(model, X, y, cv=self.cv_folds, scoring=scoring, return_train_score=True)
        
        # Process results
        processed_results = {}
        for metric in scoring:
            train_key = f'train_{metric}'
            test_key = f'test_{metric}'
            
            if train_key in cv_results:
                processed_results[f'{metric}_train_mean'] = cv_results[train_key].mean()
                processed_results[f'{metric}_train_std'] = cv_results[train_key].std()
            
            if test_key in cv_results:
                processed_results[f'{metric}_test_mean'] = cv_results[test_key].mean()
                processed_results[f'{metric}_test_std'] = cv_results[test_key].std()
        
        processed_results['cv_folds'] = self.cv_folds
        
        return processed_results


if __name__ == "__main__":
    # Example usage
    print("Model Evaluation Module - Example Usage")
    
    # Create sample classification results
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    
    # Generate sample data
    X, y = make_classification(n_samples=1000, n_features=20, n_classes=3, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)
    
    # Initialize evaluator
    evaluator = ModelEvaluator("Sample Random Forest", "classification")
    
    # Evaluate model
    results = evaluator.evaluate_classification_model(y_test, y_pred, y_pred_proba)
    print("Evaluation Results:", results)
    
    # Generate report
    report = evaluator.generate_evaluation_report(results)
    print("\nEvaluation Report:")
    print(report)
    
    # Plot confusion matrix
    print("\nPlotting confusion matrix...")
    evaluator.plot_confusion_matrix(y_test, y_pred, show_plot=False)
    
    # Cross-validation example
    print("\nPerforming cross-validation...")
    cv_validator = CrossValidator(cv_folds=5)
    cv_results = cv_validator.cross_validate_model(model, X_train, y_train)
    print("Cross-Validation Results:", cv_results)