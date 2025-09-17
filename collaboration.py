"""
Advanced Collaboration Tools for Event Management Platform
Includes real-time chat, file sharing, virtual whiteboards, and collaborative workspaces
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from werkzeug.utils import secure_filename
from flask import current_app
from flask_socketio import emit, join_room, leave_room, rooms
import redis
from cryptography.fernet import Fernet
import zipfile
from PIL import Image
import qrcode
from io import BytesIO
import base64

from database import db
from models import (
    User, Event, Team, CollaborationRoom, CollaborationMessage, 
    CollaborationToolType, UserType
)

logger = logging.getLogger(__name__)

class CollaborationManager:
    """
    Main collaboration management system handling all collaborative features
    """
    
    def __init__(self):
        self.redis_client = self.setup_redis()
        self.encryption_key = self.get_encryption_key()
        self.file_manager = FileManager()
        self.whiteboard_manager = WhiteboardManager()
        self.code_editor_manager = CodeEditorManager()
        self.video_chat_manager = VideoChatManager()
        
    def setup_redis(self):
        """Setup Redis connection for real-time features"""
        try:
            redis_client = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                db=int(os.environ.get('REDIS_DB', 0)),
                decode_responses=True
            )
            redis_client.ping()
            return redis_client
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return None
    
    def get_encryption_key(self):
        """Get or generate encryption key for secure communications"""
        key = os.environ.get('COLLABORATION_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Set COLLABORATION_ENCRYPTION_KEY environment variable.")
        
        return Fernet(key if isinstance(key, bytes) else key.encode())
    
    def create_collaboration_room(self, event_id: int, team_id: Optional[int], 
                                room_type: CollaborationToolType, name: str) -> CollaborationRoom:
        """Create a new collaboration room"""
        try:
            room = CollaborationRoom(
                event_id=event_id,
                team_id=team_id,
                name=name,
                room_type=room_type,
                is_active=True
            )
            
            db.session.add(room)
            db.session.commit()
            
            # Initialize room data in Redis
            if self.redis_client:
                room_data = {
                    'id': room.id,
                    'type': room_type.value,
                    'participants': [],
                    'created_at': datetime.utcnow().isoformat()
                }
                self.redis_client.hset(f"room:{room.id}", mapping=room_data)
            
            logger.info(f"Created collaboration room: {room.id}")
            return room
            
        except Exception as e:
            logger.error(f"Error creating collaboration room: {e}")
            db.session.rollback()
            raise
    
    def join_room_session(self, room_id: int, user_id: int) -> Dict[str, Any]:
        """Join a user to a collaboration room session"""
        try:
            room = CollaborationRoom.query.get_or_404(room_id)
            user = User.query.get_or_404(user_id)
            
            # Check permissions
            if not self.check_room_permissions(room, user):
                raise PermissionError("User not authorized for this room")
            
            # Add user to Redis session
            if self.redis_client:
                self.redis_client.sadd(f"room:{room_id}:participants", user_id)
                self.redis_client.hset(f"room:{room_id}:user:{user_id}", mapping={
                    'username': user.username,
                    'full_name': user.full_name,
                    'joined_at': datetime.utcnow().isoformat(),
                    'is_active': True
                })
            
            # Get room state
            room_state = self.get_room_state(room_id)
            
            return {
                'success': True,
                'room': {
                    'id': room.id,
                    'name': room.name,
                    'type': room.room_type.value,
                    'participants': room_state.get('participants', []),
                    'state': room_state
                }
            }
            
        except Exception as e:
            logger.error(f"Error joining room session: {e}")
            return {'success': False, 'error': str(e)}
    
    def leave_room_session(self, room_id: int, user_id: int):
        """Remove user from collaboration room session"""
        try:
            if self.redis_client:
                self.redis_client.srem(f"room:{room_id}:participants", user_id)
                self.redis_client.delete(f"room:{room_id}:user:{user_id}")
                
                # Clean up user-specific data
                pattern = f"room:{room_id}:user:{user_id}:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    self.redis_client.delete(key)
                    
        except Exception as e:
            logger.error(f"Error leaving room session: {e}")
    
    def get_room_state(self, room_id: int) -> Dict[str, Any]:
        """Get current state of collaboration room"""
        if not self.redis_client:
            return {}
        
        try:
            # Get participants
            participant_ids = self.redis_client.smembers(f"room:{room_id}:participants")
            participants = []
            
            for user_id in participant_ids:
                user_data = self.redis_client.hgetall(f"room:{room_id}:user:{user_id}")
                if user_data:
                    participants.append(user_data)
            
            # Get room-specific state based on type
            room = CollaborationRoom.query.get(room_id)
            if not room:
                return {}
                
            state = {
                'participants': participants,
                'participant_count': len(participants)
            }
            
            if room.room_type == CollaborationToolType.WHITEBOARD:
                state.update(self.whiteboard_manager.get_whiteboard_state(room_id))
            elif room.room_type == CollaborationToolType.CODE_EDITOR:
                state.update(self.code_editor_manager.get_editor_state(room_id))
            elif room.room_type == CollaborationToolType.FILE_SHARING:
                state.update(self.file_manager.get_room_files(room_id))
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting room state: {e}")
            return {}
    
    def check_room_permissions(self, room: CollaborationRoom, user: User) -> bool:
        """Check if user has permission to access the room"""
        # Event organizers have access to all rooms in their events
        if room.event.organizer_id == user.id:
            return True
        
        # Team members have access to their team rooms
        if room.team_id:
            team_member = room.team.members.filter_by(user_id=user.id).first()
            if team_member:
                return True
        
        # Registered attendees have access to general event rooms
        if not room.team_id:
            ticket = user.tickets.filter_by(event_id=room.event_id).first()
            if ticket:
                return True
        
        return False
    
    def send_chat_message(self, room_id: int, user_id: int, message: str, 
                         message_type: str = 'text') -> Dict[str, Any]:
        """Send a chat message to the room"""
        try:
            # Encrypt message content
            encrypted_message = self.encryption_key.encrypt(message.encode()).decode()
            
            # Store in database
            chat_message = CollaborationMessage(
                room_id=room_id,
                user_id=user_id,
                message=encrypted_message,
                message_type=message_type
            )
            
            db.session.add(chat_message)
            db.session.commit()
            
            # Cache in Redis for real-time delivery
            if self.redis_client:
                user = User.query.get(user_id)
                message_data = {
                    'id': chat_message.id,
                    'user_id': user_id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'message': message,
                    'message_type': message_type,
                    'timestamp': chat_message.timestamp.isoformat()
                }
                
                # Add to message stream
                self.redis_client.zadd(
                    f"room:{room_id}:messages",
                    {json.dumps(message_data): chat_message.timestamp.timestamp()}
                )
                
                # Keep only last 100 messages in cache
                self.redis_client.zremrangebyrank(f"room:{room_id}:messages", 0, -101)
            
            return {
                'success': True,
                'message_id': chat_message.id,
                'timestamp': chat_message.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_chat_history(self, room_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get chat message history for a room"""
        try:
            messages = CollaborationMessage.query.filter_by(room_id=room_id) \
                .order_by(CollaborationMessage.timestamp.desc()) \
                .limit(limit).offset(offset).all()
            
            formatted_messages = []
            for msg in messages:
                try:
                    decrypted_message = self.encryption_key.decrypt(msg.message.encode()).decode()
                except:
                    decrypted_message = "[Message could not be decrypted]"
                
                formatted_messages.append({
                    'id': msg.id,
                    'user_id': msg.user_id,
                    'username': msg.user.username,
                    'full_name': msg.user.full_name,
                    'message': decrypted_message,
                    'message_type': msg.message_type,
                    'timestamp': msg.timestamp.isoformat()
                })
            
            return list(reversed(formatted_messages))  # Return in chronological order
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []


class FileManager:
    """
    Handles file sharing and management within collaboration rooms
    """
    
    def __init__(self):
        self.upload_folder = os.path.join(current_app.instance_path, 'uploads', 'collaboration')
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
            'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', 'py', 'js', 
            'html', 'css', 'json', 'xml', 'md', 'csv'
        }
        
        # Create upload directory if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def upload_file(self, file, room_id: int, user_id: int) -> Dict[str, Any]:
        """Upload a file to a collaboration room"""
        try:
            if not file or file.filename == '':
                return {'success': False, 'error': 'No file selected'}
            
            if not self.allowed_file(file.filename):
                return {'success': False, 'error': 'File type not allowed'}
            
            if len(file.read()) > self.max_file_size:
                return {'success': False, 'error': 'File too large'}
            
            file.seek(0)  # Reset file pointer
            
            # Generate secure filename
            original_filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            filename = f"{file_id}_{original_filename}"
            
            # Create room-specific directory
            room_folder = os.path.join(self.upload_folder, str(room_id))
            os.makedirs(room_folder, exist_ok=True)
            
            file_path = os.path.join(room_folder, filename)
            file.save(file_path)
            
            # Store file metadata
            file_info = {
                'id': file_id,
                'original_name': original_filename,
                'filename': filename,
                'size': os.path.getsize(file_path),
                'uploaded_by': user_id,
                'uploaded_at': datetime.utcnow().isoformat(),
                'room_id': room_id,
                'path': file_path
            }
            
            # Store in Redis for quick access
            redis_client = redis.Redis(decode_responses=True)
            if redis_client:
                redis_client.hset(f"room:{room_id}:files", file_id, json.dumps(file_info))
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': original_filename,
                'size': file_info['size']
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_room_files(self, room_id: int) -> Dict[str, List]:
        """Get all files uploaded to a room"""
        try:
            redis_client = redis.Redis(decode_responses=True)
            if not redis_client:
                return {'files': []}
            
            file_data = redis_client.hgetall(f"room:{room_id}:files")
            files = []
            
            for file_id, file_info_json in file_data.items():
                try:
                    file_info = json.loads(file_info_json)
                    files.append({
                        'id': file_info['id'],
                        'name': file_info['original_name'],
                        'size': file_info['size'],
                        'uploaded_by': file_info['uploaded_by'],
                        'uploaded_at': file_info['uploaded_at']
                    })
                except json.JSONDecodeError:
                    continue
            
            # Sort by upload time
            files.sort(key=lambda x: x['uploaded_at'], reverse=True)
            
            return {'files': files}
            
        except Exception as e:
            logger.error(f"Error getting room files: {e}")
            return {'files': []}
    
    def delete_file(self, file_id: str, room_id: int, user_id: int) -> Dict[str, Any]:
        """Delete a file from the collaboration room"""
        try:
            redis_client = redis.Redis(decode_responses=True)
            if not redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            # Get file info
            file_info_json = redis_client.hget(f"room:{room_id}:files", file_id)
            if not file_info_json:
                return {'success': False, 'error': 'File not found'}
            
            file_info = json.loads(file_info_json)
            
            # Check permissions (only uploader or room admin can delete)
            if file_info['uploaded_by'] != user_id:
                room = CollaborationRoom.query.get(room_id)
                if room and room.event.organizer_id != user_id:
                    return {'success': False, 'error': 'Permission denied'}
            
            # Delete physical file
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
            
            # Remove from Redis
            redis_client.hdel(f"room:{room_id}:files", file_id)
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return {'success': False, 'error': str(e)}
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions


