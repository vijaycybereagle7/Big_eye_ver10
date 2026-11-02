"""
PII Protection Module
Handles Personally Identifiable Information (PII) protection and anonymization
"""

import re
import hashlib
import random
import string
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import json


class PIICategory(Enum):
    """Categories of PII data"""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    MEDICAL_ID = "medical_id"
    LICENSE_NUMBER = "license_number"
    PASSPORT_NUMBER = "passport_number"
    DRIVERS_LICENSE = "drivers_license"
    BIOMETRIC_DATA = "biometric_data"


@dataclass
class PIIPattern:
    """PII data pattern and detection rules"""
    category: PIICategory
    regex_pattern: str
    sample_format: str
    sensitivity_level: int  # 1-5 (5 being most sensitive)


class PIIProtection:
    """Handles PII detection, masking, and protection"""
    
    def __init__(self):
        self.pii_patterns = self._load_pii_patterns()
        self.masking_char = '*'
        self.hash_salt = "pii_protection_salt_2025"
        
    def _load_pii_patterns(self) -> List[PIIPattern]:
        """Load PII detection patterns"""
        patterns = [
            # Email
            PIIPattern(
                PIICategory.EMAIL,
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'user@example.com',
                3
            ),
            
            # Phone (US format)
            PIIPattern(
                PIICategory.PHONE,
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                '123-456-7890',
                3
            ),
            
            # SSN
            PIIPattern(
                PIICategory.SSN,
                r'\b\d{3}-\d{2}-\d{4}\b',
                '123-45-6789',
                5
            ),
            
            # Credit Card (with validation)
            PIIPattern(
                PIICategory.CREDIT_CARD,
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                '1234-5678-9012-3456',
                5
            ),
            
            # IP Address
            PIIPattern(
                PIICategory.IP_ADDRESS,
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
                '192.168.1.1',
                2
            ),
            
            # Date of Birth (various formats)
            PIIPattern(
                PIICategory.DATE_OF_BIRTH,
                r'\b(?:0?[1-9]|1[0-2])[-/]?(?:0?[1-9]|[12][0-9]|3[01])[-/]?(?:19|20)\d{2}\b',
                '01/01/1990',
                4
            ),
            
            # US Address pattern (simplified)
            PIIPattern(
                PIICategory.ADDRESS,
                r'\b\d+\s+(?:[A-Za-z0-9]+\s+){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b',
                '123 Main Street',
                4
            )
        ]
        
        return patterns
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text
        
        Args:
            text: Text to scan for PII
            
        Returns:
            List of detected PII instances
        """
        detected_pii = []
        
        for pattern in self.pii_patterns:
            matches = re.finditer(pattern.regex_pattern, text, re.IGNORECASE)
            
            for match in matches:
                detected_pii.append({
                    'category': pattern.category.value,
                    'sensitivity_level': pattern.sensitivity_level,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'sample_format': pattern.sample_format
                })
        
        return detected_pii
    
    def mask_pii(self, text: str, categories: Optional[List[PIICategory]] = None) -> str:
        """
        Mask PII in text
        
        Args:
            text: Text to mask
            categories: Specific categories to mask (None for all)
            
        Returns:
            Text with PII masked
        """
        masked_text = text
        
        for pattern in self.pii_patterns:
            if categories and pattern.category not in categories:
                continue
                
            # Apply masking based on category
            if pattern.category == PIICategory.EMAIL:
                masked_text = self._mask_email(masked_text, pattern.regex_pattern)
            elif pattern.category == PIICategory.PHONE:
                masked_text = self._mask_phone(masked_text, pattern.regex_pattern)
            elif pattern.category == PIICategory.SSN:
                masked_text = self._mask_ssn(masked_text, pattern.regex_pattern)
            elif pattern.category == PIICategory.CREDIT_CARD:
                masked_text = self._mask_credit_card(masked_text, pattern.regex_pattern)
            elif pattern.category == PIICategory.IP_ADDRESS:
                masked_text = self._mask_ip_address(masked_text, pattern.regex_pattern)
            elif pattern.category == PIICategory.ADDRESS:
                masked_text = self._mask_address(masked_text, pattern.regex_pattern)
            else:
                # Generic masking
                masked_text = re.sub(
                    pattern.regex_pattern,
                    lambda m: self.masking_char * len(m.group()),
                    masked_text
                )
        
        return masked_text
    
    def _mask_email(self, text: str, pattern: str) -> str:
        """Mask email addresses"""
        def replace_email(match):
            email = match.group()
            parts = email.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                # Keep first and last character of username
                if len(username) > 2:
                    masked_user = username[0] + self.masking_char * (len(username) - 2) + username[-1]
                else:
                    masked_user = self.masking_char * len(username)
                return f"{masked_user}@{domain}"
            return self.masking_char * len(email)
        
        return re.sub(pattern, replace_email, text, flags=re.IGNORECASE)
    
    def _mask_phone(self, text: str, pattern: str) -> str:
        """Mask phone numbers"""
        def replace_phone(match):
            phone = match.group()
            digits = re.sub(r'\D', '', phone)
            # Keep first 3 and last 2 digits
            if len(digits) >= 5:
                return f"{digits[:3]}-{self.masking_char * 3}-{digits[-2:]}"
            return self.masking_char * len(phone)
        
        return re.sub(pattern, replace_phone, text)
    
    def _mask_ssn(self, text: str, pattern: str) -> str:
        """Mask SSN"""
        return re.sub(pattern, lambda m: '***-**-' + m.group()[-4:], text)
    
    def _mask_credit_card(self, text: str, pattern: str) -> str:
        """Mask credit card numbers"""
        def replace_card(match):
            card = match.group()
            digits = re.sub(r'\D', '', card)
            # Keep first 4 and last 4 digits
            if len(digits) >= 8:
                return f"{digits[:4]}-{self.masking_char * 4}-{digits[-4:]}"
            return self.masking_char * len(card)
        
        return re.sub(pattern, replace_card, text)
    
    def _mask_ip_address(self, text: str, pattern: str) -> str:
        """Mask IP addresses"""
        def replace_ip(match):
            ip = match.group()
            # Keep first octet, mask rest
            parts = ip.split('.')
            if len(parts) == 4:
                return f"{parts[0]}.{self.masking_char * 3}.{self.masking_char * 3}.{self.masking_char * 3}"
            return self.masking_char * len(ip)
        
        return re.sub(pattern, replace_ip, text)
    
    def _mask_address(self, text: str, pattern: str) -> str:
        """Mask addresses"""
        return re.sub(pattern, lambda m: self.masking_char * 10 + m.group()[-10:], text)
    
    def anonymize_pii(self, text: str, method: str = 'hash') -> str:
        """
        Anonymize PII using specified method
        
        Args:
            text: Text to anonymize
            method: Anonymization method ('hash', 'pseudonym', 'synthetic')
            
        Returns:
            Anonymized text
        """
        detected_pii = self.detect_pii(text)
        anonymized_text = text
        
        for pii in detected_pii:
            if method == 'hash':
                replacement = self._hash_pii(pii['text'])
            elif method == 'pseudonym':
                replacement = self._generate_pseudonym(pii['category'])
            elif method == 'synthetic':
                replacement = self._generate_synthetic_data(pii['category'])
            else:
                replacement = self.masking_char * len(pii['text'])
            
            anonymized_text = anonymized_text.replace(pii['text'], replacement)
        
        return anonymized_text
    
    def _hash_pii(self, value: str) -> str:
        """Hash PII value for anonymization"""
        hash_obj = hashlib.sha256((value + self.hash_salt).encode())
        return hash_obj.hexdigest()[:16]  # Use first 16 chars
    
    def _generate_pseudonym(self, category: PIICategory) -> str:
        """Generate pseudonym for PII"""
        if category == PIICategory.EMAIL:
            domains = ['example.com', 'test.org', 'demo.net']
            return f"user{random.randint(1000, 9999)}@{random.choice(domains)}"
        elif category == PIICategory.PHONE:
            return f"{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
        elif category == PIICategory.SSN:
            return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        else:
            return f"ANON_{category.value.upper()}_{random.randint(1000, 9999)}"
    
    def _generate_synthetic_data(self, category: PIICategory) -> str:
        """Generate realistic synthetic data"""
        if category == PIICategory.EMAIL:
            first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones']
            domains = ['company.com', 'business.org', 'firm.net']
            return f"{random.choice(first_names).lower()}.{random.choice(last_names).lower()}@{random.choice(domains)}"
        elif category == PIICategory.PHONE:
            # Generate valid-looking US phone numbers
            area_codes = [201, 212, 213, 305, 312, 415, 617, 646, 718, 917]
            return f"{random.choice(area_codes)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}"
        elif category == PIICategory.SSN:
            # Generate SSN with valid format (not real numbers)
            return f"{random.randint(100, 899)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        else:
            return self._generate_pseudonym(category)
    
    def validate_credit_card(self, card_number: str) -> Dict[str, Any]:
        """
        Validate credit card number using Luhn algorithm
        
        Args:
            card_number: Credit card number to validate
            
        Returns:
            Validation result with card type
        """
        # Remove spaces and dashes
        digits = re.sub(r'[^0-9]', '', card_number)
        
        # Luhn algorithm
        def luhn_check(num):
            digits = [int(d) for d in num]
            checksum = 0
            reverse_digits = digits[::-1]
            
            for i, digit in enumerate(reverse_digits):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit
            
            return checksum % 10 == 0
        
        # Detect card type
        card_types = {
            'Visa': r'^4[0-9]{12}(?:[0-9]{3})?$',
            'Mastercard': r'^5[1-5][0-9]{14}$',
            'American Express': r'^3[47][0-9]{13}$',
            'Discover': r'^6(?:011|5[0-9]{2})[0-9]{12}$'
        }
        
        card_type = 'Unknown'
        for type_name, pattern in card_types.items():
            if re.match(pattern, digits):
                card_type = type_name
                break
        
        return {
            'valid': luhn_check(digits),
            'card_type': card_type,
            'length': len(digits),
            'masked': self.mask_pii(card_number, [PIICategory.CREDIT_CARD])
        }
    
    def create_data_privacy_report(self, data: Union[str, Dict, List]) -> Dict[str, Any]:
        """
        Create privacy report for data
        
        Args:
            data: Data to analyze
            
        Returns:
            Privacy analysis report
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        detected_pii = self.detect_pii(data_str)
        
        # Count by category
        category_counts = {}
        for pii in detected_pii:
            cat = pii['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Calculate sensitivity score
        sensitivity_scores = {
            PIICategory.EMAIL: 3,
            PIICategory.PHONE: 3,
            PIICategory.SSN: 5,
            PIICategory.CREDIT_CARD: 5,
            PIICategory.ADDRESS: 4,
            PIICategory.DATE_OF_BIRTH: 4,
            PIICategory.IP_ADDRESS: 2,
            PIICategory.MEDICAL_ID: 5,
            PIICategory.BANK_ACCOUNT: 5
        }
        
        total_sensitivity = sum(
            sensitivity_scores.get(PIICategory(cat), 1) * count 
            for cat, count in category_counts.items()
        )
        
        # Risk level
        if total_sensitivity >= 20:
            risk_level = 'HIGH'
        elif total_sensitivity >= 10:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'total_pii_instances': len(detected_pii),
            'category_breakdown': category_counts,
            'sensitivity_score': total_sensitivity,
            'risk_level': risk_level,
            'recommendations': self._get_recommendations(category_counts, risk_level),
            'masked_sample': self.mask_pii(data_str[:200] + '...' if len(data_str) > 200 else data_str)
        }
    
    def _get_recommendations(self, category_counts: Dict[str, int], risk_level: str) -> List[str]:
        """Get privacy protection recommendations"""
        recommendations = []
        
        if 'ssn' in category_counts:
            recommendations.append("Implement strong encryption for SSN data")
            recommendations.append("Restrict access to SSN with role-based controls")
        
        if 'credit_card' in category_counts:
            recommendations.append("Use tokenization for payment data")
            recommendations.append("Ensure PCI DSS compliance")
        
        if 'email' in category_counts:
            recommendations.append("Implement email encryption for sensitive communications")
        
        if 'phone' in category_counts:
            recommendations.append("Apply masking in user interfaces")
        
        if risk_level == 'HIGH':
            recommendations.append("Conduct privacy impact assessment")
            recommendations.append("Implement additional access controls")
            recommendations.append("Review data retention policies")
        
        return recommendations


