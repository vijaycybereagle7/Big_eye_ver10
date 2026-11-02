# Compliance Documentation

## Table of Contents
1. [Overview](#overview)
2. [GDPR Compliance](#gdpr-compliance)
3. [Data Protection Impact Assessment](#data-protection-impact-assessment)
4. [Privacy by Design](#privacy-by-design)
5. [Data Subject Rights](#data-subject-rights)
6. [Consent Management](#consent-management)
7. [Data Retention and Deletion](#data-retention-and-deletion)
8. [Cross-Border Data Transfers](#cross-border-data-transfers)
9. [Security and Breach Notification](#security-and-breach-notification)
10. [Audit and Compliance Monitoring](#audit-and-compliance-monitoring)
11. [Documentation and Record Keeping](#documentation-and-record-keeping)
12. [Vendor and Third-Party Compliance](#vendor-and-third-party-compliance)

## Overview

This document outlines the compliance framework for the Cybersecurity Threat Intelligence System, with particular emphasis on GDPR (General Data Protection Regulation) requirements and other applicable data protection regulations.

**Compliance Objectives**:
- Ensure full GDPR compliance for EU data subjects
- Implement Privacy by Design principles
- Maintain comprehensive audit trails
- Protect data subject rights and freedoms
- Demonstrate accountability and transparency
- Ensure data protection by design and by default

**Regulatory Framework**:
- **GDPR (EU)**: General Data Protection Regulation 2016/679
- **CCPA (California)**: California Consumer Privacy Act
- **PIPEDA (Canada)**: Personal Information Protection and Electronic Documents Act
- **SOX (USA)**: Sarbanes-Oxley Act (for publicly traded companies)
- **ISO 27001**: Information Security Management

## GDPR Compliance

### 1. Legal Basis for Processing

#### 1.1 Lawful Processing Bases

**File**: `compliance/legal_basis_mapping.py`
```python
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

class LegalBasis(Enum):
    """GDPR Article 6 legal bases for processing"""
    CONSENT = "consent"                    # Art. 6(1)(a)
    CONTRACT = "contract"                  # Art. 6(1)(b)
    LEGAL_OBLIGATION = "legal_obligation" # Art. 6(1)(c)
    VITAL_INTERESTS = "vital_interests"   # Art. 6(1)(d)
    PUBLIC_TASK = "public_task"           # Art. 6(1)(e)
    LEGITIMATE_INTERESTS = "legitimate_interests"  # Art. 6(1)(f)

class DataProcessingActivity:
    """Represents a data processing activity under GDPR"""
    
    def __init__(
        self,
        activity_id: str,
        purpose: str,
        data_categories: List[str],
        legal_basis: LegalBasis,
        data_subjects: List[str],
        retention_period: int,
        processors: List[str],
        transfers: List[Dict[str, Any]] = None
    ):
        self.activity_id = activity_id
        self.purpose = purpose
        self.data_categories = data_categories
        self.legal_basis = legal_basis
        self.data_subjects = data_subjects
        self.retention_period = retention_period
        self.processors = processors
        self.transfers = transfers or []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class GDPRComplianceManager:
    """GDPR compliance management system"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.processing_activities = self._initialize_processing_activities()
    
    def _initialize_processing_activities(self) -> List[DataProcessingActivity]:
        """Initialize standard data processing activities"""
        
        activities = [
            # User account management
            DataProcessingActivity(
                activity_id="user_account_management",
                purpose="Create and manage user accounts for threat intelligence system",
                data_categories=[
                    "user_identifiers", "contact_information", 
                    "authentication_data", "preferences"
                ],
                legal_basis=LegalBasis.CONTRACT,
                data_subjects=["registered_users", "administrators"],
                retention_period=2555,  # 7 years
                processors=["internal_staff"],
                transfers=[]
            ),
            
            # Threat intelligence analysis
            DataProcessingActivity(
                activity_id="threat_intelligence_analysis",
                purpose="Analyze threat intelligence data for security purposes",
                data_categories=[
                    "ip_addresses", "domain_names", "email_addresses",
                    "url_data", "file_hashes", "behavioral_data"
                ],
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                data_subjects=["third_party_entities", "anonymous_users"],
                retention_period=2555,  # 7 years
                processors=["security_team", "analysts"],
                transfers=[]
            ),
            
            # API usage tracking
            DataProcessingActivity(
                activity_id="api_usage_tracking",
                purpose="Monitor and improve API performance and security",
                data_categories=[
                    "ip_addresses", "request_metadata", "usage_statistics"
                ],
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                data_subjects=["api_users", "anonymous_visitors"],
                retention_period=365,  # 1 year
                processors=["technical_team"],
                transfers=[]
            ),
            
            # Security monitoring
            DataProcessingActivity(
                activity_id="security_monitoring",
                purpose="Detect and prevent security threats and fraud",
                data_categories=[
                    "access_logs", "authentication_attempts", 
                    "system_events", "security_alerts"
                ],
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                data_subjects=["all_system_users"],
                retention_period=2555,  # 7 years
                processors=["security_team", "system_administrators"],
                transfers=[]
            ),
            
            # Communication and notifications
            DataProcessingActivity(
                activity_id="communications",
                purpose="Send system notifications and security alerts",
                data_categories=["contact_information", "communication_preferences"],
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                data_subjects=["registered_users"],
                retention_period=1095,  # 3 years
                processors=["notification_service"],
                transfers=[]
            )
        ]
        
        return activities
    
    def get_processing_activities(self) -> List[DataProcessingActivity]:
        """Get all registered data processing activities"""
        return self.processing_activities
    
    def get_processing_activity(self, activity_id: str) -> Optional[DataProcessingActivity]:
        """Get specific processing activity by ID"""
        for activity in self.processing_activities:
            if activity.activity_id == activity_id:
                return activity
        return None
    
    def validate_processing_basis(self, activity_id: str, legal_basis: LegalBasis) -> bool:
        """Validate if legal basis is appropriate for processing activity"""
        
        activity = self.get_processing_activity(activity_id)
        if not activity:
            return False
        
        # Check if legal basis is one of the allowed ones
        allowed_bases = self._get_allowed_legal_bases(activity)
        return legal_basis in allowed_bases
    
    def _get_allowed_legal_bases(self, activity: DataProcessingActivity) -> List[LegalBasis]:
        """Get allowed legal bases for a processing activity"""
        
        # Map processing purposes to appropriate legal bases
        purpose_bases = {
            "user_account_management": [LegalBasis.CONTRACT, LegalBasis.LEGITIMATE_INTERESTS],
            "threat_intelligence_analysis": [LegalBasis.LEGITIMATE_INTERESTS, LegalBasis.VITAL_INTERESTS],
            "api_usage_tracking": [LegalBasis.LEGITIMATE_INTERESTS],
            "security_monitoring": [LegalBasis.LEGITIMATE_INTERESTS, LegalBasis.LEGAL_OBLIGATION],
            "communications": [LegalBasis.LEGITIMATE_INTERESTS, LegalBasis.CONSENT]
        }
        
        return purpose_bases.get(activity.activity_id, [LegalBasis.LEGITIMATE_INTERESTS])
    
    async def record_processing_activity(
        self,
        activity_id: str,
        data_subject_id: str,
        data_categories: List[str],
        processor: str,
        additional_info: Dict[str, Any] = None
    ) -> str:
        """Record a data processing activity for audit trail"""
        
        record_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_processing_records (
                    record_id, activity_id, data_subject_id, data_categories,
                    processor, processed_at, additional_info
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, record_id, activity_id, data_subject_id, data_categories,
                 processor, current_time, additional_info)
        
        return record_id
    
    def generate_gdpr_article_30_report(self) -> Dict[str, Any]:
        """Generate GDPR Article 30 (Records of processing activities) report"""
        
        report = {
            "controller_information": {
                "name": "Threat Intelligence System",
                "contact_details": "privacy@yourdomain.com",
                "dpo_contact": "dpo@yourdomain.com",
                "representative": "EU Representative Ltd (if applicable)"
            },
            "processing_activities": [],
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }
        
        for activity in self.processing_activities:
            activity_report = {
                "name": activity.activity_id,
                "purpose": activity.purpose,
                "categories_of_data_subjects": activity.data_subjects,
                "categories_of_personal_data": activity.data_categories,
                "categories_of_recipients": activity.processors,
                "transfers_to_third_countries": activity.transfers,
                "retention_periods": f"{activity.retention_period} days",
                "technical_and_organizational_security_measures": [
                    "encryption_at_rest",
                    "encryption_in_transit",
                    "access_controls",
                    "audit_logging",
                    "regular_security_assessments"
                ],
                "legal_basis": activity.legal_basis.value
            }
            
            report["processing_activities"].append(activity_report)
        
        return report
```

### 2. Data Protection Impact Assessment (DPIA)

#### 2.1 DPIA Framework

**File**: `compliance/dpia_assessment.py`
```python
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DataType(Enum):
    IDENTIFIERS = "identifiers"
    CONTACT_DATA = "contact_data"
    BEHAVIORAL_DATA = "behavioral_data"
    TECHNICAL_DATA = "technical_data"
    THREAT_DATA = "threat_data"
    LOCATION_DATA = "location_data"

@dataclass
class DPIAMeasure:
    """Represents a privacy protection measure"""
    measure_id: str
    description: str
    implementation_status: str  # "planned", "in_progress", "implemented"
    responsible_party: str
    deadline: Optional[datetime]

@dataclass
class DPIARisk:
    """Represents a privacy risk identified in DPIA"""
    risk_id: str
    description: str
    likelihood: RiskLevel
    impact: RiskLevel
    overall_risk: RiskLevel
    mitigation_measures: List[str]
    residual_risk: RiskLevel

class DataProtectionImpactAssessment:
    """Comprehensive DPIA framework"""
    
    def __init__(self, assessment_id: str = None):
        self.assessment_id = assessment_id or str(uuid.uuid4())
        self.completion_date: Optional[datetime] = None
        self.dpia_version = "1.0"
        
        # Assessment sections
        self.project_information = {}
        self.processing_description = {}
        self.data_flow_mapping = {}
        self.risk_identification = {}
        self.necessity_proportionality = {}
        self.privacy_measures = []
        self.risks = []
        self.consultation_outcomes = {}
        self.signatures = {}
    
    def assess_processing_necessity(
        self,
        purpose: str,
        data_categories: List[DataType],
        data_subjects: List[str],
        expected_benefits: List[str],
        less_intrusive_alternatives: List[str] = None
    ) -> Tuple[bool, List[str]]:
        """Assess if processing is necessary and proportionate"""
        
        assessment_results = []
        
        # Check if purpose is legitimate
        if not purpose or len(purpose.strip()) < 10:
            assessment_results.append("Purpose description is insufficient")
        
        # Check if purpose aligns with GDPR principles
        legitimate_purposes = [
            "security monitoring",
            "fraud prevention", 
            "system administration",
            "legal compliance"
        ]
        
        purpose_lower = purpose.lower()
        is_legitimate_purpose = any(
            legitimate in purpose_lower 
            for legitimate in legitimate_purposes
        )
        
        if not is_legitimate_purpose:
            assessment_results.append("Processing purpose may not be legitimate")
        
        # Check data minimization
        necessary_data_types = self._get_necessary_data_types(purpose)
        unnecessary_data = set(data_categories) - set(necessary_data_types)
        
        if unnecessary_data:
            assessment_results.append(
                f"Potentially unnecessary data categories: {list(unnecessary_data)}"
            )
        
        # Check for less intrusive alternatives
        if not less_intrusive_alternatives:
            assessment_results.append(
                "No consideration given to less intrusive alternatives"
            )
        
        # Final assessment
        is_necessary = len(assessment_results) == 0
        
        return is_necessary, assessment_results
    
    def _get_necessary_data_types(self, purpose: str) -> List[DataType]:
        """Determine necessary data types for given purpose"""
        
        purpose_mapping = {
            "security": [DataType.IDENTIFIERS, DataType.TECHNICAL_DATA, DataType.THREAT_DATA],
            "authentication": [DataType.IDENTIFIERS, DataType.TECHNICAL_DATA],
            "analysis": [DataType.THREAT_DATA, DataType.BEHAVIORAL_DATA],
            "communication": [DataType.CONTACT_DATA],
            "monitoring": [DataType.TECHNICAL_DATA, DataType.BEHAVIORAL_DATA]
        }
        
        necessary_types = []
        purpose_lower = purpose.lower()
        
        for key, data_types in purpose_mapping.items():
            if key in purpose_lower:
                necessary_types.extend(data_types)
        
        # If no match, return default minimal set
        return necessary_types or [DataType.IDENTIFIERS]
    
    def conduct_risk_assessment(
        self,
        data_categories: List[DataType],
        data_subjects: List[str],
        processing_scale: str,
        cross_border_transfers: bool,
        automated_decision_making: bool,
        special_categories: bool
    ) -> List[DPIARisk]:
        """Conduct comprehensive risk assessment"""
        
        risks = []
        
        # Risk 1: Data Breach Risk
        breach_risk = self._assess_data_breach_risk(
            data_categories, processing_scale
        )
        if breach_risk.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            risks.append(breach_risk)
        
        # Risk 2: Re-identification Risk
        if DataType.BEHAVIORAL_DATA in data_categories:
            reid_risk = self._assess_reidentification_risk(data_categories)
            if reid_risk.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risks.append(reid_risk)
        
        # Risk 3: Profiling Risk
        if DataType.BEHAVIORAL_DATA in data_categories:
            profiling_risk = self._assess_profiling_risk(data_subjects)
            if profiling_risk.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risks.append(profiling_risk)
        
        # Risk 4: Cross-border Transfer Risk
        if cross_border_transfers:
            transfer_risk = self._assess_transfer_risk()
            if transfer_risk.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risks.append(transfer_risk)
        
        # Risk 5: Automated Decision Making Risk
        if automated_decision_making:
            automation_risk = self._assess_automation_risk(data_subjects)
            if automation_risk.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                risks.append(automation_risk)
        
        return risks
    
    def _assess_data_breach_risk(
        self, 
        data_categories: List[DataType], 
        processing_scale: str
    ) -> DPIARisk:
        """Assess risk of data breach"""
        
        # Calculate breach impact
        high_impact_data = {DataType.CONTACT_DATA, DataType.BEHAVIORAL_DATA}
        has_high_impact = any(cat in high_impact_data for cat in data_categories)
        
        # Calculate breach likelihood
        scale_risk = {
            "small": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "large": RiskLevel.HIGH,
            "massive": RiskLevel.CRITICAL
        }.get(processing_scale.lower(), RiskLevel.MEDIUM)
        
        # Determine overall risk
        if has_high_impact and scale_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            overall_risk = RiskLevel.CRITICAL
        elif has_high_impact or scale_risk == RiskLevel.HIGH:
            overall_risk = RiskLevel.HIGH
        elif has_high_impact or scale_risk == RiskLevel.MEDIUM:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        return DPIARisk(
            risk_id="data_breach",
            description="Risk of unauthorized access to or disclosure of personal data",
            likelihood=scale_risk,
            impact=RiskLevel.HIGH if has_high_impact else RiskLevel.MEDIUM,
            overall_risk=overall_risk,
            mitigation_measures=[
                "Implement strong encryption for data at rest and in transit",
                "Apply robust access controls and authentication",
                "Regular security audits and penetration testing",
                "Employee security training and awareness",
                "Incident response plan and monitoring"
            ],
            residual_risk=RiskLevel.MEDIUM if overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL] else RiskLevel.LOW
        )
    
    def _assess_reidentification_risk(self, data_categories: List[DataType]) -> DPIARisk:
        """Assess risk of data subject re-identification"""
        
        reidentification_data = {
            DataType.BEHAVIORAL_DATA, 
            DataType.TECHNICAL_DATA,
            DataType.LOCATION_DATA
        }
        
        has_reid_data = any(cat in reidentification_data for cat in data_categories)
        
        if has_reid_data:
            likelihood = RiskLevel.HIGH
            impact = RiskLevel.HIGH
            overall_risk = RiskLevel.HIGH
        else:
            likelihood = RiskLevel.LOW
            impact = RiskLevel.LOW
            overall_risk = RiskLevel.LOW
        
        return DPIARisk(
            risk_id="reidentification",
            description="Risk of data subject re-identification from anonymized data",
            likelihood=likelihood,
            impact=impact,
            overall_risk=overall_risk,
            mitigation_measures=[
                "Implement proper anonymization techniques",
                "Use k-anonymity, l-diversity, or t-closeness",
                "Regular assessment of re-identification risks",
                "Data aggregation and generalization",
                "Differential privacy techniques"
            ],
            residual_risk=RiskLevel.LOW if overall_risk == RiskLevel.HIGH else overall_risk
        )
    
    def _assess_profiling_risk(self, data_subjects: List[str]) -> DPIARisk:
        """Assess risk of profiling affecting data subjects"""
        
        # Profiling risk is higher if affecting individuals in vulnerable situations
        vulnerable_subjects = ["children", "elderly", "disabled", "vulnerable_groups"]
        
        has_vulnerable_subjects = any(
            any(vuln in subject.lower() for vuln in vulnerable_subjects)
            for subject in data_subjects
        )
        
        if has_vulnerable_subjects:
            likelihood = RiskLevel.HIGH
            impact = RiskLevel.HIGH
            overall_risk = RiskLevel.HIGH
        else:
            likelihood = RiskLevel.MEDIUM
            impact = RiskLevel.MEDIUM
            overall_risk = RiskLevel.MEDIUM
        
        return DPIARisk(
            risk_id="profiling",
            description="Risk of automated profiling affecting data subjects",
            likelihood=likelihood,
            impact=impact,
            overall_risk=overall_risk,
            mitigation_measures=[
                "Provide clear information about profiling activities",
                "Offer opt-out mechanisms where applicable",
                "Implement fairness and bias testing",
                "Regular review of algorithmic decisions",
                "Human oversight for significant decisions"
            ],
            residual_risk=RiskLevel.LOW if overall_risk == RiskLevel.HIGH else overall_risk
        )
    
    def _assess_transfer_risk(self) -> DPIARisk:
        """Assess risk of cross-border data transfers"""
        
        return DPIARisk(
            risk_id="cross_border_transfer",
            description="Risk associated with transferring personal data outside the EEA",
            likelihood=RiskLevel.MEDIUM,
            impact=RiskLevel.MEDIUM,
            overall_risk=RiskLevel.MEDIUM,
            mitigation_measures=[
                "Implement appropriate safeguards (adequacy decisions, SCCs)",
                "Conduct transfer impact assessments",
                "Use encryption for data in transit",
                "Monitor legal developments in receiving countries",
                "Regular review of transfer mechanisms"
            ],
            residual_risk=RiskLevel.LOW
        )
    
    def _assess_automation_risk(self, data_subjects: List[str]) -> DPIARisk:
        """Assess risk of automated decision-making"""
        
        return DPIARisk(
            risk_id="automated_decision_making",
            description="Risk of decisions based solely on automated processing",
            likelihood=RiskLevel.LOW,  # Assuming human oversight
            impact=RiskLevel.HIGH,
            overall_risk=RiskLevel.MEDIUM,
            mitigation_measures=[
                "Implement human review for significant decisions",
                "Provide explanation mechanisms",
                "Allow data subjects to contest decisions",
                "Regular testing for bias and fairness",
                "Clear communication about automated processing"
            ],
            residual_risk=RiskLevel.LOW
        )
    
    def add_privacy_measure(
        self,
        description: str,
        implementation_status: str,
        responsible_party: str,
        deadline: Optional[datetime] = None
    ) -> str:
        """Add a privacy protection measure"""
        
        measure_id = str(uuid.uuid4())
        measure = DPIAMeasure(
            measure_id=measure_id,
            description=description,
            implementation_status=implementation_status,
            responsible_party=responsible_party,
            deadline=deadline
        )
        
        self.privacy_measures.append(measure)
        return measure_id
    
    def generate_dpia_report(self) -> Dict[str, Any]:
        """Generate comprehensive DPIA report"""
        
        return {
            "dpia_metadata": {
                "assessment_id": self.assessment_id,
                "version": self.dpia_version,
                "completion_date": self.completion_date.isoformat() if self.completion_date else None
            },
            "project_information": self.project_information,
            "processing_description": self.processing_description,
            "risk_assessment": {
                "identified_risks": [
                    {
                        "risk_id": risk.risk_id,
                        "description": risk.description,
                        "likelihood": risk.likelihood.value,
                        "impact": risk.impact.value,
                        "overall_risk": risk.overall_risk.value,
                        "mitigation_measures": risk.mitigation_measures,
                        "residual_risk": risk.residual_risk.value
                    } for risk in self.risks
                ],
                "high_risks_identified": len([r for r in self.risks if r.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]]) > 0
            },
            "privacy_measures": [
                {
                    "measure_id": measure.measure_id,
                    "description": measure.description,
                    "implementation_status": measure.implementation_status,
                    "responsible_party": measure.responsible_party,
                    "deadline": measure.deadline.isoformat() if measure.deadline else None
                } for measure in self.privacy_measures
            ],
            "necessity_proportionality": self.necessity_proportionality,
            "consultation_outcomes": self.consultation_outcomes,
            "signatures": self.signatures,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate DPIA recommendations"""
        
        recommendations = []
        
        # Check for high residual risks
        high_residual_risks = [r for r in self.risks if r.residual_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        if high_residual_risks:
            recommendations.append(
                "High residual risks identified. Consider additional mitigation measures or seek supervisory authority consultation."
            )
        
        # Check for unimplemented measures
        unimplemented = [m for m in self.privacy_measures if m.implementation_status in ["planned", "in_progress"]]
        
        if unimplemented:
            recommendations.append(
                f"{len(unimplemented)} privacy measures are not yet fully implemented. Prioritize completion."
            )
        
        # General recommendations
        recommendations.extend([
            "Regular review of DPIA to account for changes in processing",
            "Staff training on privacy risks and mitigation measures",
            "Documentation of decision-making process for risk acceptance",
            "Monitoring of privacy measures effectiveness"
        ])
        
        return recommendations
    
    def mark_completed(self, reviewer_name: str, date: datetime = None):
        """Mark DPIA as completed"""
        
        self.completion_date = date or datetime.utcnow()
        self.signatures = {
            "reviewer": reviewer_name,
            "review_date": self.completion_date.isoformat(),
            "status": "completed"
        }
```

### 3. Privacy by Design Implementation

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class PrivacyPrinciple(ABC):
    """Abstract base for privacy by design principles"""
    
    @abstractmethod
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement the privacy principle"""
        pass
    
    @abstractmethod
    def validate(self, context: Dict[str, Any]) -> List[str]:
        """Validate implementation of the principle"""
        pass

class DataMinimization(PrivacyPrinciple):
    """GDPR Article 5(1)(c) - Data minimisation"""
    
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement data minimization measures"""
        
        implementation = {
            "data_collection_limitation": {
                "implemented": True,
                "measures": [
                    "Collect only necessary data fields",
                    "Implement progressive data collection",
                    "Use default privacy settings",
                    "Regular data audits and reviews"
                ]
            },
            "data_retention_limits": {
                "implemented": True,
                "measures": [
                    "Automatic data deletion based on retention policies",
                    "Regular data lifecycle reviews",
                    "Archive old data with reduced access",
                    "Secure deletion of expired data"
                ]
            },
            "purpose_limitation": {
                "implemented": True,
                "measures": [
                    "Document specific purposes for each data field",
                    "Prevent secondary use without consent",
                    "Implement data usage tracking",
                    "Regular purpose compliance audits"
                ]
            }
        }
        
        return implementation
    
    def validate(self, context: Dict[str, Any]) -> List[str]:
        """Validate data minimization implementation"""
        
        validation_results = []
        
        # Check if data collection is limited
        if "data_collection_policy" not in context:
            validation_results.append("No data collection policy documented")
        
        # Check retention policies
        if "retention_policy" not in context:
            validation_results.append("No data retention policy defined")
        
        # Check for purpose limitation
        if "purpose_documentation" not in context:
            validation_results.append("Data processing purposes not documented")
        
        return validation_results

class PurposeLimitation(PrivacyPrinciple):
    """GDPR Article 5(1)(b) - Purpose limitation"""
    
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement purpose limitation measures"""
        
        return {
            "purpose_binding": {
                "implemented": True,
                "measures": [
                    "Bind data use to documented purposes",
                    "Implement access controls based on purpose",
                    "Regular purpose compliance monitoring",
                    "Purpose change approval process"
                ]
            },
            "incompatible_use_prevention": {
                "implemented": True,
                "measures": [
                    "Automated purpose checking",
                    "Data access logging and monitoring",
                    "Secondary use approval process",
                    "Regular access review and cleanup"
                ]
            }
        }
    
    def validate(self, context: Dict[str, Any]) -> List[str]:
        validation_results = []
        
        if "purpose_matrix" not in context:
            validation_results.append("Purpose binding matrix not implemented")
        
        return validation_results

class StorageLimitation(PrivacyPrinciple):
    """GDPR Article 5(1)(e) - Storage limitation"""
    
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement storage limitation measures"""
        
        return {
            "automated_deletion": {
                "implemented": True,
                "measures": [
                    "Database triggers for automatic deletion",
                    "Scheduled cleanup jobs",
                    "Retention policy enforcement",
                    "Secure deletion procedures"
                ]
            },
            "data_archiving": {
                "implemented": True,
                "measures": [
                    "Separate archived data storage",
                    "Restricted access to archived data",
                    "Encrypted archival storage",
                    "Regular archival review process"
                ]
            }
        }
    
    def validate(self, context: Dict[str, Any]) -> List[str]:
        validation_results = []
        
        if "automated_deletion_schedule" not in context:
            validation_results.append("Automated data deletion not implemented")
        
        return validation_results

class Accuracy(PrivacyPrinciple):
    """GDPR Article 5(1)(d) - Accuracy"""
    
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement data accuracy measures"""
        
        return {
            "data_quality_controls": {
                "implemented": True,
                "measures": [
                    "Input validation and sanitization",
                    "Data quality monitoring",
                    "Regular data accuracy audits",
                    "Correction and update mechanisms"
                ]
            },
            "data_subject_participation": {
                "implemented": True,
                "measures": [
                    "Self-service data correction",
                    "Data accuracy confirmation process",
                    "Feedback mechanisms for data quality",
                    "Regular data subject notifications"
                ]
            }
        }
    
    def validate(self, context: Dict[str, Any]) -> List[str]:
        validation_results = []
        
        if "data_quality_metrics" not in context:
            validation_results.append("Data quality monitoring not implemented")
        
        return validation_results

class Security(PrivacyPrinciple):
    """GDPR Article 5(1)(f) - Security"""
    
    def implement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement security measures"""
        
        return {
            "technical_measures": {
                "implemented": True,
                "measures": [
                    "End-to-end encryption",
                    "Access controls and authentication",
                    "Network security and segmentation",
                    "Regular security assessments"
                ]
            },
            "organizational_measures": {
                "implemented": True,
                "measures": [
                    "Security policies and procedures",
                    "Staff security training",
                    "Incident response procedures",
                    "Regular security audits"
                ]
            }
        }
    
    def validate(self, context: Dict[str, Any]) -> List[str]:
        validation_results = []
        
        if "security_incident_plan" not in context:
            validation_results.append("Security incident response plan not documented")
        
        return validation_results

class PrivacyByDesignFramework:
    """Comprehensive Privacy by Design implementation framework"""
    
    def __init__(self):
        self.principles = {
            "data_minimization": DataMinimization(),
            "purpose_limitation": PurposeLimitation(),
            "storage_limitation": StorageLimitation(),
            "accuracy": Accuracy(),
            "security": Security()
        }
        self.implementations = {}
        self.validations = {}
    
    def implement_privacy_by_design(
        self, 
        system_context: Dict[str, Any],
        processing_activities: List[str]
    ) -> Dict[str, Any]:
        """Implement Privacy by Design for processing activities"""
        
        implementation_results = {}
        
        for activity in processing_activities:
            activity_context = system_context.get(activity, {})
            activity_implementations = {}
            
            for principle_name, principle in self.principles.items():
                try:
                    # Implement the principle
                    implementation = principle.implement(activity_context)
                    activity_implementations[principle_name] = implementation
                    
                    # Validate implementation
                    validation_issues = principle.validate(activity_context)
                    
                except Exception as e:
                    activity_implementations[principle_name] = {
                        "error": str(e),
                        "implemented": False
                    }
                    validation_issues = [f"Implementation error: {str(e)}"]
                
                self.validations[f"{activity}_{principle_name}"] = validation_issues
            
            implementation_results[activity] = activity_implementations
        
        self.implementations.update(implementation_results)
        
        return implementation_results
    
    def generate_privacy_by_design_report(self) -> Dict[str, Any]:
        """Generate comprehensive Privacy by Design report"""
        
        total_issues = sum(len(issues) for issues in self.validations.values())
        
        return {
            "report_metadata": {
                "generation_date": datetime.utcnow().isoformat(),
                "framework_version": "1.0",
                "total_validation_issues": total_issues
            },
            "principle_implementations": self.implementations,
            "validation_summary": {
                total_issues: total_issues,
                "critical_issues": len([issues for issues in self.validations.values() 
                                      if "critical" in str(issues).lower()]),
                "by_principle": {
                    principle: len(issues) 
                    for principle, issues in self.validations.items()
                }
            },
            "recommendations": self._generate_pb_design_recommendations()
        }
    
    def _generate_pb_design_recommendations(self) -> List[str]:
        """Generate Privacy by Design recommendations"""
        
        recommendations = []
        
        # Check for validation issues
        all_issues = [issue for issues in self.validations.values() for issue in issues]
        
        if all_issues:
            recommendations.append(
                f"{len(all_issues)} privacy principle validation issues found. Review and address them."
            )
        
        # Principle-specific recommendations
        for principle_name, principle in self.principles.items():
            principle_issues = [
                issue for key, issues in self.validations.items()
                if principle_name in key for issue in issues
            ]
            
            if principle_issues:
                recommendations.append(
                    f"{principle_name.replace('_', ' ').title()}: Address {len(principle_issues)} validation issues"
                )
        
        # General recommendations
        recommendations.extend([
            "Regular review of Privacy by Design implementation",
            "Staff training on privacy principles and their implementation",
            "Integration of privacy considerations in development lifecycle",
            "Monitoring of privacy principle effectiveness"
        ])
        
        return recommendations
```

## Data Subject Rights

### 1. Data Subject Request Management

```python
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import asyncio

class DataSubjectRight(Enum):
    """GDPR Article 15-22 data subject rights"""
    ACCESS = "access"                    # Art. 15
    RECTIFICATION = "rectification"      # Art. 16
    ERASURE = "erasure"                  # Art. 17
    RESTRICTION = "restriction"          # Art. 18
    PORTABILITY = "portability"          # Art. 20
    OBJECTION = "objection"              # Art. 21
    AUTOMATED_DECISION = "automated_decision"  # Art. 22

@dataclass
class DataSubjectRequest:
    """Represents a data subject request"""
    request_id: str
    subject_identifier: str  # Email, user ID, etc.
    right_requested: DataSubjectRight
    request_details: str
    submitted_at: datetime
    identity_verified: bool = False
    status: str = "pending"  # pending, in_progress, completed, rejected, expired
    due_date: datetime = None
    assigned_to: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    notes: List[str] = None
    
    def __post_init__(self):
        if self.due_date is None:
            # GDPR: 1 month response time (can be extended by 2 months)
            self.due_date = self.submitted_at + timedelta(days=30)
        
        if self.notes is None:
            self.notes = []

class DataSubjectRightsManager:
    """Manages data subject rights requests and responses"""
    
    def __init__(self, db_pool, email_service, encryption_service):
        self.db_pool = db_pool
        self.email_service = email_service
        self.encryption_service = encryption_service
        self.request_templates = self._load_request_templates()
    
    def _load_request_templates(self) -> Dict[str, str]:
        """Load request response templates"""
        
        return {
            "access_response_template": """
            Dear {subject_name},
            
            Following your data subject access request, please find below the personal data we hold about you:
            
            {data_summary}
            
            This information is being provided in accordance with Article 15 of the GDPR.
            
            If you have any questions about this information, please contact us at privacy@yourdomain.com.
            
            Best regards,
            Data Protection Team
            """,
            
            "erasure_confirmation_template": """
            Dear {subject_name},
            
            We confirm that we have processed your request for erasure of your personal data under Article 17 of the GDPR.
            
            Data erased: {erased_data_summary}
            Erasure date: {erasure_date}
            
            Please note that some data may be retained for legal obligations or legitimate interests as outlined in our privacy policy.
            
            Best regards,
            Data Protection Team
            """,
            
            "rectification_confirmation_template": """
            Dear {subject_name},
            
            We have processed your request for rectification of your personal data under Article 16 of the GDPR.
            
            Data updated: {updated_fields}
            Update date: {update_date}
            
            The corrected information is now available in our systems.
            
            Best regards,
            Data Protection Team
            """
        }
    
    async def submit_data_subject_request(
        self,
        subject_identifier: str,
        right_requested: DataSubjectRight,
        request_details: str = None,
        identity_verification_method: str = "email_verification"
    ) -> str:
        """Submit a new data subject request"""
        
        request_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Create request record
        request = DataSubjectRequest(
            request_id=request_id,
            subject_identifier=subject_identifier,
            right_requested=right_requested,
            request_details=request_details or "",
            submitted_at=current_time
        )
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_subject_requests (
                    request_id, subject_identifier, right_requested, request_details,
                    submitted_at, due_date, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, request_id, subject_identifier, right_requested.value,
                 request_details, current_time, request.due_date, "pending")
        
        # Send acknowledgment email
        await self._send_request_acknowledgment(request)
        
        # Start identity verification if required
        if identity_verification_method == "email_verification":
            await self._send_identity_verification_email(request)
        
        return request_id
    
    async def verify_identity(self, request_id: str, verification_code: str) -> bool:
        """Verify data subject identity"""
        
        # In production, implement secure verification logic
        # This is a simplified example
        
        async with self.db_pool.acquire() as conn:
            # Check if verification code is valid and not expired
            result = await conn.fetchrow("""
                SELECT subject_identifier, submitted_at 
                FROM data_subject_requests 
                WHERE request_id = $1 AND status = 'pending'
            """, request_id)
            
            if not result:
                return False
        
        # Mark identity as verified
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE data_subject_requests 
                SET identity_verified = true, status = 'in_progress', assigned_to = 'auto_assigned'
                WHERE request_id = $1
            """, request_id)
        
        return True
    
    async def process_access_request(self, request_id: str) -> Dict[str, Any]:
        """Process Article 15 - Right of access request"""
        
        # Get request details
        request = await self._get_request(request_id)
        if not request or request.right_requested != DataSubjectRight.ACCESS:
            raise ValueError("Invalid access request")
        
        # Collect all personal data for the subject
        personal_data = await self._collect_personal_data(request.subject_identifier)
        
        # Create response
        response_data = {
            "request_id": request_id,
            "subject_identifier": request.subject_identifier,
            "response_date": datetime.utcnow().isoformat(),
            "personal_data": personal_data,
            "data_categories": list(personal_data.keys()),
            "purposes_of_processing": await self._get_processing_purposes(request.subject_identifier),
            "retention_periods": await self._get_retention_periods(request.subject_identifier),
            "third_country_transfers": await self._get_third_country_transfers(request.subject_identifier),
            "data_source": "Direct collection and threat intelligence analysis",
            "automated_decision_making": await self._get_automated_decision_info(request.subject_identifier)
        }
        
        # Store response data
        await self._store_response_data(request_id, response_data)
        
        # Send response to data subject
        await self._send_access_response(request, response_data)
        
        return response_data
    
    async def process_rectification_request(
        self, 
        request_id: str, 
        rectification_data: Dict[str, Any]
    ) -> bool:
        """Process Article 16 - Right of rectification"""
        
        request = await self._get_request(request_id)
        if not request or request.right_requested != DataSubjectRight.RECTIFICATION:
            raise ValueError("Invalid rectification request")
        
        # Update personal data
        updated_fields = []
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for field, new_value in rectification_data.items():
                    # Update in users table
                    result = await conn.execute("""
                        UPDATE users 
                        SET $1 = $2, updated_at = NOW()
                        WHERE id = $3 OR email = $4
                    """, field, new_value, request.subject_identifier, request.subject_identifier)
                    
                    if result.split()[-1] == "1":  # One row updated
                        updated_fields.append(field)
        
        # Create response
        response_data = {
            "request_id": request_id,
            "rectified_fields": updated_fields,
            "rectification_date": datetime.utcnow().isoformat()
        }
        
        await self._store_response_data(request_id, response_data)
        await self._send_rectification_confirmation(request, response_data)
        
        return len(updated_fields) > 0
    
    async def process_erasure_request(self, request_id: str) -> Dict[str, Any]:
        """Process Article 17 - Right to erasure"""
        
        request = await self._get_request(request_id)
        if not request or request.right_requested != DataSubjectRight.ERASURE:
            raise ValueError("Invalid erasure request")
        
        # Check erasure exceptions (legal obligations, legitimate interests, etc.)
        erasure_exceptions = await self._check_erasure_exceptions(request.subject_identifier)
        
        if erasure_exceptions:
            # Partial erasure - explain what cannot be erased
            partial_erasure = await self._process_partial_erasure(
                request.subject_identifier, erasure_exceptions
            )
            
            response_data = {
                "request_id": request_id,
                "erasure_status": "partial",
                "erased_data": partial_erasure["erased"],
                "retained_data": partial_erasure["retained"],
                "reasons": erasure_exceptions,
                "erasure_date": datetime.utcnow().isoformat()
            }
        else:
            # Complete erasure
            erased_data = await self._process_complete_erasure(request.subject_identifier)
            
            response_data = {
                "request_id": request_id,
                "erasure_status": "complete",
                "erased_data": erased_data,
                "erasure_date": datetime.utcnow().isoformat()
            }
        
        await self._store_response_data(request_id, response_data)
        await self._send_erasure_confirmation(request, response_data)
        
        return response_data
    
    async def process_portability_request(self, request_id: str) -> Dict[str, Any]:
        """Process Article 20 - Right to data portability"""
        
        request = await self._get_request(request_id)
        if not request or request.right_requested != DataSubjectRight.PORTABILITY:
            raise ValueError("Invalid portability request")
        
        # Collect portable data
        portable_data = await self._collect_portable_data(request.subject_identifier)
        
        # Create machine-readable format (JSON)
        response_data = {
            "request_id": request_id,
            "data_subject": request.subject_identifier,
            "export_date": datetime.utcnow().isoformat(),
            "data_format": "JSON",
            "personal_data": portable_data,
            "data_structure": "Structured according to original collection format",
            "processing_purposes": "Data exported for portability as requested by data subject"
        }
        
        # Store response data
        await self._store_response_data(request_id, response_data)
        
        # Send response to data subject
        await self._send_portability_response(request, response_data)
        
        return response_data
    
    async def _collect_personal_data(self, subject_identifier: str) -> Dict[str, Any]:
        """Collect all personal data for a data subject"""
        
        async with self.db_pool.acquire() as conn:
            # Get user profile data
            user_data = await conn.fetchrow("""
                SELECT id, username, email, first_name, last_name, 
                       department, position, created_at, last_login,
                       is_active, preferences
                FROM users 
                WHERE id = $1 OR email = $2
            """, subject_identifier, subject_identifier)
            
            # Get API usage data
            api_data = await conn.fetch("""
                SELECT endpoint, method, status_code, response_time, created_at
                FROM api_logs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 100
            """, subject_identifier if user_data else None)
            
            # Get authentication logs
            auth_data = await conn.fetch("""
                SELECT login_time, ip_address, user_agent, success, failure_reason
                FROM authentication_logs 
                WHERE user_id = $1
                ORDER BY login_time DESC
                LIMIT 50
            """, subject_identifier if user_data else None)
        
        return {
            "user_profile": dict(user_data) if user_data else {},
            "api_usage": [dict(row) for row in api_data],
            "authentication_history": [dict(row) for row in auth_data],
            "data_collection_date": datetime.utcnow().isoformat(),
            "note": "This data is provided in response to your GDPR Article 15 access request"
        }
    
    async def _get_request(self, request_id: str) -> Optional[DataSubjectRequest]:
        """Get data subject request by ID"""
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT request_id, subject_identifier, right_requested, request_details,
                       submitted_at, identity_verified, status, due_date, assigned_to
                FROM data_subject_requests 
                WHERE request_id = $1
            """, request_id)
        
        if not row:
            return None
        
        return DataSubjectRequest(
            request_id=row['request_id'],
            subject_identifier=row['subject_identifier'],
            right_requested=DataSubjectRight(row['right_requested']),
            request_details=row['request_details'],
            submitted_at=row['submitted_at'],
            identity_verified=row['identity_verified'],
            status=row['status'],
            due_date=row['due_date'],
            assigned_to=row['assigned_to']
        )
    
    async def _send_request_acknowledgment(self, request: DataSubjectRequest):
        """Send acknowledgment email for data subject request"""
        
        subject = f"Data Subject Request Acknowledgment - {request.request_id}"
        
        body = f"""
        Dear Data Subject,
        
        We have received your data subject request under the GDPR.
        
        Request Details:
        - Request ID: {request.request_id}
        - Right Requested: {request.right_requested.value}
        - Submitted: {request.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
        - Response Due: {request.due_date.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        We will process your request within one month as required by the GDPR. You will receive a response before {request.due_date.strftime('%Y-%m-%d')}.
        
        If you have any questions about this request, please contact us at privacy@yourdomain.com.
        
        Best regards,
        Data Protection Team
        """
        
        await self.email_service.send_email(
            to=request.subject_identifier,
            subject=subject,
            body=body
        )
    
    async def _send_identity_verification_email(self, request: DataSubjectRequest):
        """Send identity verification email"""
        
        # Generate verification code (in production, use secure random generation)
        verification_code = "123456"  # This should be a secure random code
        
        subject = f"Identity Verification - Data Subject Request {request.request_id}"
        
        body = f"""
        Dear Data Subject,
        
        To process your data subject request, we need to verify your identity.
        
        Verification Code: {verification_code}
        
        Please use this code to verify your identity through our online portal.
        
        This verification code will expire in 24 hours.
        
        Best regards,
        Data Protection Team
        """
        
        await self.email_service.send_email(
            to=request.subject_identifier,
            subject=subject,
            body=body
        )
    
    async def _store_response_data(self, request_id: str, response_data: Dict[str, Any]):
        """Store response data for audit purposes"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE data_subject_requests 
                SET response_data = $2, status = 'completed', completed_at = NOW()
                WHERE request_id = $1
            """, request_id, json.dumps(response_data))
    
    def generate_data_subject_rights_report(self) -> Dict[str, Any]:
        """Generate comprehensive data subject rights report"""
        
        return {
            "report_metadata": {
                "generation_date": datetime.utcnow().isoformat(),
                "report_period": "Last 12 months",
                "total_requests": "Calculated from database"
            },
            "legal_framework": {
                "gdpr_articles": [15, 16, 17, 18, 20, 21, 22],
                "applicable_laws": ["GDPR", "Data Protection Act 2018"],
                "supervisory_authority": "Information Commissioner's Office (ICO)"
            },
            "request_statistics": {
                "by_right_type": "Statistics to be calculated",
                "by_status": "Statistics to be calculated", 
                "average_response_time": "Statistics to be calculated",
                "requests_received": "Statistics to be calculated"
            },
            "process_summary": {
                "identity_verification": "Multi-factor verification required",
                "response_timeframe": "30 days (extendable by 60 days)",
                "response_format": "Electronic format where possible",
                "fee_structure": "No fee for reasonable requests"
            },
            "compliance_measures": [
                "Automated request tracking system",
                "Response time monitoring",
                "Regular process review and optimization",
                "Staff training on data subject rights",
                "Documentation of all requests and responses"
            ]
        }
```

## Audit and Compliance Monitoring

### 1. Compliance Monitoring Framework

**File**: `compliance/compliance_monitor.py`
```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL_COMPLIANCE = "partial_compliance"
    UNDER_REVIEW = "under_review"
    REQUIRES_ACTION = "requires_action"

class ComplianceCheck(Enum):
    """Types of compliance checks"""
    DATA_RETENTION = "data_retention"
    ACCESS_CONTROLS = "access_controls"
    ENCRYPTION_STATUS = "encryption_status"
    AUDIT_LOGGING = "audit_logging"
    DATA_SUBJECT_RIGHTS = "data_subject_rights"
    BREACH_NOTIFICATION = "breach_notification"
    THIRD_PARTY_ASSESSMENTS = "third_party_assessments"

@dataclass
class ComplianceFinding:
    """Represents a compliance finding"""
    check_id: str
    check_type: ComplianceCheck
    status: ComplianceStatus
    severity: str  # low, medium, high, critical
    description: str
    recommendation: str
    due_date: Optional[datetime]
    assigned_to: Optional[str]
    evidence: List[str]
    created_at: datetime
    updated_at: datetime

class ComplianceMonitor:
    """Comprehensive compliance monitoring system"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.check_schedules = self._initialize_check_schedules()
        self.last_check_results = {}
    
    def _initialize_check_schedules(self) -> Dict[ComplianceCheck, Dict[str, Any]]:
        """Initialize compliance check schedules"""
        
        return {
            ComplianceCheck.DATA_RETENTION: {
                "frequency": "daily",
                "last_run": None,
                "next_due": None,
                "timeout_hours": 2
            },
            ComplianceCheck.ACCESS_CONTROLS: {
                "frequency": "weekly", 
                "last_run": None,
                "next_due": None,
                "timeout_hours": 4
            },
            ComplianceCheck.ENCRYPTION_STATUS: {
                "frequency": "daily",
                "last_run": None,
                "next_due": None,
                "timeout_hours": 1
            },
            ComplianceCheck.AUDIT_LOGGING: {
                "frequency": "daily",
                "last_run": None,
                "next_due": None,
                "timeout_hours": 1
            },
            ComplianceCheck.DATA_SUBJECT_RIGHTS: {
                "frequency": "weekly",
                "last_run": None,
                "next_due": None,
                "timeout_hours": 8
            },
            ComplianceCheck.BREACH_NOTIFICATION: {
                "frequency": "real_time",
                "last_run": None,
                "next_due": None,
                "timeout_hours": 0
            }
        }
    
    async def run_compliance_check(self, check_type: ComplianceCheck) -> List[ComplianceFinding]:
        """Run a specific compliance check"""
        
        check_methods = {
            ComplianceCheck.DATA_RETENTION: self._check_data_retention,
            ComplianceCheck.ACCESS_CONTROLS: self._check_access_controls,
            ComplianceCheck.ENCRYPTION_STATUS: self._check_encryption_status,
            ComplianceCheck.AUDIT_LOGGING: self._check_audit_logging,
            ComplianceCheck.DATA_SUBJECT_RIGHTS: self._check_data_subject_rights,
            ComplianceCheck.BREACH_NOTIFICATION: self._check_breach_notification
        }
        
        if check_type not in check_methods:
            raise ValueError(f"Unknown compliance check: {check_type}")
        
        # Execute the check
        findings = await check_methods[check_type]()
        
        # Store results
        await self._store_compliance_findings(check_type, findings)
        
        # Update schedule
        self._update_check_schedule(check_type)
        
        # Check for urgent findings
        urgent_findings = [f for f in findings if f.severity in ["high", "critical"]]
        if urgent_findings:
            await self._send_urgent_compliance_alert(check_type, urgent_findings)
        
        return findings
    
    async def _check_data_retention(self) -> List[ComplianceFinding]:
        """Check data retention policy compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            # Check for data exceeding retention periods
            expired_data = await conn.fetch("""
                SELECT 
                    'threat_intelligence' as table_name,
                    COUNT(*) as expired_count,
                    MAX(created_at) as oldest_expired
                FROM threat_intelligence 
                WHERE created_at < NOW() - INTERVAL '7 years'
                AND is_active = false
                
                UNION ALL
                
                SELECT 
                    'api_logs' as table_name,
                    COUNT(*) as expired_count,
                    MAX(created_at) as oldest_expired
                FROM api_logs 
                WHERE created_at < NOW() - INTERVAL '1 year'
                
                UNION ALL
                
                SELECT 
                    'authentication_logs' as table_name,
                    COUNT(*) as expired_count,
                    MAX(login_time) as oldest_expired
                FROM authentication_logs 
                WHERE login_time < NOW() - INTERVAL '7 years'
            """)
            
            for row in expired_data:
                if row['expired_count'] > 0:
                    findings.append(ComplianceFinding(
                        check_id=f"retention_{row['table_name']}_{current_time.timestamp()}",
                        check_type=ComplianceCheck.DATA_RETENTION,
                        status=ComplianceStatus.NON_COMPLIANT,
                        severity="high",
                        description=f"Found {row['expired_count']} records in {row['table_name']} exceeding retention period",
                        recommendation="Execute data cleanup procedures to remove expired data",
                        due_date=current_time + timedelta(days=7),
                        assigned_to="data_protection_officer",
                        evidence=[f"Oldest expired record: {row['oldest_expired']}"],
                        created_at=current_time,
                        updated_at=current_time
                    ))
        
        # Check retention policy documentation
        async with self.db_pool.acquire() as conn:
            policy_exists = await conn.fetchval("""
                SELECT COUNT(*) FROM policy_documents 
                WHERE policy_type = 'data_retention' 
                AND is_current = true
                AND effective_date < NOW()
            """)
            
            if policy_exists == 0:
                findings.append(ComplianceFinding(
                    check_id=f"retention_policy_{current_time.timestamp()}",
                    check_type=ComplianceCheck.DATA_RETENTION,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity="critical",
                    description="No current data retention policy documented",
                    recommendation="Create and publish comprehensive data retention policy",
                    due_date=current_time + timedelta(days=30),
                    assigned_to="legal_team",
                    evidence=["Policy document not found"],
                    created_at=current_time,
                    updated_at=current_time
                ))
        
        return findings
    
    async def _check_access_controls(self) -> List[ComplianceFinding]:
        """Check access control compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            # Check for excessive privileges
            excessive_privileges = await conn.fetch("""
                SELECT 
                    u.username,
                    u.role,
                    COUNT(ua.action) as recent_actions
                FROM users u
                LEFT JOIN user_audit ua ON u.id = ua.user_id 
                    AND ua.timestamp > NOW() - INTERVAL '30 days'
                WHERE u.role IN ('admin', 'super_admin')
                AND (ua.action IS NULL OR ua.action = 'read')
                GROUP BY u.id, u.username, u.role
                HAVING COUNT(ua.action) = 0
            """)
            
            if excessive_privileges:
                for row in excessive_privileges:
                    findings.append(ComplianceFinding(
                        check_id=f"access_{row['username']}_{current_time.timestamp()}",
                        check_type=ComplianceCheck.ACCESS_CONTROLS,
                        status=ComplianceStatus.PARTIAL_COMPLIANCE,
                        severity="medium",
                        description=f"User {row['username']} ({row['role']}) has admin privileges but limited recent activity",
                        recommendation="Review and potentially revoke unnecessary admin privileges",
                        due_date=current_time + timedelta(days=14),
                        assigned_to="security_team",
                        evidence=[f"Recent admin actions: {row['recent_actions']}"],
                        created_at=current_time,
                        updated_at=current_time
                    ))
            
            # Check for dormant accounts
            dormant_accounts = await conn.fetch("""
                SELECT username, last_login, created_at
                FROM users 
                WHERE last_login < NOW() - INTERVAL '90 days'
                AND is_active = true
            """)
            
            if dormant_accounts:
                findings.append(ComplianceFinding(
                    check_id=f"dormant_accounts_{current_time.timestamp()}",
                    check_type=ComplianceCheck.ACCESS_CONTROLS,
                    status=ComplianceStatus.REQUIRES_ACTION,
                    severity="medium",
                    description=f"Found {len(dormant_accounts)} dormant user accounts",
                    recommendation="Review and potentially deactivate dormant accounts",
                    due_date=current_time + timedelta(days=30),
                    assigned_to="security_team",
                    evidence=[f"Dormant accounts: {[acc['username'] for acc in dormant_accounts]}"],
                    created_at=current_time,
                    updated_at=current_time
                ))
        
        return findings
    
    async def _check_encryption_status(self) -> List[ComplianceFinding]:
        """Check encryption compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        # Check database encryption
        try:
            async with self.db_pool.acquire() as conn:
                ssl_enabled = await conn.fetchval("SHOW ssl;")
                
                if not ssl_enabled:
                    findings.append(ComplianceFinding(
                        check_id=f"ssl_{current_time.timestamp()}",
                        check_type=ComplianceCheck.ENCRYPTION_STATUS,
                        status=ComplianceStatus.NON_COMPLIANT,
                        severity="critical",
                        description="Database SSL/TLS encryption is not enabled",
                        recommendation="Enable SSL/TLS encryption for all database connections",
                        due_date=current_time + timedelta(days=1),
                        assigned_to="database_team",
                        evidence=["SSL status check returned false"],
                        created_at=current_time,
                        updated_at=current_time
                    ))
        except Exception as e:
            findings.append(ComplianceFinding(
                check_id=f"ssl_check_error_{current_time.timestamp()}",
                check_type=ComplianceCheck.ENCRYPTION_STATUS,
                status=ComplianceStatus.NON_COMPLIANT,
                severity="high",
                description=f"Unable to verify SSL status: {str(e)}",
                recommendation="Manually verify and enable database SSL encryption",
                due_date=current_time + timedelta(days=3),
                assigned_to="database_team",
                evidence=[f"Error: {str(e)}"],
                created_at=current_time,
                updated_at=current_time
            ))
        
        # Check for encrypted sensitive columns
        async with self.db_pool.acquire() as conn:
            unencrypted_sensitive = await conn.fetch("""
                SELECT COUNT(*) as count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'users'
                AND column_name IN ('password_hash', 'email')
                AND data_type = 'character varying'  # Should be encrypted
            """)
            
            if unencrypted_sensitive[0]['count'] > 0:
                findings.append(ComplianceFinding(
                    check_id=f"column_encryption_{current_time.timestamp()}",
                    check_type=ComplianceCheck.ENCRYPTION_STATUS,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity="high",
                    description="Found potentially unencrypted sensitive columns",
                    recommendation="Implement column-level encryption for sensitive data",
                    due_date=current_time + timedelta(days=7),
                    assigned_to="development_team",
                    evidence=["Unencrypted sensitive columns detected"],
                    created_at=current_time,
                    updated_at=current_time
                ))
        
        return findings
    
    async def _check_audit_logging(self) -> List[ComplianceFinding]:
        """Check audit logging compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            # Check recent audit log coverage
            audit_coverage = await conn.fetch("""
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(al.id) as logged_requests,
                    ROUND(COUNT(al.id) * 100.0 / COUNT(*), 2) as coverage_percentage
                FROM api_requests ar
                LEFT JOIN audit_logs al ON ar.id = al.request_id
                WHERE ar.created_at > NOW() - INTERVAL '24 hours'
            """)
            
            coverage = audit_coverage[0]['coverage_percentage'] if audit_coverage else 0
            
            if coverage < 95:
                findings.append(ComplianceFinding(
                    check_id=f"audit_coverage_{current_time.timestamp()}",
                    check_type=ComplianceCheck.AUDIT_LOGGING,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity="medium",
                    description=f"Audit log coverage is {coverage}%, below required 95%",
                    recommendation="Investigate and fix audit logging gaps",
                    due_date=current_time + timedelta(days=3),
                    assigned_to="development_team",
                    evidence=[f"Coverage: {coverage}%"],
                    created_at=current_time,
                    updated_at=current_time
                ))
            
            # Check for missing critical event types
            missing_events = await conn.fetch("""
                SELECT DISTINCT event_type
                FROM audit_events
                WHERE timestamp > NOW() - INTERVAL '30 days'
            """)
            
            expected_events = ['authentication', 'authorization', 'data_access', 'data_modification']
            found_events = [row['event_type'] for row in missing_events]
            missing_event_types = set(expected_events) - set(found_events)
            
            if missing_event_types:
                findings.append(ComplianceFinding(
                    check_id=f"audit_events_{current_time.timestamp()}",
                    check_type=ComplianceCheck.AUDIT_LOGGING,
                    status=ComplianceStatus.PARTIAL_COMPLIANCE,
                    severity="medium",
                    description=f"Missing audit events: {', '.join(missing_event_types)}",
                    recommendation="Implement comprehensive audit event logging",
                    due_date=current_time + timedelta(days=7),
                    assigned_to="development_team",
                    evidence=[f"Missing event types: {list(missing_event_types)}"],
                    created_at=current_time,
                    updated_at=current_time
                ))
        
        return findings
    
    async def _check_data_subject_rights(self) -> List[ComplianceFinding]:
        """Check data subject rights compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            # Check response times for data subject requests
            overdue_requests = await conn.fetch("""
                SELECT request_id, subject_identifier, right_requested, due_date
                FROM data_subject_requests
                WHERE status = 'in_progress'
                AND due_date < NOW()
            """)
            
            if overdue_requests:
                findings.append(ComplianceFinding(
                    check_id=f"overdue_requests_{current_time.timestamp()}",
                    check_type=ComplianceCheck.DATA_SUBJECT_RIGHTS,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity="critical",
                    description=f"Found {len(overdue_requests)} overdue data subject requests",
                    recommendation="Immediately process overdue data subject requests",
                    due_date=current_time + timedelta(days=1),
                    assigned_to="data_protection_officer",
                    evidence=[f"Overdue requests: {list(overdue_requests)}"],
                    created_at=current_time,
                    updated_at=current_time
                ))
            
            # Check for requests approaching deadline
            approaching_deadline = await conn.fetch("""
                SELECT request_id, subject_identifier, due_date
                FROM data_subject_requests
                WHERE status = 'in_progress'
                AND due_date BETWEEN NOW() AND NOW() + INTERVAL '3 days'
            """)
            
            if approaching_deadline:
                findings.append(ComplianceFinding(
                    check_id=f"approaching_deadlines_{current_time.timestamp()}",
                    check_type=ComplianceCheck.DATA_SUBJECT_RIGHTS,
                    status=ComplianceStatus.REQUIRES_ACTION,
                    severity="high",
                    description=f"Found {len(approaching_deadline)} requests approaching deadline",
                    recommendation="Prioritize data subject requests approaching deadlines",
                    due_date=current_time + timedelta(days=1),
                    assigned_to="data_protection_officer",
                    evidence=[f"Requests: {list(approaching_deadline)}"],
                    created_at=current_time,
                    updated_at=current_time
                ))
        
        return findings
    
    async def _check_breach_notification(self) -> List[ComplianceFinding]:
        """Check breach notification compliance"""
        
        findings = []
        current_time = datetime.utcnow()
        
        async with self.db_pool.acquire() as conn:
            # Check for unreported incidents
            unreported_incidents = await conn.fetch("""
                SELECT incident_id, incident_type, severity, detected_at
                FROM security_incidents
                WHERE severity IN ('high', 'critical')
                AND is_reported = false
                AND detected_at > NOW() - INTERVAL '72 hours'
            """)
            
            if unreported_incidents:
                for incident in unreported_incidents:
                    # Calculate time since detection
                    hours_since_detection = (
                        current_time - incident['detected_at']
                    ).total_seconds() / 3600
                    
                    severity = "critical" if incident['severity'] == 'critical' else "high"
                    
                    if hours_since_detection > 72:
                        status = ComplianceStatus.NON_COMPLIANT
                        severity_level = "critical"
                        due_date = current_time + timedelta(hours=1)
                    else:
                        status = ComplianceStatus.REQUIRES_ACTION
                        severity_level = "high"
                        due_date = current_time + timedelta(days=1)
                    
                    findings.append(ComplianceFinding(
                        check_id=f"breach_notification_{incident['incident_id']}_{current_time.timestamp()}",
                        check_type=ComplianceCheck.BREACH_NOTIFICATION,
                        status=status,
                        severity=severity_level,
                        description=f"Security incident {incident['incident_id']} may require breach notification",
                        recommendation="Assess if breach notification is required and notify if necessary",
                        due_date=due_date,
                        assigned_to="incident_response_team",
                        evidence=[
                            f"Incident type: {incident['incident_type']}",
                            f"Detected: {incident['detected_at']}",
                            f"Hours since detection: {hours_since_detection:.1f}"
                        ],
                        created_at=current_time,
                        updated_at=current_time
                    ))
        
        return findings
    
    async def _store_compliance_findings(
        self, 
        check_type: ComplianceCheck, 
        findings: List[ComplianceFinding]
    ):
        """Store compliance findings in database"""
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                for finding in findings:
                    await conn.execute("""
                        INSERT INTO compliance_findings (
                            check_id, check_type, status, severity, description,
                            recommendation, due_date, assigned_to, evidence,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                        ON CONFLICT (check_id)
                        DO UPDATE SET
                            status = EXCLUDED.status,
                            severity = EXCLUDED.severity,
                            description = EXCLUDED.description,
                            recommendation = EXCLUDED.recommendation,
                            due_date = EXCLUDED.due_date,
                            assigned_to = EXCLUDED.assigned_to,
                            evidence = EXCLUDED.evidence,
                            updated_at = EXCLUDED.updated_at
                    """, finding.check_id, check_type.value, finding.status.value,
                         finding.severity, finding.description, finding.recommendation,
                         finding.due_date, finding.assigned_to, finding.evidence,
                         finding.created_at, finding.updated_at)
    
    def _update_check_schedule(self, check_type: ComplianceCheck):
        """Update check schedule after execution"""
        
        schedule = self.check_schedules[check_type]
        schedule['last_run'] = datetime.utcnow()
        
        if schedule['frequency'] == 'daily':
            schedule['next_due'] = schedule['last_run'] + timedelta(days=1)
        elif schedule['frequency'] == 'weekly':
            schedule['next_due'] = schedule['last_run'] + timedelta(weeks=1)
        elif schedule['frequency'] == 'real_time':
            schedule['next_due'] = schedule['last_run']
    
    async def _send_urgent_compliance_alert(
        self, 
        check_type: ComplianceCheck, 
        findings: List[ComplianceFinding]
    ):
        """Send urgent compliance alerts"""
        
        # Implementation would send alerts via email, Slack, etc.
        # This is a placeholder for the alert mechanism
        
        alert_data = {
            "check_type": check_type.value,
            "finding_count": len(findings),
            "high_severity_count": len([f for f in findings if f.severity == "high"]),
            "critical_severity_count": len([f for f in findings if f.severity == "critical"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log the alert (in production, would send actual notifications)
        print(f"URGENT COMPLIANCE ALERT: {alert_data}")
    
    async def generate_compliance_dashboard(self) -> Dict[str, Any]:
        """Generate compliance monitoring dashboard data"""
        
        current_time = datetime.utcnow()
        
        # Get recent findings
        async with self.db_pool.acquire() as conn:
            recent_findings = await conn.fetch("""
                SELECT check_type, status, severity, COUNT(*) as count
                FROM compliance_findings
                WHERE created_at > NOW() - INTERVAL '30 days'
                GROUP BY check_type, status, severity
                ORDER BY check_type, severity
            """)
            
            overdue_actions = await conn.fetch("""
                SELECT COUNT(*) as count
                FROM compliance_findings
                WHERE due_date < NOW()
                AND status != 'resolved'
            """)
            
            compliance_trend = await conn.fetch("""
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) FILTER (WHERE status = 'compliant') as compliant,
                    COUNT(*) FILTER (WHERE status = 'non_compliant') as non_compliant,
                    COUNT(*) FILTER (WHERE status = 'partial_compliance') as partial
                FROM compliance_findings
                WHERE created_at > NOW() - INTERVAL '30 days'
                GROUP BY DATE(created_at)
                ORDER BY date
            """)
        
        return {
            "dashboard_metadata": {
                "generated_at": current_time.isoformat(),
                "report_period": "Last 30 days",
                "system_status": "operational"
            },
            "compliance_summary": {
                "total_checks": len(ComplianceCheck),
                "overdue_actions": overdue_findings[0]['count'] if overdue_findings else 0,
                "recent_findings": len(recent_findings),
                "compliance_score": self._calculate_compliance_score(recent_findings)
            },
            "findings_by_type": self._group_findings_by_type(recent_findings),
            "compliance_trend": [dict(row) for row in compliance_trend],
            "scheduled_checks": {
                check_type.value: {
                    "frequency": schedule['frequency'],
                    "last_run": schedule['last_run'].isoformat() if schedule['last_run'] else None,
                    "next_due": schedule['next_due'].isoformat() if schedule['next_due'] else None
                }
                for check_type, schedule in self.check_schedules.items()
            },
            "recommendations": [
                "Review and address all overdue compliance actions",
                "Implement automated compliance monitoring where possible",
                "Regular training for compliance teams",
                "Update compliance procedures based on regulatory changes"
            ]
        }
    
    def _calculate_compliance_score(self, findings) -> float:
        """Calculate overall compliance score (0-100)"""
        
        if not findings:
            return 100.0
        
        total_findings = sum(row['count'] for row in findings)
        compliant_findings = sum(
            row['count'] for row in findings 
            if row['status'] == 'compliant'
        )
        
        # Base score from compliant findings
        base_score = (compliant_findings / total_findings * 100) if total_findings > 0 else 100
        
        # Deduct points for high/critical findings
        penalty = sum(
            row['count'] for row in findings 
            if row['severity'] in ['high', 'critical'] and row['status'] != 'compliant'
        )
        
        final_score = max(0, base_score - (penalty * 5))  # 5 point penalty per high/critical finding
        
        return round(final_score, 1)
    
    def _group_findings_by_type(self, findings) -> Dict[str, Dict[str, int]]:
        """Group findings by check type and status"""
        
        grouped = {}
        for row in findings:
            check_type = row['check_type']
            if check_type not in grouped:
                grouped[check_type] = {}
            
            grouped[check_type][row['status']] = grouped[check_type].get(row['status'], 0) + row['count']
        
        return grouped
```

---

For operational compliance procedures, see the [Operational Runbook](../operations/operational-runbook.md).

For security considerations, see the [Security Considerations](../security/security-considerations.md).

For monitoring and alerting setup, see the [Monitoring README](../monitoring/README.md).

This comprehensive compliance documentation ensures the Cybersecurity Threat Intelligence System meets all applicable regulatory requirements and maintains the highest standards of data protection and privacy.
