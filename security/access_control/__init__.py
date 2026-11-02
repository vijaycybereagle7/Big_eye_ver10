"""
Access Control Module
Implements Role-Based Access Control (RBAC) and audit logging
"""

import os
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading


class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    EXECUTE = "execute"
    ADMIN = "admin"
    AUDIT = "audit"
    BACKUP = "backup"
    RESTORE = "restore"


class ResourceType(Enum):
    """Resource types for access control"""
    USER = "user"
    ROLE = "role"
    DATA = "data"
    FILE = "file"
    API = "api"
    DATABASE = "database"
    SYSTEM = "system"
    REPORT = "report"
    CONFIG = "config"


@dataclass
class Role:
    """Role definition"""
    name: str
    description: str
    permissions: List[Permission]
    resource_access: Dict[ResourceType, Set[Permission]]
    created_at: str
    updated_at: str
    is_active: bool = True
    
    def has_permission(self, permission: Permission, resource: ResourceType) -> bool:
        """Check if role has specific permission"""
        if not self.is_active:
            return False
        
        # Check general permissions
        if permission in self.permissions:
            return True
        
        # Check resource-specific permissions
        resource_perms = self.resource_access.get(resource, set())
        return permission in resource_perms


@dataclass
class User:
    """User definition"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    is_active: bool
    created_at: str
    last_login: Optional[str]
    failed_login_attempts: int
    account_locked_until: Optional[str]
    password_hash: str
    salt: str
    
    def add_role(self, role_name: str):
        """Add role to user"""
        if role_name not in self.roles:
            self.roles.append(role_name)
    
    def remove_role(self, role_name: str):
        """Remove role from user"""
        if role_name in self.roles:
            self.roles.remove(role_name)
    
    def is_account_locked(self) -> bool:
        """Check if account is locked"""
        if not self.account_locked_until:
            return False
        return datetime.fromisoformat(self.account_locked_until) > datetime.now()


@dataclass
class AuditLog:
    """Audit log entry"""
    log_id: str
    user_id: str
    action: str
    resource: str
    resource_type: ResourceType
    timestamp: str
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AccessControlSystem:
    """Main RBAC access control system"""
    
    def __init__(self, db_path: str = '/workspace/security/access_control/access_control.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_database()
        self._create_default_roles()
    
    def _init_database(self):
        """Initialize SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    failed_login_attempts INTEGER DEFAULT 0,
                    account_locked_until TEXT
                )
            ''')
            
            # Roles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    permissions TEXT NOT NULL,
                    resource_access TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Audit logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN NOT NULL,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def _create_default_roles(self):
        """Create default system roles"""
        default_roles = [
            Role(
                name="admin",
                description="System administrator with full access",
                permissions=[Permission.ADMIN, Permission.AUDIT],
                resource_access={
                    ResourceType.USER: {Permission.READ, Permission.WRITE, Permission.DELETE},
                    ResourceType.ROLE: {Permission.READ, Permission.WRITE, Permission.DELETE},
                    ResourceType.DATA: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE},
                    ResourceType.FILE: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE},
                    ResourceType.SYSTEM: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.CREATE}
                },
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            Role(
                name="user",
                description="Regular user with basic access",
                permissions=[Permission.READ],
                resource_access={
                    ResourceType.DATA: {Permission.READ},
                    ResourceType.FILE: {Permission.READ}
                },
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            ),
            Role(
                name="auditor",
                description="User with audit and reporting access",
                permissions=[Permission.AUDIT, Permission.READ],
                resource_access={
                    ResourceType.REPORT: {Permission.READ, Permission.CREATE}
                },
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        ]
        
        for role in default_roles:
            if not self.get_role(role.name):
                self.create_role(role)
    
    def create_user(self, user: User) -> bool:
        """Create new user"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO users (
                            user_id, username, email, password_hash, salt, roles,
                            is_active, created_at, failed_login_attempts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user.user_id, user.username, user.email, user.password_hash,
                        user.salt, json.dumps(user.roles), user.is_active,
                        user.created_at, user.failed_login_attempts
                    ))
                    
                    conn.commit()
                    self._log_audit(user.user_id, "CREATE_USER", user.user_id, 
                                  ResourceType.USER, True, {})
                    return True
                    
            except sqlite3.IntegrityError:
                return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row[0], username=row[1], email=row[2],
                    password_hash=row[3], salt=row[4],
                    roles=json.loads(row[5]), is_active=bool(row[6]),
                    created_at=row[7], last_login=row[8],
                    failed_login_attempts=row[9], account_locked_until=row[10]
                )
        return None
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = "", user_agent: str = "") -> Optional[str]:
        """
        Authenticate user and return session ID
        
        Args:
            username: Username
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session ID if authentication successful, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            
            if not row:
                self._log_audit(username, "LOGIN_FAILED", username, 
                              ResourceType.USER, False, {'reason': 'user_not_found'})
                return None
            
            user = self.get_user(row[0])
            
            # Check if account is locked
            if user.is_account_locked():
                self._log_audit(user.user_id, "LOGIN_FAILED_LOCKED", username, 
                              ResourceType.USER, False, {'reason': 'account_locked'})
                return None
            
            # Verify password
            password_hash = hashlib.pbkdf2_hmac('sha256', 
                                              password.encode(), 
                                              user.salt.encode(), 
                                              100000)
            
            if password_hash != user.password_hash.encode():
                # Increment failed attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    lock_until = datetime.now() + timedelta(hours=1)
                    user.account_locked_until = lock_until.isoformat()
                
                # Update user
                cursor.execute('''
                    UPDATE users SET failed_login_attempts = ?, account_locked_until = ?
                    WHERE user_id = ?
                ''', (user.failed_login_attempts, user.account_locked_until, user.user_id))
                
                conn.commit()
                
                self._log_audit(user.user_id, "LOGIN_FAILED", username, 
                              ResourceType.USER, False, {'reason': 'invalid_password'})
                return None
            
            # Reset failed attempts on successful login
            cursor.execute('''
                UPDATE users SET failed_login_attempts = 0, account_locked_until = NULL,
                last_login = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user.user_id))
            
            # Create session
            session_id = self._create_session(user.user_id, ip_address, user_agent)
            
            self._log_audit(user.user_id, "LOGIN_SUCCESS", username, 
                          ResourceType.USER, True, {'session_id': session_id})
            
            return session_id
    
    def _create_session(self, user_id: str, ip_address: str, user_agent: str) -> str:
        """Create new user session"""
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=8)  # 8 hour session
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, created_at, expires_at,
                                    ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, datetime.now().isoformat(),
                  expires_at.isoformat(), ip_address, user_agent))
            conn.commit()
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[User]:
        """Validate session and return user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, u.* FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Check if session is expired
            expires_at = datetime.fromisoformat(row[4])
            if expires_at < datetime.now():
                return None
            
            return User(
                user_id=row[8], username=row[9], email=row[10],
                password_hash=row[11], salt=row[12],
                roles=json.loads(row[13]), is_active=bool(row[14]),
                created_at=row[15], last_login=row[16],
                failed_login_attempts=row[17], account_locked_until=row[18]
            )
    
    def check_permission(self, user_id: str, permission: Permission, 
                        resource: str, resource_type: ResourceType) -> bool:
        """
        Check if user has permission for resource
        
        Args:
            user_id: User ID
            permission: Permission to check
            resource: Resource identifier
            resource_type: Type of resource
            
        Returns:
            True if user has permission
        """
        user = self.get_user(user_id)
        if not user or not user.is_active:
            self._log_audit(user_id, "PERMISSION_DENIED", resource, 
                          resource_type, False, {'permission': permission.value})
            return False
        
        # Check each role
        for role_name in user.roles:
            role = self.get_role(role_name)
            if role and role.has_permission(permission, resource_type):
                self._log_audit(user_id, "PERMISSION_GRANTED", resource, 
                              resource_type, True, {'permission': permission.value})
                return True
        
        self._log_audit(user_id, "PERMISSION_DENIED", resource, 
                      resource_type, False, {'permission': permission.value})
        return False
    
    def create_role(self, role: Role) -> bool:
        """Create new role"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO roles (name, description, permissions, resource_access,
                                     created_at, updated_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    role.name, role.description, json.dumps([p.value for p in role.permissions]),
                    json.dumps({rt.value: [p.value for p in perms] for rt, perms in role.resource_access.items()}),
                    role.created_at, role.updated_at, role.is_active
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_role(self, name: str) -> Optional[Role]:
        """Get role by name"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM roles WHERE name = ?', (name,))
            row = cursor.fetchone()
            
            if row:
                return Role(
                    name=row[0], description=row[1],
                    permissions=[Permission(p) for p in json.loads(row[2])],
                    resource_access={ResourceType(rt): {Permission(p) for p in perms} 
                                   for rt, perms in json.loads(row[3]).items()},
                    created_at=row[4], updated_at=row[5], is_active=bool(row[6])
                )
        return None
    
    def assign_role_to_user(self, user_id: str, role_name: str) -> bool:
        """Assign role to user"""
        user = self.get_user(user_id)
        role = self.get_role(role_name)
        
        if not user or not role:
            return False
        
        if role_name not in user.roles:
            user.add_role(role_name)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE users SET roles = ? WHERE user_id = ?
                ''', (json.dumps(user.roles), user_id))
                conn.commit()
                
                self._log_audit(user_id, "ROLE_ASSIGNED", role_name, 
                              ResourceType.ROLE, True, {})
                return True
        
        return False
    
    def revoke_role_from_user(self, user_id: str, role_name: str) -> bool:
        """Revoke role from user"""
        user = self.get_user(user_id)
        
        if not user or role_name not in user.roles:
            return False
        
        user.remove_role(role_name)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET roles = ? WHERE user_id = ?
            ''', (json.dumps(user.roles), user_id))
            conn.commit()
            
            self._log_audit(user_id, "ROLE_REVOKED", role_name, 
                          ResourceType.ROLE, True, {})
            return True
    
    def _log_audit(self, user_id: str, action: str, resource: str, 
                  resource_type: ResourceType, success: bool, details: Dict[str, Any]):
        """Log audit event"""
        log_entry = AuditLog(
            log_id=secrets.token_urlsafe(16),
            user_id=user_id,
            action=action,
            resource=resource,
            resource_type=resource_type,
            timestamp=datetime.now().isoformat(),
            ip_address="",
            user_agent="",
            success=success,
            details=details
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO audit_logs (log_id, user_id, action, resource, resource_type,
                                      timestamp, ip_address, user_agent, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.log_id, log_entry.user_id, log_entry.action,
                log_entry.resource, log_entry.resource_type.value,
                log_entry.timestamp, log_entry.ip_address, log_entry.user_agent,
                log_entry.success, json.dumps(log_entry.details)
            ))
            conn.commit()
    
    def get_audit_logs(self, user_id: Optional[str] = None, 
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit logs with filtering"""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'log_id': row[0], 'user_id': row[1], 'action': row[2],
                    'resource': row[3], 'resource_type': row[4],
                    'timestamp': row[5], 'ip_address': row[6],
                    'user_agent': row[7], 'success': bool(row[8]),
                    'details': json.loads(row[9]) if row[9] else {}
                })
            
            return logs
    
    def logout(self, session_id: str) -> bool:
        """Logout user by session ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                return True
        
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM sessions WHERE expires_at < ?
            ''', (datetime.now().isoformat(),))
            deleted = cursor.rowcount
            conn.commit()
            return deleted


class PermissionChecker:
    """Helper class for checking permissions"""
    
    def __init__(self, access_control: AccessControlSystem):
        self.ac = access_control
    
    def require_permission(self, permission: Permission, resource_type: ResourceType):
        """Decorator for requiring permissions"""
        def decorator(func):
            def wrapper(self, *args, **kwargs):
                # Get user_id from context (would be set by authentication middleware)
                user_id = kwargs.get('user_id') or getattr(self, 'user_id', None)
                resource = kwargs.get('resource') or args[0] if args else 'unknown'
                
                if not self.ac.check_permission(user_id, permission, resource, resource_type):
                    raise PermissionError(f"Insufficient permissions: {permission.value}")
                
                return func(self, *args, **kwargs)
            return wrapper
        return decorator
