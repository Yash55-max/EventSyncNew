"""
Gamification System for Event Management Platform
Handles badges, achievements, points, and user progression
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import json

class BadgeCategory(Enum):
    """Categories for different types of badges"""
    SUSTAINABILITY = "sustainability"
    PLANNING = "planning" 
    ASSESSMENT = "assessment"
    ACHIEVEMENT = "achievement"
    SPECIAL = "special"
    MILESTONE = "milestone"

class BadgeTier(Enum):
    """Tiers representing badge difficulty/prestige"""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    LEGENDARY = "legendary"

class PointCategory(Enum):
    """Categories for earning points"""
    EVENT_CREATION = "event_creation"
    SUSTAINABILITY_ACTION = "sustainability_action"
    ASSESSMENT_COMPLETION = "assessment_completion"
    SKILL_IMPROVEMENT = "skill_improvement"
    COLLABORATION = "collaboration"
    INNOVATION = "innovation"
    ACHIEVEMENT = "achievement"

@dataclass
class Badge:
    """Represents a badge/achievement in the system"""
    badge_id: str
    title: str
    description: str
    category: BadgeCategory
    tier: BadgeTier
    icon: str
    points_value: int
    criteria: Dict[str, Any]
    unlock_conditions: List[str]
    rarity_score: float
    is_hidden: bool = False
    prerequisites: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate badge data after initialization"""
        if self.points_value < 0:
            raise ValueError("Points value cannot be negative")
        if not 0 <= self.rarity_score <= 100:
            raise ValueError("Rarity score must be between 0 and 100")

@dataclass
class UserBadge:
    """Represents a badge earned by a user"""
    badge_id: str
    user_id: str
    earned_date: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    is_featured: bool = False
    
@dataclass
class UserProgress:
    """Tracks user progress towards badges and achievements"""
    user_id: str
    total_points: int
    level: int
    badges_earned: List[UserBadge]
    current_streaks: Dict[str, int] = field(default_factory=dict)
    milestone_progress: Dict[str, float] = field(default_factory=dict)
    skill_ratings: Dict[str, float] = field(default_factory=dict)
    last_activity: Optional[datetime] = None

@dataclass
class PointsEntry:
    """Represents points earned by user"""
    user_id: str
    category: PointCategory
    points: int
    description: str
    timestamp: datetime
    event_id: Optional[str] = None
    assessment_id: Optional[str] = None

