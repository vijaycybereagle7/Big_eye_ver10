"""
Configuration settings for the Cyber NLP Processor
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ModelConfig:
    """Configuration for NLP models"""
    spacy_model: str = "en_core_web_sm"
    use_gpu: bool = False
    max_sequence_length: int = 512
    batch_size: int = 32
    
    # Hugging Face models
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    classification_model: str = "microsoft/DialoGPT-medium"
    
    # Confidence thresholds
    min_ioc_confidence: float = 0.7
    min_classification_confidence: float = 0.6
    
    # IOC extraction patterns
    enable_regex_patterns: bool = True
    enable_spacy_ner: bool = True


@dataclass
class ProcessingConfig:
    """Configuration for text processing"""
    # Text preprocessing
    max_text_length: int = 10000
    min_text_length: int = 10
    
    # Language detection
    enable_language_detection: bool = True
    supported_languages: List[str] = None
    
    # Sentiment analysis
    enable_sentiment_analysis: bool = True
    
    # Named Entity Recognition
    enable_ner: bool = True
    ner_entities: List[str] = None
    
    # File processing
    supported_file_extensions: List[str] = None
    
    def __post_init__(self):
        if self.supported_languages is None:
            self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl']
        
        if self.ner_entities is None:
            self.ner_entities = ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART']
        
        if self.supported_file_extensions is None:
            self.supported_file_extensions = ['.txt', '.csv', '.json', '.xml', '.log']


@dataclass
class SecurityConfig:
    """Configuration for security analysis"""
    # Email analysis
    phishing_keywords: List[str] = None
    spam_keywords: List[str] = None
    
    # Brand impersonation detection
    known_brands: Dict[str, List[str]] = None
    suspicious_patterns: List[str] = None
    
    # IOC validation
    validate_ip_addresses: bool = True
    validate_domains: bool = True
    validate_hashes: bool = True
    
    # Risk scoring
    high_risk_threshold: float = 1.0
    medium_risk_threshold: float = 0.5
    low_risk_threshold: float = 0.2
    
    def __post_init__(self):
        if self.phishing_keywords is None:
            self.phishing_keywords = [
                'urgent', 'verify your account', 'suspend', 'confirm', 'click here',
                'password reset', 'security alert', 'unusual activity', 'immediately',
                'act now', 'limited time', 'final notice', 'suspended account',
                'update required', 'response needed', 'attention required'
            ]
        
        if self.spam_keywords is None:
            self.spam_keywords = [
                'free', 'win', 'winner', 'congratulations', 'prize', 'lottery',
                'credit', 'loan', 'mortgage', 'investment', 'opportunity',
                'money back', 'guarantee', 'risk-free'
            ]
        
        if self.known_brands is None:
            self.known_brands = {
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
                'citi': ['citi.com'],
                'americanexpress': ['americanexpress.com']
            }
        
        if self.suspicious_patterns is None:
            self.suspicious_patterns = [
                r'-secure', r'-login', r'-auth', r'-verify', r'-update',
                r'-confirm', r'-support', r'-account', r'-service',
                r'secure-', r'login-', r'auth-', r'verify-', r'update-',
                r'confirm-', r'support-', r'account-', r'service-'
            ]


@dataclass
class OutputConfig:
    """Configuration for output formatting"""
    # JSON output
    indent_json: int = 2
    include_metadata: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Report generation
    generate_summary_report: bool = True
    include_confidence_scores: bool = True
    include_context_snippets: bool = True
    
    # Data export
    export_iocs_csv: bool = True
    export_analysis_json: bool = True
    export_reports_html: bool = False


@dataclass
class DatabaseConfig:
    """Configuration for database integration"""
    # Connection settings
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_database: str = "cyber_nlp"
    
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "cyber_nlp"
    
    # Collection/Table names
    iocs_collection: str = "iocs"
    threat_intel_collection: str = "threat_intelligence"
    email_analysis_collection: str = "email_analysis"
    brand_analysis_collection: str = "brand_analysis"
    
    # Indexes
    create_indexes: bool = True
    index_fields: List[str] = None
    
    def __post_init__(self):
        if self.index_fields is None:
            self.index_fields = [
                'ioc_type', 'value', 'confidence', 'timestamp',
                'source', 'threat_actor', 'malware_family'
            ]


@dataclass
class Config:
    """Main configuration class"""
    model: ModelConfig = None
    processing: ProcessingConfig = None
    security: SecurityConfig = None
    output: OutputConfig = None
    database: DatabaseConfig = None
    
    def __post_init__(self):
        if self.model is None:
            self.model = ModelConfig()
        if self.processing is None:
            self.processing = ProcessingConfig()
        if self.security is None:
            self.security = SecurityConfig()
        if self.output is None:
            self.output = OutputConfig()
        if self.database is None:
            self.database = DatabaseConfig()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        
        # Model config
        if os.getenv('NLP_SPACY_MODEL'):
            config.model.spacy_model = os.getenv('NLP_SPACY_MODEL')
        if os.getenv('NLP_USE_GPU'):
            config.model.use_gpu = os.getenv('NLP_USE_GPU').lower() == 'true'
        
        # Database config
        if os.getenv('MONGODB_HOST'):
            config.database.mongodb_host = os.getenv('MONGODB_HOST')
        if os.getenv('POSTGRES_HOST'):
            config.database.postgres_host = os.getenv('POSTGRES_HOST')
        
        return config
    
    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        import json
        
        config_dict = {
            'model': self.model.__dict__,
            'processing': self.processing.__dict__,
            'security': self.security.__dict__,
            'output': self.output.__dict__,
            'database': self.database.__dict__
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Config':
        """Load configuration from JSON file"""
        import json
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        config = cls()
        config.model = ModelConfig(**config_dict.get('model', {}))
        config.processing = ProcessingConfig(**config_dict.get('processing', {}))
        config.security = SecurityConfig(**config_dict.get('security', {}))
        config.output = OutputConfig(**config_dict.get('output', {}))
        config.database = DatabaseConfig(**config_dict.get('database', {}))
        
        return config


# Global configuration instance
default_config = Config()
