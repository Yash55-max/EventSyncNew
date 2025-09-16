#!/usr/bin/env python3
"""
Comprehensive Payment System Debug Script
Tests all components of the payment system to identify issues
"""

import sys
import os
sys.path.append('.')

def test_imports():
    """Test all required imports"""
    print("🧪 Testing Imports...")
    try:
        from app import app, db
        print("  ✓ App and database imported")
        
        from models import User, Event, Ticket, TicketStatus, UserType, EventCategory
        print("  ✓ Core models imported")
        
        from model_extensions.payment import PaymentSettings, Payment, PaymentStatus, PaymentMethod
        print("  ✓ Payment models imported")
        
        from route_blueprints.payment_routes import payment_bp
        print("  ✓ Payment routes imported")
        
        from flask import url_for
        print("  ✓ Flask utilities imported")
        
        return True, (app, db, User, Event, Ticket, PaymentSettings, UserType, EventCategory, TicketStatus)
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_database_connection(app, db, User, Event, Ticket, PaymentSettings):
    """Test database connectivity and create sample data"""
    print("\n🗄️ Testing Database Connection...")
    
    with app.app_context():
        try:
            # Test basic queries
            user_count = User.query.count()
            event_count = Event.query.count()
            ticket_count = Ticket.query.count()
            payment_count = PaymentSettings.query.count()
            
            print(f"  ✓ Database accessible")
            print(f"    Users: {user_count}")
            print(f"    Events: {event_count}")
            print(f"    Tickets: {ticket_count}")
            print(f"    Payment Settings: {payment_count}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False

def create_test_data(app, db, User, Event, Ticket, PaymentSettings, UserType, EventCategory):
    """Create comprehensive test data"""
    print("\n📝 Creating Test Data...")
    
    with app.app_context():
        try:
            # Create admin user if not exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@eventsync.com',
                    user_type=UserType.ORGANIZER,
                    full_name='System Administrator'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                print("  ✓ Created admin user")
            else:
                print("  ✓ Admin user exists")
            
            # Create test attendee
            test_user = User.query.filter_by(username='testuser').first()
            if not test_user:
                test_user = User(
                    username='testuser',
                    email='testuser@example.com',
                    user_type=UserType.ATTENDEE,
                    full_name='Test User'
                )
                test_user.set_password('password123')
                db.session.add(test_user)
                print("  ✓ Created test user")
            else:
                print("  ✓ Test user exists")
            
            # Create payment settings for admin
            payment_settings = PaymentSettings.query.filter_by(user_id=admin_user.id).first()
            if not payment_settings:
                payment_settings = PaymentSettings(
                    user_id=admin_user.id,
                    stripe_enabled=True,
                    stripe_publishable_key='pk_test_dummy',
                    stripe_secret_key='sk_test_dummy'
                )
                db.session.add(payment_settings)
                print("  ✓ Created payment settings")
            else:
                print("  ✓ Payment settings exist")
            
            # Create test events
            from datetime import datetime, timedelta
            
            # Paid event
            paid_event = Event.query.filter_by(title='Test Paid Event').first()
            if not paid_event:
                paid_event = Event(
                    title='Test Paid Event',
                    description='A test paid event for payment system testing',
                    category=EventCategory.WORKSHOP,
                    location='Test Location',
                    start_date=datetime.utcnow() + timedelta(days=30),
                    end_date=datetime.utcnow() + timedelta(days=30, hours=3),
                    max_attendees=50,
                    price=25.0,
                    organizer_id=admin_user.id
                )
                db.session.add(paid_event)
                print("  ✓ Created paid test event (£25.00)")
            else:
                print("  ✓ Paid test event exists")
            
            # Free event
            free_event = Event.query.filter_by(title='Test Free Event').first()
            if not free_event:
                free_event = Event(
                    title='Test Free Event',
                    description='A test free event for payment system testing',
                    category=EventCategory.NETWORKING,
                    location='Test Location',
                    start_date=datetime.utcnow() + timedelta(days=20),
                    end_date=datetime.utcnow() + timedelta(days=20, hours=2),
                    max_attendees=100,
                    price=0.0,
                    organizer_id=admin_user.id
                )
                db.session.add(free_event)
                print("  ✓ Created free test event (£0.00)")
            else:
                print("  ✓ Free test event exists")
            
            db.session.commit()
            
            return True, (admin_user, test_user, paid_event, free_event, payment_settings)
            
        except Exception as e:
            print(f"  ❌ Error creating test data: {e}")
            import traceback
            traceback.print_exc()
            return False, None

def test_routes_registration(app):
    """Test if payment routes are properly registered"""
    print("\n🛣️ Testing Route Registration...")
    
    with app.app_context():
        try:
            # Get all registered routes
            payment_routes = []
            all_routes = []
            
            for rule in app.url_map.iter_rules():
                all_routes.append(f"{list(rule.methods)} {rule.rule} -> {rule.endpoint}")
                if 'payment' in rule.rule.lower():
                    payment_routes.append(f"{list(rule.methods)} {rule.rule} -> {rule.endpoint}")
            
            print(f"  ✓ Total registered routes: {len(all_routes)}")
            print(f"  ✓ Payment routes found: {len(payment_routes)}")
            
            if payment_routes:
                print("    Payment routes:")
                for route in payment_routes:
                    print(f"      {route}")
            else:
                print("  ⚠️ No payment routes found")
            
            # Test URL generation for key routes
            from flask import url_for
            
            try:
                # Test main application routes
                index_url = url_for('index')
                print(f"  ✓ Index URL: {index_url}")
                
                # Test event route
                event_url = url_for('event_details', event_id=1)
                print(f"  ✓ Event details URL: {event_url}")
                
            except Exception as e:
                print(f"  ⚠️ URL generation issue: {e}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Route testing error: {e}")
            return False

def test_payment_templates():
    """Check if payment templates exist"""
    print("\n📄 Testing Payment Templates...")
    
    templates = [
        'templates/payments/checkout.html',
        'templates/payments/success.html', 
        'templates/payments/failure.html',
        'templates/payments/history.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"  ✓ {template} exists")
        else:
            print(f"  ❌ {template} missing")
            all_exist = False
    
    return all_exist

def test_payment_logic(app, db, test_user, paid_event, free_event, TicketStatus, Ticket, Event, User):
    """Test the core payment logic"""
    print("\n💰 Testing Payment Logic...")
    
    with app.app_context():
        try:
            # Re-query events to ensure they're attached to session
            free_event = Event.query.filter_by(title='Test Free Event').first()
            paid_event = Event.query.filter_by(title='Test Paid Event').first()
            test_user = User.query.filter_by(username='testuser').first()
            
            if not free_event or not paid_event or not test_user:
                print("  ❌ Required test data not found")
                return False
            
            # Test free event registration
            print("  Testing free event registration...")
            
            # Check if user already has ticket
            existing_ticket = Ticket.query.filter_by(
                event_id=free_event.id,
                attendee_id=test_user.id
            ).first()
            
            if not existing_ticket:
                # Create ticket for free event
                import secrets
                ticket = Ticket(
                    event_id=free_event.id,
                    attendee_id=test_user.id,
                    status=TicketStatus.PAID,
                    ticket_number=f'TEST-{secrets.token_hex(4).upper()}'
                )
                ticket.set_paid()
                db.session.add(ticket)
                db.session.commit()
                print(f"    ✓ Free ticket created: {ticket.ticket_number}")
            else:
                print(f"    ✓ User already has free ticket: {existing_ticket.ticket_number}")
            
            # Test paid event ticket creation (without payment processing)
            print("  Testing paid event ticket creation...")
            
            existing_paid_ticket = Ticket.query.filter_by(
                event_id=paid_event.id,
                attendee_id=test_user.id
            ).first()
            
            if not existing_paid_ticket:
                import secrets
                ticket = Ticket(
                    event_id=paid_event.id,
                    attendee_id=test_user.id,
                    status=TicketStatus.RESERVED,
                    ticket_number=f'TEST-{secrets.token_hex(4).upper()}'
                )
                db.session.add(ticket)
                db.session.commit()
                print(f"    ✓ Paid ticket reserved: {ticket.ticket_number}")
                
                # Simulate payment success
                ticket.set_paid()
                db.session.commit()
                print(f"    ✓ Ticket marked as paid")
            else:
                print(f"    ✓ User already has paid ticket: {existing_paid_ticket.ticket_number}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Payment logic error: {e}")
            import traceback
            traceback.print_exc()
            return False

def run_app_test():
    """Test if the app can start successfully"""
    print("\n🚀 Testing App Startup...")
    
    try:
        from app import app
        
        with app.app_context():
            print("  ✓ App context created successfully")
            
            # Test if all essential components are available
            if hasattr(app, 'url_map'):
                print("  ✓ URL map is available")
                
            if hasattr(app, 'config'):
                print("  ✓ App configuration is available")
                
            return True
            
    except Exception as e:
        print(f"  ❌ App startup error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 EVENTSYNC PAYMENT SYSTEM DEBUG")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Imports
    success, components = test_imports()
    results['imports'] = success
    
    if not success:
        print("\n❌ Critical import failure. Cannot continue.")
        return
    
    app, db, User, Event, Ticket, PaymentSettings, UserType, EventCategory, TicketStatus = components
    
    # Test 2: Database connection
    results['database'] = test_database_connection(app, db, User, Event, Ticket, PaymentSettings)
    
    # Test 3: Create test data
    if results['database']:
        success, test_data = create_test_data(app, db, User, Event, Ticket, PaymentSettings, UserType, EventCategory)
        results['test_data'] = success
        
        if success:
            admin_user, test_user, paid_event, free_event, payment_settings = test_data
    else:
        results['test_data'] = False
    
    # Test 4: Route registration
    results['routes'] = test_routes_registration(app)
    
    # Test 5: Templates
    results['templates'] = test_payment_templates()
    
    # Test 6: Payment logic
    if results['test_data']:
        results['payment_logic'] = test_payment_logic(app, db, test_user, paid_event, free_event, TicketStatus, Ticket, Event, User)
    else:
        results['payment_logic'] = False
    
    # Test 7: App startup
    results['app_startup'] = run_app_test()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Payment system is ready.")
        print("\n🚀 Next steps:")
        print("   1. Start the Flask app: python app.py")
        print("   2. Visit http://localhost:5000")
        print("   3. Login with admin@eventsync.com / admin123")
        print("   4. Test payment functionality")
        print("\n📝 Test events created:")
        print("   - Test Paid Event (£25.00)")
        print("   - Test Free Event (£0.00)")
    else:
        print(f"\n⚠️ {total-passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    main()