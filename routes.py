from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User, Event, Ticket, UserType, TicketStatus, EventCategory
from forms import LoginForm, RegistrationForm, ProfileForm, EventForm, SearchForm, TicketForm
from utils import (
    generate_ticket_number, format_date, format_date_short,
    get_upcoming_events, get_popular_events, get_event_stats,
    get_organizer_stats, get_attendee_stats
)
from datetime import datetime
import logging

def register_routes(app):
    
    @app.template_filter('format_date')
    def _format_date(date):
        return format_date(date)
    
    @app.template_filter('format_date_short')
    def _format_date_short(date):
        return format_date_short(date)
    
    @app.template_filter('currency')
    def _format_currency(value):
        return f"${value:.2f}"
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    @app.route('/')
    def index():
        upcoming_events = get_upcoming_events()
        popular_events = get_popular_events()
        return render_template('index.html', 
                               upcoming_events=upcoming_events,
                               popular_events=popular_events)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            if current_user.is_organizer():
                return redirect(url_for('organizer_dashboard'))
            else:
                return redirect(url_for('attendee_events'))
                
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            
            if user is None or not user.check_password(form.password.data):
                flash('Invalid email or password', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            if next_page:
                return redirect(next_page)
            elif user.is_organizer():
                return redirect(url_for('organizer_dashboard'))
            else:
                return redirect(url_for('attendee_events'))
                
        return render_template('login.html', form=form)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            user_type = UserType.ORGANIZER if form.user_type.data == 'organizer' else UserType.ATTENDEE
            
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                phone=form.phone.data,
                user_type=user_type
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        return render_template('register.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # Organizer Routes
    @app.route('/organizer/dashboard')
    @login_required
    def organizer_dashboard():
        if not current_user.is_organizer():
            flash('You need to be an organizer to access this page.', 'danger')
            return redirect(url_for('index'))
            
        # Get statistics
        stats = get_organizer_stats(current_user)
        
        # Get recent events
        events = current_user.organized_events.order_by(Event.created_at.desc()).limit(5).all()
        
        return render_template('organizer/dashboard.html', stats=stats, events=events)

    @app.route('/organizer/events/create', methods=['GET', 'POST'])
    @login_required
    def create_event():
        # Only organizers can create events
        if not current_user.is_organizer():
            flash('You need to be an organizer to create events.', 'danger')
            return redirect(url_for('index'))
            
        form = EventForm()
        if form.validate_on_submit():
            category = EventCategory[form.category.data]
            
            event = Event(
                title=form.title.data,
                description=form.description.data,
                category=category,
                location=form.location.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                image_url=form.image_url.data,
                max_attendees=form.max_attendees.data,
                price=form.price.data,
                organizer_id=current_user.id
            )
            
            db.session.add(event)
            db.session.commit()
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('event_details', event_id=event.id))
            
        return render_template('organizer/create_event.html', form=form)

    @app.route('/organizer/events')
    @login_required
    def manage_events():
        if not current_user.is_organizer():
            flash('You need to be an organizer to manage events.', 'danger')
            return redirect(url_for('index'))
            
        events = current_user.organized_events.order_by(Event.start_date.desc()).all()
        return render_template('organizer/manage_events.html', events=events)

    @app.route('/organizer/events/<int:event_id>')
    @login_required
    def event_details(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Check if current user is the organizer of this event
        if event.organizer_id != current_user.id and not current_user.is_attendee():
            flash('You are not authorized to view this event.', 'danger')
            return redirect(url_for('index'))
            
        stats = get_event_stats(event)
        tickets = event.tickets.all()
        
        return render_template('organizer/event_details.html', event=event, stats=stats, tickets=tickets)

    @app.route('/organizer/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Check if current user is the organizer of this event
        if event.organizer_id != current_user.id:
            flash('You are not authorized to edit this event.', 'danger')
            return redirect(url_for('index'))
            
        form = EventForm(obj=event)
        if form.validate_on_submit():
            category = EventCategory[form.category.data]
            
            event.title = form.title.data
            event.description = form.description.data
            event.category = category
            event.location = form.location.data
            event.start_date = form.start_date.data
            event.end_date = form.end_date.data
            event.image_url = form.image_url.data
            event.max_attendees = form.max_attendees.data
            event.price = form.price.data
            
            db.session.commit()
            
            flash('Event updated successfully!', 'success')
            return redirect(url_for('event_details', event_id=event.id))
        
        # Pre-fill the form with the event data
        form.category.data = event.category.name
            
        return render_template('organizer/create_event.html', form=form, event=event, edit_mode=True)

    @app.route('/organizer/events/<int:event_id>/delete', methods=['POST'])
    @login_required
    def delete_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Check if current user is the organizer of this event
        if event.organizer_id != current_user.id:
            flash('You are not authorized to delete this event.', 'danger')
            return redirect(url_for('index'))
            
        db.session.delete(event)
        db.session.commit()
        
        flash('Event deleted successfully!', 'success')
        return redirect(url_for('manage_events'))

    @app.route('/organizer/profile', methods=['GET', 'POST'])
    @login_required
    def organizer_profile():
        if not current_user.is_organizer():
            flash('You need to be an organizer to access this page.', 'danger')
            return redirect(url_for('index'))
            
        form = ProfileForm(obj=current_user)
        
        if form.validate_on_submit():
            # Check if the current password is correct
            if form.current_password.data and not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('organizer_profile'))
                
            # Check if username is already taken by another user
            if form.username.data != current_user.username and User.query.filter_by(username=form.username.data).first():
                flash('Username is already taken.', 'danger')
                return redirect(url_for('organizer_profile'))
                
            # Check if email is already taken by another user
            if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first():
                flash('Email is already registered.', 'danger')
                return redirect(url_for('organizer_profile'))
                
            # Update user information
            current_user.username = form.username.data
            current_user.full_name = form.full_name.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            
            # Update password if a new one is provided
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
                
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('organizer_profile'))
            
        return render_template('organizer/profile.html', form=form)

    # Attendee Routes
    @app.route('/events')
    def attendee_events():
        search_form = SearchForm(request.args, meta={'csrf': False})
        
        # Query events
        query = Event.query.filter(Event.start_date > datetime.utcnow())
        
        # Apply search filters
        if search_form.query.data:
            search_query = f"%{search_form.query.data}%"
            query = query.filter(Event.title.like(search_query) | Event.description.like(search_query))
            
        if search_form.category.data:
            category = EventCategory[search_form.category.data]
            query = query.filter(Event.category == category)
            
        if search_form.date_from.data:
            query = query.filter(Event.start_date >= search_form.date_from.data)
            
        if search_form.date_to.data:
            query = query.filter(Event.start_date <= search_form.date_to.data)
            
        # Order by start date
        events = query.order_by(Event.start_date).all()
        
        return render_template('attendee/events.html', events=events, form=search_form)

    @app.route('/events/<int:event_id>')
    def view_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Check if the event is upcoming
        is_upcoming = event.is_upcoming()
        
        # Check if the current user has already registered for this event
        has_ticket = False
        if current_user.is_authenticated and current_user.is_attendee():
            ticket = Ticket.query.filter_by(
                event_id=event.id, 
                attendee_id=current_user.id,
                status=TicketStatus.PAID
            ).first()
            has_ticket = ticket is not None
            
        # Create ticket form if the user can register
        form = TicketForm() if is_upcoming and not has_ticket and not event.is_full() else None
        
        return render_template('attendee/event_details.html', 
                               event=event, 
                               form=form, 
                               has_ticket=has_ticket,
                               is_upcoming=is_upcoming)

    @app.route('/events/<int:event_id>/register', methods=['POST'])
    @login_required
    def register_for_event(event_id):
        if not current_user.is_attendee():
            flash('You need to be an attendee to register for events.', 'danger')
            return redirect(url_for('index'))
            
        event = Event.query.get_or_404(event_id)
        
        # Check if the event is upcoming
        if not event.is_upcoming():
            flash('This event has already started or ended.', 'danger')
            return redirect(url_for('view_event', event_id=event.id))
            
        # Check if the event is full
        if event.is_full():
            flash('This event is already at full capacity.', 'danger')
            return redirect(url_for('view_event', event_id=event.id))
            
        # Check if the user has already registered for this event
        existing_ticket = Ticket.query.filter_by(
            event_id=event.id, 
            attendee_id=current_user.id,
            status=TicketStatus.PAID
        ).first()
        
        if existing_ticket:
            flash('You are already registered for this event.', 'info')
            return redirect(url_for('view_event', event_id=event.id))
            
        form = TicketForm()
        if form.validate_on_submit():
            quantity = form.quantity.data
            
            # Check if there's enough capacity
            if event.max_attendees > 0 and event.attendees_count() + quantity > event.max_attendees:
                flash(f'Only {event.max_attendees - event.attendees_count()} tickets left for this event.', 'danger')
                return redirect(url_for('view_event', event_id=event.id))
                
            for _ in range(quantity):
                ticket = Ticket(
                    event_id=event.id,
                    attendee_id=current_user.id,
                    status=TicketStatus.PAID,  # For simplicity, we're making tickets paid immediately
                    ticket_number=generate_ticket_number(),
                    paid_at=datetime.utcnow()
                )
                
                db.session.add(ticket)
                
            db.session.commit()
            
            flash(f'Successfully registered for {event.title}! Check your tickets.', 'success')
            return redirect(url_for('my_tickets'))
            
        return redirect(url_for('view_event', event_id=event.id))

    @app.route('/tickets')
    @login_required
    def my_tickets():
        if not current_user.is_attendee():
            flash('You need to be an attendee to view tickets.', 'danger')
            return redirect(url_for('index'))
            
        # Get tickets for the current user
        upcoming_tickets = Ticket.query.join(Event).filter(
            Ticket.attendee_id == current_user.id,
            Ticket.status == TicketStatus.PAID,
            Event.start_date > datetime.utcnow()
        ).order_by(Event.start_date).all()
        
        past_tickets = Ticket.query.join(Event).filter(
            Ticket.attendee_id == current_user.id,
            Ticket.status == TicketStatus.PAID,
            Event.end_date <= datetime.utcnow()
        ).order_by(Event.start_date.desc()).all()
        
        return render_template('attendee/my_tickets.html', 
                               upcoming_tickets=upcoming_tickets, 
                               past_tickets=past_tickets)

    @app.route('/tickets/<int:ticket_id>/cancel', methods=['POST'])
    @login_required
    def cancel_ticket(ticket_id):
        if not current_user.is_attendee():
            flash('You need to be an attendee to cancel tickets.', 'danger')
            return redirect(url_for('index'))
            
        ticket = Ticket.query.get_or_404(ticket_id)
        
        # Check if the ticket belongs to the current user
        if ticket.attendee_id != current_user.id:
            flash('You are not authorized to cancel this ticket.', 'danger')
            return redirect(url_for('my_tickets'))
            
        # Check if the event has already started
        if not ticket.event.is_upcoming():
            flash('Cannot cancel ticket for an event that has already started.', 'danger')
            return redirect(url_for('my_tickets'))
            
        ticket.set_cancelled()
        db.session.commit()
        
        flash('Ticket cancelled successfully!', 'success')
        return redirect(url_for('my_tickets'))

    @app.route('/attendee/profile', methods=['GET', 'POST'])
    @login_required
    def attendee_profile():
        if not current_user.is_attendee():
            flash('You need to be an attendee to access this page.', 'danger')
            return redirect(url_for('index'))
            
        form = ProfileForm(obj=current_user)
        
        if form.validate_on_submit():
            # Check if the current password is correct
            if form.current_password.data and not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('attendee_profile'))
                
            # Check if username is already taken by another user
            if form.username.data != current_user.username and User.query.filter_by(username=form.username.data).first():
                flash('Username is already taken.', 'danger')
                return redirect(url_for('attendee_profile'))
                
            # Check if email is already taken by another user
            if form.email.data != current_user.email and User.query.filter_by(email=form.email.data).first():
                flash('Email is already registered.', 'danger')
                return redirect(url_for('attendee_profile'))
                
            # Update user information
            current_user.username = form.username.data
            current_user.full_name = form.full_name.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data
            
            # Update password if a new one is provided
            if form.new_password.data:
                current_user.set_password(form.new_password.data)
                
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('attendee_profile'))
            
        # Get statistics
        stats = get_attendee_stats(current_user)
            
        return render_template('attendee/profile.html', form=form, stats=stats)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
