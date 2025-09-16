from flask import Blueprint, render_template, jsonify, request, current_app, g
from models import Event, User, Ticket
from database import db
from datetime import datetime, timedelta
import calendar as cal
import random

# Create a Blueprint for calendar routes
calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

# Helper function to get month calendar grid
def get_month_calendar(year, month):
    c = cal.monthcalendar(year, month)
    return c

# Helper function to get month name
def get_month_name(month):
    return cal.month_name[month]

# Helper function to generate random color (for demo purposes)
def get_random_color():
    colors = ['#4CAF50', '#2196F3', '#FFC107', '#E91E63', '#9C27B0', '#FF5722', '#607D8B']
    return random.choice(colors)

@calendar_bp.route('/')
def calendar():
    """Render the calendar page"""
    return render_template('calendar/calendar.html', title='Event Calendar')

@calendar_bp.route('/api/statistics')
def get_statistics():
    """Get calendar statistics"""
    # Calculate dates for filtering
    today = datetime.now().date()
    week_end = today + timedelta(days=7)
    
    # Query database for counts
    try:
        total_events = Event.query.count()
        upcoming_events = Event.query.filter(Event.start_date >= today).count()
        today_events = Event.query.filter(db.func.date(Event.start_date) == today).count()
        week_events = Event.query.filter(Event.start_date >= today, Event.start_date <= week_end).count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'today_events': today_events,
                'week_events': week_events
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load statistics'
        })

@calendar_bp.route('/api/categories')
def get_categories():
    """Get event categories with counts"""
    try:
        # This implementation depends on your Event model schema
        # Here's a simplified version - you might need to adjust this based on your actual model
        categories = {}
        events = Event.query.all()
        
        # Count events by category
        for event in events:
            cat_value = event.category.value if event.category else 'Other'
            if cat_value in categories:
                categories[cat_value] += 1
            else:
                categories[cat_value] = 1
        
        # Format for select dropdown
        formatted_categories = [{'value': 'all', 'label': 'All Categories', 'count': len(events)}]
        for cat, count in categories.items():
            formatted_categories.append({
                'value': cat,
                'label': cat,
                'count': count
            })
        
        return jsonify({
            'success': True,
            'categories': formatted_categories
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load categories'
        })

@calendar_bp.route('/api/month-view')
def month_view():
    """Get month view data"""
    try:
        # Get query parameters
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        # Get calendar grid
        calendar_grid = get_month_calendar(year, month)
        
        # Get events for this month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        events = Event.query.filter(
            Event.start_date >= start_date,
            Event.start_date <= end_date
        ).all()
        
        # Organize events by day
        events_by_day = {}
        for event in events:
            day = event.start_date.day
            if day not in events_by_day:
                events_by_day[day] = []
            
            events_by_day[day].append({
                'id': event.id,
                'title': event.title,
                'start_time': event.start_date.strftime('%H:%M') if event.start_date else 'All day',
                'color': get_random_color()  # In a real app, this might be a category color
            })
        
        return jsonify({
            'success': True,
            'data': {
                'year': year,
                'month': month,
                'month_name': get_month_name(month),
                'calendar_grid': calendar_grid,
                'events_by_day': events_by_day
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error generating month view: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load month view'
        })

@calendar_bp.route('/api/week-view')
def week_view():
    """Get week view data"""
    try:
        # Get start date from query parameters or use current date
        week_start_str = request.args.get('week_start')
        if week_start_str:
            week_start = datetime.fromisoformat(week_start_str).date()
        else:
            today = datetime.now().date()
            # Calculate the Monday of the current week
            week_start = today - timedelta(days=today.weekday())
        
        # Calculate the end of the week (Sunday)
        week_end = week_start + timedelta(days=6)
        
        # Get events for this week
        events = Event.query.filter(
            Event.start_date >= week_start,
            Event.start_date <= week_end
        ).all()
        
        # Prepare daily data
        days = []
        current_date = week_start
        today = datetime.now().date()
        
        while current_date <= week_end:
            day_events = [e for e in events if e.start_date.date() == current_date]
            formatted_events = []
            
            for event in day_events:
                formatted_events.append({
                    'id': event.id,
                    'title': event.title,
                    'start_time': event.start_date.strftime('%H:%M') if event.start_date else 'All day',
                    'color': get_random_color()
                })
            
            days.append({
                'date': current_date.isoformat(),
                'day_number': current_date.day,
                'day_name': current_date.strftime('%a'),
                'is_today': current_date == today,
                'events': formatted_events
            })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': {
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'days': days
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error generating week view: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load week view'
        })

@calendar_bp.route('/api/day-view')
def day_view():
    """Get day view data"""
    try:
        # Get date from query parameters or use current date
        date_str = request.args.get('date')
        if date_str:
            date = datetime.fromisoformat(date_str).date()
        else:
            date = datetime.now().date()
        
        # Get events for this day
        events = Event.query.filter(db.func.date(Event.start_date) == date).all()
        
        # Format the events
        formatted_events = []
        for event in events:
            # Determine if user can register
            can_register = True
            spots_available = None
            
            # If the event has capacity and tickets, calculate spots left
            if event.max_attendees and hasattr(event, 'tickets'):
                spots_available = event.max_attendees - event.attendees_count()
                can_register = spots_available > 0
            
            # Get organizer info
            organizer = None
            if event.organizer_id:
                user = User.query.get(event.organizer_id)
                if user:
                    organizer = {
                        'id': user.id,
                        'name': user.username
                    }
            
            formatted_events.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'start_time': event.start_date.strftime('%H:%M') if event.start_date else 'All day',
                'end_time': event.end_date.strftime('%H:%M') if event.end_date else None,
                'location': event.location,
                'category': event.category.value if event.category else 'Other',
                'price': event.price if hasattr(event, 'price') else 0,
                'spots_available': spots_available,
                'can_register': can_register,
                'organizer': organizer
            })
        
        return jsonify({
            'success': True,
            'data': {
                'date': date.isoformat(),
                'formatted_date': date.strftime('%A, %B %d, %Y'),
                'total_events': len(events),
                'events': formatted_events
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error generating day view: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to load day view'
        })

@calendar_bp.route('/api/search')
def search_events():
    """Search for events"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            })
        
        # Search in event title and description
        events = Event.query.filter(
            (Event.title.ilike(f'%{query}%')) | 
            (Event.description.ilike(f'%{query}%'))
        ).all()
        
        results = []
        for event in events:
            # Get organizer name
            organizer_name = "Unknown"
            if event.organizer_id:
                user = User.query.get(event.organizer_id)
                if user:
                    organizer_name = user.username
            
            results.append({
                'id': event.id,
                'title': event.title,
                'description': event.description[:150] + ('...' if len(event.description) > 150 else '') if event.description else '',
                'date': event.start_date.date().isoformat(),
                'time': event.start_date.strftime('%H:%M') if event.start_date else 'All day',
                'location': event.location,
                'organizer': organizer_name
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results
        })
    except Exception as e:
        current_app.logger.error(f"Error searching events: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to search events'
        })