"""
Pattern Recognition & Classification Models Package

This package provides comprehensive implementations of machine learning models
for cybersecurity pattern recognition tasks.

Models Included:
- Random Forest Classifier for Domain Reputation Scoring
- XGBoost for Phishing URL Detection  
- Gradient Boosting for Sender Reputation Prediction

Features:
- Comprehensive feature extraction functions
- Model training pipelines with hyperparameter tuning
- Prediction and inference interfaces
- Model evaluation and comparison tools
- Real-time analysis capabilities

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI-ML Pattern Recognition System"
__email__ = "ai-ml-system@example.com"
__description__ = "Pattern Recognition & Classification Models for Cybersecurity"

# Import main classes for easy access
from .feature_extraction import (
    DomainFeatureExtractor,
    URLFeatureExtractor,
    SenderFeatureExtractor,
    extract_all_features,
    create_feature_matrix
)

from .random_forest_domain_reputation import (
    DomainReputationClassifier,
    create_sample_data as create_domain_sample_data
)

from .xgboost_phishing_detection import (
    PhishingURLDetector,
    create_sample_phishing_data
)

from .gradient_boosting_sender_reputation import (
    SenderReputationPredictor,
    create_sample_sender_data
)

from .model_evaluation import (
    ModelEvaluator,
    CrossValidator
)

from .training_pipeline import (
    PatternRecognitionPipeline
)

from .inference import (
    PatternRecognitionInference
)

# Package metadata
__all__ = [
    # Feature extraction
    'DomainFeatureExtractor',
    'URLFeatureExtractor', 
    'SenderFeatureExtractor',
    'extract_all_features',
    'create_feature_matrix',
    
    # Models
    'DomainReputationClassifier',
    'PhishingURLDetector',
    'SenderReputationPredictor',
    
    # Sample data generators
    'create_domain_sample_data',
    'create_sample_phishing_data',
    'create_sample_sender_data',
    
    # Evaluation
    'ModelEvaluator',
    'CrossValidator',
    
    # Pipeline and inference
    'PatternRecognitionPipeline',
    'PatternRecognitionInference'
]

# Package-level configuration
DEFAULT_CONFIG = {
    'models_dir': 'trained_models',
    'results_dir': 'training_results',
    'evaluation_dir': 'evaluation_results',
    'random_state': 42,
    'cv_folds': 5,
    'test_size': 0.2
}

def get_package_info():
    """Get comprehensive package information."""
    return {
        'name': 'pattern_recognition',
        'version': __version__,
        'author': __author__,
        'description': __description__,
        'models': [
            'Random Forest Classifier (Domain Reputation)',
            'XGBoost Classifier (Phishing URL Detection)',
            'Gradient Boosting Classifier (Sender Reputation)'
        ],
        'features': [
            'Comprehensive feature extraction',
            'Automated training pipelines',
            'Hyperparameter tuning',
            'Model evaluation and comparison',
            'Real-time inference capabilities',
            'Batch processing support'
        ],
        'supported_tasks': [
            'Domain reputation scoring',
            'Phishing URL detection',
            'Sender reputation prediction',
            'Risk assessment',
            'Security analysis'
        ],
        'default_config': DEFAULT_CONFIG
    }

def create_default_pipeline(**kwargs):
    """Create a default pattern recognition pipeline with standard configuration."""
    config = {**DEFAULT_CONFIG, **kwargs}
    return PatternRecognitionPipeline(
        models_dir=config['models_dir'],
        results_dir=config['results_dir']
    )

def create_default_inference(**kwargs):
    """Create a default inference system with standard configuration."""
    config = {**DEFAULT_CONFIG, **kwargs}
    return PatternRecognitionInference(
        models_dir=config['models_dir']
    )

# Example usage instructions
USAGE_EXAMPLES = {
    'basic_training': """
# Basic training example
from ai_ml.pattern_recognition import PatternRecognitionPipeline

pipeline = PatternRecognitionPipeline()
results = pipeline.run_complete_pipeline(
    n_samples={'domain': 1000, 'phishing': 1500, 'sender': 1200},
    hyperparameter_tuning=True
)
""",
    
    'basic_inference': """
# Basic inference example  
from ai_ml.pattern_recognition import PatternRecognitionInference

inference = PatternRecognitionInference()
inference.load_models()

# Real-time analysis
result = inference.real_time_analyzer(
    domain='example.com',
    url='https://example.com/login',
    sender='user@example.com'
)
""",
    
    'feature_extraction': """
# Feature extraction example
from ai_ml.pattern_recognition import extract_all_features

# Extract features from domain
domain_features = extract_all_features('google.com', 'domain')

# Extract features from URL  
url_features = extract_all_features('https://google.com/search?q=test', 'url')

# Extract features from email
email_features = extract_all_features('user@gmail.com', 'email')
""",
    
    'individual_models': """
# Individual model usage
from ai_ml.pattern_recognition import (
    DomainReputationClassifier,
    PhishingURLDetector, 
    SenderReputationPredictor
)

# Domain reputation
domain_model = DomainReputationClassifier()
domain_predictions = domain_model.predict_reputation(['google.com', 'malware.com'])

# Phishing detection
phishing_model = PhishingURLDetector()
phishing_results = phishing_model.detect_phishing(['https://google.com', 'http://phishing.tk'])

# Sender reputation
sender_model = SenderReputationPredictor()
sender_predictions = sender_model.predict_reputation(['user@company.com', 'spam@scam.ru'])
"""
}

def get_usage_examples():
    """Get usage examples for the package."""
    return USAGE_EXAMPLES

# Package initialization summary
def _print_package_info():
    """Print package information on import."""
    info = get_package_info()
    print(f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                   Pattern Recognition & Classification Models                ║
║                                Version {info['version']}                                  ║
╠════════════════════════════════════════════════════════════════════════════╣
║ Models:                                                                     ║
║ • Random Forest Classifier (Domain Reputation)                             ║
║ • XGBoost Classifier (Phishing URL Detection)                              ║
║ • Gradient Boosting Classifier (Sender Reputation)                         ║
║                                                                              ║
║ Key Features:                                                               ║
║ • Comprehensive feature extraction                                          ║
║ • Automated training pipelines                                              ║
║ • Hyperparameter tuning                                                     ║
║ • Model evaluation and comparison                                           ║
║ • Real-time inference capabilities                                          ║
║ • Batch processing support                                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# Print package info on import (can be disabled by setting PRINT_PACKAGE_INFO=False)
try:
    import os
    if os.environ.get('PRINT_PACKAGE_INFO', 'True').lower() == 'true':
        _print_package_info()
except:
    pass  # Silent fail if environment variable access fails