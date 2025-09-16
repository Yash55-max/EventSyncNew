"""
WebRTC Calling Models for EVENTSYNC
Supports video calls, audio calls, group calls, and call management
"""

from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref
from database import db

class CallType(Enum):
    AUDIO = "audio"
    VIDEO = "video"
    SCREEN_SHARE = "screen_share"

class CallStatus(Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ON_HOLD = "on_hold"
    ENDED = "ended"
    FAILED = "failed"
    MISSED = "missed"
    DECLINED = "declined"
    BUSY = "busy"

class ParticipantStatus(Enum):
    INVITED = "invited"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    LEFT = "left"
    KICKED = "kicked"

class CallEndReason(Enum):
    NORMAL = "normal"
    TIMEOUT = "timeout"
    ERROR = "error"
    NETWORK_ISSUE = "network_issue"
    USER_DECLINED = "user_declined"
    USER_BUSY = "user_busy"
    MODERATOR_ENDED = "moderator_ended"

class Call(db.Model):
    """Main call model for WebRTC calls"""
    __tablename__ = 'calls'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(String(100), unique=True, nullable=False)  # Unique call identifier
    
    # Call details
    call_type = Column(SQLEnum(CallType), nullable=False)
    title = Column(String(200), nullable=True)  # Optional call title for group calls
    description = Column(Text, nullable=True)
    
    # Call initiator
    initiated_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    initiator = relationship('User', foreign_keys=[initiated_by], backref='initiated_calls')
    
    # Event association (if call is related to an event)
    event_id = Column(Integer, ForeignKey('event.id'), nullable=True)
    event = relationship('Event', backref=backref('calls', lazy='dynamic'))
    
    # Chat room association (if call is from chat room) - Disabled for now
    # chat_room_id = Column(Integer, ForeignKey('chat_room.id'), nullable=True)
    # chat_room = relationship('ChatRoom', backref=backref('calls', lazy='dynamic'))
    
    # Call status and timing
    status = Column(SQLEnum(CallStatus), default=CallStatus.INITIATED)
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled calls
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Call settings
    is_group_call = Column(Boolean, default=False)
    max_participants = Column(Integer, default=50)
    is_recording_enabled = Column(Boolean, default=False)
    is_screen_share_enabled = Column(Boolean, default=True)
    require_moderator_approval = Column(Boolean, default=False)
    
    # Call quality and statistics
    duration_seconds = Column(Integer, default=0)
    max_concurrent_participants = Column(Integer, default=0)
    end_reason = Column(SQLEnum(CallEndReason), nullable=True)
    
    # WebRTC configuration
    ice_servers = Column(JSON, default=[])
    signaling_data = Column(JSON, default={})
    
    # Relationships
    participants = relationship('CallParticipant', backref='call', lazy='dynamic', cascade='all, delete-orphan')
    events = relationship('CallEvent', backref='call', lazy='dynamic', cascade='all, delete-orphan')
    recordings = relationship('CallRecording', backref='call', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_active_participants(self):
        """Get currently active participants"""
        return self.participants.filter_by(status=ParticipantStatus.CONNECTED).all()
    
    def get_participant_count(self):
        """Get total participant count"""
        return self.participants.count()
    
    def get_active_participant_count(self):
        """Get active participant count"""
        return len(self.get_active_participants())
    
    def is_user_participant(self, user_id):
        """Check if user is a participant"""
        return self.participants.filter_by(user_id=user_id).first() is not None
    
    def can_user_join(self, user_id):
        """Check if user can join the call"""
        if self.status not in [CallStatus.INITIATED, CallStatus.RINGING, CallStatus.CONNECTED]:
            return False
        
        if self.get_active_participant_count() >= self.max_participants:
            return False
        
        return True
    
    def calculate_duration(self):
        """Calculate call duration"""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
            return self.duration_seconds
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'call_type': self.call_type.value,
            'title': self.title,
            'status': self.status.value,
            'initiated_by': self.initiated_by,
            'event_id': self.event_id,
            'chat_room_id': self.chat_room_id,
            'is_group_call': self.is_group_call,
            'participant_count': self.get_participant_count(),
            'active_participant_count': self.get_active_participant_count(),
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'settings': {
                'max_participants': self.max_participants,
                'is_recording_enabled': self.is_recording_enabled,
                'is_screen_share_enabled': self.is_screen_share_enabled,
                'require_moderator_approval': self.require_moderator_approval
            }
        }

class CallParticipant(db.Model):
    """Call participants model"""
    __tablename__ = 'call_participants'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Participant details
    status = Column(SQLEnum(ParticipantStatus), default=ParticipantStatus.INVITED)
    is_moderator = Column(Boolean, default=False)
    is_presenter = Column(Boolean, default=False)
    
    # Media settings
    audio_enabled = Column(Boolean, default=True)
    video_enabled = Column(Boolean, default=True)
    screen_share_enabled = Column(Boolean, default=False)
    
    # Connection details
    joined_at = Column(DateTime, nullable=True)
    left_at = Column(DateTime, nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow)
    
    # WebRTC connection data
    peer_id = Column(String(100), nullable=True)
    connection_quality = Column(String(20), default='good')  # good, fair, poor
    
    # Relationships
    user = relationship('User', backref=backref('call_participations', lazy='dynamic'))
    
    def get_duration_in_call(self):
        """Get how long participant was in call"""
        if self.joined_at:
            end_time = self.left_at or datetime.utcnow()
            delta = end_time - self.joined_at
            return int(delta.total_seconds())
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'full_name': self.user.full_name
            } if self.user else None,
            'status': self.status.value,
            'is_moderator': self.is_moderator,
            'is_presenter': self.is_presenter,
            'audio_enabled': self.audio_enabled,
            'video_enabled': self.video_enabled,
            'screen_share_enabled': self.screen_share_enabled,
            'peer_id': self.peer_id,
            'connection_quality': self.connection_quality,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'duration_seconds': self.get_duration_in_call()
        }

