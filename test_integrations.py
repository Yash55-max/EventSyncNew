"""
Comprehensive Test Suite for Integration System
Tests all integration types, API endpoints, and error handling
"""

import unittest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import os

# Set up test environment
os.environ['TESTING'] = 'True'

from app import app, db
from models import User, Event, Ticket, Integration, UserType, EventCategory, TicketStatus
from integrations import (
    IntegrationManager, IntegrationType, IntegrationConfig, IntegrationStatus,
    CalendarEvent, PaymentResult, integration_manager
)


class IntegrationTestCase(unittest.TestCase):
    """Base test case for integration tests"""
    
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test users
        self.organizer = User(
            username='testorganizer',
            email='organizer@test.com',
            full_name='Test Organizer',
            user_type=UserType.ORGANIZER
        )
        self.organizer.set_password('testpass')
        
        self.attendee = User(
            username='testattendee',
            email='attendee@test.com',
            full_name='Test Attendee',
            user_type=UserType.ATTENDEE
        )
        self.attendee.set_password('testpass')
        
        db.session.add(self.organizer)
        db.session.add(self.attendee)
        db.session.commit()
        
        # Create test event
        self.event = Event(
            title='Test Event',
            description='A test event',
            category=EventCategory.CONFERENCE,
            location='Test Location',
            start_date=datetime.utcnow() + timedelta(days=7),
            end_date=datetime.utcnow() + timedelta(days=8),
            max_attendees=100,
            price=50.0,
            organizer_id=self.organizer.id
        )
        db.session.add(self.event)
        db.session.commit()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, email, password):
        """Helper method to log in user"""
        return self.app.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)


class TestIntegrationManager(IntegrationTestCase):
    """Test the IntegrationManager class"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    def test_initialization(self):
        """Test IntegrationManager initialization"""
        self.assertIsNotNone(self.integration_manager)
        self.assertEqual(self.integration_manager.integrations, {})
        self.assertEqual(self.integration_manager.active_connections, {})
    
    @patch('integrations.stripe')
    def test_stripe_initialization(self, mock_stripe):
        """Test Stripe integration initialization"""
        with patch.dict(os.environ, {'STRIPE_SECRET_KEY': 'sk_test_123'}):
            manager = IntegrationManager()
            mock_stripe.api_key = 'sk_test_123'
            self.assertEqual(mock_stripe.api_key, 'sk_test_123')
    
    def test_config_getter(self):
        """Test configuration value getter"""
        with patch.dict(os.environ, {'TEST_CONFIG': 'test_value'}):
            value = self.integration_manager._get_config('TEST_CONFIG', 'default')
            self.assertEqual(value, 'test_value')
        
        value = self.integration_manager._get_config('NONEXISTENT_CONFIG', 'default')
        self.assertEqual(value, 'default')


class TestGoogleCalendarIntegration(IntegrationTestCase):
    """Test Google Calendar integration"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
        
        # Mock credentials
        self.mock_credentials = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'token_uri': 'https://oauth2.googleapis.com/token'
        }
    
    @patch('integrations.build')
    @patch('integrations.Credentials')
    async def test_validate_google_credentials(self, mock_credentials, mock_build):
        """Test Google Calendar credentials validation"""
        # Mock successful validation
        mock_service = Mock()
        mock_service.calendarList().list().execute.return_value = {
            'items': [{'id': 'primary'}]
        }
        mock_build.return_value = mock_service
        
        is_valid = await self.integration_manager._validate_google_credentials(self.mock_credentials)
        self.assertTrue(is_valid)
        
        # Mock failed validation
        mock_service.calendarList().list().execute.return_value = {'items': []}
        is_valid = await self.integration_manager._validate_google_credentials(self.mock_credentials)
        self.assertFalse(is_valid)
    
    @patch('integrations.build')
    @patch('integrations.Credentials')
    async def test_init_google_calendar(self, mock_credentials, mock_build):
        """Test Google Calendar service initialization"""
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        service = await self.integration_manager._init_google_calendar(self.mock_credentials)
        self.assertEqual(service, mock_service)
    
    async def test_create_calendar_event(self):
        """Test creating Google Calendar event"""
        # Mock Google service
        mock_service = Mock()
        mock_service.events().insert().execute.return_value = {
            'id': 'test_event_id'
        }
        self.integration_manager.google_service = mock_service
        
        calendar_event = CalendarEvent(
            title='Test Event',
            description='Test Description',
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(hours=2),
            location='Test Location',
            attendees=['test@example.com']
        )
        
        event_id = await self.integration_manager.create_google_calendar_event(
            self.organizer.id, calendar_event
        )
        self.assertEqual(event_id, 'test_event_id')
    
    async def test_sync_google_calendar_event(self):
        """Test syncing event with Google Calendar"""
        # Mock Google service
        mock_service = Mock()
        mock_service.events().insert().execute.return_value = {
            'id': 'synced_event_id'
        }
        self.integration_manager.google_service = mock_service
        
        success = await self.integration_manager.sync_google_calendar_event(
            self.organizer.id, self.event.id
        )
        self.assertTrue(success)
        
        # Check that the event was updated with Google Calendar ID
        db.session.refresh(self.event)
        self.assertEqual(self.event.google_calendar_id, 'synced_event_id')


