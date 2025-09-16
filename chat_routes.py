"""
Chat API Routes for EventHub
Provides REST endpoints for chat functionality
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app, send_file, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from chat_manager import get_chat_manager
from models_chat import ChatRoom, ChatRoomType, MessageType, UserStatus
from models import Event

logger = logging.getLogger(__name__)

# Create blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/rooms', methods=['GET'])
@login_required
def get_user_rooms():
    """Get all chat rooms user is participating in"""
    try:
        chat_manager = get_chat_manager()
        rooms = chat_manager.get_user_rooms(current_user.id)
        
        return jsonify({
            'success': True,
            'rooms': rooms
        })
        
    except Exception as e:
        logger.error(f"Error getting user rooms: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get rooms'
        }), 500

@chat_bp.route('/rooms', methods=['POST'])
@login_required
def create_room():
    """Create a new chat room"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        room_type = data.get('room_type', 'general')
        event_id = data.get('event_id')
        is_public = data.get('is_public', True)
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Room name is required'
            }), 400
        
        # Validate room type
        try:
            room_type_enum = ChatRoomType(room_type)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid room type'
            }), 400
        
        # Validate event if specified
        if event_id:
            event = Event.query.get(event_id)
            if not event:
                return jsonify({
                    'success': False,
                    'error': 'Event not found'
                }), 404
            
            # Check if user can create room for this event
            if not (current_user.is_organizer() or event.organizer_id == current_user.id):
                return jsonify({
                    'success': False,
                    'error': 'Permission denied'
                }), 403
        
        settings = {
            'is_public': is_public,
            'allow_file_sharing': data.get('allow_file_sharing', True),
            'allow_voice_messages': data.get('allow_voice_messages', True),
            'is_moderated': data.get('is_moderated', False)
        }
        
        chat_manager = get_chat_manager()
        result = chat_manager.create_room(
            name=name,
            creator_id=current_user.id,
            room_type=room_type_enum,
            description=description,
            event_id=event_id,
            settings=settings
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to create room'
        }), 500

@chat_bp.route('/test-create', methods=['POST'])
@login_required
def test_create_room():
    """Test room creation endpoint"""
    try:
        chat_manager = get_chat_manager()
        result = chat_manager.create_room(
            name=f"Test Room {current_user.username}",
            creator_id=current_user.id,
            room_type=ChatRoomType.GENERAL,
            description="Test room for debugging",
            event_id=None,
            settings={'is_public': True}
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Test room creation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@chat_bp.route('/rooms/<int:room_id>', methods=['GET'])
@login_required
def get_room_details(room_id):
    """Get room details"""
    try:
        chat_manager = get_chat_manager()
        room = chat_manager.get_room(room_id)
        
        if not room:
            return jsonify({
                'success': False,
                'error': 'Room not found'
            }), 404
        
        # Check if user is participant
        if not room.is_user_participant(current_user.id):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        participants = chat_manager.get_room_participants(room_id)
        
        return jsonify({
            'success': True,
            'room': room.to_dict(),
            'participants': participants,
            'is_moderator': room.is_user_moderator(current_user.id)
        })
        
    except Exception as e:
        logger.error(f"Error getting room details: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get room details'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/join', methods=['POST'])
@login_required
def join_room(room_id):
    """Join a chat room"""
    try:
        chat_manager = get_chat_manager()
        result = chat_manager.join_room(room_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to join room'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/leave', methods=['POST'])
@login_required
def leave_room(room_id):
    """Leave a chat room"""
    try:
        chat_manager = get_chat_manager()
        result = chat_manager.leave_room(room_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error leaving room: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to leave room'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@login_required
def get_messages(room_id):
    """Get messages from a chat room"""
    try:
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 messages
        before_id = request.args.get('before_id', type=int)
        
        chat_manager = get_chat_manager()
        messages = chat_manager.get_messages(room_id, current_user.id, limit, before_id)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'has_more': len(messages) == limit
        })
        
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get messages'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/messages', methods=['POST'])
@login_required
def send_message(room_id):
    """Send a message to a chat room"""
    try:
        data = request.get_json()
        
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        reply_to_id = data.get('reply_to_id')
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'Message content is required'
            }), 400
        
        # Validate message type
        try:
            message_type_enum = MessageType(message_type)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid message type'
            }), 400
        
        chat_manager = get_chat_manager()
        result = chat_manager.send_message(
            room_id=room_id,
            user_id=current_user.id,
            content=content,
            message_type=message_type_enum,
            reply_to_id=reply_to_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to send message'
        }), 500

