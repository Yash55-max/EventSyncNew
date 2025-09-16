"""
WebRTC Call Manager for EVENTSYNC
Handles call initiation, participant management, signaling, and call state management
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from database import db
from models_webrtc import (
    Call, CallParticipant, CallEvent, CallRecording, CallInvitation,
    CallType, CallStatus, ParticipantStatus, CallEndReason
)

logger = logging.getLogger(__name__)

class WebRTCCallManager:
    """Comprehensive WebRTC call management system"""
    
    def __init__(self):
        self.active_calls = {}  # In-memory cache for active calls
        self.ice_servers = [
            {'urls': 'stun:stun.l.google.com:19302'},
            {'urls': 'stun:stun1.l.google.com:19302'},
            {'urls': 'stun:stun2.l.google.com:19302'},
            # Add TURN servers for production
            # {'urls': 'turn:your-turn-server.com', 'username': 'user', 'credential': 'pass'}
        ]
    
    # Call Creation and Management
    def initiate_call(self, initiator_id: int, call_type: CallType, 
                     target_user_ids: List[int] = None, 
                     event_id: int = None, chat_room_id: int = None,
                     title: str = None, description: str = None,
                     call_settings: Dict = None) -> Call:
        """Initiate a new call"""
        try:
            # Generate unique call ID
            call_id = f"call_{uuid.uuid4().hex[:12]}"
            
            # Default settings
            settings = call_settings or {}
            
            # Create call record
            call = Call(
                call_id=call_id,
                call_type=call_type,
                title=title,
                description=description,
                initiated_by=initiator_id,
                event_id=event_id,
                chat_room_id=chat_room_id,
                is_group_call=len(target_user_ids or []) > 1,
                max_participants=settings.get('max_participants', 50),
                is_recording_enabled=settings.get('is_recording_enabled', False),
                is_screen_share_enabled=settings.get('is_screen_share_enabled', True),
                require_moderator_approval=settings.get('require_moderator_approval', False),
                ice_servers=self.ice_servers,
                status=CallStatus.INITIATED
            )
            
            db.session.add(call)
            db.session.flush()  # Get the call ID
            
            # Add initiator as first participant and moderator
            self.add_participant(call.id, initiator_id, is_moderator=True)
            
            # Add target participants if specified
            if target_user_ids:
                for user_id in target_user_ids:
                    if user_id != initiator_id:  # Don't add initiator twice
                        self.add_participant(call.id, user_id)
                        self.send_call_invitation(call.id, user_id, initiator_id)
            
            # Log call initiation
            self.log_call_event(call.id, initiator_id, 'call_initiated', {
                'call_type': call_type.value,
                'target_users': target_user_ids or [],
                'is_group_call': call.is_group_call
            })
            
            db.session.commit()
            
            # Cache active call
            self.active_calls[call_id] = {
                'call': call,
                'participants': {},
                'signaling_queue': [],
                'created_at': datetime.utcnow()
            }
            
            logger.info(f"Call initiated: {call_id} by user {initiator_id}")
            return call
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to initiate call: {str(e)}")
            raise
    
    def join_call(self, call_id: str, user_id: int, peer_id: str = None) -> Dict:
        """Join an existing call"""
        try:
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                raise ValueError("Call not found")
            
            if not call.can_user_join(user_id):
                raise ValueError("Cannot join call - call full or ended")
            
            # Get or create participant
            participant = call.participants.filter_by(user_id=user_id).first()
            if not participant:
                participant = self.add_participant(call.id, user_id)
            
            # Update participant status
            participant.status = ParticipantStatus.CONNECTING
            participant.peer_id = peer_id or f"peer_{uuid.uuid4().hex[:8]}"
            participant.joined_at = datetime.utcnow()
            
            # Update call status if first join
            if call.status == CallStatus.INITIATED:
                call.status = CallStatus.CONNECTING
                call.started_at = datetime.utcnow()
            
            # Log join event
            self.log_call_event(call.id, user_id, 'user_joining', {
                'peer_id': participant.peer_id
            })
            
            db.session.commit()
            
            # Update active call cache
            if call_id in self.active_calls:
                self.active_calls[call_id]['participants'][user_id] = {
                    'participant': participant,
                    'peer_id': participant.peer_id,
                    'joined_at': datetime.utcnow()
                }
            
            return {
                'success': True,
                'call': call.to_dict(),
                'participant': participant.to_dict(),
                'ice_servers': self.ice_servers,
                'existing_participants': [p.to_dict() for p in call.get_active_participants()]
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to join call {call_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def leave_call(self, call_id: str, user_id: int, reason: str = 'user_left') -> Dict:
        """Leave a call"""
        try:
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                return {'success': False, 'error': 'Call not found'}
            
            participant = call.participants.filter_by(user_id=user_id).first()
            if not participant:
                return {'success': False, 'error': 'Not a participant'}
            
            # Update participant status
            participant.status = ParticipantStatus.LEFT
            participant.left_at = datetime.utcnow()
            
            # Log leave event
            self.log_call_event(call.id, user_id, 'user_left', {
                'reason': reason,
                'duration': participant.get_duration_in_call()
            })
            
            # Check if call should end
            active_participants = call.get_active_participants()
            if len(active_participants) <= 1:
                self.end_call(call_id, reason='no_participants')
            
            # Update active call cache
            if call_id in self.active_calls and user_id in self.active_calls[call_id]['participants']:
                del self.active_calls[call_id]['participants'][user_id]
            
            db.session.commit()
            
            return {
                'success': True,
                'remaining_participants': len(active_participants) - 1
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to leave call {call_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def end_call(self, call_id: str, ended_by: int = None, 
                 reason: CallEndReason = CallEndReason.NORMAL) -> Dict:
        """End a call"""
        try:
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                return {'success': False, 'error': 'Call not found'}
            
            # Update call status
            call.status = CallStatus.ENDED
            call.ended_at = datetime.utcnow()
            call.end_reason = reason
            call.calculate_duration()
            
            # Update all active participants
            active_participants = call.get_active_participants()
            for participant in active_participants:
                participant.status = ParticipantStatus.LEFT
                participant.left_at = datetime.utcnow()
            
            # Log end event
            self.log_call_event(call.id, ended_by, 'call_ended', {
                'reason': reason.value,
                'duration': call.duration_seconds,
                'participant_count': len(active_participants)
            })
            
            # Remove from active calls cache
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            
            db.session.commit()
            
            return {
                'success': True,
                'call_duration': call.duration_seconds,
                'participants_notified': len(active_participants)
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to end call {call_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Participant Management
    def add_participant(self, call_id: int, user_id: int, 
                       is_moderator: bool = False, 
                       is_presenter: bool = False) -> CallParticipant:
        """Add a participant to a call"""
        participant = CallParticipant(
            call_id=call_id,
            user_id=user_id,
            status=ParticipantStatus.INVITED,
            is_moderator=is_moderator,
            is_presenter=is_presenter
        )
        
        db.session.add(participant)
        return participant
    
    def update_participant_media(self, call_id: str, user_id: int, 
                                media_settings: Dict) -> Dict:
        """Update participant's media settings"""
        try:
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                return {'success': False, 'error': 'Call not found'}
            
            participant = call.participants.filter_by(user_id=user_id).first()
            if not participant:
                return {'success': False, 'error': 'Participant not found'}
            
            # Update media settings
            if 'audio_enabled' in media_settings:
                participant.audio_enabled = media_settings['audio_enabled']
            if 'video_enabled' in media_settings:
                participant.video_enabled = media_settings['video_enabled']
            if 'screen_share_enabled' in media_settings:
                participant.screen_share_enabled = media_settings['screen_share_enabled']
            
            # Log media change
            self.log_call_event(call.id, user_id, 'media_changed', media_settings)
            
            db.session.commit()
            
            return {
                'success': True,
                'participant': participant.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    # Signaling Management
    def handle_webrtc_signal(self, call_id: str, from_user_id: int, 
                            to_user_id: int, signal_type: str, 
                            signal_data: Dict) -> Dict:
        """Handle WebRTC signaling between participants"""
        try:
            call = Call.query.filter_by(call_id=call_id).first()
            if not call:
                return {'success': False, 'error': 'Call not found'}
            
            # Validate participants
            from_participant = call.participants.filter_by(user_id=from_user_id).first()
            to_participant = call.participants.filter_by(user_id=to_user_id).first() if to_user_id else None
            
            if not from_participant:
                return {'success': False, 'error': 'Sender not in call'}
            
            # Store signaling data
            signaling_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'from_user_id': from_user_id,
                'to_user_id': to_user_id,
                'signal_type': signal_type,
                'signal_data': signal_data
            }
            
            # Add to active call signaling queue
            if call_id in self.active_calls:
                self.active_calls[call_id]['signaling_queue'].append(signaling_entry)
                
                # Keep only last 100 signaling messages
                if len(self.active_calls[call_id]['signaling_queue']) > 100:
                    self.active_calls[call_id]['signaling_queue'] = \
                        self.active_calls[call_id]['signaling_queue'][-100:]
            
            return {
                'success': True,
                'signaling_entry': signaling_entry
            }
            
        except Exception as e:
            logger.error(f"WebRTC signaling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Call Invitations
    def send_call_invitation(self, call_id: int, invited_user_id: int, 
                           invited_by: int, message: str = None,
                           expires_in_minutes: int = 5) -> CallInvitation:
        """Send a call invitation"""
        invitation = CallInvitation(
            call_id=call_id,
            invited_user_id=invited_user_id,
            invited_by=invited_by,
            invitation_message=message,
            expires_at=datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        )
        
        db.session.add(invitation)
        return invitation
    
    def respond_to_invitation(self, invitation_id: int, user_id: int, 
                            response: str) -> Dict:
        """Respond to a call invitation"""
        try:
            invitation = CallInvitation.query.get(invitation_id)
            if not invitation:
                return {'success': False, 'error': 'Invitation not found'}
            
            if invitation.invited_user_id != user_id:
                return {'success': False, 'error': 'Not your invitation'}
            
            if invitation.is_expired():
                return {'success': False, 'error': 'Invitation expired'}
            
            invitation.response = response
            invitation.responded_at = datetime.utcnow()
            
            # If accepted, allow user to join call
            if response == 'accepted':
                call = invitation.call
                if call.status in [CallStatus.INITIATED, CallStatus.RINGING, CallStatus.CONNECTED]:
                    result = self.join_call(call.call_id, user_id)
                    if result['success']:
                        db.session.commit()
                        return {
                            'success': True,
                            'action': 'joined_call',
                            'call': result['call']
                        }
                else:
                    db.session.commit()
                    return {'success': False, 'error': 'Call no longer active'}
            
            db.session.commit()
            return {
                'success': True,
                'action': response,
                'invitation': invitation.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    # Call History and Analytics
    def get_call_history(self, user_id: int, limit: int = 50, 
                        call_type: CallType = None) -> List[Dict]:
        """Get user's call history"""
        query = Call.query.join(CallParticipant).filter(
            CallParticipant.user_id == user_id
        )
        
        if call_type:
            query = query.filter(Call.call_type == call_type)
        
        calls = query.order_by(Call.created_at.desc()).limit(limit).all()
        
        return [call.to_dict() for call in calls]
    
    def get_active_calls_for_user(self, user_id: int) -> List[Dict]:
        """Get user's currently active calls"""
        calls = Call.query.join(CallParticipant).filter(
            CallParticipant.user_id == user_id,
            CallParticipant.status.in_([ParticipantStatus.CONNECTING, ParticipantStatus.CONNECTED]),
            Call.status.in_([CallStatus.INITIATED, CallStatus.RINGING, CallStatus.CONNECTED])
        ).all()
        
        return [call.to_dict() for call in calls]
    
    def get_call_analytics(self, call_id: str) -> Dict:
        """Get detailed analytics for a call"""
        call = Call.query.filter_by(call_id=call_id).first()
        if not call:
            return {'error': 'Call not found'}
        
        participants = call.participants.all()
        events = call.events.order_by(CallEvent.timestamp).all()
        
        analytics = {
            'call_info': call.to_dict(),
            'participant_summary': {
                'total_invited': len(participants),
                'total_joined': len([p for p in participants if p.joined_at]),
                'average_duration': sum(p.get_duration_in_call() for p in participants) / len(participants) if participants else 0,
                'participants': [p.to_dict() for p in participants]
            },
            'timeline': [
                {
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type,
                    'user_id': event.user_id,
                    'data': event.event_data
                } for event in events
            ]
        }
        
        return analytics
    
    # Utility Methods
    def log_call_event(self, call_id: int, user_id: int, event_type: str, 
                      event_data: Dict = None):
        """Log a call event"""
        event = CallEvent(
            call_id=call_id,
            user_id=user_id,
            event_type=event_type,
            event_data=event_data or {}
        )
        db.session.add(event)
    
    def cleanup_expired_calls(self):
        """Clean up expired and stale calls"""
        try:
            # Find calls that have been inactive for too long
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            
            stale_calls = Call.query.filter(
                Call.status.in_([CallStatus.INITIATED, CallStatus.RINGING]),
                Call.created_at < cutoff_time
            ).all()
            
            for call in stale_calls:
                self.end_call(call.call_id, reason=CallEndReason.TIMEOUT)
            
            # Clean up expired invitations
            expired_invitations = CallInvitation.query.filter(
                CallInvitation.expires_at < datetime.utcnow(),
                CallInvitation.response.is_(None)
            ).all()
            
            for invitation in expired_invitations:
                invitation.response = 'expired'
            
            db.session.commit()
            
            logger.info(f"Cleaned up {len(stale_calls)} stale calls and {len(expired_invitations)} expired invitations")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_call_by_id(self, call_id: str) -> Optional[Call]:
        """Get call by ID"""
        return Call.query.filter_by(call_id=call_id).first()
    
    def is_user_in_call(self, user_id: int) -> bool:
        """Check if user is currently in any call"""
        active_calls = self.get_active_calls_for_user(user_id)
        return len(active_calls) > 0

# Global instance
webrtc_manager = WebRTCCallManager()