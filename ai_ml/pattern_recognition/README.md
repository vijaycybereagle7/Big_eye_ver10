# Pattern Recognition & Classification Models

A comprehensive machine learning package for cybersecurity pattern recognition tasks, featuring Random Forest, XGBoost, and Gradient Boosting models for domain reputation scoring, phishing URL detection, and sender reputation prediction.

## 🚀 Features

- **Random Forest Classifier**: Domain reputation scoring with comprehensive domain analysis
- **XGBoost Classifier**: Advanced phishing URL detection with high accuracy
- **Gradient Boosting Classifier**: Sender reputation prediction with multi-class support
- **Comprehensive Feature Extraction**: Domain, URL, and email analysis
- **Automated Training Pipelines**: End-to-end model training with hyperparameter tuning
- **Model Evaluation Suite**: Detailed metrics, visualizations, and comparisons
- **Real-time Inference**: Live prediction capabilities for production use
- **Batch Processing**: Efficient analysis of multiple inputs

## 📋 Models Overview

### 1. Domain Reputation Classifier (Random Forest)
- **Purpose**: Score domain reputation from malicious to trusted
- **Categories**: Malicious, Suspicious, Legitimate, Trusted
- **Features**: Domain length, registration age, DNS resolution, suspicious patterns
- **Use Cases**: Email filtering, web security, domain blacklisting

### 2. Phishing URL Detector (XGBoost)
- **Purpose**: Detect malicious URLs and phishing attempts
- **Categories**: Legitimate, Phishing
- **Features**: URL structure, suspicious keywords, entropy analysis
- **Use Cases**: Web filtering, email security, browser protection

### 3. Sender Reputation Predictor (Gradient Boosting)
- **Purpose**: Predict email sender reputation and trustworthiness
- **Categories**: Spammer, Suspicious, Legitimate, Trusted
- **Features**: Email structure, domain analysis, metadata extraction
- **Use Cases**: Email authentication, spam detection, sender verification

## 🛠 Installation

### Requirements
```bash
pip install numpy pandas scikit-learn xgboost matplotlib seaborn joblib
```

### Optional Dependencies
```bash
pip install whois  # For domain registration analysis
```

## 📖 Quick Start

### Basic Training Pipeline

```python
from ai_ml.pattern_recognition import PatternRecognitionPipeline

# Initialize pipeline
pipeline = PatternRecognitionPipeline()

# Run complete training pipeline
results = pipeline.run_complete_pipeline(
    n_samples={
        'domain': 2000,    # Number of domain samples
        'phishing': 3000,  # Number of URL samples  
        'sender': 2500     # Number of email samples
    },
    hyperparameter_tuning=True,  # Enable hyperparameter optimization
    save_models=True,           # Save trained models
    generate_plots=True         # Generate evaluation plots
)

print("Training completed!")
print(f"Models trained: {list(results['models'].keys())}")
```

### Real-time Inference

```python
from ai_ml.pattern_recognition import PatternRecognitionInference

# Initialize inference system
inference = PatternRecognitionInference()

# Load trained models
inference.load_models()

# Real-time analysis
result = inference.real_time_analyzer(
    domain='example.com',
    url='https://example.com/login', 
    sender='user@company.com'
)

print("Analysis Results:", result)
```

### Individual Model Usage

```python
from ai_ml.pattern_recognition import (
    DomainReputationClassifier,
    PhishingURLDetector,
    SenderReputationPredictor
)

# Domain Reputation Analysis
domain_model = DomainReputationClassifier()
# (Train model first)
domain_predictions = domain_model.predict_reputation(['google.com', 'malware-site.ru'])

# Phishing Detection
phishing_model = PhishingURLDetector()
# (Train model first)
phishing_results = phishing_model.detect_phishing([
    'https://google.com',
    'http://phishing-site.tk/login'
])

# Sender Reputation
sender_model = SenderReputationPredictor()
# (Train model first)
sender_predictions = sender_model.predict_reputation([
    'ceo@company.com',
    'spam@scammer.ru'
])
```

## 🔧 Advanced Usage

### Feature Extraction

