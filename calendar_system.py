#!/usr/bin/env python3
"""
Interactive Event Calendar System
Mobile-responsive calendar with filtering, search, and event discovery
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import Event, EventCategory, EventType, Ticket, User
from database import db
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_, extract, func
import calendar
import json

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/')
def calendar_view():
    """Main calendar view"""
    return render_template('calendar/calendar.html', title='Event Calendar')

@calendar_bp.route('/api/events')
def api_get_events():
    """Get events for calendar display with filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        category = request.args.get('category')
        event_type = request.args.get('type')
        search = request.args.get('search', '').strip()
        organizer_id = request.args.get('organizer')
        
        # Base query
        query = Event.query
        
        # Date filtering
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Event.start_date >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Event.start_date <= end_dt)
            except ValueError:
                pass
        
        # Category filtering
        if category and category != 'all':
            try:
                cat_enum = EventCategory(category)
                query = query.filter(Event.category == cat_enum)
            except ValueError:
                pass
        
        # Event type filtering
        if event_type and event_type != 'all':
            try:
                type_enum = EventType(event_type)
                query = query.filter(Event.event_type == type_enum)
            except ValueError:
                pass
        
        # Search filtering
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                    Event.location.ilike(search_term)
                )
            )
        
        # Organizer filtering
        if organizer_id:
            try:
                query = query.filter(Event.organizer_id == int(organizer_id))
            except ValueError:
                pass
        
        # Execute query
        events = query.order_by(Event.start_date.asc()).all()
        
        # Format events for calendar
        calendar_events = []
        for event in events:
            # Get ticket count for this event
            ticket_count = Ticket.query.filter_by(event_id=event.id).count()
            
            # Calculate availability
            availability = "unlimited"
            if event.max_attendees > 0:
                available_spots = event.max_attendees - ticket_count
                availability = f"{available_spots}/{event.max_attendees}"
                if available_spots <= 0:
                    availability = "full"
            
            # Get organizer info
            organizer = User.query.get(event.organizer_id)
            
            calendar_events.append({
                'id': event.id,
                'title': event.title,
                'start': event.start_date.isoformat(),
                'end': event.end_date.isoformat(),
                'description': event.description or '',
                'location': event.location or '',
                'category': event.category.value if event.category else 'Other',
                'event_type': event.event_type.value if event.event_type else 'In-Person',
                'price': float(event.price) if event.price else 0.0,
                'max_attendees': event.max_attendees,
                'ticket_count': ticket_count,
                'availability': availability,
                'organizer': {
                    'id': organizer.id,
                    'name': organizer.full_name or organizer.username,
                    'email': organizer.email
                } if organizer else None,
                'color': _get_category_color(event.category),
                'url': f'/event/{event.id}',
                'virtual_link': event.virtual_link if hasattr(event, 'virtual_link') else None,
                'is_upcoming': event.start_date > datetime.utcnow(),
                'is_today': event.start_date.date() == datetime.utcnow().date(),
                'days_until': (event.start_date.date() - datetime.utcnow().date()).days if event.start_date > datetime.utcnow() else 0
            })
        
        return jsonify({
            'success': True,
            'events': calendar_events,
            'total': len(calendar_events)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/month-view')
def api_month_view():
    """Get month view data with event counts per day"""
    try:
        # Get query parameters
        year = int(request.args.get('year', datetime.utcnow().year))
        month = int(request.args.get('month', datetime.utcnow().month))
        
        # Get first and last day of the month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        
        # Get events for the month
        events = Event.query.filter(
            and_(
                Event.start_date >= first_day,
                Event.start_date <= datetime.combine(last_day, datetime.max.time())
            )
        ).all()
        
        # Group events by day
        events_by_day = {}
        for event in events:
            day = event.start_date.day
            if day not in events_by_day:
                events_by_day[day] = []
            
            events_by_day[day].append({
                'id': event.id,
                'title': event.title,
                'time': event.start_date.strftime('%H:%M'),
                'category': event.category.value if event.category else 'Other',
                'color': _get_category_color(event.category),
                'price': float(event.price) if event.price else 0.0,
                'location': event.location or 'TBD'
            })
        
        # Generate calendar grid
        cal = calendar.monthcalendar(year, month)
        month_data = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar_grid': cal,
            'events_by_day': events_by_day,
            'total_events': len(events)
        }
        
        return jsonify({
            'success': True,
            'data': month_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/week-view')
def api_week_view():
    """Get week view data"""
    try:
        # Get the start of the week (Monday)
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # Allow custom week selection
        week_start = request.args.get('week_start')
        if week_start:
            try:
                start_of_week = datetime.fromisoformat(week_start).date()
                end_of_week = start_of_week + timedelta(days=6)
            except ValueError:
                pass
        
        # Get events for the week
        events = Event.query.filter(
            and_(
                Event.start_date >= start_of_week,
                Event.start_date <= datetime.combine(end_of_week, datetime.max.time())
            )
        ).order_by(Event.start_date.asc()).all()
        
        # Group events by day
        week_events = {}
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            week_events[day.strftime('%Y-%m-%d')] = {
                'date': day.strftime('%Y-%m-%d'),
                'day_name': day.strftime('%A'),
                'day_number': day.day,
                'is_today': day == today,
                'events': []
            }
        
        for event in events:
            day_key = event.start_date.date().strftime('%Y-%m-%d')
            if day_key in week_events:
                week_events[day_key]['events'].append({
                    'id': event.id,
                    'title': event.title,
                    'start_time': event.start_date.strftime('%H:%M'),
                    'end_time': event.end_date.strftime('%H:%M') if event.end_date else None,
                    'category': event.category.value if event.category else 'Other',
                    'color': _get_category_color(event.category),
                    'location': event.location or 'TBD',
                    'price': float(event.price) if event.price else 0.0,
                    'duration_hours': (event.end_date - event.start_date).total_seconds() / 3600 if event.end_date else 1
                })
        
        return jsonify({
            'success': True,
            'data': {
                'week_start': start_of_week.strftime('%Y-%m-%d'),
                'week_end': end_of_week.strftime('%Y-%m-%d'),
                'days': list(week_events.values())
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/day-view')
def api_day_view():
    """Get detailed day view data"""
    try:
        # Get target date
        target_date = request.args.get('date')
        if target_date:
            try:
                target_dt = datetime.fromisoformat(target_date).date()
            except ValueError:
                target_dt = datetime.utcnow().date()
        else:
            target_dt = datetime.utcnow().date()
        
        # Get events for the day
        events = Event.query.filter(
            and_(
                Event.start_date >= target_dt,
                Event.start_date <= datetime.combine(target_dt, datetime.max.time())
            )
        ).order_by(Event.start_date.asc()).all()
        
        # Format events with detailed information
        day_events = []
        for event in events:
            ticket_count = Ticket.query.filter_by(event_id=event.id).count()
            organizer = User.query.get(event.organizer_id)
            
            day_events.append({
                'id': event.id,
                'title': event.title,
                'description': event.description or '',
                'start_time': event.start_date.strftime('%H:%M'),
                'end_time': event.end_date.strftime('%H:%M') if event.end_date else None,
                'duration': (event.end_date - event.start_date).total_seconds() / 3600 if event.end_date else 1,
                'location': event.location or 'TBD',
                'category': event.category.value if event.category else 'Other',
                'event_type': event.event_type.value if event.event_type else 'In-Person',
                'color': _get_category_color(event.category),
                'price': float(event.price) if event.price else 0.0,
                'max_attendees': event.max_attendees,
                'current_attendees': ticket_count,
                'spots_available': event.max_attendees - ticket_count if event.max_attendees > 0 else None,
                'organizer': {
                    'name': organizer.full_name or organizer.username,
                    'email': organizer.email
                } if organizer else None,
                'can_register': event.start_date > datetime.utcnow() and (
                    event.max_attendees == 0 or ticket_count < event.max_attendees
                )
            })
        
        return jsonify({
            'success': True,
            'data': {
                'date': target_dt.strftime('%Y-%m-%d'),
                'day_name': target_dt.strftime('%A'),
                'formatted_date': target_dt.strftime('%B %d, %Y'),
                'is_today': target_dt == datetime.utcnow().date(),
                'events': day_events,
                'total_events': len(day_events)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/search')
def api_search_events():
    """Advanced search functionality"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': True, 'results': []})
        
        # Search in title, description, and location
        search_term = f"%{query}%"
        events = Event.query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term)
            )
        ).order_by(Event.start_date.asc()).limit(20).all()
        
        results = []
        for event in events:
            organizer = User.query.get(event.organizer_id)
            results.append({
                'id': event.id,
                'title': event.title,
                'description': (event.description or '')[:100] + '...' if event.description and len(event.description) > 100 else event.description or '',
                'date': event.start_date.strftime('%Y-%m-%d'),
                'time': event.start_date.strftime('%H:%M'),
                'location': event.location or 'TBD',
                'category': event.category.value if event.category else 'Other',
                'organizer': organizer.full_name or organizer.username if organizer else 'Unknown',
                'price': float(event.price) if event.price else 0.0,
                'url': f'/event/{event.id}'
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/categories')
def api_get_categories():
    """Get available event categories with counts"""
    try:
        # Get category counts
        category_counts = db.session.query(
            Event.category,
            func.count(Event.id).label('count')
        ).filter(Event.start_date >= datetime.utcnow()).group_by(Event.category).all()
        
        categories = [{'value': 'all', 'label': 'All Categories', 'count': sum(c.count for c in category_counts)}]
        
        for category, count in category_counts:
            if category:
                categories.append({
                    'value': category.value,
                    'label': category.value.replace('_', ' ').title(),
                    'count': count,
                    'color': _get_category_color(category)
                })
        
        return jsonify({
            'success': True,
            'categories': categories
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@calendar_bp.route('/api/statistics')
def api_get_statistics():
    """Get calendar statistics"""
    try:
        now = datetime.utcnow()
        
        # Basic counts
        total_events = Event.query.count()
        upcoming_events = Event.query.filter(Event.start_date > now).count()
        today_events = Event.query.filter(
            and_(
                Event.start_date >= now.date(),
                Event.start_date <= datetime.combine(now.date(), datetime.max.time())
            )
        ).count()
        
        # This week events
        start_of_week = now.date() - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_events = Event.query.filter(
            and_(
                Event.start_date >= start_of_week,
                Event.start_date <= datetime.combine(end_of_week, datetime.max.time())
            )
        ).count()
        
        # This month events
        start_of_month = now.replace(day=1).date()
        end_of_month = (start_of_month.replace(month=start_of_month.month + 1) - timedelta(days=1)) if start_of_month.month < 12 else start_of_month.replace(year=start_of_month.year + 1, month=1) - timedelta(days=1)
        month_events = Event.query.filter(
            and_(
                Event.start_date >= start_of_month,
                Event.start_date <= datetime.combine(end_of_month, datetime.max.time())
            )
        ).count()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_events': total_events,
                'upcoming_events': upcoming_events,
                'today_events': today_events,
                'week_events': week_events,
                'month_events': month_events
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def _get_category_color(category):
    """Get color for event category"""
    color_map = {
        'CONFERENCE': '#3498db',
        'WORKSHOP': '#e74c3c',
        'SEMINAR': '#f39c12',
        'CONCERT': '#9b59b6',
        'EXHIBITION': '#1abc9c',
        'PARTY': '#e91e63',
        'NETWORKING': '#34495e',
        'HACKATHON': '#27ae60',
        'WEBINAR': '#16a085',
        'VIRTUAL_CONFERENCE': '#2980b9',
        'HYBRID_EVENT': '#8e44ad',
        'COMPETITION': '#c0392b',
        'BOOTCAMP': '#d35400',
        'MEETUP': '#7f8c8d',
        'OTHER': '#95a5a6'
    }
    
    if category and hasattr(category, 'value'):
        return color_map.get(category.value, '#95a5a6')
    
    return '#95a5a6'