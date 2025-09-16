"""
Enhanced Chat Models for EVENTSYNC
Supports event-specific chat rooms, private messaging, file sharing, and moderation
"""

from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref
from database import db

class ChatRoomType(Enum):
    EVENT = "event"
    PRIVATE = "private"
    GROUP = "group"
    SUPPORT = "support"
    GENERAL = "general"

class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    SYSTEM = "system"
    POLL = "poll"
    EVENT_UPDATE = "event_update"

class ModerationAction(Enum):
    WARN = "warn"
    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    DELETE_MESSAGE = "delete_message"

class UserStatus(Enum):
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    INVISIBLE = "invisible"
    OFFLINE = "offline"

class ChatRoom(db.Model):
    """Enhanced chat room model"""
    __tablename__ = 'chat_rooms'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    room_type = Column(SQLEnum(ChatRoomType), nullable=False, default=ChatRoomType.GENERAL)
    
    # Event association
    event_id = Column(Integer, ForeignKey('event.id'), nullable=True)
    event = relationship('Event', backref=backref('chat_rooms', lazy='dynamic'))
    
    # Room settings
    is_public = Column(Boolean, default=True)
    is_moderated = Column(Boolean, default=False)
    max_participants = Column(Integer, default=1000)
    allow_file_sharing = Column(Boolean, default=True)
    allow_voice_messages = Column(Boolean, default=True)
    
    # Creator and moderation
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    creator = relationship('User', foreign_keys=[created_by])
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # JSON settings for advanced configuration
    settings = Column(JSON, default={})
    
    # Relationships
    messages = relationship('ChatMessage', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    participants = relationship('ChatParticipant', backref='room', lazy='dynamic', cascade='all, delete-orphan')
    moderators = relationship('ChatModerator', backref='room', lazy='dynamic', cascade='all, delete-orphan')

    def get_active_participants_count(self):
        """Get count of currently active participants"""
        return self.participants.filter_by(is_active=True).count()
    
    def is_user_participant(self, user_id):
        """Check if user is a participant"""
        return self.participants.filter_by(user_id=user_id, is_active=True).first() is not None
    
    def is_user_moderator(self, user_id):
        """Check if user is a moderator"""
        return self.moderators.filter_by(user_id=user_id, is_active=True).first() is not None
    
    def can_user_send_messages(self, user_id):
        """Check if user can send messages"""
        participant = self.participants.filter_by(user_id=user_id).first()
        if not participant or not participant.is_active:
            return False
        return not participant.is_muted
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'room_type': self.room_type.value,
            'event_id': self.event_id,
            'is_public': self.is_public,
            'is_moderated': self.is_moderated,
            'max_participants': self.max_participants,
            'participant_count': self.get_active_participants_count(),
            'created_at': self.created_at.isoformat(),
            'settings': self.settings or {}
        }

class ChatParticipant(db.Model):
    """Chat room participants"""
    __tablename__ = 'chat_participants'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Participant status
    is_active = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)
    muted_until = Column(DateTime, nullable=True)
    
    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_read_message_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)
    
    # User preferences for this room
    notifications_enabled = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', backref=backref('chat_participations', lazy='dynamic'))
    last_read_message = relationship('ChatMessage', foreign_keys=[last_read_message_id])
    
    def is_currently_muted(self):
        """Check if user is currently muted"""
        if not self.is_muted:
            return False
        if self.muted_until and self.muted_until <= datetime.utcnow():
            # Mute has expired
            self.is_muted = False
            self.muted_until = None
            db.session.commit()
            return False
        return True
    
    def get_unread_count(self):
        """Get count of unread messages"""
        if not self.last_read_message_id:
            return self.room.messages.count()
        return self.room.messages.filter(ChatMessage.id > self.last_read_message_id).count()

class ChatModerator(db.Model):
    """Chat room moderators"""
    __tablename__ = 'chat_moderators'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Moderator permissions
    can_delete_messages = Column(Boolean, default=True)
    can_mute_users = Column(Boolean, default=True)
    can_kick_users = Column(Boolean, default=True)
    can_ban_users = Column(Boolean, default=False)
    can_manage_room = Column(Boolean, default=False)
    
    # Metadata
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref=backref('moderator_roles', lazy='dynamic'))
    assigner = relationship('User', foreign_keys=[assigned_by])

