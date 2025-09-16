"""
Seamless Integrations System for Revolutionary Event Management Platform
Google Calendar, Outlook, Payment Gateways, Social Media, GitHub, Slack, and Notifications
"""

import json
import logging
import asyncio
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import stripe
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from msal import ConfidentialClientApplication
import tweepy
import slack_sdk
from github import Github
import paypal_api
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from app import db
from models import Event, User, Ticket, Integration, EventAnalytics

logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    """Types of integrations"""
    GOOGLE_CALENDAR = "google_calendar"
    OUTLOOK_CALENDAR = "outlook_calendar"
    STRIPE_PAYMENT = "stripe_payment"
    PAYPAL_PAYMENT = "paypal_payment"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    GITHUB = "github"
    SLACK = "slack"
    EMAIL_NOTIFICATIONS = "email_notifications"
    SMS_NOTIFICATIONS = "sms_notifications"
    WEBHOOKS = "webhooks"

class IntegrationStatus(Enum):
    """Integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"

@dataclass
class IntegrationConfig:
    """Integration configuration"""
    integration_type: IntegrationType
    credentials: Dict[str, Any]
    settings: Dict[str, Any]
    webhook_url: Optional[str] = None
    enabled: bool = True

@dataclass
class CalendarEvent:
    """Calendar event data structure"""
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    attendees: List[str] = None
    event_id: Optional[str] = None

@dataclass
class PaymentResult:
    """Payment processing result"""
    success: bool
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "USD"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class IntegrationManager:
    """
    Main integration manager for all third-party services
    """
    
    def __init__(self):
        self.integrations = {}
        self.active_connections = {}
        self.webhook_handlers = {}
        
        # Initialize service clients
        self.google_service = None
        self.outlook_service = None
        self.stripe_client = None
        self.paypal_client = None
        self.twitter_client = None
        self.linkedin_client = None
        self.facebook_client = None
        self.github_client = None
        self.slack_client = None
        
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize all integration services"""
        try:
            # Stripe initialization
            stripe.api_key = self._get_config('STRIPE_SECRET_KEY', 'sk_test_example')
            
            logger.info("Integration services initialized")
        except Exception as e:
            logger.error(f"Error initializing integration services: {e}")
    
    def _get_config(self, key: str, default: str = None) -> str:
        """Get configuration value"""
        import os
        return os.getenv(key, default)
    
    async def register_integration(self, user_id: int, integration_config: IntegrationConfig) -> bool:
        """Register a new integration for a user"""
        try:
            # Validate credentials
            is_valid = await self._validate_credentials(integration_config)
            if not is_valid:
                logger.error(f"Invalid credentials for {integration_config.integration_type}")
                return False
            
            # Store integration in database
            integration = Integration(
                user_id=user_id,
                integration_type=integration_config.integration_type.value,
                credentials=json.dumps(integration_config.credentials),
                settings=json.dumps(integration_config.settings),
                webhook_url=integration_config.webhook_url,
                status=IntegrationStatus.ACTIVE.value,
                created_at=datetime.utcnow()
            )
            
            db.session.add(integration)
            db.session.commit()
            
            # Initialize service connection
            await self._initialize_service_connection(user_id, integration_config)
            
            logger.info(f"Integration {integration_config.integration_type} registered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering integration: {e}")
            return False
    
    async def _validate_credentials(self, config: IntegrationConfig) -> bool:
        """Validate integration credentials"""
        try:
            if config.integration_type == IntegrationType.GOOGLE_CALENDAR:
                return await self._validate_google_credentials(config.credentials)
            elif config.integration_type == IntegrationType.OUTLOOK_CALENDAR:
                return await self._validate_outlook_credentials(config.credentials)
            elif config.integration_type == IntegrationType.STRIPE_PAYMENT:
                return await self._validate_stripe_credentials(config.credentials)
            elif config.integration_type == IntegrationType.PAYPAL_PAYMENT:
                return await self._validate_paypal_credentials(config.credentials)
            elif config.integration_type == IntegrationType.GITHUB:
                return await self._validate_github_credentials(config.credentials)
            elif config.integration_type == IntegrationType.SLACK:
                return await self._validate_slack_credentials(config.credentials)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating credentials: {e}")
            return False
    
    async def _initialize_service_connection(self, user_id: int, config: IntegrationConfig):
        """Initialize service connection"""
        integration_type = config.integration_type
        
        if integration_type == IntegrationType.GOOGLE_CALENDAR:
            self.google_service = await self._init_google_calendar(config.credentials)
        elif integration_type == IntegrationType.OUTLOOK_CALENDAR:
            self.outlook_service = await self._init_outlook_calendar(config.credentials)
        elif integration_type == IntegrationType.GITHUB:
            self.github_client = Github(config.credentials.get('access_token'))
        elif integration_type == IntegrationType.SLACK:
            self.slack_client = slack_sdk.WebClient(token=config.credentials.get('bot_token'))
    
    # Google Calendar Integration
    async def _validate_google_credentials(self, credentials: Dict) -> bool:
        """Validate Google Calendar credentials"""
        try:
            creds = Credentials(
                token=credentials.get('access_token'),
                refresh_token=credentials.get('refresh_token'),
                token_uri=credentials.get('token_uri'),
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret')
            )
            
            service = build('calendar', 'v3', credentials=creds)
            calendar_list = service.calendarList().list().execute()
            
            return len(calendar_list.get('items', [])) > 0
            
        except Exception as e:
            logger.error(f"Google credentials validation error: {e}")
            return False
    
    async def _init_google_calendar(self, credentials: Dict):
        """Initialize Google Calendar service"""
        try:
            creds = Credentials(
                token=credentials.get('access_token'),
                refresh_token=credentials.get('refresh_token'),
                token_uri=credentials.get('token_uri'),
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret')
            )
            
            return build('calendar', 'v3', credentials=creds)
            
        except Exception as e:
            logger.error(f"Error initializing Google Calendar: {e}")
            return None
    
    async def create_google_calendar_event(self, user_id: int, event_data: CalendarEvent) -> Optional[str]:
        """Create event in Google Calendar"""
        try:
            if not self.google_service:
                logger.error("Google Calendar service not initialized")
                return None
            
            calendar_event = {
                'summary': event_data.title,
                'description': event_data.description,
                'location': event_data.location,
                'start': {
                    'dateTime': event_data.start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': event_data.end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in (event_data.attendees or [])],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }
            
            created_event = self.google_service.events().insert(
                calendarId='primary',
                body=calendar_event
            ).execute()
            
            logger.info(f"Google Calendar event created: {created_event.get('id')}")
            return created_event.get('id')
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return None
    
    async def sync_google_calendar_event(self, user_id: int, event_id: int) -> bool:
        """Sync event with Google Calendar"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return False
            
            calendar_event = CalendarEvent(
                title=event.title,
                description=event.description,
                start_time=event.start_date,
                end_time=event.end_date,
                location=event.location,
                attendees=[ticket.attendee.email for ticket in event.tickets if ticket.attendee]
            )
            
            google_event_id = await self.create_google_calendar_event(user_id, calendar_event)
            
            if google_event_id:
                # Store Google Calendar event ID for future updates
                event.google_calendar_id = google_event_id
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error syncing with Google Calendar: {e}")
            return False
    
    # Outlook Calendar Integration
    async def _validate_outlook_credentials(self, credentials: Dict) -> bool:
        """Validate Outlook credentials"""
        try:
            app = ConfidentialClientApplication(
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret'),
                authority=f"https://login.microsoftonline.com/{credentials.get('tenant_id')}"
            )
            
            # Test token acquisition
            result = app.acquire_token_by_authorization_code(
                code=credentials.get('auth_code'),
                scopes=['https://graph.microsoft.com/calendars.readwrite'],
                redirect_uri=credentials.get('redirect_uri')
            )
            
            return 'access_token' in result
            
        except Exception as e:
            logger.error(f"Outlook credentials validation error: {e}")
            return False
    
    async def _init_outlook_calendar(self, credentials: Dict):
        """Initialize Outlook Calendar service"""
        try:
            app = ConfidentialClientApplication(
                client_id=credentials.get('client_id'),
                client_secret=credentials.get('client_secret'),
                authority=f"https://login.microsoftonline.com/{credentials.get('tenant_id')}"
            )
            
            return app
            
        except Exception as e:
            logger.error(f"Error initializing Outlook Calendar: {e}")
            return None
    
    async def create_outlook_calendar_event(self, user_id: int, event_data: CalendarEvent) -> Optional[str]:
        """Create event in Outlook Calendar"""
        try:
            if not self.outlook_service:
                logger.error("Outlook Calendar service not initialized")
                return None
            
            # Get access token
            result = self.outlook_service.acquire_token_silent(
                scopes=['https://graph.microsoft.com/calendars.readwrite'],
                account=None
            )
            
            if not result or 'access_token' not in result:
                logger.error("Failed to acquire Outlook access token")
                return None
            
            headers = {
                'Authorization': f"Bearer {result['access_token']}",
                'Content-Type': 'application/json'
            }
            
            calendar_event = {
                'subject': event_data.title,
                'body': {
                    'contentType': 'HTML',
                    'content': event_data.description
                },
                'start': {
                    'dateTime': event_data.start_time.isoformat(),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': event_data.end_time.isoformat(),
                    'timeZone': 'UTC'
                },
                'location': {
                    'displayName': event_data.location or ''
                },
                'attendees': [
                    {
                        'emailAddress': {
                            'address': email,
                            'name': email
                        }
                    } for email in (event_data.attendees or [])
                ]
            }
            
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/events',
                headers=headers,
                json=calendar_event
            )
            
            if response.status_code == 201:
                created_event = response.json()
                logger.info(f"Outlook Calendar event created: {created_event.get('id')}")
                return created_event.get('id')
            else:
                logger.error(f"Outlook Calendar API error: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Outlook Calendar event: {e}")
            return None
    
    # Payment Gateway Integrations
    async def _validate_stripe_credentials(self, credentials: Dict) -> bool:
        """Validate Stripe credentials"""
        try:
            stripe.api_key = credentials.get('secret_key')
            
            # Test API call
            stripe.Account.retrieve()
            return True
            
        except stripe.error.AuthenticationError:
            logger.error("Invalid Stripe credentials")
            return False
        except Exception as e:
            logger.error(f"Stripe credentials validation error: {e}")
            return False
    
    async def process_stripe_payment(self, user_id: int, amount: float, currency: str = "usd", 
                                   payment_method_id: str = None, 
                                   metadata: Dict = None) -> PaymentResult:
        """Process payment through Stripe"""
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency=currency,
                payment_method=payment_method_id,
                confirmation_method='manual',
                confirm=True,
                metadata=metadata or {}
            )
            
            if payment_intent.status == 'succeeded':
                return PaymentResult(
                    success=True,
                    transaction_id=payment_intent.id,
                    amount=amount,
                    currency=currency,
                    metadata={'stripe_payment_intent': payment_intent.id}
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"Payment failed with status: {payment_intent.status}"
                )
                
        except stripe.error.CardError as e:
            return PaymentResult(
                success=False,
                error_message=f"Card error: {e.user_message}"
            )
        except Exception as e:
            logger.error(f"Stripe payment error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e)
            )
    
    async def _validate_paypal_credentials(self, credentials: Dict) -> bool:
        """Validate PayPal credentials"""
        try:
            # Test PayPal credentials with a simple API call
            client_id = credentials.get('client_id')
            client_secret = credentials.get('client_secret')
            sandbox = credentials.get('sandbox', True)
            
            base_url = "https://api.sandbox.paypal.com" if sandbox else "https://api.paypal.com"
            
            # Get access token
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers=headers,
                data='grant_type=client_credentials'
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"PayPal credentials validation error: {e}")
            return False
    
    async def process_paypal_payment(self, user_id: int, amount: float, currency: str = "USD",
                                   description: str = None) -> PaymentResult:
        """Process payment through PayPal"""
        try:
            # Get user's PayPal integration
            integration = Integration.query.filter_by(
                user_id=user_id,
                integration_type=IntegrationType.PAYPAL_PAYMENT.value,
                status=IntegrationStatus.ACTIVE.value
            ).first()
            
            if not integration:
                return PaymentResult(success=False, error_message="PayPal integration not found")
            
            credentials = json.loads(integration.credentials)
            client_id = credentials.get('client_id')
            client_secret = credentials.get('client_secret')
            sandbox = credentials.get('sandbox', True)
            
            base_url = "https://api.sandbox.paypal.com" if sandbox else "https://api.paypal.com"
            
            # Get access token
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
            }
            
            token_response = requests.post(
                f"{base_url}/v1/oauth2/token",
                headers=headers,
                data='grant_type=client_credentials'
            )
            
            if token_response.status_code != 200:
                return PaymentResult(success=False, error_message="Failed to get PayPal access token")
            
            access_token = token_response.json().get('access_token')
            
            # Create payment
            payment_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
            }
            
            payment_data = {
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description or "Event Management Payment"
                }],
                "redirect_urls": {
                    "return_url": "https://your-app.com/paypal/return",
                    "cancel_url": "https://your-app.com/paypal/cancel"
                }
            }
            
            payment_response = requests.post(
                f"{base_url}/v1/payments/payment",
                headers=payment_headers,
                json=payment_data
            )
            
            if payment_response.status_code == 201:
                payment = payment_response.json()
                return PaymentResult(
                    success=True,
                    transaction_id=payment.get('id'),
                    amount=amount,
                    currency=currency,
                    metadata={'paypal_payment': payment}
                )
            else:
                return PaymentResult(
                    success=False,
                    error_message=f"PayPal payment creation failed: {payment_response.text}"
                )
                
        except Exception as e:
            logger.error(f"PayPal payment error: {e}")
            return PaymentResult(success=False, error_message=str(e))
    
    # Social Media Integrations
    async def _validate_github_credentials(self, credentials: Dict) -> bool:
        """Validate GitHub credentials"""
        try:
            github = Github(credentials.get('access_token'))
            user = github.get_user()
            return user.login is not None
            
        except Exception as e:
            logger.error(f"GitHub credentials validation error: {e}")
            return False
    
    async def create_github_repository(self, user_id: int, repo_name: str, 
                                     description: str = None, private: bool = False) -> Optional[str]:
        """Create GitHub repository for event collaboration"""
        try:
            if not self.github_client:
                logger.error("GitHub client not initialized")
                return None
            
            user = self.github_client.get_user()
            repo = user.create_repo(
                name=repo_name,
                description=description or f"Repository for {repo_name}",
                private=private,
                auto_init=True
            )
            
            logger.info(f"GitHub repository created: {repo.html_url}")
            return repo.html_url
            
        except Exception as e:
            logger.error(f"Error creating GitHub repository: {e}")
            return None
    
    async def _validate_slack_credentials(self, credentials: Dict) -> bool:
        """Validate Slack credentials"""
        try:
            client = slack_sdk.WebClient(token=credentials.get('bot_token'))
            response = client.auth_test()
            return response['ok']
            
        except Exception as e:
            logger.error(f"Slack credentials validation error: {e}")
            return False
    
    async def send_slack_notification(self, user_id: int, channel: str, message: str,
                                    attachments: List[Dict] = None) -> bool:
        """Send notification to Slack channel"""
        try:
            if not self.slack_client:
                logger.error("Slack client not initialized")
                return False
            
            response = self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                attachments=attachments
            )
            
            return response['ok']
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def create_slack_channel(self, user_id: int, channel_name: str, 
                                 is_private: bool = False) -> Optional[str]:
        """Create Slack channel for event discussion"""
        try:
            if not self.slack_client:
                logger.error("Slack client not initialized")
                return None
            
            response = self.slack_client.conversations_create(
                name=channel_name,
                is_private=is_private
            )
            
            if response['ok']:
                channel_id = response['channel']['id']
                logger.info(f"Slack channel created: {channel_name} ({channel_id})")
                return channel_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating Slack channel: {e}")
            return None
    
    # Email Notification Integration
    async def send_email_notification(self, user_id: int, to_email: str, subject: str, 
                                    body: str, html_body: str = None) -> bool:
        """Send email notification"""
        try:
            # Get email configuration
            smtp_server = self._get_config('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(self._get_config('SMTP_PORT', '587'))
            smtp_username = self._get_config('SMTP_USERNAME')
            smtp_password = self._get_config('SMTP_PASSWORD')
            
            if not all([smtp_username, smtp_password]):
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_username
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    # Webhook Integration
    async def register_webhook(self, user_id: int, webhook_url: str, events: List[str]) -> bool:
        """Register webhook for event notifications"""
        try:
            # Validate webhook URL
            test_payload = {"test": True, "timestamp": datetime.utcnow().isoformat()}
            
            response = requests.post(
                webhook_url,
                json=test_payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code not in [200, 201, 204]:
                logger.error(f"Webhook validation failed: {response.status_code}")
                return False
            
            # Store webhook configuration
            webhook_config = {
                'url': webhook_url,
                'events': events,
                'secret': self._generate_webhook_secret()
            }
            
            integration = Integration(
                user_id=user_id,
                integration_type=IntegrationType.WEBHOOKS.value,
                credentials=json.dumps({}),
                settings=json.dumps(webhook_config),
                webhook_url=webhook_url,
                status=IntegrationStatus.ACTIVE.value,
                created_at=datetime.utcnow()
            )
            
            db.session.add(integration)
            db.session.commit()
            
            logger.info(f"Webhook registered for user {user_id}: {webhook_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering webhook: {e}")
            return False
    
    def _generate_webhook_secret(self) -> str:
        """Generate secret for webhook signature verification"""
        import secrets
        return secrets.token_urlsafe(32)
    
    async def send_webhook_notification(self, user_id: int, event_type: str, payload: Dict) -> bool:
        """Send webhook notification"""
        try:
            # Get user's webhook integrations
            integrations = Integration.query.filter_by(
                user_id=user_id,
                integration_type=IntegrationType.WEBHOOKS.value,
                status=IntegrationStatus.ACTIVE.value
            ).all()
            
            success = True
            
            for integration in integrations:
                settings = json.loads(integration.settings)
                
                # Check if this event type is subscribed
                if event_type not in settings.get('events', []):
                    continue
                
                # Prepare payload
                webhook_payload = {
                    'event': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': payload
                }
                
                # Generate signature
                secret = settings.get('secret')
                signature = self._generate_webhook_signature(webhook_payload, secret)
                
                headers = {
                    'Content-Type': 'application/json',
                    'X-Webhook-Signature': signature,
                    'X-Event-Type': event_type
                }
                
                try:
                    response = requests.post(
                        integration.webhook_url,
                        json=webhook_payload,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code not in [200, 201, 204]:
                        logger.warning(f"Webhook delivery failed: {response.status_code}")
                        success = False
                        
                except requests.RequestException as e:
                    logger.error(f"Webhook request failed: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False
    
    def _generate_webhook_signature(self, payload: Dict, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    # Event-triggered integrations
    async def on_event_created(self, event_id: int, user_id: int):
        """Trigger integrations when event is created"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return
            
            # Sync with calendar integrations
            await self.sync_google_calendar_event(user_id, event_id)
            
            # Send notifications
            await self._send_event_notifications(event, 'event_created')
            
            # Trigger webhooks
            await self.send_webhook_notification(user_id, 'event.created', {
                'event_id': event_id,
                'title': event.title,
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat()
            })
            
            logger.info(f"Event creation integrations triggered for event {event_id}")
            
        except Exception as e:
            logger.error(f"Error in event creation integrations: {e}")
    
    async def on_event_updated(self, event_id: int, user_id: int):
        """Trigger integrations when event is updated"""
        try:
            event = Event.query.get(event_id)
            if not event:
                return
            
            # Sync with calendar integrations
            await self.sync_google_calendar_event(user_id, event_id)
            
            # Send notifications
            await self._send_event_notifications(event, 'event_updated')
            
            # Trigger webhooks
            await self.send_webhook_notification(user_id, 'event.updated', {
                'event_id': event_id,
                'title': event.title,
                'start_date': event.start_date.isoformat(),
                'end_date': event.end_date.isoformat()
            })
            
            logger.info(f"Event update integrations triggered for event {event_id}")
            
        except Exception as e:
            logger.error(f"Error in event update integrations: {e}")
    
    async def on_ticket_purchased(self, ticket_id: int, user_id: int):
        """Trigger integrations when ticket is purchased"""
        try:
            ticket = Ticket.query.get(ticket_id)
            if not ticket:
                return
            
            # Send confirmation email
            await self.send_email_notification(
                user_id=ticket.attendee_id,
                to_email=ticket.attendee.email,
                subject=f"Ticket Confirmation - {ticket.event.title}",
                body=f"Your ticket for {ticket.event.title} has been confirmed!",
                html_body=self._generate_ticket_email_html(ticket)
            )
            
            # Send Slack notification if configured
            await self.send_slack_notification(
                user_id=ticket.event.organizer_id,
                channel="events",
                message=f"New ticket purchased for {ticket.event.title} by {ticket.attendee.name}"
            )
            
            # Trigger webhooks
            await self.send_webhook_notification(user_id, 'ticket.purchased', {
                'ticket_id': ticket_id,
                'event_id': ticket.event_id,
                'attendee_email': ticket.attendee.email,
                'purchase_date': ticket.purchase_date.isoformat() if ticket.purchase_date else None
            })
            
            logger.info(f"Ticket purchase integrations triggered for ticket {ticket_id}")
            
        except Exception as e:
            logger.error(f"Error in ticket purchase integrations: {e}")
    
    async def _send_event_notifications(self, event: Event, event_type: str):
        """Send event notifications through all configured channels"""
        try:
            # Email notifications to organizer
            await self.send_email_notification(
                user_id=event.organizer_id,
                to_email=event.organizer.email,
                subject=f"Event {event_type.replace('_', ' ').title()} - {event.title}",
                body=f"Your event '{event.title}' has been {event_type.replace('_', ' ')}."
            )
            
            # Social media notifications (if configured)
            # This would integrate with Twitter, LinkedIn, etc. for event promotion
            
        except Exception as e:
            logger.error(f"Error sending event notifications: {e}")
    
    def _generate_ticket_email_html(self, ticket) -> str:
        """Generate HTML email template for ticket confirmation"""
        return f"""
        <html>
        <body>
            <h2>Ticket Confirmation</h2>
            <p>Hello {ticket.attendee.name},</p>
            <p>Your ticket for <strong>{ticket.event.title}</strong> has been confirmed!</p>
            
            <div style="border: 1px solid #ddd; padding: 20px; margin: 20px 0;">
                <h3>Event Details:</h3>
                <p><strong>Event:</strong> {ticket.event.title}</p>
                <p><strong>Date:</strong> {ticket.event.start_date.strftime('%Y-%m-%d %H:%M')}</p>
                <p><strong>Location:</strong> {ticket.event.location or 'Virtual Event'}</p>
                <p><strong>Ticket ID:</strong> {ticket.id}</p>
            </div>
            
            <p>We look forward to seeing you at the event!</p>
            <p>Best regards,<br>Event Management Team</p>
        </body>
        </html>
        """
    
    # Utility methods
    async def get_user_integrations(self, user_id: int) -> List[Dict]:
        """Get all integrations for a user"""
        try:
            integrations = Integration.query.filter_by(user_id=user_id).all()
            
            result = []
            for integration in integrations:
                result.append({
                    'id': integration.id,
                    'type': integration.integration_type,
                    'status': integration.status,
                    'created_at': integration.created_at.isoformat(),
                    'webhook_url': integration.webhook_url
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting user integrations: {e}")
            return []
    
    async def disable_integration(self, user_id: int, integration_id: int) -> bool:
        """Disable an integration"""
        try:
            integration = Integration.query.filter_by(
                id=integration_id,
                user_id=user_id
            ).first()
            
            if integration:
                integration.status = IntegrationStatus.INACTIVE.value
                db.session.commit()
                logger.info(f"Integration {integration_id} disabled for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error disabling integration: {e}")
            return False


# Global integration manager instance
integration_manager = IntegrationManager()


# Utility functions for easy access
async def sync_event_to_calendars(event_id: int, user_id: int) -> Dict[str, bool]:
    """Sync event to all connected calendar services"""
    try:
        results = {}
        
        # Google Calendar
        google_result = await integration_manager.sync_google_calendar_event(user_id, event_id)
        results['google_calendar'] = google_result
        
        # Outlook Calendar could be added here
        # outlook_result = await integration_manager.sync_outlook_calendar_event(user_id, event_id)
        # results['outlook_calendar'] = outlook_result
        
        return results
        
    except Exception as e:
        logger.error(f"Error syncing event to calendars: {e}")
        return {}


async def process_event_payment(user_id: int, event_id: int, amount: float, 
                              payment_method: str = 'stripe', **kwargs) -> PaymentResult:
    """Process payment for event ticket"""
    try:
        if payment_method == 'stripe':
            return await integration_manager.process_stripe_payment(
                user_id=user_id,
                amount=amount,
                metadata={'event_id': event_id},
                **kwargs
            )
        elif payment_method == 'paypal':
            return await integration_manager.process_paypal_payment(
                user_id=user_id,
                amount=amount,
                description=f"Event ticket for event {event_id}",
                **kwargs
            )
        else:
            return PaymentResult(
                success=False,
                error_message=f"Unsupported payment method: {payment_method}"
            )
            
    except Exception as e:
        logger.error(f"Error processing event payment: {e}")
        return PaymentResult(success=False, error_message=str(e))


async def send_event_reminders(event_id: int):
    """Send event reminders through all configured channels"""
    try:
        event = Event.query.get(event_id)
        if not event:
            return
        
        # Get all attendees
        attendees = [ticket.attendee for ticket in event.tickets if ticket.attendee]
        
        for attendee in attendees:
            # Send email reminder
            await integration_manager.send_email_notification(
                user_id=attendee.id,
                to_email=attendee.email,
                subject=f"Reminder: {event.title} starts tomorrow!",
                body=f"Don't forget about {event.title} starting {event.start_date.strftime('%Y-%m-%d at %H:%M')}!",
                html_body=f"""
                <h3>Event Reminder</h3>
                <p>Hello {attendee.name},</p>
                <p>This is a friendly reminder that <strong>{event.title}</strong> starts tomorrow!</p>
                <p><strong>When:</strong> {event.start_date.strftime('%Y-%m-%d at %H:%M')}</p>
                <p><strong>Where:</strong> {event.location or 'Virtual Event'}</p>
                <p>We look forward to seeing you there!</p>
                """
            )
        
        # Send organizer notification
        await integration_manager.send_slack_notification(
            user_id=event.organizer_id,
            channel="events",
            message=f"Reminders sent for {event.title} - {len(attendees)} attendees notified"
        )
        
        logger.info(f"Event reminders sent for event {event_id}")
        
    except Exception as e:
        logger.error(f"Error sending event reminders: {e}")