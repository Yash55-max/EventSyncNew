from database import db
from datetime import datetime
from enum import Enum
import uuid
import secrets

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"

class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"  # Indian UPI payments

class Currency(Enum):
    USD = "USD"
    EUR = "EUR" 
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    INR = "INR"  # Indian Rupees

class PaymentSession(db.Model):
    """Model for tracking UPI payment sessions and automated verification"""
    __tablename__ = 'payment_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), unique=True, nullable=False) # Unique session identifier
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    
    # Session tracking
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_check_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    detection_attempts = db.Column(db.Integer, default=0)
    verification_stage = db.Column(db.String(20), default='initializing') # 'initializing', 'scanning', 'verifying', etc.
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='INR')
    payment_reference = db.Column(db.String(100))
    
    # Status & result
    is_completed = db.Column(db.Boolean, default=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'))
    completed_at = db.Column(db.DateTime)
    
    # Relations
    user = db.relationship('User', backref=db.backref('payment_sessions', lazy=True))
    event = db.relationship('Event', backref=db.backref('payment_sessions', lazy=True))
    ticket = db.relationship('Ticket', backref=db.backref('payment_session', uselist=False))
    payment = db.relationship('Payment', backref=db.backref('payment_session', uselist=False))
    
    def __init__(self, user_id, event_id, amount, currency='INR'):
        self.session_id = f'UPI-{secrets.token_hex(8)}'
        self.user_id = user_id
        self.event_id = event_id
        self.amount = amount
        self.currency = currency
        self.start_time = datetime.utcnow()
        self.last_check_time = datetime.utcnow()
        self.detection_attempts = 0
        self.verification_stage = 'initializing'
    
    def update_check(self, verification_stage=None):
        """Update session after a payment check"""
        self.detection_attempts += 1
        self.last_check_time = datetime.utcnow()
        if verification_stage:
            self.verification_stage = verification_stage
    
    def complete(self, ticket_id=None, payment_id=None):
        """Mark payment session as completed"""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        self.verification_stage = 'completed'
        if ticket_id:
            self.ticket_id = ticket_id
        if payment_id:
            self.payment_id = payment_id
    
    def calculate_elapsed_time(self):
        """Calculate elapsed time since session start in seconds"""
        if self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return 0


class Payment(db.Model):
    """Payment model for handling event ticket payments"""
    __tablename__ = 'payment'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)
    
    # Payment Details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.Enum(Currency), nullable=False, default=Currency.USD)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Gateway Information
    stripe_payment_intent_id = db.Column(db.String(200), nullable=True)
    stripe_charge_id = db.Column(db.String(200), nullable=True)
    paypal_payment_id = db.Column(db.String(200), nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)  # Store full gateway response as JSON
    
    # Transaction Details
    description = db.Column(db.String(500), nullable=True)
    receipt_url = db.Column(db.String(500), nullable=True)
    failure_reason = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='payments')
    event = db.relationship('Event', backref='payments')
    ticket = db.relationship('Ticket', backref='payment', uselist=False)
    refunds = db.relationship('PaymentRefund', backref='payment', lazy='dynamic')
    
    def __repr__(self):
        return f'<Payment {self.payment_id}: {self.amount} {self.currency.value}>'
    
    @property
    def is_successful(self):
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_refundable(self):
        return self.status in [PaymentStatus.COMPLETED] and self.amount > 0
    
    @property
    def total_refunded(self):
        """Calculate total amount refunded"""
        return sum(refund.amount for refund in self.refunds if refund.status == PaymentStatus.COMPLETED)
    
    @property
    def remaining_refundable_amount(self):
        """Calculate remaining amount that can be refunded"""
        return self.amount - self.total_refunded
    
    def to_dict(self):
        """Convert payment to dictionary for API responses"""
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'amount': float(self.amount),
            'currency': self.currency.value,
            'payment_method': self.payment_method.value,
            'status': self.status.value,
            'description': self.description,
            'receipt_url': self.receipt_url,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'event_id': self.event_id,
            'ticket_id': self.ticket_id
        }

class PaymentRefund(db.Model):
    """Model for handling payment refunds"""
    __tablename__ = 'payment_refund'
    
    id = db.Column(db.Integer, primary_key=True)
    refund_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Foreign Keys
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=False)
    processed_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Refund Details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    
    # Gateway Information
    stripe_refund_id = db.Column(db.String(200), nullable=True)
    paypal_refund_id = db.Column(db.String(200), nullable=True)
    gateway_response = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    processed_by = db.relationship('User', backref='processed_refunds')
    
    def __repr__(self):
        return f'<PaymentRefund {self.refund_id}: {self.amount}>'
    
    def to_dict(self):
        """Convert refund to dictionary for API responses"""
        return {
            'id': self.id,
            'refund_id': self.refund_id,
            'payment_id': self.payment_id,
            'amount': float(self.amount),
            'reason': self.reason,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processed_by_user_id': self.processed_by_user_id
        }

class PaymentWebhook(db.Model):
    """Model for storing payment gateway webhook events"""
    __tablename__ = 'payment_webhook'
    
    id = db.Column(db.Integer, primary_key=True)
    webhook_id = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Webhook Details
    gateway = db.Column(db.Enum(PaymentMethod), nullable=False)
    event_type = db.Column(db.String(100), nullable=False)
    gateway_event_id = db.Column(db.String(200), nullable=False)
    
    # Data
    payload = db.Column(db.Text, nullable=False)  # Store full webhook payload as JSON
    processed = db.Column(db.Boolean, default=False, nullable=False)
    processing_error = db.Column(db.Text, nullable=True)
    
    # Associated Payment
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    
    # Timestamps
    received_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<PaymentWebhook {self.webhook_id}: {self.event_type}>'

class PaymentSettings(db.Model):
    """Model for storing payment gateway settings per organizer"""
    __tablename__ = 'payment_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stripe Settings (encrypted)
    stripe_enabled = db.Column(db.Boolean, default=False, nullable=False)
    stripe_publishable_key = db.Column(db.String(200), nullable=True)
    stripe_secret_key = db.Column(db.Text, nullable=True)  # Encrypted
    stripe_webhook_secret = db.Column(db.Text, nullable=True)  # Encrypted
    
    # PayPal Settings (encrypted)
    paypal_enabled = db.Column(db.Boolean, default=False, nullable=False)
    paypal_client_id = db.Column(db.String(200), nullable=True)
    paypal_client_secret = db.Column(db.Text, nullable=True)  # Encrypted
    paypal_webhook_id = db.Column(db.String(200), nullable=True)
    
    # General Settings
    default_currency = db.Column(db.Enum(Currency), nullable=False, default=Currency.USD)
    processing_fee_percentage = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)  # Additional fee
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='payment_settings', uselist=False)
    
    def __repr__(self):
        return f'<PaymentSettings for User {self.user_id}>'
    
    @property
    def has_stripe_configured(self):
        return self.stripe_enabled and self.stripe_publishable_key and self.stripe_secret_key
    
    @property
    def has_paypal_configured(self):
        return self.paypal_enabled and self.paypal_client_id and self.paypal_client_secret
    
    @property
    def has_payment_methods(self):
        return self.has_stripe_configured or self.has_paypal_configured