#!/usr/bin/env python3
"""
Email Notification System
Automated email notifications for events, tickets, reminders, and updates
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template_string, current_app
from flask_mail import Mail, Message
from threading import Thread
from models import Event, Ticket, User, TicketStatus
from database import db

# Email templates as strings (in production, these would be separate HTML files)
TICKET_CONFIRMATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket Confirmation - EventSync</title>
    <style>
        body { font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .content { padding: 30px; }
        .event-details { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .event-details h2 { margin-top: 0; color: #495057; }
        .detail-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #666; }
        .ticket-info { background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }
        .ticket-number { font-size: 24px; font-weight: bold; letter-spacing: 2px; }
        .cta-button { display: inline-block; background: #007bff; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; font-weight: bold; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-radius: 0 0 10px 10px; font-size: 14px; }
        .qr-section { text-align: center; margin: 20px 0; padding: 20px; border: 2px dashed #007bff; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <!-- EventSync Logo in Email -->
            <div style="display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 20px;">
                <div style="width: 50px; height: 50px; background: white; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                    <span style="color: #FF5722; font-size: 24px; font-weight: bold;">ES</span>
                </div>
                <div>
                    <h1 style="margin: 0; font-size: 28px;">🎉 Ticket Confirmed!</h1>
                    <p style="margin: 5px 0 0 0; opacity: 0.9;">Powered by EventSync</p>
                </div>
            </div>
            <p>Your registration for {{ event.title }} has been confirmed</p>
        </div>
        
        <div class="content">
            <p>Hello {{ user.full_name or user.username }},</p>
            
            <p>Great news! Your ticket has been confirmed for the upcoming event. Here are your details:</p>
            
            <div class="event-details">
                <h2>📅 Event Details</h2>
                <div class="detail-row">
                    <span class="detail-label">Event:</span>
                    <span>{{ event.title }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span>{{ event.start_date.strftime('%A, %B %d, %Y') }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span>{{ event.start_date.strftime('%I:%M %p') }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span>{{ event.location or 'Virtual Event' }}</span>
                </div>
                {% if event.description %}
                <div style="margin-top: 15px;">
                    <strong>Description:</strong><br>
                    {{ event.description[:200] }}{% if event.description|length > 200 %}...{% endif %}
                </div>
                {% endif %}
            </div>
            
            <div class="ticket-info">
                <h3>🎫 Your Ticket</h3>
                <div class="ticket-number">{{ ticket.ticket_number }}</div>
                <p>Keep this ticket number safe - you'll need it for check-in!</p>
            </div>
            
            <div class="qr-section">
                <h3>📱 Digital Check-in</h3>
                <p>Show this email or your ticket number at the event for quick check-in.</p>
            </div>
            
            <div style="text-align: center;">
                <a href="{{ base_url }}/tickets/my-tickets" class="cta-button">View My Tickets</a>
            </div>
            
            <p>We're excited to see you at the event! If you have any questions, please don't hesitate to contact us.</p>
            
            <p>Best regards,<br>The EventSync Team</p>
        </div>
        
        <div class="footer">
            <p>This email was sent to {{ user.email }} because you registered for an event on EventSync.</p>
            <p>© 2025 EventSync - Event Management System</p>
        </div>
    </div>
</body>
</html>
"""

