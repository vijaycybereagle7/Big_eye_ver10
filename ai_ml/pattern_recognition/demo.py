"""
Pattern Recognition & Classification Models - Demo Script

This script demonstrates the complete functionality of the pattern recognition
system including training, evaluation, and inference.

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pattern_recognition import (
        PatternRecognitionPipeline,
        PatternRecognitionInference,
        extract_all_features,
        ModelEvaluator
    )
    print("✓ Successfully imported pattern recognition modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure all dependencies are installed:")
    print("pip install numpy pandas scikit-learn xgboost matplotlib seaborn joblib")
    sys.exit(1)


def demo_feature_extraction():
    """Demonstrate feature extraction functionality."""
    print("\n" + "="*60)
    print("FEATURE EXTRACTION DEMO")
    print("="*60)
    
    # Domain feature extraction
    domain = "google.com"
    domain_features = extract_all_features(domain, 'domain')
    print(f"Domain features for '{domain}':")
    for feature, value in list(domain_features.items())[:10]:  # Show first 10 features
        print(f"  {feature}: {value}")
    print(f"  ... and {len(domain_features)-10} more features")
    
    # URL feature extraction
    url = "https://www.google.com/search?q=test&param=value"
    url_features = extract_all_features(url, 'url')
    print(f"\nURL features for '{url[:50]}...':")
    for feature, value in list(url_features.items())[:10]:  # Show first 10 features
        print(f"  {feature}: {value}")
    print(f"  ... and {len(url_features)-10} more features")
    
    # Email feature extraction
    email = "user.name+tag@gmail.com"
    email_features = extract_all_features(email, 'email')
    print(f"\nEmail features for '{email}':")
    for feature, value in list(email_features.items())[:10]:  # Show first 10 features
        print(f"  {feature}: {value}")
    print(f"  ... and {len(email_features)-10} more features")


def demo_training_pipeline():
    """Demonstrate training pipeline with small dataset."""
    print("\n" + "="*60)
    print("TRAINING PIPELINE DEMO")
    print("="*60)
    
    try:
        # Initialize pipeline
        pipeline = PatternRecognitionPipeline(
            models_dir="demo_trained_models",
            results_dir="demo_results"
        )
        print("✓ Initialized training pipeline")
        
        # Run complete pipeline with small dataset for demo
        print("Running complete training pipeline (this may take a few minutes)...")
        results = pipeline.run_complete_pipeline(
            n_samples={
                'domain': 500,     # Small dataset for demo
                'phishing': 800,   # Small dataset for demo
                'sender': 600      # Small dataset for demo
            },
            hyperparameter_tuning=False,  # Disable for faster demo
            save_models=True,
            generate_plots=False  # Disable plots for demo
        )
        
        print("✓ Training pipeline completed successfully!")
        print(f"Models trained: {list(results['models'].keys())}")
        
        # Show training results summary
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
        
        return pipeline
        
    except Exception as e:
        print(f"✗ Training pipeline failed: {e}")
        return None


def demo_inference(pipeline=None):
    """Demonstrate inference functionality."""
    print("\n" + "="*60)
    print("INFERENCE DEMO")
    print("="*60)
    
    try:
        # Initialize inference system
        inference = PatternRecognitionInference(models_dir="demo_trained_models")
        print("✓ Initialized inference system")
        
        # Load models
        load_status = inference.load_models()
        print(f"Model load status: {load_status}")
        
        if not inference.is_loaded:
            print("⚠ No trained models found. Skipping inference demo.")
            return
        
        # Test cases for analysis
        test_cases = [
            {
                'name': 'Legitimate Google Domain',
                'domain': 'google.com',
                'url': 'https://www.google.com/search?q=test',
                'sender': 'support@google.com'
            },
            {
                'name': 'Suspicious Domain Pattern',
                'domain': 'login-secure-update.tk',
                'url': 'http://login-secure-update.tk/verify',
                'sender': 'noreply@suspicious-domain.tk'
            },
            {
                'name': 'Malicious Pattern',
                'domain': 'malware-server.ru',
                'url': 'http://phishing-site.tk/login',
                'sender': 'viagra@spam-server.ru'
            }
        ]
        
        # Analyze each test case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['name']} ---")
            
            result = inference.real_time_analyzer(
                domain=test_case['domain'],
                url=test_case['url'],
                sender=test_case['sender']
            )
            
            # Display results
            results = result['results']
            
            if 'domain' in results and 'error' not in results['domain']:
                domain_pred = results['domain']['predictions'][0]
                print(f"Domain Reputation: {domain_pred}")
            
            if 'url' in results and 'error' not in results['url']:
                url_label = results['url']['labels'][0]
                url_risk = results['url']['risk_levels'][0]
                print(f"URL Analysis: {url_label} (Risk: {url_risk})")
            
            if 'sender' in results and 'error' not in results['sender']:
                sender_pred = results['sender']['predictions'][0]
                print(f"Sender Reputation: {sender_pred}")
            
            # Overall assessment
            if 'overall_assessment' in result:
                overall = result['overall_assessment']
                print(f"Overall Risk: {overall['overall_risk_level']}")
                print(f"Recommendation: {overall['recommendation']}")
        
        # Batch analysis demo
        print(f"\n--- Batch Analysis Demo ---")
        batch_results = inference.batch_analyze(
            domains=['google.com', 'malware-site.ru'],
            urls=['https://google.com', 'http://phishing-site.tk'],
            senders=['user@company.com', 'spam@scam.ru'],
            return_all_probabilities=True
        )
        
        print("✓ Batch analysis completed")
        
        return inference
        
    except Exception as e:
        print(f"✗ Inference demo failed: {e}")
        return None


def demo_model_evaluation():
    """Demonstrate model evaluation capabilities."""
    print("\n" + "="*60)
    print("MODEL EVALUATION DEMO")
    print("="*60)
    
    try:
        from sklearn.datasets import make_classification
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        # Generate sample classification data
        X, y = make_classification(
            n_samples=1000, 
            n_features=20, 
            n_classes=3, 
            random_state=42,
            n_redundant=0,
            n_informative=15
        )
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)
        
        # Evaluate model
        evaluator = ModelEvaluator("Demo Random Forest", "classification")
        results = evaluator.evaluate_classification_model(
            y_test, y_pred, y_pred_proba,
            class_names=['Class A', 'Class B', 'Class C']
        )
        
        print("✓ Model evaluation completed!")
        print("Evaluation Results:")
        for metric, value in results.items():
            print(f"  {metric}: {value:.4f}")
        
        # Generate classification report
        report = evaluator.generate_classification_report(
            y_test, y_pred,
            class_names=['Class A', 'Class B', 'Class C']
        )
        
        print("\nClassification Report:")
        print(report)
        
        return evaluator
        
    except Exception as e:
        print(f"✗ Model evaluation demo failed: {e}")
        return None


def main():
    """Main demo function."""
    print("Pattern Recognition & Classification Models - Complete Demo")
    print("=" * 70)
    print("This demo showcases all major functionality of the pattern recognition system.")
    print("Note: Training uses small datasets for demonstration purposes.")
    
    # Demo 1: Feature Extraction
    demo_feature_extraction()
    
    # Demo 2: Model Training (may take time)
    print("\n" + "="*70)
    print("NOTE: Training demo uses small datasets and may take 1-2 minutes")
    response = input("Continue with training demo? (y/n): ").lower().strip()
    if response == 'y':
        pipeline = demo_training_pipeline()
        
        # Demo 3: Inference
        if pipeline:
            demo_inference(pipeline)
    else:
        print("Skipping training demo.")
    
    # Demo 4: Model Evaluation
    demo_model_evaluation()
    
    print("\n" + "="*70)
    print("DEMO COMPLETED!")
    print("="*70)
    print("\nTo use the pattern recognition system in your own code:")
    print("1. Import the modules: from pattern_recognition import ...")
    print("2. Initialize pipeline/inference objects")
    print("3. Train models or load pre-trained models")
    print("4. Use prediction/inference methods")
    print("\nFor detailed documentation, see README.md")


if __name__ == "__main__":
    main()