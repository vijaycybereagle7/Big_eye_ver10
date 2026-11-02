"""
Comprehensive NLP Processor for Cybersecurity Applications
Author: AI/ML Security System
Description: Implements IOC extraction, email classification, WHOIS parsing,
domain analysis, and threat intelligence extraction using spaCy and Hugging Face
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Core NLP Libraries
import spacy
from spacy import displacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch

# Data Processing
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Text Analysis
from textblob import TextBlob
import langdetect

# Network Analysis
import tld
from urllib.parse import urlparse


@dataclass
class IOC:
    """Indicators of Compromise data structure"""
    type: str
    value: str
    confidence: float
    context: str
    source: str
    timestamp: str


@dataclass
class ThreatIntelligence:
    """Threat Intelligence data structure"""
    indicators: List[IOC]
    threat_actors: List[str]
    malware_families: List[str]
    attack_vectors: List[str]
    iocs: Dict[str, Any]
    sentiment_score: float
    language: str
    entities: Dict[str, List[str]]


@dataclass
class EmailClassification:
    """Email classification result"""
    classification: str  # 'spam', 'phishing', 'legitimate'
    confidence: float
    phishing_indicators: List[str]
    suspicious_urls: List[str]
    suspicious_attachments: List[str]
    analysis_details: Dict[str, Any]


class RegexPatterns:
    """Collection of regex patterns for IOC detection"""
    
    # IP Addresses (IPv4 and IPv6)
    IPV4_PATTERN = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    IPV6_PATTERN = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    # URLs
    URL_PATTERN = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w)*)?)?'
    
    # Email Addresses
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Domain Names (excluding full URLs)
    DOMAIN_PATTERN = r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b'
    
    # File Hashes
    MD5_PATTERN = r'\b[a-fA-F0-9]{32}\b'
    SHA1_PATTERN = r'\b[a-fA-F0-9]{40}\b'
    SHA256_PATTERN = r'\b[a-fA-F0-9]{64}\b'
    
    # Windows Registry Keys
    REGISTRY_PATTERN = r'HKEY_[A-Z_]+[\\a-zA-Z0-9_-]*'
    
    # File Paths (Windows and Unix)
    WINDOWS_PATH_PATTERN = r'[A-Z]:\\[^<>:"|?*\n\r]+'
    UNIX_PATH_PATTERN = r'/[^<>:"|?*\n\r]+'
    
    # MAC Addresses
    MAC_PATTERN = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b'
    
    # CVE IDs
    CVE_PATTERN = r'CVE-\d{4}-\d{4,7}'
    
    # File Names with Extensions
    FILENAME_PATTERN = r'\b[A-Za-z0-9\-_]+\.(?:exe|dll|bat|cmd|scr|pif|vbs|js|ps1|sh|py)\b'
    
    @classmethod
    def get_patterns(cls) -> Dict[str, str]:
        """Get all regex patterns"""
        return {
            'ipv4': cls.IPV4_PATTERN,
            'ipv6': cls.IPV6_PATTERN,
            'url': cls.URL_PATTERN,
            'email': cls.EMAIL_PATTERN,
            'domain': cls.DOMAIN_PATTERN,
            'md5': cls.MD5_PATTERN,
            'sha1': cls.SHA1_PATTERN,
            'sha256': cls.SHA256_PATTERN,
            'registry': cls.REGISTRY_PATTERN,
            'windows_path': cls.WINDOWS_PATH_PATTERN,
            'unix_path': cls.UNIX_PATH_PATTERN,
            'mac': cls.MAC_PATTERN,
            'cve': cls.CVE_PATTERN,
            'filename': cls.FILENAME_PATTERN
        }


class BrandImpersonationAnalyzer:
    """Analyzer for brand impersonation in domains and URLs"""
    
    def __init__(self):
        # Common legitimate brand domains
        self.legitimate_brands = {
            'google': ['google.com', 'google.com.br', 'google.co.uk'],
            'microsoft': ['microsoft.com', 'office.com', 'live.com'],
            'apple': ['apple.com', 'icloud.com'],
            'amazon': ['amazon.com', 'amazon.co.uk'],
            'facebook': ['facebook.com', 'instagram.com'],
            'paypal': ['paypal.com'],
            'netflix': ['netflix.com'],
            'twitter': ['twitter.com', 'x.com'],
            'linkedin': ['linkedin.com'],
            'bankofamerica': ['bankofamerica.com'],
            'wellsfargo': ['wellsfargo.com'],
            'chase': ['chase.com'],
            'citi': ['citi.com']
        }
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'-secure', r'-login', r'-auth', r'-verify',
            r'-update', r'-confirm', r'-support',
            r'secure-', r'login-', r'auth-', r'verify-',
            r'update-', r'confirm-', r'support-'
        ]
    
    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain for brand impersonation indicators"""
        result = {
            'domain': domain,
            'suspicious_score': 0.0,
            'potential_brands': [],
            'suspicious_patterns': [],
            'brand_similarity': {},
            'recommendation': ''
        }
        
        domain_lower = domain.lower()
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, domain_lower):
                result['suspicious_patterns'].append(pattern)
                result['suspicious_score'] += 0.3
        
        # Check for brand similarity
        for brand, legitimate_domains in self.legitimate_brands.items():
            # Extract domain parts
            domain_parts = domain_lower.split('.')
            main_domain = '.'.join(domain_parts) if len(domain_parts) > 1 else domain_lower
            
            # Check for brand name in domain
            if brand in main_domain:
                result['potential_brands'].append(brand)
                result['suspicious_score'] += 0.2
            
            # Check for common brand TLD patterns
            for legitimate in legitimate_domains:
                legitimate_lower = legitimate.lower()
                if (brand in main_domain and 
                    not any(legitimate_lower.endswith(main_domain[-len(d):]) 
                           for d in legitimate_domains)):
                    result['suspicious_score'] += 0.5
                    result['brand_similarity'][brand] = {
                        'match_type': 'brand_name',
                        'legitimate_domains': legitimate_domains
                    }
        
        # Calculate recommendation
        if result['suspicious_score'] >= 1.0:
            result['recommendation'] = 'HIGH_RISK - Likely brand impersonation'
        elif result['suspicious_score'] >= 0.5:
            result['recommendation'] = 'MEDIUM_RISK - Potential brand impersonation'
        elif result['suspicious_score'] > 0:
            result['recommendation'] = 'LOW_RISK - Minor suspicious indicators'
        else:
            result['recommendation'] = 'LOW_RISK - No strong impersonation indicators'
        
        return result


