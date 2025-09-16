from flask import render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import User, Event, Ticket, UserType, TicketStatus, EventCategory
from forms import LoginForm, RegistrationForm, ProfileForm, EventForm, SearchForm, TicketForm
from utils import (
    generate_ticket_number, format_date, format_date_short,
    get_upcoming_events, get_popular_events, get_event_stats,
    get_organizer_stats, get_attendee_stats
)
from datetime import datetime
import logging
import asyncio

# Import integration manager for event triggers
try:
    from integrations import integration_manager
    INTEGRATIONS_ENABLED = True
except ImportError:
    integration_manager = None
    INTEGRATIONS_ENABLED = False
    logging.warning("Integrations module not available")

# Helper function to trigger integrations
def trigger_integration(integration_func, *args, **kwargs):
    """Safely trigger integration functions without blocking main thread"""
    if INTEGRATIONS_ENABLED and integration_manager is not None:
        try:
            # Run integration in background thread to avoid blocking
            import threading
            def run_integration():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(integration_func(*args, **kwargs))
                except Exception as e:
                    logging.error(f"Integration trigger error: {e}")
                finally:
                    loop.close()
            
            thread = threading.Thread(target=run_integration)
            thread.daemon = True
            thread.start()
        except Exception as e:
            logging.error(f"Failed to trigger integration: {e}")

