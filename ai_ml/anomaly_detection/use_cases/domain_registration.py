"""
Domain Registration Anomaly Detector

Detects unusual domain registration patterns that may indicate:
- Domain generation algorithms (DGAs)
- Fast-flux networks
- Cybersquatting or typosquatting
- Malicious infrastructure setup
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import re
from collections import Counter
import logging
from datetime import datetime, timedelta

from ..algorithms.autoencoder_detector_simple import AutoencoderDetector
from ..algorithms.isolation_forest_detector import IsolationForestDetector
from ..algorithms.dbscan_detector import DBSCANDetector

logger = logging.getLogger(__name__)


class DomainRegistrationDetector:
    """
    Detector for unusual domain registration patterns.
    
    Analyzes domain registration characteristics to identify potentially
    malicious or suspicious domains.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the domain registration detector.
        
        Args:
            config: Configuration dictionary with detector parameters
        """
        self.config = config or self._get_default_config()
        
        # Initialize the underlying detection algorithm
        model_type = self.config.get('model', 'autoencoder')
        if model_type == 'autoencoder':
            self.detector = AutoencoderDetector(self.config.get('autoencoder_config', {}))
        elif model_type == 'isolation_forest':
            self.detector = IsolationForestDetector(self.config.get('isolation_forest_config', {}))
        elif model_type == 'dbscan':
            self.detector = DBSCANDetector(self.config.get('dbscan_config', {}))
        else:
            self.detector = AutoencoderDetector(self.config.get('autoencoder_config', {}))
        
        self.threshold = self.config.get('threshold', 0.7)
        self.is_fitted = False
        
        logger.info("DomainRegistrationDetector initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for domain registration detection."""
        return {
            'threshold': 0.7,
            'model': 'autoencoder',
            'features': [
                'registration_age',
                'domains_per_registrar',
                'domain_length',
                'char_variance',
                'vowel_consonant_ratio',
                'digit_ratio',
                'special_char_ratio',
                'entropy_score',
                'tld_frequency',
                'subdomain_count'
            ],
            'autoencoder_config': {
                'encoding_dim': 16,
                'epochs': 50,
                'batch_size': 16,
                'threshold_percentile': 95
            },
            'isolation_forest_config': {
                'contamination': 0.1,
                'n_estimators': 100
            },
            'dbscan_config': {
                'eps': 0.5,
                'min_samples': 5
            }
        }
    
    def _extract_domain_features(self, domain_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from domain registration data.
        
        Args:
            domain_data: Dictionary containing domain information
            
        Returns:
            Feature vector as numpy array
        """
        try:
            features = []
            
            # Extract basic domain information
            domain = domain_data.get('domain', '').lower()
            registrar = domain_data.get('registrar', '')
            registration_date = domain_data.get('registration_date')
            expiration_date = domain_data.get('expiration_date')
            
            # 1. Registration Age (days since registration)
            if registration_date:
                try:
                    reg_date = pd.to_datetime(registration_date)
                    age_days = (datetime.now() - reg_date).days
                    features.append(min(age_days, 3650))  # Cap at 10 years
                except:
                    features.append(0)
            else:
                features.append(0)
            
            # 2. Domains per registrar (simulated - would come from external data)
            domains_per_registrar = domain_data.get('domains_per_registrar', 1)
            features.append(min(domains_per_registrar, 1000))  # Cap at 1000
            
            # 3. Domain length
            domain_length = len(domain)
            features.append(domain_length)
            
            # 4. Character variance (unique characters ratio)
            unique_chars = len(set(domain))
            char_variance = unique_chars / max(domain_length, 1)
            features.append(char_variance)
            
            # 5. Vowel-consonant ratio
            vowels = sum(1 for c in domain if c in 'aeiou')
            consonants = sum(1 for c in domain if c.isalpha() and c not in 'aeiou')
            vowel_consonant_ratio = vowels / max(consonants, 1)
            features.append(vowel_consonant_ratio)
            
            # 6. Digit ratio
            digits = sum(1 for c in domain if c.isdigit())
            digit_ratio = digits / max(domain_length, 1)
            features.append(digit_ratio)
            
            # 7. Special character ratio
            special_chars = sum(1 for c in domain if c in '._-')
            special_char_ratio = special_chars / max(domain_length, 1)
            features.append(special_char_ratio)
            
            # 8. Entropy score
            char_counts = Counter(domain)
            entropy = -sum((count/len(domain)) * np.log2(count/len(domain)) 
                          for count in char_counts.values() if count > 0)
            features.append(entropy)
            
            # 9. TLD frequency (common TLDs get lower scores)
            tlds = ['com', 'org', 'net', 'edu', 'gov', 'mil']
            tld = domain.split('.')[-1] if '.' in domain else ''
            tld_score = 0.2 if tld in tlds else 1.0
            features.append(tld_score)
            
            # 10. Subdomain count
            subdomain_count = domain.count('.') - 1  # Exclude TLD
            features.append(max(subdomain_count, 0))
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error extracting domain features: {str(e)}")
            # Return zeros as fallback
            return np.zeros(len(self.config['features']))
    
    def _detect_typosquatting(self, domain: str, existing_domains: List[str]) -> float:
        """
        Detect potential typosquatting by analyzing similarity to legitimate domains.
        
        Args:
            domain: Domain to check
            existing_domains: List of legitimate domains to compare against
            
        Returns:
            Typosquatting risk score (0-1, higher = more risky)
        """
        try:
            if not existing_domains:
                return 0.0
            
            max_similarity = 0.0
            domain_clean = domain.replace('www.', '').lower()
            
            for legit_domain in existing_domains:
                legit_clean = legit_domain.replace('www.', '').lower()
                
                # Calculate Levenshtein distance
                distance = self._levenshtein_distance(domain_clean, legit_clean)
                max_len = max(len(domain_clean), len(legit_clean))
                
                if max_len > 0:
                    similarity = 1 - (distance / max_len)
                    max_similarity = max(max_similarity, similarity)
            
            # High similarity (but not exact match) suggests typosquatting
            if max_similarity > 0.8 and max_similarity < 0.95:
                return max_similarity
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Error detecting typosquatting: {str(e)}")
            return 0.0
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _analyze_domain_patterns(self, domains: List[str]) -> Dict[str, float]:
        """
        Analyze domain patterns to identify suspicious characteristics.
        
        Args:
            domains: List of domains to analyze
            
        Returns:
            Dictionary of pattern analysis results
        """
        try:
            analysis = {
                'dga_indicators': 0.0,
                'fast_flux_indicators': 0.0,
                'cybersquatting_indicators': 0.0
            }
            
            if not domains:
                return analysis
            
            # Analyze DGA-like patterns
            dga_score = self._analyze_dga_patterns(domains)
            analysis['dga_indicators'] = dga_score
            
            # Analyze fast-flux patterns
            fast_flux_score = self._analyze_fast_flux_patterns(domains)
            analysis['fast_flux_indicators'] = fast_flux_score
            
            # Analyze cybersquatting patterns
            cybersquatting_score = self._analyze_cybersquatting_patterns(domains)
            analysis['cybersquatting_indicators'] = cybersquatting_score
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing domain patterns: {str(e)}")
            return {
                'dga_indicators': 0.0,
                'fast_flux_indicators': 0.0,
                'cybersquatting_indicators': 0.0
            }
    
    def _analyze_dga_patterns(self, domains: List[str]) -> float:
        """Analyze domains for DGA-like characteristics."""
        try:
            suspicious_patterns = 0
            total_domains = len(domains)
            
            for domain in domains:
                domain_clean = domain.split('.')[0].lower()
                
                # Check for high entropy (random-like domain names)
                char_counts = Counter(domain_clean)
                if len(char_counts) / max(len(domain_clean), 1) > 0.8:
                    suspicious_patterns += 1
                
                # Check for unusual character distributions
                vowel_ratio = sum(1 for c in domain_clean if c in 'aeiou') / max(len(domain_clean), 1)
                if vowel_ratio < 0.2 or vowel_ratio > 0.6:
                    suspicious_patterns += 1
                
                # Check for mixed alphanumeric patterns
                if re.search(r'[a-zA-Z]*\d+[a-zA-Z]*', domain_clean) and len(domain_clean) > 5:
                    suspicious_patterns += 1
            
            return min(suspicious_patterns / max(total_domains, 1), 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing DGA patterns: {str(e)}")
            return 0.0
    
    def _analyze_fast_flux_patterns(self, domains: List[str]) -> float:
        """Analyze domains for fast-flux characteristics."""
        try:
            # Fast flux domains often have many subdomains and rapid changes
            suspicious_score = 0.0
            
            total_domains = len(domains)
            multi_subdomain_count = 0
            short_ttl_domains = 0
            
            for domain in domains:
                # Count subdomains
                subdomain_count = domain.count('.') - 1
                if subdomain_count > 2:  # More than 2 levels suggests fast flux
                    multi_subdomain_count += 1
                
                # Check for suspicious TLD patterns
                tld = domain.split('.')[-1].lower()
                if tld in ['tk', 'ml', 'cf', 'ga']:  # Free TLDs often used in fast flux
                    suspicious_score += 0.2
            
            # Normalize scores
            subdomain_score = multi_subdomain_count / max(total_domains, 1)
            suspicious_score = min(suspicious_score + subdomain_score, 1.0)
            
            return suspicious_score
            
        except Exception as e:
            logger.error(f"Error analyzing fast flux patterns: {str(e)}")
            return 0.0
    
    def _analyze_cybersquatting_patterns(self, domains: List[str]) -> float:
        """Analyze domains for cybersquatting characteristics."""
        try:
            # Cybersquatting involves registering domains similar to legitimate brands
            suspicious_score = 0.0
            
            # Common brand patterns to watch for
            brand_patterns = [
                'google', 'facebook', 'amazon', 'microsoft', 'apple',
                'paypal', 'ebay', 'twitter', 'instagram', 'youtube'
            ]
            
            for domain in domains:
                domain_clean = domain.split('.')[0].lower()
                
                # Check for brand name variations
                for brand in brand_patterns:
                    if brand in domain_clean and domain_clean != brand:
                        # Check for additional characters (typical of typosquatting)
                        if len(domain_clean) > len(brand) + 3:
                            suspicious_score += 0.3
                        break
            
            # Check for hyphenated domains (common in cybersquatting)
            if '-' in domain:
                suspicious_score += 0.1
            
            return min(suspicious_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error analyzing cybersquatting patterns: {str(e)}")
            return 0.0
    
    def train(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the domain registration detector.
        
        Args:
            training_data: DataFrame containing domain registration data
            
        Returns:
            Training results and metrics
        """
        try:
            logger.info("Training domain registration detector...")
            
            # Extract features from training data
            feature_matrix = []
            for _, row in training_data.iterrows():
                features = self._extract_domain_features(row.to_dict())
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Train the underlying detector
            self.detector.fit(X)
            self.is_fitted = True
            
            # Get model information
            model_info = self.detector.get_model_info()
            
            logger.info("Domain registration detector training completed")
            return {
                'status': 'trained',
                'model_type': self.config['model'],
                'features_used': self.config['features'],
                'training_samples': len(X),
                'feature_dimensions': X.shape[1],
                'model_info': model_info
            }
            
        except Exception as e:
            logger.error(f"Error training domain registration detector: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def detect(self, domain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect anomalies in domain registration patterns.
        
        Args:
            domain_data: List of domain registration data
            
        Returns:
            Detection results including anomaly scores and details
        """
        try:
            if not self.is_fitted:
                raise ValueError("Detector must be trained before detection")
            
            # Extract features for all domains
            feature_matrix = []
            for domain_info in domain_data:
                features = self._extract_domain_features(domain_info)
                feature_matrix.append(features)
            
            X = np.array(feature_matrix)
            
            # Perform detection using the underlying algorithm
            if hasattr(self.detector, 'get_anomaly_scores'):
                anomaly_scores = self.detector.get_anomaly_scores(X)
                anomaly_indices = np.where(anomaly_scores > self.threshold)[0].tolist()
                anomalies_detected = len(anomaly_indices) > 0
            else:
                # Fallback for detectors without get_anomaly_scores
                anomaly_indices = []
                anomalies_detected = False
            
            # Analyze domain patterns
            domains = [data.get('domain', '') for data in domain_data]
            pattern_analysis = self._analyze_domain_patterns(domains)
            
            # Compile results
            result = {
                'anomalies_detected': anomalies_detected,
                'anomaly_count': len(anomaly_indices),
                'total_domains': len(domain_data),
                'anomaly_rate': len(anomaly_indices) / len(domain_data) if domain_data else 0.0,
                'anomaly_indices': anomaly_indices,
                'anomaly_scores': anomaly_scores.tolist() if hasattr(anomaly_scores, 'tolist') else [],
                'threshold': self.threshold,
                'pattern_analysis': pattern_analysis,
                'detected_domains': [
                    domain_data[i] for i in anomaly_indices if i < len(domain_data)
                ] if anomaly_indices else []
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting domain anomalies: {str(e)}")
            return {
                'anomalies_detected': False,
                'error': str(e),
                'anomaly_count': 0,
                'total_domains': len(domain_data) if domain_data else 0
            }
    
    def analyze_single_domain(self, domain_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single domain for suspicious characteristics.
        
        Args:
            domain_info: Dictionary containing domain information
            
        Returns:
            Analysis results for the single domain
        """
        try:
            # Extract features
            features = self._extract_domain_features(domain_info)
            features = features.reshape(1, -1)
            
            # Get anomaly score
            if hasattr(self.detector, 'get_anomaly_score'):
                anomaly_score = self.detector.get_anomaly_score(features[0])
            else:
                anomaly_score = 0.0
            
            # Analyze patterns
            domain = domain_info.get('domain', '')
            pattern_analysis = self._analyze_domain_patterns([domain])
            
            # Determine if it's anomalous
            is_anomaly = anomaly_score > self.threshold
            
            result = {
                'domain': domain,
                'is_anomaly': is_anomaly,
                'anomaly_score': float(anomaly_score),
                'threshold': self.threshold,
                'features': {
                    name: float(value) for name, value in zip(
                        self.config['features'], features[0]
                    )
                },
                'pattern_analysis': pattern_analysis,
                'risk_assessment': self._calculate_risk_level(anomaly_score, pattern_analysis)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing single domain: {str(e)}")
            return {
                'domain': domain_info.get('domain', 'unknown'),
                'is_anomaly': False,
                'error': str(e)
            }
    
    def _calculate_risk_level(self, anomaly_score: float, pattern_analysis: Dict[str, float]) -> str:
        """Calculate overall risk level based on anomaly score and patterns."""
        try:
            # Combine anomaly score with pattern indicators
            pattern_risk = max(pattern_analysis.values())
            combined_score = max(anomaly_score, pattern_risk)
            
            if combined_score >= 0.9:
                return 'critical'
            elif combined_score >= 0.7:
                return 'high'
            elif combined_score >= 0.5:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Error calculating risk level: {str(e)}")
            return 'unknown'
    
    def save_model(self, filepath: str):
        """Save the trained model."""
        try:
            self.detector.save_model(filepath)
            logger.info(f"Domain registration detector saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving domain registration detector: {str(e)}")
            raise
    
    def load_model(self, filepath: str):
        """Load a trained model."""
        try:
            self.detector.load_model(filepath)
            self.is_fitted = True
            logger.info(f"Domain registration detector loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading domain registration detector: {str(e)}")
            raise