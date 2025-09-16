"""
WebRTC Routes and API Endpoints for EVENTSYNC
Provides REST API for video/audio calling functionality
"""

import logging
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime
from webrtc_manager import webrtc_manager
from models_webrtc import CallType, CallStatus, ParticipantStatus

logger = logging.getLogger(__name__)

# Create Blueprint
webrtc_bp = Blueprint('webrtc', __name__, url_prefix='/api/webrtc')

# Call Management Endpoints

@webrtc_bp.route('/calls/initiate', methods=['POST'])
@login_required
def initiate_call():
    """Initiate a new video or audio call"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('call_type'):
            return jsonify({'error': 'Call type is required'}), 400
        
        # Parse call type
        call_type = CallType(data['call_type'])
        target_user_ids = data.get('target_user_ids', [])
        
        # Call settings
        call_settings = {
            'max_participants': data.get('max_participants', 50),
            'is_recording_enabled': data.get('is_recording_enabled', False),
            'is_screen_share_enabled': data.get('is_screen_share_enabled', True),
            'require_moderator_approval': data.get('require_moderator_approval', False)
        }
        
        # Initiate call
        call = webrtc_manager.initiate_call(
            initiator_id=current_user.id,
            call_type=call_type,
            target_user_ids=target_user_ids,
            event_id=data.get('event_id'),
            chat_room_id=data.get('chat_room_id'),
            title=data.get('title'),
            description=data.get('description'),
            call_settings=call_settings
        )
        
        return jsonify({
            'success': True,
            'call': call.to_dict(),
            'message': 'Call initiated successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error initiating call: {str(e)}")
        return jsonify({'error': 'Failed to initiate call'}), 500

@webrtc_bp.route('/calls/<call_id>/join', methods=['POST'])
@login_required
def join_call(call_id):
    """Join an existing call"""
    try:
        data = request.get_json() or {}
        peer_id = data.get('peer_id')
        
        result = webrtc_manager.join_call(call_id, current_user.id, peer_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error joining call {call_id}: {str(e)}")
        return jsonify({'error': 'Failed to join call'}), 500

@webrtc_bp.route('/calls/<call_id>/leave', methods=['POST'])
@login_required
def leave_call(call_id):
    """Leave a call"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'user_left')
        
        result = webrtc_manager.leave_call(call_id, current_user.id, reason)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Error leaving call {call_id}: {str(e)}")
        return jsonify({'error': 'Failed to leave call'}), 500