def register_routes(app):
    # Register chat blueprint
    try:
        from chat_routes import chat_bp
        app.register_blueprint(chat_bp)
        print("✓ Chat routes registered successfully")
    except ImportError as e:
        print(f"⚠ Chat routes not available: {e}")

    # Register calendar blueprint
    try:
        from route_blueprints.calendar_routes import calendar_bp
        app.register_blueprint(calendar_bp)
        print("✓ Calendar routes registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import calendar routes: {e}")

    # Register payment blueprint
    try:
        from route_blueprints.payment_routes import payment_bp
        app.register_blueprint(payment_bp)
        print("✓ Payment routes registered successfully")
    except ImportError as e:
        print(f"Warning: Could not import payment routes: {e}")
    
    # Register integration routes
    try:
        from integration_routes import register_integration_routes
        register_integration_routes(app)
    except ImportError as e:
        print(f"⚠ Integration routes not available: {e}")
    
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

    # Helper decorator to ensure only organizers can access routes
    def organizer_required(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.is_organizer():
                flash('Access denied. This page is only available for event organizers.', 'danger')
                return redirect(url_for('attendee_events'))
            return f(*args, **kwargs)
        return decorated_function

    # Organizer Routes
    @app.route('/organizer/dashboard')
    @login_required
    @organizer_required
    def organizer_dashboard():
        # Get statistics
        stats = get_organizer_stats(current_user)
        
        # Get recent events
        events = current_user.organized_events.order_by(Event.created_at.desc()).limit(5).all()
        
        return render_template('organizer/dashboard.html', stats=stats, events=events)

    @app.route('/organizer/events/create', methods=['GET', 'POST'])
    @login_required
    @organizer_required
    def create_event():
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
                organizer_id=current_user.id,
                # UPI Payment fields
                accept_upi_payments=form.accept_upi_payments.data,
                upi_id=form.upi_id.data if form.accept_upi_payments.data else None,
                payment_mobile=form.payment_mobile.data if form.accept_upi_payments.data else None,
                payment_instructions=form.payment_instructions.data if form.accept_upi_payments.data else None
            )
            
            db.session.add(event)
            db.session.commit()
            
            # Trigger integrations for event creation (if available)
            if INTEGRATIONS_ENABLED and integration_manager is not None:
                trigger_integration(integration_manager.on_event_created, event.id, current_user.id)
            
            flash('Event created successfully!', 'success')
            return redirect(url_for('event_details', event_id=event.id))
            
        return render_template('organizer/create_event.html', form=form)

    @app.route('/organizer/events')
    @login_required
    @organizer_required
    def manage_events():
        events = current_user.organized_events.order_by(Event.start_date.desc()).all()
        return render_template('organizer/manage_events.html', events=events)

    @app.route('/organizer/events/<int:event_id>')
    @login_required
    @organizer_required
    def event_details(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Only the event organizer can view their event management page
        if event.organizer_id != current_user.id:
            flash('You can only manage your own events.', 'danger')
            return redirect(url_for('view_event', event_id=event_id))
            
        stats = get_event_stats(event)
        tickets = event.tickets.all()
        
        return render_template('organizer/event_details.html', event=event, stats=stats, tickets=tickets)

    @app.route('/organizer/events/<int:event_id>/edit', methods=['GET', 'POST'])
    @login_required
    @organizer_required
    def edit_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Only the event organizer can edit their own events
        if event.organizer_id != current_user.id:
            flash('You can only edit your own events.', 'danger')
            return redirect(url_for('view_event', event_id=event_id))
            
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
            # Update UPI Payment fields
            event.accept_upi_payments = form.accept_upi_payments.data
            event.upi_id = form.upi_id.data if form.accept_upi_payments.data else None
            event.payment_mobile = form.payment_mobile.data if form.accept_upi_payments.data else None
            event.payment_instructions = form.payment_instructions.data if form.accept_upi_payments.data else None
            
            db.session.commit()
            
            # Trigger integrations for event update (if available)
            if INTEGRATIONS_ENABLED and integration_manager is not None:
                trigger_integration(integration_manager.on_event_updated, event.id, current_user.id)
            
            flash('Event updated successfully!', 'success')
            return redirect(url_for('event_details', event_id=event.id))
        
        # Pre-fill the form with the event data
        form.category.data = event.category.name
            
        return render_template('organizer/create_event.html', form=form, event=event, edit_mode=True)

    @app.route('/organizer/events/<int:event_id>/delete', methods=['POST'])
    @login_required
    @organizer_required
    def delete_event(event_id):
        event = Event.query.get_or_404(event_id)
        
        # Only the event organizer can delete their own events
        if event.organizer_id != current_user.id:
            flash('You can only delete your own events.', 'danger')
            return redirect(url_for('view_event', event_id=event_id))
            
        db.session.delete(event)
        db.session.commit()
        
        flash('Event deleted successfully!', 'success')
        return redirect(url_for('manage_events'))

    @app.route('/organizer/profile', methods=['GET', 'POST'])
    @login_required
    @organizer_required
    def organizer_profile():
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
                
            created_tickets = []  # Store created tickets for email sending
            for _ in range(quantity):
                ticket = Ticket(
                    event_id=event.id,
                    attendee_id=current_user.id,
                    status=TicketStatus.PAID,  # For simplicity, we're making tickets paid immediately
                    ticket_number=generate_ticket_number(),
                    paid_at=datetime.utcnow()
                )
                
                db.session.add(ticket)
                created_tickets.append(ticket)
                
            db.session.commit()
            
            # Send confirmation emails for each created ticket
            try:
                from email_notifications import email_service
                for ticket in created_tickets:
                    # Send confirmation email automatically
                    email_service.send_ticket_confirmation(
                        ticket=ticket,
                        user=current_user,
                        event=event,
                        base_url=request.url_root.rstrip('/')
                    )
                    print(f"✅ Confirmation email sent for ticket #{ticket.ticket_number}")
            except Exception as e:
                print(f"⚠️ Email sending failed: {str(e)}")
                # Don't let email failure break the registration process
            db.session.commit()
            
            # Send confirmation emails for each created ticket
            try:
                from email_notifications import email_service
                for ticket in created_tickets:
                    # Send confirmation email automatically
                    email_service.send_ticket_confirmation(
                        ticket=ticket,
                        user=current_user,
                        event=event,
                        base_url=request.url_root.rstrip('/')
                    )
                    print(f"✅ Confirmation email sent for ticket #{ticket.ticket_number}")
            except Exception as e:
                print(f"⚠️ Email sending failed: {str(e)}")
                # Don't let email failure break the registration process
            
            # Trigger integrations for ticket purchases
            if INTEGRATIONS_ENABLED and integration_manager is not None:
                # Get the tickets we just created to trigger integrations for each
                new_tickets = Ticket.query.filter_by(
                    event_id=event.id,
                    attendee_id=current_user.id
                ).order_by(Ticket.id.desc()).limit(quantity).all()
                
                for ticket in new_tickets:
                    trigger_integration(integration_manager.on_ticket_purchased, ticket.id, current_user.id)
            
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

    # Admin Routes
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        """Admin dashboard - main admin interface"""
        # For now, let organizers access admin features
        if not current_user.is_organizer():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        
        # Get system statistics
        total_users = User.query.count()
        total_events = Event.query.count() 
        total_tickets = Ticket.query.count()
        total_organizers = User.query.filter_by(user_type=UserType.ORGANIZER).count()
        total_attendees = User.query.filter_by(user_type=UserType.ATTENDEE).count()
        
        # Get recent activity
        recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        
        stats = {
            'total_users': total_users,
            'total_events': total_events,
            'total_tickets': total_tickets,
            'total_organizers': total_organizers,
            'total_attendees': total_attendees
        }
        
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             recent_events=recent_events,
                             recent_users=recent_users)
    
    @app.route('/admin/security')
    @login_required 
    def admin_security_redirect():
        """Redirect to security dashboard"""
        if not current_user.is_organizer():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
            
        # Set session role for security system
        from flask import session
        session['user_role'] = 'admin'  # Set as admin for security dashboard
        session['user_id'] = current_user.id
        session['user_email'] = current_user.email
        
        return redirect(url_for('security.security_dashboard'))
    
    @app.route('/admin/users')
    @login_required
    def admin_users():
        """Admin user management"""
        if not current_user.is_organizer():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
            
        users = User.query.order_by(User.created_at.desc()).all()
        return render_template('admin/users.html', users=users)
    
    @app.route('/admin/events')
    @login_required
    def admin_events():
        """Admin event management"""
        if not current_user.is_organizer():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
            
        events = Event.query.order_by(Event.created_at.desc()).all()
        return render_template('admin/events.html', events=events)
    
    # PWA Routes
    @app.route('/offline')
    def offline():
        """Offline page for PWA"""
        return render_template('offline.html')
    
    @app.route('/pwa-test')
    def pwa_test():
        """PWA test page"""
        return render_template('pwa_test.html')

    @app.route('/webrtc-demo')
    @login_required
    def webrtc_demo():
        """WebRTC calling demo page"""
        return render_template('webrtc_demo.html')
    
    @app.route('/chat')
    @login_required
    def chat_index():
        """Chat interface"""
        return render_template('chat/index.html')
    
    @app.route('/manifest.json')
    def manifest():
        """PWA manifest file"""
        from flask import send_from_directory
        return send_from_directory('static', 'manifest.json', mimetype='application/manifest+json')
    
    @app.route('/sw.js')
    def service_worker():
        """Service worker file"""
        from flask import send_from_directory, make_response
        response = make_response(send_from_directory('static', 'sw.js'))
        response.headers['Content-Type'] = 'application/javascript'
        response.headers['Service-Worker-Allowed'] = '/'
        return response
    
    @app.route('/api/push-subscription', methods=['POST'])
    @login_required
    def save_push_subscription():
        """Save push notification subscription"""
        try:
            subscription_data = request.get_json()
            
            # In production, save this to database
            # For now, just acknowledge receipt
            user_id = current_user.id
            
            # Log the subscription (in production, save to database)
            print(f"Push subscription for user {user_id}: {subscription_data}")
            
            return jsonify({
                'success': True,
                'message': 'Push subscription saved successfully'
            })
            
        except Exception as e:
            print(f"Error saving push subscription: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to save push subscription'
            }), 500
    
    @app.route('/share', methods=['POST'])
    def handle_share():
        """Handle Web Share Target API"""
        try:
            title = request.form.get('title', '')
            text = request.form.get('text', '')
            url = request.form.get('url', '')
            
            # Process shared content (in production, save or redirect appropriately)
            print(f"Shared content: {title}, {text}, {url}")
            
            # Redirect to appropriate page based on shared content
            if 'event' in url.lower():
                return redirect('/events')
            else:
                return redirect('/')
                
        except Exception as e:
            print(f"Error handling share: {e}")
            return redirect('/')
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
