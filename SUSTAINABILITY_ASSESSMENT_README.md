# Sustainability Tracking and Assessment System

This document provides comprehensive documentation for the newly integrated Sustainability Tracking and Practical Assessment features in the Event Management System.

## 🌟 Overview

The Event Management System has been enhanced with two major new features:

1. **Sustainability Tracking System** - Track and reduce the environmental impact of events
2. **Practical Assessment System** - AI-powered skill development and evaluation for event planners

## 🚀 Quick Start

### Installation & Setup

1. **Verify Integration**: Run the integration script to ensure all components are properly set up
   ```bash
   python integrate_new_features.py
   ```

2. **Initialize Sample Data** (Optional):
   ```bash
   python initialize_sample_data.py
   ```

3. **Start the Application**:
   ```bash
   python app.py
   ```

4. **Access New Features**:
   - Sustainability Dashboard: `http://localhost:5000/sustainability`
   - Assessment Dashboard: `http://localhost:5000/assessments`

## 🌱 Sustainability Tracking System

### Features

#### 1. Carbon Footprint Calculator
- **Location**: `/sustainability/calculator`
- **Purpose**: Calculate comprehensive CO₂ emissions for events
- **Calculations Include**:
  - Transportation (attendee travel modes)
  - Venue energy consumption
  - Catering and food choices
  - Materials and waste management
  - Digital vs. physical resource usage

#### 2. Sustainability Dashboard
- **Location**: `/sustainability`
- **Features**:
  - Event sustainability metrics overview
  - Carbon footprint trends
  - Sustainability score (0-100%)
  - Carbon savings potential
  - Achievement tracking

#### 3. AI-Powered Recommendations
- **Automatic Suggestions**: Based on calculated carbon footprint
- **Categories**:
  - Transportation optimization
  - Energy efficiency improvements
  - Sustainable catering options
  - Waste reduction strategies
  - Digital transformation opportunities

#### 4. Green Metrics Tracking
- **Metrics Tracked**:
  - Total CO₂ emissions per event
  - Per-attendee carbon footprint
  - Sustainability score trends
  - Improvement recommendations compliance
  - Carbon neutral event achievements

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/sustainability/` | GET | Main sustainability dashboard |
| `/sustainability/calculator` | GET | Carbon footprint calculator |
| `/sustainability/api/calculate` | POST | Calculate event carbon footprint |
| `/sustainability/analyze/<event_id>` | GET | Detailed event analysis |
| `/sustainability/recommendations/<event_id>` | GET | Get recommendations for event |

### Usage Examples

#### Calculate Carbon Footprint
```python
# Sample event data
event_data = {
    'expected_attendees': 100,
    'duration_hours': 8,
    'venue_size_sqm': 500,
    'transport_modes': {
        'car': 0.4,
        'public_transport': 0.35,
        'walking_cycling': 0.25
    },
    'meal_distribution': {
        'vegetarian': 0.6,
        'meat_moderate': 0.3,
        'vegan': 0.1
    },
    'digital_adoption_ratio': 0.7,
    'energy_source': 'mixed'
}

# Calculate footprint
from sustainability import calculate_event_footprint
footprint = calculate_event_footprint(event_id, event_data)
print(f"Total CO₂: {footprint.total_co2_kg} kg")
print(f"Per attendee: {footprint.per_attendee_kg} kg")
```

## 🎓 Practical Assessment System

### Features

#### 1. Mock Event Planning Scenarios
- **Realistic Challenges**: Based on real event planning situations
- **Decision Points**: Multiple choice decisions with consequences
- **Scenario Categories**:
  - Corporate conferences
  - Wedding planning
  - Trade shows and exhibitions
  - Crisis management situations
  - Budget constraint challenges

#### 2. AI-Powered Feedback Engine
- **Intelligent Analysis**: Evaluates user decisions in context
- **Feedback Includes**:
  - Detailed scoring (0-100%)
  - Explanation of decision impacts
  - Alternative approaches
  - Industry best practices
  - Improvement suggestions
  - Real-world consequences

#### 3. Skill Assessment & Progress Tracking
- **Skill Categories**:
  - Event Planning & Strategy
  - Budget Management
  - Crisis Management
  - Marketing & Promotion
  - Logistics & Operations
  - Sustainability

- **Progress Metrics**:
  - Overall assessment score
  - Category-specific performance
  - Skill improvement trends
  - Time to completion
  - Achievement unlocks

#### 4. Interactive Learning Modules
- **Adaptive Difficulty**: Beginner, Intermediate, Advanced levels
- **Personalized Paths**: Based on performance and goals
- **Hands-On Practice**: Learn by doing, not just reading

### Assessment Types

#### 1. Mock Event Planning
- **Duration**: 30-60 minutes
- **Format**: End-to-end event planning scenario
- **Skills Tested**: Comprehensive planning abilities

#### 2. Interactive Challenges
- **Duration**: 15-30 minutes
- **Format**: Focused problem-solving scenarios
- **Skills Tested**: Specific skill areas

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/assessments/` | GET | Assessment dashboard |
| `/assessments/create` | GET/POST | Create new assessment |
| `/assessments/take/<assessment_id>` | GET | Take assessment |
| `/assessments/api/submit-decision` | POST | Submit decision |
| `/assessments/api/complete` | POST | Complete assessment |
| `/assessments/api/progress` | GET | Get user progress |
| `/assessments/results/<assessment_id>` | GET | View results |