```python
from ai_ml.pattern_recognition import extract_all_features

# Domain features
domain_features = extract_all_features('google.com', 'domain')
print("Domain features:", domain_features)

# URL features
url_features = extract_all_features('https://google.com/search?q=test', 'url')
print("URL features:", url_features)

# Email features
email_features = extract_all_features('user@gmail.com', 'email')
print("Email features:", email_features)
```

### Custom Model Configuration

```python
# Custom domain classifier configuration
domain_config = {
    'model_type': 'classification',
    'n_estimators': 200,
    'max_depth': 25,
    'random_state': 42
}

# Custom phishing detector configuration
phishing_config = {
    'n_estimators': 150,
    'max_depth': 8,
    'learning_rate': 0.15,
    'random_state': 42
}

# Run pipeline with custom configuration
results = pipeline.run_complete_pipeline(
    n_samples={'domain': 1500, 'phishing': 2000, 'sender': 1800},
    model_configs={
        'domain': domain_config,
        'phishing': phishing_config
    }
)
```

### Batch Processing

```python
# Batch analysis
batch_results = inference.batch_analyze(
    domains=['example.com', 'malicious-site.ru'],
    urls=['https://google.com', 'http://phishing-site.tk'],
    senders=['user@company.com', 'spam@scammer.ru'],
    return_all_probabilities=True
)

print("Batch Analysis Results:")
print(f"Domains: {batch_results['domains']}")
print(f"URLs: {batch_results['urls']}")
print(f"Senders: {batch_results['senders']}")
```

### Model Evaluation

```python
from ai_ml.pattern_recognition import ModelEvaluator, CrossValidator

# Evaluate classification model
evaluator = ModelEvaluator("Phishing Detector", "classification")
results = evaluator.evaluate_classification_model(
    y_true=test_labels, 
    y_pred=predictions, 
    y_pred_proba=probabilities
)

# Cross-validation
cv_validator = CrossValidator(cv_folds=5)
cv_results = cv_validator.cross_validate_model(model, X, y)

# Generate evaluation plots
evaluator.plot_confusion_matrix(y_true, y_pred)
evaluator.plot_roc_curve(y_true, y_pred_proba)
evaluator.plot_precision_recall_curve(y_true, y_pred_proba)
```

## 📊 Model Performance

### Expected Performance Metrics

| Model | Accuracy | F1-Score | AUC-ROC | Use Case |
|-------|----------|----------|---------|----------|
| Domain Reputation | 85-92% | 0.83-0.90 | 0.90-0.95 | Classification |
| Phishing Detection | 90-95% | 0.88-0.93 | 0.92-0.97 | Classification |
| Sender Reputation | 82-88% | 0.80-0.86 | 0.88-0.93 | Classification |

*Note: Performance metrics are based on synthetic datasets and may vary with real-world data.*

### Feature Importance

The models utilize comprehensive feature sets:

**Domain Features (25+ features):**
- Domain length, subdomain count, character diversity
- Registration age, registrar information, DNS resolution
- Suspicious keywords, TLD analysis

**URL Features (30+ features):**
- URL structure analysis, parameter counting
- Suspicious patterns, encoding analysis
- Phishing keywords, shortening service detection

**Email Features (20+ features):**
- Email structure analysis, domain parts
- Character analysis, suspicious patterns
- Free provider detection, TLD analysis

## 📁 File Structure

```
ai_ml/pattern_recognition/
├── __init__.py                    # Package initialization
├── feature_extraction.py         # Feature extraction functions
├── random_forest_domain_reputation.py    # Domain reputation model
├── xgboost_phishing_detection.py        # Phishing detection model
├── gradient_boosting_sender_reputation.py # Sender reputation model
├── model_evaluation.py           # Evaluation utilities
├── training_pipeline.py          # Training orchestration
├── inference.py                  # Inference interface
└── README.md                     # Documentation
```

## 🎯 API Reference

### Core Classes

#### `PatternRecognitionPipeline`
Unified training pipeline for all models.

**Methods:**
- `run_complete_pipeline()`: Train all models with full pipeline
- `train_domain_model()`: Train domain reputation model
- `train_phishing_model()`: Train phishing detection model  
- `train_sender_model()`: Train sender reputation model

#### `PatternRecognitionInference`
Unified inference interface for all trained models.

