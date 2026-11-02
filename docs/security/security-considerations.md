# Security Considerations

## Table of Contents
1. [Overview](#overview)
2. [Threat Model](#threat-model)
3. [Security Architecture](#security-architecture)
4. [Access Control](#access-control)
5. [Data Protection](#data-protection)
6. [Network Security](#network-security)
7. [Application Security](#application-security)
8. [Database Security](#database-security)
9. [Infrastructure Security](#infrastructure-security)
10. [Monitoring and Incident Response](#monitoring-and-incident-response)
11. [Security Hardening Guide](#security-hardening-guide)
12. [Compliance and Standards](#compliance-and-standards)

## Overview

This document outlines the security considerations, threat model, and security architecture for the Cybersecurity Threat Intelligence System. It provides comprehensive guidance for protecting sensitive threat intelligence data and maintaining system integrity.

**Security Objectives**:
- **Confidentiality**: Protect sensitive threat intelligence and user data
- **Integrity**: Ensure data accuracy and prevent unauthorized modifications
- **Availability**: Maintain system availability and prevent DoS attacks
- **Authentication**: Verify user and system identities
- **Authorization**: Control access based on roles and permissions
- **Auditability**: Maintain comprehensive audit trails

## Threat Model

### 1. Assets to Protect

#### 1.1 Data Assets
- **Threat Intelligence Data**: IP addresses, domains, email addresses, URLs
- **User Credentials**: API keys, authentication tokens, passwords
- **System Configuration**: Database credentials, API configurations
- **Audit Logs**: Authentication attempts, data access, system changes
- **External API Keys**: VirusTotal, AbuseIPDB, Shodan, GreyNoise, OTX

#### 1.2 System Components
- **API Service**: FastAPI application and authentication system
- **Databases**: PostgreSQL and MongoDB containing threat intelligence
- **Cache Layer**: Redis containing temporary data and session information
- **Monitoring Stack**: Prometheus, Grafana, ELK for system observability
- **Infrastructure**: Servers, networks, load balancers

### 2. Threat Actors

#### 2.1 External Threats
- **Cybercriminals**: Financial gain, data theft, system compromise
- **Nation-State Actors**: Espionage, intellectual property theft
- **Hacktivists**: Political motives, reputation damage
- **Script Kiddies**: Opportunistic attacks using automated tools
- **Competitors**: Industrial espionage, competitive intelligence theft

#### 2.2 Internal Threats
- **Malicious Insiders**: Disgruntled employees, compromised accounts
- **Negligent Users**: Accidental data exposure, policy violations
- **Compromised Accounts**: Stolen credentials, lateral movement
- **Third-Party Vendors**: Supply chain attacks, compromised dependencies

#### 2.3 Advanced Persistent Threats (APT)
- **Reconnaissance**: Initial foothold, credential harvesting
- **Lateral Movement**: Network traversal, privilege escalation
- **Data Exfiltration**: Silent data theft, threat intelligence compromise
- **Persistence**: Backdoor installation, mechanism maintenance

### 3. Attack Vectors

#### 3.1 Network-Based Attacks
- **SQL Injection**: Database compromise through application input
- **NoSQL Injection**: MongoDB exploitation via query manipulation
- **Cross-Site Scripting (XSS)**: Client-side code injection
- **Cross-Site Request Forgery (CSRF)**: Unauthorized actions
- **Man-in-the-Middle (MITM)**: Traffic interception and modification

#### 3.2 Authentication Attacks
- **Brute Force**: Credential guessing and password cracking
- **Credential Stuffing**: Using stolen credentials from other breaches
- **Token Hijacking**: Session token theft and replay
- **Rainbow Table Attacks**: Password hash cracking
- **Social Engineering**: Credential phishing and manipulation

#### 3.3 Application-Level Attacks
- **API Abuse**: Excessive requests, rate limit bypass
- **Business Logic Flaws**: Workflow manipulation, authorization bypass
- **Insecure Direct Object References**: Unauthorized data access
- **Server-Side Request Forgery (SSRF)**: Internal network exploitation
- **Deserialization Attacks**: Remote code execution

#### 3.4 Infrastructure Attacks
- **Container Escape**: Privilege escalation in Docker/Kubernetes
- **Kernel Exploits**: System-level vulnerability exploitation
- **Supply Chain Attacks**: Compromised dependencies and packages
- **DNS Poisoning**: Traffic redirection and cache poisoning
- **Certificate Spoofing**: SSL/TLS impersonation

### 4. Risk Assessment

#### 4.1 High-Risk Scenarios
| Threat | Likelihood | Impact | Risk Level | Mitigation Priority |
|--------|------------|---------|------------|---------------------|
| Credential Compromise | High | Critical | **CRITICAL** | P0 |
| Data Breach | Medium | Critical | **HIGH** | P0 |
| SQL Injection | Medium | High | **HIGH** | P1 |
| API Abuse | High | Medium | **MEDIUM** | P1 |
| DDoS Attack | Low | High | **MEDIUM** | P2 |

#### 4.2 Data Classification
- **Public**: System documentation, non-sensitive configurations
- **Internal**: System metrics, performance data
- **Confidential**: User profiles, API usage statistics
- **Restricted**: Threat intelligence data, authentication logs
- **Top Secret**: API keys, database credentials, encryption keys

## Security Architecture

### 1. Defense in Depth Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    External World                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS/TLS
┌─────────────────────────▼───────────────────────────────────┐
│                  Web Application Firewall                   │
│              (Rate Limiting, DDoS Protection)               │
└─────────────────────────┬───────────────────────────────────┘
                          │ Authenticated Requests
┌─────────────────────────▼───────────────────────────────────┐
│                  API Gateway/LB                             │
│              (SSL Termination, Routing)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ API Calls
┌─────────────────────────▼───────────────────────────────────┐
│                   FastAPI Application                       │
│         (Authentication, Authorization, Validation)         │
└─────────────────────────┬───────────────────────────────────┘
                          │ Database Queries
┌─────────────────────────▼───────────────────────────────────┐
│                  Application Layer                          │
│     (Business Logic, Input Validation, Error Handling)      │
└─────────────────────────┬───────────────────────────────────┘
                          │ Data Access
┌─────────────────────────▼───────────────────────────────────┐
│                    Data Access Layer                        │
│        (Connection Pooling, Query Parameterization)         │
└─────────────────────────┬───────────────────────────────────┘
                          │ SQL/NoSQL
┌─────────────────────────▼───────────────────────────────────┐
│                    Database Layer                           │
│    (Encryption, Access Control, Audit Logging)              │
└─────────────────────────┬───────────────────────────────────┘
                          │ I/O
┌─────────────────────────▼───────────────────────────────────┐
│                 Infrastructure Layer                        │
│         (Network Segmentation, Host Hardening)              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Security Controls Framework

#### 2.1 Preventive Controls
- **Authentication**: Multi-factor authentication, strong password policies
- **Authorization**: Role-based access control, principle of least privilege
- **Input Validation**: Strict input sanitization, parameter validation
- **Output Encoding**: XSS prevention, content security policy
- **Network Segmentation**: VLANs, firewalls, DMZ implementation

#### 2.2 Detective Controls
- **Monitoring**: Real-time threat detection, anomaly identification
- **Logging**: Comprehensive audit trails, security event correlation
- **Alerting**: Automated incident response, security team notifications
- **Forensics**: Evidence collection, attack reconstruction

#### 2.3 Corrective Controls
- **Incident Response**: Rapid threat containment, damage assessment
- **Recovery Procedures**: Data restoration, system recovery
- **Patch Management**: Vulnerability remediation, security updates
- **Backup and Recovery**: Disaster recovery planning

## Access Control

### 1. Authentication Framework

#### 1.1 User Authentication

**File**: `api/security/authentication.py`
```python
import jwt
import bcrypt
import pyotp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

class AuthenticationService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.token_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    def create_access_token(
        self, 
        user_id: str, 
        username: str, 
        role: str,
        mfa_verified: bool = True
    ) -> str:
        """Create JWT access token"""
        
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "mfa_verified": mfa_verified,
            "iat": now,
            "exp": expire,
            "jti": str(uuid.uuid4())  # Token ID for revocation
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Check token revocation
            if self._is_token_revoked(payload["jti"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed.encode('utf-8')
        )
    
    def generate_mfa_secret(self) -> str:
        """Generate TOTP secret for MFA"""
        return pyotp.random_base32()
    
    def get_mfa_uri(self, secret: str, username: str) -> str:
        """Generate TOTP URI for QR code"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="Threat Intelligence System"
        )
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def _is_token_revoked(self, token_id: str) -> bool:
        """Check if token has been revoked"""
        # Implementation would check against Redis/blacklist
        return False

# Rate limiting for authentication attempts
class AuthenticationRateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379)
        self.max_attempts = 5
        self.block_duration = 1800  # 30 minutes
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is temporarily blocked"""
        key = f"auth_block:{identifier}"
        return self.redis_client.exists(key)
    
    def record_failed_attempt(self, identifier: str):
        """Record failed authentication attempt"""
        key = f"auth_attempts:{identifier}"
        
        pipe = self.redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 3600)  # 1 hour window
        pipe.execute()
        
        # Check if should be blocked
        attempts = int(self.redis_client.get(key))
        if attempts >= self.max_attempts:
            block_key = f"auth_block:{identifier}"
            self.redis_client.setex(block_key, self.block_duration, "blocked")
    
    def reset_attempts(self, identifier: str):
        """Reset failed attempt counter on successful login"""
        for key in [f"auth_attempts:{identifier}", f"auth_block:{identifier}"]:
            self.redis_client.delete(key)
```

#### 1.2 Service-to-Service Authentication

**File**: `api/security/service_auth.py`
```python
import hmac
import hashlib
import secrets
from typing import Dict, Any

class ServiceAuthentication:
    def __init__(self):
        self.service_secrets: Dict[str, str] = {
            "monitoring": os.getenv("MONITORING_SERVICE_SECRET"),
            "backup": os.getenv("BACKUP_SERVICE_SECRET"),
            "alert": os.getenv("ALERT_SERVICE_SECRET")
        }
    
    def create_service_token(self, service_name: str, expires_in: int = 3600) -> str:
        """Create service-to-service authentication token"""
        
        if service_name not in self.service_secrets:
            raise ValueError(f"Unknown service: {service_name}")
        
        timestamp = int(time.time())
        expiry = timestamp + expires_in
        
        payload = f"{service_name}.{timestamp}.{expiry}"
        
        # Sign with service secret
        signature = hmac.new(
            self.service_secrets[service_name].encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{payload}.{signature}"
    
    def verify_service_token(self, token: str) -> Dict[str, Any]:
        """Verify service-to-service token"""
        
        try:
            parts = token.split('.')
            if len(parts) != 4:
                raise ValueError("Invalid token format")
            
            service_name, timestamp, expiry, signature = parts
            
            if service_name not in self.service_secrets:
                raise ValueError("Unknown service")
            
            # Verify signature
            payload = f"{service_name}.{timestamp}.{expiry}"
            expected_signature = hmac.new(
                self.service_secrets[service_name].encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                raise ValueError("Invalid signature")
            
            # Check expiration
            current_time = int(time.time())
            if current_time > int(expiry):
                raise ValueError("Token expired")
            
            return {
                "service": service_name,
                "issued_at": int(timestamp),
                "expires_at": int(expiry)
            }
            
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")
```

### 2. Authorization Framework

#### 2.1 Role-Based Access Control (RBAC)

**File**: `api/security/authorization.py`
```python
from enum import Enum
from typing import List, Set, Optional
from functools import wraps

class Permission(Enum):
    # Data Access Permissions
    READ_THREAT_INTEL = "read_threat_intelligence"
    WRITE_THREAT_INTEL = "write_threat_intelligence"
    DELETE_THREAT_INTEL = "delete_threat_intelligence"
    
    # Analysis Permissions
    RUN_ANALYSIS = "run_analysis"
    VIEW_ANALYTICS = "view_analytics"
    
    # Administration Permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    VIEW_LOGS = "view_logs"
    MANAGE_ALERTS = "manage_alerts"
    
    # API Management
    MANAGE_API_KEYS = "manage_api_keys"
    VIEW_API_STATS = "view_api_statistics"

class Role:
    def __init__(self, name: str, permissions: Set[Permission]):
        self.name = name
        self.permissions = permissions
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if role has any of the specified permissions"""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if role has all specified permissions"""
        return all(self.has_permission(p) for p in permissions)

# Predefined roles
ROLES = {
    "super_admin": Role(
        "super_admin",
        set(Permission)  # All permissions
    ),
    
    "security_analyst": Role(
        "security_analyst",
        {
            Permission.READ_THREAT_INTEL,
            Permission.WRITE_THREAT_INTEL,
            Permission.RUN_ANALYSIS,
            Permission.VIEW_ANALYTICS,
            Permission.MANAGE_ALERTS,
            Permission.VIEW_API_STATS
        }
    ),
    
    "read_only_analyst": Role(
        "read_only_analyst",
        {
            Permission.READ_THREAT_INTEL,
            Permission.VIEW_ANALYTICS
        }
    ),
    
    "system_operator": Role(
        "system_operator",
        {
            Permission.READ_THREAT_INTEL,
            Permission.VIEW_LOGS,
            Permission.MANAGE_ALERTS,
            Permission.VIEW_API_STATS
        }
    ),
    
    "api_client": Role(
        "api_client",
        {
            Permission.READ_THREAT_INTEL,
            Permission.RUN_ANALYSIS
        }
    )
}

class AuthorizationService:
    def __init__(self):
        self.roles = ROLES
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> role_names
    
    def check_permission(
        self, 
        user_id: str, 
        permission: Permission
    ) -> bool:
        """Check if user has specific permission"""
        
        if user_id not in self.user_roles:
            return False
        
        user_role_names = self.user_roles[user_id]
        
        for role_name in user_role_names:
            role = self.roles.get(role_name)
            if role and role.has_permission(permission):
                return True
        
        return False
    
    def require_permission(permission: Permission):
        """Decorator to require specific permission"""
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # This would be called from within FastAPI route
                # User info would be extracted from JWT token
                user_id = kwargs.get('current_user_id')
                
                if not user_id:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                
                auth_service = AuthorizationService()
                if not auth_service.check_permission(user_id, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission denied: {permission.value}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def require_any_permission(permissions: List[Permission]):
        """Decorator to require any of specified permissions"""
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user_id = kwargs.get('current_user_id')
                
                if not user_id:
                    raise HTTPException(
                        status_code=401,
                        detail="Authentication required"
                    )
                
                auth_service = AuthorizationService()
                user_role_names = auth_service.user_roles.get(user_id, set())
                
                has_permission = False
                for role_name in user_role_names:
                    role = auth_service.roles.get(role_name)
                    if role and role.has_any_permission(permissions):
                        has_permission = True
                        break
                
                if not has_permission:
                    raise HTTPException(
                        status_code=403,
                        detail="Insufficient permissions"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
```

#### 2.2 Attribute-Based Access Control (ABAC)

**File**: `api/security/abac.py`
```python
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import ipaddress

class AccessContext:
    """Context for access control decisions"""
    
    def __init__(
        self,
        user_id: str,
        user_roles: List[str],
        user_attributes: Dict[str, Any],
        resource_attributes: Dict[str, Any],
        action: str,
        environment_attributes: Dict[str, Any]
    ):
        self.user_id = user_id
        self.user_roles = user_roles
        self.user_attributes = user_attributes
        self.resource_attributes = resource_attributes
        self.action = action
        self.environment_attributes = environment_attributes

class Policy:
    """Access control policy"""
    
    def __init__(
        self,
        name: str,
        effect: str,  # "permit" or "deny"
        target: Dict[str, Any],  # Target resource/action
        condition: Optional[callable] = None
    ):
        self.name = name
        self.effect = effect
        self.target = target
        self.condition = condition

class ABACEngine:
    """Attribute-Based Access Control engine"""
    
    def __init__(self):
        self.policies: List[Policy] = [
            # Policy: Time-based access restriction
            Policy(
                name="business_hours_only",
                effect="permit",
                target={"action": "read_threat_data"},
                condition=self._check_business_hours
            ),
            
            # Policy: IP-based access restriction
            Policy(
                name="internal_network_only",
                effect="permit",
                target={"action": "manage_system"},
                condition=self._check_internal_network
            ),
            
            # Policy: Data classification access
            Policy(
                name="data_classification_access",
                effect="permit",
                target={"action": "read"},
                condition=self._check_data_classification
            ),
            
            # Policy: Department-based access
            Policy(
                name="department_access",
                effect="permit",
                target={"action": "read"},
                condition=self._check_department_access
            )
        ]
    
    def evaluate_access(self, context: AccessContext) -> bool:
        """Evaluate access based on policies"""
        
        # Find applicable policies
        applicable_policies = []
        for policy in self.policies:
            if self._matches_target(policy.target, context):
                if policy.condition is None or policy.condition(context):
                    applicable_policies.append(policy)
        
        # Apply policy combining algorithm (deny takes precedence)
        for policy in applicable_policies:
            if policy.effect == "deny":
                return False
        
        # If any permit policy matches, allow access
        for policy in applicable_policies:
            if policy.effect == "permit":
                return True
        
        # Default deny if no policies match
        return False
    
    def _matches_target(self, target: Dict[str, Any], context: AccessContext) -> bool:
        """Check if context matches policy target"""
        
        # Check action
        if "action" in target and target["action"] != context.action:
            return False
        
        # Check resource type
        if "resource_type" in target:
            if target["resource_type"] != context.resource_attributes.get("type"):
                return False
        
        return True
    
    def _check_business_hours(self, context: AccessContext) -> bool:
        """Check if current time is within business hours"""
        
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Business hours: 8 AM to 6 PM, Monday to Friday
        if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        return 8 <= current_hour < 18
    
    def _check_internal_network(self, context: AccessContext) -> bool:
        """Check if request is from internal network"""
        
        client_ip = context.environment_attributes.get("client_ip")
        if not client_ip:
            return False
        
        # Define internal network ranges
        internal_ranges = [
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12")
        ]
        
        try:
            client_ip_obj = ipaddress.ip_address(client_ip)
            return any(client_ip_obj in network for network in internal_ranges)
        except ValueError:
            return False
    
    def _check_data_classification(self, context: AccessContext) -> bool:
        """Check data classification access"""
        
        data_classification = context.resource_attributes.get("classification")
        user_clearance = context.user_attributes.get("security_clearance")
        
        # Clearance levels: public < internal < confidential < restricted
        clearance_levels = ["public", "internal", "confidential", "restricted"]
        
        try:
            user_level = clearance_levels.index(user_clearance)
            data_level = clearance_levels.index(data_classification)
            return user_level >= data_level
        except ValueError:
            return False
    
    def _check_department_access(self, context: AccessContext) -> bool:
        """Check department-based access"""
        
        user_department = context.user_attributes.get("department")
        resource_department = context.resource_attributes.get("department")
        
        # Admin users have access to all departments
        if "admin" in context.user_roles:
            return True
        
        # Security team has access to all threat intelligence
        if user_department == "security":
            return True
        
        # Users can access their own department's resources
        return user_department == resource_department
```

## Data Protection

### 1. Encryption Strategy

#### 1.1 Data-at-Rest Encryption

**Database Encryption Configuration**:
```sql
-- PostgreSQL encryption setup
-- Enable SSL connections
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
ssl_ca_file = 'ca.crt'

-- Column-level encryption for sensitive data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt API keys and tokens
CREATE TABLE encrypted_api_keys (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50) NOT NULL,
    encrypted_key BYTEA NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(plaintext TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(ciphertext BYTEA)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, current_setting('app.encryption_key'));
END;
$$ LANGUAGE plpgsql;

-- Set encryption key (should be from secure key management)
SET app.encryption_key = 'your-secure-encryption-key-here';

-- Encrypt existing API keys
UPDATE encrypted_api_keys 
SET encrypted_key = encrypt_sensitive_data('actual-api-key-value');
```

**File Encryption Service**:
```python
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class FileEncryptionService:
    def __init__(self):
        self.key = self._generate_or_load_key()
        self.cipher = Fernet(self.key)
    
    def _generate_or_load_key(self) -> bytes:
        """Generate or load encryption key"""
        key_file = "/secure/encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        os.chmod(key_file, 0o600)  # Owner read/write only
        
        with open(key_file, "wb") as f:
            f.write(key)
        
        return key
    
    def encrypt_file(self, file_path: str) -> bytes:
        """Encrypt file contents"""
        
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        return self.cipher.encrypt(file_data)
    
    def decrypt_file(self, encrypted_data: bytes) -> bytes:
        """Decrypt file contents"""
        
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_sensitive_config(self, config_data: dict) -> str:
        """Encrypt configuration data"""
        
        import json
        json_data = json.dumps(config_data)
        encrypted_data = self.cipher.encrypt(json_data.encode())
        
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_config(self, encrypted_b64: str) -> dict:
        """Decrypt configuration data"""
        
        import json
        encrypted_data = base64.b64decode(encrypted_b64.encode())
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        return json.loads(decrypted_data.decode())
```

#### 1.2 Data-in-Transit Encryption

**TLS Configuration**:
```nginx
# Nginx SSL/TLS configuration
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/ssl/certs/threat-intel.crt;
    ssl_certificate_key /etc/ssl/private/threat-intel.key;
    ssl_trusted_certificate /etc/ssl/certs/ca.crt;

    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # SSL session optimization
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;
    
    # HSTS preload (uncomment if ready for HSTS preload)
    # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
}
```

#### 1.3 Application-Level Encryption

```python
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class ApplicationEncryption:
    def __init__(self, master_key: str = None):
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY")
        if not self.master_key:
            raise ValueError("Encryption master key not provided")
        
        self.cipher = self._create_cipher()
    
    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher from master key"""
        
        # Use PBKDF2 to derive key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'threat_intel_salt',  # Use random salt in production
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        
        return Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_b64: str) -> str:
        """Decrypt sensitive data from storage"""
        
        encrypted_data = base64.b64decode(encrypted_b64.encode())
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        return decrypted_data.decode()
    
    def hash_sensitive_data(self, data: str, salt: str = None) -> str:
        """Create hash of sensitive data for comparison"""
        
        import hashlib
        
        if salt is None:
            salt = os.urandom(16).hex()
        
        # Use PBKDF2 with SHA-256
        pdkdf2 = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        
        return f"{salt}:{base64.b64encode(pdkdf2).decode()}"
    
    def verify_hash(self, data: str, hash_value: str) -> bool:
        """Verify hash of sensitive data"""
        
        try:
            salt, stored_hash = hash_value.split(':', 1)
            computed_hash = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
            
            return base64.b64decode(stored_hash) == computed_hash
        except ValueError:
            return False

# Usage example for API key encryption
class APIKeyManager:
    def __init__(self):
        self.encryption = ApplicationEncryption()
        self.db_pool = get_db_pool()  # Your database pool
    
    async def store_api_key(self, service_name: str, api_key: str) -> None:
        """Store encrypted API key"""
        
        encrypted_key = self.encryption.encrypt_sensitive_data(api_key)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO api_keys (service_name, encrypted_key)
                VALUES ($1, $2)
                ON CONFLICT (service_name)
                DO UPDATE SET encrypted_key = $2, updated_at = NOW()
            """, service_name, encrypted_key)
    
    async def get_api_key(self, service_name: str) -> str:
        """Retrieve and decrypt API key"""
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT encrypted_key FROM api_keys WHERE service_name = $1
            """, service_name)
            
            if not row:
                raise ValueError(f"API key not found for service: {service_name}")
            
            return self.encryption.decrypt_sensitive_data(row['encrypted_key'])
```

### 2. Data Classification and Handling

#### 2.1 Data Classification Framework

```python
from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class DataClassificationRule:
    """Rule for classifying data based on patterns"""
    pattern: str
    classification: DataClassification
    description: str
    required_approval: bool = False
    retention_days: Optional[int] = None

class DataClassificationEngine:
    """Engine for automatic data classification"""
    
    def __init__(self):
        self.rules = [
            # IP addresses - Internal data
            DataClassificationRule(
                pattern=r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
                classification=DataClassification.INTERNAL,
                description="IP addresses"
            ),
            
            # Email addresses - Confidential
            DataClassificationRule(
                pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                classification=DataClassification.CONFIDENTIAL,
                description="Email addresses"
            ),
            
            # API keys - Restricted
            DataClassificationRule(
                pattern=r"[a-f0-9]{32,}",
                classification=DataClassification.RESTRICTED,
                description="API keys and tokens",
                required_approval=True,
                retention_days=90
            ),
            
            # Domain names - Internal
            DataClassificationRule(
                pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$",
                classification=DataClassification.INTERNAL,
                description="Domain names"
            )
        ]
    
    def classify_data(self, data: Any, field_name: str = None) -> DataClassification:
        """Classify data based on content and rules"""
        
        import re
        
        data_str = str(data).lower()
        
        # Check each rule
        for rule in self.rules:
            if re.search(rule.pattern, data_str):
                return rule.classification
        
        # Default classification
        return DataClassification.INTERNAL
    
    def get_handling_requirements(self, classification: DataClassification) -> Dict[str, Any]:
        """Get handling requirements for data classification"""
        
        requirements = {
            DataClassification.PUBLIC: {
                "encryption_required": False,
                "access_control": "none",
                "audit_required": False,
                "backup_required": True,
                "retention_days": None
            },
            DataClassification.INTERNAL: {
                "encryption_required": True,
                "access_control": "authenticated_users",
                "audit_required": True,
                "backup_required": True,
                "retention_days": 365
            },
            DataClassification.CONFIDENTIAL: {
                "encryption_required": True,
                "access_control": "authorized_roles",
                "audit_required": True,
                "backup_required": True,
                "retention_days": 2555  # 7 years
            },
            DataClassification.RESTRICTED: {
                "encryption_required": True,
                "access_control": "admin_only",
                "audit_required": True,
                "backup_required": True,
                "retention_days": 2555  # 7 years
            }
        }
        
        return requirements.get(classification, {})
```

#### 2.2 Data Privacy and GDPR Compliance

```python
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid

class GDPRComplianceManager:
    """GDPR compliance management"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.retention_days = {
            "threat_intelligence": 2555,  # 7 years
            "user_data": 2555,            # 7 years
            "audit_logs": 2555,           # 7 years
            "api_logs": 365,              # 1 year
            "session_data": 30            # 30 days
        }
    
    async def anonymize_user_data(self, user_id: str) -> Dict[str, Any]:
        """Anonymize user data for GDPR compliance"""
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Anonymize user profile
                await conn.execute("""
                    UPDATE users 
                    SET 
                        username = CONCAT('deleted_user_', $1),
                        email = CONCAT('deleted_', $1, '@example.com'),
                        first_name = NULL,
                        last_name = NULL,
                        phone = NULL,
                        department = NULL,
                        position = NULL,
                        is_anonymized = true,
                        anonymized_at = NOW()
                    WHERE id = $1
                """, user_id)
                
                # Anonymize API keys
                await conn.execute("""
                    UPDATE api_keys 
                    SET 
                        description = 'Anonymized key',
                        encrypted_key = 'anonymized'
                    WHERE user_id = $1
                """, user_id)
                
                # Remove from audit logs (but keep non-personal data)
                await conn.execute("""
                    DELETE FROM authentication_logs 
                    WHERE user_id = $1
                """, user_id)
    
    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for GDPR right to portability"""
        
        async with self.db_pool.acquire() as conn:
            # Get user profile
            user_profile = await conn.fetchrow("""
                SELECT id, username, email, first_name, last_name, 
                       department, position, created_at, last_login,
                       is_active, is_anonymized
                FROM users 
                WHERE id = $1
            """, user_id)
            
            # Get user's threat intelligence data
            threat_data = await conn.fetch("""
                SELECT indicator_type, indicator_value, confidence_score,
                       source_name, created_at, last_seen, is_active
                FROM threat_intelligence ti
                JOIN threat_sources ts ON ti.source_id = ts.id
                WHERE ti.created_by = $1
                ORDER BY created_at DESC
            """, user_id)
            
            # Get API usage statistics
            api_usage = await conn.fetch("""
                SELECT endpoint, method, status_code, response_time,
                       created_at
                FROM api_logs 
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 1000
            """, user_id)
            
            return {
                "export_timestamp": datetime.utcnow().isoformat(),
                "user_profile": dict(user_profile) if user_profile else {},
                "threat_intelligence_data": [dict(row) for row in threat_data],
                "api_usage_data": [dict(row) for row in api_usage]
            }
    
    async def schedule_data_deletion(self, user_id: str, deletion_date: datetime) -> None:
        """Schedule data deletion for GDPR right to be forgotten"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO data_deletion_schedule (user_id, scheduled_for, status)
                VALUES ($1, $2, 'scheduled')
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    scheduled_for = $2,
                    status = 'scheduled',
                    updated_at = NOW()
            """, user_id, deletion_date)
    
    async def cleanup_expired_data(self) -> Dict[str, int]:
        """Clean up data based on retention policies"""
        
        cleanup_stats = {}
        
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Clean up old threat intelligence data
                threat_cutoff = datetime.utcnow() - timedelta(days=self.retention_days["threat_intelligence"])
                result = await conn.execute("""
                    DELETE FROM threat_intelligence 
                    WHERE created_at < $1 AND is_active = false
                """, threat_cutoff)
                cleanup_stats["threat_intelligence"] = self._get_affected_rows(result)
                
                # Clean up old API logs
                api_cutoff = datetime.utcnow() - timedelta(days=self.retention_days["api_logs"])
                result = await conn.execute("""
                    DELETE FROM api_logs 
                    WHERE created_at < $1
                """, api_cutoff)
                cleanup_stats["api_logs"] = self._get_affected_rows(result)
                
                # Clean up scheduled deletions that are past due
                result = await conn.execute("""
                    DELETE FROM data_deletion_schedule 
                    WHERE status = 'scheduled' 
                      AND scheduled_for < NOW()
                """, 0)  # Delete all past due
                cleanup_stats["scheduled_deletions"] = self._get_affected_rows(result)
        
        return cleanup_stats
    
    def _get_affected_rows(self, sql_result: str) -> int:
        """Extract number of affected rows from SQL result"""
        try:
            # Parse result like "DELETE 123"
            parts = sql_result.split()
            return int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            return 0
    
    async def generate_data_breach_report(self, incident_id: str) -> Dict[str, Any]:
        """Generate data breach notification report"""
        
        return {
            "incident_id": incident_id,
            "detection_timestamp": datetime.utcnow().isoformat(),
            "data_types_affected": [],
            "number_of_individuals": 0,
            "likely_consequences": "",
            "measures_taken": [],
            "contact_information": {
                "dpo_email": "dpo@yourdomain.com",
                "phone": "+1-555-DPO-HELP"
            }
        }
```

## Network Security

### 1. Network Segmentation

#### 1.1 Firewall Configuration

**File**: `security/firewall-rules.sh`
```bash
#!/bin/bash
# Comprehensive firewall configuration for Threat Intelligence System

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback interface
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH from management network only (192.168.100.0/24)
iptables -A INPUT -p tcp --dport 22 -s 192.168.100.0/24 -j ACCEPT

# Allow HTTP/HTTPS from anywhere (web traffic)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow internal network traffic for database connections
iptables -A INPUT -p tcp --dport 5432 -s 192.168.1.0/24 -j ACCEPT  # PostgreSQL
iptables -A INPUT -p tcp --dport 27017 -s 192.168.1.0/24 -j ACCEPT # MongoDB
iptables -A INPUT -p tcp --dport 6379 -s 192.168.1.0/24 -j ACCEPT  # Redis

# Allow monitoring interfaces from management network
iptables -A INPUT -p tcp --dport 3000 -s 192.168.100.0/24 -j ACCEPT  # Grafana
iptables -A INPUT -p tcp --dport 9090 -s 192.168.100.0/24 -j ACCEPT  # Prometheus
iptables -A INPUT -p tcp --dport 9200 -s 192.168.100.0/24 -j ACCEPT  # Elasticsearch
iptables -A INPUT -p tcp --dport 5601 -s 192.168.100.0/24 -j ACCEPT  # Kibana

# Rate limiting for API endpoints
iptables -A INPUT -p tcp --dport 8000 -m limit --limit 25/minute --limit-burst 50 -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m state --state INVALID -j DROP

# Protection against port scanning
iptables -A INPUT -m state --state NEW -m recent --name portscan --rttl --rhash --set
iptables -A INPUT -m state --state NEW -m recent --name portscan --rttl --rhash --remove

# Logging of dropped packets
iptables -A INPUT -j LOG --log-prefix "DROP: "
iptables -A INPUT -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4

# IPv6 firewall (similar rules)
ip6tables -F
ip6tables -X
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT ACCEPT

# Allow loopback
ip6tables -A INPUT -i lo -j ACCEPT
ip6tables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Save IPv6 rules
ip6tables-save > /etc/iptables/rules.v6
```

#### 1.2 Network Isolation

**Docker Network Configuration**:
```yaml
# docker-compose.network.yml
version: '3.8'

networks:
  threat-intel-frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.name: threat-intel-fe
  
  threat-intel-backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
    driver_opts:
      com.docker.network.bridge.name: threat-intel-be
  
  threat-intel-monitoring:
    driver: bridge
    ipam:
      config:
        - subnet: 172.22.0.0/16
    driver_opts:
      com.docker.network.bridge.name: threat-intel-mon

  threat-intel-db:
    driver: bridge
    ipam:
      config:
        - subnet: 172.23.0.0/16
    driver_opts:
      com.docker.network.bridge.name: threat-intel-db

services:
  # Frontend services (API, Load Balancer)
  nginx:
    networks:
      - threat-intel-frontend
    ports:
      - "80:80"
      - "443:443"

  api:
    networks:
      - threat-intel-frontend
      - threat-intel-backend
    depends_on:
      - postgres
      - mongodb
      - redis

  # Backend services (Databases)
  postgres:
    networks:
      - threat-intel-backend
      - threat-intel-db
    # No external ports exposed

  mongodb:
    networks:
      - threat-intel-backend
      - threat-intel-db
    # No external ports exposed

  redis:
    networks:
      - threat-intel-backend
      - threat-intel-db
    # No external ports exposed

  # Monitoring services
  prometheus:
    networks:
      - threat-intel-monitoring
      - threat-intel-backend
    ports:
      - "9090:9090"  # Only from management network

  grafana:
    networks:
      - threat-intel-monitoring
      - threat-intel-backend
    ports:
      - "3000:3000"  # Only from management network
```

### 2. SSL/TLS Security

#### 2.1 Certificate Management

```python
import ssl
import socket
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import datetime

class CertificateManager:
    """Manage SSL/TLS certificates"""
    
    def __init__(self, ca_certificate_path: str, ca_key_path: str):
        self.ca_cert_path = ca_certificate_path
        self.ca_key_path = ca_key_path
        self.ca_cert = None
        self.ca_key = None
        self._load_ca_certificate()
    
    def _load_ca_certificate(self):
        """Load CA certificate and key"""
        
        with open(self.ca_cert_path, 'rb') as f:
            self.ca_cert = x509.load_pem_x509_certificate(f.read())
        
        with open(self.ca_key_path, 'rb') as f:
            self.ca_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )
    
    def generate_certificate(
        self, 
        common_name: str, 
        san_dns_names: List[str] = None,
        valid_days: int = 365
    ) -> bytes:
        """Generate SSL certificate signed by internal CA"""
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        
        # Create certificate subject
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Threat Intelligence System"),
        ])
        
        # Create SAN extension
        san_names = []
        if san_dns_names:
            san_names = [x509.DNSName(name) for name in san_dns_names]
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=valid_days)
        ).add_extension(
            x509.SubjectAlternativeName(san_names),
            critical=False,
            # Sign the certificate
        ).sign(self.ca_key, hashes.SHA256())
        
        return cert.public_bytes(serialization.Encoding.PEM)
    
    def validate_certificate(self, cert_data: bytes) -> Dict[str, Any]:
        """Validate SSL certificate"""
        
        try:
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check expiration
            now = datetime.datetime.utcnow()
            is_expired = cert.not_valid_after < now
            days_until_expiry = (cert.not_valid_after - now).days
            
            # Check if self-signed
            is_self_signed = cert.issuer == cert.subject
            
            # Get key usage
            try:
                key_usage = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.KEY_USAGE
                ).value
                key_usage_dict = {
                    'digital_signature': key_usage.digital_signature,
                    'key_encipherment': key_usage.key_encipherment,
                    'key_agreement': key_usage.key_agreement,
                    'key_cert_sign': key_usage.key_cert_sign,
                    'crl_sign': key_usage.crl_sign
                }
            except x509.ExtensionNotFound:
                key_usage_dict = {}
            
            return {
                'valid': True,
                'subject': cert.subject.rfc4514_string(),
                'issuer': cert.issuer.rfc4514_string(),
                'serial_number': str(cert.serial_number),
                'not_valid_before': cert.not_valid_before.isoformat(),
                'not_valid_after': cert.not_valid_after.isoformat(),
                'days_until_expiry': days_until_expiry,
                'is_expired': is_expired,
                'is_self_signed': is_self_signed,
                'key_usage': key_usage_dict,
                'san_dns_names': self._extract_san_dns_names(cert)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _extract_san_dns_names(self, cert: x509.Certificate) -> List[str]:
        """Extract SAN DNS names from certificate"""
        
        try:
            san_ext = cert.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
            ).value
            
            dns_names = []
            for name in san_ext:
                if isinstance(name, x509.DNSName):
                    dns_names.append(name.value)
            
            return dns_names
            
        except x509.ExtensionNotFound:
            return []
    
    def check_certificate_expiry(self, cert_path: str, warning_days: int = 30) -> Dict[str, Any]:
        """Check certificate expiry and generate warnings"""
        
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
        
        validation = self.validate_certificate(cert_data)
        
        if not validation['valid']:
            return validation
        
        days_until_expiry = validation['days_until_expiry']
        
        if days_until_expiry <= 0:
            status = 'expired'
            action_required = 'Replace certificate immediately'
        elif days_until_expiry <= warning_days:
            status = 'warning'
            action_required = f'Certificate expires in {days_until_expiry} days'
        else:
            status = 'valid'
            action_required = 'No action required'
        
        return {
            'status': status,
            'days_until_expiry': days_until_expiry,
            'action_required': action_required,
            'certificate_info': validation
        }
```

#### 2.2 TLS Configuration Hardening

```nginx
# Nginx TLS hardening configuration
# /etc/nginx/conf.d/ssl-hardening.conf

# Modern SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;

# SSL session configuration
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# OCSP stapling configuration
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# SSL rating optimization
ssl_ecdh_curve secp384r1;
ssl_dhparam /etc/nginx/ssl/dhparam.pem;

# Disable server tokens
server_tokens off;

# HSTS configuration
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Additional security headers
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https:; connect-src 'self' https:; media-src 'none'; object-src 'none'; child-src 'none'; frame-ancestors 'none';" always;

# Certificate transparency
add_header Expect-CT "max-age=86400, enforce" always;

# Feature policy (deprecated but still useful)
add_header Feature-Policy "geolocation 'none'; microphone 'none'; camera 'none';" always;
```

### 3. Intrusion Detection and Prevention

#### 3.1 Web Application Firewall (WAF)

```nginx
# ModSecurity configuration
# /etc/nginx/modsec/main.conf

# Core ModSecurity rules
Include /etc/nginx/modsec/modsecurity.conf
Include /etc/nginx/modsec/unicode.mapping

# OWASP Core Rule Set
Include /etc/nginx/modsec/coreruleset/*.conf

# Custom rules for Threat Intelligence System
SecRuleEngine On
SecRequestBodyAccess On
SecRule REQUEST_HEADERS:Content-Type "^(?:application(?:/soap\+|/)text/)xml(?:/|$)|(?:application/)xml(?:/|$)" \
     "id:'200000',phase:1,t:none,t:lowercase,pass,nolog"

SecRule REQUEST_HEADERS:Content-Type "^(?:application(?:/soap\+|/)json|text/)xml(?:/|$)|(?:application/)json(?:/|$)" \
     "id:'200001',phase:1,t:none,t:lowercase,pass,nolog"

SecRule REQUEST_HEADERS:Content-Type "^(?:text/)xml(?:/|$)|(?:application)/(?:soap\+|)xml" \
     "id:'200002',phase:1,t:none,t:lowercase,pass,nolog"

# Threat Intelligence specific rules
SecRule REQUEST_URI "@contains /threat-intelligence" \
     "id:1001,\
     phase:1,\
     t:none,\
     pass,\
     msg:'Threat Intelligence API Access',\
     logdata:'%{REMOTE_ADDR} - %{REQUEST_URI}'"

# Rate limiting for API endpoints
SecAction \
  "id:1002,\
   phase:1,\
   t:none,\
   pass,\
   nolog,\
   chain"
  SecRule REQUEST_URI "@contains /api/" \
    SecRule &REQUEST_HEADERS:@rottle "^\s*\@rottle\s*\([\s]*['\"]?([0-9]+)['\"]?\s*,\s*['\"]?([0-9]+)['\"]?\s*,\s*['\"]?([0-9]+)['\"]?\s*,\s*['\"]?([0-9]+)['\"]?\s*\)" \
      "t:none,\
       t:lowercase,\
       pass,\
       msg:'Rate Limiting Triggered'"

# SQL injection protection
SecRule REQUEST_URI "@contains /threat-intelligence/lookup" \
     "id:1003,\
      phase:1,\
      t:none,\
      block,\
      msg:'SQL Injection Attack Detected in Threat Intelligence Query',\
      logdata:'%{REQUEST_URI}'"

# NoSQL injection protection
SecRule REQUEST_BODY "@rx '(?i)(?:union\s+select|select\s+.+\s+from|\bor\b\s+1=1\b|\bdrop\s+table\b|\binsert\s+into\b|\bupdate\b\s+.+\s+set\b)'" \
     "id:1004,\
      phase:2,\
      t:none,\
      block,\
      msg:'NoSQL Injection Attack Detected',\
      logdata:'%{REQUEST_BODY}'"

# XSS protection
SecRule REQUEST_HEADERS "@rx '(?i)(?:\b(?:on\w+)\s*=|<\s*script\b|javascript:|vbscript:|onload\s*=|onerror\s*=)'" \
     "id:1005,\
      phase:1,\
      t:none,\
      block,\
      msg:'Cross-Site Scripting (XSS) Attack Detected',\
      logdata:'%{REQUEST_HEADERS}'"

# Command injection protection
SecRule REQUEST_URI "@rx '(?i)(?:\b(?:cat|ls|whoami|pwd|id|uname|wget|curl|nc|netcat|telnet|ssh|ftp)\b|[\;\`\'\"\:\|\*]+|[&]{2,})'" \
     "id:1006,\
      phase:1,\
      t:none,\
      block,\
      msg:'Command Injection Attack Detected',\
      logdata:'%{REQUEST_URI}'"

# Path traversal protection
SecRule REQUEST_URI "@contains ../" \
     "id:1007,\
      phase:1,\
      t:none,\
      block,\
      msg:'Path Traversal Attack Detected',\
      logdata:'%{REQUEST_URI}'"

# API abuse protection
SecRule REQUEST_URI "@contains /api/" \
     "id:1008,\
      phase:1,\
      t:none,\
      pass,\
      nolog,\
      chain"
  SecRule &REQUEST_HEADERS:@rx "^\s*\@rottle\s*\([\s]*['\"]?([0-9]+)['\"]?\s*,\s*['\"]?([0-9]+)['\"]?\s*\)" \
    SecRule REQBODY_PROCESSING "@rx '([0-9]+)'" \
      "t:none,\
       t:lowercase,\
       block,\
       msg:'API Rate Limit Exceeded',\
       logdata:'%{REMOTE_ADDR}'"

# IP reputation checking
SecRule REMOTE_ADDR "@ipMatch 192.0.2.0/24,198.51.100.0/24,203.0.113.0/24" \
     "id:1009,\
      phase:1,\
      t:none,\
      block,\
      msg:'Blocked IP Address',\
      logdata:'%{REMOTE_ADDR}'"

# Bot detection
SecRule REQUEST_HEADERS:User-Agent "@rx '(?i)(?:\bbot\b|crawler|spider|crawl|curl|wget|python|perl|ruby|java|go|jsoup|okhttp)'" \
     "id:1010,\
      phase:1,\
      t:none,\
      pass,\
      nolog,\
      chain"
  SecRule REQUEST_URI "@contains /api/" \
    SecRule &REQUEST_HEADERS:@rx "^\s*\@rottle\s*\([\s]*['\"]?([0-9]+)['\"]?\s*,\s*['\"]?([0-9]+)['\"]?\s*\)" \
      "t:none,\
       t:lowercase,\
       block,\
       msg:'Potential Bot Access to API',\
       logdata:'%{REQUEST_HEADERS}'"
```

#### 3.2 Fail2ban Configuration

**File**: `/etc/fail2ban/jail.local`
```ini
[DEFAULT]
# Ban IP addresses that fail authentication repeatedly
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 192.168.100.0/24

# Email notifications
destemail = security@yourdomain.com
sender = fail2ban@yourdomain.com
mta = sendmail
action = %(action_mwl)s

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

[nginx-noproxy]
enabled = true
filter = nginx-noproxy
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 7200

[threat-intel-api]
enabled = true
filter = threat-intel-api
logpath = /var/log/threat-intel/api/app.log
maxretry = 5
bantime = 1800
findtime = 300

[threat-intel-auth]
enabled = true
filter = threat-intel-auth
logpath = /var/log/threat-intel/api/auth.log
maxretry = 3
bantime = 7200
findtime = 600

[threat-intel-rate-limit]
enabled = true
filter = threat-intel-rate-limit
logpath = /var/log/threat-intel/api/access.log
maxretry = 10
bantime = 3600
findtime = 300

[postgresql]
enabled = true
filter = postgresql
logpath = /var/log/postgresql/postgresql-*.log
maxretry = 3
bantime = 7200
```

**File**: `/etc/fail2ban/filter.d/threat-intel-api.conf`
```ini
[Definition]
failregex = ^.*\[ERROR\].*Authentication failed for user.*from <HOST>.*$
            ^.*\[ERROR\].*Invalid API key from <HOST>.*$
            ^.*\[ERROR\].*Rate limit exceeded from <HOST>.*$
            ^.*\[ERROR\].*Suspicious activity detected from <HOST>.*$

ignoreregex =
```

## Application Security

### 1. Input Validation and Sanitization

#### 1.1 Input Validation Framework

```python
import re
import html
import bleach
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator, ValidationError
from datetime import datetime
import ipaddress
import urllib.parse

class InputValidator:
    """Comprehensive input validation framework"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    IPV4_PATTERN = re.compile(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
    IPV6_PATTERN = re.compile(r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$')
    DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    HASH_PATTERN = re.compile(r'^[a-fA-F0-9]{32,64}$')
    
    # SQL injection patterns (dangerous patterns)
    SQL_INJECTION_PATTERNS = [
        re.compile(r'(?i)(\bunion\b\s+\bselect\b|\bselect\b\s+.+\s+\bfrom\b|\bor\b\s+1=1\b)',
                   re.IGNORECASE),
        re.compile(r'(?i)(\bdrop\s+table\b|\binsert\s+into\b|\bupdate\b\s+.+\s+\bset\b|\bdelete\b\s+from\b)',
                   re.IGNORECASE),
        re.compile(r'(?i)(\bexec\b\s*\(|\bexecute\b\s*\()', re.IGNORECASE),
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        re.compile(r'(?i)(<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>)', re.IGNORECASE),
        re.compile(r'(?i)(javascript:|vbscript:|onload\s*=|onerror\s*=)', re.IGNORECASE),
        re.compile(r'(?i)(<iframe\b|<object\b|<embed\b|<link\b|<style\b|<img\b)', re.IGNORECASE),
    ]
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML to prevent XSS attacks"""
        
        # Allow only safe HTML tags
        allowed_tags = ['b', 'i', 'em', 'strong', 'a', 'p', 'br']
        allowed_attributes = {
            'a': ['href', 'title'],
            '*': []
        }
        
        return bleach.clean(
            text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        
        # Remove dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        
        # Remove path traversal attempts
        sanitized = re.sub(r'\.\./', '', sanitized)
        
        # Limit length
        sanitized = sanitized[:255]
        
        return sanitized
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        
        if not email or len(email) > 254:
            return False
        
        return InputValidator.EMAIL_PATTERN.match(email) is not None
    
    @staticmethod
    def validate_ip_address(ip: str, ip_version: int = None) -> bool:
        """Validate IP address"""
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            if ip_version == 4 and ip_obj.version != 4:
                return False
            elif ip_version == 6 and ip_obj.version != 6:
                return False
            
            # Exclude private and reserved addresses for external data
            if ip_obj.is_private or ip_obj.is_reserved:
                return False
            
            return True
            
        except ValueError:
            return False
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Validate domain name"""
        
        if not domain or len(domain) > 253:
            return False
        
        domain = domain.lower()
        
        # Check basic pattern
        if not InputValidator.DOMAIN_PATTERN.match(domain):
            return False
        
        # Check for valid TLD
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        tld = parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False
        
        # Check for valid labels
        for part in parts:
            if not part or len(part) > 63:
                return False
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL"""
        
        if not url or len(url) > 2048:
            return False
        
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check netloc
            if not parsed.netloc:
                return False
            
            # Validate hostname
            if not InputValidator.validate_domain(parsed.hostname):
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def check_sql_injection(text: str) -> bool:
        """Check for SQL injection patterns"""
        
        return any(pattern.search(text) for pattern in InputValidator.SQL_INJECTION_PATTERNS)
    
    @staticmethod
    def check_xss(text: str) -> bool:
        """Check for XSS patterns"""
        
        return any(pattern.search(text) for pattern in InputValidator.XSS_PATTERNS)
    
    @staticmethod
    def validate_threat_indicator(indicator: str, indicator_type: str) -> tuple[bool, Optional[str]]:
        """
        Validate threat intelligence indicator
        
        Returns:
            (is_valid, error_message)
        """
        
        if not indicator or len(indicator) > 1000:
            return False, "Invalid indicator length"
        
        # Check for malicious patterns
        if InputValidator.check_sql_injection(indicator):
            return False, "SQL injection pattern detected"
        
        if InputValidator.check_xss(indicator):
            return False, "XSS pattern detected"
        
        # Type-specific validation
        if indicator_type == 'ip_address':
            if not InputValidator.validate_ip_address(indicator):
                return False, "Invalid IP address format"
        
        elif indicator_type == 'domain':
            if not InputValidator.validate_domain(indicator):
                return False, "Invalid domain format"
        
        elif indicator_type == 'url':
            if not InputValidator.validate_url(indicator):
                return False, "Invalid URL format"
        
        elif indicator_type == 'email':
            if not InputValidator.validate_email(indicator):
                return False, "Invalid email format"
        
        elif indicator_type == 'hash':
            if not InputValidator.HASH_PATTERN.match(indicator):
                return False, "Invalid hash format"
        
        else:
            return False, f"Unknown indicator type: {indicator_type}"
        
        return True, None

# Pydantic models for input validation
class ThreatIntelligenceQuery(BaseModel):
    """Model for threat intelligence queries"""
    
    indicator: str
    indicator_type: str
    
    @validator('indicator_type')
    def validate_indicator_type(cls, v):
        valid_types = ['ip_address', 'domain', 'email', 'url', 'hash']
        if v not in valid_types:
            raise ValueError(f'Invalid indicator type. Must be one of: {valid_types}')
        return v
    
    @validator('indicator')
    def validate_indicator(cls, v, values):
        if 'indicator_type' in values:
            is_valid, error = InputValidator.validate_threat_indicator(
                v, values['indicator_type']
            )
            if not is_valid:
                raise ValueError(f'Invalid indicator: {error}')
        return v

class UserRegistration(BaseModel):
    """Model for user registration"""
    
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check password strength
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v is not None:
            # Sanitize name fields
            v = re.sub(r'[^a-zA-Z\s\'-]', '', v).strip()
            if len(v) > 50:
                raise ValueError('Name must be less than 50 characters')
        return v

class APIKeyRequest(BaseModel):
    """Model for API key requests"""
    
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v) < 3 or len(v) > 100:
            raise ValueError('Name must be between 3 and 100 characters')
        
        # Check for XSS in name
        if InputValidator.check_xss(v):
            raise ValueError('Name contains potentially dangerous content')
        
        return v
    
    @validator('permissions')
    def validate_permissions(cls, v):
        valid_permissions = [
            'read_threat_intelligence',
            'write_threat_intelligence',
            'run_analysis',
            'view_analytics'
        ]
        
        for permission in v:
            if permission not in valid_permissions:
                raise ValueError(f'Invalid permission: {permission}')
        
        return v
```

### 2. Output Encoding and Escaping

```python
import html
import json
import urllib.parse
from typing import Any, Dict, List

class OutputEncoder:
    """Output encoding and escaping utilities"""
    
    @staticmethod
    def encode_html(text: str) -> str:
        """HTML encode text to prevent XSS"""
        
        if text is None:
            return ""
        
        return html.escape(text, quote=True)
    
    @staticmethod
    def encode_url(text: str) -> str:
        """URL encode text for safe embedding in URLs"""
        
        return urllib.parse.quote(text, safe='')
    
    @staticmethod
    def encode_json(data: Any, ensure_ascii: bool = True) -> str:
        """Safely encode data as JSON"""
        
        return json.dumps(
            data,
            ensure_ascii=ensure_ascii,
            separators=(',', ':'),
            default=str
        )
    
    @staticmethod
    def encode_csv(data: List[List[Any]]) -> str:
        """Safely encode data as CSV"""
        
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        for row in data:
            # Ensure all values are strings and escape quotes
            safe_row = []
            for value in row:
                if value is None:
                    safe_row.append('')
                else:
                    safe_row.append(str(value).replace('"', '""'))
            writer.writerow(safe_row)
        
        return output.getvalue()
    
    @staticmethod
    def escape_for_sql(text: str) -> str:
        """Escape text for safe SQL embedding (parameterization is preferred)"""
        
        if text is None:
            return ""
        
        # Replace single quotes with double quotes (SQL escaping)
        escaped = text.replace("'", "''")
        
        return escaped

class SafeResponse:
    """Safe response generation utilities"""
    
    @staticmethod
    def create_success_response(
        data: Any = None, 
        message: str = "Success",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a safe success response"""
        
        response = {
            "status": "success",
            "message": OutputEncoder.encode_html(message),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def create_error_response(
        error: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        include_traceback: bool = False
    ) -> Dict[str, Any]:
        """Create a safe error response"""
        
        response = {
            "status": "error",
            "error": OutputEncoder.encode_html(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details:
            # Sanitize details for safe output
            response["details"] = SafeResponse._sanitize_details(details)
        
        if include_traceback and os.getenv('ENVIRONMENT') == 'development':
            import traceback
            response["traceback"] = traceback.format_exc()
        
        return response
    
    @staticmethod
    def _sanitize_details(details: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize details to remove sensitive information"""
        
        sensitive_keys = [
            'password', 'token', 'key', 'secret', 'api_key',
            'authorization', 'credential', 'private', 'confidential'
        ]
        
        sanitized = {}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = SafeResponse._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    SafeResponse._sanitize_details(item) if isinstance(item, dict) 
                    else "***REDACTED***" if any(sensitive in str(item).lower() for sensitive in sensitive_keys)
                    else item
                    for item in value
                ]
            else:
                # Check if value contains sensitive information
                value_str = str(value).lower()
                if any(sensitive in value_str for sensitive in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
        
        return sanitized
```

---

For operational security procedures, see the [Operational Runbook](../operations/operational-runbook.md).

For compliance documentation, see the [Compliance Documentation](../compliance/compliance-documentation.md).

For monitoring and incident response, see the [Security Monitoring Guide](#monitoring-and-incident-response).