@chat_bp.route('/messages/<int:message_id>/edit', methods=['PUT'])
@login_required
def edit_message(message_id):
    """Edit a message"""
    try:
        data = request.get_json()
        new_content = data.get('content', '').strip()
        
        if not new_content:
            return jsonify({
                'success': False,
                'error': 'Message content is required'
            }), 400
        
        chat_manager = get_chat_manager()
        result = chat_manager.edit_message(message_id, current_user.id, new_content)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to edit message'
        }), 500

@chat_bp.route('/messages/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    try:
        data = request.get_json() or {}
        room_id = data.get('room_id')
        
        # Check if user is moderator
        is_moderator = False
        if room_id:
            chat_manager = get_chat_manager()
            room = chat_manager.get_room(room_id)
            is_moderator = room and room.is_user_moderator(current_user.id)
        
        result = chat_manager.delete_message(message_id, current_user.id, is_moderator)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to delete message'
        }), 500

@chat_bp.route('/messages/<int:message_id>/react', methods=['POST'])
@login_required
def add_reaction(message_id):
    """Add reaction to a message"""
    try:
        data = request.get_json()
        emoji = data.get('emoji', '').strip()
        
        if not emoji:
            return jsonify({
                'success': False,
                'error': 'Emoji is required'
            }), 400
        
        chat_manager = get_chat_manager()
        result = chat_manager.add_reaction(message_id, current_user.id, emoji)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to add reaction'
        }), 500

@chat_bp.route('/messages/<int:message_id>/react', methods=['DELETE'])
@login_required
def remove_reaction(message_id):
    """Remove reaction from a message"""
    try:
        data = request.get_json()
        emoji = data.get('emoji', '').strip()
        
        if not emoji:
            return jsonify({
                'success': False,
                'error': 'Emoji is required'
            }), 400
        
        chat_manager = get_chat_manager()
        result = chat_manager.remove_reaction(message_id, current_user.id, emoji)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to remove reaction'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/upload', methods=['POST'])