**Methods:**
- `load_models()`: Load trained models from files
- `predict_domain_reputation()`: Analyze domain reputation
- `detect_phishing_urls()`: Detect phishing URLs
- `predict_sender_reputation()`: Predict sender reputation
- `real_time_analyzer()`: Comprehensive real-time analysis
- `batch_analyze()`: Process multiple inputs efficiently

#### Individual Model Classes
- `DomainReputationClassifier`: Random Forest domain analysis
- `PhishingURLDetector`: XGBoost URL phishing detection
- `SenderReputationPredictor`: Gradient Boosting sender analysis

### Utility Classes

#### `ModelEvaluator`
Comprehensive model evaluation with metrics and visualizations.

#### `Feature Extractors`
- `DomainFeatureExtractor`: Domain-specific feature extraction
- `URLFeatureExtractor`: URL-specific feature extraction  
- `SenderFeatureExtractor`: Email/sender-specific feature extraction

## 🔍 Examples

### Complete Example: End-to-End Workflow

```python
from ai_ml.pattern_recognition import (
    PatternRecognitionPipeline,
    PatternRecognitionInference
)

def main():
    # Step 1: Training
    print("Starting training pipeline...")
    pipeline = PatternRecognitionPipeline()
    
    results = pipeline.run_complete_pipeline(
        n_samples={'domain': 1000, 'phishing': 1500, 'sender': 1200},
        hyperparameter_tuning=False,  # Disable for demo
        save_models=True
    )
    
    # Step 2: Inference
    print("Loading models for inference...")
    inference = PatternRecognitionInference()
    inference.load_models()
    
    # Step 3: Real-time analysis
    test_cases = [
        {'domain': 'google.com', 'url': 'https://google.com', 'sender': 'support@google.com'},
        {'domain': 'malware-site.ru', 'url': 'http://phishing-site.tk', 'sender': 'spam@scam.ru'}
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nAnalyzing Test Case {i}: {case}")
        result = inference.real_time_analyzer(**case)
        print(f"Overall Assessment: {result['overall_assessment']}")

if __name__ == "__main__":
    main()
```

### Security Analysis Example

```python
def security_analysis_workflow():
    """Example workflow for security analysis."""
    inference = PatternRecognitionInference()
    inference.load_models()
    
    # Analyze suspicious email with multiple data points
    analysis = inference.real_time_analyzer(
        domain='suspicious-domain.tk',
        url='http://suspicious-domain.tk/login',
        sender={'email': 'noreply@suspicious-domain.tk', 'domain': 'suspicious-domain.tk'}
    )
    
    # Extract key findings
    findings = {
        'domain_risk': analysis['results']['domain']['analysis']['risk_assessment'],
        'url_risk': analysis['results']['url']['analysis']['risk_level'],
        'sender_trust': analysis['results']['sender']['analysis']['trust_level'],
        'overall_recommendation': analysis['overall_assessment']['recommendation']
    }
    
    print("Security Analysis Results:")
    for key, value in findings.items():
        print(f"  {key}: {value}")
    
    return findings
```

## 🚨 Important Notes

### Model Limitations
- Models are trained on synthetic datasets for demonstration
- Real-world performance requires training on actual threat data
- Feature extraction may require internet connectivity for some checks
- Domain registration features depend on WHOIS database availability

### Performance Considerations
- Training time increases with sample size and hyperparameter tuning
- Feature extraction can be computationally intensive for large batches
- Model inference is optimized for real-time use
- Memory usage scales with number of features and models loaded

### Security Considerations
- Models should be regularly retrained with new threat data
- False positives/negatives should be monitored in production
- Consider ensemble methods for critical security applications
- Implement proper model versioning and rollback procedures

## 🤝 Contributing

This is a demonstration package. For production use:

1. Train models on real threat intelligence data
2. Implement proper data validation and cleaning
3. Add comprehensive logging and monitoring
4. Consider privacy and security implications
5. Implement proper testing and validation procedures

## 📄 License

This package is provided for educational and demonstration purposes. See LICENSE file for details.

## 📞 Support

For questions, issues, or contributions, please refer to the documentation and code comments for detailed implementation guidance.

---

**Disclaimer**: This package is intended for educational and research purposes. For production security applications, ensure proper validation, testing, and ongoing maintenance of models and systems.