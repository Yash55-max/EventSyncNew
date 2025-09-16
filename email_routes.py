#!/usr/bin/env python3
"""
Email Management Routes
Admin interface for managing email notifications and settings
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Event, Ticket, User
from email_notifications import email_service, send_event_reminder_emails, schedule_automated_reminders
from datetime import datetime, timedelta

email_bp = Blueprint('email', __name__, url_prefix='/email')

@email_bp.route('/dashboard')
@login_required
def email_dashboard():
    """Email management dashboard for organizers"""
    if current_user.user_type.value != 'organizer':
        flash('Access denied. Only organizers can access email management.', 'error')
        return redirect(url_for('index'))
    
    # Get organizer's events
    user_events = Event.query.filter_by(organizer_id=current_user.id).all()
    
    return render_template('email/dashboard.html', 
                         user_events=user_events,
                         title='Email Management')

@email_bp.route('/send-reminders', methods=['POST'])
@login_required
def send_manual_reminders():
    """Send manual reminders for an event"""
    if current_user.user_type.value != 'organizer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        days_before = int(data.get('days_before', 1))
        
        if not event_id:
            return jsonify({'success': False, 'message': 'Event ID is required'})
        
        # Verify the organizer owns this event
        event = Event.query.get(event_id)
        if not event or event.organizer_id != current_user.id:
            return jsonify({'success': False, 'message': 'Event not found or access denied'})
        
        # Send reminders
        sent_count = send_event_reminder_emails(event_id, days_before)
        
        return jsonify({
            'success': True,
            'message': f'Successfully sent {sent_count} reminder emails',
            'sent_count': sent_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending reminders: {str(e)}'})

@email_bp.route('/send-update', methods=['POST'])
@login_required
def send_event_update():
    """Send update notification to event attendees"""
    if current_user.user_type.value != 'organizer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        update_message = data.get('update_message', '').strip()
        
        if not event_id or not update_message:
            return jsonify({'success': False, 'message': 'Event ID and update message are required'})
        
        # Verify the organizer owns this event
        event = Event.query.get(event_id)
        if not event or event.organizer_id != current_user.id:
            return jsonify({'success': False, 'message': 'Event not found or access denied'})
        
        # Get all attendees for this event
        tickets = Ticket.query.filter_by(event_id=event_id).all()
        sent_count = 0
        
        for ticket in tickets:
            user = User.query.get(ticket.attendee_id)
            if user:
                success = email_service.send_event_update(user, event, update_message)
                if success:
                    sent_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Successfully sent update to {sent_count} attendees',
            'sent_count': sent_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending update: {str(e)}'})

@email_bp.route('/test-email', methods=['POST'])
@login_required
def send_test_email():
    """Send test email to verify email configuration"""
    if current_user.user_type.value != 'organizer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Send test email to current user
        subject = "EVENTSYNC - Test Email"
        html_body = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <h2 style="color: #667eea;">✅ Test Email Successful!</h2>
                <p>Hello {{ user.full_name or user.username }},</p>
                <p>This is a test email to verify that your EVENTSYNC email configuration is working correctly.</p>
                <p><strong>Test details:</strong></p>
                <ul>
                    <li>Sent at: {{ timestamp }}</li>
                    <li>Recipient: {{ user.email }}</li>
                    <li>System: EVENTSYNC Email Service</li>
                </ul>
                <p>If you received this email, your email system is configured properly!</p>
                <p>Best regards,<br>The EVENTSYNC Team</p>
            </div>
        </body>
        </html>
        """.replace('{{ user.full_name or user.username }}', current_user.full_name or current_user.username)\
           .replace('{{ user.email }}', current_user.email)\
           .replace('{{ timestamp }}', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        success = email_service.send_email_async(subject, current_user.email, html_body)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Test email sent to {current_user.email}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email. Check email configuration.'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending test email: {str(e)}'})

