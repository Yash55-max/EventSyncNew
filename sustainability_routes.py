"""
Routes for Sustainability Tracking and Assessment Systems
"""

import json
import asyncio
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user

from database import db
from models import Event, User, EventAnalytics
from sustainability import (
    sustainability_tracker, calculate_event_footprint, 
    get_sustainability_recommendations, analyze_event_sustainability
)
from assessments import (
    assessment_manager, create_user_assessment, submit_user_decision, 
    complete_user_assessment, get_user_assessment_progress,
    AssessmentType, DifficultyLevel, AssessmentCategory, UserDecision
)

# Create blueprints
sustainability_bp = Blueprint('sustainability', __name__, url_prefix='/sustainability')
assessment_bp = Blueprint('assessments', __name__, url_prefix='/assessments')

# Sustainability Routes
@sustainability_bp.route('/')
@login_required
def dashboard():
    """Sustainability dashboard"""
    try:
        # Get user's events for sustainability analysis
        user_events = Event.query.filter_by(organizer_id=current_user.id).all()
        
        # Calculate sustainability metrics for recent events
        sustainability_data = []
        total_carbon_saved = 0
        
        for event in user_events[-5:]:  # Last 5 events
            # Create sample data for demonstration
            event_data = {
                'expected_attendees': event.attendees_count() or 100,
                'duration_hours': 8,
                'venue_size_sqm': 500,
                'transport_modes': {'car': 0.4, 'public_transport': 0.3, 'walking_cycling': 0.3},
                'meal_distribution': {'vegetarian': 0.4, 'meat_moderate': 0.4, 'vegan': 0.2},
                'digital_adoption_ratio': 0.7,
                'energy_source': 'mixed',
                'waste_management': {'recycling': 0.5, 'landfill': 0.3, 'composting': 0.2}
            }
            
            # Calculate carbon footprint
            footprint = calculate_event_footprint(event.id, event_data)
            
            sustainability_data.append({
                'event_id': event.id,
                'event_title': event.title,
                'carbon_footprint': footprint.total_co2_kg,
                'per_attendee': footprint.per_attendee_kg,
                'impact_level': footprint.impact_level.value,
                'reduction_potential': footprint.reduction_potential
            })
            
            total_carbon_saved += footprint.reduction_potential
        
        # Overall sustainability stats
        sustainability_stats = {
            'total_events_analyzed': len(sustainability_data),
            'total_carbon_footprint': sum(data['carbon_footprint'] for data in sustainability_data),
            'average_per_attendee': sum(data['per_attendee'] for data in sustainability_data) / len(sustainability_data) if sustainability_data else 0,
            'total_carbon_saved_potential': total_carbon_saved,
            'sustainability_score': 78.5  # Sample score
        }
        
        return render_template('sustainability/dashboard.html', 
                             sustainability_data=sustainability_data,
                             sustainability_stats=sustainability_stats)
    
    except Exception as e:
        flash(f'Error loading sustainability dashboard: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@sustainability_bp.route('/calculator')
@login_required
def calculator():
    """Carbon footprint calculator"""
    return render_template('sustainability/calculator.html')

@sustainability_bp.route('/api/calculate', methods=['POST'])
@login_required
def calculate_footprint():
    """Calculate carbon footprint for event data"""
    try:
        event_data = request.get_json()
        
        if not event_data:
            return jsonify({'success': False, 'error': 'No event data provided'}), 400
        
        # Calculate footprint
        footprint = calculate_event_footprint(0, event_data)  # 0 for mock calculation
        
        # Get recommendations
        recommendations = get_sustainability_recommendations(event_data)
        
        return jsonify({
            'success': True,
            'footprint': {
                'total_co2_kg': footprint.total_co2_kg,
                'per_attendee_kg': footprint.per_attendee_kg,
                'impact_level': footprint.impact_level.value,
                'category_breakdown': footprint.category_breakdown,
                'comparison_data': footprint.comparison_data,
                'reduction_potential': footprint.reduction_potential
            },
            'recommendations': [
                {
                    'title': rec.title,
                    'description': rec.description,
                    'category': rec.category.value,
                    'impact_reduction': rec.impact_reduction,
                    'cost_impact': rec.cost_impact,
                    'difficulty': rec.difficulty,
                    'implementation_steps': rec.implementation_steps
                } for rec in recommendations
            ]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sustainability_bp.route('/analyze/<int:event_id>')
@login_required
def analyze_event(event_id):
    """Analyze sustainability of specific event"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if user owns the event
        if event.organizer_id != current_user.id:
            flash('You can only analyze your own events.', 'error')
            return redirect(url_for('sustainability.dashboard'))
        
        # Create comprehensive event data
        event_data = {
            'expected_attendees': event.attendees_count() or 100,
            'duration_hours': 8,
            'venue_size_sqm': 500,
            'event_type': event.category.value if event.category else 'conference',
            'transport_modes': {'car': 0.4, 'public_transport': 0.3, 'walking_cycling': 0.3},
            'meal_distribution': {'vegetarian': 0.4, 'meat_moderate': 0.4, 'vegan': 0.2},
            'digital_adoption_ratio': 0.7,
            'energy_source': 'mixed',
            'waste_management': {'recycling': 0.5, 'landfill': 0.3, 'composting': 0.2},
            'local_sourcing_ratio': 0.6,
            'materials': {
                'paper_kg': event.attendees_count() * 0.1,
                'plastic_kg': event.attendees_count() * 0.05
            }
        }
        
        # Perform comprehensive analysis
        metrics = analyze_event_sustainability(event_id, event_data)
        
        return render_template('sustainability/analysis.html', 
                             event=event,
                             metrics=metrics)
    
    except Exception as e:
        flash(f'Error analyzing event sustainability: {str(e)}', 'error')
        return redirect(url_for('sustainability.dashboard'))

@sustainability_bp.route('/recommendations/<int:event_id>')
@login_required
def event_recommendations(event_id):
    """Get sustainability recommendations for event"""
    try:
        event = Event.query.get_or_404(event_id)
        
        # Check if user owns the event
        if event.organizer_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Sample event data
        event_data = {
            'expected_attendees': event.attendees_count() or 100,
            'duration_hours': 8,
            'transport_modes': {'car': 0.5, 'public_transport': 0.3, 'walking_cycling': 0.2},
            'meal_distribution': {'meat_heavy': 0.3, 'meat_moderate': 0.4, 'vegetarian': 0.3}
        }
        
        recommendations = get_sustainability_recommendations(event_data)
        
        return jsonify({
            'success': True,
            'recommendations': [
                {
                    'title': rec.title,
                    'description': rec.description,
                    'category': rec.category.value,
                    'impact_reduction': rec.impact_reduction,
                    'cost_impact': rec.cost_impact,
                    'difficulty': rec.difficulty,
                    'implementation_steps': rec.implementation_steps,
                    'estimated_savings': rec.estimated_savings
                } for rec in recommendations
            ]
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Assessment Routes
@assessment_bp.route('/')
@login_required
def dashboard():
    """Assessment dashboard"""
    try:
        # Check for active assessment
        progress = get_user_assessment_progress(current_user.id)
        
        # Sample completed assessments
        completed_assessments = [
            {
                'id': 'assessment_001',
                'title': 'Corporate Conference Planning',
                'category': 'Planning',
                'difficulty': 'Intermediate',
                'score': 85,
                'completed_date': '2024-01-15',
                'achievements': ['Strong Event Planner', 'Thoughtful Planner']
            },
            {
                'id': 'assessment_002', 
                'title': 'Crisis Management Challenge',
                'category': 'Crisis Management',
                'difficulty': 'Advanced',
                'score': 78,
                'completed_date': '2024-01-10',
                'achievements': ['Quick Decision Maker']
            }
        ]
        
        # Assessment stats
        assessment_stats = {
            'total_completed': len(completed_assessments),
            'average_score': sum(a['score'] for a in completed_assessments) / len(completed_assessments) if completed_assessments else 0,
            'achievements_earned': 3,
            'hours_practiced': 12.5
        }
        
        return render_template('assessments/dashboard.html',
                             progress=progress,
                             completed_assessments=completed_assessments,
                             assessment_stats=assessment_stats)
    
    except Exception as e:
        flash(f'Error loading assessment dashboard: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@assessment_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_assessment():
    """Create new assessment"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            assessment_type = AssessmentType(data.get('assessment_type', 'mock_event_planning'))
            difficulty = DifficultyLevel(data.get('difficulty', 'intermediate'))
            category = AssessmentCategory(data.get('category', 'planning'))
            
            assessment_id = create_user_assessment(current_user.id, assessment_type, difficulty, category)
            
            return jsonify({
                'success': True,
                'assessment_id': assessment_id,
                'redirect_url': url_for('assessments.take_assessment', assessment_id=assessment_id)
            })
        
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('assessments/create.html')

@assessment_bp.route('/take/<assessment_id>')
@login_required
def take_assessment(assessment_id):
    """Take assessment"""
    try:
        # Get current scenario
        scenario = assessment_manager.get_scenario(current_user.id)
        
        if not scenario:
            flash('No active assessment found.', 'error')
            return redirect(url_for('assessments.dashboard'))
        
        # Get progress
        progress = get_user_assessment_progress(current_user.id)
        
        return render_template('assessments/take.html',
                             scenario=scenario,
                             progress=progress,
                             assessment_id=assessment_id)
    
    except Exception as e:
        flash(f'Error loading assessment: {str(e)}', 'error')
        return redirect(url_for('assessments.dashboard'))

@assessment_bp.route('/api/submit-decision', methods=['POST'])
@login_required
def submit_decision():
    """Submit assessment decision"""
    try:
        data = request.get_json()
        
        decision_id = data.get('decision_id')
        choice = data.get('choice')
        rationale = data.get('rationale', '')
        confidence = data.get('confidence', 0.7)
        time_taken = data.get('time_taken', 30)
        
        # Create decision object
        decision = UserDecision(
            decision_id=decision_id,
            choice_made=choice,
            rationale=rationale,
            timestamp=datetime.utcnow(),
            time_taken=time_taken,
            confidence_level=confidence
        )
        
        # Submit decision and get feedback
        feedback = assessment_manager.submit_decision(current_user.id, decision)
        
        return jsonify({
            'success': True,
            'feedback': {
                'decision_id': feedback.decision_id,
                'impact_assessment': feedback.impact_assessment.value,
                'score': feedback.score,
                'feedback_text': feedback.feedback_text,
                'improvement_suggestions': feedback.improvement_suggestions,
                'alternative_approaches': feedback.alternative_approaches,
                'industry_best_practices': feedback.industry_best_practices,
                'consequences': feedback.consequences
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@assessment_bp.route('/api/complete', methods=['POST'])
@login_required
def complete_assessment():
    """Complete assessment"""
    try:
        result = complete_user_assessment(current_user.id)
        
        return jsonify({
            'success': True,
            'result': {
                'assessment_id': result.assessment_id,
                'overall_score': result.overall_score,
                'category_scores': result.category_scores,
                'achievements': result.achievements,
                'areas_for_improvement': result.areas_for_improvement,
                'next_recommended_assessments': result.next_recommended_assessments,
                'real_world_application': result.real_world_application
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@assessment_bp.route('/api/progress')
@login_required
def get_progress():
    """Get assessment progress"""
    try:
        progress = get_user_assessment_progress(current_user.id)
        return jsonify({'success': True, 'progress': progress})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@assessment_bp.route('/results/<assessment_id>')
@login_required
def view_results(assessment_id):
    """View assessment results"""
    try:
        # In a real implementation, you'd fetch results from database
        # For now, we'll show a sample results page
        
        sample_results = {
            'assessment_id': assessment_id,
            'overall_score': 85,
            'category_scores': {
                'planning': 88,
                'marketing': 82,
                'crisis_management': 85
            },
            'achievements': ['Strong Event Planner', 'Thoughtful Decision Maker'],
            'areas_for_improvement': ['Budget Management', 'Risk Assessment'],
            'recommendations': ['Try Advanced Crisis Management', 'Practice Marketing Strategy'],
            'real_world_application': 'Focus on developing contingency plans and building vendor relationships.'
        }
        
        return render_template('assessments/results.html', results=sample_results)
    
    except Exception as e:
        flash(f'Error loading results: {str(e)}', 'error')
        return redirect(url_for('assessments.dashboard'))

# Register blueprint functions
def register_sustainability_routes(app):
    """Register sustainability routes with the Flask app"""
    app.register_blueprint(sustainability_bp)
    print("✓ Sustainability routes registered successfully")

def register_assessment_routes(app):
    """Register assessment routes with the Flask app"""
    app.register_blueprint(assessment_bp)
    print("✓ Assessment routes registered successfully")