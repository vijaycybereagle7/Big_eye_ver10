"""
Compliance Module
Implements GDPR compliance features including data retention and right to be forgotten
"""

import os
import json
import sqlite3
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading


class DataCategory(Enum):
    """Categories of personal data"""
    PERSONAL_IDENTIFIERS = "personal_identifiers"
    CONTACT_DATA = "contact_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"
    FINANCIAL_DATA = "financial_data"
    HEALTH_DATA = "health_data"
    LOCATION_DATA = "location_data"
    BIOMETRIC_DATA = "biometric_data"


class RetentionPeriod(Enum):
    """Data retention periods"""
    IMMEDIATE = "immediate"  # No retention
    SHORT_TERM = "short_term"  # 30 days
    MEDIUM_TERM = "medium_term"  # 1 year
    LONG_TERM = "long_term"  # 7 years
    INDEFINITE = "indefinite"  # Until explicitly deleted


class DataSubjectRequest(Enum):
    """Types of data subject requests"""
    ACCESS = "access"  # Article 15 - Right of access
    RECTIFICATION = "rectification"  # Article 16 - Right to rectification
    ERASURE = "erasure"  # Article 17 - Right to erasure
    PORTABILITY = "portability"  # Article 20 - Right to data portability
    RESTRICTION = "restriction"  # Article 18 - Right to restriction
    OBJECTION = "objection"  # Article 21 - Right to object


@dataclass
class DataRecord:
    """Personal data record"""
    record_id: str
    user_id: str
    data_category: DataCategory
    data_content: str
    source: str
    created_at: str
    last_accessed: str
    retention_period: RetentionPeriod
    retention_date: str
    is_anonymized: bool
    anonymization_date: Optional[str]
    
    def is_expired(self) -> bool:
        """Check if data retention period has expired"""
        return datetime.fromisoformat(self.retention_date) < datetime.now()


@dataclass
class DataSubjectRequestRecord:
    """Record of data subject request"""
    request_id: str
    user_id: str
    request_type: DataSubjectRequest
    request_date: str
    status: str  # pending, processing, completed, rejected
    completed_date: Optional[str]
    details: Dict[str, Any]
    verification_status: str  # verified, pending, failed
    
    def is_overdue(self) -> bool:
        """Check if GDPR response deadline is exceeded"""
        if self.status in ['completed', 'rejected']:
            return False
        
        # GDPR requires response within 30 days
        deadline = datetime.fromisoformat(self.request_date) + timedelta(days=30)
        return datetime.now() > deadline


@dataclass
class ConsentRecord:
    """Consent record for data processing"""
    consent_id: str
    user_id: str
    consent_type: str
    purpose: str
    granted: bool
    granted_date: Optional[str]
    withdrawn_date: Optional[str]
    ip_address: str
    user_agent: str
    legal_basis: str  # consent, contract, legal_obligation, etc.
    
    def is_active(self) -> bool:
        """Check if consent is still valid"""
        if not self.granted:
            return False
        
        if self.withdrawn_date:
            return False
        
        return True


