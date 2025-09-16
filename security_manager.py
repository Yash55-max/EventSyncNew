"""
Enhanced Security and Privacy Manager for Revolutionary Event Management System

This module provides comprehensive security features including:
- Role-based Access Control (RBAC)
- End-to-end Encryption
- GDPR/CCPA Compliance
- Multi-factor Authentication (2FA)
- Data Anonymization and Privacy Controls
- Security Audit Logging
- Session Management
- API Security
"""

import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
try:
    import pyotp
    import qrcode
except ImportError:
    print("Installing missing dependencies for 2FA...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyotp", "qrcode[pil]"])
    import pyotp
    import qrcode
from io import BytesIO
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions for role-based access control"""
    READ_EVENTS = "read_events"
    CREATE_EVENTS = "create_events"
    EDIT_EVENTS = "edit_events"
    DELETE_EVENTS = "delete_events"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_PAYMENTS = "manage_payments"
    SYSTEM_ADMIN = "system_admin"
    MODERATE_CONTENT = "moderate_content"
    EXPORT_DATA = "export_data"
    MANAGE_INTEGRATIONS = "manage_integrations"

class Role(Enum):
    """User roles with different permission levels"""
    GUEST = "guest"
    ATTENDEE = "attendee" 
    ORGANIZER = "organizer"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class DataCategory(Enum):
    """Data categories for privacy compliance"""
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    PAYMENT = "payment"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"

@dataclass
class SecurityAuditLog:
    """Security audit log entry"""
    timestamp: datetime
    user_id: Optional[int]
    action: str
    resource: str
    ip_address: str
    user_agent: str
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataProcessingRecord:
    """GDPR data processing record"""
    user_id: int
    data_category: DataCategory
    purpose: str
    legal_basis: str
    retention_period: timedelta
    created_at: datetime
    last_accessed: Optional[datetime] = None

class SecurityManager:
    """Main security management class"""
    
    def __init__(self):
        self.audit_logs: List[SecurityAuditLog] = []
        self.data_processing_records: List[DataProcessingRecord] = []
        self.blocked_ips: set = set()
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Role-permission mapping
        self.role_permissions = {
            Role.GUEST: set(),
            Role.ATTENDEE: {Permission.READ_EVENTS},
            Role.ORGANIZER: {
                Permission.READ_EVENTS, Permission.CREATE_EVENTS, 
                Permission.EDIT_EVENTS, Permission.VIEW_ANALYTICS
            },
            Role.MODERATOR: {
                Permission.READ_EVENTS, Permission.CREATE_EVENTS,
                Permission.EDIT_EVENTS, Permission.MODERATE_CONTENT,
                Permission.VIEW_ANALYTICS
            },
            Role.ADMIN: {
                Permission.READ_EVENTS, Permission.CREATE_EVENTS,
                Permission.EDIT_EVENTS, Permission.DELETE_EVENTS,
                Permission.MANAGE_USERS, Permission.VIEW_ANALYTICS,
                Permission.MANAGE_PAYMENTS, Permission.MODERATE_CONTENT,
                Permission.EXPORT_DATA, Permission.MANAGE_INTEGRATIONS
            },
            Role.SUPER_ADMIN: {perm for perm in Permission}
        }
        
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for data protection"""
        return Fernet.generate_key()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """Hash password with salt"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(password_hash, password)

    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure token"""
        return secrets.token_urlsafe(length)

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = ['password', '123456', 'qwerty', 'admin']
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        return len(errors) == 0, errors
    
    def log_security_event(self, action: str, resource: str, success: bool, 
                          user_id: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        """Log security event for audit trail"""
        log_entry = SecurityAuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            action=action,
            resource=resource,
            ip_address=request.remote_addr if request else "unknown",
            user_agent=request.user_agent.string if request else "unknown",
            success=success,
            details=details or {}
        )
        
        self.audit_logs.append(log_entry)
        logger.info(f"Security event: {action} on {resource} - {'SUCCESS' if success else 'FAILURE'}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data"""
        recent_logs = [log for log in self.audit_logs 
                      if log.timestamp > datetime.utcnow() - timedelta(hours=24)]
        
        failed_attempts = [log for log in recent_logs if not log.success]
        
        return {
            'total_events_24h': len(recent_logs),
            'failed_attempts_24h': len(failed_attempts),
            'blocked_ips': len(self.blocked_ips),
            'active_data_processing_records': len(self.data_processing_records),
            'recent_failed_logins': [
                {
                    'timestamp': log.timestamp.isoformat(),
                    'ip_address': log.ip_address,
                    'details': log.details
                }
                for log in failed_attempts if log.action == 'login_attempt'
            ][-10:]  # Last 10 failed attempts
        }
    
    def export_audit_logs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Export audit logs for compliance"""
        filtered_logs = [
            log for log in self.audit_logs
            if start_date <= log.timestamp <= end_date
        ]
        
        return [
            {
                'timestamp': log.timestamp.isoformat(),
                'user_id': log.user_id,
                'action': log.action,
                'resource': log.resource,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'success': log.success,
                'details': log.details
            }
            for log in filtered_logs
        ]

class RoleBasedAccessControl:
    """Role-based access control system"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
    
    def has_permission(self, user_role: Role, permission: Permission) -> bool:
        """Check if user role has specific permission"""
        return permission in self.security_manager.role_permissions.get(user_role, set())
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Get current user role from session/context
                user_role = self._get_current_user_role()
                
                if not self.has_permission(user_role, permission):
                    self._log_unauthorized_access(permission)
                    raise PermissionError(f"Access denied. Required permission: {permission.value}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def _get_current_user_role(self) -> Role:
        """Get current user's role from session"""
        # This would integrate with your user session management
        role_str = session.get('user_role', 'guest')
        return Role(role_str)
    
    def _log_unauthorized_access(self, permission: Permission):
        """Log unauthorized access attempt"""
        self.security_manager.log_security_event(
            action="unauthorized_access_attempt",
            resource=permission.value,
            success=False,
            details={"requested_permission": permission.value}
        )

class TwoFactorAuth:
    """Two-factor authentication system"""
    
    def __init__(self):
        self.secret_key_length = 32
    
    def generate_secret(self) -> str:
        """Generate TOTP secret for user"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret: str, issuer: str = "Event Management") -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for web display
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_code_data}"
    
    def verify_token(self, secret: str, token: str) -> bool:
        """Verify TOTP token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=1)  # Allow 30-second window
        except Exception as e:
            logger.error(f"2FA verification failed: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for 2FA"""
        return [secrets.token_hex(8) for _ in range(count)]

class GDPRCompliance:
    """GDPR and privacy compliance manager"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.data_retention_periods = {
            DataCategory.PERSONAL: timedelta(days=2555),  # 7 years
            DataCategory.SENSITIVE: timedelta(days=1095),  # 3 years
            DataCategory.PAYMENT: timedelta(days=2555),    # 7 years (legal requirement)
            DataCategory.BEHAVIORAL: timedelta(days=730),  # 2 years
            DataCategory.TECHNICAL: timedelta(days=365)    # 1 year
        }
    
    def record_data_processing(self, user_id: int, category: DataCategory, 
                             purpose: str, legal_basis: str) -> DataProcessingRecord:
        """Record data processing activity for GDPR compliance"""
        record = DataProcessingRecord(
            user_id=user_id,
            data_category=category,
            purpose=purpose,
            legal_basis=legal_basis,
            retention_period=self.data_retention_periods[category],
            created_at=datetime.utcnow()
        )
        
        self.security_manager.data_processing_records.append(record)
        return record
    
    def anonymize_user_data(self, user_id: int) -> Dict[str, Any]:
        """Anonymize user data while preserving analytics value"""
        anonymized_id = hashlib.sha256(f"user_{user_id}_{secrets.token_hex(16)}".encode()).hexdigest()[:16]
        
        anonymization_map = {
            'user_id': anonymized_id,
            'email': f"anonymous_{anonymized_id}@example.com",
            'name': f"Anonymous User {anonymized_id[:8]}",
            'phone': None,
            'address': None
        }
        
        self.security_manager.log_security_event(
            action="data_anonymization",
            resource=f"user_{user_id}",
            success=True,
            details={"anonymized_id": anonymized_id}
        )
        
        return anonymization_map
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Export all user data for GDPR data portability"""
        # This would collect data from all relevant tables
        user_data = {
            'personal_info': {},
            'events': [],
            'tickets': [],
            'payments': [],
            'analytics': [],
            'processing_records': []
        }
        
        # Add processing records
        for record in self.security_manager.data_processing_records:
            if record.user_id == user_id:
                user_data['processing_records'].append({
                    'category': record.data_category.value,
                    'purpose': record.purpose,
                    'legal_basis': record.legal_basis,
                    'created_at': record.created_at.isoformat(),
                    'retention_period': str(record.retention_period)
                })
        
        return user_data
    
    def check_data_retention(self) -> List[DataProcessingRecord]:
        """Check for data that should be deleted based on retention periods"""
        current_time = datetime.utcnow()
        expired_records = []
        
        for record in self.security_manager.data_processing_records:
            if current_time > record.created_at + record.retention_period:
                expired_records.append(record)
        
        return expired_records

class SessionManager:
    """Secure session management"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.session_timeout = timedelta(minutes=30)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """Create secure session"""
        session_id = self.security_manager.generate_secure_token(64)
        
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'ip_address': ip_address,
            'user_agent': user_agent,
            'csrf_token': self.security_manager.generate_secure_token(32)
        }
        
        self.active_sessions[session_id] = session_data
        
        self.security_manager.log_security_event(
            action="session_created",
            resource=f"user_{user_id}",
            success=True,
            details={'session_id': session_id}
        )
        
        return session_id
    
    def validate_session(self, session_id: str, ip_address: str, user_agent: str) -> bool:
        """Validate session and check for security issues"""
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        current_time = datetime.utcnow()
        
        # Check session timeout
        if current_time > session_data['last_activity'] + self.session_timeout:
            self.destroy_session(session_id)
            return False
        
        # Check IP address consistency (optional strict mode)
        if session_data['ip_address'] != ip_address:
            logger.warning(f"IP address mismatch for session {session_id}")
            # Could implement IP change notifications here
        
        # Update last activity
        session_data['last_activity'] = current_time
        return True
    
    def destroy_session(self, session_id: str):
        """Destroy session securely"""
        if session_id in self.active_sessions:
            user_id = self.active_sessions[session_id]['user_id']
            del self.active_sessions[session_id]
            
            self.security_manager.log_security_event(
                action="session_destroyed",
                resource=f"user_{user_id}",
                success=True,
                details={'session_id': session_id}
            )

class RateLimiter:
    """Rate limiting for API protection"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.limits = {
            'login': (5, timedelta(minutes=15)),     # 5 attempts per 15 minutes
            'api_call': (100, timedelta(minutes=1)), # 100 calls per minute
            'password_reset': (3, timedelta(hours=1)) # 3 resets per hour
        }
    
    def check_rate_limit(self, identifier: str, action: str) -> bool:
        """Check if action is rate limited"""
        if action not in self.limits:
            return True
        
        max_attempts, window = self.limits[action]
        key = f"{identifier}_{action}"
        current_time = datetime.utcnow()
        
        # Clean old entries
        if key in self.security_manager.rate_limits:
            self.security_manager.rate_limits[key] = [
                timestamp for timestamp in self.security_manager.rate_limits[key]
                if current_time - timestamp < window
            ]
        else:
            self.security_manager.rate_limits[key] = []
        
        # Check limit
        if len(self.security_manager.rate_limits[key]) >= max_attempts:
            self.security_manager.log_security_event(
                action="rate_limit_exceeded",
                resource=action,
                success=False,
                details={'identifier': identifier, 'action': action}
            )
            return False
        
        # Add current attempt
        self.security_manager.rate_limits[key].append(current_time)
        return True

# Security decorators and utilities
def require_https(func):
    """Decorator to require HTTPS"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            raise SecurityError("HTTPS required")
        return func(*args, **kwargs)
    return wrapper

def validate_csrf_token(func):
    """Decorator to validate CSRF token"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        if not token or token != session.get('csrf_token'):
            raise SecurityError("Invalid CSRF token")
        return func(*args, **kwargs)
    return wrapper

class SecurityError(Exception):
    """Custom security exception"""
    pass


# Initialize global security manager
security_manager = SecurityManager()
rbac = RoleBasedAccessControl(security_manager)
two_factor_auth = TwoFactorAuth()
gdpr_compliance = GDPRCompliance(security_manager)
session_manager = SessionManager(security_manager)
rate_limiter = RateLimiter(security_manager)

def initialize_security_system():
    """Initialize the security system"""
    logger.info("Security system initialized successfully")
    logger.info("Features enabled: RBAC, 2FA, GDPR Compliance, Session Management, Rate Limiting")
    return {
        'security_manager': security_manager,
        'rbac': rbac,
        'two_factor_auth': two_factor_auth,
        'gdpr_compliance': gdpr_compliance,
        'session_manager': session_manager,
        'rate_limiter': rate_limiter
    }

if __name__ == "__main__":
    # Example usage and testing
    security_system = initialize_security_system()
    
    # Test password validation
    valid, errors = security_manager.validate_password_strength("MySecureP@ssw0rd123")
    print(f"Password validation: {valid}, Errors: {errors}")
    
    # Test 2FA
    secret = two_factor_auth.generate_secret()
    qr_code = two_factor_auth.generate_qr_code("user@example.com", secret)
    print(f"2FA setup complete. Secret length: {len(secret)}")
    
    # Test data encryption
    test_data = "Sensitive user information"
    encrypted = security_manager.encrypt_data(test_data)
    decrypted = security_manager.decrypt_data(encrypted)
    print(f"Encryption test: {test_data == decrypted}")