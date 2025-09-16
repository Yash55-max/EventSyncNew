import enum
from datetime import datetime
from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class UserType(enum.Enum):
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False)
    full_name = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    organized_events = db.relationship('Event', backref='organizer', lazy='dynamic')
    tickets = db.relationship('Ticket', backref='attendee', lazy='dynamic')
    skills = db.relationship('UserSkill', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    interests = db.relationship('UserInterest', backref='user', lazy='dynamic', cascade="all, delete-orphan")
    led_teams = db.relationship('Team', foreign_keys='Team.leader_id', backref='team_leader', lazy='dynamic')
    team_memberships = db.relationship('TeamMember', backref='member', lazy='dynamic', cascade="all, delete-orphan")
    recommendations = db.relationship('AIRecommendation', backref='recommended_user', lazy='dynamic', cascade="all, delete-orphan")
    badges = db.relationship('UserBadge', backref='badge_owner', lazy='dynamic', cascade="all, delete-orphan")
    integrations = db.relationship('Integration', backref='integration_owner', lazy='dynamic', cascade="all, delete-orphan")
    collaboration_messages = db.relationship('CollaborationMessage', backref='sender', lazy='dynamic', cascade="all, delete-orphan")
    feedback_given = db.relationship('EventFeedback', backref='reviewer', lazy='dynamic', cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_organizer(self):
        return self.user_type == UserType.ORGANIZER
    
    def is_attendee(self):
        return self.user_type == UserType.ATTENDEE
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'user_type': self.user_type.value,
            'is_organizer': self.is_organizer(),
            'is_attendee': self.is_attendee()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class EventCategory(enum.Enum):
    CONFERENCE = "Conference"
    WORKSHOP = "Workshop"
    SEMINAR = "Seminar"
    CONCERT = "Concert"
    EXHIBITION = "Exhibition"
    PARTY = "Party"
    NETWORKING = "Networking"
    HACKATHON = "Hackathon"
    WEBINAR = "Webinar"
    VIRTUAL_CONFERENCE = "Virtual Conference"
    HYBRID_EVENT = "Hybrid Event"
    COMPETITION = "Competition"
    BOOTCAMP = "Bootcamp"
    MEETUP = "Meetup"
    OTHER = "Other"

class EventType(enum.Enum):
    IN_PERSON = "In-Person"
    VIRTUAL = "Virtual"
    HYBRID = "Hybrid"
    VR_AR = "VR/AR"

class SkillLevel(enum.Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class CollaborationToolType(enum.Enum):
    CHAT = "Chat"
    WHITEBOARD = "Whiteboard"
    CODE_EDITOR = "Code Editor"
    FILE_SHARING = "File Sharing"
    VIDEO_CALL = "Video Call"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.Enum(EventCategory), default=EventCategory.OTHER)
    event_type = db.Column(db.Enum(EventType), default=EventType.IN_PERSON)
    location = db.Column(db.String(120))
    virtual_link = db.Column(db.String(255))  # For virtual/hybrid events
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(255))  # URL to event image
    max_attendees = db.Column(db.Integer, default=0)  # 0 means unlimited
    price = db.Column(db.Float, default=0.0)  # 0 means free
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # New advanced features
    requires_team = db.Column(db.Boolean, default=False)  # For hackathons/competitions
    max_team_size = db.Column(db.Integer, default=1)
    min_team_size = db.Column(db.Integer, default=1)
    skill_level = db.Column(db.Enum(SkillLevel))
    tags = db.Column(db.Text)  # JSON string of tags
    sustainability_score = db.Column(db.Float, default=0.0)
    carbon_footprint = db.Column(db.Float, default=0.0)  # kg CO2 equivalent
    has_live_streaming = db.Column(db.Boolean, default=False)
    has_interactive_features = db.Column(db.Boolean, default=False)
    enable_collaboration = db.Column(db.Boolean, default=False)
    
    # UPI Payment Information
    upi_id = db.Column(db.String(255), nullable=True)  # UPI ID for payments
    payment_mobile = db.Column(db.String(15), nullable=True)  # Mobile number for payments
    payment_qr_code = db.Column(db.Text, nullable=True)  # Generated QR code data
    accept_upi_payments = db.Column(db.Boolean, default=False)  # Enable UPI payments
    payment_instructions = db.Column(db.Text, nullable=True)  # Custom payment instructions
    
    # Relationships
    tickets = db.relationship('Ticket', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    teams = db.relationship('Team', backref='event', lazy='dynamic', cascade="all, delete-orphan")
    analytics = db.relationship('EventAnalytics', backref='event', uselist=False, cascade="all, delete-orphan")
    collaboration_rooms = db.relationship('CollaborationRoom', backref='event', lazy='dynamic', cascade="all, delete-orphan")

    def attendees_count(self):
        return self.tickets.count()
    
    def is_full(self):
        if self.max_attendees == 0:  # Unlimited
            return False
        return self.attendees_count() >= self.max_attendees
    
    def is_upcoming(self):
        return self.start_date > datetime.utcnow()
    
    def is_ongoing(self):
        now = datetime.utcnow()
        return self.start_date <= now <= self.end_date
    
    def is_past(self):
        return self.end_date < datetime.utcnow()
    
    def __repr__(self):
        return f'<Event {self.title}>'

class TicketStatus(enum.Enum):
    RESERVED = "Reserved"
    PAID = "Paid"
    CANCELLED = "Cancelled"
    USED = "Used"

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    attendee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.RESERVED)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    def set_paid(self):
        self.status = TicketStatus.PAID
        self.paid_at = datetime.utcnow()
    
    def set_cancelled(self):
        self.status = TicketStatus.CANCELLED
        
    def set_used(self):
        self.status = TicketStatus.USED
    
    def __repr__(self):
        return f'<Ticket {self.ticket_number}>'

# New Advanced Models

class UserSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    skill_name = db.Column(db.String(80), nullable=False)
    level = db.Column(db.Enum(SkillLevel), nullable=False)
    verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSkill {self.skill_name}: {self.level.value}>'

class UserInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    interest = db.Column(db.String(80), nullable=False)
    weight = db.Column(db.Float, default=1.0)  # Interest strength
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserInterest {self.interest}>'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_members = db.Column(db.Integer, default=5)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members = db.relationship('TeamMember', backref='team', lazy='dynamic', cascade="all, delete-orphan")
    leader = db.relationship('User', foreign_keys=[leader_id], overlaps="led_teams,team_leader")
    
    def member_count(self):
        return self.members.count()
    
    def is_full(self):
        return self.member_count() >= self.max_members
    
    def __repr__(self):
        return f'<Team {self.name}>'

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(50), default='Member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', overlaps="member,team_memberships")
    
    def __repr__(self):
        return f'<TeamMember {self.user.username}>'

class AIRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    recommendation_type = db.Column(db.String(50))  # 'event', 'team', 'skill_match'
    score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    reason = db.Column(db.Text)  # AI explanation for recommendation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', overlaps="recommendations,recommended_user")
    event = db.relationship('Event')
    
    def __repr__(self):
        return f'<AIRecommendation {self.recommendation_type}: {self.score}>'

class EventAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    total_views = db.Column(db.Integer, default=0)
    unique_visitors = db.Column(db.Integer, default=0)
    registration_rate = db.Column(db.Float, default=0.0)  # %
    attendance_rate = db.Column(db.Float, default=0.0)  # %
    engagement_score = db.Column(db.Float, default=0.0)  # 0-100
    sponsor_roi = db.Column(db.Float, default=0.0)
    feedback_average = db.Column(db.Float, default=0.0)  # 1-5 stars
    collaboration_usage = db.Column(db.Integer, default=0)  # minutes
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<EventAnalytics Event:{self.event_id}>'

class CollaborationRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    name = db.Column(db.String(120), nullable=False)
    room_type = db.Column(db.Enum(CollaborationToolType), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    team = db.relationship('Team')
    messages = db.relationship('CollaborationMessage', backref='room', lazy='dynamic', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<CollaborationRoom {self.name}: {self.room_type.value}>'

class CollaborationMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('collaboration_room.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, file, code, etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', overlaps="collaboration_messages,sender")
    
    def __repr__(self):
        return f'<CollaborationMessage {self.user.username}: {self.message[:20]}...>'

class EventFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    category = db.Column(db.String(50))  # 'content', 'organization', 'platform', etc.
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event')
    user = db.relationship('User', overlaps="feedback_given,reviewer")
    
    def __repr__(self):
        return f'<EventFeedback {self.rating}/5 for Event:{self.event_id}>'

class SustainabilityMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)  # 'carbon_footprint', 'waste', 'energy'
    value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # 'kg CO2', 'kWh', etc.
    description = db.Column(db.Text)
    calculated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    event = db.relationship('Event')
    
    def __repr__(self):
        return f'<SustainabilityMetric {self.metric_type}: {self.value} {self.unit}>'

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    icon_url = db.Column(db.String(255))
    criteria = db.Column(db.Text)  # JSON criteria for earning badge
    points = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Badge {self.name}>'

class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))  # Optional: badge from specific event
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', overlaps="badge_owner,badges")
    badge = db.relationship('Badge')
    event = db.relationship('Event')
    
    def __repr__(self):
        return f'<UserBadge {self.user.username}: {self.badge.name}>'

class Integration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    integration_type = db.Column(db.String(50), nullable=False)  # 'google_calendar', 'github', 'slack'
    credentials = db.Column(db.Text)  # Encrypted JSON credentials
    settings = db.Column(db.Text)  # JSON settings/configuration
    webhook_url = db.Column(db.String(255))  # Webhook URL for notifications
    status = db.Column(db.String(20), default='active')  # active, inactive, error, pending
    
    # Relationships
    user = db.relationship('User', overlaps="integration_owner,integrations")
    
    def __repr__(self):
        return f'<Integration {self.integration_type}>'

    last_sync = db.Column(db.DateTime)  # Last successful sync
    error_message = db.Column(db.Text)  # Last error message
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_active(self):
        return self.status == 'active'
    
    def set_error(self, error_msg):
        self.status = 'error'
        self.error_message = error_msg
        self.updated_at = datetime.utcnow()
    
    def set_active(self):
        self.status = 'active'
        self.error_message = None
        self.last_sync = datetime.utcnow()
        self.updated_at = datetime.utcnow()

# Import payment models to ensure they're registered with SQLAlchemy
from model_extensions.payment import Payment, PaymentRefund, PaymentWebhook, PaymentSettings

# Import WebRTC models to ensure they're registered with SQLAlchemy
try:
    from models_webrtc import (
        CallType, CallStatus, ParticipantStatus, CallEndReason,
        Call, CallParticipant, CallInvitation, CallRecording,
        CallEvent
    )
except ImportError as e:
    print(f"Warning: Could not import WebRTC models: {e}")
