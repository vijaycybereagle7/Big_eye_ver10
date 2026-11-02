"""
Inference Module for Pattern Recognition Models

This module provides unified inference and prediction functionality for:
- Domain Reputation Classifier
- Phishing URL Detector  
- Sender Reputation Predictor

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

# Import all model classes
from .random_forest_domain_reputation import DomainReputationClassifier
from .xgboost_phishing_detection import PhishingURLDetector
from .gradient_boosting_sender_reputation import SenderReputationPredictor


class PatternRecognitionInference:
    """Unified inference interface for all pattern recognition models."""
    
    def __init__(self, models_dir: str = "trained_models"):
        """
        Initialize the Pattern Recognition Inference system.
        
        Args:
            models_dir: Directory containing trained models
        """
        self.models_dir = models_dir
        self.models = {}
        self.model_metadata = {}
        self.is_loaded = False
        
    def load_models(self, model_files: Optional[Dict[str, str]] = None) -> Dict[str, bool]:
        """
        Load trained models from files.
        
        Args:
            model_files: Dictionary mapping model names to file paths. 
                        If None, will auto-discover models in models_dir
            
        Returns:
            Dictionary indicating which models were loaded successfully
        """
        print("Loading trained models...")
        load_status = {}
        
        if model_files is None:
            # Auto-discover model files
            model_files = self._discover_model_files()
        
        # Load domain reputation classifier
        if 'domain' in model_files:
            try:
                self.models['domain'] = DomainReputationClassifier()
                self.models['domain'].load_model(model_files['domain'])
                load_status['domain'] = True
                print(f"✓ Loaded domain reputation model from {model_files['domain']}")
            except Exception as e:
                load_status['domain'] = False
                print(f"✗ Failed to load domain model: {e}")
        
        # Load phishing URL detector
        if 'phishing' in model_files:
            try:
                self.models['phishing'] = PhishingURLDetector()
                self.models['phishing'].load_model(model_files['phishing'])
                load_status['phishing'] = True
                print(f"✓ Loaded phishing detector from {model_files['phishing']}")
            except Exception as e:
                load_status['phishing'] = False
                print(f"✗ Failed to load phishing model: {e}")
        
        # Load sender reputation predictor
        if 'sender' in model_files:
            try:
                self.models['sender'] = SenderReputationPredictor()
                self.models['sender'].load_model(model_files['sender'])
                load_status['sender'] = True
                print(f"✓ Loaded sender reputation model from {model_files['sender']}")
            except Exception as e:
                load_status['sender'] = False
                print(f"✗ Failed to load sender model: {e}")
        
        # Load metadata if available
        self._load_model_metadata()
        
        self.is_loaded = any(load_status.values())
        return load_status
    
    def _discover_model_files(self) -> Dict[str, str]:
        """Auto-discover model files in the models directory."""
        if not os.path.exists(self.models_dir):
            print(f"Models directory {self.models_dir} not found")
            return {}
        
        model_files = {}
        for filename in os.listdir(self.models_dir):
            if filename.endswith('.pkl'):
                if 'domain' in filename:
                    model_files['domain'] = os.path.join(self.models_dir, filename)
                elif 'phishing' in filename:
                    model_files['phishing'] = os.path.join(self.models_dir, filename)
                elif 'sender' in filename:
                    model_files['sender'] = os.path.join(self.models_dir, filename)
        
        return model_files
    
    def _load_model_metadata(self):
        """Load metadata for loaded models."""
        for model_name, model in self.models.items():
            self.model_metadata[model_name] = {
                'model_type': getattr(model, 'model_type', 'unknown'),
                'is_trained': getattr(model, 'is_trained', False),
                'feature_count': len(getattr(model, 'feature_names', [])),
                'last_updated': datetime.now().isoformat()
            }
    
    def predict_domain_reputation(self, domains: List[str], 
                                return_probabilities: bool = False) -> Dict[str, Union[List[str], Dict]]:
        """
        Predict reputation for domains.
        
        Args:
            domains: List of domain strings to analyze
            return_probabilities: Whether to return probability scores
            
        Returns:
            Dictionary containing predictions and optionally probabilities
        """
        if 'domain' not in self.models:
            raise ValueError("Domain reputation model not loaded")
        
        model = self.models['domain']
        predictions = model.predict_reputation(domains)
        
        result = {
            'domains': domains,
            'predictions': predictions,
            'model_info': self.model_metadata.get('domain', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        if return_probabilities and hasattr(model, 'predict_reputation_probabilities'):
            probabilities = model.predict_reputation_probabilities(domains)
            result['probabilities'] = {
                cat: prob.tolist() for cat, prob in zip(model.reputation_categories, probabilities.T)
            }
        
        return result
    
    def detect_phishing_urls(self, urls: List[str], 
                           return_probabilities: bool = True,
                           risk_threshold: float = 0.5) -> Dict[str, Union[List[int], List[str], Dict]]:
        """
        Detect phishing URLs.
        
        Args:
            urls: List of URLs to analyze
            return_probabilities: Whether to return probability scores
            risk_threshold: Threshold for considering URL as phishing
            
        Returns:
            Dictionary containing predictions, risk scores, and classifications
        """
        if 'phishing' not in self.models:
            raise ValueError("Phishing detection model not loaded")
        
        model = self.models['phishing']
        predictions, probabilities = model.detect_phishing(urls)
        
        # Convert binary predictions to labels
        labels = ['Phishing' if pred == 1 else 'Legitimate' for pred in predictions]
        
        # Risk assessment
        risk_scores = probabilities
        risk_levels = []
        for score in risk_scores:
            if score >= 0.8:
                risk_levels.append('Very High')
            elif score >= 0.6:
                risk_levels.append('High')
            elif score >= 0.4:
                risk_levels.append('Medium')
            elif score >= 0.2:
                risk_levels.append('Low')
            else:
                risk_levels.append('Very Low')
        
        result = {
            'urls': urls,
            'predictions': predictions,
            'labels': labels,
            'risk_scores': risk_scores,
            'risk_levels': risk_levels,
            'risk_threshold': risk_threshold,
            'model_info': self.model_metadata.get('phishing', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        if return_probabilities:
            result['phishing_probabilities'] = probabilities
        
        return result
    
    def predict_sender_reputation(self, sender_data: List[Union[str, Dict[str, str]]], 
                                return_probabilities: bool = False) -> Dict[str, Union[List[str], Dict]]:
        """
        Predict reputation for senders.
        
        Args:
            sender_data: List of email addresses or sender metadata dictionaries
            return_probabilities: Whether to return probability scores
            
        Returns:
            Dictionary containing predictions and optionally probabilities
        """
        if 'sender' not in self.models:
            raise ValueError("Sender reputation model not loaded")
        
        model = self.models['sender']
        predictions = model.predict_reputation(sender_data)
        
        result = {
            'sender_data': sender_data,
            'predictions': predictions,
            'model_info': self.model_metadata.get('sender', {}),
            'timestamp': datetime.now().isoformat()
        }
        
        if return_probabilities and hasattr(model, 'predict_reputation_probabilities'):
            probabilities = model.predict_reputation_probabilities(sender_data)
            result['probabilities'] = {
                cat: prob.tolist() for cat, prob in zip(model.reputation_categories, probabilities.T)
            }
        
        return result
    
    def batch_analyze(self, domains: Optional[List[str]] = None,
                     urls: Optional[List[str]] = None,
                     senders: Optional[List[Union[str, Dict[str, str]]]] = None,
                     return_all_probabilities: bool = True) -> Dict[str, Dict]:
        """
        Perform batch analysis on multiple types of inputs.
        
        Args:
            domains: List of domains to analyze
            urls: List of URLs to analyze
            senders: List of senders to analyze
            return_all_probabilities: Whether to return probability scores for all models
            
        Returns:
            Dictionary containing results for all analyzed items
        """
        results = {}
        
        # Analyze domains
        if domains:
            try:
                results['domains'] = self.predict_domain_reputation(
                    domains, return_probabilities=return_all_probabilities
                )
            except Exception as e:
                results['domains'] = {'error': str(e)}
        
        # Analyze URLs
        if urls:
            try:
                results['urls'] = self.detect_phishing_urls(
                    urls, return_probabilities=return_all_probabilities
                )
            except Exception as e:
                results['urls'] = {'error': str(e)}
        
        # Analyze senders
        if senders:
            try:
                results['senders'] = self.predict_sender_reputation(
                    senders, return_probabilities=return_all_probabilities
                )
            except Exception as e:
                results['senders'] = {'error': str(e)}
        
        results['batch_timestamp'] = datetime.now().isoformat()
        return results
    
    def real_time_analyzer(self, domain: Optional[str] = None,
                          url: Optional[str] = None,
                          sender: Optional[Union[str, Dict[str, str]]] = None,
                          return_detailed_analysis: bool = True) -> Dict[str, Any]:
        """
        Real-time analysis for a single item (domain, URL, or sender).
        
        Args:
            domain: Single domain to analyze
            url: Single URL to analyze
            sender: Single sender to analyze
            return_detailed_analysis: Whether to return detailed analysis
            
        Returns:
            Comprehensive analysis results
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'analysis_type': 'real_time',
            'results': {}
        }
        
        # Analyze domain
        if domain:
            try:
                domain_result = self.predict_domain_reputation([domain], return_probabilities=True)
                analysis['results']['domain'] = domain_result
                
                if return_detailed_analysis:
                    analysis['results']['domain']['analysis'] = self._analyze_domain_details(domain, domain_result)
                    
            except Exception as e:
                analysis['results']['domain'] = {'error': str(e)}
        
        # Analyze URL
        if url:
            try:
                url_result = self.detect_phishing_urls([url], return_probabilities=True)
                analysis['results']['url'] = url_result
                
                if return_detailed_analysis:
                    analysis['results']['url']['analysis'] = self._analyze_url_details(url, url_result)
                    
            except Exception as e:
                analysis['results']['url'] = {'error': str(e)}
        
        # Analyze sender
        if sender:
            try:
                sender_result = self.predict_sender_reputation([sender], return_probabilities=True)
                analysis['results']['sender'] = sender_result
                
                if return_detailed_analysis:
                    analysis['results']['sender']['analysis'] = self._analyze_sender_details(sender, sender_result)
                    
            except Exception as e:
                analysis['results']['sender'] = {'error': str(e)}
        
        # Generate overall risk assessment
        if len(analysis['results']) > 1:
            analysis['overall_assessment'] = self._generate_overall_assessment(analysis['results'])
        
        return analysis
    
    def _analyze_domain_details(self, domain: str, result: Dict) -> Dict[str, Any]:
        """Generate detailed analysis for domain."""
        prediction = result['predictions'][0] if result['predictions'] else 'Unknown'
        proba = result.get('probabilities', {})
        
        analysis = {
            'domain': domain,
            'reputation_prediction': prediction,
            'confidence_levels': {},
            'risk_assessment': 'Unknown'
        }
        
        # Analyze confidence levels
        if proba:
            for category, scores in proba.items():
                if isinstance(scores, list) and len(scores) > 0:
                    analysis['confidence_levels'][category] = scores[0]
        
        # Risk assessment
        if prediction in ['Malicious', 'Suspicious']:
            analysis['risk_assessment'] = 'High Risk'
        elif prediction == 'Legitimate':
            analysis['risk_assessment'] = 'Medium Risk'
        elif prediction == 'Trusted':
            analysis['risk_assessment'] = 'Low Risk'
        
        # Recommendations
        recommendations = []
        if prediction in ['Malicious', 'Suspicious']:
            recommendations.append("Avoid using this domain for sensitive operations")
            recommendations.append("Consider additional security checks")
        elif prediction == 'Legitimate':
            recommendations.append("Monitor domain activity for changes")
        else:
            recommendations.append("Domain appears safe for use")
        
        analysis['recommendations'] = recommendations
        return analysis
    
    def _analyze_url_details(self, url: str, result: Dict) -> Dict[str, Any]:
        """Generate detailed analysis for URL."""
        label = result['labels'][0] if result['labels'] else 'Unknown'
        risk_score = result['risk_scores'][0] if result['risk_scores'] else 0
        risk_level = result['risk_levels'][0] if result['risk_levels'] else 'Unknown'
        
        analysis = {
            'url': url,
            'phishing_prediction': label,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'is_suspicious': risk_score > 0.5,
            'recommendations': []
        }
        
        # Generate recommendations
        if risk_score > 0.8:
            analysis['recommendations'].extend([
                "URL is highly likely to be phishing",
                "Do not visit this URL",
                "Report to security team if this is unexpected"
            ])
        elif risk_score > 0.5:
            analysis['recommendations'].extend([
                "URL shows phishing characteristics",
                "Exercise extreme caution",
                "Verify URL through alternative means"
            ])
        elif risk_score > 0.2:
            analysis['recommendations'].append("URL shows some suspicious patterns - verify before visiting")
        else:
            analysis['recommendations'].append("URL appears legitimate")
        
        # Additional checks
        analysis['checks'] = {
            'has_https': url.startswith('https://'),
            'has_query_params': '?' in url,
            'is_shortened': any(shortener in url.lower() for shortener in ['bit.ly', 't.co', 'goo.gl']),
            'domain_matches_expected': True  # Placeholder - would need context
        }
        
        return analysis
    
    def _analyze_sender_details(self, sender: Union[str, Dict[str, str]], result: Dict) -> Dict[str, Any]:
        """Generate detailed analysis for sender."""
        prediction = result['predictions'][0] if result['predictions'] else 'Unknown'
        proba = result.get('probabilities', {})
        
        analysis = {
            'sender': sender,
            'reputation_prediction': prediction,
            'confidence_levels': {},
            'trust_level': 'Unknown'
        }
        
        # Analyze confidence levels
        if proba:
            for category, scores in proba.items():
                if isinstance(scores, list) and len(scores) > 0:
                    analysis['confidence_levels'][category] = scores[0]
        
        # Trust level assessment
        if prediction == 'Trusted':
            analysis['trust_level'] = 'High'
        elif prediction == 'Legitimate':
            analysis['trust_level'] = 'Medium'
        elif prediction == 'Suspicious':
            analysis['trust_level'] = 'Low'
        else:  # Spammer
            analysis['trust_level'] = 'Very Low'
        
        # Recommendations
        recommendations = []
        if prediction == 'Spammer':
            recommendations.extend([
                "Do not trust emails from this sender",
                "Add to blocked senders list",
                "Report as spam"
            ])
        elif prediction == 'Suspicious':
            recommendations.extend([
                "Verify sender identity before responding",
                "Be cautious with attachments and links",
                "Request additional verification if needed"
            ])
        elif prediction == 'Legitimate':
            recommendations.append("Sender appears legitimate but still exercise standard precautions")
        else:
            recommendations.append("Sender can be trusted for communications")
        
        analysis['recommendations'] = recommendations
        return analysis
    
    def _generate_overall_assessment(self, results: Dict) -> Dict[str, Any]:
        """Generate overall risk assessment from multiple analyses."""
        high_risk_count = 0
        total_analyses = len(results)
        risk_scores = []
        
        # Collect risk indicators
        for analysis_type, analysis_result in results.items():
            if 'error' in analysis_result:
                continue
            
            if analysis_type == 'domain':
                prediction = analysis_result.get('predictions', [''])[0]
                if prediction in ['Malicious', 'Suspicious']:
                    high_risk_count += 1
                risk_scores.append(0.8 if prediction in ['Malicious'] else 0.6 if prediction == 'Suspicious' else 0.2)
            
            elif analysis_type == 'url':
                risk_score = analysis_result.get('risk_scores', [0])[0]
                risk_scores.append(risk_score)
                if risk_score > 0.6:
                    high_risk_count += 1
            
            elif analysis_type == 'sender':
                prediction = analysis_result.get('predictions', [''])[0]
                if prediction in ['Spammer', 'Suspicious']:
                    high_risk_count += 1
                risk_scores.append(0.8 if prediction == 'Spammer' else 0.6 if prediction == 'Suspicious' else 0.2)
        
        # Calculate overall risk
        overall_risk_score = np.mean(risk_scores) if risk_scores else 0
        
        if overall_risk_score > 0.7:
            overall_risk = 'Very High'
        elif overall_risk_score > 0.5:
            overall_risk = 'High'
        elif overall_risk_score > 0.3:
            overall_risk = 'Medium'
        else:
            overall_risk = 'Low'
        
        return {
            'overall_risk_score': overall_risk_score,
            'overall_risk_level': overall_risk,
            'high_risk_indicators': high_risk_count,
            'total_analyses': total_analyses,
            'recommendation': self._get_overall_recommendation(overall_risk_score, high_risk_count, total_analyses)
        }
    
    def _get_overall_recommendation(self, risk_score: float, high_risk_count: int, total_count: int) -> str:
        """Get overall recommendation based on risk assessment."""
        if total_count == 0:
            return "No analyses performed"
        
        risk_ratio = high_risk_count / total_count
        
        if risk_ratio > 0.5 or risk_score > 0.7:
            return "High risk detected - avoid interaction and implement security measures"
        elif risk_ratio > 0.3 or risk_score > 0.5:
            return "Moderate risk detected - proceed with caution and additional verification"
        elif risk_ratio > 0.1 or risk_score > 0.3:
            return "Low risk detected - proceed with normal security practices"
        else:
            return "Very low risk - safe to proceed with standard precautions"
    
    def save_inference_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save inference results to file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"inference_results_{timestamp}.json"
        
        filepath = os.path.join(self.models_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        return filepath
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all loaded models."""
        return {
            'models_loaded': list(self.models.keys()),
            'is_ready': self.is_loaded,
            'model_metadata': self.model_metadata,
            'models_directory': self.models_dir
        }


def main():
    """Main function to demonstrate inference usage."""
    print("Pattern Recognition Inference Demo")
    print("="*40)
    
    # Initialize inference system
    inference = PatternRecognitionInference()
    
    # Load models (will auto-discover if available)
    load_status = inference.load_models()
    print(f"Model load status: {load_status}")
    
    if not inference.is_loaded:
        print("No models loaded. Please train models first.")
        return
    
    # Demo real-time analysis
    print("\nReal-time Analysis Demo:")
    
    test_cases = [
        {'domain': 'google.com'},
        {'url': 'https://www.google.com/search?q=test'},
        {'sender': 'ceo@company.com'},
        {'domain': 'malware-server.ru', 'url': 'http://phishing-site.tk/login'},
    ]
    
    for test_case in test_cases:
        print(f"\nAnalyzing: {test_case}")
        result = inference.real_time_analyzer(**test_case)
        print(f"Result: {result['results']}")


if __name__ == "__main__":
    main()