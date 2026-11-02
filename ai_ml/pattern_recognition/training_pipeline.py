"""
Training Pipeline for Pattern Recognition Models

This module provides a unified training pipeline for all pattern recognition models:
- Domain Reputation Classifier (Random Forest)
- Phishing URL Detector (XGBoost)
- Sender Reputation Predictor (Gradient Boosting)

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import os
import json
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from .random_forest_domain_reputation import DomainReputationClassifier, create_sample_data as create_domain_data
from .xgboost_phishing_detection import PhishingURLDetector, create_sample_phishing_data
from .gradient_boosting_sender_reputation import SenderReputationPredictor, create_sample_sender_data
from .model_evaluation import ModelEvaluator, CrossValidator


class PatternRecognitionPipeline:
    """Unified training pipeline for all pattern recognition models."""
    
    def __init__(self, models_dir: str = "trained_models", results_dir: str = "training_results"):
        """
        Initialize the Pattern Recognition Pipeline.
        
        Args:
            models_dir: Directory to save trained models
            results_dir: Directory to save training results
        """
        self.models_dir = models_dir
        self.results_dir = results_dir
        self.trained_models = {}
        self.training_history = {}
        
        # Create directories if they don't exist
        os.makedirs(models_dir, exist_ok=True)
        os.makedirs(results_dir, exist_ok=True)
        
        # Initialize models
        self.domain_classifier = DomainReputationClassifier()
        self.phishing_detector = PhishingURLDetector()
        self.sender_predictor = SenderReputationPredictor()
        
    def generate_synthetic_data(self, n_samples: Dict[str, int]) -> Dict[str, Tuple]:
        """
        Generate synthetic training data for all models.
        
        Args:
            n_samples: Dictionary with sample counts for each model
            
        Returns:
            Dictionary containing training data for all models
        """
        print("Generating synthetic training data...")
        
        data = {}
        
        # Domain reputation data
        if 'domain' in n_samples:
            domains, scores, categories = create_domain_data(n_samples['domain'])
            data['domain'] = {
                'domains': domains,
                'scores': scores,
                'categories': categories
            }
            print(f"Generated {len(domains)} domain samples")
        
        # Phishing URL data
        if 'phishing' in n_samples:
            urls, labels = create_sample_phishing_data(n_samples['phishing'])
            data['phishing'] = {
                'urls': urls,
                'labels': labels
            }
            print(f"Generated {len(urls)} phishing URL samples")
        
        # Sender reputation data
        if 'sender' in n_samples:
            emails, scores, categories = create_sample_sender_data(n_samples['sender'])
            data['sender'] = {
                'emails': emails,
                'scores': scores,
                'categories': categories
            }
            print(f"Generated {len(emails)} sender samples")
        
        return data
    
    def train_domain_model(self, domains: List[str], scores: List[float], 
                          categories: List[str], 
                          model_config: Optional[Dict] = None,
                          hyperparameter_tuning: bool = True,
                          evaluation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the domain reputation classifier.
        
        Args:
            domains: List of domain strings
            scores: List of reputation scores
            categories: List of reputation categories
            model_config: Custom model configuration
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            evaluation_split: Data split ratio for evaluation
            
        Returns:
            Training results and metrics
        """
        print("\n" + "="*50)
        print("Training Domain Reputation Classifier")
        print("="*50)
        
        # Configure model
        if model_config:
            self.domain_classifier.model_type = model_config.get('model_type', 'classification')
            self.domain_classifier.n_estimators = model_config.get('n_estimators', 100)
            self.domain_classifier.max_depth = model_config.get('max_depth', 20)
            self.domain_classifier.random_state = model_config.get('random_state', 42)
        
        # Train model
        train_metrics = self.domain_classifier.train(
            domains, scores, categories, validation_split=evaluation_split
        )
        print(f"Initial training metrics: {train_metrics}")
        
        # Hyperparameter tuning
        tuning_results = None
        if hyperparameter_tuning:
            print("Performing hyperparameter tuning...")
            tuning_results = self.domain_classifier.hyperparameter_tuning(domains, scores, categories)
            print(f"Best parameters: {tuning_results['best_params']}")
            print(f"Best CV score: {tuning_results['best_score']}")
        
        # Evaluate model
        test_domains, test_scores, test_categories = self._split_data(
            domains, scores, categories, evaluation_split
        )
        
        eval_results = self.domain_classifier.evaluate_model(
            test_domains, test_scores, test_categories
        )
        print(f"Evaluation results: {eval_results}")
        
        # Store trained model
        self.trained_models['domain'] = self.domain_classifier
        
        # Compile results
        results = {
            'model_name': 'Domain Reputation Classifier',
            'model_type': self.domain_classifier.model_type,
            'training_metrics': train_metrics,
            'hyperparameter_tuning': tuning_results,
            'evaluation_results': eval_results,
            'training_samples': len(domains),
            'test_samples': len(test_domains),
            'training_timestamp': datetime.now().isoformat()
        }
        
        self.training_history['domain'] = results
        return results
    
    def train_phishing_model(self, urls: List[str], labels: List[int],
                           model_config: Optional[Dict] = None,
                           hyperparameter_tuning: bool = True,
                           evaluation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the phishing URL detector.
        
        Args:
            urls: List of URL strings
            labels: List of labels (0=legitimate, 1=phishing)
            model_config: Custom model configuration
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            evaluation_split: Data split ratio for evaluation
            
        Returns:
            Training results and metrics
        """
        print("\n" + "="*50)
        print("Training Phishing URL Detector")
        print("="*50)
        
        # Configure model
        if model_config:
            self.phishing_detector.n_estimators = model_config.get('n_estimators', 100)
            self.phishing_detector.max_depth = model_config.get('max_depth', 6)
            self.phishing_detector.learning_rate = model_config.get('learning_rate', 0.1)
            self.phishing_detector.random_state = model_config.get('random_state', 42)
        
        # Train model
        train_metrics = self.phishing_detector.train(
            urls, labels, validation_split=evaluation_split
        )
        print(f"Initial training metrics: {train_metrics}")
        
        # Hyperparameter tuning
        tuning_results = None
        if hyperparameter_tuning:
            print("Performing hyperparameter tuning...")
            tuning_results = self.phishing_detector.hyperparameter_tuning(urls, labels)
            print(f"Best parameters: {tuning_results['best_params']}")
            print(f"Best CV score: {tuning_results['best_score']}")
        
        # Evaluate model
        test_urls, test_labels = self._split_data(urls, labels, evaluation_split)
        
        eval_results = self.phishing_detector.evaluate_model(test_urls, test_labels)
        print(f"Evaluation results: {eval_results}")
        
        # Store trained model
        self.trained_models['phishing'] = self.phishing_detector
        
        # Compile results
        results = {
            'model_name': 'Phishing URL Detector',
            'model_type': 'classification',
            'training_metrics': train_metrics,
            'hyperparameter_tuning': tuning_results,
            'evaluation_results': eval_results,
            'training_samples': len(urls),
            'test_samples': len(test_urls),
            'phishing_ratio': sum(labels) / len(labels),
            'training_timestamp': datetime.now().isoformat()
        }
        
        self.training_history['phishing'] = results
        return results
    
    def train_sender_model(self, emails: List[str], scores: List[float], 
                          categories: List[str],
                          model_config: Optional[Dict] = None,
                          hyperparameter_tuning: bool = True,
                          evaluation_split: float = 0.2) -> Dict[str, Any]:
        """
        Train the sender reputation predictor.
        
        Args:
            emails: List of email addresses
            scores: List of reputation scores
            categories: List of reputation categories
            model_config: Custom model configuration
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            evaluation_split: Data split ratio for evaluation
            
        Returns:
            Training results and metrics
        """
        print("\n" + "="*50)
        print("Training Sender Reputation Predictor")
        print("="*50)
        
        # Configure model
        if model_config:
            self.sender_predictor.model_type = model_config.get('model_type', 'classification')
            self.sender_predictor.n_estimators = model_config.get('n_estimators', 100)
            self.sender_predictor.max_depth = model_config.get('max_depth', 5)
            self.sender_predictor.learning_rate = model_config.get('learning_rate', 0.1)
            self.sender_predictor.random_state = model_config.get('random_state', 42)
        
        # Train model
        train_metrics = self.sender_predictor.train(
            emails, scores, categories, validation_split=evaluation_split
        )
        print(f"Initial training metrics: {train_metrics}")
        
        # Hyperparameter tuning
        tuning_results = None
        if hyperparameter_tuning:
            print("Performing hyperparameter tuning...")
            tuning_results = self.sender_predictor.hyperparameter_tuning(emails, scores, categories)
            print(f"Best parameters: {tuning_results['best_params']}")
            print(f"Best CV score: {tuning_results['best_score']}")
        
        # Evaluate model
        test_emails, test_scores, test_categories = self._split_data(
            emails, scores, categories, evaluation_split
        )
        
        eval_results = self.sender_predictor.evaluate_model(
            test_emails, test_scores, test_categories
        )
        print(f"Evaluation results: {eval_results}")
        
        # Store trained model
        self.trained_models['sender'] = self.sender_predictor
        
        # Compile results
        results = {
            'model_name': 'Sender Reputation Predictor',
            'model_type': self.sender_predictor.model_type,
            'training_metrics': train_metrics,
            'hyperparameter_tuning': tuning_results,
            'evaluation_results': eval_results,
            'training_samples': len(emails),
            'test_samples': len(test_emails),
            'training_timestamp': datetime.now().isoformat()
        }
        
        self.training_history['sender'] = results
        return results
    
    def _split_data(self, *data_arrays, split_ratio: float):
        """Split data arrays into train/test."""
        from sklearn.model_selection import train_test_split
        
        if len(data_arrays) == 1:
            X = data_arrays[0]
            X_train, X_test = train_test_split(X, test_size=split_ratio, random_state=42)
            return X_train, X_test
        else:
            return train_test_split(*data_arrays, test_size=split_ratio, random_state=42)
    
    def run_complete_pipeline(self, n_samples: Dict[str, int] = None,
                            model_configs: Optional[Dict[str, Dict]] = None,
                            hyperparameter_tuning: bool = True,
                            save_models: bool = True,
                            generate_plots: bool = True) -> Dict[str, Any]:
        """
        Run the complete training pipeline for all models.
        
        Args:
            n_samples: Number of samples for each model
            model_configs: Custom configurations for each model
            hyperparameter_tuning: Whether to perform hyperparameter tuning
            save_models: Whether to save trained models
            generate_plots: Whether to generate evaluation plots
            
        Returns:
            Complete pipeline results
        """
        print("Starting Pattern Recognition Training Pipeline")
        print("=" * 60)
        
        pipeline_start = datetime.now()
        
        # Default sample sizes
        if n_samples is None:
            n_samples = {
                'domain': 2000,
                'phishing': 3000,
                'sender': 2500
            }
        
        # Generate synthetic data
        data = self.generate_synthetic_data(n_samples)
        
        # Training configurations
        if model_configs is None:
            model_configs = {}
        
        pipeline_results = {
            'pipeline_start': pipeline_start.isoformat(),
            'sample_sizes': n_samples,
            'hyperparameter_tuning': hyperparameter_tuning,
            'models': {}
        }
        
        # Train domain model
        if 'domain' in data:
            domain_config = model_configs.get('domain', {})
            domain_results = self.train_domain_model(
                data['domain']['domains'],
                data['domain']['scores'],
                data['domain']['categories'],
                model_config=domain_config,
                hyperparameter_tuning=hyperparameter_tuning
            )
            pipeline_results['models']['domain'] = domain_results
            
            if generate_plots:
                self._generate_domain_plots()
        
        # Train phishing model
        if 'phishing' in data:
            phishing_config = model_configs.get('phishing', {})
            phishing_results = self.train_phishing_model(
                data['phishing']['urls'],
                data['phishing']['labels'],
                model_config=phishing_config,
                hyperparameter_tuning=hyperparameter_tuning
            )
            pipeline_results['models']['phishing'] = phishing_results
            
            if generate_plots:
                self._generate_phishing_plots()
        
        # Train sender model
        if 'sender' in data:
            sender_config = model_configs.get('sender', {})
            sender_results = self.train_sender_model(
                data['sender']['emails'],
                data['sender']['scores'],
                data['sender']['categories'],
                model_config=sender_config,
                hyperparameter_tuning=hyperparameter_tuning
            )
            pipeline_results['models']['sender'] = sender_results
            
            if generate_plots:
                self._generate_sender_plots()
        
        # Save models
        if save_models:
            self.save_all_models()
        
        # Save pipeline results
        pipeline_results['pipeline_end'] = datetime.now().isoformat()
        pipeline_results['total_duration'] = str(datetime.now() - pipeline_start)
        
        self.save_pipeline_results(pipeline_results)
        
        # Generate summary
        self._generate_pipeline_summary(pipeline_results)
        
        print("\n" + "="*60)
        print("Pipeline Execution Completed!")
        print("="*60)
        print(f"Total duration: {pipeline_results['total_duration']}")
        print(f"Models trained: {list(pipeline_results['models'].keys())}")
        print(f"Results saved to: {self.results_dir}")
        print(f"Models saved to: {self.models_dir}")
        
        return pipeline_results
    
    def _generate_domain_plots(self):
        """Generate evaluation plots for domain model."""
        try:
            from .model_evaluation import ModelEvaluator
            
            evaluator = ModelEvaluator("Domain Reputation", "classification")
            
            # Get test data for plotting
            X_test = getattr(self.domain_classifier, 'X_test', None)
            y_test = getattr(self.domain_classifier, 'y_test', None)
            
            if X_test is not None and y_test is not None:
                y_pred = self.domain_classifier.model.predict(X_test)
                
                # Confusion matrix
                evaluator.plot_confusion_matrix(
                    y_test, y_pred, 
                    class_names=self.domain_classifier.reputation_categories,
                    save_path=os.path.join(self.results_dir, 'domain_confusion_matrix.png'),
                    show_plot=False
                )
                
                # Feature importance
                if self.domain_classifier.feature_importance:
                    evaluator.plot_feature_importance_comparison(
                        self.domain_classifier.feature_importance,
                        save_path=os.path.join(self.results_dir, 'domain_feature_importance.png'),
                        show_plot=False
                    )
                
        except Exception as e:
            print(f"Warning: Could not generate domain plots: {e}")
    
    def _generate_phishing_plots(self):
        """Generate evaluation plots for phishing model."""
        try:
            from .model_evaluation import ModelEvaluator
            
            evaluator = ModelEvaluator("Phishing Detection", "classification")
            
            # Get test data for plotting
            X_test = getattr(self.phishing_detector, 'X_test', None)
            y_test = getattr(self.phishing_detector, 'y_test', None)
            y_pred_proba = getattr(self.phishing_detector, 'y_pred_proba', None)
            
            if X_test is not None and y_test is not None:
                y_pred = self.phishing_detector.model.predict(X_test)
                
                # Confusion matrix
                evaluator.plot_confusion_matrix(
                    y_test, y_pred, 
                    class_names=['Legitimate', 'Phishing'],
                    save_path=os.path.join(self.results_dir, 'phishing_confusion_matrix.png'),
                    show_plot=False
                )
                
                # ROC and PR curves
                if y_pred_proba is not None:
                    evaluator.plot_roc_curve(
                        y_test, y_pred_proba,
                        save_path=os.path.join(self.results_dir, 'phishing_roc_curve.png'),
                        show_plot=False
                    )
                    
                    evaluator.plot_precision_recall_curve(
                        y_test, y_pred_proba,
                        save_path=os.path.join(self.results_dir, 'phishing_pr_curve.png'),
                        show_plot=False
                    )
                
                # Feature importance
                if self.phishing_detector.feature_importance:
                    evaluator.plot_feature_importance_comparison(
                        self.phishing_detector.feature_importance,
                        save_path=os.path.join(self.results_dir, 'phishing_feature_importance.png'),
                        show_plot=False
                    )
                
        except Exception as e:
            print(f"Warning: Could not generate phishing plots: {e}")
    
    def _generate_sender_plots(self):
        """Generate evaluation plots for sender model."""
        try:
            from .model_evaluation import ModelEvaluator
            
            evaluator = ModelEvaluator("Sender Reputation", "classification")
            
            # Get test data for plotting
            X_test = getattr(self.sender_predictor, 'X_test', None)
            y_test = getattr(self.sender_predictor, 'y_test', None)
            
            if X_test is not None and y_test is not None:
                y_pred = self.sender_predictor.model.predict(X_test)
                
                # Confusion matrix
                evaluator.plot_confusion_matrix(
                    y_test, y_pred, 
                    class_names=self.sender_predictor.reputation_categories,
                    save_path=os.path.join(self.results_dir, 'sender_confusion_matrix.png'),
                    show_plot=False
                )
                
                # Feature importance
                if self.sender_predictor.feature_importance:
                    evaluator.plot_feature_importance_comparison(
                        self.sender_predictor.feature_importance,
                        save_path=os.path.join(self.results_dir, 'sender_feature_importance.png'),
                        show_plot=False
                    )
                
        except Exception as e:
            print(f"Warning: Could not generate sender plots: {e}")
    
    def save_all_models(self):
        """Save all trained models."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for model_name, model in self.trained_models.items():
            model_path = os.path.join(self.models_dir, f"{model_name}_model_{timestamp}.pkl")
            model.save_model(model_path)
            print(f"Saved {model_name} model to {model_path}")
    
    def save_pipeline_results(self, results: Dict[str, Any]):
        """Save pipeline results to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = os.path.join(self.results_dir, f"pipeline_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Pipeline results saved to {results_file}")
    
    def _generate_pipeline_summary(self, results: Dict[str, Any]):
        """Generate a summary of the pipeline execution."""
        print("\n" + "="*60)
        print("PIPELINE SUMMARY")
        print("="*60)
        
        for model_name, model_results in results['models'].items():
            print(f"\n{model_results['model_name']}:")
            print(f"  Training samples: {model_results['training_samples']}")
            print(f"  Test samples: {model_results['test_samples']}")
            
            eval_results = model_results.get('evaluation_results', {})
            if eval_results:
                if 'accuracy' in eval_results:
                    print(f"  Accuracy: {eval_results['accuracy']:.4f}")
                if 'f1_score' in eval_results:
                    print(f"  F1-Score: {eval_results['f1_score']:.4f}")
                if 'r2_score' in eval_results:
                    print(f"  R² Score: {eval_results['r2_score']:.4f}")
        
        print(f"\nTotal pipeline duration: {results.get('total_duration', 'N/A')}")
        print(f"Hyperparameter tuning: {'Enabled' if results.get('hyperparameter_tuning') else 'Disabled'}")


def main():
    """Main function to demonstrate pipeline usage."""
    print("Pattern Recognition Training Pipeline Demo")
    print("="*50)
    
    # Initialize pipeline
    pipeline = PatternRecognitionPipeline()
    
    # Run complete pipeline with moderate sample sizes for demo
    results = pipeline.run_complete_pipeline(
        n_samples={
            'domain': 1000,
            'phishing': 1500,
            'sender': 1200
        },
        hyperparameter_tuning=False,  # Disable for faster demo
        save_models=True,
        generate_plots=True
    )
    
    return pipeline, results


if __name__ == "__main__":
    pipeline, results = main()