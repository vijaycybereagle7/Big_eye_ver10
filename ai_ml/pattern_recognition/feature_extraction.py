"""
Feature Extraction Module for Pattern Recognition Models

This module provides comprehensive feature extraction functions for:
- Domain reputation scoring
- Phishing URL detection  
- Sender reputation prediction

Author: AI-ML Pattern Recognition System
Date: 2025-10-30
"""

import re
import urllib.parse
from typing import Dict, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import hashlib
import socket
import whois
from urllib.parse import urlparse
import warnings
warnings.filterwarnings('ignore')


class DomainFeatureExtractor:
    """Extract features from domain information for reputation scoring."""
    
    @staticmethod
    def extract_basic_domain_features(domain: str) -> Dict[str, float]:
        """Extract basic domain-based features.
        
        Args:
            domain: Domain string to analyze
            
        Returns:
            Dictionary of basic domain features
        """
        features = {}
        
        # Domain length
        features['domain_length'] = len(domain)
        
        # Number of subdomains
        subdomain_count = domain.count('.') if '.' in domain else 0
        features['subdomain_count'] = subdomain_count
        
        # Contains numbers
        features['has_numbers'] = 1 if any(c.isdigit() for c in domain) else 0
        
        # Contains hyphens
        features['has_hyphens'] = 1 if '-' in domain else 0
        
        # Contains mixed case
        features['has_mixed_case'] = 1 if any(c.isupper() for c in domain) and any(c.islower() for c in domain) else 0
        
        # Suspicious keywords count
        suspicious_keywords = ['admin', 'login', 'secure', 'verify', 'update', 'support', 'help']
        features['suspicious_keywords_count'] = sum(1 for keyword in suspicious_keywords if keyword in domain.lower())
        
        # Character diversity
        unique_chars = len(set(domain.lower()))
        features['char_diversity'] = unique_chars / len(domain) if len(domain) > 0 else 0
        
        # TLD information
        tld = domain.split('.')[-1] if '.' in domain else ''
        features['is_common_tld'] = 1 if tld.lower() in ['com', 'org', 'net', 'edu', 'gov'] else 0
        
        return features
    
    @staticmethod
    def extract_registration_features(domain: str) -> Dict[str, float]:
        """Extract domain registration features.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Dictionary of registration features
        """
        features = {}
        
        try:
            w = whois.whois(domain)
            
            # Registration age in days
            if w.creation_date:
                if isinstance(w.creation_date, list):
                    creation_date = w.creation_date[0]
                else:
                    creation_date = w.creation_date
                
                age_days = (pd.Timestamp.now() - pd.Timestamp(creation_date)).days
                features['domain_age_days'] = max(0, age_days)
                features['domain_is_recent'] = 1 if age_days < 90 else 0
            else:
                features['domain_age_days'] = 0
                features['domain_is_recent'] = 0
            
            # Registrar information
            if w.registrar:
                features['has_registrar_info'] = 1
                # Check if registrar is known
                common_registrars = ['godaddy', 'namecheap', 'network solutions', 'reg.ru']
                features['is_common_registrar'] = 1 if any(reg in str(w.registrar).lower() for reg in common_registrars) else 0
            else:
                features['has_registrar_info'] = 0
                features['is_common_registrar'] = 0
            
            # Name servers count
            if w.name_servers:
                features['name_servers_count'] = len(w.name_servers) if isinstance(w.name_servers, list) else 1
            else:
                features['name_servers_count'] = 0
                
        except Exception as e:
            # Default values for domains that can't be queried
            features.update({
                'domain_age_days': 0,
                'domain_is_recent': 1,  # Assume suspicious if can't be queried
                'has_registrar_info': 0,
                'is_common_registrar': 0,
                'name_servers_count': 0
            })
        
        return features
    
    @staticmethod
    def extract_dns_features(domain: str) -> Dict[str, float]:
        """Extract DNS-related features.
        
        Args:
            domain: Domain to analyze
            
        Returns:
            Dictionary of DNS features
        """
        features = {}
        
        try:
            ip_addresses = socket.gethostbyname_ex(domain)[2]
            features['has_dns_resolution'] = 1
            features['ip_count'] = len(ip_addresses)
            
            # Check for private IP ranges (potentially suspicious)
            for ip in ip_addresses:
                if ip.startswith(('192.168.', '10.', '172.')):
                    features['has_private_ip'] = 1
                    break
            else:
                features['has_private_ip'] = 0
                
        except Exception as e:
            features.update({
                'has_dns_resolution': 0,
                'ip_count': 0,
                'has_private_ip': 0
            })
        
        return features