class DataAnonymizer:
    """Advanced data anonymization for datasets"""
    
    def __init__(self):
        self.pii_protection = PIIProtection()
        
    def anonymize_dataset(self, data: List[Dict[str, Any]], 
                         method: str = 'hash') -> List[Dict[str, Any]]:
        """
        Anonymize entire dataset
        
        Args:
            data: List of records to anonymize
            method: Anonymization method
            
        Returns:
            Anonymized dataset
        """
        anonymized_data = []
        
        for record in data:
            anonymized_record = {}
            
            for field, value in record.items():
                if isinstance(value, str):
                    # Anonymize string values
                    anonymized_record[field] = self.pii_protection.anonymize_pii(value, method)
                else:
                    # Keep non-string values as-is
                    anonymized_record[field] = value
            
            anonymized_data.append(anonymized_record)
        
        return anonymized_data
    
    def pseudonymize_dataset(self, data: List[Dict[str, Any]]) -> tuple:
        """
        Create pseudonymized dataset with mapping
        
        Args:
            data: Original dataset
            
        Returns:
            Tuple of (pseudonymized_data, pseudonym_mapping)
        """
        pseudonymized_data = []
        pseudonym_mapping = {}
        
        for record in data:
            pseudonymized_record = {}
            
            for field, value in record.items():
                if isinstance(value, str):
                    detected_pii = self.pii_protection.detect_pii(value)
                    if detected_pii:
                        for pii in detected_pii:
                            pseudonym = self.pii_protection._generate_pseudonym(
                                PIICategory(pii['category'])
                            )
                            
                            # Create mapping
                            if pii['category'] not in pseudonym_mapping:
                                pseudonym_mapping[pii['category']] = {}
                            
                            pseudonym_mapping[pii['category']][value] = pseudonym
                            value = value.replace(pii['text'], pseudonym)
                    
                    pseudonymized_record[field] = value
                else:
                    pseudonymized_record[field] = value
            
            pseudonymized_data.append(pseudonymized_record)
        
        return pseudonymized_data, pseudonym_mapping
