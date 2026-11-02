"""
Test script for AI/ML Anomaly Detection System

Simple test to verify that all components are working correctly.
"""

import numpy as np
import pandas as pd
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")
    
    try:
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
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {str(e)}")
        return False

def test_basic_functionality():
    """Test basic functionality of core components."""
    print("\nTesting basic functionality...")
    
    try:
        # Test Isolation Forest
        from ai_ml.anomaly_detection import IsolationForestDetector
        
        # Generate sample data
        np.random.seed(42)
        X = np.random.randn(100, 5)
        
        # Add some anomalies
        X[80:90] = np.random.randn(10, 5) * 3
        
        # Test detector
        detector = IsolationForestDetector()
        detector.fit(X)
        scores = detector.get_anomaly_scores(X)
        
        print(f"✅ Isolation Forest test passed - found {np.sum(scores > 0.5)} anomalies")
        
        # Test Autoencoder
        from ai_ml.anomaly_detection import AutoencoderDetector
        
        autoencoder = AutoencoderDetector({'epochs': 10})  # Quick test
        autoencoder.fit(X)
        ae_scores = autoencoder.get_anomaly_scores(X)
        
        print(f"✅ Autoencoder test passed - found {np.sum(ae_scores > 0.5)} anomalies")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {str(e)}")
        return False

def test_domain_registration():
    """Test domain registration detector."""
    print("\nTesting domain registration detector...")
    
    try:
        from ai_ml.anomaly_detection import DomainRegistrationDetector
        
        # Create sample data
        domain_data = pd.DataFrame([
            {
                'domain': 'legitimate-site.com',
                'registrar': 'GoDaddy',
                'registration_date': '2024-01-01',
                'domains_per_registrar': 5,
                'domain_length': 15
            },
            {
                'domain': 'suspicious123.tk',
                'registrar': 'Freenom',
                'registration_date': '2025-01-15',
                'domains_per_registrar': 150,
                'domain_length': 25
            }
        ])
        
        detector = DomainRegistrationDetector()
        result = detector.train(domain_data)
        
        print(f"✅ Domain registration detector test passed - status: {result['status']}")
        
        # Test detection
        test_data = domain_data.to_dict('records')
        detection = detector.detect(test_data)
        
        print(f"✅ Detection test passed - anomalies detected: {detection['anomalies_detected']}")
        
        return True
    except Exception as e:
        print(f"❌ Domain registration test failed: {str(e)}")
        return False

def test_email_volume():
    """Test email volume detector."""
    print("\nTesting email volume detector...")
    
    try:
        from ai_ml.anomaly_detection import EmailVolumeDetector
        
        # Create sample data
        email_data = pd.DataFrame([
            {
                'sender': 'user@company.com',
                'email_count': 10,
                'recipients': ['colleague@company.com'],
                'attachments': 1,
                'timestamp': '2025-01-15T10:00:00',
                'failed_deliveries': 0,
                'bounced_emails': 0
            },
            {
                'sender': 'spammer@unknown.com',
                'email_count': 200,
                'recipients': [f'spam{i}@unknown.com' for i in range(100)],
                'attachments': 5,
                'timestamp': '2025-01-15T02:00:00',
                'failed_deliveries': 25,
                'bounced_emails': 15
            }
        ])
        
        detector = EmailVolumeDetector()
        result = detector.train(email_data)
        
        print(f"✅ Email volume detector test passed - status: {result['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Email volume test failed: {str(e)}")
        return False

def test_alert_system():
    """Test alert management system."""
    print("\nTesting alert system...")
    
    try:
        from ai_ml.anomaly_detection import AlertManager
        
        alert_manager = AlertManager()
        
        # Create test alert
        alert = {
            'use_case': 'test_detection',
            'severity': 'high',
            'anomaly_count': 5,
            'anomaly_rate': 0.25,
            'threshold': 0.7,
            'source': 'test_system'
        }
        
        # Send alert
        success = alert_manager.send_alert(alert)
        
        # Get statistics
        stats = alert_manager.get_alert_statistics()
        
        print(f"✅ Alert system test passed - alerts sent: {success}")
        print(f"   Total alerts: {stats['total_alerts']}")
        
        return True
    except Exception as e:
        print(f"❌ Alert system test failed: {str(e)}")
        return False

def test_unified_engine():
    """Test unified detection engine."""
    print("\nTesting unified detection engine...")
    
    try:
        from ai_ml.anomaly_detection import AnomalyDetectionEngine
        
        # Initialize engine
        engine = AnomalyDetectionEngine()
        
        # Create minimal test data
        test_data = {
            'domain_registration': pd.DataFrame([
                {
                    'domain': 'test.com',
                    'registrar': 'TestReg',
                    'registration_date': '2024-01-01',
                    'domains_per_registrar': 1,
                    'domain_length': 8
                }
            ])
        }
        
        # Train engine
        training_results = engine.train_models(test_data)
        
        print(f"✅ Unified engine test passed - training completed")
        
        # Test detection
        detection_results = engine.detect_anomalies(test_data)
        
        print(f"✅ Detection test passed - {len(detection_results)} use cases processed")
        
        return True
    except Exception as e:
        print(f"❌ Unified engine test failed: {str(e)}")
        return False

def run_all_tests():
    """Run all tests."""
    print("🧪 Starting AI/ML Anomaly Detection System Tests")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_functionality,
        test_domain_registration,
        test_email_volume,
        test_alert_system,
        test_unified_engine
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🚀 System is ready for anomaly detection!")
        print("📖 See README.md for usage examples and documentation.")
    else:
        print("\n🔧 Please fix the failing tests before using the system.")
        sys.exit(1)