### Usage Examples

#### Create Assessment
```python
from assessments import create_user_assessment, AssessmentType, DifficultyLevel, AssessmentCategory

assessment_id = create_user_assessment(
    user_id="user_123",
    assessment_type=AssessmentType.MOCK_EVENT_PLANNING,
    difficulty=DifficultyLevel.INTERMEDIATE,
    category=AssessmentCategory.PLANNING
)
```

#### Submit Decision
```python
from assessments import submit_user_decision, UserDecision
from datetime import datetime

decision = UserDecision(
    decision_id="decision_001",
    choice_made="option_a",
    rationale="This choice balances cost and quality effectively",
    timestamp=datetime.utcnow(),
    time_taken=45,
    confidence_level=0.8
)

feedback = submit_user_decision(user_id, decision)
print(f"Score: {feedback.score}%")
print(f"Feedback: {feedback.feedback_text}")
```

## 🏆 Gamification System

### Features

#### 1. Achievement Badges
- **Categories**:
  - Sustainability achievements
  - Planning milestones
  - Assessment accomplishments
  - Special recognitions
  - Community contributions

#### 2. Points & Levels
- **Point Categories**:
  - Event creation: 50 points
  - Sustainability actions: 25-100 points
  - Assessment completion: 75-400 points
  - Skill improvement: Variable
  - Collaboration: 50-200 points

#### 3. Progress Tracking
- **Metrics**:
  - Total points earned
  - Current level
  - Badges earned
  - Skill ratings
  - Activity streaks

### Badge Examples

| Badge | Category | Criteria | Points |
|-------|----------|----------|--------|
| Eco Warrior | Sustainability | Reduce CO₂ by 50kg+ | 100 |
| Quick Learner | Assessment | Complete first assessment with 80%+ | 75 |
| Event Creator | Planning | Create first event | 50 |
| Crisis Manager | Achievement | Handle 3 crisis scenarios successfully | 350 |

### Usage Examples

#### Award Badge
```python
from gamification import award_user_badge

# Award badge when criteria met
success = award_user_badge(
    user_id="user_123",
    badge_id="eco_warrior",
    context={"carbon_reduction_kg": 75}
)
```

#### Check Progress
```python
from gamification import get_achievement_progress

progress = get_achievement_progress("user_123")
print(f"Level: {progress['level']}")
print(f"Total Points: {progress['total_points']}")
print(f"Badges Earned: {progress['badges_earned']}")
```

## 🎨 Frontend Components

### Templates Created

1. **Sustainability Dashboard** (`templates/sustainability/dashboard.html`)
   - Overview metrics
   - Recent events analysis
   - Sustainability score visualization
   - Quick actions panel

2. **Carbon Calculator** (`templates/sustainability/calculator.html`)
   - Interactive form with sliders
   - Real-time calculations
   - Results visualization
   - Recommendations display

3. **Assessment Dashboard** (`templates/assessments/dashboard.html`)
   - Performance overview
   - Active and recent assessments
   - Skill breakdown
   - Achievement showcase

4. **Assessment Creation** (`templates/assessments/create.html`)
   - Step-by-step wizard
   - Assessment type selection
   - Difficulty and category options
   - Preview and confirmation

### Styling Features

- **Modern UI Design**: Gradient cards, smooth animations
- **Responsive Layout**: Mobile-friendly design
- **Interactive Elements**: Sliders, progress bars, modal dialogs
- **Visual Feedback**: Loading states, success animations
- **Accessibility**: ARIA labels, keyboard navigation

## 🔧 Technical Architecture

### Backend Components

