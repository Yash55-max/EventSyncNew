"""
WebRTC WebSocket Handlers for EVENTSYNC
Real-time signaling for video/audio calls using WebSocket
"""

import logging
import json
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from webrtc_manager import webrtc_manager
from models_webrtc import CallStatus, ParticipantStatus

logger = logging.getLogger(__name__)

class WebRTCWebSocketHandler:
    """WebRTC WebSocket event handlers"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.user_sessions = {}  # Track user sessions
        self.call_rooms = {}     # Track call room memberships
        
    def register_handlers(self):
        """Register all WebRTC WebSocket event handlers"""
        
        # Call Management Events
        @self.socketio.on('webrtc_join_call')
        def handle_join_call(data):
            """Handle user joining a call room"""
            try:
                if not current_user.is_authenticated:
                    emit('webrtc_error', {'error': 'Not authenticated'})
                    return
                
                call_id = data.get('call_id')
                if not call_id:
                    emit('webrtc_error', {'error': 'Call ID required'})
                    return
                
                # Validate call exists and user can join
                call = webrtc_manager.get_call_by_id(call_id)
                if not call:
                    emit('webrtc_error', {'error': 'Call not found'})
                    return
                
                if not call.is_user_participant(current_user.id):
                    emit('webrtc_error', {'error': 'Not authorized to join call'})
                    return
                
                # Join the call room
                join_room(f"call_{call_id}")
                
                # Update user session tracking
                self.user_sessions[current_user.id] = {
                    'call_id': call_id,
                    'session_id': data.get('session_id'),
                    'joined_at': datetime.utcnow()
                }
                
                # Update call room tracking
                if call_id not in self.call_rooms:
                    self.call_rooms[call_id] = set()
                self.call_rooms[call_id].add(current_user.id)
                
                # Notify others in the call
                emit('webrtc_user_joined', {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'full_name': current_user.full_name,
                    'joined_at': datetime.utcnow().isoformat()
                }, room=f"call_{call_id}", include_self=False)
                
                # Send current participants to the joining user
                participants = []
                if call_id in self.call_rooms:
                    for user_id in self.call_rooms[call_id]:
                        if user_id != current_user.id:
                            participants.append({
                                'user_id': user_id,
                                'session_id': self.user_sessions.get(user_id, {}).get('session_id')
                            })
                
                emit('webrtc_call_joined', {
                    'call_id': call_id,
                    'participants': participants,
                    'call_info': call.to_dict()
                })
                
                logger.info(f"User {current_user.id} joined call {call_id}")
                
            except Exception as e:
                logger.error(f"Error joining call: {str(e)}")
                emit('webrtc_error', {'error': 'Failed to join call'})
        
        @self.socketio.on('webrtc_leave_call')
        def handle_leave_call(data):
            """Handle user leaving a call room"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                if not call_id:
                    return
                
                # Leave the call room
                leave_room(f"call_{call_id}")
                
                # Update tracking
                if call_id in self.call_rooms:
                    self.call_rooms[call_id].discard(current_user.id)
                    if not self.call_rooms[call_id]:
                        del self.call_rooms[call_id]
                
                if current_user.id in self.user_sessions:
                    del self.user_sessions[current_user.id]
                
                # Notify others in the call
                emit('webrtc_user_left', {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'left_at': datetime.utcnow().isoformat()
                }, room=f"call_{call_id}")
                
                logger.info(f"User {current_user.id} left call {call_id}")
                
            except Exception as e:
                logger.error(f"Error leaving call: {str(e)}")
        
        # WebRTC Signaling Events
        @self.socketio.on('webrtc_signal')
        def handle_webrtc_signal(data):
            """Handle WebRTC signaling messages"""
            try:
                if not current_user.is_authenticated:
                    emit('webrtc_error', {'error': 'Not authenticated'})
                    return
                
                call_id = data.get('call_id')
                target_user_id = data.get('target_user_id')
                signal_type = data.get('signal_type')
                signal_data = data.get('signal_data')
                
                if not all([call_id, signal_type, signal_data]):
                    emit('webrtc_error', {'error': 'Missing required signaling data'})
                    return
                
                # Validate call and participant
                call = webrtc_manager.get_call_by_id(call_id)
                if not call or not call.is_user_participant(current_user.id):
                    emit('webrtc_error', {'error': 'Not authorized for this call'})
                    return
                
                # Handle signaling through manager
                result = webrtc_manager.handle_webrtc_signal(
                    call_id, current_user.id, target_user_id, signal_type, signal_data
                )
                
                if not result['success']:
                    emit('webrtc_error', {'error': result['error']})
                    return
                
                # Forward signal to target user or broadcast
                signal_message = {
                    'call_id': call_id,
                    'from_user_id': current_user.id,
                    'signal_type': signal_type,
                    'signal_data': signal_data,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if target_user_id:
                    # Send to specific user
                    emit('webrtc_signal_received', signal_message, 
                         room=f"user_{target_user_id}")
                else:
                    # Broadcast to all participants except sender
                    emit('webrtc_signal_received', signal_message, 
                         room=f"call_{call_id}", include_self=False)
                
                logger.debug(f"WebRTC signal {signal_type} from {current_user.id} in call {call_id}")
                
            except Exception as e:
                logger.error(f"Error handling WebRTC signal: {str(e)}")
                emit('webrtc_error', {'error': 'Signaling failed'})
        
        @self.socketio.on('webrtc_ice_candidate')
        def handle_ice_candidate(data):
            """Handle ICE candidate exchange"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                target_user_id = data.get('target_user_id')
                candidate = data.get('candidate')
                
                if not all([call_id, target_user_id, candidate]):
                    emit('webrtc_error', {'error': 'Missing ICE candidate data'})
                    return
                
                # Validate call participation
                call = webrtc_manager.get_call_by_id(call_id)
                if not call or not call.is_user_participant(current_user.id):
                    emit('webrtc_error', {'error': 'Not authorized for this call'})
                    return
                
                # Forward ICE candidate to target user
                emit('webrtc_ice_candidate_received', {
                    'call_id': call_id,
                    'from_user_id': current_user.id,
                    'candidate': candidate
                }, room=f"user_{target_user_id}")
                
                logger.debug(f"ICE candidate from {current_user.id} to {target_user_id} in call {call_id}")
                
            except Exception as e:
                logger.error(f"Error handling ICE candidate: {str(e)}")
        
        # Media Control Events
        @self.socketio.on('webrtc_toggle_audio')
        def handle_toggle_audio(data):
            """Handle audio toggle"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                audio_enabled = data.get('audio_enabled', False)
                
                # Update participant media settings
                result = webrtc_manager.update_participant_media(
                    call_id, current_user.id, {'audio_enabled': audio_enabled}
                )
                
                if result['success']:
                    # Notify other participants
                    emit('webrtc_audio_toggled', {
                        'user_id': current_user.id,
                        'audio_enabled': audio_enabled
                    }, room=f"call_{call_id}", include_self=False)
                    
                    emit('webrtc_media_updated', result)
                else:
                    emit('webrtc_error', {'error': result['error']})
                
            except Exception as e:
                logger.error(f"Error toggling audio: {str(e)}")
                emit('webrtc_error', {'error': 'Failed to toggle audio'})
        
        @self.socketio.on('webrtc_toggle_video')
        def handle_toggle_video(data):
            """Handle video toggle"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                video_enabled = data.get('video_enabled', False)
                
                # Update participant media settings
                result = webrtc_manager.update_participant_media(
                    call_id, current_user.id, {'video_enabled': video_enabled}
                )
                
                if result['success']:
                    # Notify other participants
                    emit('webrtc_video_toggled', {
                        'user_id': current_user.id,
                        'video_enabled': video_enabled
                    }, room=f"call_{call_id}", include_self=False)
                    
                    emit('webrtc_media_updated', result)
                else:
                    emit('webrtc_error', {'error': result['error']})
                
            except Exception as e:
                logger.error(f"Error toggling video: {str(e)}")
                emit('webrtc_error', {'error': 'Failed to toggle video'})
        
        @self.socketio.on('webrtc_toggle_screen_share')
        def handle_toggle_screen_share(data):
            """Handle screen share toggle"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                screen_share_enabled = data.get('screen_share_enabled', False)
                
                # Update participant media settings
                result = webrtc_manager.update_participant_media(
                    call_id, current_user.id, {'screen_share_enabled': screen_share_enabled}
                )
                
                if result['success']:
                    # Notify other participants
                    emit('webrtc_screen_share_toggled', {
                        'user_id': current_user.id,
                        'screen_share_enabled': screen_share_enabled
                    }, room=f"call_{call_id}", include_self=False)
                    
                    emit('webrtc_media_updated', result)
                else:
                    emit('webrtc_error', {'error': result['error']})
                
            except Exception as e:
                logger.error(f"Error toggling screen share: {str(e)}")
                emit('webrtc_error', {'error': 'Failed to toggle screen share'})
        
        # Call Events
        @self.socketio.on('webrtc_call_invitation')
        def handle_call_invitation(data):
            """Handle incoming call invitation notifications"""
            try:
                if not current_user.is_authenticated:
                    return
                
                # This is typically called from the backend to notify users
                # of incoming call invitations
                target_user_id = data.get('target_user_id')
                call_info = data.get('call_info')
                invitation_info = data.get('invitation_info')
                
                # Send invitation to target user
                emit('webrtc_incoming_call', {
                    'call_info': call_info,
                    'invitation_info': invitation_info
                }, room=f"user_{target_user_id}")
                
            except Exception as e:
                logger.error(f"Error handling call invitation: {str(e)}")
        
        @self.socketio.on('webrtc_connection_quality')
        def handle_connection_quality(data):
            """Handle connection quality updates"""
            try:
                if not current_user.is_authenticated:
                    return
                
                call_id = data.get('call_id')
                quality = data.get('quality', 'good')  # good, fair, poor
                stats = data.get('stats', {})
                
                # Update participant connection quality
                call = webrtc_manager.get_call_by_id(call_id)
                if call:
                    participant = call.participants.filter_by(user_id=current_user.id).first()
                    if participant:
                        participant.connection_quality = quality
                        from database import db
                        db.session.commit()
                
                # Optionally broadcast quality info to moderators
                emit('webrtc_quality_update', {
                    'user_id': current_user.id,
                    'quality': quality,
                    'stats': stats
                }, room=f"call_{call_id}_moderators")
                
            except Exception as e:
                logger.error(f"Error handling connection quality: {str(e)}")
        
        # Disconnection Events
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle user disconnection"""
            try:
                if not current_user.is_authenticated:
                    return
                
                # Clean up user session
                if current_user.id in self.user_sessions:
                    session_info = self.user_sessions[current_user.id]
                    call_id = session_info.get('call_id')
                    
                    if call_id:
                        # Leave call room
                        leave_room(f"call_{call_id}")
                        
                        # Update tracking
                        if call_id in self.call_rooms:
                            self.call_rooms[call_id].discard(current_user.id)
                            if not self.call_rooms[call_id]:
                                del self.call_rooms[call_id]
                        
                        # Notify others
                        emit('webrtc_user_disconnected', {
                            'user_id': current_user.id,
                            'username': current_user.username
                        }, room=f"call_{call_id}")
                        
                        # Update participant status in database
                        webrtc_manager.leave_call(call_id, current_user.id, 'disconnected')
                    
                    del self.user_sessions[current_user.id]
                
                logger.info(f"User {current_user.id} disconnected from WebRTC")
                
            except Exception as e:
                logger.error(f"Error handling disconnect: {str(e)}")
    
    def send_call_invitation_notification(self, call_id, target_user_id, invitation_data):
        """Send call invitation notification to specific user"""
        try:
            self.socketio.emit('webrtc_incoming_call', {
                'call_id': call_id,
                'invitation_data': invitation_data
            }, room=f"user_{target_user_id}")
            
        except Exception as e:
            logger.error(f"Error sending call invitation notification: {str(e)}")
    
    def broadcast_call_event(self, call_id, event_type, event_data):
        """Broadcast call event to all participants"""
        try:
            self.socketio.emit('webrtc_call_event', {
                'event_type': event_type,
                'event_data': event_data,
                'timestamp': datetime.utcnow().isoformat()
            }, room=f"call_{call_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting call event: {str(e)}")
    
    def get_call_participants(self, call_id):
        """Get active participants in a call room"""
        return list(self.call_rooms.get(call_id, set()))
    
    def is_user_in_call(self, user_id):
        """Check if user is currently in any call room"""
        return user_id in self.user_sessions

# Global WebRTC WebSocket handler instance
webrtc_ws_handler = None

def register_webrtc_websocket_handlers(socketio):
    """Register WebRTC WebSocket handlers with SocketIO"""
    global webrtc_ws_handler
    
    try:
        webrtc_ws_handler = WebRTCWebSocketHandler(socketio)
        webrtc_ws_handler.register_handlers()
        
        logger.info("WebRTC WebSocket handlers registered successfully")
        return webrtc_ws_handler
        
    except Exception as e:
        logger.error(f"Failed to register WebRTC WebSocket handlers: {str(e)}")
        return None

def get_webrtc_handler():
    """Get the global WebRTC WebSocket handler instance"""
    return webrtc_ws_handler
