"""
AI Engine for Event Management Platform
Provides AI-powered matching, recommendations, and team formation
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple, Optional
import logging

from app import db
from models import (
    User, Event, UserSkill, UserInterest, Team, TeamMember, 
    AIRecommendation, EventCategory, SkillLevel, Ticket, EventFeedback
)

logger = logging.getLogger(__name__)

class AIMatchingEngine:
    """
    AI-powered matching and recommendation engine for events and team formation
    """
    
    def __init__(self):
        self.skill_weights = {
            SkillLevel.EXPERT: 4.0,
            SkillLevel.ADVANCED: 3.0,
            SkillLevel.INTERMEDIATE: 2.0,
            SkillLevel.BEGINNER: 1.0
        }
    
    def calculate_user_skill_vector(self, user_id: int) -> Dict[str, float]:
        """Calculate normalized skill vector for a user"""
        skills = UserSkill.query.filter_by(user_id=user_id).all()
        skill_vector = {}
        
        for skill in skills:
            weight = self.skill_weights.get(skill.level, 1.0)
            if skill.verified:
                weight *= 1.5  # Boost verified skills
            skill_vector[skill.skill_name.lower()] = weight
            
        return skill_vector
    
    def calculate_user_interest_vector(self, user_id: int) -> Dict[str, float]:
        """Calculate normalized interest vector for a user"""
        interests = UserInterest.query.filter_by(user_id=user_id).all()
        interest_vector = {}
        
        for interest in interests:
            interest_vector[interest.interest.lower()] = interest.weight
            
        return interest_vector
    
    def calculate_compatibility_score(self, user1_id: int, user2_id: int) -> float:
        """Calculate compatibility score between two users (0.0 to 1.0)"""
        try:
            # Get skill vectors
            skills1 = self.calculate_user_skill_vector(user1_id)
            skills2 = self.calculate_user_skill_vector(user2_id)
            
            # Get interest vectors
            interests1 = self.calculate_user_interest_vector(user1_id)
            interests2 = self.calculate_user_interest_vector(user2_id)
            
            # Calculate skill complementarity (different skills complement each other)
            skill_complement_score = self._calculate_complementarity_score(skills1, skills2)
            
            # Calculate interest similarity
            interest_similarity_score = self._calculate_similarity_score(interests1, interests2)
            
            # Combined score (weighted average)
            compatibility_score = (skill_complement_score * 0.6 + interest_similarity_score * 0.4)
            
            return min(compatibility_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {e}")
            return 0.0
    
    def _calculate_complementarity_score(self, vector1: Dict[str, float], vector2: Dict[str, float]) -> float:
        """Calculate how well two skill vectors complement each other"""
        if not vector1 or not vector2:
            return 0.0
            
        all_skills = set(vector1.keys()) | set(vector2.keys())
        if not all_skills:
            return 0.0
            
        complement_score = 0.0
        overlap_penalty = 0.0
        
        for skill in all_skills:
            skill1_level = vector1.get(skill, 0.0)
            skill2_level = vector2.get(skill, 0.0)
            
            # Reward when one has skill and other doesn't (complementarity)
            if skill1_level > 0 and skill2_level == 0:
                complement_score += skill1_level
            elif skill2_level > 0 and skill1_level == 0:
                complement_score += skill2_level
            elif skill1_level > 0 and skill2_level > 0:
                # Small penalty for overlap, but still positive
                overlap_penalty += min(skill1_level, skill2_level) * 0.3
        
        total_score = complement_score + overlap_penalty
        max_possible_score = sum(vector1.values()) + sum(vector2.values())
        
        return total_score / max_possible_score if max_possible_score > 0 else 0.0
    
    def _calculate_similarity_score(self, vector1: Dict[str, float], vector2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vector1 or not vector2:
            return 0.0
            
        all_keys = set(vector1.keys()) | set(vector2.keys())
        if not all_keys:
            return 0.0
            
        vec1 = np.array([vector1.get(key, 0.0) for key in all_keys])
        vec2 = np.array([vector2.get(key, 0.0) for key in all_keys])
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def recommend_events_for_user(self, user_id: int, limit: int = 10) -> List[Tuple[Event, float]]:
        """Recommend events for a user based on their profile"""
        try:
            user = User.query.get(user_id)
            if not user:
                return []
                
            # Get user's skill and interest vectors
            user_skills = self.calculate_user_skill_vector(user_id)
            user_interests = self.calculate_user_interest_vector(user_id)
            
            # Get upcoming events
            upcoming_events = Event.query.filter(
                Event.start_date > datetime.utcnow()
            ).all()
            
            event_scores = []
            
            for event in upcoming_events:
                # Skip events user already registered for
                if user.tickets.filter_by(event_id=event.id).first():
                    continue
                    
                score = self._calculate_event_user_match_score(
                    event, user_skills, user_interests, user
                )
                
                if score > 0.1:  # Only recommend events with meaningful score
                    event_scores.append((event, score))
            
            # Sort by score and return top recommendations
            event_scores.sort(key=lambda x: x[1], reverse=True)
            return event_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error generating event recommendations: {e}")
            return []
    
    def _calculate_event_user_match_score(self, event: Event, user_skills: Dict, user_interests: Dict, user: User) -> float:
        """Calculate how well an event matches a user's profile"""
        score = 0.0
        
        # Category interest matching
        if event.category:
            category_name = event.category.value.lower()
            if category_name in user_interests:
                score += user_interests[category_name] * 0.3
        
        # Skill level matching
        if event.skill_level and user_skills:
            avg_user_skill = np.mean(list(user_skills.values()))
            event_skill_value = self.skill_weights.get(event.skill_level, 2.0)
            
            # Prefer events slightly above user's level for growth
            skill_diff = event_skill_value - avg_user_skill
            if -1.0 <= skill_diff <= 1.5:  # Sweet spot for learning
                score += 0.2
        
        # Event tags matching (if available)
        if event.tags:
            try:
                event_tags = json.loads(event.tags)
                for tag in event_tags:
                    tag_lower = tag.lower()
                    if tag_lower in user_skills:
                        score += user_skills[tag_lower] * 0.1
                    if tag_lower in user_interests:
                        score += user_interests[tag_lower] * 0.1
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Past event attendance patterns
        user_past_events = user.tickets.join(Event).filter(
            Event.end_date < datetime.utcnow()
        ).all()
        
        if user_past_events:
            # Boost score for similar event types
            for ticket in user_past_events[-5]:  # Last 5 events
                if ticket.event.category == event.category:
                    score += 0.1
        
        # Boost for events requiring teams if user is social
        if event.requires_team and len(user_past_events) > 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def find_team_matches_for_user(self, user_id: int, event_id: int, limit: int = 5) -> List[Tuple[Team, float]]:
        """Find teams that would be a good match for a user"""
        try:
            event = Event.query.get(event_id)
            if not event or not event.requires_team:
                return []
                
            # Get all teams for this event that aren't full
            available_teams = Team.query.filter(
                Team.event_id == event_id,
                Team.is_public == True
            ).all()
            
            available_teams = [team for team in available_teams if not team.is_full()]
            
            if not available_teams:
                return []
                
            user_skills = self.calculate_user_skill_vector(user_id)
            user_interests = self.calculate_user_interest_vector(user_id)
            
            team_scores = []
            
            for team in available_teams:
                score = self._calculate_team_user_match_score(
                    team, user_skills, user_interests, user_id
                )
                if score > 0.0:
                    team_scores.append((team, score))
            
            team_scores.sort(key=lambda x: x[1], reverse=True)
            return team_scores[:limit]
            
        except Exception as e:
            logger.error(f"Error finding team matches: {e}")
            return []
    
    def _calculate_team_user_match_score(self, team: Team, user_skills: Dict, user_interests: Dict, user_id: int) -> float:
        """Calculate how well a user would fit into a team"""
        score = 0.0
        
        # Get team members' skills and interests
        team_members = team.members.all()
        if not team_members:
            return 0.5  # New team, neutral score
        
        team_skills = {}
        team_interests = {}
        
        for member in team_members:
            member_skills = self.calculate_user_skill_vector(member.user_id)
            member_interests = self.calculate_user_interest_vector(member.user_id)
            
            for skill, level in member_skills.items():
                team_skills[skill] = max(team_skills.get(skill, 0), level)
            
            for interest, weight in member_interests.items():
                team_interests[interest] = team_interests.get(interest, 0) + weight
        
        # Calculate skill complementarity
        complement_score = self._calculate_complementarity_score(user_skills, team_skills)
        score += complement_score * 0.4
        
        # Calculate interest alignment
        interest_score = self._calculate_similarity_score(user_interests, team_interests)
        score += interest_score * 0.3
        
        # Team size factor (prefer teams with 2-4 members)
        team_size = len(team_members)
        if 2 <= team_size <= 4:
            score += 0.2
        elif team_size == 1:
            score += 0.1  # New team, some bonus
        
        # Leader compatibility (if not the leader)
        if team.leader_id != user_id:
            leader_compat = self.calculate_compatibility_score(user_id, team.leader_id)
            score += leader_compat * 0.1
        
        return min(score, 1.0)
    
    def suggest_team_formation(self, event_id: int, max_teams: int = 10) -> List[List[int]]:
        """Suggest optimal team formations for an event"""
        try:
            event = Event.query.get(event_id)
            if not event or not event.requires_team:
                return []
            
            # Get users registered for this event without teams
            registered_users = db.session.query(User).join(Ticket).filter(
                Ticket.event_id == event_id,
                ~User.id.in_(
                    db.session.query(TeamMember.user_id).join(Team).filter(
                        Team.event_id == event_id
                    )
                )
            ).all()
            
            if len(registered_users) < 2:
                return []
            
            # Calculate compatibility matrix
            user_ids = [user.id for user in registered_users]
            n_users = len(user_ids)
            
            compatibility_matrix = np.zeros((n_users, n_users))
            
            for i in range(n_users):
                for j in range(i + 1, n_users):
                    compat = self.calculate_compatibility_score(user_ids[i], user_ids[j])
                    compatibility_matrix[i][j] = compat
                    compatibility_matrix[j][i] = compat
            
            # Use clustering to form teams
            max_team_size = event.max_team_size or 5
            min_team_size = event.min_team_size or 2
            
            optimal_teams = self._form_teams_with_clustering(
                user_ids, compatibility_matrix, min_team_size, max_team_size, max_teams
            )
            
            return optimal_teams
            
        except Exception as e:
            logger.error(f"Error suggesting team formation: {e}")
            return []
    
    def _form_teams_with_clustering(self, user_ids: List[int], compat_matrix: np.ndarray, 
                                  min_size: int, max_size: int, max_teams: int) -> List[List[int]]:
        """Form teams using clustering algorithm"""
        n_users = len(user_ids)
        if n_users < min_size:
            return []
        
        # Estimate number of teams
        n_teams = min(max_teams, max(1, n_users // max_size))
        
        # Use K-means clustering on compatibility matrix
        try:
            # Convert compatibility to distance matrix
            distance_matrix = 1 - compat_matrix
            
            # Apply K-means
            kmeans = KMeans(n_clusters=n_teams, random_state=42)
            cluster_labels = kmeans.fit_predict(distance_matrix)
            
            # Group users by cluster
            teams = []
            for cluster_id in range(n_teams):
                team_members = [user_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                # Only keep teams with minimum size
                if len(team_members) >= min_size:
                    # If team is too large, split it
                    while len(team_members) > max_size:
                        teams.append(team_members[:max_size])
                        team_members = team_members[max_size:]
                    
                    if len(team_members) >= min_size:
                        teams.append(team_members)
            
            return teams
            
        except Exception as e:
            logger.error(f"Clustering failed, using greedy approach: {e}")
            return self._form_teams_greedy(user_ids, compat_matrix, min_size, max_size, max_teams)
    
    def _form_teams_greedy(self, user_ids: List[int], compat_matrix: np.ndarray,
                          min_size: int, max_size: int, max_teams: int) -> List[List[int]]:
        """Fallback greedy team formation algorithm"""
        n_users = len(user_ids)
        used = [False] * n_users
        teams = []
        
        while len(teams) < max_teams and sum(used) < n_users:
            # Find the user with highest average compatibility with unused users
            best_starter = -1
            best_avg_compat = -1
            
            for i in range(n_users):
                if used[i]:
                    continue
                
                avg_compat = np.mean([compat_matrix[i][j] for j in range(n_users) if not used[j] and i != j])
                if avg_compat > best_avg_compat:
                    best_avg_compat = avg_compat
                    best_starter = i
            
            if best_starter == -1:
                break
                
            # Build team starting with best_starter
            team = [user_ids[best_starter]]
            used[best_starter] = True
            
            # Add compatible users to the team
            while len(team) < max_size:
                best_addition = -1
                best_team_compat = -1
                
                for i in range(n_users):
                    if used[i]:
                        continue
                    
                    # Calculate average compatibility with current team members
                    team_compat = np.mean([compat_matrix[best_starter][i] for best_starter in [user_ids.index(uid) for uid in team]])
                    
                    if team_compat > best_team_compat:
                        best_team_compat = team_compat
                        best_addition = i
                
                if best_addition == -1 or best_team_compat < 0.3:  # Minimum compatibility threshold
                    break
                    
                team.append(user_ids[best_addition])
                used[best_addition] = True
            
            if len(team) >= min_size:
                teams.append(team)
        
        return teams
    
    def store_recommendation(self, user_id: int, event_id: int, rec_type: str, score: float, reason: str):
        """Store an AI recommendation in the database"""
        try:
            recommendation = AIRecommendation(
                user_id=user_id,
                event_id=event_id,
                recommendation_type=rec_type,
                score=score,
                reason=reason
            )
            db.session.add(recommendation)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error storing recommendation: {e}")
            db.session.rollback()
    
    def update_user_profile_from_activity(self, user_id: int):
        """Update user's interests and skills based on their activity"""
        try:
            user = User.query.get(user_id)
            if not user:
                return
            
            # Analyze attended events to infer interests
            attended_events = user.tickets.join(Event).filter(
                Event.end_date < datetime.utcnow()
            ).all()
            
            category_counts = {}
            for ticket in attended_events:
                event = ticket.event
                category = event.category.value if event.category else 'Other'
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Update interests based on event attendance
            for category, count in category_counts.items():
                interest = UserInterest.query.filter_by(
                    user_id=user_id, 
                    interest=category
                ).first()
                
                weight = min(count * 0.2, 2.0)  # Cap weight at 2.0
                
                if interest:
                    interest.weight = max(interest.weight, weight)
                else:
                    new_interest = UserInterest(
                        user_id=user_id,
                        interest=category,
                        weight=weight
                    )
                    db.session.add(new_interest)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            db.session.rollback()


# Global AI engine instance
ai_engine = AIMatchingEngine()


def get_user_recommendations(user_id: int, limit: int = 5) -> List[Dict]:
    """Get formatted recommendations for a user"""
    try:
        recommendations = ai_engine.recommend_events_for_user(user_id, limit)
        
        formatted_recs = []
        for event, score in recommendations:
            formatted_recs.append({
                'event': event,
                'score': score,
                'confidence': 'High' if score > 0.7 else 'Medium' if score > 0.4 else 'Low',
                'reason': f"Based on your skills and interests (Match: {score:.1%})"
            })
        
        return formatted_recs
    except Exception as e:
        logger.error(f"Error getting user recommendations: {e}")
        return []


def get_team_suggestions(user_id: int, event_id: int, limit: int = 3) -> List[Dict]:
    """Get formatted team suggestions for a user"""
    try:
        suggestions = ai_engine.find_team_matches_for_user(user_id, event_id, limit)
        
        formatted_suggestions = []
        for team, score in suggestions:
            formatted_suggestions.append({
                'team': team,
                'score': score,
                'confidence': 'High' if score > 0.7 else 'Medium' if score > 0.4 else 'Low',
                'reason': f"Good skill complementarity and interests alignment (Match: {score:.1%})"
            })
        
        return formatted_suggestions
    except Exception as e:
        logger.error(f"Error getting team suggestions: {e}")
        return []