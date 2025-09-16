"""
Payment Gateway Service
Handles integration with Stripe and PayPal payment processors
"""
import os
import json
import requests
import stripe
from datetime import datetime
from decimal import Decimal
from flask import current_app
from typing import Dict, Any, Optional, Tuple
from model_extensions.payment import PaymentStatus, PaymentMethod, Currency, Payment
from database import db

# Set Stripe API version
stripe.api_version = "2023-08-16"

class PaymentGatewayError(Exception):
    """Custom exception for payment gateway errors"""
    pass

class StripeGateway:
    """Stripe payment gateway integration"""
    
    def __init__(self, secret_key: str, publishable_key: str, webhook_secret: str = None):
        self.secret_key = secret_key
        self.publishable_key = publishable_key
        self.webhook_secret = webhook_secret
        stripe.api_key = secret_key
    
    def create_payment_intent(self, amount: Decimal, currency: str, description: str,
                            customer_email: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Create a Stripe Payment Intent"""
        try:
            # Convert amount to cents (Stripe expects amounts in smallest currency unit)
            amount_cents = int(amount * 100)
            
            intent_params = {
                'amount': amount_cents,
                'currency': currency.lower(),
                'description': description,
                'automatic_payment_methods': {
                    'enabled': True,
                },
                'metadata': metadata or {}
            }
            
            if customer_email:
                intent_params['receipt_email'] = customer_email
            
            intent = stripe.PaymentIntent.create(**intent_params)
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status,
                'amount': amount,
                'currency': currency,
                'publishable_key': self.publishable_key
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def confirm_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """Confirm a payment intent and get details"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                'success': True,
                'payment_intent_id': intent.id,
                'status': intent.status,
                'amount': Decimal(intent.amount) / 100,  # Convert back from cents
                'currency': intent.currency.upper(),
                'charge_id': intent.latest_charge,
                'receipt_url': intent.charges.data[0].receipt_url if intent.charges.data else None
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def create_refund(self, charge_id: str, amount: Decimal = None, reason: str = None) -> Dict[str, Any]:
        """Create a refund for a charge"""
        try:
            refund_params = {
                'charge': charge_id,
            }
            
            if amount:
                refund_params['amount'] = int(amount * 100)  # Convert to cents
            
            if reason:
                refund_params['reason'] = reason
            
            refund = stripe.Refund.create(**refund_params)
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status,
                'amount': Decimal(refund.amount) / 100,
                'charge_id': refund.charge
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error creating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def verify_webhook(self, payload: str, signature: str) -> Dict[str, Any]:
        """Verify Stripe webhook signature and return event"""
        try:
            if not self.webhook_secret:
                raise PaymentGatewayError("Webhook secret not configured")
            
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            return {
                'success': True,
                'event': event
            }
            
        except ValueError:
            return {'success': False, 'error': 'Invalid payload'}
        except stripe.error.SignatureVerificationError:
            return {'success': False, 'error': 'Invalid signature'}

class PayPalGateway:
    """PayPal payment gateway integration"""
    
    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.base_url = "https://api-m.sandbox.paypal.com" if sandbox else "https://api-m.paypal.com"
        self._access_token = None
        self._token_expires_at = None
    
    def _get_access_token(self) -> str:
        """Get or refresh PayPal access token"""
        now = datetime.utcnow()
        
        if self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'en_US',
                },
                auth=(self.client_id, self.client_secret),
                data={'grant_type': 'client_credentials'}
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data['access_token']
            # Set expiration time slightly before actual expiration
            expires_in = data.get('expires_in', 3600) - 300  # 5 minutes buffer
            self._token_expires_at = now + datetime.timedelta(seconds=expires_in)
            
            return self._access_token
            
        except requests.RequestException as e:
            current_app.logger.error(f"PayPal error getting access token: {str(e)}")
            raise PaymentGatewayError(f"Failed to get PayPal access token: {str(e)}")
    
    def create_order(self, amount: Decimal, currency: str, description: str,
                    return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a PayPal order"""
        try:
            access_token = self._get_access_token()
            
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": str(amount)
                    },
                    "description": description
                }],
                "application_context": {
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                    "brand_name": "EVENTSYNC",
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}',
                },
                json=order_data
            )
            
            response.raise_for_status()
            order = response.json()
            
            # Find approval URL
            approval_url = None
            for link in order.get('links', []):
                if link.get('rel') == 'approve':
                    approval_url = link.get('href')
                    break
            
            return {
                'success': True,
                'order_id': order['id'],
                'approval_url': approval_url,
                'status': order['status']
            }
            
        except requests.RequestException as e:
            current_app.logger.error(f"PayPal error creating order: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PayPalError'
            }
    
    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """Capture a PayPal order after approval"""
        try:
            access_token = self._get_access_token()
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}',
                }
            )
            
            response.raise_for_status()
            capture_data = response.json()
            
            # Extract capture details
            capture = capture_data['purchase_units'][0]['payments']['captures'][0]
            
            return {
                'success': True,
                'order_id': order_id,
                'capture_id': capture['id'],
                'status': capture['status'],
                'amount': Decimal(capture['amount']['value']),
                'currency': capture['amount']['currency_code']
            }
            
        except requests.RequestException as e:
            current_app.logger.error(f"PayPal error capturing order: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PayPalError'
            }
    
    def create_refund(self, capture_id: str, amount: Decimal = None, currency: str = None) -> Dict[str, Any]:
        """Create a refund for a captured payment"""
        try:
            access_token = self._get_access_token()
            
            refund_data = {}
            if amount and currency:
                refund_data['amount'] = {
                    'value': str(amount),
                    'currency_code': currency
                }
            
            response = requests.post(
                f"{self.base_url}/v2/payments/captures/{capture_id}/refund",
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {access_token}',
                },
                json=refund_data
            )
            
            response.raise_for_status()
            refund = response.json()
            
            return {
                'success': True,
                'refund_id': refund['id'],
                'status': refund['status'],
                'amount': Decimal(refund['amount']['value']) if 'amount' in refund else None
            }
            
        except requests.RequestException as e:
            current_app.logger.error(f"PayPal error creating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'PayPalError'
            }

class PaymentGatewayService:
    """Unified payment gateway service"""
    
    def __init__(self):
        self.stripe_gateway = None
        self.paypal_gateway = None
    
    def initialize_stripe(self, secret_key: str, publishable_key: str, webhook_secret: str = None):
        """Initialize Stripe gateway"""
        self.stripe_gateway = StripeGateway(secret_key, publishable_key, webhook_secret)
    
    def initialize_paypal(self, client_id: str, client_secret: str, sandbox: bool = True):
        """Initialize PayPal gateway"""
        self.paypal_gateway = PayPalGateway(client_id, client_secret, sandbox)
    
    def create_payment(self, payment_method: PaymentMethod, amount: Decimal, 
                      currency: Currency, description: str, **kwargs) -> Dict[str, Any]:
        """Create a payment using the specified method"""
        if payment_method == PaymentMethod.STRIPE:
            if not self.stripe_gateway:
                return {'success': False, 'error': 'Stripe not configured'}
            return self.stripe_gateway.create_payment_intent(
                amount, currency.value, description, 
                kwargs.get('customer_email'), kwargs.get('metadata')
            )
        
        elif payment_method == PaymentMethod.PAYPAL:
            if not self.paypal_gateway:
                return {'success': False, 'error': 'PayPal not configured'}
            return self.paypal_gateway.create_order(
                amount, currency.value, description,
                kwargs.get('return_url'), kwargs.get('cancel_url')
            )
        
        else:
            return {'success': False, 'error': f'Unsupported payment method: {payment_method}'}
    
    def process_payment_update(self, payment: Payment, webhook_data: Dict[str, Any]) -> bool:
        """Process payment update from webhook"""
        try:
            if payment.payment_method == PaymentMethod.STRIPE:
                return self._process_stripe_webhook(payment, webhook_data)
            elif payment.payment_method == PaymentMethod.PAYPAL:
                return self._process_paypal_webhook(payment, webhook_data)
            
            return False
            
        except Exception as e:
            current_app.logger.error(f"Error processing payment update: {str(e)}")
            return False
    
    def _process_stripe_webhook(self, payment: Payment, event: Dict[str, Any]) -> bool:
        """Process Stripe webhook event"""
        event_type = event.get('type')
        
        if event_type == 'payment_intent.succeeded':
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.utcnow()
            payment.stripe_charge_id = event['data']['object'].get('latest_charge')
            
        elif event_type == 'payment_intent.payment_failed':
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = event['data']['object'].get('last_payment_error', {}).get('message')
            
        elif event_type == 'payment_intent.canceled':
            payment.status = PaymentStatus.CANCELLED
            
        else:
            return False  # Unhandled event type
        
        payment.gateway_response = json.dumps(event)
        db.session.commit()
        return True
    
    def _process_paypal_webhook(self, payment: Payment, event: Dict[str, Any]) -> bool:
        """Process PayPal webhook event"""
        event_type = event.get('event_type')
        
        if event_type == 'CHECKOUT.ORDER.APPROVED':
            payment.status = PaymentStatus.PROCESSING
            
        elif event_type == 'PAYMENT.CAPTURE.COMPLETED':
            payment.status = PaymentStatus.COMPLETED
            payment.processed_at = datetime.utcnow()
            
        elif event_type == 'PAYMENT.CAPTURE.DECLINED':
            payment.status = PaymentStatus.FAILED
            
        else:
            return False  # Unhandled event type
        
        payment.gateway_response = json.dumps(event)
        db.session.commit()
        return True

# Global payment service instance
payment_service = PaymentGatewayService()