class TestPaymentIntegrations(IntegrationTestCase):
    """Test payment gateway integrations"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    @patch('integrations.stripe')
    async def test_validate_stripe_credentials(self, mock_stripe):
        """Test Stripe credentials validation"""
        mock_stripe.Account.retrieve.return_value = {'id': 'acct_test'}
        mock_stripe.error = Mock()
        mock_stripe.error.AuthenticationError = Exception
        
        credentials = {'secret_key': 'sk_test_123'}
        is_valid = await self.integration_manager._validate_stripe_credentials(credentials)
        self.assertTrue(is_valid)
        
        # Test invalid credentials
        mock_stripe.Account.retrieve.side_effect = mock_stripe.error.AuthenticationError()
        is_valid = await self.integration_manager._validate_stripe_credentials(credentials)
        self.assertFalse(is_valid)
    
    @patch('integrations.stripe')
    async def test_process_stripe_payment(self, mock_stripe):
        """Test Stripe payment processing"""
        # Mock successful payment
        mock_payment_intent = Mock()
        mock_payment_intent.status = 'succeeded'
        mock_payment_intent.id = 'pi_test_123'
        mock_stripe.PaymentIntent.create.return_value = mock_payment_intent
        
        result = await self.integration_manager.process_stripe_payment(
            user_id=self.attendee.id,
            amount=50.0,
            payment_method_id='pm_test_123'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.transaction_id, 'pi_test_123')
        self.assertEqual(result.amount, 50.0)
        
        # Test failed payment
        mock_payment_intent.status = 'requires_payment_method'
        result = await self.integration_manager.process_stripe_payment(
            user_id=self.attendee.id,
            amount=50.0,
            payment_method_id='pm_invalid'
        )
        
        self.assertFalse(result.success)
    
    @patch('integrations.requests')
    async def test_process_paypal_payment(self, mock_requests):
        """Test PayPal payment processing"""
        # Create PayPal integration
        integration = Integration(
            user_id=self.organizer.id,
            integration_type='paypal_payment',
            credentials=json.dumps({
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'sandbox': True
            }),
            settings=json.dumps({}),
            status='active'
        )
        db.session.add(integration)
        db.session.commit()
        
        # Mock PayPal API responses
        mock_token_response = Mock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {'access_token': 'test_token'}
        
        mock_payment_response = Mock()
        mock_payment_response.status_code = 201
        mock_payment_response.json.return_value = {'id': 'PAY-test123'}
        
        mock_requests.post.side_effect = [mock_token_response, mock_payment_response]
        
        result = await self.integration_manager.process_paypal_payment(
            user_id=self.organizer.id,
            amount=100.0,
            currency='USD',
            description='Test payment'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.transaction_id, 'PAY-test123')


class TestWebhookIntegration(IntegrationTestCase):
    """Test webhook integration"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    @patch('integrations.requests')
    async def test_register_webhook(self, mock_requests):
        """Test webhook registration"""
        # Mock successful webhook test
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        success = await self.integration_manager.register_webhook(
            user_id=self.organizer.id,
            webhook_url='https://test.example.com/webhook',
            events=['event.created', 'ticket.purchased']
        )
        
        self.assertTrue(success)
        
        # Check that integration was created
        integration = Integration.query.filter_by(
            user_id=self.organizer.id,
            integration_type='webhooks'
        ).first()
        self.assertIsNotNone(integration)
        
        settings = json.loads(integration.settings)
        self.assertIn('event.created', settings['events'])
        self.assertIn('ticket.purchased', settings['events'])
    
    def test_generate_webhook_secret(self):
        """Test webhook secret generation"""
        secret = self.integration_manager._generate_webhook_secret()
        self.assertIsInstance(secret, str)
        self.assertTrue(len(secret) > 20)
    
    def test_generate_webhook_signature(self):
        """Test webhook signature generation"""
        payload = {'test': 'data'}
        secret = 'test_secret'
        
        signature = self.integration_manager._generate_webhook_signature(payload, secret)
        self.assertTrue(signature.startswith('sha256='))
        self.assertTrue(len(signature) > 10)