@login_required
def upload_file(room_id):
    """Upload a file to chat"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        file = request.files['file']
        message_content = request.form.get('message', '')
        
        chat_manager = get_chat_manager()
        result = chat_manager.upload_file(file, room_id, current_user.id, message_content)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload file'
        }), 500

@chat_bp.route('/files/<file_id>/download')
@login_required
def download_file(file_id):
    """Download a chat file"""
    try:
        from models_chat import ChatFileShare
        
        # Try to get file by ID or stored filename
        if file_id.isdigit():
            file_share = ChatFileShare.query.get(int(file_id))
        else:
            file_share = ChatFileShare.query.filter_by(stored_filename=file_id).first()
        
        if not file_share:
            abort(404)
        
        # Check if file exists
        if not os.path.exists(file_share.file_path):
            abort(404)
        
        # Check if file is expired
        if file_share.is_expired():
            abort(410)  # Gone
        
        # Check access permissions (simplified - user must be in the room)
        room = file_share.room
        if not room.is_user_participant(current_user.id):
            abort(403)
        
        # Update download count
        file_share.download_count += 1
        from extensions import db
        db.session.commit()
        
        return send_file(
            file_share.file_path,
            as_attachment=True,
            download_name=file_share.original_filename,
            mimetype=file_share.mime_type
        )
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        abort(500)

@chat_bp.route('/files/<int:file_id>/thumbnail')
@login_required
def get_thumbnail(file_id):
    """Get thumbnail for image file"""
    try:
        from models_chat import ChatFileShare
        
        file_share = ChatFileShare.query.get(file_id)
        if not file_share:
            abort(404)
        
        if not file_share.is_image or not file_share.thumbnail_path:
            abort(404)
        
        if not os.path.exists(file_share.thumbnail_path):
            abort(404)
        
        # Check access permissions
        room = file_share.room
        if not room.is_user_participant(current_user.id):
            abort(403)
        
        return send_file(
            file_share.thumbnail_path,
            mimetype='image/jpeg'
        )
        
    except Exception as e:
        logger.error(f"Error getting thumbnail: {e}")
        abort(500)

@chat_bp.route('/presence', methods=['PUT'])
@login_required
def update_presence():
    """Update user presence"""
    try:
        data = request.get_json()
        
        status = data.get('status')
        custom_status = data.get('custom_status')
        room_id = data.get('room_id')
        
        # Validate status
        status_enum = None
        if status:
            try:
                status_enum = UserStatus(status)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid status'
                }), 400
        
        chat_manager = get_chat_manager()
        result = chat_manager.update_user_presence(
            user_id=current_user.id,
            status=status_enum,
            custom_status=custom_status,
            room_id=room_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error updating presence: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to update presence'
        }), 500

@chat_bp.route('/events/<int:event_id>/rooms', methods=['GET'])
@login_required
def get_event_rooms(event_id):
    """Get chat rooms for an event"""
    try:
        # Check if user has access to the event
        event = Event.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
        
        chat_manager = get_chat_manager()
        rooms = chat_manager.get_event_rooms(event_id)
        
        return jsonify({
            'success': True,
            'rooms': rooms
        })
        
    except Exception as e:
        logger.error(f"Error getting event rooms: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get event rooms'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/participants', methods=['GET'])
@login_required
def get_room_participants(room_id):
    """Get participants in a room"""
    try:
        chat_manager = get_chat_manager()
        room = chat_manager.get_room(room_id)
        
        if not room:
            return jsonify({
                'success': False,
                'error': 'Room not found'
            }), 404
        
        # Check if user is participant
        if not room.is_user_participant(current_user.id):
            return jsonify({
                'success': False,
                'error': 'Access denied'
            }), 403
        
        participants = chat_manager.get_room_participants(room_id)
        
        return jsonify({
            'success': True,
            'participants': participants
        })
        
    except Exception as e:
        logger.error(f"Error getting room participants: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to get participants'
        }), 500

# Moderation endpoints (for room moderators/admins)
@chat_bp.route('/rooms/<int:room_id>/mute', methods=['POST'])
@login_required
def mute_user(room_id):
    """Mute a user in a room"""
    try:
        data = request.get_json()
        target_user_id = data.get('user_id')
        duration_minutes = data.get('duration_minutes')
        reason = data.get('reason', '')
        
        if not target_user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Check if current user is moderator
        chat_manager = get_chat_manager()
        room = chat_manager.get_room(room_id)
        
        if not room or not room.is_user_moderator(current_user.id):
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        result = chat_manager.mute_user(
            room_id=room_id,
            user_id=target_user_id,
            moderator_id=current_user.id,
            duration_minutes=duration_minutes,
            reason=reason
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error muting user: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to mute user'
        }), 500

@chat_bp.route('/rooms/<int:room_id>/unmute', methods=['POST'])
@login_required
def unmute_user(room_id):
    """Unmute a user in a room"""
    try:
        data = request.get_json()
        target_user_id = data.get('user_id')
        
        if not target_user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Check if current user is moderator
        chat_manager = get_chat_manager()
        room = chat_manager.get_room(room_id)
        
        if not room or not room.is_user_moderator(current_user.id):
            return jsonify({
                'success': False,
                'error': 'Permission denied'
            }), 403
        
        result = chat_manager.unmute_user(room_id, target_user_id, current_user.id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error unmuting user: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to unmute user'
        }), 500