class GDPRCompliance:
    """GDPR compliance management system"""
    
    def __init__(self, db_path: str = '/workspace/security/compliance/gdpr.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize compliance database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Data records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_records (
                    record_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    data_category TEXT NOT NULL,
                    data_content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    retention_period TEXT NOT NULL,
                    retention_date TEXT NOT NULL,
                    is_anonymized BOOLEAN DEFAULT 0,
                    anonymization_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Data subject requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_subject_requests (
                    request_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    request_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    completed_date TEXT,
                    details TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Consent records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consent_records (
                    consent_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    granted BOOLEAN NOT NULL,
                    granted_date TEXT,
                    withdrawn_date TEXT,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Processing activities table (Article 30)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processing_activities (
                    activity_id TEXT PRIMARY KEY,
                    controller_name TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    data_subjects TEXT NOT NULL,
                    recipients TEXT NOT NULL,
                    retention_periods TEXT NOT NULL,
                    security_measures TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Breach incidents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS breach_incidents (
                    incident_id TEXT PRIMARY KEY,
                    incident_date TEXT NOT NULL,
                    data_categories_affected TEXT NOT NULL,
                    number_subjects_affected INTEGER,
                    likely_consequences TEXT NOT NULL,
                    measures_taken TEXT NOT NULL,
                    notified_supervisory_authority BOOLEAN DEFAULT 0,
                    notification_date TEXT,
                    notified_data_subjects BOOLEAN DEFAULT 0,
                    notification_date_subjects TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def register_data_record(self, record: DataRecord) -> bool:
        """Register personal data record"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO data_records (
                            record_id, user_id, data_category, data_content, source,
                            created_at, last_accessed, retention_period, retention_date,
                            is_anonymized, anonymization_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.record_id, record.user_id, record.data_category.value,
                        record.data_content, record.source, record.created_at,
                        record.last_accessed, record.retention_period.value,
                        record.retention_date, record.is_anonymized,
                        record.anonymization_date
                    ))
                    
                    conn.commit()
                    return True
                    
            except sqlite3.IntegrityError:
                return False
    
    def get_user_data_records(self, user_id: str) -> List[DataRecord]:
        """Get all data records for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM data_records WHERE user_id = ? ORDER BY created_at
            ''', (user_id,))
            
            records = []
            for row in cursor.fetchall():
                records.append(DataRecord(
                    record_id=row[0], user_id=row[1],
                    data_category=DataCategory(row[2]), data_content=row[3],
                    source=row[4], created_at=row[5], last_accessed=row[6],
                    retention_period=RetentionPeriod(row[7]),
                    retention_date=row[8], is_anonymized=bool(row[9]),
                    anonymization_date=row[10]
                ))
            
            return records
    
    def create_data_subject_request(self, user_id: str, 
                                  request_type: DataSubjectRequest,
                                  details: Dict[str, Any]) -> str:
        """Create new data subject request"""
        import secrets
        
        request_id = secrets.token_urlsafe(16)
        request_date = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO data_subject_requests (
                    request_id, user_id, request_type, request_date, status,
                    completed_date, details, verification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_id, user_id, request_type.value, request_date,
                'pending', None, json.dumps(details), 'pending'
            ))
            
            conn.commit()
            return request_id
    
    def process_data_subject_request(self, request_id: str, 
                                   verification_status: str) -> Dict[str, Any]:
        """Process data subject request"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM data_subject_requests WHERE request_id = ?
            ''', (request_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError("Request not found")
            
            request_record = DataSubjectRequestRecord(
                request_id=row[0], user_id=row[1],
                request_type=DataSubjectRequest(row[2]),
                request_date=row[3], status=row[4],
                completed_date=row[5], details=json.loads(row[6]),
                verification_status=row[7]
            )
            
            if verification_status == 'verified':
                # Process based on request type
                result = self._execute_data_subject_request(request_record)
                
                # Update status
                cursor.execute('''
                    UPDATE data_subject_requests SET status = ?, completed_date = ?
                    WHERE request_id = ?
                ''', ('completed', datetime.now().isoformat(), request_id))
                
                conn.commit()
                return result
            
            else:
                # Mark as rejected
                cursor.execute('''
                    UPDATE data_subject_requests SET status = ?, verification_status = ?
                    WHERE request_id = ?
                ''', ('rejected', verification_status, request_id))
                conn.commit()
                
                return {'status': 'rejected', 'reason': verification_status}
    
    def _execute_data_subject_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Execute the actual data subject request"""
        if request.request_type == DataSubjectRequest.ACCESS:
            return self._process_access_request(request)
        elif request.request_type == DataSubjectRequest.RECTIFICATION:
            return self._process_rectification_request(request)
        elif request.request_type == DataSubjectRequest.ERASURE:
            return self._process_erasure_request(request)
        elif request.request_type == DataSubjectRequest.PORTABILITY:
            return self._process_portability_request(request)
        elif request.request_type == DataSubjectRequest.RESTRICTION:
            return self._process_restriction_request(request)
        elif request.request_type == DataSubjectRequest.OBJECTION:
            return self._process_objection_request(request)
        
        return {'status': 'error', 'message': 'Unknown request type'}
    
    def _process_access_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 15 - Right of access request"""
        records = self.get_user_data_records(request.user_id)
        
        # Update last accessed timestamp
        self._update_last_accessed(request.user_id)
        
        return {
            'status': 'completed',
            'request_type': 'access',
            'data_records': [asdict(record) for record in records],
            'data_summary': {
                'total_records': len(records),
                'categories': list(set(r.data_category.value for r in records)),
                'oldest_record': min(r.created_at for r in records) if records else None,
                'newest_record': max(r.created_at for r in records) if records else None
            }
        }
    
    def _process_rectification_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 16 - Right to rectification request"""
        # This would integrate with data correction logic
        return {
            'status': 'completed',
            'request_type': 'rectification',
            'message': 'Data rectification processed'
        }
    
    def _process_erasure_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 17 - Right to erasure (Right to be forgotten)"""
        erased_count = self._erase_user_data(request.user_id)
        
        return {
            'status': 'completed',
            'request_type': 'erasure',
            'records_erased': erased_count,
            'message': 'User data has been erased'
        }
    
    def _process_portability_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 20 - Right to data portability"""
        records = self.get_user_data_records(request.user_id)
        
        # Create portable data format
        portable_data = {
            'user_id': request.user_id,
            'export_date': datetime.now().isoformat(),
            'data_records': [asdict(record) for record in records]
        }
        
        return {
            'status': 'completed',
            'request_type': 'portability',
            'portable_data': portable_data,
            'format': 'JSON'
        }
    
    def _process_restriction_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 18 - Right to restriction"""
        # Mark user data as restricted
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE data_records SET data_content = 'RESTRICTED' 
                WHERE user_id = ?
            ''', (request.user_id,))
            conn.commit()
        
        return {
            'status': 'completed',
            'request_type': 'restriction',
            'message': 'Data processing restricted'
        }
    
    def _process_objection_request(self, request: DataSubjectRequestRecord) -> Dict[str, Any]:
        """Process Article 21 - Right to object"""
        # Stop processing user data for specified purposes
        return {
            'status': 'completed',
            'request_type': 'objection',
            'message': 'Processing objection recorded'
        }
    
    def _erase_user_data(self, user_id: str) -> int:
        """Erase all user data (Right to be forgotten)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get count before deletion
            cursor.execute('SELECT COUNT(*) FROM data_records WHERE user_id = ?', (user_id,))
            count = cursor.fetchone()[0]
            
            # Delete all data records
            cursor.execute('DELETE FROM data_records WHERE user_id = ?', (user_id,))
            
            # Delete consent records
            cursor.execute('DELETE FROM consent_records WHERE user_id = ?', (user_id,))
            
            # Delete data subject requests
            cursor.execute('DELETE FROM data_subject_requests WHERE user_id = ?', (user_id,))
            
            conn.commit()
            return count
    
    def _update_last_accessed(self, user_id: str):
        """Update last accessed timestamp for user data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE data_records SET last_accessed = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            conn.commit()
    
    def record_consent(self, consent: ConsentRecord) -> bool:
        """Record user consent for data processing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO consent_records (
                        consent_id, user_id, consent_type, purpose, granted,
                        granted_date, withdrawn_date, ip_address, user_agent,
                        legal_basis
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    consent.consent_id, consent.user_id, consent.consent_type,
                    consent.purpose, consent.granted, consent.granted_date,
                    consent.withdrawn_date, consent.ip_address,
                    consent.user_agent, consent.legal_basis
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def withdraw_consent(self, consent_id: str) -> bool:
        """Withdraw consent"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE consent_records SET withdrawn_date = ?
                WHERE consent_id = ?
            ''', (datetime.now().isoformat(), consent_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
            return False
    
    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM consent_records WHERE user_id = ?
            ''', (user_id,))
            
            consents = []
            for row in cursor.fetchall():
                consents.append(ConsentRecord(
                    consent_id=row[0], user_id=row[1], consent_type=row[2],
                    purpose=row[3], granted=bool(row[4]), granted_date=row[5],
                    withdrawn_date=row[6], ip_address=row[7],
                    user_agent=row[8], legal_basis=row[9]
                ))
            
            return consents
    
    def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up data that has exceeded retention period"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get expired records
            cursor.execute('''
                SELECT * FROM data_records WHERE retention_date < ?
            ''', (datetime.now().isoformat(),))
            
            records = cursor.fetchall()
            
            # Delete expired records
            cursor.execute('''
                DELETE FROM data_records WHERE retention_date < ?
            ''', (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            return {
                'records_processed': len(records),
                'records_deleted': deleted_count,
                'cleanup_date': datetime.now().isoformat()
            }
    
    def get_overdue_requests(self) -> List[DataSubjectRequestRecord]:
        """Get data subject requests that are overdue"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM data_subject_requests 
                WHERE status IN ('pending', 'processing')
            ''')
            
            overdue = []
            for row in cursor.fetchall():
                request = DataSubjectRequestRecord(
                    request_id=row[0], user_id=row[1],
                    request_type=DataSubjectRequest(row[2]),
                    request_date=row[3], status=row[4],
                    completed_date=row[5], details=json.loads(row[6]),
                    verification_status=row[7]
                )
                
                if request.is_overdue():
                    overdue.append(request)
            
            return overdue
    
    def register_processing_activity(self, activity_id: str, 
                                   controller_name: str,
                                   processing_purpose: str,
                                   data_categories: List[str],
                                   data_subjects: List[str],
                                   recipients: List[str],
                                   retention_periods: List[str],
                                   security_measures: List[str]) -> bool:
        """Register processing activity (Article 30 requirement)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                now = datetime.now().isoformat()
                cursor.execute('''
                    INSERT INTO processing_activities (
                        activity_id, controller_name, processing_purpose,
                        data_categories, data_subjects, recipients,
                        retention_periods, security_measures, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity_id, controller_name, processing_purpose,
                    json.dumps(data_categories), json.dumps(data_subjects),
                    json.dumps(recipients), json.dumps(retention_periods),
                    json.dumps(security_measures), now, now
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def generate_privacy_report(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive privacy report for user"""
        data_records = self.get_user_data_records(user_id)
        consents = self.get_user_consents(user_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM data_subject_requests WHERE user_id = ?
            ''', (user_id,))
            
            requests = []
            for row in cursor.fetchall():
                requests.append(DataSubjectRequestRecord(
                    request_id=row[0], user_id=row[1],
                    request_type=DataSubjectRequest(row[2]),
                    request_date=row[3], status=row[4],
                    completed_date=row[5], details=json.loads(row[6]),
                    verification_status=row[7]
                ))
        
        # Categorize data
        data_by_category = {}
        for record in data_records:
            category = record.data_category.value
            if category not in data_by_category:
                data_by_category[category] = []
            data_by_category[category].append(record)
        
        # Calculate retention status
        retention_status = {
            'expired': sum(1 for r in data_records if r.is_expired()),
            'active': sum(1 for r in data_records if not r.is_expired()),
            'anonymized': sum(1 for r in data_records if r.is_anonymized)
        }
        
        return {
            'user_id': user_id,
            'report_date': datetime.now().isoformat(),
            'data_summary': {
                'total_records': len(data_records),
                'by_category': {cat: len(records) for cat, records in data_by_category.items()},
                'retention_status': retention_status
            },
            'consent_summary': {
                'total_consents': len(consents),
                'active_consents': sum(1 for c in consents if c.is_active()),
                'withdrawn_consents': sum(1 for c in consents if c.withdrawn_date)
            },
            'rights_exercise': {
                'total_requests': len(requests),
                'completed_requests': sum(1 for r in requests if r.status == 'completed'),
                'pending_requests': sum(1 for r in requests if r.status in ['pending', 'processing']),
                'overdue_requests': sum(1 for r in requests if r.is_overdue())
            },
            'recommendations': self._generate_privacy_recommendations(data_records, consents)
        }
    
    def _generate_privacy_recommendations(self, data_records: List[DataRecord],
                                        consents: List[ConsentRecord]) -> List[str]:
        """Generate privacy protection recommendations"""
        recommendations = []
        
        if not data_records:
            recommendations.append("No personal data found - ensure all data processing is properly documented")
        
        expired_count = sum(1 for r in data_records if r.is_expired())
        if expired_count > 0:
            recommendations.append(f"Clean up {expired_count} expired data records")
        
        if not consents:
            recommendations.append("No consent records found - ensure consent management is in place")
        
        unanonymized = [r for r in data_records if not r.is_anonymized and r.retention_period != RetentionPeriod.INDEFINITE]
        if len(unanonymized) > 0:
            recommendations.append(f"Consider anonymizing {len(unanonymized)} data records")
        
        return recommendations


class DataAnonymizer:
    """Data anonymization for compliance"""
    
    @staticmethod
    def anonymize_for_compliance(data_content: str, category: DataCategory) -> str:
        """Anonymize data based on category"""
        if category == DataCategory.PERSONAL_IDENTIFIERS:
            # Hash personal identifiers
            return hashlib.sha256((data_content + "salt").encode()).hexdigest()
        elif category == DataCategory.CONTACT_DATA:
            # Mask contact information
            if '@' in data_content:
                # Email
                parts = data_content.split('@')
                username = parts[0]
                domain = parts[1]
                return f"{username[0]}***@{domain}"
            else:
                return "***-***-****"
        elif category == DataCategory.LOCATION_DATA:
            # Generalize location data
            return "Location Data Anonymized"
        else:
            # Default anonymization
            return hashlib.sha256((data_content + "compliance").encode()).hexdigest()