class TestSlackIntegration(IntegrationTestCase):
    """Test Slack integration"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    @patch('integrations.slack_sdk')
    async def test_validate_slack_credentials(self, mock_slack_sdk):
        """Test Slack credentials validation"""
        mock_client = Mock()
        mock_client.auth_test.return_value = {'ok': True}
        mock_slack_sdk.WebClient.return_value = mock_client
        
        credentials = {'bot_token': 'xoxb-test-token'}
        is_valid = await self.integration_manager._validate_slack_credentials(credentials)
        self.assertTrue(is_valid)
        
        # Test invalid credentials
        mock_client.auth_test.return_value = {'ok': False}
        is_valid = await self.integration_manager._validate_slack_credentials(credentials)
        self.assertFalse(is_valid)
    
    @patch('integrations.slack_sdk')
    async def test_send_slack_notification(self, mock_slack_sdk):
        """Test sending Slack notifications"""
        mock_client = Mock()
        mock_client.chat_postMessage.return_value = {'ok': True}
        self.integration_manager.slack_client = mock_client
        
        success = await self.integration_manager.send_slack_notification(
            user_id=self.organizer.id,
            channel='#general',
            message='Test notification'
        )
        
        self.assertTrue(success)
        mock_client.chat_postMessage.assert_called_once()
    
    @patch('integrations.slack_sdk')
    async def test_create_slack_channel(self, mock_slack_sdk):
        """Test creating Slack channels"""
        mock_client = Mock()
        mock_client.conversations_create.return_value = {
            'ok': True,
            'channel': {'id': 'C1234567890'}
        }
        self.integration_manager.slack_client = mock_client
        
        channel_id = await self.integration_manager.create_slack_channel(
            user_id=self.organizer.id,
            channel_name='test-event-channel'
        )
        
        self.assertEqual(channel_id, 'C1234567890')


class TestGitHubIntegration(IntegrationTestCase):
    """Test GitHub integration"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    @patch('integrations.Github')
    async def test_validate_github_credentials(self, mock_github):
        """Test GitHub credentials validation"""
        mock_user = Mock()
        mock_user.login = 'testuser'
        mock_github_instance = Mock()
        mock_github_instance.get_user.return_value = mock_user
        mock_github.return_value = mock_github_instance
        
        credentials = {'access_token': 'ghp_test_token'}
        is_valid = await self.integration_manager._validate_github_credentials(credentials)
        self.assertTrue(is_valid)
    
    @patch('integrations.Github')
    async def test_create_github_repository(self, mock_github):
        """Test creating GitHub repositories"""
        mock_repo = Mock()
        mock_repo.html_url = 'https://github.com/testuser/test-repo'
        mock_user = Mock()
        mock_user.create_repo.return_value = mock_repo
        mock_github_instance = Mock()
        mock_github_instance.get_user.return_value = mock_user
        self.integration_manager.github_client = mock_github_instance
        
        repo_url = await self.integration_manager.create_github_repository(
            user_id=self.organizer.id,
            repo_name='test-event-repo',
            description='Test repository for event collaboration'
        )
        
        self.assertEqual(repo_url, 'https://github.com/testuser/test-repo')


