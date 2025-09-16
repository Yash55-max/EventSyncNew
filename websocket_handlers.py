"""
WebSocket handlers for real-time collaboration features
Handles Socket.IO events for chat, whiteboard, code editing, and video chat
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_login import current_user

from collaboration import collaboration_manager
from chat_manager import get_chat_manager
from models import User, CollaborationRoom, CollaborationMessage, CollaborationToolType
from models_chat import (
    ChatRoom, ChatMessage, ChatParticipant, UserPresence,
    ChatRoomType, MessageType, UserStatus
)

logger = logging.getLogger(__name__)

# Global websocket manager instance
websocket_manager = None

def register_handlers(socketio: SocketIO):
    """Register WebSocket handlers with SocketIO instance"""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    logger.info("WebSocket handlers registered successfully")
    return websocket_manager

class WebSocketManager:
    """
    Manages WebSocket connections and real-time collaboration events
    """
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.active_connections = {}  # user_id -> {socket_id, rooms[]}
        self.chat_manager = get_chat_manager()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new WebSocket connection"""
            try:
                if not current_user.is_authenticated:
                    logger.warning("Unauthenticated user attempted WebSocket connection")
                    disconnect()
                    return False
                
                user_id = current_user.id
                socket_id = request.sid
                
                # Track connection
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = {
                        'socket_ids': set(),
                        'rooms': set()
                    }
                
                self.active_connections[user_id]['socket_ids'].add(socket_id)
                
                logger.info(f"User {user_id} connected with socket {socket_id}")
                
                emit('connected', {
                    'status': 'connected',
                    'user_id': user_id,
                    'username': current_user.username
                })
                
                return True
                
            except Exception as e:
                logger.error(f"Error handling connect: {e}")
                disconnect()
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection"""
            try:
                if current_user.is_authenticated:
                    user_id = current_user.id
                    socket_id = request.sid
                    
                    if user_id in self.active_connections:
                        # Remove socket ID
                        self.active_connections[user_id]['socket_ids'].discard(socket_id)
                        
                        # Leave all rooms for this socket
                        rooms_to_leave = list(self.active_connections[user_id]['rooms'])
                        for room_id in rooms_to_leave:
                            self.leave_collaboration_room(room_id, user_id, socket_id)
                        
                        # Clean up if no more sockets
                        if not self.active_connections[user_id]['socket_ids']:
                            del self.active_connections[user_id]
                    
                    logger.info(f"User {user_id} disconnected socket {socket_id}")
                
            except Exception as e:
                logger.error(f"Error handling disconnect: {e}")
        
        @self.socketio.on('join_collaboration_room')
        def handle_join_room(data):
            """Handle joining a collaboration room"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    emit('error', {'message': 'Room ID required'})
                    return
                
                user_id = current_user.id
                socket_id = request.sid
                
                # Join the room session
                result = collaboration_manager.join_room_session(room_id, user_id)
                
                if result['success']:
                    # Join Socket.IO room
                    join_room(str(room_id))
                    
                    # Track in active connections
                    if user_id in self.active_connections:
                        self.active_connections[user_id]['rooms'].add(room_id)
                    
                    # Notify room of new participant
                    emit('user_joined', {
                        'user_id': user_id,
                        'username': current_user.username,
                        'full_name': current_user.full_name,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=str(room_id))
                    
                    # Send room state to user
                    emit('room_state', result['room'])
                    
                    logger.info(f"User {user_id} joined collaboration room {room_id}")
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to join room')})
                
            except Exception as e:
                logger.error(f"Error joining collaboration room: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('leave_collaboration_room')
        def handle_leave_room(data):
            """Handle leaving a collaboration room"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    return
                
                user_id = current_user.id
                socket_id = request.sid
                
                self.leave_collaboration_room(room_id, user_id, socket_id)
                
            except Exception as e:
                logger.error(f"Error leaving collaboration room: {e}")
        
        @self.socketio.on('chat_message')
        def handle_chat_message(data):
            """Handle chat message"""
            try:
                room_id = data.get('room_id')
                message = data.get('message', '').strip()
                message_type = data.get('type', 'text')
                
                if not room_id or not message:
                    emit('error', {'message': 'Room ID and message required'})
                    return
                
                user_id = current_user.id
                
                # Send message through collaboration manager
                result = collaboration_manager.send_chat_message(
                    room_id, user_id, message, message_type
                )
                
                if result['success']:
                    # Broadcast to all room participants
                    message_data = {
                        'id': result['message_id'],
                        'user_id': user_id,
                        'username': current_user.username,
                        'full_name': current_user.full_name,
                        'message': message,
                        'message_type': message_type,
                        'timestamp': result['timestamp']
                    }
                    
                    emit('chat_message', message_data, room=str(room_id))
                    logger.info(f"Chat message sent in room {room_id} by user {user_id}")
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to send message')})
                
            except Exception as e:
                logger.error(f"Error handling chat message: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('whiteboard_stroke')
        def handle_whiteboard_stroke(data):
            """Handle whiteboard drawing stroke"""
            try:
                room_id = data.get('room_id')
                stroke_data = data.get('stroke_data', {})
                
                if not room_id or not stroke_data:
                    emit('error', {'message': 'Room ID and stroke data required'})
                    return
                
                user_id = current_user.id
                
                # Process stroke through whiteboard manager
                result = collaboration_manager.whiteboard_manager.create_whiteboard_stroke(
                    room_id, user_id, stroke_data
                )
                
                if result['success']:
                    # Broadcast stroke to all room participants
                    stroke_event = {
                        'stroke_id': result['stroke_id'],
                        'user_id': user_id,
                        'username': current_user.username,
                        'stroke_data': stroke_data,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    emit('whiteboard_stroke', stroke_event, room=str(room_id), include_self=False)
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to create stroke')})
                
            except Exception as e:
                logger.error(f"Error handling whiteboard stroke: {e}")
                emit('error', {'message': 'Failed to create stroke'})
        
        @self.socketio.on('code_content_change')
        def handle_code_content_change(data):
            """Handle code editor content changes"""
            try:
                room_id = data.get('room_id')
                doc_id = data.get('document_id')
                content = data.get('content', '')
                cursor_position = data.get('cursor_position', 0)
                
                if not room_id or not doc_id:
                    emit('error', {'message': 'Room ID and document ID required'})
                    return
                
                user_id = current_user.id
                
                # Update content through code editor manager
                result = collaboration_manager.code_editor_manager.update_code_content(
                    room_id, doc_id, user_id, content, cursor_position
                )
                
                if result['success']:
                    # Broadcast change to other participants
                    change_event = {
                        'document_id': doc_id,
                        'content': content,
                        'cursor_position': cursor_position,
                        'user_id': user_id,
                        'username': current_user.username,
                        'version': result['version'],
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    emit('code_content_change', change_event, room=str(room_id), include_self=False)
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to update content')})
                
            except Exception as e:
                logger.error(f"Error handling code content change: {e}")
                emit('error', {'message': 'Failed to update content'})
        
        @self.socketio.on('cursor_position')
        def handle_cursor_position(data):
            """Handle cursor position updates in code editor"""
            try:
                room_id = data.get('room_id')
                doc_id = data.get('document_id')
                position = data.get('position', 0)
                
                if not room_id or not doc_id:
                    return
                
                user_id = current_user.id
                
                # Broadcast cursor position to other participants
                cursor_event = {
                    'document_id': doc_id,
                    'user_id': user_id,
                    'username': current_user.username,
                    'position': position,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                emit('cursor_position', cursor_event, room=str(room_id), include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling cursor position: {e}")
        
        @self.socketio.on('video_signal')
        def handle_video_signal(data):
            """Handle WebRTC signaling for video chat"""
            try:
                room_id = data.get('room_id')
                target_user_id = data.get('target_user_id')
                signal_type = data.get('type')  # 'offer', 'answer', 'ice-candidate'
                signal_data = data.get('data')
                
                if not room_id or not signal_type:
                    emit('error', {'message': 'Room ID and signal type required'})
                    return
                
                user_id = current_user.id
                
                # Prepare signal message
                signal_message = {
                    'type': signal_type,
                    'data': signal_data,
                    'from_user_id': user_id,
                    'from_username': current_user.username,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if target_user_id:
                    # Send to specific user
                    self.send_to_user(target_user_id, 'video_signal', signal_message)
                else:
                    # Broadcast to room (for offers)
                    emit('video_signal', signal_message, room=str(room_id), include_self=False)
                
                logger.info(f"Video signal {signal_type} from user {user_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error handling video signal: {e}")
                emit('error', {'message': 'Failed to process video signal'})
        
        @self.socketio.on('screen_share')
        def handle_screen_share(data):
            """Handle screen sharing events"""
            try:
                room_id = data.get('room_id')
                action = data.get('action')  # 'start', 'stop'
                
                if not room_id or not action:
                    emit('error', {'message': 'Room ID and action required'})
                    return
                
                user_id = current_user.id
                
                screen_share_event = {
                    'action': action,
                    'user_id': user_id,
                    'username': current_user.username,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                emit('screen_share', screen_share_event, room=str(room_id))
                logger.info(f"Screen share {action} by user {user_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error handling screen share: {e}")
                emit('error', {'message': 'Failed to process screen share'})
        
        @self.socketio.on('file_upload_progress')
        def handle_file_upload_progress(data):
            """Handle file upload progress updates"""
            try:
                room_id = data.get('room_id')
                file_id = data.get('file_id')
                progress = data.get('progress', 0)
                
                if not room_id or not file_id:
                    return
                
                user_id = current_user.id
                
                progress_event = {
                    'file_id': file_id,
                    'user_id': user_id,
                    'username': current_user.username,
                    'progress': progress,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                emit('file_upload_progress', progress_event, room=str(room_id), include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling file upload progress: {e}")
        
        @self.socketio.on('typing_indicator')
        def handle_typing_indicator(data):
            """Handle typing indicators for chat"""
            try:
                room_id = data.get('room_id')
                is_typing = data.get('is_typing', False)
                
                if not room_id:
                    return
                
                user_id = current_user.id
                
                typing_event = {
                    'user_id': user_id,
                    'username': current_user.username,
                    'is_typing': is_typing,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                emit('typing_indicator', typing_event, room=str(room_id), include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing indicator: {e}")
        
        @self.socketio.on('presence_update')
        def handle_presence_update(data):
            """Handle user presence updates"""
            try:
                room_id = data.get('room_id')
                status = data.get('status', 'active')  # 'active', 'away', 'busy'
                
                if not room_id:
                    return
                
                user_id = current_user.id
                
                presence_event = {
                    'user_id': user_id,
                    'username': current_user.username,
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                emit('presence_update', presence_event, room=str(room_id), include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling presence update: {e}")
        
        @self.socketio.on('request_room_state')
        def handle_request_room_state(data):
            """Handle request for current room state"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    emit('error', {'message': 'Room ID required'})
                    return
                
                # Get current room state
                room_state = collaboration_manager.get_room_state(room_id)
                emit('room_state_update', {
                    'room_id': room_id,
                    'state': room_state
                })
                
            except Exception as e:
                logger.error(f"Error handling room state request: {e}")
                emit('error', {'message': 'Failed to get room state'})
        
        # Enhanced Chat Handlers
        @self.socketio.on('join_chat_room')
        def handle_join_chat_room(data):
            """Handle joining a chat room"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    emit('error', {'message': 'Room ID required'})
                    return
                
                user_id = current_user.id
                
                # Join the chat room
                result = self.chat_manager.join_room(room_id, user_id)
                
                if result['success']:
                    # Join Socket.IO room
                    join_room(f"chat_{room_id}")
                    
                    # Track in active connections
                    if user_id in self.active_connections:
                        self.active_connections[user_id]['rooms'].add(f"chat_{room_id}")
                    
                    # Get recent messages
                    messages = self.chat_manager.get_messages(room_id, user_id, limit=50)
                    
                    # Get participants
                    participants = self.chat_manager.get_room_participants(room_id)
                    
                    # Notify room of new participant
                    emit('user_joined_chat', {
                        'user_id': user_id,
                        'username': current_user.username,
                        'full_name': current_user.full_name,
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=f"chat_{room_id}")
                    
                    # Send room data to user
                    emit('chat_room_joined', {
                        'room': result['room'],
                        'messages': messages,
                        'participants': participants
                    })
                    
                    logger.info(f"User {user_id} joined chat room {room_id}")
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to join room')})
                
            except Exception as e:
                logger.error(f"Error joining chat room: {e}")
                emit('error', {'message': 'Internal server error'})
        
        @self.socketio.on('send_chat_message')
        def handle_send_chat_message(data):
            """Handle sending chat message"""
            try:
                room_id = data.get('room_id')
                content = data.get('content', '').strip()
                message_type = MessageType(data.get('message_type', 'text'))
                reply_to_id = data.get('reply_to_id')
                
                if not room_id or not content:
                    emit('error', {'message': 'Room ID and content required'})
                    return
                
                user_id = current_user.id
                
                # Send message through chat manager
                result = self.chat_manager.send_message(
                    room_id=room_id,
                    user_id=user_id,
                    content=content,
                    message_type=message_type,
                    reply_to_id=reply_to_id
                )
                
                if result['success']:
                    # Broadcast to all room participants
                    emit('new_chat_message', result['message'], room=f"chat_{room_id}")
                    logger.info(f"Chat message sent by user {user_id} in room {room_id}")
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to send message')})
                
            except Exception as e:
                logger.error(f"Error sending chat message: {e}")
                emit('error', {'message': 'Failed to send message'})
        
        @self.socketio.on('add_message_reaction')
        def handle_add_message_reaction(data):
            """Handle adding reaction to message"""
            try:
                message_id = data.get('message_id')
                emoji = data.get('emoji')
                room_id = data.get('room_id')
                
                if not message_id or not emoji or not room_id:
                    emit('error', {'message': 'Message ID, emoji, and room ID required'})
                    return
                
                user_id = current_user.id
                
                result = self.chat_manager.add_reaction(message_id, user_id, emoji)
                
                if result['success']:
                    # Broadcast reaction to room
                    emit('message_reaction_added', {
                        'message_id': message_id,
                        'emoji': emoji,
                        'user_id': user_id,
                        'username': current_user.username,
                        'reactions': result['reactions'],
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=f"chat_{room_id}")
                    
                else:
                    emit('error', {'message': result.get('error', 'Failed to add reaction')})
                
            except Exception as e:
                logger.error(f"Error adding message reaction: {e}")
                emit('error', {'message': 'Failed to add reaction'})
        
        @self.socketio.on('chat_typing_start')
        def handle_chat_typing_start(data):
            """Handle typing indicator start"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    return
                
                user_id = current_user.id
                
                # Update typing status
                self.chat_manager.set_typing_indicator(user_id, room_id, True)
                
                # Broadcast typing indicator
                emit('user_typing_start', {
                    'user_id': user_id,
                    'username': current_user.username,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"chat_{room_id}", include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing start: {e}")
        
        @self.socketio.on('chat_typing_stop')
        def handle_chat_typing_stop(data):
            """Handle typing indicator stop"""
            try:
                room_id = data.get('room_id')
                if not room_id:
                    return
                
                user_id = current_user.id
                
                # Update typing status
                self.chat_manager.set_typing_indicator(user_id, room_id, False)
                
                # Broadcast typing indicator stop
                emit('user_typing_stop', {
                    'user_id': user_id,
                    'username': current_user.username,
                    'timestamp': datetime.utcnow().isoformat()
                }, room=f"chat_{room_id}", include_self=False)
                
            except Exception as e:
                logger.error(f"Error handling typing stop: {e}")
    
    def leave_collaboration_room(self, room_id: int, user_id: int, socket_id: str):
        """Helper method to leave a collaboration room"""
        try:
            # Leave Socket.IO room
            leave_room(str(room_id))
            
            # Remove from session
            collaboration_manager.leave_room_session(room_id, user_id)
            
            # Update active connections
            if user_id in self.active_connections:
                self.active_connections[user_id]['rooms'].discard(room_id)
            
            # Notify room of user leaving
            self.socketio.emit('user_left', {
                'user_id': user_id,
                'username': getattr(current_user, 'username', 'Unknown'),
                'timestamp': datetime.utcnow().isoformat()
            }, room=str(room_id))
            
            logger.info(f"User {user_id} left collaboration room {room_id}")
            
        except Exception as e:
            logger.error(f"Error leaving collaboration room: {e}")
    
    def send_to_user(self, user_id: int, event: str, data: Dict[str, Any]):
        """Send event to specific user across all their socket connections"""
        try:
            if user_id in self.active_connections:
                socket_ids = self.active_connections[user_id]['socket_ids']
                for socket_id in socket_ids:
                    self.socketio.emit(event, data, room=socket_id)
            
        except Exception as e:
            logger.error(f"Error sending to user {user_id}: {e}")
    
    def broadcast_to_room(self, room_id: int, event: str, data: Dict[str, Any], exclude_user: int = None):
        """Broadcast event to all users in a collaboration room"""
        try:
            # Get room participants
            room_state = collaboration_manager.get_room_state(room_id)
            participants = room_state.get('participants', [])
            
            for participant in participants:
                participant_user_id = participant.get('user_id')
                if participant_user_id and participant_user_id != exclude_user:
                    self.send_to_user(participant_user_id, event, data)
            
        except Exception as e:
            logger.error(f"Error broadcasting to room {room_id}: {e}")
    
    def get_room_participants(self, room_id: int) -> list:
        """Get list of active participants in a room"""
        try:
            room_state = collaboration_manager.get_room_state(room_id)
            return room_state.get('participants', [])
            
        except Exception as e:
            logger.error(f"Error getting room participants: {e}")
            return []
    
    def cleanup_inactive_connections(self):
        """Clean up inactive connections (called periodically)"""
        try:
            # This would be called by a background task
            # Remove users who haven't been active for a while
            pass
            
        except Exception as e:
            logger.error(f"Error cleaning up connections: {e}")


# Global WebSocket manager instance (will be initialized with app)
websocket_manager = None


def init_websocket_manager(socketio: SocketIO):
    """Initialize the WebSocket manager with the SocketIO instance"""
    global websocket_manager
    websocket_manager = WebSocketManager(socketio)
    return websocket_manager
