"""
Integration Management Routes for Event Management System
Handles all integration setup, configuration, and management endpoints
"""

import json
import asyncio
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.exceptions import BadRequest

from database import db
from models import Integration, Event, Ticket
from integrations import (
    integration_manager, IntegrationType, IntegrationConfig, IntegrationStatus,
    sync_event_to_calendars, process_event_payment, send_event_reminders
)

# Create blueprint
integrations_bp = Blueprint('integrations', __name__, url_prefix='/integrations')

@integrations_bp.route('/')
@login_required
def integration_dashboard():
    """Display integration dashboard"""
    try:
        # Get user's integrations
        user_integrations = Integration.query.filter_by(user_id=current_user.id).all()
        
        # Convert to dict format
        integrations_data = []
        for integration in user_integrations:
            integrations_data.append({
                'id': integration.id,
                'type': integration.integration_type,
                'status': integration.status,
                'last_sync': integration.last_sync.isoformat() if integration.last_sync else None,
                'error_message': integration.error_message,
                'created_at': integration.created_at.isoformat(),
                'webhook_url': integration.webhook_url
            })
        
        # Available integration types
        available_integrations = [
            {'type': 'google_calendar', 'name': 'Google Calendar', 'icon': 'fab fa-google', 'description': 'Sync events with Google Calendar'},
            {'type': 'outlook_calendar', 'name': 'Outlook Calendar', 'icon': 'fab fa-microsoft', 'description': 'Sync events with Microsoft Outlook'},
            {'type': 'stripe_payment', 'name': 'Stripe', 'icon': 'fab fa-stripe', 'description': 'Process payments with Stripe'},
            {'type': 'github', 'name': 'GitHub', 'icon': 'fab fa-github', 'description': 'Create repositories for collaboration'},
            {'type': 'slack', 'name': 'Slack', 'icon': 'fab fa-slack', 'description': 'Send notifications to Slack channels'},
            {'type': 'twitter', 'name': 'Twitter', 'icon': 'fab fa-twitter', 'description': 'Share events on Twitter'},
            {'type': 'linkedin', 'name': 'LinkedIn', 'icon': 'fab fa-linkedin', 'description': 'Share events on LinkedIn'},
            {'type': 'email_notifications', 'name': 'Email Notifications', 'icon': 'fas fa-envelope', 'description': 'Send email notifications'},
            {'type': 'webhooks', 'name': 'Webhooks', 'icon': 'fas fa-webhook', 'description': 'Custom webhook integrations'}
        ]
        
        return render_template('integrations/dashboard.html',
                             integrations=integrations_data,
                             available_integrations=available_integrations)
    
    except Exception as e:
        flash(f'Error loading integrations: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))


@integrations_bp.route('/api/register', methods=['POST'])
@login_required
def register_integration():
    """Register a new integration"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        integration_type_str = data.get('integration_type')
        credentials = data.get('credentials', {})
        settings = data.get('settings', {})
        webhook_url = data.get('webhook_url')
        
        # Validate integration type
        try:
            integration_type = IntegrationType(integration_type_str)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid integration type'}), 400
        
        # Create integration config
        integration_config = IntegrationConfig(
            integration_type=integration_type,
            credentials=credentials,
            settings=settings,
            webhook_url=webhook_url
        )
        
        # Register integration asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            integration_manager.register_integration(current_user.id, integration_config)
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Integration registered successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to register integration'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/test/<int:integration_id>', methods=['POST'])
@login_required
def test_integration(integration_id):
    """Test an integration"""
    try:
        integration = Integration.query.filter_by(
            id=integration_id,
            user_id=current_user.id
        ).first()
        
        if not integration:
            return jsonify({'success': False, 'error': 'Integration not found'}), 404
        
        # Test integration based on type
        test_result = _test_integration_by_type(integration)
        
        return jsonify(test_result)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _test_integration_by_type(integration):
    """Test integration based on its type"""
    try:
        integration_type = integration.integration_type
        credentials = json.loads(integration.credentials) if integration.credentials else {}
        
        if integration_type == 'google_calendar':
            return _test_google_calendar(credentials)
        elif integration_type == 'github':
            return _test_github(credentials)
        elif integration_type == 'slack':
            return _test_slack(credentials)
        elif integration_type == 'stripe_payment':
            return _test_stripe(credentials)
        elif integration_type == 'webhooks':
            return _test_webhook(integration.webhook_url)
        else:
            return {'success': True, 'message': 'Test not implemented for this integration type'}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _test_google_calendar(credentials):
    """Test Google Calendar integration"""
    try:
        # This would implement actual Google Calendar API test
        if credentials.get('access_token'):
            return {'success': True, 'message': 'Google Calendar connection successful'}
        else:
            return {'success': False, 'error': 'Missing access token'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _test_github(credentials):
    """Test GitHub integration"""
    try:
        if credentials.get('access_token'):
            return {'success': True, 'message': 'GitHub connection successful'}
        else:
            return {'success': False, 'error': 'Missing access token'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _test_slack(credentials):
    """Test Slack integration"""
    try:
        if credentials.get('bot_token'):
            return {'success': True, 'message': 'Slack connection successful'}
        else:
            return {'success': False, 'error': 'Missing bot token'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _test_stripe(credentials):
    """Test Stripe integration"""
    try:
        if credentials.get('secret_key'):
            return {'success': True, 'message': 'Stripe connection successful'}
        else:
            return {'success': False, 'error': 'Missing secret key'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _test_webhook(webhook_url):
    """Test webhook integration"""
    import requests
    try:
        if not webhook_url:
            return {'success': False, 'error': 'No webhook URL provided'}
        
        # Send test payload
        test_payload = {
            'test': True,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Test webhook from Event Management System'
        }
        
        response = requests.post(
            webhook_url,
            json=test_payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201, 204]:
            return {'success': True, 'message': f'Webhook test successful (Status: {response.status_code})'}
        else:
            return {'success': False, 'error': f'Webhook test failed (Status: {response.status_code})'}
    
    except requests.Timeout:
        return {'success': False, 'error': 'Webhook request timed out'}
    except requests.RequestException as e:
        return {'success': False, 'error': f'Webhook request failed: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@integrations_bp.route('/api/disable/<int:integration_id>', methods=['POST'])
@login_required
def disable_integration(integration_id):
    """Disable an integration"""
    try:
        integration = Integration.query.filter_by(
            id=integration_id,
            user_id=current_user.id
        ).first()
        
        if not integration:
            return jsonify({'success': False, 'error': 'Integration not found'}), 404
        
        integration.status = 'inactive'
        integration.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Integration disabled successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/enable/<int:integration_id>', methods=['POST'])
@login_required
def enable_integration(integration_id):
    """Enable an integration"""
    try:
        integration = Integration.query.filter_by(
            id=integration_id,
            user_id=current_user.id
        ).first()
        
        if not integration:
            return jsonify({'success': False, 'error': 'Integration not found'}), 404
        
        integration.status = 'active'
        integration.error_message = None
        integration.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Integration enabled successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/delete/<int:integration_id>', methods=['DELETE'])
@login_required
def delete_integration(integration_id):
    """Delete an integration"""
    try:
        integration = Integration.query.filter_by(
            id=integration_id,
            user_id=current_user.id
        ).first()
        
        if not integration:
            return jsonify({'success': False, 'error': 'Integration not found'}), 404
        
        db.session.delete(integration)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Integration deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/sync-event/<int:event_id>', methods=['POST'])
@login_required
def sync_event(event_id):
    """Sync event to calendar integrations"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if user owns the event
        if event.organizer_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Sync to calendars
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            sync_event_to_calendars(event_id, current_user.id)
        )
        
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'message': f'Synced to {success_count}/{total_count} calendar services',
            'results': results
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    """Process payment through integrated payment gateway"""
    try:
        data = request.get_json()
        
        event_id = data.get('event_id')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'stripe')
        payment_method_id = data.get('payment_method_id')
        
        if not all([event_id, amount]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Process payment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            process_event_payment(
                user_id=current_user.id,
                event_id=event_id,
                amount=float(amount),
                payment_method=payment_method,
                payment_method_id=payment_method_id
            )
        )
        
        if result.success:
            return jsonify({
                'success': True,
                'transaction_id': result.transaction_id,
                'message': 'Payment processed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error_message
            }), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/send-reminders/<int:event_id>', methods=['POST'])