class WHOISParser:
    """Parser for WHOIS data and domain information"""
    
    def __init__(self):
        pass
    
    def parse_whois_text(self, whois_text: str) -> Dict[str, Any]:
        """Parse raw WHOIS text into structured data"""
        result = {
            'registrar': None,
            'creation_date': None,
            'expiration_date': None,
            'name_servers': [],
            'registrant_info': {},
            'admin_info': {},
            'tech_info': {},
            'domain_status': [],
            'parsing_errors': []
        }
        
        lines = whois_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('%') or line.startswith('>>>'):
                continue
            
            # Registrar
            if 'registrar:' in line.lower():
                result['registrar'] = line.split(':', 1)[1].strip()
            
            # Creation date
            elif any(date_key in line.lower() for date_key in ['created:', 'creation date:', 'created date:']):
                result['creation_date'] = line.split(':', 1)[1].strip()
            
            # Expiration date
            elif any(date_key in line.lower() for date_key in ['expiry date:', 'expiration date:', 'expires:']):
                result['expiration_date'] = line.split(':', 1)[1].strip()
            
            # Name servers
            elif 'name server:' in line.lower():
                ns = line.split(':', 1)[1].strip()
                if ns not in result['name_servers']:
                    result['name_servers'].append(ns)
            
            # Domain status
            elif any(status_key in line.lower() for status_key in ['status:', 'domain status:']):
                status = line.split(':', 1)[1].strip()
                if status not in result['domain_status']:
                    result['domain_status'].append(status)
            
            # Registrant info
            elif any(info_key in line.lower() for info_key in ['registrant', ' registrant name:', ' registrant organization:']):
                key = line.split(':', 1)[0].strip().lower()
                value = line.split(':', 1)[1].strip() if ':' in line else ''
                result['registrant_info'][key] = value
        
        return result
    
    def analyze_domain_age(self, creation_date: str) -> Dict[str, Any]:
        """Analyze domain age from creation date"""
        try:
            # Try to parse various date formats
            date_formats = [
                '%d-%b-%Y', '%d-%b-%Y %H:%M:%S',
                '%Y-%m-%d', '%Y-%m-%d %H:%M:%S',
                '%m/%d/%Y', '%m/%d/%Y %H:%M:%S'
            ]
            
            creation_dt = None
            for fmt in date_formats:
                try:
                    creation_dt = datetime.strptime(creation_date.split()[0], fmt)
                    break
                except ValueError:
                    continue
            
            if creation_dt:
                age_days = (datetime.now() - creation_dt).days
                age_years = age_days / 365.25
                
                risk_level = 'LOW'
                if age_years < 1:
                    risk_level = 'HIGH'
                elif age_years < 3:
                    risk_level = 'MEDIUM'
                
                return {
                    'creation_date': creation_date,
                    'age_days': age_days,
                    'age_years': age_years,
                    'risk_level': risk_level
                }
        except Exception as e:
            return {'error': f'Failed to parse date: {str(e)}'}
        
        return {'error': 'Could not parse creation date'}