class WhiteboardManager:
    """
    Manages virtual whiteboards for collaborative drawing and note-taking
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
    
    def create_whiteboard_stroke(self, room_id: int, user_id: int, stroke_data: Dict) -> Dict[str, Any]:
        """Add a drawing stroke to the whiteboard"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            stroke_id = str(uuid.uuid4())
            stroke_info = {
                'id': stroke_id,
                'user_id': user_id,
                'type': stroke_data.get('type', 'path'),
                'coordinates': stroke_data.get('coordinates', []),
                'style': stroke_data.get('style', {}),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Store stroke in Redis
            self.redis_client.zadd(
                f"room:{room_id}:whiteboard:strokes",
                {json.dumps(stroke_info): datetime.utcnow().timestamp()}
            )
            
            return {
                'success': True,
                'stroke_id': stroke_id
            }
            
        except Exception as e:
            logger.error(f"Error creating whiteboard stroke: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_whiteboard_state(self, room_id: int) -> Dict[str, Any]:
        """Get current whiteboard state"""
        try:
            if not self.redis_client:
                return {'strokes': []}
            
            # Get all strokes
            stroke_data = self.redis_client.zrange(
                f"room:{room_id}:whiteboard:strokes", 
                0, -1, 
                withscores=False
            )
            
            strokes = []
            for stroke_json in stroke_data:
                try:
                    stroke = json.loads(stroke_json)
                    strokes.append(stroke)
                except json.JSONDecodeError:
                    continue
            
            return {
                'strokes': strokes,
                'stroke_count': len(strokes)
            }
            
        except Exception as e:
            logger.error(f"Error getting whiteboard state: {e}")
            return {'strokes': []}
    
    def clear_whiteboard(self, room_id: int, user_id: int) -> Dict[str, Any]:
        """Clear all content from whiteboard"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            # Check permissions
            room = CollaborationRoom.query.get(room_id)
            if room and room.event.organizer_id != user_id:
                return {'success': False, 'error': 'Permission denied'}
            
            self.redis_client.delete(f"room:{room_id}:whiteboard:strokes")
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Error clearing whiteboard: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_whiteboard_snapshot(self, room_id: int, user_id: int) -> Dict[str, Any]:
        """Save whiteboard as image snapshot"""
        try:
            whiteboard_state = self.get_whiteboard_state(room_id)
            
            # Generate image from strokes (simplified version)
            snapshot_id = str(uuid.uuid4())
            snapshot_data = {
                'id': snapshot_id,
                'room_id': room_id,
                'created_by': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'stroke_count': len(whiteboard_state['strokes'])
            }
            
            if self.redis_client:
                self.redis_client.hset(
                    f"room:{room_id}:whiteboard:snapshots",
                    snapshot_id,
                    json.dumps(snapshot_data)
                )
            
            return {
                'success': True,
                'snapshot_id': snapshot_id
            }
            
        except Exception as e:
            logger.error(f"Error saving whiteboard snapshot: {e}")
            return {'success': False, 'error': str(e)}


class CodeEditorManager:
    """
    Manages collaborative code editing sessions
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.supported_languages = {
            'python', 'javascript', 'java', 'cpp', 'c', 'html', 'css', 
            'sql', 'json', 'xml', 'markdown', 'yaml', 'bash'
        }
    
    def create_code_document(self, room_id: int, user_id: int, filename: str, 
                           language: str = 'text') -> Dict[str, Any]:
        """Create a new code document in the collaboration room"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            doc_id = str(uuid.uuid4())
            document_data = {
                'id': doc_id,
                'filename': filename,
                'language': language if language in self.supported_languages else 'text',
                'content': '',
                'created_by': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'version': 1
            }
            
            self.redis_client.hset(
                f"room:{room_id}:code:documents",
                doc_id,
                json.dumps(document_data)
            )
            
            return {
                'success': True,
                'document_id': doc_id,
                'document': document_data
            }
            
        except Exception as e:
            logger.error(f"Error creating code document: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_code_content(self, room_id: int, doc_id: str, user_id: int, 
                           content: str, cursor_position: int = 0) -> Dict[str, Any]:
        """Update code document content"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            # Get current document
            doc_json = self.redis_client.hget(f"room:{room_id}:code:documents", doc_id)
            if not doc_json:
                return {'success': False, 'error': 'Document not found'}
            
            document = json.loads(doc_json)
            document['content'] = content
            document['version'] += 1
            document['last_modified_by'] = user_id
            document['last_modified_at'] = datetime.utcnow().isoformat()
            
            # Update document
            self.redis_client.hset(
                f"room:{room_id}:code:documents",
                doc_id,
                json.dumps(document)
            )
            
            # Store user cursor position
            cursor_data = {
                'user_id': user_id,
                'position': cursor_position,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis_client.hset(
                f"room:{room_id}:code:{doc_id}:cursors",
                user_id,
                json.dumps(cursor_data)
            )
            
            return {
                'success': True,
                'version': document['version']
            }
            
        except Exception as e:
            logger.error(f"Error updating code content: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_editor_state(self, room_id: int) -> Dict[str, Any]:
        """Get current state of code editor"""
        try:
            if not self.redis_client:
                return {'documents': [], 'active_cursors': {}}
            
            # Get all documents
            doc_data = self.redis_client.hgetall(f"room:{room_id}:code:documents")
            documents = []
            
            for doc_id, doc_json in doc_data.items():
                try:
                    doc = json.loads(doc_json)
                    documents.append(doc)
                except json.JSONDecodeError:
                    continue
            
            # Get active cursors for all documents
            active_cursors = {}
            for doc in documents:
                cursor_data = self.redis_client.hgetall(f"room:{room_id}:code:{doc['id']}:cursors")
                cursors = []
                
                for user_id, cursor_json in cursor_data.items():
                    try:
                        cursor = json.loads(cursor_json)
                        # Only include recent cursors (within last 5 minutes)
                        cursor_time = datetime.fromisoformat(cursor['timestamp'])
                        if datetime.utcnow() - cursor_time < timedelta(minutes=5):
                            cursors.append(cursor)
                    except (json.JSONDecodeError, ValueError):
                        continue
                
                if cursors:
                    active_cursors[doc['id']] = cursors
            
            return {
                'documents': documents,
                'active_cursors': active_cursors,
                'document_count': len(documents)
            }
            
        except Exception as e:
            logger.error(f"Error getting editor state: {e}")
            return {'documents': [], 'active_cursors': {}}
    
    def run_code(self, room_id: int, doc_id: str, user_id: int) -> Dict[str, Any]:
        """Execute code (sandbox simulation - for demo purposes)"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            doc_json = self.redis_client.hget(f"room:{room_id}:code:documents", doc_id)
            if not doc_json:
                return {'success': False, 'error': 'Document not found'}
            
            document = json.loads(doc_json)
            
            # Simulate code execution (in real implementation, use secure sandboxing)
            execution_result = {
                'success': True,
                'output': f"Code executed successfully!\n\n[Simulated output for {document['language']} code]",
                'execution_time': '0.123s',
                'language': document['language'],
                'executed_by': user_id,
                'executed_at': datetime.utcnow().isoformat()
            }
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Error running code: {e}")
            return {'success': False, 'error': str(e)}


class VideoChatManager:
    """
    Manages video chat integration and virtual meeting rooms
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
    
    def create_video_room(self, room_id: int, user_id: int) -> Dict[str, Any]:
        """Create a video chat room"""
        try:
            video_room_id = f"video_{room_id}_{uuid.uuid4().hex[:8]}"
            
            video_room_data = {
                'id': video_room_id,
                'collaboration_room_id': room_id,
                'created_by': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True,
                'max_participants': 10
            }
            
            if self.redis_client:
                self.redis_client.hset(
                    f"room:{room_id}:video",
                    "config",
                    json.dumps(video_room_data)
                )
            
            # Generate QR code for easy joining
            qr_data = self.generate_room_qr(video_room_id)
            
            return {
                'success': True,
                'video_room_id': video_room_id,
                'join_url': f"/collaboration/video/{video_room_id}",
                'qr_code': qr_data
            }
            
        except Exception as e:
            logger.error(f"Error creating video room: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_room_qr(self, video_room_id: str) -> str:
        """Generate QR code for video room joining"""
        try:
            join_url = f"{current_app.config.get('BASE_URL', 'http://localhost:5000')}/collaboration/video/{video_room_id}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(join_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 for easy embedding
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return ""
    
    def join_video_room(self, video_room_id: str, user_id: int) -> Dict[str, Any]:
        """Join a video chat session"""
        try:
            if not self.redis_client:
                return {'success': False, 'error': 'Redis not available'}
            
            # Add user to video room participants
            participant_data = {
                'user_id': user_id,
                'joined_at': datetime.utcnow().isoformat(),
                'is_video_enabled': True,
                'is_audio_enabled': True
            }
            
            self.redis_client.hset(
                f"video:{video_room_id}:participants",
                user_id,
                json.dumps(participant_data)
            )
            
            return {
                'success': True,
                'room_id': video_room_id,
                'ice_servers': [  # WebRTC ICE servers
                    {'urls': 'stun:stun.l.google.com:19302'},
                    {'urls': 'stun:stun1.l.google.com:19302'}
                ]
            }
            
        except Exception as e:
            logger.error(f"Error joining video room: {e}")
            return {'success': False, 'error': str(e)}


# Global,collaboration manager instance
collaboration_manager = CollaborationManager()