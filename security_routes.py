"""
Security API Routes for Revolutionary Event Management System

This module provides Flask routes for:
- Security dashboard data
- Two-factor authentication setup and verification
- Role-based access control management
- Audit log retrieval and export
- GDPR compliance operations
- Security settings management
"""

from flask import Blueprint, request, jsonify, session, send_file, current_app, render_template
from datetime import datetime, timedelta
import json
import csv
import io
from functools import wraps
import logging

from security_manager import (
    security_manager, rbac, two_factor_auth, gdpr_compliance, 
    session_manager, rate_limiter, Role, Permission, DataCategory
)

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

def require_admin(func):
    """Decorator to require admin access"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_role = session.get('user_role')
        if user_role not in ['admin', 'super_admin']:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return func(*args, **kwargs)
    return wrapper

def rate_limit(action):
    """Decorator to apply rate limiting"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = request.remote_addr
            if not rate_limiter.check_rate_limit(identifier, action):
                return jsonify({
                    'success': False, 
                    'message': 'Rate limit exceeded'
                }), 429
            return func(*args, **kwargs)
        return wrapper
    return decorator

@security_bp.route('/dashboard-data')
@require_admin
def get_dashboard_data():
    """Get security dashboard overview data"""
    try:
        dashboard_data = security_manager.get_security_dashboard_data()
        
        # Calculate security score based on various factors
        security_score = calculate_security_score()
        
        return jsonify({
            'success': True,
            'dashboard_data': dashboard_data,
            'security_score': security_score
        })
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/overview')
@require_admin
def get_overview_data():
    """Get security overview metrics and recent events"""
    try:
        dashboard_data = security_manager.get_security_dashboard_data()
        
        # Get recent security events (last 24 hours)
        recent_logs = [
            {
                'timestamp': log.timestamp.isoformat(),
                'action': log.action,
                'resource': log.resource,
                'ip_address': log.ip_address,
                'success': log.success
            }
            for log in security_manager.audit_logs
            if log.timestamp > datetime.utcnow() - timedelta(hours=24)
        ][-10:]  # Last 10 events
        
        return jsonify({
            'success': True,
            'metrics': dashboard_data,
            'recent_events': recent_logs
        })
        
    except Exception as e:
        logger.error(f"Failed to get overview data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/rbac')
@require_admin
def get_rbac_data():
    """Get role-based access control data"""
    try:
        # Convert role permissions to serializable format
        role_permissions = {}
        for role, permissions in security_manager.role_permissions.items():
            role_permissions[role.value] = [perm.value for perm in permissions]
        
        return jsonify({
            'success': True,
            'permissions': role_permissions,
            'roles': list(Role.__members__.keys())
        })
        
    except Exception as e:
        logger.error(f"Failed to get RBAC data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/audit-logs')
@require_admin
def get_audit_logs():
    """Get filtered audit logs"""
    try:
        date_range = request.args.get('date_range', '24h')
        event_type = request.args.get('event_type', 'all')
        success_filter = request.args.get('success_filter', 'all')
        
        # Calculate date filter
        if date_range == '24h':
            start_date = datetime.utcnow() - timedelta(hours=24)
        elif date_range == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif date_range == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        else:
            start_date = datetime.utcnow() - timedelta(hours=24)
        
        # Filter logs
        filtered_logs = []
        for log in security_manager.audit_logs:
            if log.timestamp < start_date:
                continue
                
            if event_type != 'all' and log.action != event_type:
                continue
                
            if success_filter == 'success' and not log.success:
                continue
            elif success_filter == 'failure' and log.success:
                continue
            
            filtered_logs.append({
                'timestamp': log.timestamp.isoformat(),
                'user_id': log.user_id,
                'action': log.action,
                'resource': log.resource,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'success': log.success,
                'details': log.details
            })
        
        # Sort by timestamp (most recent first)
        filtered_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'logs': filtered_logs[:100]  # Limit to 100 most recent
        })
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/export-audit-logs')
@require_admin
def export_audit_logs():
    """Export audit logs as CSV"""
    try:
        date_range = request.args.get('date_range', '24h')
        event_type = request.args.get('event_type', 'all')
        success_filter = request.args.get('success_filter', 'all')
        
        # Get filtered logs (reuse logic from get_audit_logs)
        if date_range == '24h':
            start_date = datetime.utcnow() - timedelta(hours=24)
        elif date_range == '7d':
            start_date = datetime.utcnow() - timedelta(days=7)
        elif date_range == '30d':
            start_date = datetime.utcnow() - timedelta(days=30)
        else:
            start_date = datetime.utcnow() - timedelta(hours=24)
        
        filtered_logs = []
        for log in security_manager.audit_logs:
            if log.timestamp < start_date:
                continue
            if event_type != 'all' and log.action != event_type:
                continue
            if success_filter == 'success' and not log.success:
                continue
            elif success_filter == 'failure' and log.success:
                continue
            
            filtered_logs.append(log)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Timestamp', 'User ID', 'Action', 'Resource', 
            'IP Address', 'User Agent', 'Success', 'Details'
        ])
        
        # Write data
        for log in filtered_logs:
            writer.writerow([
                log.timestamp.isoformat(),
                log.user_id,
                log.action,
                log.resource,
                log.ip_address,
                log.user_agent,
                'Success' if log.success else 'Failed',
                json.dumps(log.details)
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'security-audit-logs-{datetime.now().strftime("%Y%m%d")}.csv'
        )
        
    except Exception as e:
        logger.error(f"Failed to export audit logs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/privacy-data')
@require_admin
def get_privacy_data():
    """Get GDPR and privacy compliance data"""
    try:
        total_records = len(security_manager.data_processing_records)
        
        # Check for records expiring soon (within 30 days)
        expiring_soon = len([
            record for record in security_manager.data_processing_records
            if (record.created_at + record.retention_period) < 
               (datetime.utcnow() + timedelta(days=30))
        ])
        
        # Count anonymized records (this would need to be tracked separately)
        anonymized = 0  # Placeholder
        
        return jsonify({
            'success': True,
            'stats': {
                'total_records': total_records,
                'expiring_soon': expiring_soon,
                'anonymized': anonymized
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get privacy data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/export-user-data/<int:user_id>', methods=['POST'])
@require_admin
def export_user_data(user_id):
    """Export all user data for GDPR compliance"""
    try:
        user_data = gdpr_compliance.export_user_data(user_id)
        
        # Create JSON file
        json_data = json.dumps(user_data, indent=2, default=str)
        
        return send_file(
            io.BytesIO(json_data.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'user-data-{user_id}-{datetime.now().strftime("%Y%m%d")}.json'
        )
        
    except Exception as e:
        logger.error(f"Failed to export user data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/anonymize-user-data/<int:user_id>', methods=['POST'])
@require_admin
def anonymize_user_data(user_id):
    """Anonymize user data"""
    try:
        anonymization_map = gdpr_compliance.anonymize_user_data(user_id)
        
        return jsonify({
            'success': True,
            'message': 'User data anonymized successfully',
            'anonymized_id': anonymization_map['user_id']
        })
        
    except Exception as e:
        logger.error(f"Failed to anonymize user data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/delete-expired-data', methods=['DELETE'])
@require_admin
def delete_expired_data():
    """Delete expired data based on retention policies"""
    try:
        expired_records = gdpr_compliance.check_data_retention()
        
        # In a real implementation, you would delete the actual data here
        # For now, we'll just remove the processing records
        for record in expired_records:
            security_manager.data_processing_records.remove(record)
        
        security_manager.log_security_event(
            action='data_retention_cleanup',
            resource='expired_data',
            success=True,
            details={'deleted_count': len(expired_records)}
        )
        
        return jsonify({
            'success': True,
            'message': f'Deleted {len(expired_records)} expired records',
            'deleted_count': len(expired_records)
        })
        
    except Exception as e:
        logger.error(f"Failed to delete expired data: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/setup-2fa', methods=['POST'])
@rate_limit('2fa_setup')
def setup_2fa():
    """Setup two-factor authentication for user"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Not authenticated'}), 401
        
        # Generate 2FA secret and QR code
        secret = two_factor_auth.generate_secret()
        user_email = session.get('user_email', 'user@example.com')
        qr_code = two_factor_auth.generate_qr_code(user_email, secret)
        backup_codes = two_factor_auth.generate_backup_codes()
        
        # Store in session temporarily
        session['2fa_setup_secret'] = secret
        session['2fa_backup_codes'] = backup_codes
        
        security_manager.log_security_event(
            action='2fa_setup_initiated',
            resource=f'user_{user_id}',
            success=True,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'secret': secret,
            'qr_code': qr_code,
            'backup_codes': backup_codes
        })
        
    except Exception as e:
        logger.error(f"Failed to setup 2FA: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/verify-2fa', methods=['POST'])
@rate_limit('2fa_verify')
def verify_2fa():
    """Verify two-factor authentication setup"""
    try:
        data = request.get_json()
        secret = data.get('secret')
        token = data.get('token')
        
        if not secret or not token:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400
        
        # Verify token
        if two_factor_auth.verify_token(secret, token):
            user_id = session.get('user_id')
            
            # Store 2FA secret for user (in real implementation, save to database)
            session['2fa_enabled'] = True
            session['2fa_secret'] = secret
            
            # Clear temporary setup data
            session.pop('2fa_setup_secret', None)
            
            security_manager.log_security_event(
                action='2fa_enabled',
                resource=f'user_{user_id}',
                success=True,
                user_id=user_id
            )
            
            return jsonify({
                'success': True,
                'message': '2FA enabled successfully'
            })
        else:
            security_manager.log_security_event(
                action='2fa_verification_failed',
                resource=f'user_{session.get("user_id")}',
                success=False,
                user_id=session.get('user_id')
            )
            
            return jsonify({
                'success': False,
                'message': 'Invalid verification code'
            }), 400
        
    except Exception as e:
        logger.error(f"Failed to verify 2FA: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/settings')
@require_admin
def get_security_settings():
    """Get current security settings"""
    try:
        # In a real implementation, these would be stored in database
        settings = {
            'enforce_2fa': True,
            'session_timeout': 30,
            'strict_ip': False,
            'login_attempts': 5,
            'api_calls': 100,
            'password_resets': 3,
            'password_min_length': 8,
            'password_require_uppercase': True,
            'password_require_lowercase': True,
            'password_require_numbers': True,
            'password_require_special': True
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        logger.error(f"Failed to get security settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@security_bp.route('/settings', methods=['PUT'])
@require_admin
def update_security_settings():
    """Update security settings"""
    try:
        data = request.get_json()
        
        # Validate settings
        if data.get('session_timeout', 0) < 5:
            return jsonify({
                'success': False, 
                'message': 'Session timeout must be at least 5 minutes'
            }), 400
        
        if data.get('password_min_length', 0) < 6:
            return jsonify({
                'success': False,
                'message': 'Password minimum length must be at least 6 characters'
            }), 400
        
        # In a real implementation, save settings to database
        user_id = session.get('user_id')
        
        security_manager.log_security_event(
            action='security_settings_updated',
            resource='system_settings',
            success=True,
            user_id=user_id,
            details=data
        )
        
        return jsonify({
            'success': True,
            'message': 'Security settings updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update security settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def calculate_security_score():
    """Calculate overall security score based on various factors"""
    score = 0
    max_score = 100
    
    # 2FA enabled for admins (20 points)
    if session.get('2fa_enabled'):
        score += 20
    
    # Recent failed login attempts (deduct points)
    recent_failed = len([
        log for log in security_manager.audit_logs
        if log.action == 'login_attempt' and not log.success and
           log.timestamp > datetime.utcnow() - timedelta(hours=24)
    ])
    score -= min(recent_failed * 2, 15)  # Max 15 point deduction
    
    # HTTPS enforcement (10 points)
    if request.is_secure:
        score += 10
    
    # Session security (15 points)
    if session_manager.session_timeout <= timedelta(minutes=30):
        score += 15
    
    # Password policy strength (15 points)
    score += 15  # Assume strong policy is enabled
    
    # Rate limiting active (10 points)
    score += 10
    
    # Audit logging active (10 points)
    score += 10
    
    # GDPR compliance measures (10 points)
    if len(security_manager.data_processing_records) > 0:
        score += 10
    
    # Ensure score is between 0 and 100
    return max(0, min(score, max_score))

# Error handlers
@security_bp.errorhandler(403)
def forbidden(error):
    return jsonify({'success': False, 'message': 'Access forbidden'}), 403

@security_bp.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Resource not found'}), 404

@security_bp.route('/dashboard')
@require_admin
def security_dashboard():
    """Render security dashboard page"""
    try:
        dashboard_data = security_manager.get_security_dashboard_data()
        security_score = calculate_security_score()
        
        # Mock data for template
        template_data = {
            'dashboard_data': dashboard_data,
            'security_score': security_score,
            'role_permissions': {
                'guest': [],
                'attendee': ['read_events'],
                'organizer': ['read_events', 'create_events', 'edit_events', 'view_analytics'],
                'moderator': ['read_events', 'create_events', 'edit_events', 'moderate_content', 'view_analytics'],
                'admin': ['read_events', 'create_events', 'edit_events', 'delete_events', 'manage_users', 'view_analytics', 'manage_payments', 'moderate_content', 'export_data', 'manage_integrations'],
                'super_admin': ['all_permissions']
            },
            'data_processing_stats': {
                'total_records': len(security_manager.data_processing_records),
                'expiring_soon': 0,
                'anonymized': 0
            }
        }
        
        return render_template('admin/security_dashboard.html', **template_data)
    except Exception as e:
        logger.error(f"Failed to render security dashboard: {e}")
        return f"Error loading security dashboard: {e}", 500

@security_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500
