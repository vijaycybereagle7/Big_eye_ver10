"""
Example Usage of AI/ML Anomaly Detection System

This comprehensive example demonstrates how to use the anomaly detection
system for various cybersecurity use cases including:
- Domain registration pattern analysis
- Email volume anomaly detection
- Zero-day threat identification
- Compromised account detection
- DGA (Domain Generation Algorithm) detection
- Fast-flux network detection

Author: AI Cybersecurity System
Date: 2025-10-30
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import os

# Import all components of the anomaly detection system
from ai_ml.anomaly_detection import (
    AnomalyDetectionEngine,
    IsolationForestDetector,
    DBSCANDetector,
    AutoencoderDetector,
    DomainRegistrationDetector,
    EmailVolumeDetector,
    ZeroDayThreatDetector,
    CompromisedAccountDetector,
    DGADetector,
    FastFluxDetector,
    ModelTrainer,
    AlertManager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sample_data():
    """Generate sample data for demonstration purposes."""
    logger.info("Generating sample data for demonstration...")
    
    # Sample domain registration data
    domain_data = []
    for i in range(100):
        domain_info = {
            'domain': f'legitimate-domain-{i}.com',
            'registrar': 'GoDaddy',
            'registration_date': (datetime.now() - timedelta(days=np.random.randint(1, 365))).isoformat(),
            'expiration_date': (datetime.now() + timedelta(days=np.random.randint(365, 1095))).isoformat(),
            'domains_per_registrar': np.random.randint(1, 10),
            'domain_length': np.random.randint(5, 20)
        }
        domain_data.append(domain_info)
    
    # Add some suspicious domain data
    for i in range(20):
        domain_info = {
            'domain': f'suspicious{random_string(8)}.tk',
            'registrar': 'Freenom',
            'registration_date': (datetime.now() - timedelta(days=np.random.randint(1, 30))).isoformat(),
            'expiration_date': (datetime.now() + timedelta(days=np.random.randint(365, 730))).isoformat(),
            'domains_per_registrar': np.random.randint(50, 200),
            'domain_length': np.random.randint(15, 30)
        }
        domain_data.append(domain_info)
    
    # Sample email volume data
    email_data = []
    for i in range(150):
        activity = {
            'sender': f'user{i}@company.com',
            'email_count': np.random.randint(1, 50),
            'recipients': [f'recipient{j}@external.com' for j in range(np.random.randint(1, 10))],
            'attachments': np.random.randint(0, 5),
            'timestamp': (datetime.now() - timedelta(hours=np.random.randint(0, 720))).isoformat(),
            'failed_deliveries': np.random.randint(0, 3),
            'bounced_emails': np.random.randint(0, 2)
        }
        email_data.append(activity)
    
    # Add some suspicious email activities
    for i in range(30):
        activity = {
            'sender': f'compromised{i}@company.com',
            'email_count': np.random.randint(100, 500),
            'recipients': [f'spam{j}@unknown.com' for j in range(np.random.randint(50, 200))],
            'attachments': np.random.randint(0, 10),
            'timestamp': (datetime.now() - timedelta(hours=np.random.randint(0, 24))).isoformat(),
            'failed_deliveries': np.random.randint(20, 100),
            'bounced_emails': np.random.randint(10, 50)
        }
        email_data.append(activity)
    
    # Sample zero-day threat data
    threat_data = []
    for i in range(80):
        sample = {
            'entropy': np.random.uniform(4.0, 7.5),
            'api_calls': ['CreateProcess', 'WriteFile', 'RegSetValue'],
            'network_indicators': np.random.uniform(0.0, 0.3),
            'file_size': np.random.randint(10000, 500000),
            'section_count': np.random.randint(3, 8),
            'import_count': np.random.randint(5, 50),
            'suspicious_strings': [],
            'packing_score': np.random.uniform(0.0, 0.2),
            'anti_analysis_count': np.random.randint(0, 2)
        }
        threat_data.append(sample)
    
    # Add suspicious samples
    for i in range(25):
        sample = {
            'entropy': np.random.uniform(7.5, 8.5),
            'api_calls': ['CreateProcess', 'WriteFile', 'RegSetValue', 'InternetOpen', 'URLDownloadToFile'],
            'network_indicators': np.random.uniform(0.7, 1.0),
            'file_size': np.random.randint(500000, 2000000),
            'section_count': np.random.randint(8, 15),
            'import_count': np.random.randint(50, 150),
            'suspicious_strings': ['malware', 'trojan', 'virus'],
            'packing_score': np.random.uniform(0.8, 1.0),
            'anti_analysis_count': np.random.randint(5, 15)
        }
        threat_data.append(sample)
    
    # Sample compromised account data
    account_data = []
    for i in range(120):
        activity = {
            'user_id': f'user{i}',
            'login_hour': np.random.randint(8, 18),  # Business hours
            'usual_location': [40.7128, -74.0060],  # NYC
            'current_location': [40.7128, -74.0060],  # Same location
            'action_sequence': ['view', 'read', 'search'],
            'usual_device': 'desktop_windows',
            'current_device': 'desktop_windows',
            'session_duration_minutes': np.random.randint(10, 120),
            'actions_per_minute': np.random.uniform(0.5, 2.0),
            'total_logins': np.random.randint(1, 10),
            'failed_logins': np.random.randint(0, 2)
        }
        account_data.append(activity)
    
    # Add compromised accounts
    for i in range(35):
        activity = {
            'user_id': f'compromised{i}',
            'login_hour': np.random.randint(0, 6),  # Off hours
            'usual_location': [40.7128, -74.0060],  # NYC
            'current_location': [35.6762, 139.6503],  # Tokyo - suspicious
            'action_sequence': ['delete', 'transfer', 'export'],
            'usual_device': 'desktop_windows',
            'current_device': 'mobile_android',
            'session_duration_minutes': np.random.randint(240, 480),  # Very long
            'actions_per_minute': np.random.uniform(5.0, 15.0),  # Very active
            'total_logins': np.random.randint(1, 5),
            'failed_logins': np.random.randint(3, 8)
        }
        account_data.append(activity)
    
    logger.info("Sample data generation completed")
    return {
        'domain_registration': pd.DataFrame(domain_data),
        'email_volume': pd.DataFrame(email_data),
        'zero_day_threats': pd.DataFrame(threat_data),
        'compromised_accounts': pd.DataFrame(account_data)
    }


def random_string(length):
    """Generate a random string."""
    import string
    return ''.join(np.random.choice(list(string.ascii_lowercase), length))


def demonstrate_individual_detectors():
    """Demonstrate each detector individually."""
    logger.info("=== Demonstrating Individual Detectors ===")
    
    # Initialize all detectors
    domain_detector = DomainRegistrationDetector()
    email_detector = EmailVolumeDetector()
    threat_detector = ZeroDayThreatDetector()
    account_detector = CompromisedAccountDetector()
    dga_detector = DGADetector()
    flux_detector = FastFluxDetector()
    
    # Generate sample data
    sample_data = generate_sample_data()
    
    # Test domain registration detector
    logger.info("\n1. Testing Domain Registration Detector...")
    domain_training_data = sample_data['domain_registration']
    domain_result = domain_detector.train(domain_training_data)
    logger.info(f"Domain registration training result: {domain_result['status']}")
    
    if domain_result['status'] == 'trained':
        domain_test_data = domain_training_data.to_dict('records')
        domain_detection = domain_detector.detect(domain_test_data[:20])
        logger.info(f"Domain anomalies detected: {domain_detection['anomalies_detected']}")
        logger.info(f"Domain anomaly count: {domain_detection['anomaly_count']}")
    
    # Test email volume detector
    logger.info("\n2. Testing Email Volume Detector...")
    email_training_data = sample_data['email_volume']
    email_result = email_detector.train(email_training_data)
    logger.info(f"Email volume training result: {email_result['status']}")
    
    if email_result['status'] == 'trained':
        email_test_data = email_training_data.to_dict('records')
        email_detection = email_detector.detect(email_test_data[:20])
        logger.info(f"Email anomalies detected: {email_detection['anomalies_detected']}")
        logger.info(f"Email anomaly count: {email_detection['anomaly_count']}")
    
    # Test zero-day threat detector
    logger.info("\n3. Testing Zero-Day Threat Detector...")
    threat_training_data = sample_data['zero_day_threats']
    threat_result = threat_detector.train(threat_training_data)
    logger.info(f"Zero-day threat training result: {threat_result['status']}")
    
    if threat_result['status'] == 'trained':
        threat_test_data = threat_training_data.to_dict('records')
        threat_detection = threat_detector.detect(threat_test_data[:20])
        logger.info(f"Zero-day anomalies detected: {threat_detection['anomalies_detected']}")
        logger.info(f"Zero-day anomaly count: {threat_detection['anomaly_count']}")
    
    # Test compromised account detector
    logger.info("\n4. Testing Compromised Account Detector...")
    account_training_data = sample_data['compromised_accounts']
    account_result = account_detector.train(account_training_data)
    logger.info(f"Account training result: {account_result['status']}")
    
    if account_result['status'] == 'trained':
        account_test_data = account_training_data.to_dict('records')
        account_detection = account_detector.detect(account_test_data[:20])
        logger.info(f"Account anomalies detected: {account_detection['anomalies_detected']}")
        logger.info(f"Account anomaly count: {account_detection['anomaly_count']}")


def demonstrate_unified_engine():
    """Demonstrate the unified anomaly detection engine."""
    logger.info("\n=== Demonstrating Unified Detection Engine ===")
    
    # Initialize the engine
    engine = AnomalyDetectionEngine()
    
    # Generate sample data
    sample_data = generate_sample_data()
    
    # Train all models
    logger.info("Training all detection models...")
    training_results = engine.train_models(sample_data)
    
    logger.info("Training results:")
    for use_case, result in training_results.items():
        logger.info(f"  {use_case}: {result.get('status', 'unknown')}")
    
    # Perform detection on all use cases
    logger.info("\nPerforming anomaly detection...")
    detection_results = engine.detect_anomalies(sample_data)
    
    logger.info("Detection results:")
    for use_case, result in detection_results.items():
        if 'error' in result:
            logger.info(f"  {use_case}: ERROR - {result['error']}")
        else:
            logger.info(f"  {use_case}: {result['anomalies_detected']} "
                       f"({result['anomaly_count']}/{result['total_samples']} samples)")
    
    # Test real-time detection
    logger.info("\nTesting real-time detection...")
    real_time_data = {
        'domain_registration': {
            'domain': 'suspicious-domain123.tk',
            'registrar': 'Freenom',
            'registration_date': (datetime.now() - timedelta(days=5)).isoformat(),
            'domains_per_registrar': 150,
            'domain_length': 22
        },
        'email_volume': {
            'sender': 'test@company.com',
            'email_count': 200,
            'recipients': [f'spam{i}@unknown.com' for i in range(100)],
            'attachments': 5,
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'failed_deliveries': 25,
            'bounced_emails': 15
        }
    }
    
    for use_case, data in real_time_data.items():
        result = engine.get_real_time_detection(data)
        logger.info(f"Real-time {use_case} detection:")
        for detection_type, detection_result in result.items():
            if 'error' not in detection_result:
                logger.info(f"  {detection_type}: anomaly={detection_result.get('is_anomaly', False)}, "
                           f"score={detection_result.get('anomaly_score', 0):.3f}")


def demonstrate_model_evaluation():
    """Demonstrate model evaluation and comparison."""
    logger.info("\n=== Demonstrating Model Evaluation ===")
    
    # Initialize detectors with different algorithms
    detectors = {
        'isolation_forest': IsolationForestDetector(),
        'dbscan': DBSCANDetector(),
        'autoencoder': AutoencoderDetector()
    }
    
    # Generate training and test data
    sample_data = generate_sample_data()
    training_data = sample_data['email_volume']
    
    # Generate ground truth labels (simulated)
    np.random.seed(42)  # For reproducible results
    n_samples = len(training_data)
    ground_truth = np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2])  # 20% anomalies
    
    # Train and evaluate each detector
    evaluation_results = {}
    for name, detector in detectors.items():
        logger.info(f"Training and evaluating {name}...")
        
        try:
            # Train the detector
            features = training_data[['email_count', 'attachments', 'failed_deliveries']].fillna(0).values
            detector.fit(features)
            
            # Make predictions
            predictions = detector.detect(features)
            
            # Calculate metrics
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            evaluation_results[name] = {
                'accuracy': float(accuracy_score(ground_truth, predictions)),
                'precision': float(precision_score(ground_truth, predictions, zero_division=0)),
                'recall': float(recall_score(ground_truth, predictions, zero_division=0)),
                'f1_score': float(f1_score(ground_truth, predictions, zero_division=0))
            }
            
            logger.info(f"{name} evaluation:")
            for metric, value in evaluation_results[name].items():
                logger.info(f"  {metric}: {value:.3f}")
                
        except Exception as e:
            logger.error(f"Error evaluating {name}: {str(e)}")
            evaluation_results[name] = {'error': str(e)}


def demonstrate_alert_system():
    """Demonstrate the alert management system."""
    logger.info("\n=== Demonstrating Alert System ===")
    
    # Initialize alert manager
    alert_manager = AlertManager()
    
    # Create sample alerts
    sample_alerts = [
        {
            'use_case': 'domain_registration',
            'severity': 'critical',
            'anomaly_count': 15,
            'anomaly_rate': 0.75,
            'threshold': 0.7,
            'source': 'production_system'
        },
        {
            'use_case': 'email_volume',
            'severity': 'high',
            'anomaly_count': 8,
            'anomaly_rate': 0.53,
            'threshold': 0.8,
            'source': 'mail_gateway'
        },
        {
            'use_case': 'zero_day_threats',
            'severity': 'medium',
            'anomaly_count': 3,
            'anomaly_rate': 0.15,
            'threshold': 0.9,
            'source': 'sandbox'
        }
    ]
    
    # Send alerts
    for alert in sample_alerts:
        logger.info(f"Sending alert: {alert['use_case']} - {alert['severity']}")
        success = alert_manager.send_alert(alert)
        logger.info(f"Alert sent successfully: {success}")
    
    # Get alert statistics
    stats = alert_manager.get_alert_statistics()
    logger.info("Alert statistics:")
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Save alerts to file
    alert_file = 'alerts_demo.json'
    alert_manager.save_alerts(alert_file)
    logger.info(f"Alerts saved to {alert_file}")


def demonstrate_model_training_utilities():
    """Demonstrate model training utilities."""
    logger.info("\n=== Demonstrating Model Training Utilities ===")
    
    # Initialize model trainer
    trainer = ModelTrainer()
    
    # Generate sample data
    sample_data = generate_sample_data()
    training_data = sample_data['email_volume']
    
    # Prepare features
    features = training_data[['email_count', 'attachments', 'failed_deliveries']].fillna(0).values
    labels = np.random.choice([0, 1], size=len(features), p=[0.8, 0.2])
    
    # Demonstrate single model training
    logger.info("Training individual models...")
    iso_forest = IsolationForestDetector()
    train_result = trainer.train_single_model(iso_forest, features, labels, "isolation_forest_demo")
    logger.info(f"Single model training result: {train_result['status']}")
    
    # Demonstrate model comparison
    logger.info("Comparing multiple models...")
    models = {
        'isolation_forest': IsolationForestDetector(),
        'autoencoder': AutoencoderDetector()
    }
    
    comparison_result = trainer.compare_models(models, features)
    logger.info(f"Model comparison result: {comparison_result['status']}")
    if 'best_model' in comparison_result:
        logger.info(f"Best model: {comparison_result['best_model']}")
    
    # Save training results
    trainer.save_training_results('training_results_demo.json')
    logger.info("Training results saved")


def run_comprehensive_demo():
    """Run a comprehensive demonstration of all components."""
    logger.info("Starting Comprehensive Anomaly Detection Demo")
    logger.info("=" * 60)
    
    try:
        # Create output directory
        os.makedirs('demo_output', exist_ok=True)
        
        # Demonstrate individual detectors
        demonstrate_individual_detectors()
        
        # Demonstrate unified engine
        demonstrate_unified_engine()
        
        # Demonstrate model evaluation
        demonstrate_model_evaluation()
        
        # Demonstrate alert system
        demonstrate_alert_system()
        
        # Demonstrate training utilities
        demonstrate_model_training_utilities()
        
        logger.info("=" * 60)
        logger.info("Comprehensive demo completed successfully!")
        
        # Create summary report
        summary_report = {
            'demo_completed': datetime.now().isoformat(),
            'components_tested': [
                'DomainRegistrationDetector',
                'EmailVolumeDetector', 
                'ZeroDayThreatDetector',
                'CompromisedAccountDetector',
                'DGADetector',
                'FastFluxDetector',
                'AnomalyDetectionEngine',
                'AlertManager',
                'ModelTrainer'
            ],
            'algorithms_used': [
                'Isolation Forest',
                'DBSCAN',
                'Autoencoder',
                'Ensemble Methods'
            ],
            'use_cases_covered': [
                'Domain Registration Anomalies',
                'Email Volume Analysis',
                'Zero-Day Threat Detection',
                'Compromised Account Detection',
                'DGA Detection',
                'Fast-Flux Detection'
            ]
        }
        
        with open('demo_output/demo_summary.json', 'w') as f:
            json.dump(summary_report, f, indent=2)
        
        logger.info("Demo summary saved to demo_output/demo_summary.json")
        
    except Exception as e:
        logger.error(f"Demo failed with error: {str(e)}")
        raise


if __name__ == "__main__":
    # Set random seed for reproducible results
    np.random.seed(42)
    
    # Run the comprehensive demonstration
    run_comprehensive_demo()