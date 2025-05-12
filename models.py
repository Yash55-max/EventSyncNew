import enum
from datetime import datetime
from app import db
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
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_organizer(self):
        return self.user_type == UserType.ORGANIZER
    
    def is_attendee(self):
        return self.user_type == UserType.ATTENDEE
    
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
    OTHER = "Other"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.Enum(EventCategory), default=EventCategory.OTHER)
    location = db.Column(db.String(120))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    image_url = db.Column(db.String(255))  # URL to event image
    max_attendees = db.Column(db.Integer, default=0)  # 0 means unlimited
    price = db.Column(db.Float, default=0.0)  # 0 means free
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='event', lazy='dynamic', cascade="all, delete-orphan")

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
