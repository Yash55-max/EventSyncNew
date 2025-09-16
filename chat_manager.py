"""
Enhanced Chat Manager for EventHub
Handles real-time chat, file sharing, moderation, and presence
"""

import os
import uuid
import logging
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from werkzeug.utils import secure_filename
from PIL import Image
import io

from flask import current_app
from database import db
from models_chat import (
    ChatRoom, ChatMessage, ChatParticipant, ChatModerator, 
    ChatModerationLog, UserPresence, ChatFileShare,
    ChatRoomType, MessageType, ModerationAction, UserStatus
)

logger = logging.getLogger(__name__)

class ChatManager:
    """Enhanced chat manager with comprehensive features"""
    
    def __init__(self, upload_folder=None):
        self.upload_folder = upload_folder or os.path.join(current_app.instance_path, 'chat_uploads')
        self.thumbnail_folder = os.path.join(self.upload_folder, 'thumbnails')
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'},
            'audio': {'mp3', 'wav', 'ogg', 'm4a'},
            'video': {'mp4', 'webm', 'avi', 'mov'},
            'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.ensure_upload_folders()
    
    def ensure_upload_folders(self):
        """Ensure upload folders exist"""
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.thumbnail_folder, exist_ok=True)
    
    # Room Management
    def create_room(self, name: str, creator_id: int, room_type: ChatRoomType = ChatRoomType.GENERAL,
                   description: str = None, event_id: int = None, settings: Dict = None) -> Dict:
        """Create a new chat room"""
        try:
            room = ChatRoom(
                name=name,
                description=description,
                room_type=room_type,
                event_id=event_id,
                created_by=creator_id,
                settings=settings or {}
            )
            
            db.session.add(room)
            db.session.flush()  # Get the room ID
            
            # Add creator as participant and moderator
            self.join_room(room.id, creator_id)
            self.add_moderator(room.id, creator_id, creator_id, can_manage_room=True)
            
            db.session.commit()
            
            logger.info(f"Created chat room {room.id} by user {creator_id}")
            return {'success': True, 'room': room.to_dict()}
            
        except Exception as e:
            logger.error(f"Error creating chat room: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_room(self, room_id: int) -> Optional[ChatRoom]:
        """Get room by ID"""
        return ChatRoom.query.filter_by(id=room_id, is_active=True).first()
    
    def get_user_rooms(self, user_id: int) -> List[Dict]:
        """Get all rooms user is participating in"""
        try:
            participants = ChatParticipant.query.filter_by(
                user_id=user_id, is_active=True
            ).all()
            
            rooms = []
            for participant in participants:
                if participant.room and participant.room.is_active:
                    room_data = participant.room.to_dict()
                    room_data['unread_count'] = participant.get_unread_count()
                    room_data['last_seen'] = participant.last_seen.isoformat()
                    rooms.append(room_data)
            
            return rooms
            
        except Exception as e:
            logger.error(f"Error getting user rooms: {e}")
            return []
    
    def get_event_rooms(self, event_id: int) -> List[Dict]:
        """Get all chat rooms for an event"""
        try:
            rooms = ChatRoom.query.filter_by(
                event_id=event_id, is_active=True
            ).all()
            
            return [room.to_dict() for room in rooms]
            
        except Exception as e:
            logger.error(f"Error getting event rooms: {e}")
            return []
    
    # Participant Management
    def join_room(self, room_id: int, user_id: int) -> Dict:
        """Join a chat room"""
        try:
            room = self.get_room(room_id)
            if not room:
                return {'success': False, 'error': 'Room not found'}
            
            # Check if already a participant
            existing = ChatParticipant.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.joined_at = datetime.utcnow()
            else:
                participant = ChatParticipant(
                    room_id=room_id,
                    user_id=user_id
                )
                db.session.add(participant)
            
            # Update user presence
            self.update_user_presence(user_id, room_id=room_id)
            
            db.session.commit()
            
            logger.info(f"User {user_id} joined room {room_id}")
            return {'success': True, 'room': room.to_dict()}
            
        except Exception as e:
            logger.error(f"Error joining room: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def leave_room(self, room_id: int, user_id: int) -> Dict:
        """Leave a chat room"""
        try:
            participant = ChatParticipant.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            
            if participant:
                participant.is_active = False
                participant.last_seen = datetime.utcnow()
            
            # Update presence
            presence = UserPresence.query.filter_by(user_id=user_id).first()
            if presence and presence.current_room_id == room_id:
                presence.current_room_id = None
            
            db.session.commit()
            
            logger.info(f"User {user_id} left room {room_id}")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error leaving room: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_room_participants(self, room_id: int) -> List[Dict]:
        """Get active participants in a room"""
        try:
            participants = ChatParticipant.query.filter_by(
                room_id=room_id, is_active=True
            ).join(ChatParticipant.user).all()
            
            result = []
            for participant in participants:
                user_data = {
                    'user_id': participant.user.id,
                    'username': participant.user.username,
                    'full_name': participant.user.full_name,
                    'joined_at': participant.joined_at.isoformat(),
                    'last_seen': participant.last_seen.isoformat(),
                    'is_muted': participant.is_currently_muted()
                }
                
                # Add presence info
                presence = UserPresence.query.filter_by(user_id=participant.user.id).first()
                if presence:
                    user_data['status'] = presence.status.value
                    user_data['is_online'] = presence.is_online()
                
                result.append(user_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting room participants: {e}")
            return []
    
    # Message Management
    def send_message(self, room_id: int, user_id: int, content: str, 
                    message_type: MessageType = MessageType.TEXT, 
                    reply_to_id: int = None, file_data: Dict = None) -> Dict:
        """Send a message to a chat room"""
        try:
            room = self.get_room(room_id)
            if not room:
                return {'success': False, 'error': 'Room not found'}
            
            # Check if user can send messages
            if not room.can_user_send_messages(user_id):
                return {'success': False, 'error': 'You are not allowed to send messages'}
            
            # Create message
            message = ChatMessage(
                room_id=room_id,
                user_id=user_id,
                content=content,
                message_type=message_type,
                reply_to_id=reply_to_id
            )
            
            # Handle file attachment
            if file_data:
                message.file_url = file_data.get('file_url')
                message.file_name = file_data.get('file_name')
                message.file_size = file_data.get('file_size')
                message.file_type = file_data.get('file_type')
            
            # Extract mentions
            mentions = self.extract_mentions(content)
            if mentions:
                message.mentions = mentions
            
            db.session.add(message)
            db.session.flush()
            
            # Update participant's last activity
            participant = ChatParticipant.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            if participant:
                participant.last_seen = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Message sent by user {user_id} in room {room_id}")
            return {
                'success': True, 
                'message': message.to_dict(),
                'message_id': message.id
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_messages(self, room_id: int, user_id: int, limit: int = 50, 
                    before_id: int = None) -> List[Dict]:
        """Get messages from a chat room"""
        try:
            # Check if user is participant
            room = self.get_room(room_id)
            if not room or not room.is_user_participant(user_id):
                return []
            
            query = ChatMessage.query.filter_by(
                room_id=room_id, is_deleted=False
            )
            
            if before_id:
                query = query.filter(ChatMessage.id < before_id)
            
            messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            # Mark messages as read
            if messages:
                participant = ChatParticipant.query.filter_by(
                    room_id=room_id, user_id=user_id
                ).first()
                if participant:
                    participant.last_read_message_id = messages[0].id
                    participant.last_seen = datetime.utcnow()
                    db.session.commit()
            
            return [msg.to_dict() for msg in reversed(messages)]
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def edit_message(self, message_id: int, user_id: int, new_content: str) -> Dict:
        """Edit a message"""
        try:
            message = ChatMessage.query.filter_by(
                id=message_id, user_id=user_id, is_deleted=False
            ).first()
            
            if not message:
                return {'success': False, 'error': 'Message not found'}
            
            # Check if message is too old (e.g., older than 24 hours)
            if (datetime.utcnow() - message.created_at) > timedelta(hours=24):
                return {'success': False, 'error': 'Message too old to edit'}
            
            message.content = new_content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            
            # Update mentions
            mentions = self.extract_mentions(new_content)
            message.mentions = mentions
            
            db.session.commit()
            
            return {'success': True, 'message': message.to_dict()}
            
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_message(self, message_id: int, user_id: int, is_moderator: bool = False) -> Dict:
        """Delete a message"""
        try:
            message = ChatMessage.query.filter_by(id=message_id).first()
            if not message:
                return {'success': False, 'error': 'Message not found'}
            
            # Check permissions
            if not is_moderator and message.user_id != user_id:
                return {'success': False, 'error': 'Permission denied'}
            
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            message.deleted_by = user_id
            
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def add_reaction(self, message_id: int, user_id: int, emoji: str) -> Dict:
        """Add reaction to a message"""
        try:
            message = ChatMessage.query.filter_by(id=message_id).first()
            if not message:
                return {'success': False, 'error': 'Message not found'}
            
            message.add_reaction(emoji, user_id)
            return {'success': True, 'reactions': message.reactions}
            
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return {'success': False, 'error': str(e)}
    
    def remove_reaction(self, message_id: int, user_id: int, emoji: str) -> Dict:
        """Remove reaction from a message"""
        try:
            message = ChatMessage.query.filter_by(id=message_id).first()
            if not message:
                return {'success': False, 'error': 'Message not found'}
            
            message.remove_reaction(emoji, user_id)
            return {'success': True, 'reactions': message.reactions}
            
        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            return {'success': False, 'error': str(e)}
    
    # File Sharing
    def upload_file(self, file, room_id: int, user_id: int, message_content: str = "") -> Dict:
        """Upload a file to chat"""
        try:
            if not file or file.filename == '':
                return {'success': False, 'error': 'No file selected'}
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                return {'success': False, 'error': 'File too large'}
            
            # Check file type
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            
            if not self.is_allowed_file(file_ext):
                return {'success': False, 'error': 'File type not allowed'}
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Determine file type and create thumbnail if image
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            is_image = file_ext in self.allowed_extensions['images']
            thumbnail_path = None
            
            if is_image:
                thumbnail_path = self.create_thumbnail(file_path, unique_filename)
            
            # Create message with file
            message_type = self.get_message_type_for_file(file_ext)
            content = message_content or f"Shared file: {filename}"
            
            file_data = {
                'file_url': f"/api/chat/files/{unique_filename}",
                'file_name': filename,
                'file_size': file_size,
                'file_type': file_ext
            }
            
            result = self.send_message(
                room_id=room_id,
                user_id=user_id,
                content=content,
                message_type=message_type,
                file_data=file_data
            )
            
            if result['success']:
                # Create file share record
                file_share = ChatFileShare(
                    message_id=result['message_id'],
                    room_id=room_id,
                    user_id=user_id,
                    original_filename=filename,
                    stored_filename=unique_filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=file_ext,
                    mime_type=mime_type,
                    is_image=is_image,
                    thumbnail_path=thumbnail_path
                )
                
                db.session.add(file_share)
                db.session.commit()
                
                result['file_share_id'] = file_share.id
            
            return result
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_thumbnail(self, file_path: str, filename: str) -> str:
        """Create thumbnail for image"""
        try:
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = os.path.join(self.thumbnail_folder, thumbnail_filename)
            
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Create thumbnail
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, "JPEG", quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    def get_message_type_for_file(self, file_ext: str) -> MessageType:
        """Get message type based on file extension"""
        if file_ext in self.allowed_extensions['images']:
            return MessageType.IMAGE
        elif file_ext in self.allowed_extensions['audio']:
            return MessageType.AUDIO
        elif file_ext in self.allowed_extensions['video']:
            return MessageType.VIDEO
        else:
            return MessageType.FILE
    
    def is_allowed_file(self, file_ext: str) -> bool:
        """Check if file type is allowed"""
        for category in self.allowed_extensions.values():
            if file_ext in category:
                return True
        return False
    
    # User Presence
    def update_user_presence(self, user_id: int, status: UserStatus = None, 
                           custom_status: str = None, room_id: int = None) -> Dict:
        """Update user presence"""
        try:
            presence = UserPresence.query.filter_by(user_id=user_id).first()
            
            if not presence:
                presence = UserPresence(user_id=user_id)
                db.session.add(presence)
            
            if status:
                presence.status = status
                presence.status_updated_at = datetime.utcnow()
            
            if custom_status is not None:
                presence.custom_status = custom_status
            
            if room_id is not None:
                presence.current_room_id = room_id
            
            presence.last_seen = datetime.utcnow()
            
            db.session.commit()
            
            return {'success': True, 'presence': {
                'status': presence.status.value,
                'custom_status': presence.custom_status,
                'last_seen': presence.last_seen.isoformat(),
                'is_online': presence.is_online()
            }}
            
        except Exception as e:
            logger.error(f"Error updating presence: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def set_typing_indicator(self, user_id: int, room_id: int, is_typing: bool) -> Dict:
        """Set typing indicator"""
        try:
            presence = UserPresence.query.filter_by(user_id=user_id).first()
            
            if not presence:
                return {'success': False, 'error': 'User presence not found'}
            
            if is_typing:
                presence.is_typing_in_room = room_id
            else:
                if presence.is_typing_in_room == room_id:
                    presence.is_typing_in_room = None
            
            presence.last_seen = datetime.utcnow()
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error setting typing indicator: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    # Moderation
    def add_moderator(self, room_id: int, user_id: int, assigned_by: int, 
                     **permissions) -> Dict:
        """Add moderator to room"""
        try:
            # Check if already a moderator
            existing = ChatModerator.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            
            if existing:
                if not existing.is_active:
                    existing.is_active = True
                    existing.assigned_at = datetime.utcnow()
                    existing.assigned_by = assigned_by
                # Update permissions
                for key, value in permissions.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
            else:
                moderator = ChatModerator(
                    room_id=room_id,
                    user_id=user_id,
                    assigned_by=assigned_by,
                    **permissions
                )
                db.session.add(moderator)
            
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error adding moderator: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def mute_user(self, room_id: int, user_id: int, moderator_id: int, 
                 duration_minutes: int = None, reason: str = None) -> Dict:
        """Mute a user in a room"""
        try:
            participant = ChatParticipant.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            
            if not participant:
                return {'success': False, 'error': 'User is not a participant'}
            
            participant.is_muted = True
            if duration_minutes:
                participant.muted_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
            
            # Log the action
            log = ChatModerationLog(
                room_id=room_id,
                moderator_id=moderator_id,
                target_user_id=user_id,
                action=ModerationAction.MUTE,
                reason=reason,
                duration=duration_minutes
            )
            if duration_minutes:
                log.expires_at = participant.muted_until
            
            db.session.add(log)
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error muting user: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def unmute_user(self, room_id: int, user_id: int, moderator_id: int) -> Dict:
        """Unmute a user"""
        try:
            participant = ChatParticipant.query.filter_by(
                room_id=room_id, user_id=user_id
            ).first()
            
            if not participant:
                return {'success': False, 'error': 'User is not a participant'}
            
            participant.is_muted = False
            participant.muted_until = None
            
            db.session.commit()
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error unmuting user: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def extract_mentions(self, content: str) -> List[int]:
        """Extract user mentions from message content"""
        # Simple implementation - look for @username patterns
        # In a real implementation, you'd want to validate usernames
        import re
        mentions = []
        
        # Find @username patterns
        pattern = r'@(\w+)'
        matches = re.findall(pattern, content)
        
        if matches:
            # Look up user IDs (simplified)
            from models import User
            for username in matches:
                user = User.query.filter_by(username=username).first()
                if user:
                    mentions.append(user.id)
        
        return mentions

# Global chat manager instance
chat_manager = ChatManager()

def get_chat_manager():
    """Get chat manager instance"""
    return chat_manager