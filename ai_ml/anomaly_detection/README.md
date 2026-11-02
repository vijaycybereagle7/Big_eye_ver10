# AI/ML Anomaly Detection for Cybersecurity

A comprehensive anomaly detection system using scikit-learn and TensorFlow for detecting various cybersecurity threats and suspicious activities.

## Overview

This system provides advanced anomaly detection capabilities for cybersecurity use cases, including:

- **Domain Registration Anomaly Detection** - Unusual domain registration patterns
- **Email Volume Analysis** - Abnormal sending volume and suspicious email patterns  
- **Zero-Day Threat Identification** - Behavioral analysis of potential zero-day threats
- **Compromised Account Detection** - Behavioral patterns indicating account compromise
- **DGA Detection** - Domain Generation Algorithm generated domains
- **Fast-Flux Detection** - Fast-flux network infrastructure detection

## Features

### Detection Algorithms
- **Isolation Forest** - Effective for high-dimensional anomaly detection
- **DBSCAN** - Density-based clustering for identifying outliers
- **Autoencoder** - Deep learning approach for complex pattern detection
- **Ensemble Methods** - Combining multiple algorithms for improved accuracy

### Core Components

#### 1. Core Detection Engine (`core/detection_engine.py`)
Main orchestration engine that coordinates different detection algorithms and use case specific detectors.

#### 2. Detection Algorithms (`algorithms/`)
- `isolation_forest_detector.py` - Isolation Forest implementation
- `dbscan_detector.py` - DBSCAN density-based detection
- `autoencoder_detector.py` - TensorFlow-based autoencoder

#### 3. Use Case Detectors (`use_cases/`)
- `domain_registration.py` - Domain registration pattern analysis
- `email_volume.py` - Email activity anomaly detection
- `zero_day_threats.py` - Zero-day threat behavioral analysis
- `compromised_accounts.py` - Account compromise detection
- `dga_detection.py` - Domain Generation Algorithm detection
- `fast_flux.py` - Fast-flux network detection

#### 4. Utility Components (`utils/`)
- `model_trainer.py` - Model training, validation, and comparison utilities
- `alert_manager.py` - Comprehensive alert management and notification system

## Installation

```bash
# Install required dependencies
pip install numpy pandas scikit-learn tensorflow joblib
```

## Quick Start

### Basic Usage

```python
from ai_ml.anomaly_detection import AnomalyDetectionEngine

# Initialize the detection engine
engine = AnomalyDetectionEngine()

# Prepare your data (example for domain registration)
training_data = {
    'domain_registration': pd.DataFrame(domain_data),
    'email_volume': pd.DataFrame(email_data)
}

# Train all models
training_results = engine.train_models(training_data)

# Perform detection
detection_results = engine.detect_anomalies(new_data)

# Real-time detection
result = engine.get_real_time_detection(single_data_point)
```

### Individual Detector Usage

```python
from ai_ml.anomaly_detection import DomainRegistrationDetector

# Initialize domain registration detector
detector = DomainRegistrationDetector()

# Train on domain data
result = detector.train(training_dataframe)

# Detect anomalies
detection_result = detector.detect(domain_data_list)
```

## Configuration

The system supports comprehensive configuration for each component:

```python
config = {
    'isolation_forest': {
        'contamination': 0.1,
        'n_estimators': 100,
        'random_state': 42
    },
    'autoencoder': {
        'encoding_dim': 32,
        'epochs': 100,
        'batch_size': 32
    },
    'domain_registration': {
        'threshold': 0.7,
        'model': 'autoencoder',
        'features': ['registration_age', 'domain_length', 'entropy_score']
    },
    'alerts': {
        'severity_thresholds': {
            'critical': 0.9,
            'high': 0.8,
            'medium': 0.7,
            'low': 0.6
        },
        'notification_channels': ['log', 'console', 'email']
    }
}

engine = AnomalyDetectionEngine(config)
```

## Use Cases

### 1. Domain Registration Anomaly Detection

Detects suspicious domain registration patterns that may indicate:
- Domain Generation Algorithms (DGAs)
- Cybersquatting or typosquatting
- Fast-flux infrastructure setup
- Malicious domain campaigns

```python
domain_data = [
    {
        'domain': 'suspicious123.tk',
        'registrar': 'Freenom',
        'registration_date': '2025-01-15',
        'domains_per_registrar': 150,
        'domain_length': 22
    }
]

detector = DomainRegistrationDetector()
detector.train(training_data)
result = detector.detect(domain_data)
```

### 2. Email Volume Analysis

Identifies abnormal email patterns indicating:
- Compromised email accounts
- Spam campaigns
- Phishing attacks
- Business Email Compromise (BEC)

