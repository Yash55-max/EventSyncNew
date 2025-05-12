import random
import string
from datetime import datetime, timedelta
from models import Event, TicketStatus

def generate_ticket_number():
    """Generate a unique ticket number"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))

def format_date(date):
    """Format datetime for display"""
    return date.strftime("%B %d, %Y at %I:%M %p")

def format_date_short(date):
    """Format datetime for display in a shorter format"""
    return date.strftime("%m/%d/%Y %H:%M")

def get_upcoming_events(limit=6):
    """Get upcoming events"""
    return Event.query.filter(Event.start_date > datetime.utcnow()).order_by(Event.start_date).limit(limit).all()

def get_popular_events(limit=6):
    """Get popular events based on ticket count"""
    # This is a simplified version. In a real-world scenario, you might want to use 
    # a more sophisticated algorithm that accounts for recent popularity trends
    events = Event.query.filter(Event.start_date > datetime.utcnow()).all()
    events.sort(key=lambda e: e.attendees_count(), reverse=True)
    return events[:limit]

def get_event_stats(event):
    """Get statistics for an event"""
    tickets = event.tickets.all()
    
    total_tickets = len(tickets)
    reserved_tickets = sum(1 for t in tickets if t.status == TicketStatus.RESERVED)
    paid_tickets = sum(1 for t in tickets if t.status == TicketStatus.PAID)
    cancelled_tickets = sum(1 for t in tickets if t.status == TicketStatus.CANCELLED)
    used_tickets = sum(1 for t in tickets if t.status == TicketStatus.USED)
    
    revenue = sum(event.price for t in tickets if t.status in [TicketStatus.PAID, TicketStatus.USED])
    
    # Calculate percentage of capacity filled
    capacity_percent = 0
    if event.max_attendees > 0:
        active_tickets = reserved_tickets + paid_tickets
        capacity_percent = (active_tickets / event.max_attendees) * 100
    
    return {
        'total_tickets': total_tickets,
        'reserved_tickets': reserved_tickets,
        'paid_tickets': paid_tickets,
        'cancelled_tickets': cancelled_tickets, 
        'used_tickets': used_tickets,
        'revenue': revenue,
        'capacity_percent': capacity_percent
    }

def get_organizer_stats(user):
    """Get statistics for an organizer"""
    events = user.organized_events.all()
    
    total_events = len(events)
    past_events = sum(1 for e in events if e.is_past())
    upcoming_events = sum(1 for e in events if e.is_upcoming())
    ongoing_events = sum(1 for e in events if e.is_ongoing())
    
    total_tickets = sum(e.attendees_count() for e in events)
    total_revenue = sum(e.price * e.tickets.filter_by(status=TicketStatus.PAID).count() for e in events)
    
    return {
        'total_events': total_events,
        'past_events': past_events,
        'upcoming_events': upcoming_events,
        'ongoing_events': ongoing_events,
        'total_tickets': total_tickets,
        'total_revenue': total_revenue
    }

def get_attendee_stats(user):
    """Get statistics for an attendee"""
    tickets = user.tickets.all()
    
    total_tickets = len(tickets)
    upcoming_tickets = sum(1 for t in tickets if t.event.is_upcoming())
    past_tickets = sum(1 for t in tickets if t.event.is_past())
    
    money_spent = sum(t.event.price for t in tickets if t.status in [TicketStatus.PAID, TicketStatus.USED])
    
    # Get categories distribution
    categories = {}
    for ticket in tickets:
        category = ticket.event.category.value
        if category in categories:
            categories[category] += 1
        else:
            categories[category] = 1
    
    return {
        'total_tickets': total_tickets,
        'upcoming_tickets': upcoming_tickets,
        'past_tickets': past_tickets,
        'money_spent': money_spent,
        'categories': categories
    }
