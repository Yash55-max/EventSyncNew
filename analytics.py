"""
Advanced Analytics Dashboard for Revolutionary Event Management Platform
Comprehensive analytics, predictive modeling, and interactive reporting
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict, Counter

from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from app import db
from models import (
    Event, User, Ticket, EventAnalytics, EventFeedback, Team, TeamMember,
    UserSkill, UserInterest, Badge, UserBadge, SustainabilityMetric,
    EventCategory, EventType, TicketStatus, UserType
)

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of analytics metrics"""
    ATTENDANCE = "attendance"
    ENGAGEMENT = "engagement" 
    REVENUE = "revenue"
    SATISFACTION = "satisfaction"
    SOCIAL = "social"
    PERFORMANCE = "performance"
    SUSTAINABILITY = "sustainability"
    PREDICTIVE = "predictive"

class TimeRange(Enum):
    """Time ranges for analytics"""
    LAST_24H = "last_24h"
    LAST_7D = "last_7d"
    LAST_30D = "last_30d"
    LAST_90D = "last_90d"
    LAST_YEAR = "last_year"
    ALL_TIME = "all_time"
    CUSTOM = "custom"

@dataclass
class AnalyticsQuery:
    """Analytics query parameters"""
    metric_types: List[MetricType]
    time_range: TimeRange
    event_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None
    categories: Optional[List[EventCategory]] = None
    custom_start: Optional[datetime] = None
    custom_end: Optional[datetime] = None
    granularity: str = "day"  # hour, day, week, month
    include_predictions: bool = False

@dataclass
class MetricResult:
    """Analytics metric result"""
    metric_type: MetricType
    value: float
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    metadata: Optional[Dict] = None

@dataclass
class AnalyticsReport:
    """Comprehensive analytics report"""
    metrics: List[MetricResult]
    charts: List[Dict]
    insights: List[str]
    recommendations: List[str]
    generated_at: datetime
    query: AnalyticsQuery