```python
email_data = [
    {
        'sender': 'user@company.com',
        'email_count': 200,
        'recipients': ['spam1@unknown.com', 'spam2@unknown.com'],
        'attachments': 5,
        'timestamp': '2025-01-15T10:30:00',
        'failed_deliveries': 25
    }
]

detector = EmailVolumeDetector()
result = detector.detect(email_data)
```

### 3. Zero-Day Threat Detection

Analyzes file behavior to identify potential zero-day threats:
- High entropy files
- Suspicious API calls
- Anti-analysis techniques
- Packed malware

```python
threat_data = [
    {
        'entropy': 7.8,
        'api_calls': ['CreateProcess', 'WriteFile', 'InternetOpen'],
        'network_indicators': 0.8,
        'file_size': 1500000,
        'packing_score': 0.9,
        'anti_analysis_count': 8
    }
]

detector = ZeroDayThreatDetector()
result = detector.detect(threat_data)
```

### 4. Compromised Account Detection

Detects account compromise through behavioral analysis:
- Unusual login times
- Geographic anomalies
- Device fingerprint changes
- Suspicious action sequences

```python
account_data = [
    {
        'user_id': 'user123',
        'login_hour': 2,  # 2 AM - unusual
        'usual_location': [40.7128, -74.0060],  # NYC
        'current_location': [35.6762, 139.6503],  # Tokyo
        'action_sequence': ['delete', 'transfer', 'export'],
        'session_duration_minutes': 360,
        'actions_per_minute': 8.5
    }
]

detector = CompromisedAccountDetector()
result = detector.detect(account_data)
```

### 5. DGA Detection

Identifies domains generated by Domain Generation Algorithms:
- High entropy domain names
- Unusual character patterns
- Lack of meaningful n-grams
- Suspicious TLD usage

```python
dga_data = [
    {
        'domain': 'klj3h8x7z9q2m4n.com',
        'char_frequency': 0.85,
        'n_gram_analysis': 0.9,
        'entropy_score': 0.88,
        'vowel_consonant_ratio': 0.3,
        'length_score': 0.7
    }
]

detector = DGADetector()
result = detector.detect(dga_data)
```

### 6. Fast-Flux Detection

Detects fast-flux network infrastructure:
- Rapid IP rotation
- High TTL variance
- Geographic distribution
- Unusual DNS patterns

```python
flux_data = [
    {
        'domain': 'malicious-site.tk',
        'dns_response_times': [1200, 800, 1500, 900],
        'ip_addresses': ['1.2.3.4', '5.6.7.8', '9.10.11.12'],
        'ip_rotation_rate': 5.2,
        'ttl_variance': 7200,
        'ip_geographic_spread': 8
    }
]

detector = FastFluxDetector()
result = detector.detect(flux_data)
```

## Model Training and Evaluation

### Training Models

```python
from ai_ml.anomaly_detection import ModelTrainer

trainer = ModelTrainer()

# Train individual models
result = trainer.train_single_model(model, X, y, "model_name")

# Hyperparameter tuning
param_grid = {
    'n_estimators': [50, 100, 200],
    'contamination': [0.05, 0.1, 0.15]
}
tuned_result = trainer.hyperparameter_tuning(IsolationForestDetector, param_grid, X, y)

# Model comparison
models = {
    'isolation_forest': IsolationForestDetector(),
    'dbscan': DBSCANDetector(),
    'autoencoder': AutoencoderDetector()
}
comparison = trainer.compare_models(models, X, y)
```

### Evaluating Models

```python
# Evaluate trained model
metrics = detector.evaluate(X_test, y_true)

print(f"Accuracy: {metrics['accuracy']:.3f}")
print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1-Score: {metrics['f1_score']:.3f}")
```

## Alert Management

### Setting Up Alerts

```python
from ai_ml.anomaly_detection import AlertManager

alert_config = {
    'severity_thresholds': {
        'critical': 0.9,
        'high': 0.8,
        'medium': 0.7,
        'low': 0.6
    },
    'notification_channels': ['log', 'console', 'email'],
    'email_config': {
        'smtp_server': 'smtp.company.com',
        'from_address': 'alerts@company.com',
        'to_addresses': ['security@company.com']
    }
}

alert_manager = AlertManager(alert_config)

# Send alert
alert = {
    'use_case': 'domain_registration',
    'severity': 'high',
    'anomaly_count': 15,
    'anomaly_rate': 0.75,
    'threshold': 0.7
}

success = alert_manager.send_alert(alert)
```

## Model Persistence

### Saving Models

```python
# Save individual detector
detector.save_model('models/domain_detector.pkl')

# Save all models
engine.save_models('models/')

# Save training results
trainer.save_training_results('training_results.json')

# Save alerts
alert_manager.save_alerts('alerts_history.json')
```

### Loading Models

```python
# Load individual detector
detector.load_model('models/domain_detector.pkl')

# Load all models
engine.load_models('models/')

# Load training results
trainer.load_training_results('training_results.json')
```