class CallEvent(db.Model):
    """Call events and logs"""
    __tablename__ = 'call_events'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # joined, left, muted, unmuted, etc.
    event_data = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', backref=backref('call_events', lazy='dynamic'))

class CallRecording(db.Model):
    """Call recordings model"""
    __tablename__ = 'call_recordings'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False)
    
    # Recording details
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)  # Size in bytes
    duration_seconds = Column(Integer, default=0)
    
    # Recording metadata
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    started_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Recording settings
    audio_quality = Column(String(20), default='high')
    video_quality = Column(String(20), default='720p')
    
    # Relationships
    recorder = relationship('User', backref=backref('recorded_calls', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'filename': self.filename,
            'duration_seconds': self.duration_seconds,
            'file_size': self.file_size,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'started_by': self.started_by,
            'audio_quality': self.audio_quality,
            'video_quality': self.video_quality
        }

class CallInvitation(db.Model):
    """Call invitations for managing call requests"""
    __tablename__ = 'call_invitations'
    
    id = Column(Integer, primary_key=True)
    call_id = Column(Integer, ForeignKey('calls.id'), nullable=False)
    invited_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    invited_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Invitation details
    invitation_message = Column(Text, nullable=True)
    invited_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)
    response = Column(String(20), nullable=True)  # accepted, declined, ignored
    
    # Auto-expiry
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    call = relationship('Call', backref=backref('invitations', lazy='dynamic'))
    invited_user = relationship('User', foreign_keys=[invited_user_id], backref='call_invitations_received')
    inviter = relationship('User', foreign_keys=[invited_by], backref='call_invitations_sent')
    
    def is_expired(self):
        """Check if invitation is expired"""
        if self.expires_at and self.expires_at <= datetime.utcnow():
            return True
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'call_id': self.call_id,
            'invited_user_id': self.invited_user_id,
            'invited_by': self.invited_by,
            'invitation_message': self.invitation_message,
            'invited_at': self.invited_at.isoformat(),
            'responded_at': self.responded_at.isoformat() if self.responded_at else None,
            'response': self.response,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired()
        }

# Add WebRTC-specific methods to User model (if needed)
def add_webrtc_methods_to_user():
    """Add WebRTC-related methods to the existing User model"""
    from models import User
    
    def get_active_calls(self):
        """Get user's active calls"""
        return Call.query.join(CallParticipant).filter(
            CallParticipant.user_id == self.id,
            CallParticipant.status == ParticipantStatus.CONNECTED,
            Call.status.in_([CallStatus.CONNECTED, CallStatus.RINGING])
        ).all()
    
    def is_in_call(self):
        """Check if user is currently in any call"""
        return len(self.get_active_calls()) > 0
    
    def get_call_history(self, limit=50):
        """Get user's call history"""
        return Call.query.join(CallParticipant).filter(
            CallParticipant.user_id == self.id
        ).order_by(Call.created_at.desc()).limit(limit).all()
    
    # Add methods to User class
    User.get_active_calls = get_active_calls
    User.is_in_call = is_in_call
    User.get_call_history = get_call_history

# Initialize WebRTC methods when this module is imported
add_webrtc_methods_to_user()