1. **`sustainability.py`**: Core sustainability calculations and tracking
2. **`assessments.py`**: Assessment engine and AI feedback system
3. **`gamification.py`**: Badge system and achievement tracking
4. **`sustainability_routes.py`**: Flask routes and API endpoints

### Key Classes

#### Sustainability
- `SustainabilityTracker`: Main tracking and calculation engine
- `CarbonFootprintCalculator`: Detailed emission calculations
- `SustainabilityRecommendationEngine`: AI-powered suggestions

#### Assessments
- `AssessmentManager`: Manages assessment lifecycle
- `MockEventScenarioGenerator`: Creates realistic scenarios
- `AIFeedbackEngine`: Provides intelligent feedback

#### Gamification
- `BadgeSystem`: Manages badges and achievements
- `UserProgress`: Tracks user advancement
- `PointsEntry`: Records point transactions

### Data Models

#### Sustainability Data
```python
@dataclass
class CarbonFootprintResult:
    total_co2_kg: float
    per_attendee_kg: float
    category_breakdown: Dict[str, float]
    impact_level: ImpactLevel
    comparison_data: Dict[str, float]
    reduction_potential: float
```

#### Assessment Data
```python
@dataclass
class AssessmentScenario:
    scenario_id: str
    title: str
    description: str
    background_context: str
    constraints: List[str]
    decision_points: List[DecisionPoint]
    success_criteria: List[str]
    difficulty_level: DifficultyLevel
    category: AssessmentCategory
    estimated_duration: int
```

### Configuration

#### Environment Variables
- `SUSTAINABILITY_ENABLED`: Enable/disable sustainability features
- `ASSESSMENTS_ENABLED`: Enable/disable assessment features
- `GAMIFICATION_ENABLED`: Enable/disable gamification
- `AI_FEEDBACK_MODEL`: AI model for feedback generation

## 📊 Analytics & Reporting

### Sustainability Analytics
- Carbon footprint trends over time
- Sustainability score improvements
- Recommendation adoption rates
- Industry benchmarking

### Assessment Analytics
- Average scores by category
- Skill improvement trajectories
- Time-to-completion metrics
- Success rate analysis

### Gamification Analytics
- Badge earning patterns
- Point accumulation rates
- User engagement metrics
- Achievement unlock rates

## 🚀 Deployment

### Production Considerations

1. **Database Setup**: Ensure tables for sustainability, assessments, and gamification data
2. **Performance**: Consider caching for calculations and recommendations
3. **Security**: Validate user inputs, sanitize data
4. **Scalability**: Use async processing for complex calculations

### Environment Setup

```bash
# Install additional dependencies if needed
pip install numpy pandas scikit-learn

# Set environment variables
export SUSTAINABILITY_ENABLED=True
export ASSESSMENTS_ENABLED=True
export GAMIFICATION_ENABLED=True
```

## 🔬 Testing

### Unit Tests
```bash
# Test sustainability calculations
python -m pytest tests/test_sustainability.py

# Test assessment engine
python -m pytest tests/test_assessments.py

# Test gamification system
python -m pytest tests/test_gamification.py
```

### Integration Tests
```bash
# Test route functionality
python -m pytest tests/test_routes.py

# Test template rendering
python -m pytest tests/test_templates.py
```

## 🤝 Contributing

### Adding New Features

1. **Sustainability Metrics**: Extend calculation models in `sustainability.py`
2. **Assessment Scenarios**: Add new scenarios to `assessments.py`
3. **Badges**: Define new achievements in `gamification.py`
4. **UI Components**: Create templates in respective directories

### Code Style
- Follow PEP 8 for Python code
- Use type hints for function parameters and return values
- Include comprehensive docstrings
- Add unit tests for new functionality

## 📈 Future Enhancements

### Planned Features

1. **Advanced AI Integration**
   - Natural language feedback
   - Personalized learning paths
   - Predictive sustainability scoring

2. **Social Features**
   - Leaderboards and competitions
   - Peer collaboration tools
   - Community challenges

3. **Extended Analytics**
   - Detailed reporting dashboards
   - Export capabilities
   - Integration with external tools

4. **Mobile App**
   - Native mobile application
   - Offline assessment capabilities
   - Push notifications for achievements

## 🆘 Troubleshooting

### Common Issues

1. **Templates not rendering**: Check template directory structure
2. **Routes not found**: Verify integration script ran successfully
3. **Calculations incorrect**: Validate input data format
4. **Badges not awarded**: Check eligibility criteria and context data

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support
For technical support or questions about these features, please refer to the main project documentation or create an issue in the project repository.

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Compatibility**: Event Management System v2.0+