## Real-Time Detection

```python
# Get real-time anomaly detection for a single data point
data_point = {
    'domain': 'suspicious-domain.tk',
    'registrar': 'Unknown',
    'registration_date': '2025-01-15',
    'domains_per_registrar': 200
}

result = engine.get_real_time_detection(data_point)

for use_case, detection in result.items():
    if detection['is_anomaly']:
        print(f"Anomaly detected in {use_case}: {detection['severity']}")
        print(f"Anomaly score: {detection['anomaly_score']:.3f}")
```

## Running the Demo

```bash
# Run the comprehensive demonstration
python ai_ml/anomaly_detection/example_usage.py
```

The demo will:
1. Generate sample data for all use cases
2. Train individual detectors
3. Demonstrate the unified detection engine
4. Show model evaluation and comparison
5. Test the alert management system
6. Demonstrate training utilities

## Output

The system generates comprehensive outputs:

### Detection Results
```json
{
    "anomalies_detected": true,
    "anomaly_count": 15,
    "total_samples": 100,
    "anomaly_rate": 0.15,
    "anomaly_indices": [5, 12, 23, 34, 45, ...],
    "anomaly_scores": [0.85, 0.92, 0.78, 0.89, 0.94, ...],
    "pattern_analysis": {
        "dga_indicators": 0.7,
        "fast_flux_indicators": 0.3,
        "cybersquatting_indicators": 0.5
    }
}
```

### Model Information
```json
{
    "model_type": "Autoencoder",
    "is_fitted": true,
    "encoding_dim": 32,
    "epochs_trained": 100,
    "training_samples": 1000,
    "reconstruction_error_mean": 0.025,
    "reconstruction_error_std": 0.012
}
```

### Alert Notifications
```
🚨 ANOMALY DETECTION ALERT 🚨
Use Case: domain_registration
Severity: HIGH
Anomalies: 15
Rate: 15.00%
Time: 2025-01-15T10:30:00
Threshold: 0.70
```

## Architecture

The system follows a modular architecture:

```
ai_ml/anomaly_detection/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── detection_engine.py          # Main orchestration engine
├── algorithms/
│   ├── __init__.py
│   ├── isolation_forest_detector.py
│   ├── dbscan_detector.py
│   └── autoencoder_detector.py
├── use_cases/
│   ├── __init__.py
│   ├── domain_registration.py
│   ├── email_volume.py
│   ├── zero_day_threats.py
│   ├── compromised_accounts.py
│   ├── dga_detection.py
│   └── fast_flux.py
├── utils/
│   ├── __init__.py
│   ├── model_trainer.py
│   └── alert_manager.py
├── example_usage.py                 # Comprehensive demonstration
└── README.md                        # This file
```

## Customization

### Adding New Use Cases

1. Create a new detector class in `use_cases/`
2. Inherit from base detector classes
3. Implement required methods: `train()`, `detect()`
4. Add to the main engine configuration

```python
from ai_ml.anomaly_detection import AutoencoderDetector

class CustomDetector:
    def __init__(self, config):
        self.detector = AutoencoderDetector(config)
        self.threshold = config.get('threshold', 0.7)
    
    def train(self, training_data):
        # Extract features and train
        features = self._extract_features(training_data)
        return self.detector.fit(features)
    
    def detect(self, data):
        # Perform detection
        features = self._extract_features(data)
        return self.detector.detect(features)
```

### Custom Alert Channels

```python
def custom_alert_handler(alert):
    # Custom alert processing
    webhook_url = "https://hooks.slack.com/services/..."
    requests.post(webhook_url, json=alert)
    
    return True

alert_manager.notification_handlers['slack'] = custom_alert_handler
```

## Performance Considerations

### Optimization Tips
1. **Feature Selection** - Use relevant features only
2. **Data Preprocessing** - Proper scaling and normalization
3. **Batch Processing** - Process data in batches for efficiency
4. **Model Selection** - Choose appropriate algorithms for data size
5. **Threshold Tuning** - Optimize thresholds for your use case

### Memory Usage
- Autoencoder models can be memory intensive for large datasets
- DBSCAN may require significant memory for high-dimensional data
- Consider dimensionality reduction for large feature spaces

### Real-time Performance
- Pre-trained models enable fast real-time detection
- Feature extraction should be optimized for speed
- Consider caching for repeated detections

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Implement your changes with tests
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:

- Create an issue in the repository
- Contact the development team
- Check the documentation and examples

## Changelog

### Version 1.0.0 (2025-10-30)
- Initial release
- Core anomaly detection algorithms implemented
- All 6 use case detectors completed
- Comprehensive alert management system
- Model training and evaluation utilities
- Real-time detection capabilities
- Complete documentation and examples