class ChatMessage(db.Model):
    """Enhanced chat messages"""
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), default=MessageType.TEXT)
    
    # Reply/thread support
    reply_to_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)
    reply_to = relationship('ChatMessage', remote_side=[id], backref='replies')
    
    # File attachments
    file_url = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_type = Column(String(100), nullable=True)
    
    # Message metadata
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Message reactions and interactions
    reactions = Column(JSON, default={})  # {emoji: [user_ids]}
    mentions = Column(JSON, default=[])  # [user_ids] who are mentioned
    
    # System message data
    system_data = Column(JSON, nullable=True)  # For system messages
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], backref=backref('chat_messages', lazy='dynamic'))
    deleter = relationship('User', foreign_keys=[deleted_by])
    
    def add_reaction(self, emoji, user_id):
        """Add reaction to message"""
        if not self.reactions:
            self.reactions = {}
        
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        
        if user_id not in self.reactions[emoji]:
            self.reactions[emoji].append(user_id)
            db.session.commit()
    
    def remove_reaction(self, emoji, user_id):
        """Remove reaction from message"""
        if not self.reactions or emoji not in self.reactions:
            return
        
        if user_id in self.reactions[emoji]:
            self.reactions[emoji].remove(user_id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]
            db.session.commit()
    
    def get_reaction_count(self, emoji):
        """Get count for specific reaction"""
        if not self.reactions or emoji not in self.reactions:
            return 0
        return len(self.reactions[emoji])
    
    def to_dict(self, include_user=True):
        data = {
            'id': self.id,
            'room_id': self.room_id,
            'user_id': self.user_id,
            'content': self.content,
            'message_type': self.message_type.value,
            'reply_to_id': self.reply_to_id,
            'is_edited': self.is_edited,
            'edited_at': self.edited_at.isoformat() if self.edited_at else None,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat(),
            'reactions': self.reactions or {},
            'mentions': self.mentions or [],
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
        }
        
        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'full_name': self.user.full_name,
                'avatar_url': getattr(self.user, 'avatar_url', None)
            }
        
        return data

class ChatModerationLog(db.Model):
    """Log of moderation actions"""
    __tablename__ = 'chat_moderation_logs'
    
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    moderator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    target_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # Action details
    action = Column(SQLEnum(ModerationAction), nullable=False)
    reason = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in minutes for temporary actions
    
    # Related message (if applicable)
    message_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    room = relationship('ChatRoom', backref=backref('moderation_logs', lazy='dynamic'))
    moderator = relationship('User', foreign_keys=[moderator_id])
    target_user = relationship('User', foreign_keys=[target_user_id])
    message = relationship('ChatMessage', backref='moderation_logs')

class UserPresence(db.Model):
    """User presence and status"""
    __tablename__ = 'user_presence'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, unique=True)
    
    # Status
    status = Column(SQLEnum(UserStatus), default=UserStatus.OFFLINE)
    custom_status = Column(String(200), nullable=True)
    
    # Timestamps
    last_seen = Column(DateTime, default=datetime.utcnow)
    status_updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Current activity
    current_room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=True)
    is_typing_in_room = Column(Integer, ForeignKey('chat_rooms.id'), nullable=True)
    
    # Relationships
    user = relationship('User', backref=backref('presence', uselist=False, cascade='all, delete-orphan'))
    current_room = relationship('ChatRoom', foreign_keys=[current_room_id])
    typing_room = relationship('ChatRoom', foreign_keys=[is_typing_in_room])
    
    def is_online(self):
        """Check if user is considered online"""
        if self.status == UserStatus.OFFLINE:
            return False
        
        # Consider user offline if last seen more than 5 minutes ago
        return (datetime.utcnow() - self.last_seen) < timedelta(minutes=5)
    
    def update_activity(self, room_id=None):
        """Update user activity"""
        self.last_seen = datetime.utcnow()
        self.current_room_id = room_id
        if self.status == UserStatus.OFFLINE:
            self.status = UserStatus.ONLINE
            self.status_updated_at = datetime.utcnow()
        db.session.commit()

class ChatFileShare(db.Model):
    """File sharing in chat"""
    __tablename__ = 'chat_file_shares'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('chat_rooms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # File details
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    mime_type = Column(String(200), nullable=False)
    
    # File metadata
    is_image = Column(Boolean, default=False)
    thumbnail_path = Column(String(500), nullable=True)
    
    # Access control
    download_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship('ChatMessage', backref='file_shares')
    room = relationship('ChatRoom')
    user = relationship('User', backref='uploaded_files')
    
    def get_file_url(self):
        """Get file download URL"""
        return f"/api/chat/files/{self.id}/download"
    
    def get_thumbnail_url(self):
        """Get thumbnail URL for images"""
        if self.is_image and self.thumbnail_path:
            return f"/api/chat/files/{self.id}/thumbnail"
        return None
    
    def is_expired(self):
        """Check if file is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

# Add relationships to existing User model if needed
def add_chat_relationships_to_user():
    """Add chat-related relationships to User model"""
    # This would be called during model initialization
    # User.chat_rooms_created = relationship('ChatRoom', foreign_keys='ChatRoom.created_by')
    # User.chat_messages = relationship('ChatMessage', foreign_keys='ChatMessage.user_id')
    pass