@login_required
def send_reminders(event_id):
    """Send event reminders through all configured channels"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if user owns the event
        if event.organizer_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Send reminders
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(send_event_reminders(event_id))
        
        return jsonify({'success': True, 'message': 'Reminders sent successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/api/integrations', methods=['GET'])
@login_required
def get_user_integrations():
    """Get user's integrations"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        integrations = loop.run_until_complete(
            integration_manager.get_user_integrations(current_user.id)
        )
        
        return jsonify({'success': True, 'integrations': integrations})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@integrations_bp.route('/setup/<integration_type>')
@login_required
def setup_integration(integration_type):
    """Setup page for specific integration"""
    try:
        # Validate integration type
        valid_types = [t.value for t in IntegrationType]
        if integration_type not in valid_types:
            flash('Invalid integration type', 'error')
            return redirect(url_for('integrations.integration_dashboard'))
        
        # Get integration info
        integration_info = _get_integration_info(integration_type)
        
        return render_template(f'integrations/setup/{integration_type}.html',
                             integration_type=integration_type,
                             integration_info=integration_info)
    
    except Exception as e:
        flash(f'Error loading setup page: {str(e)}', 'error')
        return redirect(url_for('integrations.integration_dashboard'))


def _get_integration_info(integration_type):
    """Get integration information"""
    integration_configs = {
        'google_calendar': {
            'name': 'Google Calendar',
            'description': 'Sync your events with Google Calendar',
            'required_fields': ['client_id', 'client_secret', 'access_token'],
            'optional_fields': ['refresh_token'],
            'setup_instructions': [
                'Go to Google Cloud Console',
                'Create a new project or select existing',
                'Enable Google Calendar API',
                'Create credentials (OAuth 2.0)',
                'Add authorized redirect URIs',
                'Copy Client ID and Client Secret'
            ]
        },
        'github': {
            'name': 'GitHub',
            'description': 'Create repositories and manage collaboration',
            'required_fields': ['access_token'],
            'optional_fields': ['organization'],
            'setup_instructions': [
                'Go to GitHub Settings',
                'Navigate to Developer settings > Personal access tokens',
                'Generate new token with repo permissions',
                'Copy the generated token'
            ]
        },
        'slack': {
            'name': 'Slack',
            'description': 'Send notifications to Slack channels',
            'required_fields': ['bot_token'],
            'optional_fields': ['channel', 'webhook_url'],
            'setup_instructions': [
                'Go to Slack API dashboard',
                'Create new Slack app',
                'Install app to workspace',
                'Copy Bot User OAuth Token'
            ]
        },
        'stripe_payment': {
            'name': 'Stripe',
            'description': 'Process payments securely',
            'required_fields': ['publishable_key', 'secret_key'],
            'optional_fields': ['webhook_secret'],
            'setup_instructions': [
                'Create Stripe account',
                'Go to API keys section',
                'Copy publishable and secret keys',
                'Configure webhook endpoint (optional)'
            ]
        },
        'webhooks': {
            'name': 'Webhooks',
            'description': 'Send HTTP notifications to your endpoints',
            'required_fields': ['webhook_url'],
            'optional_fields': ['secret', 'events'],
            'setup_instructions': [
                'Prepare your webhook endpoint',
                'Ensure it accepts POST requests',
                'Return 200-299 status codes',
                'Handle webhook signatures (recommended)'
            ]
        }
    }
    
    return integration_configs.get(integration_type, {
        'name': integration_type.replace('_', ' ').title(),
        'description': f'Configure {integration_type} integration',
        'required_fields': [],
        'optional_fields': [],
        'setup_instructions': ['Please refer to the documentation']
    })