@webrtc_bp.route('/calls/<call_id>/end', methods=['POST'])
@login_required
def end_call(call_id):
    """End a call (moderator only)"""
    try:
        call = webrtc_manager.get_call_by_id(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if user is moderator or call initiator
        participant = call.participants.filter_by(user_id=current_user.id).first()
        if not participant or (not participant.is_moderator and call.initiated_by != current_user.id):
            return jsonify({'error': 'Not authorized to end call'}), 403
        
        from models_webrtc import CallEndReason
        result = webrtc_manager.end_call(call_id, current_user.id, CallEndReason.MODERATOR_ENDED)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Error ending call {call_id}: {str(e)}")
        return jsonify({'error': 'Failed to end call'}), 500

@webrtc_bp.route('/calls/<call_id>', methods=['GET'])
@login_required
def get_call_info(call_id):
    """Get call information"""
    try:
        call = webrtc_manager.get_call_by_id(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if user is participant
        if not call.is_user_participant(current_user.id):
            return jsonify({'error': 'Not authorized to view call'}), 403
        
        return jsonify({
            'call': call.to_dict(),
            'participants': [p.to_dict() for p in call.participants.all()]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting call info {call_id}: {str(e)}")
        return jsonify({'error': 'Failed to get call info'}), 500

# Participant Management

@webrtc_bp.route('/calls/<call_id>/participants/<int:user_id>/media', methods=['PUT'])
@login_required
def update_participant_media(call_id, user_id):
    """Update participant media settings"""
    try:
        # Only allow users to update their own media settings
        if user_id != current_user.id:
            return jsonify({'error': 'Can only update your own media settings'}), 403
        
        data = request.get_json()
        media_settings = {
            'audio_enabled': data.get('audio_enabled'),
            'video_enabled': data.get('video_enabled'),
            'screen_share_enabled': data.get('screen_share_enabled')
        }
        
        # Remove None values
        media_settings = {k: v for k, v in media_settings.items() if v is not None}
        
        result = webrtc_manager.update_participant_media(call_id, user_id, media_settings)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Error updating participant media: {str(e)}")
        return jsonify({'error': 'Failed to update media settings'}), 500

@webrtc_bp.route('/calls/<call_id>/participants', methods=['GET'])
@login_required
def get_call_participants(call_id):
    """Get call participants"""
    try:
        call = webrtc_manager.get_call_by_id(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if user is participant
        if not call.is_user_participant(current_user.id):
            return jsonify({'error': 'Not authorized'}), 403
        
        participants = [p.to_dict() for p in call.participants.all()]
        
        return jsonify({
            'participants': participants,
            'total_count': len(participants),
            'active_count': call.get_active_participant_count()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting participants: {str(e)}")
        return jsonify({'error': 'Failed to get participants'}), 500

# Call Invitations

@webrtc_bp.route('/calls/<call_id>/invite', methods=['POST'])
@login_required
def invite_to_call(call_id):
    """Invite users to a call"""
    try:
        call = webrtc_manager.get_call_by_id(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if user is moderator or initiator
        participant = call.participants.filter_by(user_id=current_user.id).first()
        if not participant or (not participant.is_moderator and call.initiated_by != current_user.id):
            return jsonify({'error': 'Not authorized to invite'}), 403
        
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        message = data.get('message')
        
        invitations = []
        for user_id in user_ids:
            # Check if user is already in call
            if call.is_user_participant(user_id):
                continue
                
            # Add participant and send invitation
            webrtc_manager.add_participant(call.id, user_id)
            invitation = webrtc_manager.send_call_invitation(
                call.id, user_id, current_user.id, message
            )
            invitations.append(invitation.to_dict())
        
        from database import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'invitations': invitations,
            'message': f'Sent {len(invitations)} invitations'
        }), 200
        
    except Exception as e:
        logger.error(f"Error inviting to call: {str(e)}")
        return jsonify({'error': 'Failed to send invitations'}), 500

@webrtc_bp.route('/invitations/<int:invitation_id>/respond', methods=['POST'])
@login_required
def respond_to_call_invitation(invitation_id):
    """Respond to a call invitation"""
    try:
        data = request.get_json()
        response = data.get('response')  # 'accepted' or 'declined'
        
        if response not in ['accepted', 'declined']:
            return jsonify({'error': 'Invalid response'}), 400
        
        result = webrtc_manager.respond_to_invitation(
            invitation_id, current_user.id, response
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Error responding to invitation: {str(e)}")
        return jsonify({'error': 'Failed to respond to invitation'}), 500

@webrtc_bp.route('/invitations/pending', methods=['GET'])
@login_required
def get_pending_invitations():
    """Get user's pending call invitations"""
    try:
        from models_webrtc import CallInvitation
        
        invitations = CallInvitation.query.filter_by(
            invited_user_id=current_user.id,
            response=None
        ).filter(
            CallInvitation.expires_at > datetime.utcnow()
        ).all()
        
        return jsonify({
            'invitations': [inv.to_dict() for inv in invitations]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pending invitations: {str(e)}")
        return jsonify({'error': 'Failed to get invitations'}), 500

# Call History and Analytics

@webrtc_bp.route('/calls/history', methods=['GET'])
@login_required
def get_call_history():
    """Get user's call history"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        call_type = request.args.get('call_type')
        
        call_type_enum = None
        if call_type:
            try:
                call_type_enum = CallType(call_type)
            except ValueError:
                return jsonify({'error': 'Invalid call type'}), 400
        
        history = webrtc_manager.get_call_history(
            current_user.id, limit, call_type_enum
        )
        
        return jsonify({
            'calls': history,
            'total': len(history)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting call history: {str(e)}")
        return jsonify({'error': 'Failed to get call history'}), 500

@webrtc_bp.route('/calls/active', methods=['GET'])
@login_required
def get_active_calls():
    """Get user's active calls"""
    try:
        active_calls = webrtc_manager.get_active_calls_for_user(current_user.id)
        
        return jsonify({
            'calls': active_calls,
            'total': len(active_calls)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting active calls: {str(e)}")
        return jsonify({'error': 'Failed to get active calls'}), 500

@webrtc_bp.route('/calls/<call_id>/analytics', methods=['GET'])
@login_required
def get_call_analytics(call_id):
    """Get call analytics (moderator/initiator only)"""
    try:
        call = webrtc_manager.get_call_by_id(call_id)
        if not call:
            return jsonify({'error': 'Call not found'}), 404
        
        # Check if user is moderator or initiator
        participant = call.participants.filter_by(user_id=current_user.id).first()
        if not participant or (not participant.is_moderator and call.initiated_by != current_user.id):
            return jsonify({'error': 'Not authorized to view analytics'}), 403
        
        analytics = webrtc_manager.get_call_analytics(call_id)
        
        return jsonify(analytics), 200
        
    except Exception as e:
        logger.error(f"Error getting call analytics: {str(e)}")
        return jsonify({'error': 'Failed to get analytics'}), 500

# Status and Utility Endpoints

@webrtc_bp.route('/status', methods=['GET'])
@login_required
def get_user_call_status():
    """Get user's current call status"""
    try:
        is_in_call = webrtc_manager.is_user_in_call(current_user.id)
        active_calls = webrtc_manager.get_active_calls_for_user(current_user.id)
        
        return jsonify({
            'is_in_call': is_in_call,
            'active_calls_count': len(active_calls),
            'active_calls': active_calls
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting call status: {str(e)}")
        return jsonify({'error': 'Failed to get call status'}), 500

@webrtc_bp.route('/ice-servers', methods=['GET'])
@login_required
def get_ice_servers():
    """Get ICE servers for WebRTC connection"""
    return jsonify({
        'ice_servers': webrtc_manager.ice_servers
    }), 200

# Quick Call Endpoints (for direct user-to-user calls)

@webrtc_bp.route('/quick-call/audio/<int:target_user_id>', methods=['POST'])
@login_required
def initiate_quick_audio_call(target_user_id):
    """Initiate a quick audio call to another user"""
    try:
        if target_user_id == current_user.id:
            return jsonify({'error': 'Cannot call yourself'}), 400
        
        call = webrtc_manager.initiate_call(
            initiator_id=current_user.id,
            call_type=CallType.AUDIO,
            target_user_ids=[target_user_id],
            title=f"Audio call with {current_user.username}"
        )
        
        return jsonify({
            'success': True,
            'call': call.to_dict(),
            'message': 'Audio call initiated'
        }), 201
        
    except Exception as e:
        logger.error(f"Error initiating quick audio call: {str(e)}")
        return jsonify({'error': 'Failed to initiate call'}), 500

@webrtc_bp.route('/quick-call/video/<int:target_user_id>', methods=['POST'])
@login_required
def initiate_quick_video_call(target_user_id):
    """Initiate a quick video call to another user"""
    try:
        if target_user_id == current_user.id:
            return jsonify({'error': 'Cannot call yourself'}), 400
        
        call = webrtc_manager.initiate_call(
            initiator_id=current_user.id,
            call_type=CallType.VIDEO,
            target_user_ids=[target_user_id],
            title=f"Video call with {current_user.username}"
        )
        
        return jsonify({
            'success': True,
            'call': call.to_dict(),
            'message': 'Video call initiated'
        }), 201
        
    except Exception as e:
        logger.error(f"Error initiating quick video call: {str(e)}")
        return jsonify({'error': 'Failed to initiate call'}), 500

# Error Handlers

@webrtc_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@webrtc_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed'}), 405

@webrtc_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize WebRTC cleanup scheduler
def init_webrtc_cleanup(app):
    """Initialize WebRTC cleanup tasks"""
    import atexit
    import threading
    import time
    
    def cleanup_task(app):
        """Background task for cleaning up expired calls"""
        with app.app_context():
            while True:
                try:
                    webrtc_manager.cleanup_expired_calls()
                    time.sleep(300)  # Run every 5 minutes
                except Exception as e:
                    logger.error(f"Cleanup task error: {str(e)}")
                    time.sleep(60)  # Wait 1 minute before retry
    
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_task, args=(app,), daemon=True)
    cleanup_thread.start()
    logger.info("WebRTC cleanup task started")
    
    # Cleanup on exit
    atexit.register(lambda: logger.info("WebRTC cleanup completed"))

# Register the blueprint initialization
def register_webrtc_routes(app):
    """Register WebRTC routes with the Flask app"""
    app.register_blueprint(webrtc_bp)
    init_webrtc_cleanup(app)
    logger.info("WebRTC routes registered successfully")
