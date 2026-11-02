# Technical Implementation Guide: Email Authentication for Phishing Detection Systems

## Table of Contents
1. [SPF Implementation Examples](#spf-implementation-examples)
2. [DKIM Implementation Examples](#dkim-implementation-examples)
3. [DMARC Implementation Examples](#dmarc-implementation-examples)
4. [Phishing Detection Algorithms](#phishing-detection-algorithms)
5. [Real-World Configuration Examples](#real-world-configuration-examples)
6. [Monitoring and Alerting Systems](#monitoring-and-alerting-systems)
7. [Integration with Security Tools](#integration-with-security-tools)

---

## SPF Implementation Examples

### DNS Record Examples

#### Basic SPF Configuration
```dns
example.com. IN TXT "v=spf1 ip4:192.0.2.0/24 include:_spf.google.com include:_spf.office365.com -all"
```

#### Complex SPF Configuration
```dns
example.com. IN TXT "v=spf1 \
  include:_spf.google.com \
  include:_spf.office365.com \
  include:amazonses.com \
  include:sendgrid.net \
  include:mailchimp.com \
  ip4:203.0.113.0/24 \
  ip4:198.51.100.0/24 \
  a \
  mx \
  ~all"
```

#### SPF Record Parsing Algorithm
```python
import re
import ipaddress

class SPFRecordParser:
    def __init__(self, spf_record):
        self.spf_record = spf_record
        self.mechanisms = self._parse_spf_record()
        self.errors = []
    
    def _parse_spf_record(self):
        """Parse SPF record into components"""
        mechanisms = []
        
        # Remove v=spf1 prefix
        if not self.spf_record.startswith('v=spf1'):
            self.errors.append("Missing or invalid version")
            return mechanisms
        
        # Extract mechanisms
        record_parts = self.spf_record.split()[1:]
        
        for part in record_parts:
            mechanism = self._parse_mechanism(part)
            if mechanism:
                mechanisms.append(mechanism)
        
        return mechanisms
    
    def _parse_mechanism(self, mechanism_str):
        """Parse individual SPF mechanism"""
        mechanism = {
            'type': None,
            'value': None,
            'qualifier': None
        }
        
        # Determine qualifier
        if mechanism_str.startswith('-'):
            mechanism['qualifier'] = 'fail'
            mechanism_str = mechanism_str[1:]
        elif mechanism_str.startswith('~'):
            mechanism['qualifier'] = 'softfail'
            mechanism_str = mechanism_str[1:]
        elif mechanism_str.startswith('+'):
            mechanism['qualifier'] = 'pass'
            mechanism_str = mechanism_str[1:]
        elif mechanism_str.startswith('?'):
            mechanism['qualifier'] = 'neutral'
            mechanism_str = mechanism_str[1:]
        else:
            mechanism['qualifier'] = 'pass'
        
        # Parse mechanism type
        if ':' in mechanism_str:
            mech_type, value = mechanism_str.split(':', 1)
            mechanism['type'] = mech_type
            mechanism['value'] = value
        else:
            mechanism['type'] = mechanism_str
            mechanism['value'] = None
        
        return mechanism
    
    def validate_sender(self, sender_ip, sender_domain, mail_from=None):
        """Validate sender IP against SPF record"""
        if not self.mechanisms:
            return {'result': 'error', 'reason': 'Invalid SPF record'}
        
        # Check all mechanisms in order
        for mechanism in self.mechanisms:
            result = self._check_mechanism(mechanism, sender_ip, sender_domain, mail_from)
            if result['matched']:
                return {
                    'result': result['qualifier'],
                    'mechanism': mechanism,
                    'matched_rule': result.get('matched_rule')
                }
        
        return {'result': 'neutral', 'reason': 'No match found'}

# Usage example
spf_record = "v=spf1 ip4:192.0.2.0/24 include:_spf.google.com ~all"
parser = SPFRecordParser(spf_record)
result = parser.validate_sender(
    sender_ip="192.0.2.10",
    sender_domain="example.com"
)
```

### SPF Vulnerability Detection

#### Invalid SPF Record Detection
```python
def detect_spf_vulnerabilities(spf_record):
    """Detect common SPF configuration vulnerabilities"""
    vulnerabilities = []
    
    # Check for all pass
    if " +all" in spf_record:
        vulnerabilities.append({
            'type': 'misconfiguration',
            'severity': 'critical',
            'description': 'SPF record uses "+all" which allows any server',
            'recommendation': 'Replace +all with -all or specific IP ranges'
        })
    
    # Check for too many DNS lookups
    lookup_count = spf_record.count('include:') + spf_record.count('exists:')
    if spf_record.count('a') > 0: lookup_count += 1
    if spf_record.count('mx') > 0: lookup_count += 1
    
    if lookup_count > 10:
        vulnerabilities.append({
            'type': 'performance',
            'severity': 'high',
            'description': f'SPF record has {lookup_count} DNS lookups, exceeds 10 limit',
            'recommendation': 'Reduce number of include statements or flatten SPF record'
        })
    
    # Check for softfail with policy -all
    if "~all" in spf_record and "-all" in spf_record:
        vulnerabilities.append({
            'type': 'inconsistency',
            'severity': 'medium',
            'description': 'SPF record contains both softfail and hardfail',
            'recommendation': 'Use consistent policy (either ~all or -all)'
        })
    
    return vulnerabilities
```

---

## DKIM Implementation Examples

### DKIM Key Generation
```bash
#!/bin/bash
# DKIM key generation script

DOMAIN=$1
SELECTOR=$2
KEY_SIZE=2048

if [ -z "$DOMAIN" ] || [ -z "$SELECTOR" ]; then
    echo "Usage: $0 <domain> <selector>"
    exit 1
fi

# Generate private key
openssl genrsa -out ${SELECTOR}_private.key ${KEY_SIZE}

# Generate public key
openssl rsa -in ${SELECTOR}_private.key -pubout -out ${SELECTOR}_public.key

# Extract public key for DNS
openssl rsa -in ${SELECTOR}_private.key -pubout -outform PEM | \
    openssl rsa -pubin -outform DER 2>/dev/null | \
    openssl base64 -A > ${SELECTOR}_public_base64.txt

echo "Private key generated: ${SELECTOR}_private.key"
echo "Public key generated: ${SELECTOR}_public.key"
echo "Base64 public key for DNS:"
cat ${SELECTOR}_public_base64.txt

# Generate DNS record
echo "DNS record to add:"
echo "${SELECTOR}._domainkey.${DOMAIN}. IN TXT \"v=DKIM1; k=rsa; p=$(cat ${SELECTOR}_public_base64.txt)\""
```

### DKIM-Signature Header Processing
```python
import base64
import re
import hashlib
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class DKIMProcessor:
    def __init__(self, dkim_signature, dkim_public_key):
        self.dkim_signature = dkim_signature
        self.dkim_public_key = dkim_public_key
        self.parsed_signature = self._parse_signature()
    
    def _parse_signature(self):
        """Parse DKIM-Signature header"""
        signature = {}
        
        # Extract key-value pairs
        parts = self.dkim_signature.replace('\r\n', '').replace('\n', '').split(';')
        
        for part in parts[1:]:  # Skip first empty part
            part = part.strip()
            if '=' in part:
                key, value = part.split('=', 1)
                signature[key.strip()] = value.strip()
        
        return signature
    
    def sign_message(self, headers, body, private_key):
        """Generate DKIM signature for message"""
        # Create canonicalized message
        canonicalized_message = self._canonicalize_message(headers, body)
        
        # Hash the canonicalized message
        message_hash = hashlib.sha256(canonicalized_message.encode()).digest()
        
        # Sign the hash
        signature = private_key.sign(
            message_hash,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        
        # Base64 encode the signature
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, headers, body, signature_data):
        """Verify DKIM signature"""
        try:
            # Get signature parameters
            a = self.parsed_signature.get('a', 'rsa-sha256')
            d = self.parsed_signature.get('d')  # domain
            s = self.parsed_signature.get('s')  # selector
            c = self.parsed_signature.get('c', 'relaxed/relaxed')  # canonicalization
            h = self.parsed_signature.get('h')  # signed headers
            
            # Validate parameters
            if a != 'rsa-sha256':
                return {'valid': False, 'reason': f'Unsupported algorithm: {a}'}
            
            if not d or not s:
                return {'valid': False, 'reason': 'Missing domain or selector'}
            
            # Create canonicalized message
            canonicalized_message = self._canonicalize_message(headers, body)
            
            # Hash the canonicalized message
            message_hash = hashlib.sha256(canonicalized_message.encode()).digest()
            
            # Verify signature
            signature_bytes = base64.b64decode(signature_data)
            public_key = serialization.load_pem_public_key(
                self.dkim_public_key.encode()
            )
            
            public_key.verify(
                signature_bytes,
                message_hash,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return {'valid': True, 'domain': d, 'selector': s}
            
        except Exception as e:
            return {'valid': False, 'reason': str(e)}
```

---

## DMARC Implementation Examples

### DMARC Record Validation
```python
import re
import ipaddress
from urllib.parse import urlparse

class DMARCRecordValidator:
    def __init__(self, dmarc_record):
        self.dmarc_record = dmarc_record
        self.record = self._parse_record()
        self.errors = []
        self.warnings = []
    
    def _parse_record(self):
        """Parse DMARC DNS record"""
        record = {}
        
        if not self.dmarc_record.startswith('v=DMARC1'):
            self.errors.append("Invalid DMARC version")
            return record
        
        # Parse all parameters
        params = self.dmarc_record.split(';')
        
        for param in params:
            param = param.strip()
            if '=' in param:
                key, value = param.split('=', 1)
                record[key] = value
        
        return record
    
    def validate_record(self):
        """Validate DMARC record configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'score': 0
        }
        
        # Check required fields
        if 'p' not in self.record:
            validation_result['errors'].append("Missing required policy (p) parameter")
            validation_result['valid'] = False
        
        # Validate policy
        if 'p' in self.record:
            policy = self.record['p']
            if policy not in ['none', 'quarantine', 'reject']:
                validation_result['errors'].append(f"Invalid policy: {policy}")
                validation_result['valid'] = False
        
        # Check for strict alignment when policy is reject
        if self.record.get('p') == 'reject':
            if self.record.get('adkim') == 'r' or self.record.get('aspf') == 'r':
                validation_result['warnings'].append(
                    "Consider using strict alignment (s) for reject policy"
                )
        
        # Validate report URIs
        for report_type in ['rua', 'ruf']:
            if report_type in self.record:
                uri = self.record[report_type]
                if not uri.startswith('mailto:'):
                    validation_result['errors'].append(
                        f"Invalid {report_type} URI format: must use mailto:"
                    )
        
        # Check percentage settings
        pct = self.record.get('pct', '100')
        try:
            pct_value = int(pct)
            if not 1 <= pct_value <= 100:
                validation_result['errors'].append(
                    f"Invalid percentage: {pct_value} (must be 1-100)"
                )
        except ValueError:
            validation_result['errors'].append(f"Invalid percentage format: {pct}")
        
        return validation_result

# Example usage
dmarc_record = "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com; sp=reject; adkim=s; aspf=s; pct=100"
validator = DMARCRecordValidator(dmarc_record)
result = validator.validate_record()
```

### DMARC Report Analysis
```python
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict

class DMARCReportAnalyzer:
    def __init__(self, report_xml_content):
        self.report_xml = report_xml_content
        self.parsed_report = self._parse_xml()
        self.analysis = {}
    
    def _parse_xml(self):
        """Parse DMARC XML report"""
        try:
            root = ET.fromstring(self.report_xml)
            return {
                'policy_published': self._parse_policy_published(root),
                'records': self._parse_records(root),
                'metadata': self._parse_metadata(root)
            }
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML format: {e}")
    
    def _parse_policy_published(self, root):
        """Parse policy_published section"""
        policy_elem = root.find('.//policy_published')
        if policy_elem is None:
            return {}
        
        return {
            'domain': policy_elem.findtext('domain'),
            'p': policy_elem.findtext('p'),
            'sp': policy_elem.findtext('sp'),
            'adkim': policy_elem.findtext('adkim'),
            'aspf': policy_elem.findtext('aspf')
        }
    
    def _parse_records(self, root):
        """Parse all records from report"""
        records = []
        record_elems = root.findall('.//record')
        
        for record_elem in record_elems:
            record = {
                'row': self._parse_row(record_elem),
                'identifiers': self._parse_identifiers(record_elem),
                'auth_results': self._parse_auth_results(record_elem)
            }
            records.append(record)
        
        return records
    
    def _parse_row(self, record_elem):
        """Parse row element containing IP and counts"""
        row_elem = record_elem.find('row')
        if row_elem is None:
            return {}
        
        source_elem = row_elem.find('source_ip')
        count_elem = row_elem.find('count')
        
        return {
            'source_ip': source_elem.text if source_elem is not None else None,
            'count': int(count_elem.text) if count_elem is not None else 0
        }
    
    def _parse_identifiers(self, record_elem):
        """Parse identifiers section"""
        identifiers_elem = record_elem.find('identifiers')
        if identifiers_elem is None:
            return {}
        
        return {
            'header_from': identifiers_elem.findtext('header_from'),
            'envelope_from': identifiers_elem.findtext('envelope_from'),
            'envelope_to': identifiers_elem.findtext('envelope_to')
        }
    
    def _parse_auth_results(self, record_elem):
        """Parse authentication results"""
        auth_results_elem = record_elem.find('auth_results')
        if auth_results_elem is None:
            return {}
        
        auth_results = {}
        
        # Parse SPF result
        spf_elem = auth_results_elem.find('spf')
        if spf_elem is not None:
            auth_results['spf'] = {
                'domain': spf_elem.findtext('domain'),
                'result': spf_elem.findtext('result')
            }
        
        # Parse DKIM results
        dkim_results = []
        dkim_elems = auth_results_elem.findall('dkim')
        for dkim_elem in dkim_elems:
            dkim_results.append({
                'domain': dkim_elem.findtext('domain'),
                'result': dkim_elem.findtext('result'),
                'selector': dkim_elem.findtext('selector')
            })
        auth_results['dkim'] = dkim_results
        
        return auth_results
    
    def generate_threat_intelligence(self):
        """Generate threat intelligence from DMARC report"""
        threat_data = {
            'malicious_sources': [],
            'failed_authentication': [],
            'suspicious_domains': [],
            'statistics': {}
        }
        
        # Analyze each record
        for record in self.parsed_report['records']:
            row = record['row']
            auth_results = record['auth_results']
            identifiers = record['identifiers']
            
            # Check for failed authentication
            spf_pass = auth_results.get('spf', {}).get('result') == 'pass'
            dkim_pass = any(dkim.get('result') == 'pass' for dkim in auth_results.get('dkim', []))
            
            if not spf_pass and not dkim_pass:
                threat_data['failed_authentication'].append({
                    'source_ip': row['source_ip'],
                    'source_count': row['count'],
                    'header_from': identifiers.get('header_from'),
                    'envelope_from': identifiers.get('envelope_from'),
                    'spf_result': auth_results.get('spf', {}).get('result', 'unknown'),
                    'dkim_results': [dkim.get('result', 'unknown') for dkim in auth_results.get('dkim', [])]
                })
                
                # Add to malicious sources if high volume
                if row['count'] > 10:
                    threat_data['malicious_sources'].append({
                        'ip': row['source_ip'],
                        'volume': row['count'],
                        'domain': identifiers.get('header_from'),
                        'severity': 'high' if row['count'] > 100 else 'medium'
                    })
        
        # Calculate statistics
        total_records = len(threat_data['failed_authentication'])
        unique_ips = len(set(record['source_ip'] for record in threat_data['failed_authentication']))
        
        threat_data['statistics'] = {
            'total_failed_records': total_records,
            'unique_malicious_ips': unique_ips,
            'high_volume_sources': len(threat_data['malicious_sources'])
        }
        
        return threat_data
```

---

## Phishing Detection Algorithms

### Multi-Layer Detection System
```python
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class EmailPhishingDetector:
    def __init__(self, config):
        self.config = config
        self.threat_intelligence = ThreatIntelligence()
        self.auth_validator = EmailAuthenticationValidator()
        
    def analyze_email(self, email_data: Dict) -> Dict:
        """Comprehensive phishing detection analysis"""
        analysis_result = {
            'email_id': email_data.get('message_id'),
            'timestamp': datetime.now().isoformat(),
            'risk_score': 0,
            'risk_factors': [],
            'authentication_results': {},
            'threat_indicators': [],
            'recommendation': 'deliver'
        }
        
        # Layer 1: Email Authentication Analysis
        auth_analysis = self._analyze_email_authentication(email_data)
        analysis_result['authentication_results'] = auth_analysis
        
        # Layer 2: Content Analysis
        content_analysis = self._analyze_email_content(email_data)
        
        # Layer 3: Behavioral Analysis
        behavioral_analysis = self._analyze_sender_behavior(email_data)
        
        # Layer 4: Threat Intelligence Check
        ti_analysis = self._check_threat_intelligence(email_data)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(
            auth_analysis, content_analysis, 
            behavioral_analysis, ti_analysis
        )
        analysis_result['risk_score'] = risk_score
        
        # Generate recommendation
        analysis_result['recommendation'] = self._generate_recommendation(risk_score)
        
        return analysis_result
    
    def _analyze_email_authentication(self, email_data: Dict) -> Dict:
        """Analyze email authentication results"""
        spf_result = email_data.get('spf_result', {})
        dkim_result = email_data.get('dkim_result', {})
        dmarc_result = email_data.get('dmarc_result', {})
        
        analysis = {
            'spf': self._evaluate_spf_result(spf_result),
            'dkim': self._evaluate_dkim_result(dkim_result),
            'dmarc': self._evaluate_dmarc_result(dmarc_result)
        }
        
        # Check domain alignment
        analysis['domain_alignment'] = self._check_domain_alignment(email_data)
        
        return analysis
    
    def _evaluate_spf_result(self, spf_result: Dict) -> Dict:
        """Evaluate SPF authentication result"""
        result = spf_result.get('result', 'unknown')
        
        evaluation = {
            'status': result,
            'risk_contribution': 0,
            'issues': []
        }
        
        if result == 'fail':
            evaluation['risk_contribution'] = 30
            evaluation['issues'].append('SPF authentication failed - potential spoofing')
        elif result == 'softfail':
            evaluation['risk_contribution'] = 15
            evaluation['issues'].append('SPF softfail - suspicious sender')
        elif result == 'pass':
            evaluation['risk_contribution'] = -5
        elif result == 'neutral':
            evaluation['risk_contribution'] = 5
            evaluation['issues'].append('SPF neutral - no clear policy')
        
        return evaluation
    
    def _evaluate_dkim_result(self, dkim_result: Dict) -> Dict:
        """Evaluate DKIM authentication result"""
        result = dkim_result.get('result', 'unknown')
        
        evaluation = {
            'status': result,
            'risk_contribution': 0,
            'issues': []
        }
        
        if result == 'fail':
            evaluation['risk_contribution'] = 35
            evaluation['issues'].append('DKIM authentication failed - message integrity compromised')
        elif result == 'pass':
            evaluation['risk_contribution'] = -10
        elif result == 'missing':
            evaluation['risk_contribution'] = 20
            evaluation['issues'].append('Missing DKIM signature')
        
        return evaluation
    
    def _evaluate_dmarc_result(self, dmarc_result: Dict) -> Dict:
        """Evaluate DMARC policy and result"""
        result = dmarc_result.get('result', 'unknown')
        policy = dmarc_result.get('policy', 'none')
        
        evaluation = {
            'status': result,
            'policy': policy,
            'risk_contribution': 0,
            'issues': []
        }
        
        if result == 'fail':
            evaluation['risk_contribution'] = 40
            evaluation['issues'].append('DMARC authentication failed - domain spoofing detected')
            
            # Increase risk if policy is set to none
            if policy == 'none':
                evaluation['risk_contribution'] += 10
                evaluation['issues'].append('DMARC policy set to none - no enforcement')
        elif result == 'pass':
            evaluation['risk_contribution'] = -15
        
        return evaluation
    
    def _check_domain_alignment(self, email_data: Dict) -> Dict:
        """Check domain alignment for SPF and DKIM"""
        from_domain = email_data.get('from_domain')
        spf_domain = email_data.get('spf_domain')
        dkim_domain = email_data.get('dkim_domain')
        
        alignment = {
            'spf_aligned': False,
            'dkim_aligned': False,
            'overall_aligned': False,
            'issues': []
        }
        
        # Check SPF alignment
        if from_domain and spf_domain:
            alignment['spf_aligned'] = self._domains_align(from_domain, spf_domain)
            if not alignment['spf_aligned']:
                alignment['issues'].append('SPF domain misalignment')
        
        # Check DKIM alignment
        if from_domain and dkim_domain:
            alignment['dkim_aligned'] = self._domains_align(from_domain, dkim_domain)
            if not alignment['dkim_aligned']:
                alignment['issues'].append('DKIM domain misalignment')
        
        # Overall alignment (at least one must align)
        alignment['overall_aligned'] = alignment['spf_aligned'] or alignment['dkim_aligned']
        
        return alignment
    
    def _domains_align(self, domain1: str, domain2: str) -> bool:
        """Check if two domains align (organizational domain match)"""
        def get_org_domain(domain):
            # Simple organizational domain extraction
            parts = domain.lower().split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])  # Return last two parts
            return domain.lower()
        
        return get_org_domain(domain1) == get_org_domain(domain2)
    
    def _analyze_email_content(self, email_data: Dict) -> Dict:
        """Analyze email content for phishing indicators"""
        analysis = {
            'suspicious_links': [],
            'social_engineering_indicators': [],
            'attachment_indicators': [],
            'risk_contribution': 0
        }
        
        # Analyze subject line
        subject = email_data.get('subject', '')
        if self._contains_suspicious_subject_keywords(subject):
            analysis['risk_contribution'] += 10
        
        # Analyze email body
        body = email_data.get('body', '')
        if self._contains_suspicious_body_keywords(body):
            analysis['risk_contribution'] += 15
        
        # Analyze attachments
        attachments = email_data.get('attachments', [])
        for attachment in attachments:
            if attachment.get('type') in ['.exe', '.scr', '.js']:
                analysis['risk_contribution'] += 25
                analysis['attachment_indicators'].append(f"Suspicious attachment: {attachment.get('filename')}")
        
        return analysis
    
    def _analyze_sender_behavior(self, email_data: Dict) -> Dict:
        """Analyze sender behavior patterns"""
        analysis = {
            'first_time_sender': False,
            'high_volume_sender': False,
            'geographic_anomaly': False,
            'time_anomaly': False,
            'risk_contribution': 0
        }
        
        sender_email = email_data.get('from_email')
        sender_ip = email_data.get('sender_ip')
        
        # Check if first time sender
        if not self._is_known_sender(sender_email):
            analysis['first_time_sender'] = True
            analysis['risk_contribution'] += 15
        
        # Check geographic anomalies
        if self._is_suspicious_geography(sender_ip):
            analysis['geographic_anomaly'] = True
            analysis['risk_contribution'] += 10
        
        # Check time anomalies
        if self._is_unusual_send_time(email_data.get('timestamp')):
            analysis['time_anomaly'] = True
            analysis['risk_contribution'] += 5
        
        return analysis
    
    def _check_threat_intelligence(self, email_data: Dict) -> Dict:
        """Check against threat intelligence feeds"""
        analysis = {
            'malicious_ip': False,
            'malicious_domain': False,
            'known_phishing_campaign': False,
            'risk_contribution': 0
        }
        
        sender_ip = email_data.get('sender_ip')
        from_domain = email_data.get('from_domain')
        
        # Check IP reputation
        if self.threat_intelligence.is_malicious_ip(sender_ip):
            analysis['malicious_ip'] = True
            analysis['risk_contribution'] += 50
        
        # Check domain reputation
        if self.threat_intelligence.is_malicious_domain(from_domain):
            analysis['malicious_domain'] = True
            analysis['risk_contribution'] += 40
        
        # Check against known phishing campaigns
        if self.threat_intelligence.is_known_campaign(email_data):
            analysis['known_phishing_campaign'] = True
            analysis['risk_contribution'] += 30
        
        return analysis
    
    def _calculate_risk_score(self, auth_analysis, content_analysis, behavioral_analysis, ti_analysis) -> int:
        """Calculate overall email risk score"""
        total_score = 0
        
        # Authentication contribution
        total_score += auth_analysis['spf']['risk_contribution']
        total_score += auth_analysis['dkim']['risk_contribution']
        total_score += auth_analysis['dmarc']['risk_contribution']
        
        # Domain alignment penalty
        if not auth_analysis['domain_alignment']['overall_aligned']:
            total_score += 20
        
        # Content analysis contribution
        total_score += content_analysis['risk_contribution']
        
        # Behavioral analysis contribution
        total_score += behavioral_analysis['risk_contribution']
        
        # Threat intelligence contribution
        total_score += ti_analysis['risk_contribution']
        
        # Cap score at 100
        return min(total_score, 100)
    
    def _generate_recommendation(self, risk_score: int) -> str:
        """Generate email handling recommendation based on risk score"""
        if risk_score >= 80:
            return 'reject'
        elif risk_score >= 60:
            return 'quarantine'
        elif risk_score >= 30:
            return 'flag_and_deliver'
        else:
            return 'deliver'

class ThreatIntelligence:
    """Mock threat intelligence feed"""
    
    def __init__(self):
        self.malicious_ips = {
            '192.0.2.100': 'known_phishing_server',
            '198.51.100.200': 'malware_distribution',
        }
        self.malicious_domains = {
            'malicious-site.com': 'phishing_campaign',
            'fake-login.net': 'credential_harvesting',
        }
    
    def is_malicious_ip(self, ip_address: str) -> bool:
        return ip_address in self.malicious_ips
    
    def is_malicious_domain(self, domain: str) -> bool:
        return domain in self.malicious_domains
    
    def is_known_campaign(self, email_data: Dict) -> bool:
        # Check for known phishing campaign indicators
        subject = email_data.get('subject', '').lower()
        return 'urgent' in subject and 'password' in subject

# Example usage
email_sample = {
    'message_id': '<abc123@example.com>',
    'from_email': 'sender@example.com',
    'from_domain': 'example.com',
    'subject': 'Urgent: Password Reset Required',
    'sender_ip': '192.0.2.10',
    'spf_result': {'result': 'fail'},
    'dkim_result': {'result': 'missing'},
    'dmarc_result': {'result': 'fail', 'policy': 'none'},
    'timestamp': datetime.now().isoformat(),
    'body': 'Please click here to reset your password immediately...',
    'attachments': []
}

detector = EmailPhishingDetector({})
result = detector.analyze_email(email_sample)
print(json.dumps(result, indent=2))
```

---

## Real-World Configuration Examples

### Microsoft 365 Email Authentication
```powershell
# PowerShell script for Microsoft 365 SPF configuration
Import-Module ExchangeOnlineManagement

# Connect to Exchange Online
Connect-ExchangeOnline -Credential $credentials

# Set SPF record
$spfRecord = "v=spf1 include:spf.protection.outlook.com include:_spf.google.com -all"

# Create or update SPF record using Azure DNS
az network dns record-set txt add `
  --resource-group "EmailResourceGroup" `
  --zone-name "yourdomain.com" `
  --record-set-name "@" `
  --value $spfRecord

# Configure DKIM for Microsoft 365
Enable-DkimSigningConfig -Identity "yourdomain.com"

# Configure DMARC policy
$dmarcRecord = "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; fo=1; pct=25; adkim=s; aspf=s"
az network dns record-set txt add `
  --resource-group "EmailResourceGroup" `
  --zone-name "yourdomain.com" `
  --record-set-name "_dmarc" `
  --value $dmarcRecord
```

### Google Workspace Email Authentication
```bash
#!/bin/bash
# Google Workspace email authentication setup script

DOMAIN="yourdomain.com"
SELECTOR="google"
SPF_RECORD='v=spf1 include:_spf.google.com -all'

# Add SPF record
gcloud dns record-sets create --zone="$DOMAIN" \
  --name="$DOMAIN." \
  --type="TXT" \
  --ttl="300" \
  --data="$SPF_RECORD"

# DMARC record
DMARC_RECORD='v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; adkim=s; aspf=s; pct=25'

gcloud dns record-sets create --zone="$DOMAIN" \
  --name="_dmarc.$DOMAIN." \
  --type="TXT" \
  --ttl="300" \
  --data="$DMARC_RECORD"

# DKIM will be automatically configured via Google Admin Console
```

### Cloudflare Email Security Configuration
```python
# Cloudflare API script for email authentication
import requests
import json

class CloudflareEmailAuth:
    def __init__(self, api_token, zone_id):
        self.api_token = api_token
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_spf_record(self, spf_record):
        """Create SPF TXT record"""
        data = {
            "type": "TXT",
            "name": "@",
            "content": spf_record,
            "ttl": 300
        }
        
        response = requests.post(
            f"{self.base_url}/zones/{self.zone_id}/dns_records",
            headers=self.headers,
            json=data
        )
        
        return response.json()
    
    def create_dkim_record(self, selector, public_key):
        """Create DKIM TXT record"""
        data = {
            "type": "TXT",
            "name": f"{selector}._domainkey",
            "content": f"v=DKIM1; k=rsa; p={public_key}",
            "ttl": 300
        }
        
        response = requests.post(
            f"{self.base_url}/zones/{self.zone_id}/dns_records",
            headers=self.headers,
            json=data
        )
        
        return response.json()
    
    def create_dmarc_record(self, dmarc_record):
        """Create DMARC TXT record"""
        data = {
            "type": "TXT",
            "name": "_dmarc",
            "content": dmarc_record,
            "ttl": 300
        }
        
        response = requests.post(
            f"{self.base_url}/zones/{self.zone_id}/dns_records",
            headers=self.headers,
            json=data
        )
        
        return response.json()

# Usage example
cf_api = CloudflareEmailAuth("YOUR_API_TOKEN", "YOUR_ZONE_ID")

# Create SPF record
spf_result = cf_api.create_spf_record("v=spf1 include:_spf.google.com -all")

# Create DMARC record
dmarc_record = "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; fo=1; adkim=s; aspf=s; pct=100"
dmarc_result = cf_api.create_dmarc_record(dmarc_record)
```

---

## Monitoring and Alerting Systems

### Real-time DMARC Monitoring System
```python
import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import json

class DMARCMonitor:
    def __init__(self, config):
        self.config = config
        self.alert_thresholds = {
            'failure_rate': 0.05,  # Alert if >5% failure rate
            'high_volume_sources': 10,  # Alert if >10 high-volume failures
            'new_malicious_domains': 1   # Alert on any new malicious domain
        }
    
    async def monitor_dmarc_reports(self):
        """Monitor DMARC reports for real-time alerts"""
        while True:
            try:
                # Check for new DMARC reports
                new_reports = await self.fetch_new_reports()
                
                for report in new_reports:
                    analysis = await self.analyze_report(report)
                    
                    if self.should_alert(analysis):
                        await self.send_alert(analysis)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def analyze_report(self, report_data):
        """Analyze DMARC report for threats"""
        analysis = {
            'report_id': report_data.get('id'),
            'domain': report_data.get('domain'),
            'analysis_time': datetime.now().isoformat(),
            'failure_statistics': {},
            'threat_indicators': [],
            'recommendations': []
        }
        
        # Calculate failure rates
        total_emails = sum(record.get('count', 0) for record in report_data.get('records', []))
        failed_emails = sum(
            record.get('count', 0) 
            for record in report_data.get('records', [])
            if not self.is_authentication_passed(record)
        )
        
        failure_rate = failed_emails / total_emails if total_emails > 0 else 0
        analysis['failure_statistics'] = {
            'total_emails': total_emails,
            'failed_emails': failed_emails,
            'failure_rate': failure_rate
        }
        
        # Identify threat indicators
        for record in report_data.get('records', []):
            if not self.is_authentication_passed(record):
                threat_indicator = self.analyze_record_threats(record)
                if threat_indicator:
                    analysis['threat_indicators'].append(threat_indicator)
        
        return analysis
    
    def is_authentication_passed(self, record):
        """Check if record shows passed authentication"""
        auth_results = record.get('auth_results', {})
        
        spf_pass = auth_results.get('spf', {}).get('result') == 'pass'
        dkim_pass = any(
            dkim.get('result') == 'pass' 
            for dkim in auth_results.get('dkim', [])
        )
        
        return spf_pass or dkim_pass
    
    def analyze_record_threats(self, record):
        """Analyze individual record for threat indicators"""
        threats = []
        
        row = record.get('row', {})
        auth_results = record.get('auth_results', {})
        identifiers = record.get('identifiers', {})
        
        # High volume attacks
        if row.get('count', 0) > 100:
            threats.append({
                'type': 'high_volume_attack',
                'severity': 'high',
                'source_ip': row.get('source_ip'),
                'volume': row.get('count'),
                'domain': identifiers.get('header_from')
            })
        
        # Complete authentication failure
        spf_result = auth_results.get('spf', {}).get('result', 'unknown')
        dkim_results = [dkim.get('result') for dkim in auth_results.get('dkim', [])]
        
        if spf_result in ['fail', 'softfail'] and all(
            result in ['fail', 'missing'] for result in dkim_results
        ):
            threats.append({
                'type': 'complete_authentication_failure',
                'severity': 'medium',
                'source_ip': row.get('source_ip'),
                'spf_result': spf_result,
                'dkim_results': dkim_results
            })
        
        return threats if threats else None
    
    def should_alert(self, analysis):
        """Determine if analysis warrants an alert"""
        failure_rate = analysis['failure_statistics']['failure_rate']
        threat_count = len(analysis['threat_indicators'])
        
        return (
            failure_rate > self.alert_thresholds['failure_rate'] or
            threat_count > self.alert_thresholds['new_malicious_domains']
        )
    
    async def send_alert(self, analysis):
        """Send alert notification"""
        alert_message = self.create_alert_message(analysis)
        
        if self.config.get('slack_webhook'):
            await self.send_slack_alert(alert_message)
        
        if self.config.get('email_alerts'):
            await self.send_email_alert(alert_message)
    
    def create_alert_message(self, analysis):
        """Create formatted alert message"""
        return {
            'title': f"DMARC Alert: {analysis['domain']}",
            'severity': self.calculate_severity(analysis),
            'summary': f"Failure rate: {analysis['failure_statistics']['failure_rate']:.2%}",
            'details': analysis,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_severity(self, analysis):
        """Calculate alert severity"""
        failure_rate = analysis['failure_statistics']['failure_rate']
        
        if failure_rate > 0.2 or len(analysis['threat_indicators']) > 5:
            return 'critical'
        elif failure_rate > 0.1 or len(analysis['threat_indicators']) > 2:
            return 'high'
        else:
            return 'medium'
```

---

## Integration with Security Tools

### SIEM Integration Example
```python
import json
import logging
from datetime import datetime

class EmailSecuritySIEMIntegration:
    def __init__(self, siem_config):
        self.siem_config = siem_config
        self.logger = logging.getLogger('email_security.siem')
    
    def send_authentication_event(self, auth_result):
        """Send email authentication event to SIEM"""
        event = {
            'event_type': 'email_authentication',
            'timestamp': datetime.now().isoformat(),
            'source': 'email_security_system',
            'severity': self.calculate_severity(auth_result),
            'data': {
                'message_id': auth_result.get('message_id'),
                'from_domain': auth_result.get('from_domain'),
                'source_ip': auth_result.get('source_ip'),
                'spf_result': auth_result.get('authentication_results', {}).get('spf', {}).get('status'),
                'dkim_result': auth_result.get('authentication_results', {}).get('dkim', {}).get('status'),
                'dmarc_result': auth_result.get('authentication_results', {}).get('dmarc', {}).get('status'),
                'domain_alignment': auth_result.get('authentication_results', {}).get('domain_alignment', {}),
                'risk_score': auth_result.get('risk_score'),
                'recommendation': auth_result.get('recommendation')
            }
        }
        
        # Send to different SIEM platforms
        if self.siem_config.get('splunk'):
            self.send_to_splunk(event)
        
        if self.siem_config.get('elastic'):
            self.send_to_elastic(event)
        
        if self.siem_config.get('qradar'):
            self.send_to_qradar(event)
    
    def calculate_severity(self, auth_result):
        """Calculate event severity for SIEM"""
        risk_score = auth_result.get('risk_score', 0)
        
        if risk_score >= 80:
            return 'critical'
        elif risk_score >= 60:
            return 'high'
        elif risk_score >= 30:
            return 'medium'
        else:
            return 'low'
    
    def send_to_splunk(self, event):
        """Send event to Splunk"""
        # Implement Splunk HTTP Event Collector integration
        splunk_endpoint = self.siem_config['splunk']['hec_endpoint']
        token = self.siem_config['splunk']['token']
        
        headers = {
            'Authorization': f'Splunk {token}',
            'Content-Type': 'application/json'
        }
        
        # Send event to Splunk
        # implementation details...
    
    def send_to_elastic(self, event):
        """Send event to Elasticsearch"""
        # Implement Elasticsearch integration
        elastic_endpoint = self.siem_config['elastic']['endpoint']
        index = self.siem_config['elastic']['index']
        
        # Send event to Elasticsearch
        # implementation details...
```

This comprehensive technical implementation guide provides practical examples, code snippets, and real-world configurations for implementing email authentication protocols in phishing detection systems. The examples include proper error handling, security considerations, and integration patterns for enterprise environments.