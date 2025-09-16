#!/usr/bin/env python3
"""
Advanced Analytics Dashboard
Provides comprehensive analytics for events, tickets, users, and business metrics
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from models import Event, Ticket, User, EventCategory, TicketStatus, UserType
from database import db
from datetime import datetime, timedelta
import json
from sqlalchemy import func, extract, desc

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

@analytics_bp.route('/dashboard')
@login_required
def analytics_dashboard():
    """Main analytics dashboard"""
    if current_user.user_type.value != 'organizer':
        return redirect(url_for('index'))
    
    return render_template('analytics/dashboard.html', title='Analytics Dashboard')

@analytics_bp.route('/api/overview')
@login_required
def api_overview():
    """Get overview statistics"""
    try:
        # Total events
        total_events = Event.query.count()
        
        # Total tickets
        total_tickets = Ticket.query.count()
        
        # Total users
        total_users = User.query.count()
        total_attendees = User.query.filter_by(user_type=UserType.ATTENDEE).count()
        total_organizers = User.query.filter_by(user_type=UserType.ORGANIZER).count()
        
        # Revenue calculation
        total_revenue = db.session.query(func.sum(Event.price * func.count(Ticket.id))).select_from(
            Event).join(Ticket).filter(Ticket.status == TicketStatus.PAID).scalar() or 0
        
        # Active events (upcoming)
        active_events = Event.query.filter(Event.start_date > datetime.utcnow()).count()
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_tickets = Ticket.query.filter(Ticket.created_at >= thirty_days_ago).count()
        
        # Growth metrics
        this_month_events = Event.query.filter(
            extract('year', Event.created_at) == datetime.utcnow().year,
            extract('month', Event.created_at) == datetime.utcnow().month
        ).count()
        
        last_month_events = Event.query.filter(
            extract('year', Event.created_at) == datetime.utcnow().year,
            extract('month', Event.created_at) == datetime.utcnow().month - 1
        ).count()
        
        event_growth = ((this_month_events - last_month_events) / max(last_month_events, 1)) * 100 if last_month_events > 0 else 100
        
        return jsonify({
            'success': True,
            'data': {
                'total_events': total_events,
                'total_tickets': total_tickets,
                'total_users': total_users,
                'total_attendees': total_attendees,
                'total_organizers': total_organizers,
                'total_revenue': round(total_revenue, 2),
                'active_events': active_events,
                'recent_tickets': recent_tickets,
                'event_growth': round(event_growth, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@analytics_bp.route('/api/event-stats')
@login_required
def api_event_stats():
    """Get event statistics"""
    try:
        # Events by category
        category_stats = db.session.query(
            Event.category,
            func.count(Event.id).label('count')
        ).group_by(Event.category).all()
        
        category_data = []
        for category, count in category_stats:
            category_data.append({
                'category': category.value if category else 'Other',
                'count': count
            })
        
        # Events by month (last 12 months)
        monthly_events = []
        for i in range(11, -1, -1):  # Last 12 months
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            events_count = Event.query.filter(
                Event.created_at >= month_start,
                Event.created_at <= month_end
            ).count()
            
            monthly_events.append({
                'month': month_start.strftime('%b %Y'),
                'count': events_count
            })
        
        # Popular events (by ticket count)
        popular_events = db.session.query(
            Event.title,
            func.count(Ticket.id).label('ticket_count')
        ).join(Ticket).group_by(Event.id, Event.title).order_by(desc('ticket_count')).limit(10).all()
        
        popular_data = []
        for title, count in popular_events:
            popular_data.append({
                'event': title,
                'tickets': count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'category_distribution': category_data,
                'monthly_events': monthly_events,
                'popular_events': popular_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@analytics_bp.route('/api/ticket-analytics')
@login_required
def api_ticket_analytics():
    """Get ticket analytics"""
    try:
        # Ticket status distribution
        status_stats = db.session.query(
            Ticket.status,
            func.count(Ticket.id).label('count')
        ).group_by(Ticket.status).all()
        
        status_data = []
        for status, count in status_stats:
            status_data.append({
                'status': status.value,
                'count': count
            })
        
        # Daily ticket sales (last 30 days)
        daily_sales = []
        for i in range(29, -1, -1):  # Last 30 days
            day = datetime.utcnow().date() - timedelta(days=i)
            
            tickets_count = Ticket.query.filter(
                func.date(Ticket.created_at) == day
            ).count()
            
            daily_sales.append({
                'date': day.strftime('%m/%d'),
                'tickets': tickets_count
            })
        
        # Revenue by event
        revenue_by_event = db.session.query(
            Event.title,
            (Event.price * func.count(Ticket.id)).label('revenue')
        ).join(Ticket).filter(Ticket.status == TicketStatus.PAID).group_by(
            Event.id, Event.title, Event.price
        ).order_by(desc('revenue')).limit(10).all()
        
        revenue_data = []
        for title, revenue in revenue_by_event:
            revenue_data.append({
                'event': title,
                'revenue': float(revenue or 0)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'status_distribution': status_data,
                'daily_sales': daily_sales,
                'revenue_by_event': revenue_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@analytics_bp.route('/api/user-insights')
@login_required
def api_user_insights():
    """Get user insights and demographics"""
    try:
        # User registration over time (last 12 months)
        monthly_registrations = []
        for i in range(11, -1, -1):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            registrations = User.query.filter(
                User.created_at >= month_start,
                User.created_at <= month_end
            ).count()
            
            monthly_registrations.append({
                'month': month_start.strftime('%b %Y'),
                'count': registrations
            })
        
        # User type distribution
        user_types = db.session.query(
            User.user_type,
            func.count(User.id).label('count')
        ).group_by(User.user_type).all()
        
        user_type_data = []
        for user_type, count in user_types:
            user_type_data.append({
                'type': user_type.value.title(),
                'count': count
            })
        
        # Most active users (by ticket count)
        active_users = db.session.query(
            User.username,
            func.count(Ticket.id).label('ticket_count')
        ).join(Ticket).group_by(User.id, User.username).order_by(desc('ticket_count')).limit(10).all()
        
        active_user_data = []
        for username, count in active_users:
            active_user_data.append({
                'username': username,
                'tickets': count
            })
        
        return jsonify({
            'success': True,
            'data': {
                'monthly_registrations': monthly_registrations,
                'user_type_distribution': user_type_data,
                'most_active_users': active_user_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@analytics_bp.route('/api/performance-metrics')
@login_required
def api_performance_metrics():
    """Get performance and engagement metrics"""
    try:
        # Event success metrics
        event_metrics = []
        
        events = Event.query.all()
        for event in events:
            ticket_count = event.tickets.count()
            capacity_utilization = (ticket_count / event.max_attendees * 100) if event.max_attendees > 0 else 0
            
            event_metrics.append({
                'event': event.title,
                'tickets_sold': ticket_count,
                'capacity': event.max_attendees or 'Unlimited',
                'utilization': round(capacity_utilization, 1),
                'revenue': float(event.price * ticket_count)
            })
        
        # Sort by tickets sold
        event_metrics = sorted(event_metrics, key=lambda x: x['tickets_sold'], reverse=True)[:10]
        
        # Conversion metrics
        total_events = Event.query.count()
        events_with_tickets = db.session.query(Event.id).join(Ticket).distinct().count()
        conversion_rate = (events_with_tickets / total_events * 100) if total_events > 0 else 0
        
        # Average metrics
        avg_tickets_per_event = db.session.query(func.avg(
            db.session.query(func.count(Ticket.id)).filter(Ticket.event_id == Event.id).scalar_subquery()
        )).scalar() or 0
        
        avg_revenue_per_event = db.session.query(func.avg(Event.price)).scalar() or 0
        
        return jsonify({
            'success': True,
            'data': {
                'event_performance': event_metrics,
                'conversion_rate': round(conversion_rate, 1),
                'avg_tickets_per_event': round(float(avg_tickets_per_event), 1),
                'avg_revenue_per_event': round(float(avg_revenue_per_event), 2)
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@analytics_bp.route('/export/<format>')
@login_required
def export_analytics(format):
    """Export analytics data in various formats"""
    try:
        if format not in ['csv', 'json', 'excel']:
            return jsonify({'success': False, 'message': 'Unsupported format'})
        
        # Gather all analytics data
        overview_data = api_overview().get_json()
        event_data = api_event_stats().get_json()
        ticket_data = api_ticket_analytics().get_json()
        
        export_data = {
            'generated_at': datetime.utcnow().isoformat(),
            'overview': overview_data['data'],
            'events': event_data['data'],
            'tickets': ticket_data['data']
        }
        
        if format == 'json':
            return jsonify({
                'success': True,
                'filename': f'analytics_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json',
                'data': export_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{format.upper()} export not implemented yet'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})