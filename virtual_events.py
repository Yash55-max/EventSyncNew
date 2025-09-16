"""
Virtual Events Engine for Revolutionary Event Management Platform
Supports VR/AR experiences, live streaming, interactive polls, and immersive environments
"""

import json
import uuid
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
from flask import current_app
import redis
from PIL import Image
import base64
from io import BytesIO

from app import db
from models import (
    Event, User, EventType, Badge, UserBadge, EventAnalytics,
    EventFeedback, SustainabilityMetric
)

logger = logging.getLogger(__name__)

class VirtualEnvironmentType(Enum):
    """Types of virtual environments supported"""
    CONFERENCE_HALL = "conference_hall"
    AUDITORIUM = "auditorium"
    EXHIBITION = "exhibition"
    NETWORKING_LOUNGE = "networking_lounge"
    HACKATHON_SPACE = "hackathon_space"
    VR_WORLD = "vr_world"
    AR_OVERLAY = "ar_overlay"
    HYBRID_SPACE = "hybrid_space"

class StreamQuality(Enum):
    """Live stream quality options"""
    LOW = "360p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "4K"

class PollType(Enum):
    """Interactive poll types"""
    MULTIPLE_CHOICE = "multiple_choice"
    RATING = "rating"
    WORD_CLOUD = "word_cloud"
    QUIZ = "quiz"
    LIVE_QA = "live_qa"

@dataclass
class VirtualEnvironment:
    """Virtual environment configuration"""
    environment_id: str
    name: str
    type: VirtualEnvironmentType
    capacity: int
    background_url: str
    assets: Dict[str, Any]
    interactive_elements: List[Dict]
    lighting_config: Dict[str, Any]
    audio_zones: List[Dict]

@dataclass
class StreamConfig:
    """Live streaming configuration"""
    stream_key: str
    rtmp_url: str
    quality: StreamQuality
    bitrate: int
    framerate: int
    audio_bitrate: int
    enable_chat: bool
    enable_screen_share: bool
    recording_enabled: bool