class CyberNLPProcessor:
    """Main NLP processor for cybersecurity applications"""
    
    def __init__(self, use_gpu: bool = False):
        """Initialize the NLP processor"""
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.device = 0 if self.use_gpu else -1
        
        # Initialize models
        self._load_models()
        
        # Initialize analyzers
        self.brand_analyzer = BrandImpersonationAnalyzer()
        self.whois_parser = WHOISParser()
        
        # Initialize email classifier
        self.email_classifier = None
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_models(self):
        """Load spaCy and Hugging Face models"""
        try:
            # Load spaCy model
            self.nlp = spacy.load('en_core_web_sm')
            self.logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        try:
            # Load sentiment analysis pipeline
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=self.device
            )
            self.logger.info("Loaded sentiment analysis model")
        except Exception as e:
            self.logger.warning(f"Could not load sentiment model: {e}")
            self.sentiment_analyzer = None
        
        try:
            # Load text classification pipeline for threat intelligence
            self.threat_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                device=self.device
            )
            self.logger.info("Loaded threat classification model")
        except Exception as e:
            self.logger.warning(f"Could not load threat classification model: {e}")
            self.threat_classifier = None
    
    def extract_iocs(self, text: str, min_confidence: float = 0.7) -> List[IOC]:
        """Extract Indicators of Compromise from text"""
        if not text:
            return []
        
        iocs = []
        patterns = RegexPatterns.get_patterns()
        
        # Use spaCy for NER if available
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract URLs and domains from spaCy entities
            for ent in doc.ents:
                if ent.label_ in ['URL', 'ORG', 'PERSON']:
                    # Check if it's a domain or URL
                    for pattern_name, pattern in patterns.items():
                        if pattern_name in ['domain', 'url']:
                            matches = re.finditer(pattern, ent.text, re.IGNORECASE)
                            for match in matches:
                                iocs.append(IOC(
                                    type=pattern_name,
                                    value=match.group(),
                                    confidence=0.9,
                                    context=ent.text,
                                    source='spacy_ner',
                                    timestamp=datetime.now().isoformat()
                                ))
        
        # Use regex for additional IOC extraction
        for ioc_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip if already found by spaCy
                if not any(ioc.value == match.group() for ioc in iocs):
                    iocs.append(IOC(
                        type=ioc_type,
                        value=match.group(),
                        confidence=0.95,
                        context=text[max(0, match.start()-50):match.end()+50],
                        source='regex',
                        timestamp=datetime.now().isoformat()
                    ))
        
        # Filter by confidence
        return [ioc for ioc in iocs if ioc.confidence >= min_confidence]
    
    def analyze_email(self, email_content: str, subject: str = "", sender: str = "") -> EmailClassification:
        """Analyze email for spam and phishing indicators"""
        if not email_content:
            return EmailClassification(
                classification='unknown',
                confidence=0.0,
                phishing_indicators=[],
                suspicious_urls=[],
                suspicious_attachments=[],
                analysis_details={}
            )
        
        analysis_details = {
            'length': len(email_content),
            'word_count': len(email_content.split()),
            'uppercase_ratio': sum(1 for c in email_content if c.isupper()) / len(email_content) if email_content else 0,
            'contains_links': False,
            'contains_attachments': False,
            'language_detected': 'unknown'
        }
        
        # Detect language
        try:
            language = langdetect.detect(email_content)
            analysis_details['language_detected'] = language
        except:
            analysis_details['language_detected'] = 'unknown'
        
        # Extract suspicious indicators
        phishing_indicators = []
        suspicious_urls = []
        suspicious_attachments = []
        
        # Check for phishing indicators in text
        phishing_keywords = [
            'urgent', 'verify your account', 'suspend', 'confirm', 'click here',
            'password reset', 'security alert', 'unusual activity', 'immediately'
        ]
        
        email_lower = email_content.lower()
        for keyword in phishing_keywords:
            if keyword in email_lower:
                phishing_indicators.append(f"Contains phishing keyword: {keyword}")
        
        # Extract URLs
        url_pattern = RegexPatterns.get_patterns()['url']
        urls = re.findall(url_pattern, email_content, re.IGNORECASE)
        analysis_details['contains_links'] = len(urls) > 0
        
        for url in urls:
            # Analyze each URL
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                if domain:
                    brand_analysis = self.brand_analyzer.analyze_domain(domain)
                    if brand_analysis['suspicious_score'] > 0.5:
                        suspicious_urls.append({
                            'url': url,
                            'domain': domain,
                            'risk_score': brand_analysis['suspicious_score'],
                            'analysis': brand_analysis
                        })
            except Exception:
                suspicious_urls.append({'url': url, 'error': 'Failed to analyze'})
        
        # Check for suspicious file attachments
        file_extensions = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.vbs', '.js', '.ps1', '.zip', '.rar']
        for ext in file_extensions:
            if ext in email_lower:
                suspicious_attachments.append(f"Potentially dangerous attachment: {ext}")
        
        # Count indicators
        suspicious_score = 0
        suspicious_score += len(phishing_indicators) * 0.3
        suspicious_score += len(suspicious_urls) * 0.4
        suspicious_score += len(suspicious_attachments) * 0.5
        suspicious_score += analysis_details['uppercase_ratio'] * 0.2
        
        # Classification logic
        if suspicious_score >= 1.5:
            classification = 'phishing'
            confidence = min(0.95, suspicious_score / 2.0)
        elif suspicious_score >= 0.8:
            classification = 'spam'
            confidence = min(0.85, suspicious_score / 2.0)
        else:
            classification = 'legitimate'
            confidence = max(0.6, 1.0 - suspicious_score)
        
        return EmailClassification(
            classification=classification,
            confidence=confidence,
            phishing_indicators=phishing_indicators,
            suspicious_urls=suspicious_urls,
            suspicious_attachments=suspicious_attachments,
            analysis_details=analysis_details
        )
    
    def parse_whois_data(self, whois_text: str) -> Dict[str, Any]:
        """Parse WHOIS data and perform additional analysis"""
        if not whois_text:
            return {'error': 'No WHOIS data provided'}
        
        parsed_data = self.whois_parser.parse_whois_text(whois_text)
        
        # Analyze domain age if creation date is available
        if parsed_data.get('creation_date'):
            age_analysis = self.whois_parser.analyze_domain_age(parsed_data['creation_date'])
            parsed_data['age_analysis'] = age_analysis
        
        # Extract domain name from registrar info for brand analysis
        if parsed_data.get('registrar'):
            registrar_lower = parsed_data['registrar'].lower()
            brand_keywords = ['godaddy', 'namecheap', 'google domains', 'aws registrar']
            if any(keyword in registrar_lower for keyword in brand_keywords):
                parsed_data['popular_registrar'] = True
        
        return parsed_data
    
    def analyze_domain_brands(self, domain: str) -> Dict[str, Any]:
        """Analyze domain for brand impersonation"""
        if not domain:
            return {'error': 'No domain provided'}
        
        analysis = self.brand_analyzer.analyze_domain(domain)
        
        # Additional checks
        try:
            # Use tld library to get additional domain info
            domain_obj = tld.get_tld(f"https://{domain}", fix_protocol=True)
            analysis['tld_info'] = {
                'tld': domain_obj.tld,
                'domain': domain_obj.domain,
                'subdomain': domain_obj.subdomain
            }
        except Exception as e:
            analysis['tld_error'] = str(e)
        
        return analysis
    
    def extract_threat_intelligence(self, text: str) -> ThreatIntelligence:
        """Extract comprehensive threat intelligence from unstructured text"""
        if not text:
            return ThreatIntelligence(
                indicators=[],
                threat_actors=[],
                malware_families=[],
                attack_vectors=[],
                iocs={},
                sentiment_score=0.0,
                language='unknown',
                entities={}
            )
        
        # Detect language
        try:
            language = langdetect.detect(text)
        except:
            language = 'unknown'
        
        # Extract IOCs
        iocs = self.extract_iocs(text)
        
        # Process with spaCy for NER
        entities = {'PERSON': [], 'ORG': [], 'GPE': [], 'PRODUCT': []}
        threat_actors = []
        malware_families = []
        attack_vectors = []
        
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in entities:
                    entities[ent.label_].append(ent.text)
            
            # Identify threat actors and malware (heuristic approach)
            for ent in doc.ents:
                text_lower = ent.text.lower()
                if any(actor_indicator in text_lower for actor_indicator in ['apt', 'group', 'actor', 'campaign']):
                    threat_actors.append(ent.text)
                elif any(malware_indicator in text_lower for malware_indicator in ['trojan', 'malware', 'virus', 'worm']):
                    malware_families.append(ent.text)
        
        # Sentiment analysis
        sentiment_score = 0.0
        if self.sentiment_analyzer:
            try:
                result = self.sentiment_analyzer(text[:512])  # Limit for model input
                if result and len(result) > 0:
                    # Convert to score (-1 to 1)
                    if result[0]['label'] == 'LABEL_2':  # Positive
                        sentiment_score = result[0]['score']
                    elif result[0]['label'] == 'LABEL_0':  # Negative
                        sentiment_score = -result[0]['score']
            except Exception as e:
                self.logger.warning(f"Sentiment analysis failed: {e}")
        
        # Organize IOCs by type
        iocs_by_type = {}
        for ioc in iocs:
            if ioc.type not in iocs_by_type:
                iocs_by_type[ioc.type] = []
            iocs_by_type[ioc.type].append(ioc.value)
        
        return ThreatIntelligence(
            indicators=iocs,
            threat_actors=list(set(threat_actors)),
            malware_families=list(set(malware_families)),
            attack_vectors=list(set(attack_vectors)),
            iocs=iocs_by_type,
            sentiment_score=sentiment_score,
            language=language,
            entities=entities
        )
    
    def train_email_classifier(self, training_data: List[Tuple[str, str, str]], 
                              model_path: Optional[str] = None) -> Dict[str, Any]:
        """Train email classifier with provided data
        
        Args:
            training_data: List of tuples (subject, content, label)
            model_path: Optional path to save the trained model
        """
        if len(training_data) < 10:
            return {'error': 'Insufficient training data (minimum 10 samples required)'}
        
        # Prepare data
        texts = [f"{subject} {content}" if subject else content for subject, content, _ in training_data]
        labels = [label for _, _, label in training_data]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            texts, labels, test_size=0.2, random_state=42, stratify=labels
        )
        
        # Vectorize text
        vectorizer = TfidfVectorizer(max_features=5000, stop_words='english', ngram_range=(1, 2))
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        from sklearn.naive_bayes import MultinomialNB
        
        # Train model
        classifier = MultinomialNB(alpha=1.0)
        classifier.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = classifier.predict(X_test_vec)
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # Save model if path provided
        if model_path:
            model_data = {
                'classifier': classifier,
                'vectorizer': vectorizer,
                'label_mapping': sorted(list(set(labels)))
            }
            joblib.dump(model_data, model_path)
            self.logger.info(f"Model saved to {model_path}")
        
        # Store for inference
        self.email_classifier = {
            'classifier': classifier,
            'vectorizer': vectorizer,
            'label_mapping': sorted(list(set(labels)))
        }
        
        return {
            'accuracy': report['accuracy'],
            'classification_report': report,
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
    
    def classify_email_trained(self, subject: str, content: str) -> Dict[str, Any]:
        """Classify email using trained model"""
        if not self.email_classifier:
            return {'error': 'No trained model available'}
        
        try:
            text = f"{subject} {content}" if subject else content
            text_vec = self.email_classifier['vectorizer'].transform([text])
            
            prediction = self.email_classifier['classifier'].predict(text_vec)[0]
            probabilities = self.email_classifier['classifier'].predict_proba(text_vec)[0]
            
            return {
                'classification': prediction,
                'confidence': float(max(probabilities)),
                'probabilities': {
                    label: float(prob) for label, prob in 
                    zip(self.email_classifier['label_mapping'], probabilities)
                }
            }
        except Exception as e:
            return {'error': f'Classification failed: {str(e)}'}


def main():
    """Main function for testing and demonstration"""
    
    # Initialize processor
    processor = CyberNLPProcessor(use_gpu=False)
    
    # Test IOC extraction
    sample_text = """
    The threat actor used IP address 192.168.1.100 to host malware at 
    http://malicious-domain.com/payload.exe. The file hash is 
    a1b2c3d4e5f6789012345678901234567890abcd. The attack was attributed 
    to APT29 and used the Cobalt Strike beacon.
    """
    
    print("=== IOC Extraction Test ===")
    iocs = processor.extract_iocs(sample_text)
    for ioc in iocs:
        print(f"Type: {ioc.type}, Value: {ioc.value}, Confidence: {ioc.confidence}")
    
    # Test email analysis
    print("\n=== Email Analysis Test ===")
    sample_email = """
    Subject: URGENT: Verify Your Account
    
    Dear User,
    We have detected unusual activity in your account. Please verify your 
    account immediately by clicking the link below:
    http://security-verify-login.com/confirm
    """
    
    email_result = processor.analyze_email(sample_email, 
                                         subject="URGENT: Verify Your Account")
    print(f"Classification: {email_result.classification}")
    print(f"Confidence: {email_result.confidence}")
    print(f"Phishing Indicators: {email_result.phishing_indicators}")
    
    # Test threat intelligence extraction
    print("\n=== Threat Intelligence Extraction Test ===")
    threat_text = """
    Security researchers at Mandiant discovered a new campaign attributed to 
    APT41 targeting healthcare organizations. The threat actor used spear-phishing 
    emails with malicious attachments. Indicators include domains like 
    healthcare-update.com and IPs 203.0.113.10 and 203.0.113.11.
    """
    
    threat_intel = processor.extract_threat_intelligence(threat_text)
    print(f"Language: {threat_intel.language}")
    print(f"Threat Actors: {threat_intel.threat_actors}")
    print(f"Malware Families: {threat_intel.malware_families}")
    print(f"IOCs found: {len(threat_intel.indicators)}")
    
    # Test brand analysis
    print("\n=== Brand Analysis Test ===")
    suspicious_domain = "google-secure-login-verify.com"
    brand_analysis = processor.analyze_domain_brands(suspicious_domain)
    print(f"Domain: {suspicious_domain}")
    print(f"Suspicious Score: {brand_analysis['suspicious_score']}")
    print(f"Recommendation: {brand_analysis['recommendation']}")


if __name__ == "__main__":
    main()