@email_bp.route('/api/event-stats/<int:event_id>')
@login_required
def get_event_email_stats(event_id):
    """Get email statistics for an event"""
    if current_user.user_type.value != 'organizer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Verify the organizer owns this event
        event = Event.query.get(event_id)
        if not event or event.organizer_id != current_user.id:
            return jsonify({'success': False, 'message': 'Event not found or access denied'})
        
        # Get ticket statistics
        total_tickets = Ticket.query.filter_by(event_id=event_id).count()
        paid_tickets = Ticket.query.filter_by(event_id=event_id, status='PAID').count()
        reserved_tickets = Ticket.query.filter_by(event_id=event_id, status='RESERVED').count()
        
        # Calculate days until event
        days_until_event = (event.start_date - datetime.utcnow()).days
        
        return jsonify({
            'success': True,
            'data': {
                'event_title': event.title,
                'event_date': event.start_date.strftime('%Y-%m-%d %H:%M'),
                'total_tickets': total_tickets,
                'paid_tickets': paid_tickets,
                'reserved_tickets': reserved_tickets,
                'days_until_event': days_until_event,
                'can_send_reminders': days_until_event >= 0
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@email_bp.route('/api/email-status')
@login_required
def get_email_status():
    """Get email system status"""
    try:
        # Check if email service is configured
        is_configured = bool(email_service.mail and 
                           email_service.app and 
                           email_service.app.config.get('MAIL_USERNAME'))
        
        return jsonify({
            'success': True,
            'data': {
                'configured': is_configured,
                'mail_server': email_service.app.config.get('MAIL_SERVER', 'Not set') if email_service.app else 'Not set',
                'mail_port': email_service.app.config.get('MAIL_PORT', 'Not set') if email_service.app else 'Not set',
                'mail_username': email_service.app.config.get('MAIL_USERNAME', 'Not set') if email_service.app else 'Not set',
                'use_tls': email_service.app.config.get('MAIL_USE_TLS', False) if email_service.app else False
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@email_bp.route('/schedule-reminders', methods=['POST'])
@login_required
def trigger_scheduled_reminders():
    """Manually trigger automated reminders (admin only)"""
    if current_user.user_type.value != 'organizer':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        sent_count = schedule_automated_reminders()
        
        return jsonify({
            'success': True,
            'message': f'Automated reminders completed. {sent_count} emails sent.',
            'sent_count': sent_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error running automated reminders: {str(e)}'})

@email_bp.route('/preview-template/<template_type>')
@login_required
def preview_email_template(template_type):
    """Preview email templates"""
    if current_user.user_type.value != 'organizer':
        return redirect(url_for('index'))
    
    # Sample data for preview
    sample_event = {
        'id': 1,
        'title': 'Sample Tech Conference',
        'description': 'A sample technology conference for preview purposes.',
        'start_date': datetime.utcnow() + timedelta(days=7),
        'location': 'Convention Center, Sample City',
        'virtual_link': 'https://meet.example.com/sample'
    }
    
    sample_user = {
        'username': 'sample_user',
        'full_name': 'Sample User',
        'email': 'sample@example.com'
    }
    
    sample_ticket = {
        'ticket_number': 'SAMPLE123',
        'status': 'PAID'
    }
    
    try:
        if template_type == 'confirmation':
            from email_notifications import TICKET_CONFIRMATION_TEMPLATE
            from flask import render_template_string
            
            html_content = render_template_string(
                TICKET_CONFIRMATION_TEMPLATE,
                event=type('obj', (object,), sample_event),
                user=type('obj', (object,), sample_user),
                ticket=type('obj', (object,), sample_ticket),
                base_url="http://localhost:5000"
            )
            
        elif template_type == 'reminder':
            from email_notifications import EVENT_REMINDER_TEMPLATE
            from flask import render_template_string
            
            html_content = render_template_string(
                EVENT_REMINDER_TEMPLATE,
                event=type('obj', (object,), sample_event),
                user=type('obj', (object,), sample_user),
                ticket=type('obj', (object,), sample_ticket),
                time_until_event="7 days remaining",
                base_url="http://localhost:5000"
            )
            
        elif template_type == 'update':
            from email_notifications import EVENT_UPDATE_TEMPLATE
            from flask import render_template_string
            
            html_content = render_template_string(
                EVENT_UPDATE_TEMPLATE,
                event=type('obj', (object,), sample_event),
                user=type('obj', (object,), sample_user),
                update_message="This is a sample update message for preview purposes."
            )
        else:
            html_content = "<p>Template not found</p>"
        
        return html_content
        
    except Exception as e:
        return f"<p>Error previewing template: {str(e)}</p>"