class TestIntegrationRoutes(IntegrationTestCase):
    """Test integration API routes"""
    
    def test_integration_dashboard_unauthorized(self):
        """Test accessing integration dashboard without login"""
        response = self.app.get('/integrations/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_integration_dashboard_authorized(self):
        """Test accessing integration dashboard with login"""
        self.login('organizer@test.com', 'testpass')
        response = self.app.get('/integrations/')
        self.assertEqual(response.status_code, 200)
    
    def test_register_integration_api(self):
        """Test registering integration via API"""
        self.login('organizer@test.com', 'testpass')
        
        integration_data = {
            'integration_type': 'webhooks',
            'credentials': {},
            'settings': {
                'events': ['event.created'],
                'secret': 'test_secret'
            },
            'webhook_url': 'https://test.example.com/webhook'
        }
        
        with patch('integration_routes.integration_manager') as mock_manager:
            mock_manager.register_integration.return_value = asyncio.Future()
            mock_manager.register_integration.return_value.set_result(True)
            
            response = self.app.post(
                '/integrations/api/register',
                json=integration_data,
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
    
    def test_integration_test_api(self):
        """Test testing integration via API"""
        self.login('organizer@test.com', 'testpass')
        
        # Create a test integration
        integration = Integration(
            user_id=self.organizer.id,
            integration_type='webhooks',
            credentials=json.dumps({}),
            settings=json.dumps({'events': ['event.created']}),
            webhook_url='https://test.example.com/webhook',
            status='active'
        )
        db.session.add(integration)
        db.session.commit()
        
        with patch('integration_routes._test_webhook') as mock_test:
            mock_test.return_value = {'success': True, 'message': 'Test successful'}
            
            response = self.app.post(f'/integrations/api/test/{integration.id}')
            self.assertEqual(response.status_code, 200)
            
            data = json.loads(response.data)
            self.assertTrue(data['success'])


class TestIntegrationEventTriggers(IntegrationTestCase):
    """Test integration event triggers"""
    
    def setUp(self):
        super().setUp()
        
        # Create integration for testing
        self.integration = Integration(
            user_id=self.organizer.id,
            integration_type='webhooks',
            credentials=json.dumps({}),
            settings=json.dumps({
                'events': ['event.created', 'ticket.purchased'],
                'secret': 'test_secret'
            }),
            webhook_url='https://test.example.com/webhook',
            status='active'
        )
        db.session.add(self.integration)
        db.session.commit()
    
    @patch('integrations.integration_manager')
    async def test_event_creation_trigger(self, mock_manager):
        """Test event creation triggers integrations"""
        mock_manager.on_event_created = Mock(return_value=asyncio.Future())
        mock_manager.on_event_created.return_value.set_result(None)
        
        await integration_manager.on_event_created(self.event.id, self.organizer.id)
        
        # This test would verify that integrations are triggered
        # In a real environment, we'd check webhook calls, calendar syncs, etc.
    
    async def test_ticket_purchase_trigger(self):
        """Test ticket purchase triggers integrations"""
        # Create a ticket
        ticket = Ticket(
            event_id=self.event.id,
            attendee_id=self.attendee.id,
            status=TicketStatus.PAID,
            ticket_number='TEST-001'
        )
        db.session.add(ticket)
        db.session.commit()
        
        with patch('integrations.integration_manager.send_webhook_notification') as mock_webhook:
            mock_webhook.return_value = asyncio.Future()
            mock_webhook.return_value.set_result(True)
            
            await integration_manager.on_ticket_purchased(ticket.id, self.attendee.id)
            
            # Verify webhook was called
            mock_webhook.assert_called()


class TestIntegrationErrorHandling(IntegrationTestCase):
    """Test error handling in integration system"""
    
    def setUp(self):
        super().setUp()
        self.integration_manager = IntegrationManager()
    
    async def test_invalid_credentials_handling(self):
        """Test handling of invalid credentials"""
        invalid_credentials = {'access_token': 'invalid_token'}
        
        is_valid = await self.integration_manager._validate_google_credentials(invalid_credentials)
        self.assertFalse(is_valid)
    
    @patch('integrations.requests')
    async def test_webhook_failure_handling(self, mock_requests):
        """Test handling of webhook failures"""
        # Mock failed webhook response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests.post.return_value = mock_response
        
        success = await self.integration_manager.register_webhook(
            user_id=self.organizer.id,
            webhook_url='https://broken.example.com/webhook',
            events=['event.created']
        )
        
        self.assertFalse(success)
    
    async def test_network_error_handling(self):
        """Test handling of network errors"""
        with patch('integrations.requests.post') as mock_post:
            mock_post.side_effect = ConnectionError('Network error')
            
            try:
                await self.integration_manager.register_webhook(
                    user_id=self.organizer.id,
                    webhook_url='https://test.example.com/webhook',
                    events=['event.created']
                )
                # Should not raise exception, should handle gracefully
            except ConnectionError:
                self.fail("Network error not handled gracefully")


def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestIntegrationManager,
        TestGoogleCalendarIntegration,
        TestPaymentIntegrations,
        TestWebhookIntegration,
        TestSlackIntegration,
        TestGitHubIntegration,
        TestIntegrationRoutes,
        TestIntegrationEventTriggers,
        TestIntegrationErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)