class VirtualEventsEngine:
    """
    Main engine for managing virtual events with immersive features
    """
    
    def __init__(self):
        self.redis_client = self.setup_redis()
        self.environments = self.load_default_environments()
        self.active_streams = {}
        self.active_polls = {}
        self.leaderboard_manager = LeaderboardManager()
        self.gamification_engine = GamificationEngine()
        self.vr_ar_manager = VRARManager()
        
    def setup_redis(self):
        """Setup Redis connection for real-time features"""
        try:
            redis_client = redis.Redis(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                db=int(os.environ.get('REDIS_DB', 1)),
                decode_responses=True
            )
            redis_client.ping()
            return redis_client
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return None
    
    def load_default_environments(self) -> Dict[str, VirtualEnvironment]:
        """Load default virtual environments"""
        environments = {}
        
        # Conference Hall Environment
        environments["conference_hall"] = VirtualEnvironment(
            environment_id="conference_hall",
            name="Modern Conference Hall",
            type=VirtualEnvironmentType.CONFERENCE_HALL,
            capacity=500,
            background_url="/static/environments/conference_hall.jpg",
            assets={
                "stage": {"position": [0, 0, -5], "scale": [10, 5, 2]},
                "seats": {"rows": 15, "seats_per_row": 20},
                "screens": [{"position": [-8, 3, -4], "size": [4, 3]}]
            },
            interactive_elements=[
                {"type": "applause_button", "position": [0, -2, 0]},
                {"type": "raise_hand", "position": [1, -2, 0]},
                {"type": "emoji_reactions", "position": [2, -2, 0]}
            ],
            lighting_config={
                "ambient": {"color": "#ffffff", "intensity": 0.3},
                "stage": {"color": "#ffdd00", "intensity": 0.8, "spotlight": True}
            },
            audio_zones=[
                {"name": "stage", "position": [0, 0, -5], "radius": 15},
                {"name": "audience", "position": [0, 0, 5], "radius": 20}
            ]
        )
        
        # VR World Environment
        environments["vr_world"] = VirtualEnvironment(
            environment_id="vr_world",
            name="Immersive VR Conference",
            type=VirtualEnvironmentType.VR_WORLD,
            capacity=100,
            background_url="/static/environments/vr_space.jpg",
            assets={
                "floating_stage": {"position": [0, 5, 0], "scale": [8, 1, 8]},
                "holograms": {"count": 5, "interactive": True},
                "portal_gates": [{"destination": "networking", "position": [10, 0, 0]}]
            },
            interactive_elements=[
                {"type": "3d_whiteboard", "position": [-5, 2, 0]},
                {"type": "holographic_display", "position": [5, 2, 0]},
                {"type": "virtual_booth", "position": [0, 0, 8]}
            ],
            lighting_config={
                "ambient": {"color": "#0066ff", "intensity": 0.5},
                "neon_accents": {"color": "#ff00ff", "intensity": 1.0}
            },
            audio_zones=[
                {"name": "center", "position": [0, 0, 0], "radius": 25, "3d_audio": True}
            ]
        )
        
        # Hackathon Space Environment
        environments["hackathon_space"] = VirtualEnvironment(
            environment_id="hackathon_space",
            name="Collaborative Hackathon Arena",
            type=VirtualEnvironmentType.HACKATHON_SPACE,
            capacity=200,
            background_url="/static/environments/hackathon_arena.jpg",
            assets={
                "team_pods": {"count": 20, "capacity": 5},
                "code_walls": {"count": 8, "interactive": True},
                "mentor_stations": {"count": 4}
            },
            interactive_elements=[
                {"type": "code_editor", "position": [0, 1, 0]},
                {"type": "timer_display", "position": [0, 4, 0]},
                {"type": "leaderboard", "position": [8, 2, 0]},
                {"type": "submission_portal", "position": [-8, 2, 0]}
            ],
            lighting_config={
                "ambient": {"color": "#ffffff", "intensity": 0.6},
                "team_areas": {"color": "#00ff00", "intensity": 0.4}
            },
            audio_zones=[
                {"name": "main_hall", "position": [0, 0, 0], "radius": 30},
                {"name": "quiet_zones", "positions": [[10, 0, 10], [-10, 0, 10]], "radius": 5}
            ]
        )
        
        return environments
    
    def create_virtual_event(self, event_id: int, environment_type: str, 
                           custom_config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a virtual event environment"""
        try:
            event = Event.query.get_or_404(event_id)
            
            if environment_type not in self.environments:
                return {"success": False, "error": "Invalid environment type"}
            
            base_env = self.environments[environment_type]
            virtual_event_id = f"ve_{event_id}_{uuid.uuid4().hex[:8]}"
            
            # Apply custom configuration if provided
            environment_config = self._apply_custom_config(base_env, custom_config or {})
            
            # Store virtual event configuration
            virtual_event_data = {
                "id": virtual_event_id,
                "event_id": event_id,
                "environment": environment_config.__dict__,
                "created_at": datetime.utcnow().isoformat(),
                "is_active": False,
                "participants": [],
                "interactive_state": {},
                "stream_config": None
            }
            
            if self.redis_client:
                self.redis_client.hset(
                    f"virtual_event:{virtual_event_id}",
                    mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                            for k, v in virtual_event_data.items()}
                )
            
            # Initialize gamification elements
            self.gamification_engine.initialize_event_gamification(virtual_event_id, event_id)
            
            logger.info(f"Created virtual event {virtual_event_id} for event {event_id}")
            
            return {
                "success": True,
                "virtual_event_id": virtual_event_id,
                "environment": environment_config.__dict__,
                "join_url": f"/virtual-events/{virtual_event_id}"
            }
            
        except Exception as e:
            logger.error(f"Error creating virtual event: {e}")
            return {"success": False, "error": str(e)}
    
    def setup_live_stream(self, virtual_event_id: str, stream_config: Dict) -> Dict[str, Any]:
        """Setup live streaming for virtual event"""
        try:
            if not self.redis_client:
                return {"success": False, "error": "Redis not available"}
            
            # Generate unique stream key
            stream_key = f"stream_{virtual_event_id}_{uuid.uuid4().hex[:12]}"
            
            # Configure streaming settings
            stream_settings = StreamConfig(
                stream_key=stream_key,
                rtmp_url=f"rtmp://stream.platform.com/live/{stream_key}",
                quality=StreamQuality(stream_config.get("quality", "1080p")),
                bitrate=stream_config.get("bitrate", 4000),
                framerate=stream_config.get("framerate", 30),
                audio_bitrate=stream_config.get("audio_bitrate", 128),
                enable_chat=stream_config.get("enable_chat", True),
                enable_screen_share=stream_config.get("enable_screen_share", True),
                recording_enabled=stream_config.get("recording", True)
            )
            
            # Store stream configuration
            self.redis_client.hset(
                f"virtual_event:{virtual_event_id}",
                "stream_config",
                json.dumps(stream_settings.__dict__)
            )
            
            self.active_streams[virtual_event_id] = stream_settings
            
            return {
                "success": True,
                "stream_key": stream_key,
                "rtmp_url": stream_settings.rtmp_url,
                "settings": stream_settings.__dict__
            }
            
        except Exception as e:
            logger.error(f"Error setting up live stream: {e}")
            return {"success": False, "error": str(e)}
    
    def join_virtual_event(self, virtual_event_id: str, user_id: int, 
                          device_info: Dict) -> Dict[str, Any]:
        """Join a user to virtual event"""
        try:
            if not self.redis_client:
                return {"success": False, "error": "Redis not available"}
            
            user = User.query.get_or_404(user_id)
            
            # Get virtual event data
            event_data = self.redis_client.hgetall(f"virtual_event:{virtual_event_id}")
            if not event_data:
                return {"success": False, "error": "Virtual event not found"}
            
            # Check capacity
            participants = json.loads(event_data.get("participants", "[]"))
            environment = json.loads(event_data.get("environment", "{}"))
            
            if len(participants) >= environment.get("capacity", 100):
                return {"success": False, "error": "Virtual event at capacity"}
            
            # Add user to participants
            participant_data = {
                "user_id": user_id,
                "username": user.username,
                "full_name": user.full_name,
                "joined_at": datetime.utcnow().isoformat(),
                "device_info": device_info,
                "position": [0, 0, 0],  # Initial position in 3D space
                "avatar_config": self._generate_default_avatar(user),
                "is_active": True,
                "capabilities": self._detect_device_capabilities(device_info)
            }
            
            participants.append(participant_data)
            
            # Update participants list
            self.redis_client.hset(
                f"virtual_event:{virtual_event_id}",
                "participants",
                json.dumps(participants)
            )
            
            # Initialize user state
            self.redis_client.hset(
                f"virtual_event:{virtual_event_id}:user:{user_id}",
                mapping={
                    "status": "active",
                    "position": json.dumps([0, 0, 0]),
                    "rotation": json.dumps([0, 0, 0]),
                    "interactions": json.dumps([]),
                    "points": "0"
                }
            )
            
            # Award joining badge
            self.gamification_engine.award_badge(user_id, "virtual_explorer", virtual_event_id)
            
            # Get initial state
            event_state = self._get_virtual_event_state(virtual_event_id)
            
            logger.info(f"User {user_id} joined virtual event {virtual_event_id}")
            
            return {
                "success": True,
                "participant_id": user_id,
                "environment": environment,
                "initial_state": event_state,
                "capabilities": participant_data["capabilities"],
                "avatar": participant_data["avatar_config"]
            }
            
        except Exception as e:
            logger.error(f"Error joining virtual event: {e}")
            return {"success": False, "error": str(e)}
    
    def create_interactive_poll(self, virtual_event_id: str, organizer_id: int, 
                              poll_data: Dict) -> Dict[str, Any]:
        """Create an interactive poll for virtual event"""
        try:
            poll_id = f"poll_{virtual_event_id}_{uuid.uuid4().hex[:8]}"
            
            poll_config = {
                "id": poll_id,
                "virtual_event_id": virtual_event_id,
                "created_by": organizer_id,
                "title": poll_data.get("title", ""),
                "type": poll_data.get("type", PollType.MULTIPLE_CHOICE.value),
                "options": poll_data.get("options", []),
                "duration": poll_data.get("duration", 300),  # 5 minutes default
                "created_at": datetime.utcnow().isoformat(),
                "is_active": True,
                "responses": {},
                "results": {}
            }
            
            if self.redis_client:
                self.redis_client.hset(
                    f"poll:{poll_id}",
                    mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
                            for k, v in poll_config.items()}
                )
                
                # Set expiration
                self.redis_client.expire(f"poll:{poll_id}", poll_config["duration"])
                
                # Add to active polls list
                self.redis_client.sadd(f"virtual_event:{virtual_event_id}:polls", poll_id)
            
            self.active_polls[poll_id] = poll_config
            
            return {
                "success": True,
                "poll_id": poll_id,
                "config": poll_config
            }
            
        except Exception as e:
            logger.error(f"Error creating interactive poll: {e}")
            return {"success": False, "error": str(e)}
    
    def submit_poll_response(self, poll_id: str, user_id: int, response: Any) -> Dict[str, Any]:
        """Submit response to interactive poll"""
        try:
            if not self.redis_client:
                return {"success": False, "error": "Redis not available"}
            
            # Get poll configuration
            poll_data = self.redis_client.hgetall(f"poll:{poll_id}")
            if not poll_data:
                return {"success": False, "error": "Poll not found"}
            
            poll_config = {k: json.loads(v) if k in ["options", "responses", "results"] else v 
                          for k, v in poll_data.items()}
            
            if not poll_config.get("is_active", "false") == "true":
                return {"success": False, "error": "Poll is not active"}
            
            # Store response
            responses = poll_config.get("responses", {})
            responses[str(user_id)] = {
                "response": response,
                "submitted_at": datetime.utcnow().isoformat()
            }
            
            # Update poll data
            self.redis_client.hset(f"poll:{poll_id}", "responses", json.dumps(responses))
            
            # Award participation points
            self.gamification_engine.award_points(user_id, 10, "poll_participation")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Error submitting poll response: {e}")
            return {"success": False, "error": str(e)}
    
    def get_poll_results(self, poll_id: str) -> Dict[str, Any]:
        """Get real-time poll results"""
        try:
            if not self.redis_client:
                return {"success": False, "error": "Redis not available"}
            
            poll_data = self.redis_client.hgetall(f"poll:{poll_id}")
            if not poll_data:
                return {"success": False, "error": "Poll not found"}
            
            responses = json.loads(poll_data.get("responses", "{}"))
            poll_type = poll_data.get("type", PollType.MULTIPLE_CHOICE.value)
            options = json.loads(poll_data.get("options", "[]"))
            
            # Calculate results based on poll type
            if poll_type == PollType.MULTIPLE_CHOICE.value:
                results = self._calculate_multiple_choice_results(responses, options)
            elif poll_type == PollType.RATING.value:
                results = self._calculate_rating_results(responses)
            elif poll_type == PollType.WORD_CLOUD.value:
                results = self._calculate_word_cloud_results(responses)
            else:
                results = {"total_responses": len(responses)}
            
            return {
                "success": True,
                "poll_id": poll_id,
                "type": poll_type,
                "results": results,
                "total_responses": len(responses)
            }
            
        except Exception as e:
            logger.error(f"Error getting poll results: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user_position(self, virtual_event_id: str, user_id: int, 
                           position: List[float], rotation: List[float]) -> Dict[str, Any]:
        """Update user position in virtual environment"""
        try:
            if not self.redis_client:
                return {"success": False, "error": "Redis not available"}
            
            # Update user position
            self.redis_client.hset(
                f"virtual_event:{virtual_event_id}:user:{user_id}",
                mapping={
                    "position": json.dumps(position),
                    "rotation": json.dumps(rotation),
                    "last_updated": datetime.utcnow().isoformat()
                }
            )
            
            # Check for proximity interactions
            interactions = self._check_proximity_interactions(virtual_event_id, user_id, position)
            
            if interactions:
                self.gamification_engine.process_interactions(user_id, interactions)
            
            return {"success": True, "interactions": interactions}
            
        except Exception as e:
            logger.error(f"Error updating user position: {e}")
            return {"success": False, "error": str(e)}
    
    def _apply_custom_config(self, base_env: VirtualEnvironment, custom_config: Dict) -> VirtualEnvironment:
        """Apply custom configuration to base environment"""
        # Create a copy and apply customizations
        env_dict = base_env.__dict__.copy()
        
        for key, value in custom_config.items():
            if key in env_dict:
                if isinstance(env_dict[key], dict) and isinstance(value, dict):
                    env_dict[key].update(value)
                else:
                    env_dict[key] = value
        
        return VirtualEnvironment(**env_dict)
    
    def _generate_default_avatar(self, user: User) -> Dict[str, Any]:
        """Generate default avatar configuration for user"""
        return {
            "id": str(uuid.uuid4()),
            "name": user.username,
            "appearance": {
                "body_type": "default",
                "clothing": "casual",
                "accessories": [],
                "colors": {
                    "primary": "#3498db",
                    "secondary": "#2ecc71"
                }
            },
            "animations": {
                "idle": "default_idle",
                "walking": "default_walk",
                "talking": "default_talk"
            }
        }
    
    def _detect_device_capabilities(self, device_info: Dict) -> Dict[str, bool]:
        """Detect device capabilities for optimal experience"""
        capabilities = {
            "vr_support": False,
            "ar_support": False,
            "high_quality_graphics": True,
            "spatial_audio": False,
            "hand_tracking": False,
            "eye_tracking": False
        }
        
        user_agent = device_info.get("user_agent", "").lower()
        
        # VR device detection
        if any(vr in user_agent for vr in ["oculus", "vive", "steamvr", "webxr"]):
            capabilities["vr_support"] = True
            capabilities["spatial_audio"] = True
            capabilities["hand_tracking"] = True
        
        # AR device detection
        if any(ar in user_agent for ar in ["arcore", "arkit", "hololens"]):
            capabilities["ar_support"] = True
        
        # Mobile device detection (lower graphics quality)
        if any(mobile in user_agent for mobile in ["mobile", "android", "iphone"]):
            capabilities["high_quality_graphics"] = False
        
        return capabilities
    
    def _get_virtual_event_state(self, virtual_event_id: str) -> Dict[str, Any]:
        """Get current state of virtual event"""
        try:
            if not self.redis_client:
                return {}
            
            event_data = self.redis_client.hgetall(f"virtual_event:{virtual_event_id}")
            
            # Get active polls
            active_polls = list(self.redis_client.smembers(f"virtual_event:{virtual_event_id}:polls"))
            
            # Get leaderboard
            leaderboard = self.leaderboard_manager.get_event_leaderboard(virtual_event_id)
            
            state = {
                "participants": json.loads(event_data.get("participants", "[]")),
                "interactive_state": json.loads(event_data.get("interactive_state", "{}")),
                "active_polls": active_polls,
                "leaderboard": leaderboard,
                "stream_active": event_data.get("stream_config") is not None
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting virtual event state: {e}")
            return {}
    
    def _check_proximity_interactions(self, virtual_event_id: str, user_id: int, 
                                    position: List[float]) -> List[Dict]:
        """Check for proximity-based interactions"""
        interactions = []
        
        try:
            # Get environment data
            event_data = self.redis_client.hgetall(f"virtual_event:{virtual_event_id}")
            environment = json.loads(event_data.get("environment", "{}"))
            
            # Check interactive elements
            for element in environment.get("interactive_elements", []):
                element_pos = element.get("position", [0, 0, 0])
                distance = np.linalg.norm(np.array(position) - np.array(element_pos))
                
                if distance < 2.0:  # Within interaction range
                    interactions.append({
                        "type": element["type"],
                        "element": element,
                        "distance": distance
                    })
            
            return interactions
            
        except Exception as e:
            logger.error(f"Error checking proximity interactions: {e}")
            return []
    
    def _calculate_multiple_choice_results(self, responses: Dict, options: List) -> Dict:
        """Calculate multiple choice poll results"""
        results = {}
        total = len(responses)
        
        # Count responses for each option
        option_counts = {}
        for response_data in responses.values():
            response = response_data.get("response")
            if response in option_counts:
                option_counts[response] += 1
            else:
                option_counts[response] = 1
        
        # Calculate percentages
        for option in options:
            count = option_counts.get(option, 0)
            percentage = (count / total * 100) if total > 0 else 0
            results[option] = {"count": count, "percentage": percentage}
        
        return results
    
    def _calculate_rating_results(self, responses: Dict) -> Dict:
        """Calculate rating poll results"""
        ratings = [float(response_data.get("response", 0)) for response_data in responses.values()]
        
        if not ratings:
            return {"average": 0, "total_responses": 0}
        
        return {
            "average": sum(ratings) / len(ratings),
            "total_responses": len(ratings),
            "distribution": {
                f"{i}": sum(1 for r in ratings if i <= r < i+1) 
                for i in range(1, 6)
            }
        }
    
    def _calculate_word_cloud_results(self, responses: Dict) -> Dict:
        """Calculate word cloud poll results"""
        words = {}
        
        for response_data in responses.values():
            response_words = response_data.get("response", "").lower().split()
            for word in response_words:
                if len(word) > 2:  # Filter short words
                    words[word] = words.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "words": dict(sorted_words[:50]),  # Top 50 words
            "total_words": len(words)
        }


class LeaderboardManager:
    """
    Manages leaderboards and scoring for virtual events
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
    
    def update_user_score(self, user_id: int, event_id: str, points: int, category: str):
        """Update user score on leaderboard"""
        try:
            if not self.redis_client:
                return
            
            # Update total score
            self.redis_client.zincrby(f"leaderboard:{event_id}:total", points, user_id)
            
            # Update category score
            self.redis_client.zincrby(f"leaderboard:{event_id}:{category}", points, user_id)
            
            # Update user's total points
            self.redis_client.hincrby(f"user:{user_id}:points", event_id, points)
            
        except Exception as e:
            logger.error(f"Error updating user score: {e}")
    
    def get_event_leaderboard(self, event_id: str, limit: int = 10) -> List[Dict]:
        """Get event leaderboard"""
        try:
            if not self.redis_client:
                return []
            
            # Get top users with scores
            leaderboard_data = self.redis_client.zrevrange(
                f"leaderboard:{event_id}:total", 
                0, limit-1, 
                withscores=True
            )
            
            leaderboard = []
            for rank, (user_id, score) in enumerate(leaderboard_data, 1):
                user = User.query.get(int(user_id))
                if user:
                    leaderboard.append({
                        "rank": rank,
                        "user_id": int(user_id),
                        "username": user.username,
                        "full_name": user.full_name,
                        "score": int(score)
                    })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []


class GamificationEngine:
    """
    Handles gamification elements like badges, achievements, and point systems
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.badge_definitions = self.load_badge_definitions()
    
    def load_badge_definitions(self) -> Dict[str, Dict]:
        """Load badge definitions"""
        return {
            "virtual_explorer": {
                "name": "Virtual Explorer",
                "description": "Joined your first virtual event",
                "icon": "🌐",
                "points": 50
            },
            "poll_master": {
                "name": "Poll Master",
                "description": "Participated in 10 polls",
                "icon": "📊",
                "points": 100
            },
            "social_butterfly": {
                "name": "Social Butterfly",
                "description": "Interacted with 20 different participants",
                "icon": "🦋",
                "points": 150
            },
            "environment_architect": {
                "name": "Environment Architect",
                "description": "Customized virtual environment",
                "icon": "🏗️",
                "points": 200
            },
            "stream_star": {
                "name": "Stream Star",
                "description": "Attended 5 live streams",
                "icon": "⭐",
                "points": 75
            }
        }
    
    def initialize_event_gamification(self, virtual_event_id: str, event_id: int):
        """Initialize gamification elements for an event"""
        try:
            if not self.redis_client:
                return
            
            # Create achievement tracking
            self.redis_client.hset(
                f"gamification:{virtual_event_id}",
                mapping={
                    "event_id": event_id,
                    "badges_awarded": json.dumps({}),
                    "achievements": json.dumps({}),
                    "challenges": json.dumps([])
                }
            )
            
        except Exception as e:
            logger.error(f"Error initializing gamification: {e}")
    
    def award_badge(self, user_id: int, badge_key: str, event_context: str = None):
        """Award a badge to a user"""
        try:
            badge_def = self.badge_definitions.get(badge_key)
            if not badge_def:
                return
            
            # Check if user already has this badge
            existing_badge = UserBadge.query.filter_by(
                user_id=user_id,
                badge_id=badge_key  # Using badge_key as badge_id for now
            ).first()
            
            if existing_badge:
                return  # Already has badge
            
            # Create badge record
            badge = Badge.query.filter_by(name=badge_def["name"]).first()
            if not badge:
                badge = Badge(
                    name=badge_def["name"],
                    description=badge_def["description"],
                    icon_url=badge_def["icon"],
                    points=badge_def["points"]
                )
                db.session.add(badge)
                db.session.commit()
            
            # Award badge to user
            user_badge = UserBadge(
                user_id=user_id,
                badge_id=badge.id,
                event_id=event_context
            )
            db.session.add(user_badge)
            db.session.commit()
            
            # Award points
            self.award_points(user_id, badge_def["points"], f"badge_{badge_key}")
            
            logger.info(f"Awarded badge {badge_key} to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error awarding badge: {e}")
            db.session.rollback()
    
    def award_points(self, user_id: int, points: int, reason: str):
        """Award points to a user"""
        try:
            if not self.redis_client:
                return
            
            # Add to user's total points
            self.redis_client.hincrby(f"user:{user_id}:total_points", "total", points)
            
            # Log the point award
            self.redis_client.lpush(
                f"user:{user_id}:point_history",
                json.dumps({
                    "points": points,
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat()
                })
            )
            
            # Keep only last 100 entries
            self.redis_client.ltrim(f"user:{user_id}:point_history", 0, 99)
            
        except Exception as e:
            logger.error(f"Error awarding points: {e}")
    
    def process_interactions(self, user_id: int, interactions: List[Dict]):
        """Process user interactions for gamification"""
        for interaction in interactions:
            interaction_type = interaction.get("type")
            
            if interaction_type == "applause_button":
                self.award_points(user_id, 5, "applause_interaction")
            elif interaction_type == "raise_hand":
                self.award_points(user_id, 3, "raise_hand")
            elif interaction_type == "emoji_reactions":
                self.award_points(user_id, 2, "emoji_reaction")
            elif interaction_type == "3d_whiteboard":
                self.award_points(user_id, 10, "whiteboard_interaction")


class VRARManager:
    """
    Manages VR/AR specific features and optimizations
    """
    
    def __init__(self):
        self.vr_sessions = {}
        self.ar_sessions = {}
    
    def initialize_vr_session(self, user_id: int, device_info: Dict) -> Dict[str, Any]:
        """Initialize VR session for user"""
        try:
            session_id = f"vr_{user_id}_{uuid.uuid4().hex[:8]}"
            
            vr_config = {
                "session_id": session_id,
                "user_id": user_id,
                "device_type": device_info.get("device_type", "generic_vr"),
                "controllers": device_info.get("controllers", []),
                "room_scale": device_info.get("room_scale", True),
                "hand_tracking": device_info.get("hand_tracking", False),
                "eye_tracking": device_info.get("eye_tracking", False),
                "haptic_feedback": device_info.get("haptic_feedback", True)
            }
            
            self.vr_sessions[session_id] = vr_config
            
            return {
                "success": True,
                "session_id": session_id,
                "config": vr_config
            }
            
        except Exception as e:
            logger.error(f"Error initializing VR session: {e}")
            return {"success": False, "error": str(e)}
    
    def initialize_ar_session(self, user_id: int, device_info: Dict) -> Dict[str, Any]:
        """Initialize AR session for user"""
        try:
            session_id = f"ar_{user_id}_{uuid.uuid4().hex[:8]}"
            
            ar_config = {
                "session_id": session_id,
                "user_id": user_id,
                "platform": device_info.get("platform", "web"),
                "camera_access": device_info.get("camera_access", True),
                "motion_tracking": device_info.get("motion_tracking", True),
                "plane_detection": device_info.get("plane_detection", True),
                "light_estimation": device_info.get("light_estimation", False)
            }
            
            self.ar_sessions[session_id] = ar_config
            
            return {
                "success": True,
                "session_id": session_id,
                "config": ar_config
            }
            
        except Exception as e:
            logger.error(f"Error initializing AR session: {e}")
            return {"success": False, "error": str(e)}


# Global virtual events engine instance
virtual_events_engine = VirtualEventsEngine()