class URLFeatureExtractor:
    """Extract features from URLs for phishing detection."""
    
    @staticmethod
    def extract_url_features(url: str) -> Dict[str, float]:
        """Extract comprehensive URL features.
        
        Args:
            url: URL string to analyze
            
        Returns:
            Dictionary of URL features
        """
        features = {}
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Basic URL features
            features['url_length'] = len(url)
            features['domain_length'] = len(parsed.netloc)
            features['path_length'] = len(parsed.path)
            features['query_length'] = len(parsed.query)
            features['fragment_length'] = len(parsed.fragment)
            
            # URL structure features
            features['has_query_params'] = 1 if parsed.query else 0
            features['has_fragment'] = 1 if parsed.fragment else 0
            features['has_user_info'] = 1 if parsed.username or parsed.password else 0
            features['param_count'] = len(urllib.parse.parse_qsl(parsed.query))
            
            # Suspicious patterns
            suspicious_patterns = {
                'has_ip_address': 0,
                'has_port': 0,
                'has_subdomain': 0,
                'has_unusual_chars': 0,
                'url_encoded_count': 0,
                'double_slash_count': 0,
                'dash_in_domain': 0,
                'underscore_in_domain': 0
            }
            
            # Check for IP address instead of domain
            if re.match(r'^\d+\.\d+\.\d+\.\d+$', parsed.netloc):
                suspicious_patterns['has_ip_address'] = 1
            
            # Check for port specification
            if ':' in parsed.netloc and not parsed.netloc.startswith('['):  # IPv6 bracket notation
                suspicious_patterns['has_port'] = 1
            
            # Check for subdomain count
            if parsed.netloc.count('.') > 1:
                suspicious_patterns['has_subdomain'] = 1
            
            # Check for unusual characters
            unusual_chars = ['@', '!', '*', '(', ')', '[', ']', '{', '}', '|', '\\', '^', '~']
            suspicious_patterns['has_unusual_chars'] = 1 if any(char in url for char in unusual_chars) else 0
            
            # Count URL encoding
            suspicious_patterns['url_encoded_count'] = url.count('%')
            
            # Count double slashes
            suspicious_patterns['double_slash_count'] = url.count('//')
            
            # Check domain for suspicious characters
            domain_part = parsed.netloc
            suspicious_patterns['dash_in_domain'] = 1 if '-' in domain_part else 0
            suspicious_patterns['underscore_in_domain'] = 1 if '_' in domain_part else 0
            
            features.update(suspicious_patterns)
            
            # Phishing keywords
            phishing_keywords = [
                'login', 'signin', 'verify', 'update', 'secure', 'confirm', 'account',
                'bank', 'paypal', 'ebay', 'amazon', 'credit', 'password', 'reset'
            ]
            features['phishing_keywords_count'] = sum(1 for keyword in phishing_keywords if keyword in url.lower())
            
            # Shortening services (potentially suspicious)
            shortening_services = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly', 'is.gd']
            features['from_shortening_service'] = 1 if any(service in parsed.netloc.lower() for service in shortening_services) else 0
            
        except Exception as e:
            # Default values for malformed URLs
            features.update({
                'url_length': len(url),
                'domain_length': 0,
                'path_length': 0,
                'query_length': 0,
                'fragment_length': 0,
                'has_query_params': 0,
                'has_fragment': 0,
                'has_user_info': 0,
                'param_count': 0,
                'has_ip_address': 0,
                'has_port': 0,
                'has_subdomain': 0,
                'has_unusual_chars': 0,
                'url_encoded_count': 0,
                'double_slash_count': 0,
                'dash_in_domain': 0,
                'underscore_in_domain': 0,
                'phishing_keywords_count': 0,
                'from_shortening_service': 0
            })
        
        return features
    
    @staticmethod
    def extract_content_features(url: str) -> Dict[str, float]:
        """Extract content-based features from URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary of content features
        """
        features = {}
        
        # Entropy calculation
        def calculate_entropy(text):
            if len(text) == 0:
                return 0
            chars = list(text)
            char_freq = {char: chars.count(char) for char in set(chars)}
            entropy = 0
            for count in char_freq.values():
                if count > 0:
                    probability = count / len(text)
                    entropy -= probability * np.log2(probability)
            return entropy
        
        features['url_entropy'] = calculate_entropy(url)
        
        # Linguistic features
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        
        features['vowel_ratio'] = sum(1 for char in url.lower() if char in vowels) / len(url) if len(url) > 0 else 0
        features['consonant_ratio'] = sum(1 for char in url.lower() if char in consonants) / len(url) if len(url) > 0 else 0
        
        # Ratio features
        features['digit_ratio'] = sum(1 for char in url if char.isdigit()) / len(url) if len(url) > 0 else 0
        features['special_char_ratio'] = sum(1 for char in url if not char.isalnum()) / len(url) if len(url) > 0 else 0
        
        return features


