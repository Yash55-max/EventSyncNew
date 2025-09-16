"""
Practical Assessment System for Event Management
Hands-on challenges, mock event scenarios, and AI-powered feedback
"""

import json
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import math

from app import db
from models import Event, User, EventAnalytics

logger = logging.getLogger(__name__)

class AssessmentType(Enum):
    """Types of practical assessments"""
    MOCK_EVENT_PLANNING = "mock_event_planning"
    CRISIS_MANAGEMENT = "crisis_management"
    BUDGET_OPTIMIZATION = "budget_optimization"
    MARKETING_CAMPAIGN = "marketing_campaign"
    VENDOR_SELECTION = "vendor_selection"
    SUSTAINABILITY_CHALLENGE = "sustainability_challenge"
    AUDIENCE_ENGAGEMENT = "audience_engagement"
    TECHNOLOGY_INTEGRATION = "technology_integration"
    MULTI_DAY_FESTIVAL = "multi_day_festival"
    VIRTUAL_EVENT_DESIGN = "virtual_event_design"

class DifficultyLevel(Enum):
    """Assessment difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class AssessmentCategory(Enum):
    """Assessment categories"""
    PLANNING = "planning"
    EXECUTION = "execution"
    MARKETING = "marketing"
    FINANCE = "finance"
    TECHNOLOGY = "technology"
    SUSTAINABILITY = "sustainability"
    CRISIS_MANAGEMENT = "crisis_management"
    ANALYTICS = "analytics"

class DecisionImpact(Enum):
    """Impact levels of user decisions"""
    CRITICAL_SUCCESS = "critical_success"
    MAJOR_POSITIVE = "major_positive"
    MINOR_POSITIVE = "minor_positive"
    NEUTRAL = "neutral"
    MINOR_NEGATIVE = "minor_negative"
    MAJOR_NEGATIVE = "major_negative"
    CRITICAL_FAILURE = "critical_failure"

@dataclass
class AssessmentScenario:
    """Assessment scenario definition"""
    id: str
    title: str
    description: str
    assessment_type: AssessmentType
    difficulty: DifficultyLevel
    category: AssessmentCategory
    estimated_duration: int  # minutes
    learning_objectives: List[str]
    scenario_context: Dict[str, Any]
    decision_points: List[Dict[str, Any]]
    success_criteria: List[Dict[str, Any]]
    resources_provided: List[Dict[str, Any]]

@dataclass
class UserDecision:
    """User decision in assessment"""
    decision_id: str
    choice_made: str
    rationale: Optional[str]
    timestamp: datetime
    time_taken: int  # seconds
    confidence_level: float  # 0-1

@dataclass
class DecisionFeedback:
    """AI feedback on user decision"""
    decision_id: str
    impact_assessment: DecisionImpact
    score: float  # 0-100
    feedback_text: str
    improvement_suggestions: List[str]
    alternative_approaches: List[str]
    industry_best_practices: List[str]
    consequences: Dict[str, Any]

@dataclass
class AssessmentResult:
    """Complete assessment result"""
    assessment_id: str
    user_id: int
    scenario_id: str
    start_time: datetime
    completion_time: Optional[datetime]
    decisions: List[UserDecision]
    feedback: List[DecisionFeedback]
    overall_score: float  # 0-100
    category_scores: Dict[str, float]
    achievements: List[str]
    areas_for_improvement: List[str]
    next_recommended_assessments: List[str]
    real_world_application: str

class MockEventScenarioGenerator:
    """Generates realistic mock event scenarios"""
    
    EVENT_TYPES = [
        "Corporate Conference", "Wedding Reception", "Music Festival",
        "Product Launch", "Charity Gala", "Tech Meetup", "Art Exhibition",
        "Sports Tournament", "Fashion Show", "Food Festival", "Book Fair",
        "Startup Pitch Event", "Academic Symposium", "Trade Show"
    ]
    
    CONSTRAINTS = [
        {"type": "budget", "values": [5000, 15000, 50000, 100000, 500000]},
        {"type": "timeline", "values": [2, 4, 8, 12, 24]},  # weeks
        {"type": "attendees", "values": [50, 100, 300, 500, 1000, 2000]},
        {"type": "venue_type", "values": ["indoor", "outdoor", "virtual", "hybrid"]},
        {"type": "season", "values": ["spring", "summer", "fall", "winter"]}
    ]
    
    COMPLICATIONS = [
        "Key speaker cancelled last minute",
        "Venue double-booked",
        "Budget cut by 30%",
        "Weather forecast shows rain",
        "Catering company went out of business",
        "AV equipment malfunctioned",
        "Fire safety inspection failed",
        "Competitor scheduled similar event same day",
        "Social media backlash over event theme",
        "Key sponsor pulled out",
        "Permit application rejected",
        "Staff member called in sick",
        "Supply chain disruption",
        "Security threat received",
        "Technology platform crashed"
    ]
    
    def generate_scenario(self, difficulty: DifficultyLevel, category: AssessmentCategory) -> AssessmentScenario:
        """Generate a random assessment scenario"""
        
        event_type = random.choice(self.EVENT_TYPES)
        constraints = self._select_constraints(difficulty)
        complications = self._select_complications(difficulty)
        
        scenario_id = f"scenario_{random.randint(10000, 99999)}"
        
        # Base scenario context
        context = {
            "event_type": event_type,
            "constraints": constraints,
            "complications": complications,
            "client_requirements": self._generate_client_requirements(event_type),
            "market_conditions": self._generate_market_conditions(),
            "available_resources": self._generate_available_resources()
        }
        
        # Generate decision points based on category
        decision_points = self._generate_decision_points(category, context, difficulty)
        
        # Define success criteria
        success_criteria = self._generate_success_criteria(category, constraints)
        
        # Provide resources
        resources = self._generate_resources(category, difficulty)
        
        learning_objectives = self._generate_learning_objectives(category, difficulty)
        
        return AssessmentScenario(
            id=scenario_id,
            title=f"{event_type} Challenge - {category.value.title()}",
            description=self._generate_scenario_description(event_type, constraints, complications),
            assessment_type=AssessmentType.MOCK_EVENT_PLANNING,
            difficulty=difficulty,
            category=category,
            estimated_duration=self._calculate_duration(difficulty, len(decision_points)),
            learning_objectives=learning_objectives,
            scenario_context=context,
            decision_points=decision_points,
            success_criteria=success_criteria,
            resources_provided=resources
        )
    
    def _select_constraints(self, difficulty: DifficultyLevel) -> Dict[str, Any]:
        """Select constraints based on difficulty"""
        constraints = {}
        
        # More constraints for higher difficulty
        constraint_count = {
            DifficultyLevel.BEGINNER: 2,
            DifficultyLevel.INTERMEDIATE: 3,
            DifficultyLevel.ADVANCED: 4,
            DifficultyLevel.EXPERT: 5
        }[difficulty]
        
        selected_constraints = random.sample(self.CONSTRAINTS, constraint_count)
        
        for constraint in selected_constraints:
            if constraint["type"] == "budget" and difficulty == DifficultyLevel.BEGINNER:
                # Higher budget for beginners
                constraints[constraint["type"]] = random.choice(constraint["values"][-3:])
            elif constraint["type"] == "timeline" and difficulty == DifficultyLevel.EXPERT:
                # Shorter timeline for experts
                constraints[constraint["type"]] = random.choice(constraint["values"][:2])
            else:
                constraints[constraint["type"]] = random.choice(constraint["values"])
        
        return constraints
    
    def _select_complications(self, difficulty: DifficultyLevel) -> List[str]:
        """Select complications based on difficulty"""
        complication_count = {
            DifficultyLevel.BEGINNER: 1,
            DifficultyLevel.INTERMEDIATE: 2,
            DifficultyLevel.ADVANCED: 3,
            DifficultyLevel.EXPERT: 4
        }[difficulty]
        
        return random.sample(self.COMPLICATIONS, complication_count)
    
    def _generate_client_requirements(self, event_type: str) -> List[str]:
        """Generate realistic client requirements"""
        base_requirements = [
            "Professional photography/videography",
            "High-quality catering",
            "Reliable AV equipment",
            "Comfortable seating arrangements",
            "Easy parking access"
        ]
        
        specific_requirements = {
            "Corporate Conference": [
                "Live streaming capability",
                "Breakout session rooms",
                "High-speed WiFi",
                "Presentation equipment",
                "Networking area"
            ],
            "Wedding Reception": [
                "Dance floor",
                "Romantic lighting",
                "Wedding cake table",
                "Photo booth area",
                "Bridal suite access"
            ],
            "Music Festival": [
                "Multiple stages",
                "Sound system for 5000+ people",
                "Security barriers",
                "Food vendor space",
                "Emergency medical station"
            ]
        }
        
        return base_requirements + specific_requirements.get(event_type, [])
    
    def _generate_market_conditions(self) -> Dict[str, Any]:
        """Generate current market conditions"""
        return {
            "venue_availability": random.choice(["high", "medium", "low"]),
            "vendor_pricing": random.choice(["competitive", "average", "premium"]),
            "demand_level": random.choice(["low", "medium", "high"]),
            "economic_climate": random.choice(["recession", "stable", "growth"]),
            "seasonal_factors": random.choice(["peak_season", "off_season", "shoulder_season"])
        }
    
    def _generate_available_resources(self) -> Dict[str, Any]:
        """Generate available resources"""
        return {
            "team_size": random.randint(2, 10),
            "experience_level": random.choice(["junior", "mixed", "senior"]),
            "vendor_relationships": random.choice(["new", "established", "premium"]),
            "technology_access": random.choice(["basic", "standard", "advanced"]),
            "emergency_budget": random.randint(1000, 10000)
        }
    
    def _generate_decision_points(self, category: AssessmentCategory, context: Dict, 
                                 difficulty: DifficultyLevel) -> List[Dict[str, Any]]:
        """Generate decision points based on category"""
        
        decision_templates = {
            AssessmentCategory.PLANNING: [
                {
                    "id": "venue_selection",
                    "title": "Venue Selection",
                    "description": "Choose the best venue option",
                    "options": [
                        {"id": "premium", "text": "Premium venue (+50% cost, best amenities)"},
                        {"id": "standard", "text": "Standard venue (budget-friendly, adequate)"},
                        {"id": "alternative", "text": "Non-traditional venue (unique, potential risks)"}
                    ]
                },
                {
                    "id": "catering_strategy",
                    "title": "Catering Strategy",
                    "description": "Select catering approach",
                    "options": [
                        {"id": "full_service", "text": "Full-service catering (highest cost, no hassle)"},
                        {"id": "buffet", "text": "Buffet style (medium cost, efficient)"},
                        {"id": "food_trucks", "text": "Multiple food trucks (trendy, coordination needed)"}
                    ]
                }
            ],
            AssessmentCategory.MARKETING: [
                {
                    "id": "marketing_channel",
                    "title": "Primary Marketing Channel",
                    "description": "Choose main marketing strategy",
                    "options": [
                        {"id": "social_media", "text": "Social media campaign (broad reach, cost-effective)"},
                        {"id": "traditional", "text": "Traditional advertising (targeted, higher cost)"},
                        {"id": "influencer", "text": "Influencer partnerships (trendy, variable ROI)"}
                    ]
                }
            ],
            AssessmentCategory.CRISIS_MANAGEMENT: [
                {
                    "id": "crisis_response",
                    "title": "Crisis Response Strategy",
                    "description": f"How do you handle: {context.get('complications', [''])[0]}",
                    "options": [
                        {"id": "immediate", "text": "Take immediate action (fast, potentially costly)"},
                        {"id": "consult", "text": "Consult with team first (measured, might delay)"},
                        {"id": "postpone", "text": "Consider postponing event (safe, disappointing)"}
                    ]
                }
            ]
        }
        
        # Get base decisions for category
        base_decisions = decision_templates.get(category, decision_templates[AssessmentCategory.PLANNING])
        
        # Add complexity based on difficulty
        if difficulty in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
            base_decisions.extend([
                {
                    "id": "budget_reallocation",
                    "title": "Budget Emergency",
                    "description": "Budget cut by 25% - where do you reduce spending?",
                    "options": [
                        {"id": "venue", "text": "Downgrade venue (impacts experience)"},
                        {"id": "catering", "text": "Reduce catering quality (attendee dissatisfaction)"},
                        {"id": "marketing", "text": "Cut marketing budget (lower attendance)"}
                    ]
                }
            ])
        
        return base_decisions
    
    def _generate_success_criteria(self, category: AssessmentCategory, constraints: Dict) -> List[Dict[str, Any]]:
        """Generate success criteria"""
        base_criteria = [
            {"metric": "budget_adherence", "target": 95, "weight": 0.3},
            {"metric": "timeline_adherence", "target": 100, "weight": 0.2},
            {"metric": "attendee_satisfaction", "target": 85, "weight": 0.3},
            {"metric": "safety_compliance", "target": 100, "weight": 0.2}
        ]
        
        category_specific = {
            AssessmentCategory.MARKETING: [
                {"metric": "registration_rate", "target": 80, "weight": 0.4}
            ],
            AssessmentCategory.SUSTAINABILITY: [
                {"metric": "carbon_footprint_reduction", "target": 20, "weight": 0.3}
            ]
        }
        
        return base_criteria + category_specific.get(category, [])
    
    def _generate_resources(self, category: AssessmentCategory, difficulty: DifficultyLevel) -> List[Dict[str, Any]]:
        """Generate available resources"""
        base_resources = [
            {"type": "document", "title": "Event Planning Checklist", "url": "/resources/checklist.pdf"},
            {"type": "tool", "title": "Budget Calculator", "url": "/tools/budget-calc"},
            {"type": "database", "title": "Vendor Directory", "url": "/vendors/search"}
        ]
        
        if difficulty in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]:
            base_resources.extend([
                {"type": "guide", "title": "Best Practices Guide", "url": "/guides/best-practices"},
                {"type": "template", "title": "Timeline Template", "url": "/templates/timeline"}
            ])
        
        return base_resources
    
    def _generate_learning_objectives(self, category: AssessmentCategory, difficulty: DifficultyLevel) -> List[str]:
        """Generate learning objectives"""
        base_objectives = [
            "Apply event planning fundamentals",
            "Make data-driven decisions",
            "Balance competing priorities",
            "Manage stakeholder expectations"
        ]
        
        category_objectives = {
            AssessmentCategory.PLANNING: [
                "Create comprehensive event timelines",
                "Optimize resource allocation",
                "Identify critical path dependencies"
            ],
            AssessmentCategory.MARKETING: [
                "Design effective marketing campaigns",
                "Calculate marketing ROI",
                "Target appropriate audience segments"
            ],
            AssessmentCategory.CRISIS_MANAGEMENT: [
                "Develop crisis response strategies",
                "Communicate effectively under pressure",
                "Minimize negative impact on event"
            ]
        }
        
        return base_objectives + category_objectives.get(category, [])
    
    def _generate_scenario_description(self, event_type: str, constraints: Dict, complications: List[str]) -> str:
        """Generate scenario description"""
        description = f"You are tasked with planning a {event_type} with the following constraints:\n\n"
        
        for key, value in constraints.items():
            description += f"• {key.title()}: {value}\n"
        
        if complications:
            description += f"\nChallenges you must navigate:\n"
            for complication in complications:
                description += f"• {complication}\n"
        
        description += "\nMake strategic decisions to ensure event success while managing these constraints and challenges."
        
        return description
    
    def _calculate_duration(self, difficulty: DifficultyLevel, decision_count: int) -> int:
        """Calculate estimated duration in minutes"""
        base_time = {
            DifficultyLevel.BEGINNER: 5,
            DifficultyLevel.INTERMEDIATE: 8,
            DifficultyLevel.ADVANCED: 12,
            DifficultyLevel.EXPERT: 15
        }[difficulty]
        
        return base_time * decision_count + 10  # 10 minutes for reading scenario

class AIFeedbackEngine:
    """AI-powered feedback system for assessments"""
    
    def __init__(self):
        self.decision_patterns = self._load_decision_patterns()
        self.industry_benchmarks = self._load_industry_benchmarks()
        self.feedback_templates = self._load_feedback_templates()
    
    def analyze_decision(self, decision: UserDecision, scenario_context: Dict, 
                        decision_definition: Dict) -> DecisionFeedback:
        """Analyze a user decision and provide AI feedback"""
        
        # Assess decision impact
        impact = self._assess_decision_impact(decision, scenario_context, decision_definition)
        
        # Calculate score
        score = self._calculate_decision_score(decision, impact, scenario_context)
        
        # Generate feedback text
        feedback_text = self._generate_feedback_text(decision, impact, score)
        
        # Generate improvement suggestions
        improvements = self._generate_improvement_suggestions(decision, impact, decision_definition)
        
        # Generate alternative approaches
        alternatives = self._generate_alternatives(decision, decision_definition)
        
        # Get industry best practices
        best_practices = self._get_best_practices(decision_definition["id"])
        
        # Calculate consequences
        consequences = self._calculate_consequences(decision, impact, scenario_context)
        
        return DecisionFeedback(
            decision_id=decision.decision_id,
            impact_assessment=impact,
            score=score,
            feedback_text=feedback_text,
            improvement_suggestions=improvements,
            alternative_approaches=alternatives,
            industry_best_practices=best_practices,
            consequences=consequences
        )
    
    def _assess_decision_impact(self, decision: UserDecision, scenario_context: Dict, 
                               decision_definition: Dict) -> DecisionImpact:
        """Assess the impact of a decision"""
        
        # Get decision option details
        options = {opt["id"]: opt for opt in decision_definition["options"]}
        chosen_option = options.get(decision.choice_made)
        
        if not chosen_option:
            return DecisionImpact.NEUTRAL
        
        # Analyze decision based on scenario context
        constraints = scenario_context.get("constraints", {})
        complications = scenario_context.get("complications", [])
        
        # Decision-specific logic
        if decision_definition["id"] == "venue_selection":
            return self._analyze_venue_decision(decision.choice_made, constraints)
        elif decision_definition["id"] == "catering_strategy":
            return self._analyze_catering_decision(decision.choice_made, constraints)
        elif decision_definition["id"] == "marketing_channel":
            return self._analyze_marketing_decision(decision.choice_made, constraints)
        elif decision_definition["id"] == "crisis_response":
            return self._analyze_crisis_decision(decision.choice_made, complications)
        elif decision_definition["id"] == "budget_reallocation":
            return self._analyze_budget_decision(decision.choice_made, constraints)
        
        return DecisionImpact.NEUTRAL
    
    def _analyze_venue_decision(self, choice: str, constraints: Dict) -> DecisionImpact:
        """Analyze venue selection decision"""
        budget = constraints.get("budget", 50000)
        attendees = constraints.get("attendees", 300)
        
        if choice == "premium":
            if budget > 100000:
                return DecisionImpact.MAJOR_POSITIVE  # Can afford it
            elif attendees > 500:
                return DecisionImpact.MINOR_POSITIVE  # Worth it for large events
            else:
                return DecisionImpact.MINOR_NEGATIVE  # Overspending
        
        elif choice == "standard":
            return DecisionImpact.MINOR_POSITIVE  # Safe choice
        
        elif choice == "alternative":
            if attendees < 200:
                return DecisionImpact.MAJOR_POSITIVE  # Creative for small events
            else:
                return DecisionImpact.MINOR_NEGATIVE  # Risky for large events
        
        return DecisionImpact.NEUTRAL
    
    def _analyze_catering_decision(self, choice: str, constraints: Dict) -> DecisionImpact:
        """Analyze catering strategy decision"""
        budget = constraints.get("budget", 50000)
        attendees = constraints.get("attendees", 300)
        
        cost_per_person = budget / attendees if attendees > 0 else 0
        
        if choice == "full_service":
            if cost_per_person > 100:
                return DecisionImpact.MAJOR_POSITIVE  # Can afford premium
            else:
                return DecisionImpact.MAJOR_NEGATIVE  # Budget strain
        
        elif choice == "buffet":
            return DecisionImpact.MINOR_POSITIVE  # Balanced choice
        
        elif choice == "food_trucks":
            if attendees < 500:
                return DecisionImpact.MAJOR_POSITIVE  # Trendy and manageable
            else:
                return DecisionImpact.MINOR_NEGATIVE  # Coordination challenges
        
        return DecisionImpact.NEUTRAL
    
    def _analyze_marketing_decision(self, choice: str, constraints: Dict) -> DecisionImpact:
        """Analyze marketing channel decision"""
        budget = constraints.get("budget", 50000)
        attendees = constraints.get("attendees", 300)
        
        marketing_budget = budget * 0.15  # Assume 15% marketing budget
        
        if choice == "social_media":
            if attendees < 1000:
                return DecisionImpact.MAJOR_POSITIVE  # Cost-effective for smaller events
            else:
                return DecisionImpact.MINOR_POSITIVE  # Good reach
        
        elif choice == "traditional":
            if marketing_budget > 5000:
                return DecisionImpact.MINOR_POSITIVE  # Can afford it
            else:
                return DecisionImpact.MINOR_NEGATIVE  # Expensive
        
        elif choice == "influencer":
            if attendees < 500:
                return DecisionImpact.MINOR_NEGATIVE  # Limited reach for small events
            else:
                return DecisionImpact.MINOR_POSITIVE  # Good for large events
        
        return DecisionImpact.NEUTRAL
    
    def _analyze_crisis_decision(self, choice: str, complications: List[str]) -> DecisionImpact:
        """Analyze crisis management decision"""
        # More complex decisions get better results for immediate action
        severity = len(complications)
        
        if choice == "immediate":
            if severity > 2:
                return DecisionImpact.MAJOR_POSITIVE  # Quick action needed
            else:
                return DecisionImpact.MINOR_POSITIVE  # Proactive
        
        elif choice == "consult":
            if severity <= 2:
                return DecisionImpact.MINOR_POSITIVE  # Good for minor issues
            else:
                return DecisionImpact.MINOR_NEGATIVE  # Delays in crisis
        
        elif choice == "postpone":
            if severity > 3:
                return DecisionImpact.MINOR_POSITIVE  # Sometimes necessary
            else:
                return DecisionImpact.MAJOR_NEGATIVE  # Unnecessary cancellation
        
        return DecisionImpact.NEUTRAL
    
    def _analyze_budget_decision(self, choice: str, constraints: Dict) -> DecisionImpact:
        """Analyze budget reallocation decision"""
        event_type = constraints.get("event_type", "Corporate Conference")
        
        # Different events prioritize different aspects
        if event_type in ["Wedding Reception", "Charity Gala"]:
            if choice == "marketing":
                return DecisionImpact.MAJOR_POSITIVE  # Less marketing needed
            elif choice == "venue":
                return DecisionImpact.MAJOR_NEGATIVE  # Venue is critical
        
        elif event_type in ["Corporate Conference", "Product Launch"]:
            if choice == "catering":
                return DecisionImpact.MINOR_POSITIVE  # Can manage with simpler food
            elif choice == "marketing":
                return DecisionImpact.MINOR_NEGATIVE  # Marketing important for corporate
        
        return DecisionImpact.MINOR_NEGATIVE  # Budget cuts always have some impact
    
    def _calculate_decision_score(self, decision: UserDecision, impact: DecisionImpact, 
                                 scenario_context: Dict) -> float:
        """Calculate numeric score for decision"""
        
        # Base scores for different impact levels
        impact_scores = {
            DecisionImpact.CRITICAL_SUCCESS: 95,
            DecisionImpact.MAJOR_POSITIVE: 85,
            DecisionImpact.MINOR_POSITIVE: 75,
            DecisionImpact.NEUTRAL: 60,
            DecisionImpact.MINOR_NEGATIVE: 45,
            DecisionImpact.MAJOR_NEGATIVE: 30,
            DecisionImpact.CRITICAL_FAILURE: 15
        }
        
        base_score = impact_scores[impact]
        
        # Adjust for decision time (faster decisions get slight bonus)
        time_bonus = max(0, 5 - (decision.time_taken / 30))  # 30 seconds = 0 bonus
        
        # Adjust for confidence (higher confidence with good decisions gets bonus)
        confidence_modifier = 0
        if impact in [DecisionImpact.MAJOR_POSITIVE, DecisionImpact.CRITICAL_SUCCESS]:
            confidence_modifier = (decision.confidence_level - 0.5) * 10
        elif impact in [DecisionImpact.MAJOR_NEGATIVE, DecisionImpact.CRITICAL_FAILURE]:
            confidence_modifier = (0.5 - decision.confidence_level) * 10
        
        # Rationale bonus
        rationale_bonus = 5 if decision.rationale and len(decision.rationale) > 50 else 0
        
        final_score = base_score + time_bonus + confidence_modifier + rationale_bonus
        return max(0, min(100, final_score))
    
    def _generate_feedback_text(self, decision: UserDecision, impact: DecisionImpact, score: float) -> str:
        """Generate personalized feedback text"""
        
        impact_messages = {
            DecisionImpact.CRITICAL_SUCCESS: "Excellent decision! This choice demonstrates exceptional event management skills.",
            DecisionImpact.MAJOR_POSITIVE: "Great choice! This decision shows strong understanding of event planning principles.",
            DecisionImpact.MINOR_POSITIVE: "Good decision. This choice addresses the key requirements effectively.",
            DecisionImpact.NEUTRAL: "Reasonable choice. This decision is acceptable but may have missed optimization opportunities.",
            DecisionImpact.MINOR_NEGATIVE: "This choice has some drawbacks. Consider the potential consequences more carefully.",
            DecisionImpact.MAJOR_NEGATIVE: "This decision could create significant challenges for your event.",
            DecisionImpact.CRITICAL_FAILURE: "This choice could jeopardize the entire event. Reconsider your approach."
        }
        
        base_feedback = impact_messages[impact]
        
        # Add score-specific commentary
        if score >= 90:
            base_feedback += " Your score reflects mastery-level decision making."
        elif score >= 80:
            base_feedback += " Your score shows strong competency in this area."
        elif score >= 70:
            base_feedback += " Your score indicates good understanding with room for improvement."
        elif score >= 60:
            base_feedback += " Your score suggests you grasp the basics but need more practice."
        else:
            base_feedback += " Your score indicates this is an area requiring significant development."
        
        # Add rationale feedback if provided
        if decision.rationale:
            if len(decision.rationale) > 100:
                base_feedback += " Your detailed rationale shows thoughtful consideration of the decision."
            elif len(decision.rationale) > 50:
                base_feedback += " Good job providing rationale for your decision."
            else:
                base_feedback += " Try to provide more detailed rationale to demonstrate your thinking process."
        else:
            base_feedback += " Consider providing rationale for your decisions to show your thought process."
        
        return base_feedback
    
    def _generate_improvement_suggestions(self, decision: UserDecision, impact: DecisionImpact, 
                                        decision_definition: Dict) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if impact in [DecisionImpact.MINOR_NEGATIVE, DecisionImpact.MAJOR_NEGATIVE, DecisionImpact.CRITICAL_FAILURE]:
            decision_id = decision_definition["id"]
            
            if decision_id == "venue_selection":
                suggestions.extend([
                    "Consider venue capacity relative to expected attendance",
                    "Factor in accessibility requirements for all attendees",
                    "Evaluate venue's technical capabilities for your event needs",
                    "Review venue's track record and references from similar events"
                ])
            
            elif decision_id == "catering_strategy":
                suggestions.extend([
                    "Consider dietary restrictions and preferences of your audience",
                    "Factor in service timing and logistics for meal service",
                    "Evaluate catering quality vs. budget trade-offs",
                    "Plan for contingencies like last-minute attendance changes"
                ])
            
            elif decision_id == "marketing_channel":
                suggestions.extend([
                    "Analyze your target audience's media consumption habits",
                    "Calculate expected return on investment for each channel",
                    "Consider integrated marketing approaches vs. single channels",
                    "Test marketing messages before full campaign launch"
                ])
            
            elif decision_id == "crisis_response":
                suggestions.extend([
                    "Develop crisis communication protocols in advance",
                    "Create decision trees for common crisis scenarios",
                    "Establish clear escalation procedures",
                    "Practice crisis response through scenario planning"
                ])
        
        # General suggestions
        if decision.time_taken > 180:  # More than 3 minutes
            suggestions.append("Practice making decisions more quickly under time pressure")
        
        if decision.confidence_level < 0.6:
            suggestions.append("Build confidence through additional scenario practice")
        
        if not decision.rationale:
            suggestions.append("Always document your decision rationale for future reference")
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _generate_alternatives(self, decision: UserDecision, decision_definition: Dict) -> List[str]:
        """Generate alternative approaches"""
        alternatives = []
        chosen_option = decision.choice_made
        
        # Find unchosen options
        for option in decision_definition["options"]:
            if option["id"] != chosen_option:
                alternatives.append(f"{option['text']} - {self._get_option_analysis(option['id'], decision_definition['id'])}")
        
        return alternatives
    
    def _get_option_analysis(self, option_id: str, decision_id: str) -> str:
        """Get analysis for an option"""
        analyses = {
            "venue_selection": {
                "premium": "Higher cost but superior attendee experience and fewer logistical issues",
                "standard": "Balanced approach with predictable outcomes and manageable costs",
                "alternative": "Creative differentiation but requires more planning and risk management"
            },
            "catering_strategy": {
                "full_service": "Highest attendee satisfaction but premium pricing",
                "buffet": "Cost-effective with good variety but requires space planning",
                "food_trucks": "Unique experience with Instagram-worthy moments but coordination complexity"
            },
            "marketing_channel": {
                "social_media": "Cost-effective reach with engagement metrics and targeting options",
                "traditional": "Professional credibility with established audience reach",
                "influencer": "Authentic endorsements with potential viral reach but variable reliability"
            }
        }
        
        return analyses.get(decision_id, {}).get(option_id, "Alternative approach with different trade-offs")
    
    def _get_best_practices(self, decision_id: str) -> List[str]:
        """Get industry best practices for decision type"""
        practices = {
            "venue_selection": [
                "Visit venues in person before making final decisions",
                "Review contracts carefully for hidden fees and restrictions",
                "Confirm backup plans for outdoor venues",
                "Verify insurance requirements and liability coverage"
            ],
            "catering_strategy": [
                "Conduct tasting sessions before finalizing menus",
                "Plan for 10-15% more food than confirmed attendees",
                "Accommodate dietary restrictions and cultural preferences",
                "Coordinate catering timeline with event schedule"
            ],
            "marketing_channel": [
                "Start marketing campaigns 6-8 weeks before event",
                "Create compelling calls-to-action with clear value propositions",
                "Track conversion metrics and adjust strategies accordingly",
                "Leverage early bird pricing to drive initial momentum"
            ],
            "crisis_response": [
                "Communicate transparently with stakeholders about issues",
                "Have contingency plans prepared for common problems",
                "Document all crisis decisions for post-event analysis",
                "Follow up with affected parties to maintain relationships"
            ]
        }
        
        return practices.get(decision_id, [
            "Research thoroughly before making decisions",
            "Consider long-term implications of choices",
            "Get input from experienced team members",
            "Document decisions for future reference"
        ])
    
    def _calculate_consequences(self, decision: UserDecision, impact: DecisionImpact, 
                               scenario_context: Dict) -> Dict[str, Any]:
        """Calculate decision consequences"""
        consequences = {
            "budget_impact": 0,
            "timeline_impact": 0,
            "attendee_satisfaction": 0,
            "risk_level": "medium",
            "reputation_impact": 0
        }
        
        # Impact-based consequences
        if impact == DecisionImpact.CRITICAL_SUCCESS:
            consequences.update({
                "budget_impact": 5,  # Positive impact
                "attendee_satisfaction": 20,
                "risk_level": "low",
                "reputation_impact": 15
            })
        elif impact == DecisionImpact.MAJOR_POSITIVE:
            consequences.update({
                "budget_impact": 2,
                "attendee_satisfaction": 10,
                "risk_level": "low",
                "reputation_impact": 8
            })
        elif impact == DecisionImpact.MAJOR_NEGATIVE:
            consequences.update({
                "budget_impact": -15,
                "timeline_impact": -5,
                "attendee_satisfaction": -15,
                "risk_level": "high",
                "reputation_impact": -10
            })
        elif impact == DecisionImpact.CRITICAL_FAILURE:
            consequences.update({
                "budget_impact": -25,
                "timeline_impact": -10,
                "attendee_satisfaction": -25,
                "risk_level": "critical",
                "reputation_impact": -20
            })
        
        return consequences
    
    def _load_decision_patterns(self) -> Dict:
        """Load decision pattern data"""
        # In a real implementation, this would load from a database or ML model
        return {}
    
    def _load_industry_benchmarks(self) -> Dict:
        """Load industry benchmark data"""
        # In a real implementation, this would load from industry data sources
        return {}
    
    def _load_feedback_templates(self) -> Dict:
        """Load feedback templates"""
        # In a real implementation, this would load from configuration files
        return {}

class AssessmentManager:
    """Main assessment management system"""
    
    def __init__(self):
        self.scenario_generator = MockEventScenarioGenerator()
        self.feedback_engine = AIFeedbackEngine()
        self.active_assessments = {}  # user_id -> assessment_result
    
    def create_assessment(self, user_id: int, assessment_type: AssessmentType, 
                         difficulty: DifficultyLevel, category: AssessmentCategory) -> str:
        """Create a new assessment for a user"""
        
        # Generate scenario
        scenario = self.scenario_generator.generate_scenario(difficulty, category)
        
        # Create assessment result
        assessment_id = f"assessment_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        assessment_result = AssessmentResult(
            assessment_id=assessment_id,
            user_id=user_id,
            scenario_id=scenario.id,
            start_time=datetime.utcnow(),
            completion_time=None,
            decisions=[],
            feedback=[],
            overall_score=0.0,
            category_scores={},
            achievements=[],
            areas_for_improvement=[],
            next_recommended_assessments=[],
            real_world_application=""
        )
        
        # Store active assessment
        self.active_assessments[user_id] = {
            'assessment': assessment_result,
            'scenario': scenario
        }
        
        return assessment_id
    
    def submit_decision(self, user_id: int, decision: UserDecision) -> DecisionFeedback:
        """Submit a user decision and get immediate feedback"""
        
        if user_id not in self.active_assessments:
            raise ValueError("No active assessment found for user")
        
        active = self.active_assessments[user_id]
        assessment = active['assessment']
        scenario = active['scenario']
        
        # Find decision definition
        decision_def = None
        for dp in scenario.decision_points:
            if dp["id"] == decision.decision_id:
                decision_def = dp
                break
        
        if not decision_def:
            raise ValueError("Invalid decision ID")
        
        # Generate feedback
        feedback = self.feedback_engine.analyze_decision(
            decision, scenario.scenario_context, decision_def
        )
        
        # Store decision and feedback
        assessment.decisions.append(decision)
        assessment.feedback.append(feedback)
        
        return feedback
    
    def complete_assessment(self, user_id: int) -> AssessmentResult:
        """Complete an assessment and calculate final results"""
        
        if user_id not in self.active_assessments:
            raise ValueError("No active assessment found for user")
        
        active = self.active_assessments[user_id]
        assessment = active['assessment']
        scenario = active['scenario']
        
        # Set completion time
        assessment.completion_time = datetime.utcnow()
        
        # Calculate overall score
        if assessment.feedback:
            assessment.overall_score = sum(f.score for f in assessment.feedback) / len(assessment.feedback)
        
        # Calculate category scores
        assessment.category_scores = self._calculate_category_scores(assessment, scenario)
        
        # Determine achievements
        assessment.achievements = self._determine_achievements(assessment, scenario)
        
        # Identify improvement areas
        assessment.areas_for_improvement = self._identify_improvement_areas(assessment)
        
        # Recommend next assessments
        assessment.next_recommended_assessments = self._recommend_next_assessments(assessment, scenario)
        
        # Generate real-world application
        assessment.real_world_application = self._generate_real_world_application(assessment, scenario)
        
        # Store assessment (in real implementation, save to database)
        self._store_assessment_result(assessment)
        
        # Clean up active assessment
        del self.active_assessments[user_id]
        
        return assessment
    
    def get_assessment_progress(self, user_id: int) -> Dict[str, Any]:
        """Get progress of current assessment"""
        
        if user_id not in self.active_assessments:
            return {"error": "No active assessment"}
        
        active = self.active_assessments[user_id]
        assessment = active['assessment']
        scenario = active['scenario']
        
        total_decisions = len(scenario.decision_points)
        completed_decisions = len(assessment.decisions)
        
        return {
            "assessment_id": assessment.assessment_id,
            "scenario_title": scenario.title,
            "progress_percentage": (completed_decisions / total_decisions) * 100,
            "completed_decisions": completed_decisions,
            "total_decisions": total_decisions,
            "current_score": sum(f.score for f in assessment.feedback) / len(assessment.feedback) if assessment.feedback else 0,
            "time_elapsed": (datetime.utcnow() - assessment.start_time).total_seconds() / 60,  # minutes
            "estimated_remaining": max(0, scenario.estimated_duration - ((datetime.utcnow() - assessment.start_time).total_seconds() / 60))
        }
    
    def get_scenario(self, user_id: int) -> Optional[AssessmentScenario]:
        """Get current scenario for user"""
        
        if user_id not in self.active_assessments:
            return None
        
        return self.active_assessments[user_id]['scenario']
    
    def _calculate_category_scores(self, assessment: AssessmentResult, scenario: AssessmentScenario) -> Dict[str, float]:
        """Calculate scores by category"""
        category_scores = {}
        
        if assessment.feedback:
            # Group feedback by decision category (simplified)
            planning_scores = [f.score for f in assessment.feedback if any(kw in f.decision_id for kw in ['venue', 'catering', 'timeline'])]
            marketing_scores = [f.score for f in assessment.feedback if 'marketing' in f.decision_id]
            crisis_scores = [f.score for f in assessment.feedback if 'crisis' in f.decision_id]
            budget_scores = [f.score for f in assessment.feedback if 'budget' in f.decision_id]
            
            if planning_scores:
                category_scores['planning'] = sum(planning_scores) / len(planning_scores)
            if marketing_scores:
                category_scores['marketing'] = sum(marketing_scores) / len(marketing_scores)
            if crisis_scores:
                category_scores['crisis_management'] = sum(crisis_scores) / len(crisis_scores)
            if budget_scores:
                category_scores['budget_management'] = sum(budget_scores) / len(budget_scores)
        
        return category_scores
    
    def _determine_achievements(self, assessment: AssessmentResult, scenario: AssessmentScenario) -> List[str]:
        """Determine achievements earned"""
        achievements = []
        
        # Score-based achievements
        if assessment.overall_score >= 95:
            achievements.append("Perfect Score")
        elif assessment.overall_score >= 90:
            achievements.append("Excellence in Event Management")
        elif assessment.overall_score >= 80:
            achievements.append("Strong Event Planner")
        
        # Speed achievements
        duration = (assessment.completion_time - assessment.start_time).total_seconds() / 60
        if duration <= scenario.estimated_duration * 0.75:
            achievements.append("Speed Demon")
        
        # Decision quality achievements
        excellent_decisions = [f for f in assessment.feedback if f.impact_assessment in [DecisionImpact.CRITICAL_SUCCESS, DecisionImpact.MAJOR_POSITIVE]]
        if len(excellent_decisions) == len(assessment.feedback):
            achievements.append("Decision Master")
        
        # Rationale achievements
        detailed_rationales = [d for d in assessment.decisions if d.rationale and len(d.rationale) > 100]
        if len(detailed_rationales) >= len(assessment.decisions) * 0.8:
            achievements.append("Thoughtful Planner")
        
        return achievements
    
    def _identify_improvement_areas(self, assessment: AssessmentResult) -> List[str]:
        """Identify areas needing improvement"""
        areas = []
        
        # Find lowest-scoring feedback
        if assessment.feedback:
            low_score_feedback = [f for f in assessment.feedback if f.score < 70]
            
            for feedback in low_score_feedback:
                if 'venue' in feedback.decision_id:
                    areas.append("Venue Selection Strategy")
                elif 'catering' in feedback.decision_id:
                    areas.append("Catering Management")
                elif 'marketing' in feedback.decision_id:
                    areas.append("Marketing Strategy")
                elif 'crisis' in feedback.decision_id:
                    areas.append("Crisis Management")
                elif 'budget' in feedback.decision_id:
                    areas.append("Budget Management")
        
        # Remove duplicates and limit to top 5
        areas = list(set(areas))[:5]
        
        return areas
    
    def _recommend_next_assessments(self, assessment: AssessmentResult, scenario: AssessmentScenario) -> List[str]:
        """Recommend next assessments based on performance"""
        recommendations = []
        
        current_difficulty = scenario.difficulty
        current_category = scenario.category
        
        # If performed well, suggest harder difficulty or different category
        if assessment.overall_score >= 85:
            if current_difficulty != DifficultyLevel.EXPERT:
                next_difficulty = {
                    DifficultyLevel.BEGINNER: DifficultyLevel.INTERMEDIATE,
                    DifficultyLevel.INTERMEDIATE: DifficultyLevel.ADVANCED,
                    DifficultyLevel.ADVANCED: DifficultyLevel.EXPERT
                }[current_difficulty]
                recommendations.append(f"{current_category.value.title()} - {next_difficulty.value.title()}")
            
            # Suggest different categories
            other_categories = [cat for cat in AssessmentCategory if cat != current_category][:2]
            for cat in other_categories:
                recommendations.append(f"{cat.value.title()} - {current_difficulty.value.title()}")
        
        # If performed poorly, suggest similar difficulty or easier
        elif assessment.overall_score < 70:
            if current_difficulty != DifficultyLevel.BEGINNER:
                easier_difficulty = {
                    DifficultyLevel.EXPERT: DifficultyLevel.ADVANCED,
                    DifficultyLevel.ADVANCED: DifficultyLevel.INTERMEDIATE,
                    DifficultyLevel.INTERMEDIATE: DifficultyLevel.BEGINNER
                }[current_difficulty]
                recommendations.append(f"{current_category.value.title()} - {easier_difficulty.value.title()}")
            
            # Suggest practice in same category
            recommendations.append(f"{current_category.value.title()} - Practice Session")
        
        # Always suggest complementary categories
        if current_category == AssessmentCategory.PLANNING:
            recommendations.append("Marketing - Intermediate")
        elif current_category == AssessmentCategory.MARKETING:
            recommendations.append("Crisis Management - Intermediate")
        
        return recommendations[:3]
    
    def _generate_real_world_application(self, assessment: AssessmentResult, scenario: AssessmentScenario) -> str:
        """Generate real-world application advice"""
        
        application = f"Based on your {scenario.title} assessment, here's how to apply these skills in real-world event planning:\n\n"
        
        # High performers get advanced advice
        if assessment.overall_score >= 85:
            application += "You demonstrated strong event management capabilities. Focus on:\n"
            application += "• Leading larger, more complex events\n"
            application += "• Mentoring junior event planners\n"
            application += "• Developing innovative event concepts\n"
            application += "• Building strategic vendor partnerships\n"
        
        # Medium performers get practical advice
        elif assessment.overall_score >= 70:
            application += "You show good fundamental understanding. To improve:\n"
            application += "• Practice decision-making under time pressure\n"
            application += "• Shadow experienced event planners\n"
            application += "• Join professional event planning associations\n"
            application += "• Take on progressively challenging events\n"
        
        # Lower performers get foundational advice
        else:
            application += "Focus on building strong foundations:\n"
            application += "• Study event planning fundamentals\n"
            application += "• Start with smaller, simpler events\n"
            application += "• Work closely with mentors\n"
            application += "• Practice with mock scenarios regularly\n"
        
        # Add category-specific advice
        if scenario.category == AssessmentCategory.PLANNING:
            application += "\nFor event planning specifically:\n"
            application += "• Create detailed project timelines\n"
            application += "• Build comprehensive vendor databases\n"
            application += "• Develop contingency plans for all major components\n"
        
        elif scenario.category == AssessmentCategory.MARKETING:
            application += "\nFor event marketing specifically:\n"
            application += "• Study your target audience demographics\n"
            application += "• Test marketing messages before full campaigns\n"
            application += "• Track and analyze campaign performance metrics\n"
        
        return application
    
    def _store_assessment_result(self, assessment: AssessmentResult):
        """Store assessment result in database"""
        try:
            # In a real implementation, this would store in a dedicated Assessment table
            # For now, we'll use EventAnalytics or create a simple storage mechanism
            logger.info(f"Assessment {assessment.assessment_id} completed with score {assessment.overall_score}")
            
        except Exception as e:
            logger.error(f"Error storing assessment result: {e}")

# Global instance
assessment_manager = AssessmentManager()

# Utility functions for easy access
def create_user_assessment(user_id: int, assessment_type: AssessmentType = AssessmentType.MOCK_EVENT_PLANNING,
                          difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                          category: AssessmentCategory = AssessmentCategory.PLANNING) -> str:
    """Create a new assessment for a user"""
    return assessment_manager.create_assessment(user_id, assessment_type, difficulty, category)

def submit_user_decision(user_id: int, decision_id: str, choice: str, 
                        rationale: str = "", confidence: float = 0.7) -> DecisionFeedback:
    """Submit a user decision"""
    decision = UserDecision(
        decision_id=decision_id,
        choice_made=choice,
        rationale=rationale,
        timestamp=datetime.utcnow(),
        time_taken=30,  # Default time
        confidence_level=confidence
    )
    
    return assessment_manager.submit_decision(user_id, decision)

def complete_user_assessment(user_id: int) -> AssessmentResult:
    """Complete an assessment"""
    return assessment_manager.complete_assessment(user_id)

def get_user_assessment_progress(user_id: int) -> Dict[str, Any]:
    """Get assessment progress"""
    return assessment_manager.get_assessment_progress(user_id)