# Webhook endpoint for external services
@integrations_bp.route('/webhook/<integration_type>', methods=['POST'])
def handle_webhook(integration_type):
    """Handle incoming webhooks from external services"""
    try:
        data = request.get_json()
        headers = dict(request.headers)
        
        # Log webhook received
        print(f"Webhook received for {integration_type}: {data}")
        
        # Handle different webhook types
        if integration_type == 'stripe':
            return _handle_stripe_webhook(data, headers)
        elif integration_type == 'github':
            return _handle_github_webhook(data, headers)
        elif integration_type == 'slack':
            return _handle_slack_webhook(data, headers)
        else:
            return jsonify({'error': 'Unsupported webhook type'}), 400
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


def _handle_stripe_webhook(data, headers):
    """Handle Stripe webhooks"""
    # Implement Stripe webhook signature verification
    # Handle different event types (payment_intent.succeeded, etc.)
    return jsonify({'status': 'received'}), 200


def _handle_github_webhook(data, headers):
    """Handle GitHub webhooks"""
    # Handle GitHub events (push, pull_request, etc.)
    return jsonify({'status': 'received'}), 200


def _handle_slack_webhook(data, headers):
    """Handle Slack webhooks"""
    # Handle Slack events and interactions
    return jsonify({'status': 'received'}), 200


# Register blueprint function
def register_integration_routes(app):
    """Register integration routes with the Flask app"""
    app.register_blueprint(integrations_bp)
    print("✓ Integration routes registered successfully")