class SenderFeatureExtractor:
    """Extract features from email sender information."""
    
    @staticmethod
    def extract_email_features(email: str) -> Dict[str, float]:
        """Extract features from email addresses.
        
        Args:
            email: Email address to analyze
            
        Returns:
            Dictionary of email features
        """
        features = {}
        
        if '@' not in email:
            return {f'email_{key}': 0 for key in ['length', 'has_at', 'domain_parts', 'has_numbers', 'char_diversity']}
        
        local_part, domain = email.split('@', 1)
        
        # Basic features
        features['email_length'] = len(email)
        features['local_part_length'] = len(local_part)
        features['domain_length'] = len(domain)
        features['has_at'] = 1
        
        # Domain analysis
        domain_parts = domain.split('.')
        features['domain_parts'] = len(domain_parts)
        features['has_subdomain'] = 1 if len(domain_parts) > 2 else 0
        
        # Character analysis
        features['has_numbers'] = 1 if any(c.isdigit() for c in email) else 0
        features['has_underscore'] = 1 if '_' in local_part else 0
        features['has_dot'] = 1 if '.' in local_part else 0
        features['has_plus'] = 1 if '+' in local_part else 0
        features['has_dash'] = 1 if '-' in local_part else 0
        
        # Character diversity
        unique_chars = len(set(email.lower()))
        features['char_diversity'] = unique_chars / len(email) if len(email) > 0 else 0
        
        # Suspicious patterns
        suspicious_patterns = [
            'admin', 'noreply', 'no-reply', 'support', 'info', 'help',
            'service', 'system', 'automated', 'bot', 'robot'
        ]
        features['suspicious_local_part'] = 1 if any(pattern in local_part.lower() for pattern in suspicious_patterns) else 0
        
        # TLD analysis
        tld = domain_parts[-1] if domain_parts else ''
        features['is_common_tld'] = 1 if tld.lower() in ['com', 'org', 'net', 'edu', 'gov'] else 0
        
        # Free email providers
        free_providers = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com', 'icloud.com']
        features['is_free_provider'] = 1 if domain.lower() in free_providers else 0
        
        return features
    
    @staticmethod
    def extract_sender_metadata(sender_info: Dict[str, str]) -> Dict[str, float]:
        """Extract features from sender metadata.
        
        Args:
            sender_info: Dictionary containing sender metadata
            
        Returns:
            Dictionary of metadata features
        """
        features = {}
        
        # Extract various metadata fields
        for key, value in sender_info.items():
            if isinstance(value, str):
                # Basic string features
                features[f'{key}_length'] = len(value)
                features[f'{key}_word_count'] = len(value.split())
                features[f'{key}_has_numbers'] = 1 if any(c.isdigit() for c in value) else 0
                
                # Character analysis
                upper_count = sum(1 for c in value if c.isupper())
                lower_count = sum(1 for c in value if c.islower())
                total_chars = upper_count + lower_count
                
                if total_chars > 0:
                    features[f'{key}_upper_ratio'] = upper_count / total_chars
                    features[f'{key}_lower_ratio'] = lower_count / total_chars
                else:
                    features[f'{key}_upper_ratio'] = 0
                    features[f'{key}_lower_ratio'] = 0
        
        return features


def extract_all_features(data: Union[str, Dict[str, str]], feature_type: str) -> Dict[str, float]:
    """Extract comprehensive features based on type.
    
    Args:
        data: Input data (URL, domain, email, or metadata dict)
        feature_type: Type of features to extract ('domain', 'url', 'email', 'metadata')
        
    Returns:
        Dictionary of all extracted features
    """
    features = {}
    
    if feature_type == 'domain':
        domain_extractor = DomainFeatureExtractor()
        features.update(domain_extractor.extract_basic_domain_features(data))
        features.update(domain_extractor.extract_registration_features(data))
        features.update(domain_extractor.extract_dns_features(data))
        
    elif feature_type == 'url':
        url_extractor = URLFeatureExtractor()
        features.update(url_extractor.extract_url_features(data))
        features.update(url_extractor.extract_content_features(data))
        
    elif feature_type == 'email':
        sender_extractor = SenderFeatureExtractor()
        features.update(sender_extractor.extract_email_features(data))
        
    elif feature_type == 'metadata':
        sender_extractor = SenderFeatureExtractor()
        features.update(sender_extractor.extract_sender_metadata(data))
    
    return features


def create_feature_matrix(data_list: List[Union[str, Dict[str, str]]], feature_type: str) -> Tuple[np.ndarray, List[str]]:
    """Create feature matrix from list of data.
    
    Args:
        data_list: List of input data
        feature_type: Type of features to extract
        
    Returns:
        Tuple of (feature_matrix, feature_names)
    """
    all_features = []
    all_feature_names = set()
    
    # Extract features from all data points
    for data in data_list:
        features = extract_all_features(data, feature_type)
        all_features.append(features)
        all_feature_names.update(features.keys())
    
    # Convert to sorted list for consistency
    feature_names = sorted(list(all_feature_names))
    
    # Create feature matrix
    feature_matrix = np.array([[features.get(name, 0) for name in feature_names] 
                              for features in all_features])
    
    return feature_matrix, feature_names


if __name__ == "__main__":
    # Example usage
    print("Feature Extraction Module - Example Usage")
    
    # Test domain features
    domain = "google.com"
    domain_features = extract_all_features(domain, 'domain')
    print(f"Domain features for {domain}: {domain_features}")
    
    # Test URL features
    url = "https://www.google.com/search?q=test"
    url_features = extract_all_features(url, 'url')
    print(f"URL features: {url_features}")
    
    # Test email features
    email = "user@gmail.com"
    email_features = extract_all_features(email, 'email')
    print(f"Email features: {email_features}")