class BadgeSystem:
    """Core badge and achievement system"""
    
    def __init__(self):
        self.badges: Dict[str, Badge] = {}
        self.user_progress: Dict[str, UserProgress] = {}
        self.points_history: List[PointsEntry] = []
        self._initialize_default_badges()
    
    def _initialize_default_badges(self):
        """Initialize default badges available in the system"""
        default_badges = [
            # Sustainability Badges
            Badge(
                badge_id="eco_warrior",
                title="Eco Warrior",
                description="Reduce event carbon footprint by 50kg+ CO₂",
                category=BadgeCategory.SUSTAINABILITY,
                tier=BadgeTier.BRONZE,
                icon="fas fa-leaf",
                points_value=100,
                criteria={"carbon_reduction_kg": 50},
                unlock_conditions=["Calculate carbon footprint for at least 1 event"],
                rarity_score=75.0
            ),
            Badge(
                badge_id="green_champion",
                title="Green Champion",
                description="Achieve 90%+ sustainability score on 3 events",
                category=BadgeCategory.SUSTAINABILITY,
                tier=BadgeTier.SILVER,
                icon="fas fa-award",
                points_value=250,
                criteria={"sustainability_score": 90, "event_count": 3},
                unlock_conditions=["Have eco_warrior badge"],
                rarity_score=85.0,
                prerequisites=["eco_warrior"]
            ),
            Badge(
                badge_id="carbon_neutral_master",
                title="Carbon Neutral Master",
                description="Organize 5 carbon-neutral events",
                category=BadgeCategory.SUSTAINABILITY,
                tier=BadgeTier.GOLD,
                icon="fas fa-globe",
                points_value=500,
                criteria={"carbon_neutral_events": 5},
                unlock_conditions=["Have green_champion badge"],
                rarity_score=95.0,
                prerequisites=["green_champion"]
            ),
            
            # Planning Badges
            Badge(
                badge_id="first_event",
                title="Event Creator",
                description="Create your first event",
                category=BadgeCategory.PLANNING,
                tier=BadgeTier.BRONZE,
                icon="fas fa-calendar-plus",
                points_value=50,
                criteria={"events_created": 1},
                unlock_conditions=[],
                rarity_score=10.0
            ),
            Badge(
                badge_id="experienced_planner",
                title="Experienced Planner",
                description="Successfully organize 10 events",
                category=BadgeCategory.PLANNING,
                tier=BadgeTier.SILVER,
                icon="fas fa-calendar-check",
                points_value=200,
                criteria={"successful_events": 10},
                unlock_conditions=["Have first_event badge"],
                rarity_score=60.0,
                prerequisites=["first_event"]
            ),
            Badge(
                badge_id="event_master",
                title="Event Master",
                description="Organize 50+ events with 85%+ success rate",
                category=BadgeCategory.PLANNING,
                tier=BadgeTier.GOLD,
                icon="fas fa-crown",
                points_value=750,
                criteria={"events_organized": 50, "success_rate": 85},
                unlock_conditions=["Have experienced_planner badge"],
                rarity_score=90.0,
                prerequisites=["experienced_planner"]
            ),
            
            # Assessment Badges
            Badge(
                badge_id="quick_learner",
                title="Quick Learner",
                description="Complete first assessment with 80%+ score",
                category=BadgeCategory.ASSESSMENT,
                tier=BadgeTier.BRONZE,
                icon="fas fa-brain",
                points_value=75,
                criteria={"first_assessment_score": 80},
                unlock_conditions=[],
                rarity_score=40.0
            ),
            Badge(
                badge_id="skill_builder",
                title="Skill Builder",
                description="Complete 10 assessments with average 85%+ score",
                category=BadgeCategory.ASSESSMENT,
                tier=BadgeTier.SILVER,
                icon="fas fa-chart-line",
                points_value=300,
                criteria={"assessments_completed": 10, "average_score": 85},
                unlock_conditions=["Have quick_learner badge"],
                rarity_score=70.0,
                prerequisites=["quick_learner"]
            ),
            Badge(
                badge_id="assessment_perfectionist",
                title="Assessment Perfectionist",
                description="Achieve 100% score on any advanced assessment",
                category=BadgeCategory.ASSESSMENT,
                tier=BadgeTier.GOLD,
                icon="fas fa-star",
                points_value=400,
                criteria={"perfect_advanced_score": 100},
                unlock_conditions=["Complete at least 5 assessments"],
                rarity_score=92.0
            ),
            
            # Special Achievement Badges
            Badge(
                badge_id="crisis_manager",
                title="Crisis Manager",
                description="Successfully handle 3 crisis management scenarios",
                category=BadgeCategory.ACHIEVEMENT,
                tier=BadgeTier.SILVER,
                icon="fas fa-fire-extinguisher",
                points_value=350,
                criteria={"crisis_scenarios_passed": 3},
                unlock_conditions=["Complete at least 1 crisis management assessment"],
                rarity_score=80.0
            ),
            Badge(
                badge_id="budget_ninja",
                title="Budget Ninja",
                description="Stay under budget on 5 consecutive events",
                category=BadgeCategory.ACHIEVEMENT,
                tier=BadgeTier.GOLD,
                icon="fas fa-dollar-sign",
                points_value=450,
                criteria={"consecutive_under_budget": 5},
                unlock_conditions=["Organize at least 5 events with budget tracking"],
                rarity_score=88.0
            ),
            Badge(
                badge_id="innovation_pioneer",
                title="Innovation Pioneer",
                description="Be first to try 3 new platform features",
                category=BadgeCategory.SPECIAL,
                tier=BadgeTier.PLATINUM,
                icon="fas fa-rocket",
                points_value=600,
                criteria={"new_features_tried": 3},
                unlock_conditions=["Be an early adopter"],
                rarity_score=96.0,
                is_hidden=True
            ),
            
            # Milestone Badges
            Badge(
                badge_id="dedication_streak",
                title="Dedication Streak",
                description="Use platform for 30 consecutive days",
                category=BadgeCategory.MILESTONE,
                tier=BadgeTier.SILVER,
                icon="fas fa-calendar-check",
                points_value=250,
                criteria={"daily_streak": 30},
                unlock_conditions=[],
                rarity_score=65.0
            ),
            Badge(
                badge_id="community_helper",
                title="Community Helper",
                description="Help 10 other users with feedback or collaboration",
                category=BadgeCategory.MILESTONE,
                tier=BadgeTier.GOLD,
                icon="fas fa-hands-helping",
                points_value=300,
                criteria={"users_helped": 10},
                unlock_conditions=["Have at least 2 badges"],
                rarity_score=85.0
            )
        ]
        
        for badge in default_badges:
            self.badges[badge.badge_id] = badge
    
    def get_available_badges(self, user_id: str, include_hidden: bool = False) -> List[Badge]:
        """Get badges available to user (not yet earned)"""
        user_progress = self.user_progress.get(user_id)
        if not user_progress:
            return []
        
        earned_badge_ids = {ub.badge_id for ub in user_progress.badges_earned}
        available = []
        
        for badge in self.badges.values():
            if badge.badge_id not in earned_badge_ids:
                if include_hidden or not badge.is_hidden:
                    # Check prerequisites
                    if all(prereq in earned_badge_ids for prereq in badge.prerequisites):
                        available.append(badge)
        
        return sorted(available, key=lambda b: (b.tier.value, b.rarity_score))
    
    def check_badge_eligibility(self, user_id: str, badge_id: str, context: Dict[str, Any]) -> bool:
        """Check if user meets criteria for specific badge"""
        if badge_id not in self.badges:
            return False
        
        badge = self.badges[badge_id]
        user_progress = self.user_progress.get(user_id)
        
        if not user_progress:
            return False
        
        # Check if already earned
        earned_badges = {ub.badge_id for ub in user_progress.badges_earned}
        if badge_id in earned_badges:
            return False
        
        # Check prerequisites
        if not all(prereq in earned_badges for prereq in badge.prerequisites):
            return False
        
        # Check specific criteria based on badge
        return self._evaluate_badge_criteria(badge, user_progress, context)
    
    def _evaluate_badge_criteria(self, badge: Badge, user_progress: UserProgress, context: Dict[str, Any]) -> bool:
        """Evaluate specific criteria for badge eligibility"""
        criteria = badge.criteria
        
        # Sustainability badges
        if badge.badge_id == "eco_warrior":
            return context.get("carbon_reduction_kg", 0) >= criteria["carbon_reduction_kg"]
        
        elif badge.badge_id == "green_champion":
            events_with_high_score = context.get("events_with_90plus_sustainability", 0)
            return events_with_high_score >= criteria["event_count"]
        
        elif badge.badge_id == "carbon_neutral_master":
            return context.get("carbon_neutral_events", 0) >= criteria["carbon_neutral_events"]
        
        # Planning badges
        elif badge.badge_id == "first_event":
            return context.get("events_created", 0) >= criteria["events_created"]
        
        elif badge.badge_id == "experienced_planner":
            return context.get("successful_events", 0) >= criteria["successful_events"]
        
        elif badge.badge_id == "event_master":
            events_count = context.get("events_organized", 0)
            success_rate = context.get("success_rate", 0)
            return (events_count >= criteria["events_organized"] and 
                   success_rate >= criteria["success_rate"])
        
        # Assessment badges
        elif badge.badge_id == "quick_learner":
            return context.get("first_assessment_score", 0) >= criteria["first_assessment_score"]
        
        elif badge.badge_id == "skill_builder":
            completed = context.get("assessments_completed", 0)
            avg_score = context.get("average_assessment_score", 0)
            return (completed >= criteria["assessments_completed"] and 
                   avg_score >= criteria["average_score"])
        
        elif badge.badge_id == "assessment_perfectionist":
            return context.get("has_perfect_advanced_score", False)
        
        # Achievement badges
        elif badge.badge_id == "crisis_manager":
            return context.get("crisis_scenarios_passed", 0) >= criteria["crisis_scenarios_passed"]
        
        elif badge.badge_id == "budget_ninja":
            return context.get("consecutive_under_budget", 0) >= criteria["consecutive_under_budget"]
        
        elif badge.badge_id == "innovation_pioneer":
            return context.get("new_features_tried", 0) >= criteria["new_features_tried"]
        
        # Milestone badges
        elif badge.badge_id == "dedication_streak":
            return user_progress.current_streaks.get("daily_login", 0) >= criteria["daily_streak"]
        
        elif badge.badge_id == "community_helper":
            return context.get("users_helped", 0) >= criteria["users_helped"]
        
        return False
    
    def award_badge(self, user_id: str, badge_id: str, context: Dict[str, Any] = None) -> bool:
        """Award badge to user if eligible"""
        if context is None:
            context = {}
        
        if not self.check_badge_eligibility(user_id, badge_id, context):
            return False
        
        badge = self.badges[badge_id]
        user_badge = UserBadge(
            badge_id=badge_id,
            user_id=user_id,
            earned_date=datetime.utcnow(),
            context=context
        )
        
        # Initialize user progress if not exists
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(
                user_id=user_id,
                total_points=0,
                level=1,
                badges_earned=[]
            )
        
        user_progress = self.user_progress[user_id]
        user_progress.badges_earned.append(user_badge)
        
        # Award points
        self.award_points(user_id, PointCategory.ACHIEVEMENT, 
                         badge.points_value, f"Earned badge: {badge.title}")
        
        return True
    
    def award_points(self, user_id: str, category: PointCategory, points: int, 
                    description: str, event_id: str = None, assessment_id: str = None):
        """Award points to user"""
        points_entry = PointsEntry(
            user_id=user_id,
            category=category,
            points=points,
            description=description,
            timestamp=datetime.utcnow(),
            event_id=event_id,
            assessment_id=assessment_id
        )
        
        self.points_history.append(points_entry)
        
        # Update user progress
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(
                user_id=user_id,
                total_points=0,
                level=1,
                badges_earned=[]
            )
        
        user_progress = self.user_progress[user_id]
        user_progress.total_points += points
        user_progress.level = self._calculate_level(user_progress.total_points)
        user_progress.last_activity = datetime.utcnow()
    
    def _calculate_level(self, total_points: int) -> int:
        """Calculate user level based on total points"""
        # Level formula: sqrt(points/100) + 1
        import math
        return int(math.sqrt(total_points / 100)) + 1
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        user_progress = self.user_progress.get(user_id)
        if not user_progress:
            return {
                "total_points": 0,
                "level": 1,
                "badges_earned": [],
                "badges_by_category": {},
                "rare_badges": [],
                "next_level_progress": 0
            }
        
        # Categorize badges
        badges_by_category = {}
        rare_badges = []
        
        for user_badge in user_progress.badges_earned:
            badge = self.badges.get(user_badge.badge_id)
            if badge:
                category = badge.category.value
                if category not in badges_by_category:
                    badges_by_category[category] = []
                badges_by_category[category].append(badge)
                
                # Consider badges with rarity > 80 as rare
                if badge.rarity_score > 80:
                    rare_badges.append(badge)
        
        # Calculate progress to next level
        current_level = user_progress.level
        points_for_current = (current_level - 1) ** 2 * 100
        points_for_next = current_level ** 2 * 100
        progress_to_next = (user_progress.total_points - points_for_current) / (points_for_next - points_for_current)
        
        return {
            "total_points": user_progress.total_points,
            "level": user_progress.level,
            "badges_earned": len(user_progress.badges_earned),
            "badges_by_category": badges_by_category,
            "rare_badges": rare_badges,
            "next_level_progress": min(progress_to_next * 100, 100),
            "recent_activity": user_progress.last_activity
        }
    
    def check_and_award_automatic_badges(self, user_id: str, action_context: Dict[str, Any]):
        """Check and award badges automatically based on user actions"""
        available_badges = self.get_available_badges(user_id)
        
        for badge in available_badges:
            if self.check_badge_eligibility(user_id, badge.badge_id, action_context):
                self.award_badge(user_id, badge.badge_id, action_context)
    
    def get_leaderboard(self, limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
        """Get leaderboard of top users"""
        leaderboard = []
        
        for user_id, progress in self.user_progress.items():
            entry = {
                "user_id": user_id,
                "total_points": progress.total_points,
                "level": progress.level,
                "badges_count": len(progress.badges_earned)
            }
            
            if category:
                # Filter by specific badge category
                category_badges = [
                    ub for ub in progress.badges_earned
                    if self.badges.get(ub.badge_id, {}).category.value == category
                ]
                entry["category_badges"] = len(category_badges)
                entry["category_points"] = sum(
                    self.badges.get(ub.badge_id, Badge(
                        badge_id="", title="", description="", category=BadgeCategory.PLANNING,
                        tier=BadgeTier.BRONZE, icon="", points_value=0, criteria={}, 
                        unlock_conditions=[], rarity_score=0
                    )).points_value
                    for ub in category_badges
                )
                
                leaderboard.append(entry)
                # Sort by category-specific criteria
                leaderboard.sort(key=lambda x: (x["category_points"], x["total_points"]), reverse=True)
            else:
                leaderboard.append(entry)
        
        if not category:
            leaderboard.sort(key=lambda x: (x["total_points"], x["badges_count"]), reverse=True)
        
        return leaderboard[:limit]

# Global instance
gamification_system = BadgeSystem()

# Utility functions for easy access
def award_user_badge(user_id: str, badge_id: str, context: Dict[str, Any] = None) -> bool:
    """Award badge to user"""
    return gamification_system.award_badge(user_id, badge_id, context or {})

def award_user_points(user_id: str, category: PointCategory, points: int, description: str, 
                     event_id: str = None, assessment_id: str = None):
    """Award points to user"""
    gamification_system.award_points(user_id, category, points, description, event_id, assessment_id)

def get_user_badges(user_id: str) -> List[Dict[str, Any]]:
    """Get user's earned badges with details"""
    user_progress = gamification_system.user_progress.get(user_id)
    if not user_progress:
        return []
    
    badges_info = []
    for user_badge in user_progress.badges_earned:
        badge = gamification_system.badges.get(user_badge.badge_id)
        if badge:
            badges_info.append({
                "badge_id": badge.badge_id,
                "title": badge.title,
                "description": badge.description,
                "category": badge.category.value,
                "tier": badge.tier.value,
                "icon": badge.icon,
                "points_value": badge.points_value,
                "rarity_score": badge.rarity_score,
                "earned_date": user_badge.earned_date.isoformat(),
                "is_featured": user_badge.is_featured
            })
    
    return sorted(badges_info, key=lambda b: b["earned_date"], reverse=True)

def check_automatic_badges(user_id: str, action_type: str, **context):
    """Check and award badges based on user actions"""
    action_context = {"action_type": action_type, **context}
    gamification_system.check_and_award_automatic_badges(user_id, action_context)

def get_achievement_progress(user_id: str) -> Dict[str, Any]:
    """Get user achievement progress and stats"""
    return gamification_system.get_user_stats(user_id)