EVENT_REMINDER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Reminder - EventSync</title>
    <style>
        body { font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .header h1 { margin: 0; font-size: 28px; }
        .content { padding: 30px; }
        .reminder-box { background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
        .countdown { font-size: 24px; font-weight: bold; color: #e17055; margin: 10px 0; }
        .event-details { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .detail-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 8px 0; border-bottom: 1px solid #eee; }
        .detail-label { font-weight: bold; color: #666; }
        .cta-button { display: inline-block; background: #e17055; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; font-weight: bold; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-radius: 0 0 10px 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⏰ Event Reminder</h1>
            <p>Don't forget about your upcoming event!</p>
        </div>
        
        <div class="content">
            <p>Hello {{ user.full_name or user.username }},</p>
            
            <div class="reminder-box">
                <h3>{{ event.title }}</h3>
                <div class="countdown">{{ time_until_event }}</div>
                <p>Your event is coming up soon!</p>
            </div>
            
            <div class="event-details">
                <h2>📅 Event Details</h2>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span>{{ event.start_date.strftime('%A, %B %d, %Y') }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span>{{ event.start_date.strftime('%I:%M %p') }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span>{{ event.location or 'Virtual Event' }}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Your Ticket:</span>
                    <span>{{ ticket.ticket_number }}</span>
                </div>
            </div>
            
            <div style="background: #e8f5e8; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>✅ What to bring:</h3>
                <ul>
                    <li>This email or your ticket number</li>
                    <li>Valid ID for verification</li>
                    <li>Arrive 15 minutes early for smooth check-in</li>
                </ul>
            </div>
            
            {% if event.virtual_link %}
            <div style="background: #cce5ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>💻 Virtual Event Access</h3>
                <p>Join the event online: <a href="{{ event.virtual_link }}">{{ event.virtual_link }}</a></p>
            </div>
            {% endif %}
            
            <div style="text-align: center;">
                <a href="{{ base_url }}/tickets/my-tickets" class="cta-button">View My Tickets</a>
            </div>
            
            <p>We look forward to seeing you at the event!</p>
            
            <p>Best regards,<br>The EventSync Team</p>
        </div>
        
        <div class="footer">
            <p>This reminder was sent to {{ user.email }}.</p>
            <p>© 2025 EventSync - Event Management System</p>
        </div>
    </div>
</body>
</html>
"""

EVENT_UPDATE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Event Update - EventSync</title>
    <style>
        body { font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { padding: 30px; }
        .update-box { background: #e3f2fd; border-left: 4px solid #2196f3; padding: 20px; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; border-radius: 0 0 10px 10px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📢 Event Update</h1>
            <p>Important information about your event</p>
        </div>
        
        <div class="content">
            <p>Hello {{ user.full_name or user.username }},</p>
            
            <p>We have an important update regarding your upcoming event:</p>
            
            <div class="update-box">
                <h3>{{ event.title }}</h3>
                <p><strong>Update:</strong> {{ update_message }}</p>
            </div>
            
            <p>If you have any questions about this update, please don't hesitate to contact us.</p>
            
            <p>Thank you for your understanding.</p>
            
            <p>Best regards,<br>The EventSync Team</p>
        </div>
        
        <div class="footer">
            <p>© 2025 EventSync - Event Management System</p>
        </div>
    </div>
</body>
</html>
"""

class EmailNotificationService:
    def __init__(self, app=None):
        self.app = app
        self.mail = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the email service with Flask app"""
        self.app = app
        
        # Configure Flask-Mail
        app.config.setdefault('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'smtp.gmail.com'))
        app.config.setdefault('MAIL_PORT', int(os.environ.get('MAIL_PORT', '587')))
        app.config.setdefault('MAIL_USE_TLS', os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes'])
        app.config.setdefault('MAIL_USE_SSL', os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', '1', 'yes'])
        app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME', ''))
        app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD', ''))
        app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@eventsync.com'))
        
        self.mail = Mail(app)
        
        # Set up logging
        logging.getLogger('email_notifications').setLevel(logging.INFO)
    
    def _send_async_email(self, app, msg):
        """Send email asynchronously"""
        try:
            with app.app_context():
                self.mail.send(msg)
                logging.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
    
    def send_email_async(self, subject, recipients, html_body, text_body=None):
        """Send email asynchronously in background thread"""
        if not self.mail:
            logging.error("Email service not initialized")
            return False
        
        try:
            msg = Message(
                subject=subject,
                recipients=recipients if isinstance(recipients, list) else [recipients],
                html=html_body,
                body=text_body or "Please view this email in an HTML-capable client."
            )
            
            # Send in background thread
            thread = Thread(target=self._send_async_email, args=(self.app, msg))
            thread.start()
            
            return True
        except Exception as e:
            logging.error(f"Error creating email message: {str(e)}")
            return False
    
    def send_ticket_confirmation(self, ticket, user, event, base_url="http://localhost:5000"):
        """Send ticket confirmation email"""
        subject = f"Ticket Confirmed: {event.title}"
        
        html_body = render_template_string(
            TICKET_CONFIRMATION_TEMPLATE,
            ticket=ticket,
            user=user,
            event=event,
            base_url=base_url
        )
        
        return self.send_email_async(subject, user.email, html_body)
    
    def send_event_reminder(self, ticket, user, event, days_before=1, base_url="http://localhost:5000"):
        """Send event reminder email"""
        time_until_event = self._format_time_until(event.start_date)
        
        if days_before == 1:
            subject = f"Tomorrow: {event.title}"
        elif days_before == 7:
            subject = f"Next Week: {event.title}"
        else:
            subject = f"Reminder: {event.title}"
        
        html_body = render_template_string(
            EVENT_REMINDER_TEMPLATE,
            ticket=ticket,
            user=user,
            event=event,
            time_until_event=time_until_event,
            base_url=base_url
        )
        
        return self.send_email_async(subject, user.email, html_body)
    
    def send_event_update(self, user, event, update_message):
        """Send event update notification"""
        subject = f"Update: {event.title}"
        
        html_body = render_template_string(
            EVENT_UPDATE_TEMPLATE,
            user=user,
            event=event,
            update_message=update_message
        )
        
        return self.send_email_async(subject, user.email, html_body)
    
    def send_event_cancellation(self, ticket, user, event, reason=""):
        """Send event cancellation notification"""
        subject = f"Event Cancelled: {event.title}"
        
        cancellation_template = """
        <p>Dear {{ user.full_name or user.username }},</p>
        
        <p>We regret to inform you that the following event has been cancelled:</p>
        
        <h3>{{ event.title }}</h3>
        <p><strong>Originally scheduled for:</strong> {{ event.start_date.strftime('%A, %B %d, %Y at %I:%M %p') }}</p>
        <p><strong>Your ticket number:</strong> {{ ticket.ticket_number }}</p>
        
        {% if reason %}
        <p><strong>Reason for cancellation:</strong> {{ reason }}</p>
        {% endif %}
        
        <p>If you paid for this event, a refund will be processed within 3-5 business days.</p>
        
        <p>We sincerely apologize for any inconvenience this may cause.</p>
        
        <p>Best regards,<br>The EventSync Team</p>
        """
        
        html_body = render_template_string(
            cancellation_template,
            ticket=ticket,
            user=user,
            event=event,
            reason=reason
        )
        
        return self.send_email_async(subject, user.email, html_body)
    
    def _format_time_until(self, event_date):
        """Format time remaining until event"""
        now = datetime.utcnow()
        delta = event_date - now
        
        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''} remaining"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} remaining"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} remaining"
    
    def send_bulk_reminder(self, event, days_before=1, base_url="http://localhost:5000"):
        """Send reminder emails to all attendees of an event"""
        try:
            tickets = Ticket.query.filter_by(event_id=event.id).filter(
                Ticket.status.in_([TicketStatus.PAID, TicketStatus.RESERVED])
            ).all()
            
            sent_count = 0
            
            for ticket in tickets:
                user = User.query.get(ticket.attendee_id)
                if user:
                    success = self.send_event_reminder(ticket, user, event, days_before, base_url)
                    if success:
                        sent_count += 1
            
            logging.info(f"Sent {sent_count} reminder emails for event: {event.title}")
            return sent_count
            
        except Exception as e:
            logging.error(f"Error sending bulk reminders: {str(e)}")
            return 0

# Global instance
email_service = EmailNotificationService()

# Helper functions for easy integration
def send_ticket_confirmation_email(ticket_id):
    """Helper function to send ticket confirmation"""
    try:
        ticket = Ticket.query.get(ticket_id)
        if not ticket:
            return False
        
        user = User.query.get(ticket.attendee_id)
        event = Event.query.get(ticket.event_id)
        
        if user and event:
            return email_service.send_ticket_confirmation(ticket, user, event)
    except Exception as e:
        logging.error(f"Error sending ticket confirmation: {str(e)}")
        return False

def send_event_reminder_emails(event_id, days_before=1):
    """Helper function to send event reminders"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return 0
        
        return email_service.send_bulk_reminder(event, days_before)
    except Exception as e:
        logging.error(f"Error sending event reminders: {str(e)}")
        return 0

def schedule_automated_reminders():
    """Schedule automated reminder emails (to be called by a scheduler)"""
    try:
        # Get events happening tomorrow
        tomorrow = datetime.utcnow() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events_tomorrow = Event.query.filter(
            Event.start_date >= tomorrow_start,
            Event.start_date <= tomorrow_end
        ).all()
        
        total_sent = 0
        for event in events_tomorrow:
            sent = email_service.send_bulk_reminder(event, days_before=1)
            total_sent += sent
        
        # Get events happening next week
        next_week = datetime.utcnow() + timedelta(days=7)
        week_start = next_week.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = next_week.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events_next_week = Event.query.filter(
            Event.start_date >= week_start,
            Event.start_date <= week_end
        ).all()
        
        for event in events_next_week:
            sent = email_service.send_bulk_reminder(event, days_before=7)
            total_sent += sent
        
        logging.info(f"Automated reminders: {total_sent} emails sent")
        return total_sent
        
    except Exception as e:
        logging.error(f"Error in automated reminders: {str(e)}")
        return 0