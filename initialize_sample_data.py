
"""
Sample data initialization for Sustainability and Assessment features
"""

from sustainability import sustainability_tracker, SustainabilityTracker
from assessments import assessment_manager, AssessmentManager  
from gamification import gamification_system, award_user_points, PointCategory
from datetime import datetime

def initialize_sample_data():
    """Initialize sample data for demo purposes"""
    
    # Sample user ID (replace with actual user ID from your system)
    sample_user_id = "user_123"
    
    # Initialize sample sustainability data
    sample_event_data = {
        'expected_attendees': 150,
        'duration_hours': 8,
        'venue_size_sqm': 400,
        'transport_modes': {'car': 0.4, 'public_transport': 0.35, 'walking_cycling': 0.25},
        'meal_distribution': {'vegetarian': 0.6, 'meat_moderate': 0.3, 'vegan': 0.1},
        'digital_adoption_ratio': 0.8,
        'energy_source': 'mixed',
        'waste_management': {'recycling': 0.6, 'landfill': 0.2, 'composting': 0.2}
    }
    
    print("✅ Sample sustainability data prepared")
    
    # Award some sample points
    award_user_points(sample_user_id, PointCategory.EVENT_CREATION, 50, "Created first event")
    award_user_points(sample_user_id, PointCategory.SUSTAINABILITY_ACTION, 75, "Used carbon calculator")
    
    print("✅ Sample gamification data created")
    
    return True

if __name__ == "__main__":
    initialize_sample_data()
    print("🎉 Sample data initialization completed!")