class AnalyticsEngine:
    """
    Main analytics engine for comprehensive event data analysis
    """
    
    def __init__(self):
        self.ml_models = {}
        self.cache = {}
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize machine learning models for predictive analytics"""
        self.ml_models = {
            'attendance_predictor': LinearRegression(),
            'engagement_predictor': LinearRegression(),
            'revenue_predictor': LinearRegression(),
            'satisfaction_predictor': LinearRegression(),
            'churn_predictor': LinearRegression()
        }
    
    async def generate_report(self, query: AnalyticsQuery) -> AnalyticsReport:
        """Generate comprehensive analytics report"""
        try:
            # Validate query
            self._validate_query(query)
            
            # Get time bounds
            start_time, end_time = self._get_time_bounds(query)
            
            # Calculate metrics
            metrics = []
            
            for metric_type in query.metric_types:
                metric = await self._calculate_metric(
                    metric_type, start_time, end_time, query
                )
                if metric:
                    metrics.append(metric)
            
            # Generate charts
            charts = await self._generate_charts(metrics, query)
            
            # Generate insights
            insights = await self._generate_insights(metrics, query)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(metrics, query)
            
            # Create report
            report = AnalyticsReport(
                metrics=metrics,
                charts=charts,
                insights=insights,
                recommendations=recommendations,
                generated_at=datetime.utcnow(),
                query=query
            )
            
            logger.info(f"Generated analytics report with {len(metrics)} metrics")
            return report
            
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            raise
    
    async def _calculate_metric(self, metric_type: MetricType, start_time: datetime, 
                               end_time: datetime, query: AnalyticsQuery) -> Optional[MetricResult]:
        """Calculate specific metric"""
        try:
            if metric_type == MetricType.ATTENDANCE:
                return await self._calculate_attendance_metrics(start_time, end_time, query)
            elif metric_type == MetricType.ENGAGEMENT:
                return await self._calculate_engagement_metrics(start_time, end_time, query)
            elif metric_type == MetricType.REVENUE:
                return await self._calculate_revenue_metrics(start_time, end_time, query)
            elif metric_type == MetricType.SATISFACTION:
                return await self._calculate_satisfaction_metrics(start_time, end_time, query)
            elif metric_type == MetricType.SOCIAL:
                return await self._calculate_social_metrics(start_time, end_time, query)
            elif metric_type == MetricType.PERFORMANCE:
                return await self._calculate_performance_metrics(start_time, end_time, query)
            elif metric_type == MetricType.SUSTAINABILITY:
                return await self._calculate_sustainability_metrics(start_time, end_time, query)
            elif metric_type == MetricType.PREDICTIVE:
                return await self._calculate_predictive_metrics(start_time, end_time, query)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating {metric_type} metric: {e}")
            return None
    
    async def _calculate_attendance_metrics(self, start_time: datetime, 
                                          end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate attendance-related metrics"""
        try:
            # Base query for events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            # Apply filters
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            # Calculate attendance metrics
            total_tickets = Ticket.query.filter(
                Ticket.event_id.in_(event_ids),
                Ticket.status == TicketStatus.PAID
            ).count()
            
            total_capacity = sum(e.max_attendees or 1000 for e in events if e.max_attendees > 0)
            total_events = len(events)
            
            # Calculate attendance rate
            attendance_rate = (total_tickets / total_capacity * 100) if total_capacity > 0 else 0
            
            # Calculate previous period for comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            prev_event_ids = [e.id for e in prev_events]
            
            prev_tickets = Ticket.query.filter(
                Ticket.event_id.in_(prev_event_ids),
                Ticket.status == TicketStatus.PAID
            ).count()
            
            # Calculate change percentage
            change_pct = None
            trend = None
            if prev_tickets > 0:
                change_pct = ((total_tickets - prev_tickets) / prev_tickets) * 100
                trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"
            
            # Additional metrics
            avg_attendance_per_event = total_tickets / total_events if total_events > 0 else 0
            
            # No-show rate calculation (simplified)
            no_shows = Ticket.query.filter(
                Ticket.event_id.in_(event_ids),
                Ticket.status == TicketStatus.CANCELLED
            ).count()
            
            no_show_rate = (no_shows / (total_tickets + no_shows) * 100) if (total_tickets + no_shows) > 0 else 0
            
            return MetricResult(
                metric_type=MetricType.ATTENDANCE,
                value=total_tickets,
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "attendance_rate": round(attendance_rate, 2),
                    "total_capacity": total_capacity,
                    "avg_attendance_per_event": round(avg_attendance_per_event, 2),
                    "no_show_rate": round(no_show_rate, 2),
                    "total_events": total_events
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating attendance metrics: {e}")
            return None
    
    async def _calculate_engagement_metrics(self, start_time: datetime, 
                                          end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate engagement-related metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            if not event_ids:
                return MetricResult(metric_type=MetricType.ENGAGEMENT, value=0)
            
            # Calculate engagement score based on various factors
            total_engagement_score = 0
            total_events = len(events)
            
            for event in events:
                event_score = 0
                
                # Ticket sales engagement (normalized)
                tickets_sold = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                capacity = event.max_attendees or 100
                sales_score = min(tickets_sold / capacity * 100, 100) if capacity > 0 else 0
                event_score += sales_score * 0.3
                
                # Feedback engagement
                feedback_count = EventFeedback.query.filter_by(event_id=event.id).count()
                feedback_score = min(feedback_count / max(tickets_sold, 1) * 100, 100)
                event_score += feedback_score * 0.2
                
                # Team formation engagement (for hackathons)
                if event.requires_team:
                    teams_count = Team.query.filter_by(event_id=event.id).count()
                    team_score = min(teams_count / max(tickets_sold // 4, 1) * 100, 100)
                    event_score += team_score * 0.2
                
                # Social engagement (badges, interactions)
                badges_earned = UserBadge.query.filter_by(event_id=event.id).count()
                badge_score = min(badges_earned / max(tickets_sold, 1) * 100, 100)
                event_score += badge_score * 0.15
                
                # Time-based engagement (event duration attendance)
                duration_hours = (event.end_date - event.start_date).total_seconds() / 3600
                duration_score = min(duration_hours / 8 * 100, 100)  # 8 hours = perfect score
                event_score += duration_score * 0.15
                
                total_engagement_score += event_score
            
            avg_engagement = total_engagement_score / total_events if total_events > 0 else 0
            
            # Calculate previous period comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            
            # Calculate previous engagement (simplified)
            prev_engagement = 0
            if prev_events:
                prev_tickets = sum(e.tickets.filter(Ticket.status == TicketStatus.PAID).count() for e in prev_events)
                prev_feedback = sum(EventFeedback.query.filter_by(event_id=e.id).count() for e in prev_events)
                prev_engagement = (prev_feedback / max(prev_tickets, 1)) * 100
            
            change_pct = None
            trend = None
            if prev_engagement > 0:
                change_pct = ((avg_engagement - prev_engagement) / prev_engagement) * 100
                trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"
            
            return MetricResult(
                metric_type=MetricType.ENGAGEMENT,
                value=round(avg_engagement, 2),
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "total_events": total_events,
                    "avg_feedback_rate": round(sum(EventFeedback.query.filter_by(event_id=e.id).count() 
                                                 for e in events) / max(sum(e.tickets.filter(Ticket.status == TicketStatus.PAID).count() 
                                                                           for e in events), 1) * 100, 2),
                    "team_formation_rate": round(sum(Team.query.filter_by(event_id=e.id).count() 
                                                   for e in events if e.requires_team) / max(len([e for e in events if e.requires_team]), 1), 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return None
    
    async def _calculate_revenue_metrics(self, start_time: datetime, 
                                       end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate revenue-related metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            # Calculate total revenue
            total_revenue = 0
            total_tickets = 0
            
            for event in events:
                paid_tickets = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                event_revenue = paid_tickets * (event.price or 0)
                total_revenue += event_revenue
                total_tickets += paid_tickets
            
            # Calculate previous period for comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            
            prev_revenue = 0
            for event in prev_events:
                paid_tickets = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                prev_revenue += paid_tickets * (event.price or 0)
            
            # Calculate metrics
            change_pct = None
            trend = None
            if prev_revenue > 0:
                change_pct = ((total_revenue - prev_revenue) / prev_revenue) * 100
                trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"
            
            avg_ticket_price = total_revenue / total_tickets if total_tickets > 0 else 0
            avg_revenue_per_event = total_revenue / len(events) if events else 0
            
            # Revenue by category
            revenue_by_category = {}
            for event in events:
                category = event.category.value if event.category else "Other"
                paid_tickets = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                category_revenue = paid_tickets * (event.price or 0)
                revenue_by_category[category] = revenue_by_category.get(category, 0) + category_revenue
            
            return MetricResult(
                metric_type=MetricType.REVENUE,
                value=total_revenue,
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "total_tickets_sold": total_tickets,
                    "avg_ticket_price": round(avg_ticket_price, 2),
                    "avg_revenue_per_event": round(avg_revenue_per_event, 2),
                    "revenue_by_category": {k: round(v, 2) for k, v in revenue_by_category.items()},
                    "total_events": len(events)
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return None
    
    async def _calculate_satisfaction_metrics(self, start_time: datetime, 
                                            end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate satisfaction-related metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            if not event_ids:
                return MetricResult(metric_type=MetricType.SATISFACTION, value=0)
            
            # Get all feedback for events
            feedback_query = EventFeedback.query.filter(EventFeedback.event_id.in_(event_ids))
            feedback_records = feedback_query.all()
            
            if not feedback_records:
                return MetricResult(metric_type=MetricType.SATISFACTION, value=0)
            
            # Calculate average rating
            total_rating = sum(f.rating for f in feedback_records)
            avg_rating = total_rating / len(feedback_records)
            
            # Calculate rating distribution
            rating_distribution = Counter(f.rating for f in feedback_records)
            
            # Calculate satisfaction score (0-100 scale)
            satisfaction_score = (avg_rating / 5.0) * 100
            
            # Calculate Net Promoter Score (NPS) - simplified
            # Ratings 4-5 = Promoters, 3 = Neutral, 1-2 = Detractors
            promoters = sum(1 for f in feedback_records if f.rating >= 4)
            detractors = sum(1 for f in feedback_records if f.rating <= 2)
            total_responses = len(feedback_records)
            
            nps = ((promoters - detractors) / total_responses * 100) if total_responses > 0 else 0
            
            # Calculate previous period comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            prev_event_ids = [e.id for e in prev_events]
            
            prev_feedback = EventFeedback.query.filter(EventFeedback.event_id.in_(prev_event_ids)).all()
            
            change_pct = None
            trend = None
            if prev_feedback:
                prev_avg_rating = sum(f.rating for f in prev_feedback) / len(prev_feedback)
                prev_satisfaction = (prev_avg_rating / 5.0) * 100
                change_pct = ((satisfaction_score - prev_satisfaction) / prev_satisfaction) * 100
                trend = "up" if change_pct > 2 else "down" if change_pct < -2 else "stable"
            
            # Satisfaction by category
            satisfaction_by_category = {}
            for event in events:
                category = event.category.value if event.category else "Other"
                event_feedback = [f for f in feedback_records if f.event_id == event.id]
                if event_feedback:
                    category_avg = sum(f.rating for f in event_feedback) / len(event_feedback)
                    satisfaction_by_category[category] = (category_avg / 5.0) * 100
            
            return MetricResult(
                metric_type=MetricType.SATISFACTION,
                value=round(satisfaction_score, 2),
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "average_rating": round(avg_rating, 2),
                    "total_responses": total_responses,
                    "response_rate": round((total_responses / sum(e.tickets.filter(Ticket.status == TicketStatus.PAID).count() 
                                                                for e in events)) * 100, 2) if events else 0,
                    "nps_score": round(nps, 2),
                    "rating_distribution": dict(rating_distribution),
                    "satisfaction_by_category": {k: round(v, 2) for k, v in satisfaction_by_category.items()}
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating satisfaction metrics: {e}")
            return None
    
    async def _calculate_social_metrics(self, start_time: datetime, 
                                      end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate social interaction metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            if not event_ids:
                return MetricResult(metric_type=MetricType.SOCIAL, value=0)
            
            # Calculate social metrics
            total_teams = Team.query.filter(Team.event_id.in_(event_ids)).count()
            total_team_members = TeamMember.query.join(Team).filter(Team.event_id.in_(event_ids)).count()
            total_badges_earned = UserBadge.query.filter(UserBadge.event_id.in_(event_ids)).count()
            
            # Get unique participants across all events
            unique_participants = set()
            for event in events:
                participants = [t.attendee_id for t in event.tickets.filter(Ticket.status == TicketStatus.PAID)]
                unique_participants.update(participants)
            
            total_participants = len(unique_participants)
            
            # Calculate social engagement rate
            social_engagement_rate = 0
            if total_participants > 0:
                socially_active_users = set()
                
                # Users in teams
                team_members = TeamMember.query.join(Team).filter(Team.event_id.in_(event_ids)).all()
                socially_active_users.update(tm.user_id for tm in team_members)
                
                # Users who earned badges
                badge_earners = UserBadge.query.filter(UserBadge.event_id.in_(event_ids)).all()
                socially_active_users.update(ub.user_id for ub in badge_earners)
                
                # Users who gave feedback
                feedback_givers = EventFeedback.query.filter(EventFeedback.event_id.in_(event_ids)).all()
                socially_active_users.update(fb.user_id for fb in feedback_givers)
                
                social_engagement_rate = (len(socially_active_users) / total_participants) * 100
            
            # Team formation rate (for events that support teams)
            team_events = [e for e in events if e.requires_team]
            team_formation_rate = 0
            if team_events:
                team_event_participants = 0
                for event in team_events:
                    team_event_participants += event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                
                if team_event_participants > 0:
                    team_formation_rate = (total_team_members / team_event_participants) * 100
            
            # Calculate networking score
            avg_team_size = total_team_members / total_teams if total_teams > 0 else 0
            networking_score = min(social_engagement_rate + (avg_team_size * 10), 100)
            
            # Previous period comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            prev_event_ids = [e.id for e in prev_events]
            
            prev_teams = Team.query.filter(Team.event_id.in_(prev_event_ids)).count()
            prev_badges = UserBadge.query.filter(UserBadge.event_id.in_(prev_event_ids)).count()
            
            change_pct = None
            trend = None
            prev_social_activity = prev_teams + prev_badges
            current_social_activity = total_teams + total_badges_earned
            
            if prev_social_activity > 0:
                change_pct = ((current_social_activity - prev_social_activity) / prev_social_activity) * 100
                trend = "up" if change_pct > 10 else "down" if change_pct < -10 else "stable"
            
            return MetricResult(
                metric_type=MetricType.SOCIAL,
                value=round(networking_score, 2),
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "total_teams": total_teams,
                    "total_team_members": total_team_members,
                    "avg_team_size": round(avg_team_size, 2),
                    "total_badges_earned": total_badges_earned,
                    "social_engagement_rate": round(social_engagement_rate, 2),
                    "team_formation_rate": round(team_formation_rate, 2),
                    "total_participants": total_participants
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating social metrics: {e}")
            return None
    
    async def _calculate_performance_metrics(self, start_time: datetime, 
                                           end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate performance-related metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            
            if not events:
                return MetricResult(metric_type=MetricType.PERFORMANCE, value=0)
            
            # Calculate overall performance score
            total_performance_score = 0
            total_events = len(events)
            
            for event in events:
                event_score = 0
                
                # Registration performance (capacity utilization)
                tickets_sold = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                capacity = event.max_attendees or 100
                utilization_score = min((tickets_sold / capacity) * 100, 100) if capacity > 0 else 0
                event_score += utilization_score * 0.3
                
                # Time to sell out (if applicable)
                if tickets_sold >= capacity:
                    # Event sold out - bonus points
                    event_score += 20
                
                # Feedback quality score
                feedback_records = EventFeedback.query.filter_by(event_id=event.id).all()
                if feedback_records:
                    avg_rating = sum(f.rating for f in feedback_records) / len(feedback_records)
                    feedback_score = (avg_rating / 5.0) * 100
                    event_score += feedback_score * 0.25
                
                # Team collaboration score (for team events)
                if event.requires_team:
                    teams = Team.query.filter_by(event_id=event.id).all()
                    if teams:
                        avg_team_members = sum(t.members.count() for t in teams) / len(teams)
                        optimal_team_size = event.max_team_size or 5
                        team_score = min((avg_team_members / optimal_team_size) * 100, 100)
                        event_score += team_score * 0.2
                
                # Innovation/engagement score (badges, interactions)
                badges_earned = UserBadge.query.filter_by(event_id=event.id).count()
                innovation_score = min((badges_earned / max(tickets_sold, 1)) * 100, 100)
                event_score += innovation_score * 0.15
                
                # Sustainability score
                sustainability_metrics = SustainabilityMetric.query.filter_by(event_id=event.id).all()
                if sustainability_metrics:
                    # Higher sustainability scores are better
                    avg_sustainability = sum(m.value for m in sustainability_metrics) / len(sustainability_metrics)
                    sustainability_score = min(avg_sustainability, 100)
                    event_score += sustainability_score * 0.1
                
                total_performance_score += min(event_score, 100)  # Cap at 100
            
            avg_performance = total_performance_score / total_events
            
            # Calculate category performance
            performance_by_category = {}
            category_counts = Counter()
            
            for event in events:
                category = event.category.value if event.category else "Other"
                category_counts[category] += 1
                
                # Simplified performance calculation per event
                tickets_sold = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                capacity = event.max_attendees or 100
                utilization = min((tickets_sold / capacity) * 100, 100) if capacity > 0 else 0
                
                if category not in performance_by_category:
                    performance_by_category[category] = 0
                performance_by_category[category] += utilization
            
            # Average performance by category
            for category, total_score in performance_by_category.items():
                performance_by_category[category] = total_score / category_counts[category]
            
            # Previous period comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            
            # Simplified previous performance calculation
            prev_performance = 0
            if prev_events:
                prev_total_utilization = 0
                for event in prev_events:
                    tickets_sold = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                    capacity = event.max_attendees or 100
                    utilization = min((tickets_sold / capacity) * 100, 100) if capacity > 0 else 0
                    prev_total_utilization += utilization
                prev_performance = prev_total_utilization / len(prev_events)
            
            change_pct = None
            trend = None
            if prev_performance > 0:
                change_pct = ((avg_performance - prev_performance) / prev_performance) * 100
                trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"
            
            return MetricResult(
                metric_type=MetricType.PERFORMANCE,
                value=round(avg_performance, 2),
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "total_events": total_events,
                    "avg_capacity_utilization": round(sum(min((e.tickets.filter(Ticket.status == TicketStatus.PAID).count() / 
                                                             (e.max_attendees or 100)) * 100, 100) for e in events) / total_events, 2),
                    "events_sold_out": sum(1 for e in events if e.tickets.filter(Ticket.status == TicketStatus.PAID).count() >= 
                                         (e.max_attendees or float('inf'))),
                    "performance_by_category": {k: round(v, 2) for k, v in performance_by_category.items()},
                    "avg_satisfaction": round(sum(sum(f.rating for f in EventFeedback.query.filter_by(event_id=e.id).all()) / 
                                                max(EventFeedback.query.filter_by(event_id=e.id).count(), 1) for e in events) / total_events, 2)
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return None
    
    async def _calculate_sustainability_metrics(self, start_time: datetime, 
                                              end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate sustainability-related metrics"""
        try:
            # Get events in time range
            events_query = Event.query.filter(
                Event.start_date >= start_time,
                Event.start_date <= end_time
            )
            
            if query.event_ids:
                events_query = events_query.filter(Event.id.in_(query.event_ids))
            if query.categories:
                events_query = events_query.filter(Event.category.in_(query.categories))
            
            events = events_query.all()
            event_ids = [e.id for e in events]
            
            if not event_ids:
                return MetricResult(metric_type=MetricType.SUSTAINABILITY, value=0)
            
            # Get sustainability metrics for events
            sustainability_records = SustainabilityMetric.query.filter(
                SustainabilityMetric.event_id.in_(event_ids)
            ).all()
            
            # Calculate total carbon footprint
            carbon_footprint_records = [s for s in sustainability_records if s.metric_type == 'carbon_footprint']
            total_carbon_footprint = sum(s.value for s in carbon_footprint_records)
            
            # Calculate average sustainability score per event
            sustainability_scores = []
            for event in events:
                event_metrics = [s for s in sustainability_records if s.event_id == event.id]
                
                if event_metrics:
                    # Higher values are better for most sustainability metrics
                    event_score = sum(s.value for s in event_metrics) / len(event_metrics)
                    sustainability_scores.append(event_score)
                else:
                    # Default score for events without sustainability data
                    sustainability_scores.append(50)  # Neutral score
            
            avg_sustainability_score = sum(sustainability_scores) / len(sustainability_scores) if sustainability_scores else 0
            
            # Calculate sustainability by event type
            sustainability_by_type = {}
            virtual_events = [e for e in events if e.event_type == EventType.VIRTUAL]
            hybrid_events = [e for e in events if e.event_type == EventType.HYBRID]
            in_person_events = [e for e in events if e.event_type == EventType.IN_PERSON]
            
            # Virtual events have lower carbon footprint
            if virtual_events:
                virtual_carbon = sum(e.carbon_footprint or 0 for e in virtual_events) / len(virtual_events)
                sustainability_by_type['Virtual'] = max(100 - (virtual_carbon / 10), 50)  # Invert carbon footprint
            
            if hybrid_events:
                hybrid_carbon = sum(e.carbon_footprint or 0 for e in hybrid_events) / len(hybrid_events)
                sustainability_by_type['Hybrid'] = max(100 - (hybrid_carbon / 8), 40)
            
            if in_person_events:
                in_person_carbon = sum(e.carbon_footprint or 0 for e in in_person_events) / len(in_person_events)
                sustainability_by_type['In-Person'] = max(100 - (in_person_carbon / 5), 30)
            
            # Calculate green initiatives adoption
            events_with_sustainability_data = len([e for e in events if any(s.event_id == e.id for s in sustainability_records)])
            sustainability_adoption_rate = (events_with_sustainability_data / len(events)) * 100 if events else 0
            
            # Previous period comparison
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_events = Event.query.filter(
                Event.start_date >= prev_start,
                Event.start_date <= prev_end
            )
            
            if query.event_ids:
                prev_events = prev_events.filter(Event.id.in_(query.event_ids))
            if query.categories:
                prev_events = prev_events.filter(Event.category.in_(query.categories))
            
            prev_events = prev_events.all()
            prev_event_ids = [e.id for e in prev_events]
            
            prev_sustainability_records = SustainabilityMetric.query.filter(
                SustainabilityMetric.event_id.in_(prev_event_ids)
            ).all()
            
            prev_carbon_footprint = sum(s.value for s in prev_sustainability_records 
                                      if s.metric_type == 'carbon_footprint')
            
            change_pct = None
            trend = None
            if prev_carbon_footprint > 0 and total_carbon_footprint > 0:
                # For carbon footprint, reduction is good
                change_pct = ((prev_carbon_footprint - total_carbon_footprint) / prev_carbon_footprint) * 100
                trend = "up" if change_pct > 5 else "down" if change_pct < -5 else "stable"
            
            return MetricResult(
                metric_type=MetricType.SUSTAINABILITY,
                value=round(avg_sustainability_score, 2),
                change_percentage=change_pct,
                trend=trend,
                metadata={
                    "total_carbon_footprint": round(total_carbon_footprint, 2),
                    "avg_carbon_per_event": round(total_carbon_footprint / len(events), 2) if events else 0,
                    "sustainability_adoption_rate": round(sustainability_adoption_rate, 2),
                    "sustainability_by_type": {k: round(v, 2) for k, v in sustainability_by_type.items()},
                    "virtual_events_count": len(virtual_events),
                    "hybrid_events_count": len(hybrid_events),
                    "in_person_events_count": len(in_person_events),
                    "total_events": len(events)
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating sustainability metrics: {e}")
            return None
    
    async def _calculate_predictive_metrics(self, start_time: datetime, 
                                          end_time: datetime, query: AnalyticsQuery) -> MetricResult:
        """Calculate predictive analytics metrics"""
        try:
            # This is a simplified predictive analytics implementation
            # In a real system, you'd use more sophisticated ML models
            
            # Get historical data for prediction
            historical_events = Event.query.filter(Event.start_date <= end_time).all()
            
            if len(historical_events) < 10:  # Need minimum data for predictions
                return MetricResult(
                    metric_type=MetricType.PREDICTIVE,
                    value=0,
                    metadata={"message": "Insufficient historical data for predictions"}
                )
            
            # Prepare data for ML models
            features = []
            attendance_targets = []
            revenue_targets = []
            satisfaction_targets = []
            
            for event in historical_events:
                # Features: [category_encoded, price, capacity, duration_hours, is_virtual]
                category_encoded = hash(event.category.value if event.category else "Other") % 10
                price = event.price or 0
                capacity = event.max_attendees or 100
                duration_hours = (event.end_date - event.start_date).total_seconds() / 3600
                is_virtual = 1 if event.event_type == EventType.VIRTUAL else 0
                
                feature_vector = [category_encoded, price, capacity, duration_hours, is_virtual]
                
                # Targets
                attendance = event.tickets.filter(Ticket.status == TicketStatus.PAID).count()
                revenue = attendance * price
                feedback_records = EventFeedback.query.filter_by(event_id=event.id).all()
                avg_satisfaction = sum(f.rating for f in feedback_records) / len(feedback_records) if feedback_records else 3.0
                
                features.append(feature_vector)
                attendance_targets.append(attendance)
                revenue_targets.append(revenue)
                satisfaction_targets.append(avg_satisfaction)
            
            # Convert to numpy arrays
            X = np.array(features)
            y_attendance = np.array(attendance_targets)
            y_revenue = np.array(revenue_targets)
            y_satisfaction = np.array(satisfaction_targets)
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train models
            attendance_model = LinearRegression()
            revenue_model = LinearRegression()
            satisfaction_model = LinearRegression()
            
            attendance_model.fit(X_scaled, y_attendance)
            revenue_model.fit(X_scaled, y_revenue)
            satisfaction_model.fit(X_scaled, y_satisfaction)
            
            # Make predictions for future events (next 30 days)
            future_start = end_time
            future_end = end_time + timedelta(days=30)
            
            future_events = Event.query.filter(
                Event.start_date >= future_start,
                Event.start_date <= future_end
            ).all()
            
            predictions = {
                "attendance_forecast": [],
                "revenue_forecast": [],
                "satisfaction_forecast": [],
                "total_predicted_attendance": 0,
                "total_predicted_revenue": 0,
                "avg_predicted_satisfaction": 0
            }
            
            for event in future_events:
                # Prepare features for prediction
                category_encoded = hash(event.category.value if event.category else "Other") % 10
                price = event.price or 0
                capacity = event.max_attendees or 100
                duration_hours = (event.end_date - event.start_date).total_seconds() / 3600
                is_virtual = 1 if event.event_type == EventType.VIRTUAL else 0
                
                feature_vector = np.array([[category_encoded, price, capacity, duration_hours, is_virtual]])
                feature_vector_scaled = scaler.transform(feature_vector)
                
                # Make predictions
                pred_attendance = max(0, attendance_model.predict(feature_vector_scaled)[0])
                pred_revenue = max(0, revenue_model.predict(feature_vector_scaled)[0])
                pred_satisfaction = min(5, max(1, satisfaction_model.predict(feature_vector_scaled)[0]))
                
                predictions["attendance_forecast"].append({
                    "event_id": event.id,
                    "event_title": event.title,
                    "predicted_attendance": round(pred_attendance),
                    "predicted_revenue": round(pred_revenue, 2),
                    "predicted_satisfaction": round(pred_satisfaction, 1)
                })
                
                predictions["total_predicted_attendance"] += pred_attendance
                predictions["total_predicted_revenue"] += pred_revenue
                predictions["avg_predicted_satisfaction"] += pred_satisfaction
            
            if future_events:
                predictions["avg_predicted_satisfaction"] /= len(future_events)
            
            # Calculate model accuracy (simplified)
            attendance_accuracy = r2_score(y_attendance, attendance_model.predict(X_scaled)) * 100
            revenue_accuracy = r2_score(y_revenue, revenue_model.predict(X_scaled)) * 100
            satisfaction_accuracy = r2_score(y_satisfaction, satisfaction_model.predict(X_scaled)) * 100
            
            overall_accuracy = (attendance_accuracy + revenue_accuracy + satisfaction_accuracy) / 3
            
            # Generate insights
            insights = []
            
            if predictions["total_predicted_attendance"] > 0:
                insights.append(f"Predicted {int(predictions['total_predicted_attendance'])} total attendees for upcoming events")
                
            if predictions["total_predicted_revenue"] > 0:
                insights.append(f"Forecasted revenue of ${predictions['total_predicted_revenue']:,.2f} for next 30 days")
                
            if predictions["avg_predicted_satisfaction"] > 0:
                satisfaction_level = "excellent" if predictions["avg_predicted_satisfaction"] >= 4.5 else \
                                  "good" if predictions["avg_predicted_satisfaction"] >= 3.5 else "average"
                insights.append(f"Expected {satisfaction_level} satisfaction levels (avg: {predictions['avg_predicted_satisfaction']:.1f}/5)")
            
            return MetricResult(
                metric_type=MetricType.PREDICTIVE,
                value=round(overall_accuracy, 2),
                trend="up" if overall_accuracy > 70 else "stable" if overall_accuracy > 50 else "down",
                metadata={
                    "model_accuracy": round(overall_accuracy, 2),
                    "attendance_accuracy": round(attendance_accuracy, 2),
                    "revenue_accuracy": round(revenue_accuracy, 2),
                    "satisfaction_accuracy": round(satisfaction_accuracy, 2),
                    "predictions": predictions,
                    "insights": insights,
                    "future_events_count": len(future_events),
                    "training_events_count": len(historical_events)
                }
            )
            
        except Exception as e:
            logger.error(f"Error calculating predictive metrics: {e}")
            return MetricResult(
                metric_type=MetricType.PREDICTIVE,
                value=0,
                metadata={"error": str(e)}
            )
    
    async def _generate_charts(self, metrics: List[MetricResult], query: AnalyticsQuery) -> List[Dict]:
        """Generate chart configurations for analytics data"""
        charts = []
        
        try:
            # Attendance chart
            attendance_metric = next((m for m in metrics if m.metric_type == MetricType.ATTENDANCE), None)
            if attendance_metric:
                charts.append({
                    "type": "line",
                    "title": "Attendance Trends",
                    "data": {
                        "labels": self._generate_time_labels(query),
                        "datasets": [{
                            "label": "Total Attendance",
                            "data": [attendance_metric.value],
                            "borderColor": "#3498db",
                            "backgroundColor": "rgba(52, 152, 219, 0.1)"
                        }]
                    }
                })
            
            # Revenue chart
            revenue_metric = next((m for m in metrics if m.metric_type == MetricType.REVENUE), None)
            if revenue_metric:
                charts.append({
                    "type": "bar",
                    "title": "Revenue by Category",
                    "data": {
                        "labels": list(revenue_metric.metadata.get("revenue_by_category", {}).keys()),
                        "datasets": [{
                            "label": "Revenue ($)",
                            "data": list(revenue_metric.metadata.get("revenue_by_category", {}).values()),
                            "backgroundColor": ["#e74c3c", "#f39c12", "#2ecc71", "#9b59b6", "#1abc9c"]
                        }]
                    }
                })
            
            # Satisfaction chart
            satisfaction_metric = next((m for m in metrics if m.metric_type == MetricType.SATISFACTION), None)
            if satisfaction_metric:
                rating_dist = satisfaction_metric.metadata.get("rating_distribution", {})
                charts.append({
                    "type": "doughnut",
                    "title": "Satisfaction Rating Distribution",
                    "data": {
                        "labels": [f"{k} Stars" for k in sorted(rating_dist.keys())],
                        "datasets": [{
                            "data": [rating_dist[k] for k in sorted(rating_dist.keys())],
                            "backgroundColor": ["#e74c3c", "#f39c12", "#f1c40f", "#2ecc71", "#27ae60"]
                        }]
                    }
                })
            
            # Performance comparison chart
            performance_metric = next((m for m in metrics if m.metric_type == MetricType.PERFORMANCE), None)
            if performance_metric:
                perf_by_cat = performance_metric.metadata.get("performance_by_category", {})
                charts.append({
                    "type": "radar",
                    "title": "Performance by Category",
                    "data": {
                        "labels": list(perf_by_cat.keys()),
                        "datasets": [{
                            "label": "Performance Score",
                            "data": list(perf_by_cat.values()),
                            "borderColor": "#9b59b6",
                            "backgroundColor": "rgba(155, 89, 182, 0.2)"
                        }]
                    }
                })
            
            # Sustainability trends
            sustainability_metric = next((m for m in metrics if m.metric_type == MetricType.SUSTAINABILITY), None)
            if sustainability_metric:
                sust_by_type = sustainability_metric.metadata.get("sustainability_by_type", {})
                charts.append({
                    "type": "bar",
                    "title": "Sustainability Score by Event Type",
                    "data": {
                        "labels": list(sust_by_type.keys()),
                        "datasets": [{
                            "label": "Sustainability Score",
                            "data": list(sust_by_type.values()),
                            "backgroundColor": ["#27ae60", "#f39c12", "#e74c3c"]
                        }]
                    }
                })
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts
    
    async def _generate_insights(self, metrics: List[MetricResult], query: AnalyticsQuery) -> List[str]:
        """Generate AI-powered insights from metrics"""
        insights = []
        
        try:
            # Attendance insights
            attendance_metric = next((m for m in metrics if m.metric_type == MetricType.ATTENDANCE), None)
            if attendance_metric:
                if attendance_metric.trend == "up":
                    insights.append(f"📈 Attendance is trending upward with {attendance_metric.change_percentage:.1f}% growth")
                elif attendance_metric.trend == "down":
                    insights.append(f"📉 Attendance has declined by {abs(attendance_metric.change_percentage):.1f}% - consider reviewing event promotion strategies")
                
                attendance_rate = attendance_metric.metadata.get("attendance_rate", 0)
                if attendance_rate > 80:
                    insights.append("🎯 Strong attendance rate indicates high event appeal")
                elif attendance_rate < 50:
                    insights.append("⚠️ Low attendance rate suggests need for better targeting or marketing")
            
            # Engagement insights
            engagement_metric = next((m for m in metrics if m.metric_type == MetricType.ENGAGEMENT), None)
            if engagement_metric:
                if engagement_metric.value > 75:
                    insights.append("💡 Excellent engagement levels - participants are highly active")
                elif engagement_metric.value < 40:
                    insights.append("📝 Low engagement detected - consider adding more interactive elements")
            
            # Revenue insights
            revenue_metric = next((m for m in metrics if m.metric_type == MetricType.REVENUE), None)
            if revenue_metric and revenue_metric.value > 0:
                avg_ticket_price = revenue_metric.metadata.get("avg_ticket_price", 0)
                if revenue_metric.trend == "up":
                    insights.append(f"💰 Revenue growth of {revenue_metric.change_percentage:.1f}% indicates strong monetization")
                
                revenue_by_category = revenue_metric.metadata.get("revenue_by_category", {})
                if revenue_by_category:
                    top_category = max(revenue_by_category.items(), key=lambda x: x[1])
                    insights.append(f"🏆 {top_category[0]} events generate the highest revenue (${top_category[1]:,.2f})")
            
            # Satisfaction insights
            satisfaction_metric = next((m for m in metrics if m.metric_type == MetricType.SATISFACTION), None)
            if satisfaction_metric:
                nps_score = satisfaction_metric.metadata.get("nps_score", 0)
                if nps_score > 50:
                    insights.append("😊 Excellent Net Promoter Score - participants are likely to recommend events")
                elif nps_score < 0:
                    insights.append("⚠️ Negative NPS score indicates participant dissatisfaction - urgent review needed")
                
                response_rate = satisfaction_metric.metadata.get("response_rate", 0)
                if response_rate < 20:
                    insights.append("📋 Low feedback response rate - consider incentivizing feedback collection")
            
            # Social insights
            social_metric = next((m for m in metrics if m.metric_type == MetricType.SOCIAL), None)
            if social_metric:
                team_formation_rate = social_metric.metadata.get("team_formation_rate", 0)
                if team_formation_rate > 80:
                    insights.append("🤝 High team formation rate indicates strong collaborative environment")
                elif team_formation_rate < 50:
                    insights.append("🔧 Consider improving team formation tools and matchmaking features")
            
            # Performance insights
            performance_metric = next((m for m in metrics if m.metric_type == MetricType.PERFORMANCE), None)
            if performance_metric:
                events_sold_out = performance_metric.metadata.get("events_sold_out", 0)
                total_events = performance_metric.metadata.get("total_events", 0)
                
                if events_sold_out > 0:
                    insights.append(f"🔥 {events_sold_out} events sold out - consider increasing capacity for popular event types")
                
                avg_utilization = performance_metric.metadata.get("avg_capacity_utilization", 0)
                if avg_utilization > 90:
                    insights.append("📊 High capacity utilization - excellent event planning")
                elif avg_utilization < 60:
                    insights.append("📈 Room for improvement in capacity planning or marketing reach")
            
            # Sustainability insights
            sustainability_metric = next((m for m in metrics if m.metric_type == MetricType.SUSTAINABILITY), None)
            if sustainability_metric:
                virtual_count = sustainability_metric.metadata.get("virtual_events_count", 0)
                total_events = sustainability_metric.metadata.get("total_events", 1)
                virtual_percentage = (virtual_count / total_events) * 100
                
                if virtual_percentage > 50:
                    insights.append("🌱 High proportion of virtual events contributing to sustainability goals")
                elif virtual_percentage < 20:
                    insights.append("🌍 Consider increasing virtual/hybrid events to improve sustainability metrics")
            
            # Predictive insights
            predictive_metric = next((m for m in metrics if m.metric_type == MetricType.PREDICTIVE), None)
            if predictive_metric:
                predictions = predictive_metric.metadata.get("predictions", {})
                ai_insights = predictions.get("insights", [])
                insights.extend([f"🔮 {insight}" for insight in ai_insights])
                
                accuracy = predictive_metric.value
                if accuracy > 80:
                    insights.append("🎯 High prediction accuracy - forecasts are reliable for planning")
                elif accuracy < 60:
                    insights.append("📊 Model accuracy could be improved with more historical data")
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights
    
    async def _generate_recommendations(self, metrics: List[MetricResult], query: AnalyticsQuery) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        try:
            # Attendance recommendations
            attendance_metric = next((m for m in metrics if m.metric_type == MetricType.ATTENDANCE), None)
            if attendance_metric:
                attendance_rate = attendance_metric.metadata.get("attendance_rate", 0)
                no_show_rate = attendance_metric.metadata.get("no_show_rate", 0)
                
                if attendance_rate < 70:
                    recommendations.append("🎯 Implement targeted marketing campaigns to improve attendance rates")
                    recommendations.append("📧 Use AI-powered personalized event recommendations to reach relevant audiences")
                
                if no_show_rate > 15:
                    recommendations.append("⏰ Send reminder notifications 24-48 hours before events to reduce no-shows")
                    recommendations.append("🎫 Consider implementing a small confirmation fee to ensure commitment")
            
            # Engagement recommendations
            engagement_metric = next((m for m in metrics if m.metric_type == MetricType.ENGAGEMENT), None)
            if engagement_metric and engagement_metric.value < 60:
                recommendations.append("🎮 Add gamification elements like badges and leaderboards to boost engagement")
                recommendations.append("📊 Implement real-time polls and Q&A sessions during events")
                recommendations.append("🤝 Encourage team formation and collaborative activities")
            
            # Revenue recommendations
            revenue_metric = next((m for m in metrics if m.metric_type == MetricType.REVENUE), None)
            if revenue_metric:
                avg_ticket_price = revenue_metric.metadata.get("avg_ticket_price", 0)
                revenue_by_category = revenue_metric.metadata.get("revenue_by_category", {})
                
                if avg_ticket_price < 50 and revenue_by_category:
                    top_category = max(revenue_by_category.items(), key=lambda x: x[1])
                    recommendations.append(f"💡 Focus on {top_category[0]} events as they generate highest revenue")
                
                if revenue_metric.trend == "down":
                    recommendations.append("💰 Consider tiered pricing strategies or premium add-on services")
                    recommendations.append("🎁 Offer early-bird discounts to incentivize advance bookings")
            
            # Satisfaction recommendations
            satisfaction_metric = next((m for m in metrics if m.metric_type == MetricType.SATISFACTION), None)
            if satisfaction_metric:
                avg_rating = satisfaction_metric.metadata.get("average_rating", 0)
                response_rate = satisfaction_metric.metadata.get("response_rate", 0)
                
                if avg_rating < 4.0:
                    recommendations.append("📝 Conduct detailed feedback analysis to identify improvement areas")
                    recommendations.append("🎤 Implement post-event surveys with specific action items")
                
                if response_rate < 30:
                    recommendations.append("🎁 Offer incentives for feedback completion (discounts, badges)")
                    recommendations.append("⚡ Simplify feedback forms and make them more engaging")
            
            # Social recommendations
            social_metric = next((m for m in metrics if m.metric_type == MetricType.SOCIAL), None)
            if social_metric:
                social_engagement = social_metric.metadata.get("social_engagement_rate", 0)
                team_formation_rate = social_metric.metadata.get("team_formation_rate", 0)
                
                if social_engagement < 50:
                    recommendations.append("🌐 Create networking lounges and breakout rooms for better interaction")
                    recommendations.append("💬 Implement mentor-mentee matching for knowledge sharing")
                
                if team_formation_rate < 70:
                    recommendations.append("🤖 Use AI-powered team matching based on skills and interests")
                    recommendations.append("🎯 Provide clearer guidelines and tools for team formation")
            
            # Performance recommendations
            performance_metric = next((m for m in metrics if m.metric_type == MetricType.PERFORMANCE), None)
            if performance_metric:
                capacity_utilization = performance_metric.metadata.get("avg_capacity_utilization", 0)
                
                if capacity_utilization > 95:
                    recommendations.append("📈 Consider increasing event capacity or adding additional sessions")
                elif capacity_utilization < 60:
                    recommendations.append("🎯 Optimize event scheduling and improve marketing targeting")
                    recommendations.append("📊 Analyze competitor events and market demand patterns")
            
            # Sustainability recommendations
            sustainability_metric = next((m for m in metrics if m.metric_type == MetricType.SUSTAINABILITY), None)
            if sustainability_metric:
                virtual_count = sustainability_metric.metadata.get("virtual_events_count", 0)
                total_events = sustainability_metric.metadata.get("total_events", 1)
                
                if virtual_count / total_events < 0.3:
                    recommendations.append("🌱 Increase virtual and hybrid events to reduce carbon footprint")
                    recommendations.append("♻️ Implement sustainability tracking and reporting for all events")
                    recommendations.append("🌍 Partner with eco-friendly venues and suppliers")
            
            # Predictive recommendations
            predictive_metric = next((m for m in metrics if m.metric_type == MetricType.PREDICTIVE), None)
            if predictive_metric:
                predictions = predictive_metric.metadata.get("predictions", {})
                forecast_data = predictions.get("attendance_forecast", [])
                
                if forecast_data:
                    high_demand_events = [e for e in forecast_data if e["predicted_attendance"] > 100]
                    if high_demand_events:
                        recommendations.append("🚀 Scale up marketing for high-demand predicted events")
                        recommendations.append("⚡ Prepare additional resources for events with high predicted attendance")
                
                accuracy = predictive_metric.value
                if accuracy < 70:
                    recommendations.append("📈 Collect more historical data to improve prediction accuracy")
                    recommendations.append("🧠 Consider additional features for ML models (weather, holidays, etc.)")
        
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _validate_query(self, query: AnalyticsQuery):
        """Validate analytics query parameters"""
        if not query.metric_types:
            raise ValueError("At least one metric type must be specified")
        
        if query.time_range == TimeRange.CUSTOM:
            if not query.custom_start or not query.custom_end:
                raise ValueError("Custom time range requires start and end dates")
            if query.custom_start >= query.custom_end:
                raise ValueError("Start date must be before end date")
    
    def _get_time_bounds(self, query: AnalyticsQuery) -> Tuple[datetime, datetime]:
        """Get time bounds based on query time range"""
        now = datetime.utcnow()
        
        if query.time_range == TimeRange.LAST_24H:
            return now - timedelta(days=1), now
        elif query.time_range == TimeRange.LAST_7D:
            return now - timedelta(days=7), now
        elif query.time_range == TimeRange.LAST_30D:
            return now - timedelta(days=30), now
        elif query.time_range == TimeRange.LAST_90D:
            return now - timedelta(days=90), now
        elif query.time_range == TimeRange.LAST_YEAR:
            return now - timedelta(days=365), now
        elif query.time_range == TimeRange.ALL_TIME:
            return datetime(2020, 1, 1), now  # Reasonable start date
        elif query.time_range == TimeRange.CUSTOM:
            return query.custom_start, query.custom_end
        else:
            return now - timedelta(days=30), now  # Default to last 30 days
    
    def _generate_time_labels(self, query: AnalyticsQuery) -> List[str]:
        """Generate time labels for charts based on query granularity"""
        start_time, end_time = self._get_time_bounds(query)
        
        labels = []
        current = start_time
        
        if query.granularity == "hour":
            delta = timedelta(hours=1)
            format_str = "%H:%M"
        elif query.granularity == "day":
            delta = timedelta(days=1)
            format_str = "%m/%d"
        elif query.granularity == "week":
            delta = timedelta(weeks=1)
            format_str = "%m/%d"
        elif query.granularity == "month":
            delta = timedelta(days=30)
            format_str = "%Y-%m"
        else:
            delta = timedelta(days=1)
            format_str = "%m/%d"
        
        while current <= end_time:
            labels.append(current.strftime(format_str))
            current += delta
            
            # Limit labels to prevent overcrowding
            if len(labels) >= 20:
                break
        
        return labels


# Global analytics engine instance
analytics_engine = AnalyticsEngine()


# Utility functions for easy access
async def generate_dashboard_data(user_id: int, role: str = "organizer", 
                                time_range: TimeRange = TimeRange.LAST_30D) -> Dict[str, Any]:
    """Generate dashboard data for a specific user"""
    try:
        # Determine which events to analyze based on user role
        event_ids = None
        if role == "organizer":
            user = User.query.get(user_id)
            if user:
                event_ids = [e.id for e in user.organized_events.all()]
        
        # Create analytics query
        query = AnalyticsQuery(
            metric_types=[
                MetricType.ATTENDANCE,
                MetricType.ENGAGEMENT, 
                MetricType.REVENUE,
                MetricType.SATISFACTION,
                MetricType.SOCIAL,
                MetricType.PERFORMANCE
            ],
            time_range=time_range,
            event_ids=event_ids
        )
        
        # Generate report
        report = await analytics_engine.generate_report(query)
        
        # Format for dashboard
        dashboard_data = {
            "metrics": [asdict(m) for m in report.metrics],
            "charts": report.charts,
            "insights": report.insights,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}")
        return {"error": str(e)}


async def generate_event_report(event_id: int) -> Dict[str, Any]:
    """Generate detailed analytics report for a specific event"""
    try:
        query = AnalyticsQuery(
            metric_types=[
                MetricType.ATTENDANCE,
                MetricType.ENGAGEMENT,
                MetricType.SATISFACTION,
                MetricType.SOCIAL,
                MetricType.PERFORMANCE,
                MetricType.SUSTAINABILITY
            ],
            time_range=TimeRange.ALL_TIME,
            event_ids=[event_id]
        )
        
        report = await analytics_engine.generate_report(query)
        
        return {
            "event_id": event_id,
            "metrics": [asdict(m) for m in report.metrics],
            "charts": report.charts,
            "insights": report.insights,
            "recommendations": report.recommendations,
            "generated_at": report.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating event report: {e}")
        return {"error": str(e)}


async def generate_predictive_report(time_horizon_days: int = 30) -> Dict[str, Any]:
    """Generate predictive analytics report"""
    try:
        query = AnalyticsQuery(
            metric_types=[MetricType.PREDICTIVE],
            time_range=TimeRange.ALL_TIME,
            include_predictions=True
        )
        
        report = await analytics_engine.generate_report(query)
        
        return {
            "predictions": report.metrics[0].metadata if report.metrics else {},
            "insights": report.insights,
            "recommendations": report.recommendations,
            "time_horizon_days": time_horizon_days,
            "generated_at": report.generated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating predictive report: {e}")
        return {"error": str(e)}