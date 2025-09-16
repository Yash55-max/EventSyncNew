import os
import logging

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from database import db
from models import *
 
# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///event_management.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with the app
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Import and register routes after app context is established
def initialize_app():
    with app.app_context():
        import models  # noqa: F401
        from routes import register_routes
        
        # Register main routes
        register_routes(app)
        
        # Register advanced feature blueprints
        try:
            from security_routes import security_bp
            app.register_blueprint(security_bp)
            print("✓ Security routes registered successfully")
        except ImportError as e:
            print(f"Warning: Could not import security routes: {e}")
        
        # Register WebSocket handlers
        try:
            import websocket_handlers
            websocket_handlers.register_handlers(socketio)
            print("✓ WebSocket handlers registered successfully")
        except ImportError as e:
            print(f"Warning: Could not import websocket handlers: {e}")
        
        # Register WebRTC routes and handlers
        try:
            from webrtc_routes import register_webrtc_routes
            register_webrtc_routes(app)
            print("✓ WebRTC routes registered successfully")
        except ImportError as e:
            print(f"Warning: Could not import WebRTC routes: {e}")
        
        try:
            from webrtc_websockets import register_webrtc_websocket_handlers
            register_webrtc_websocket_handlers(socketio)
            print("✓ WebRTC WebSocket handlers registered successfully")
        except ImportError as e:
            print(f"Warning: Could not import WebRTC WebSocket handlers: {e}")
        
        # Initialize security system
        try:
            from security_manager import initialize_security_system
            security_components = initialize_security_system()
            app.config['SECURITY_MANAGER'] = security_components
            print("✓ Security system initialized successfully")
        except ImportError as e:
            print(f"Warning: Could not initialize security system: {e}")
        
        # Initialize email notification service
        try:
            from email_notifications import email_service
            email_service.init_app(app)
            print("✓ Email notification service initialized successfully")
        except ImportError as e:
            print(f"Warning: Could not initialize email service: {e}")
        
        # Create database tables
        db.create_all()
        print("✓ Database tables created successfully")
        
        # Add development admin user if doesn't exist
        try:
            admin_user = User.query.filter_by(email='admin@eventsync.com').first()
            if not admin_user:
                from werkzeug.security import generate_password_hash
                admin_user = User(
                    username='admin',
                    email='admin@eventsync.com',
                    user_type=UserType.ORGANIZER
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✓ Admin user created: admin@eventsync.com / admin123")
        except Exception as e:
            print(f"Note: Could not create admin user: {e}")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the app
initialize_app()

# Main execution

# Import sustainability and assessment routes
try:
    from sustainability_routes import register_sustainability_routes, register_assessment_routes
    SUSTAINABILITY_AVAILABLE = True
except ImportError:
    print("⚠️  Sustainability and Assessment modules not found. Some features will be unavailable.")
    SUSTAINABILITY_AVAILABLE = False

# Register sustainability and assessment routes (add this after other route registrations)
if SUSTAINABILITY_AVAILABLE:
    register_sustainability_routes(app)
    register_assessment_routes(app)
    print("✅ Sustainability and Assessment routes registered successfully")

# Register ticket system routes
try:
    from ticket_routes import ticket_bp
    app.register_blueprint(ticket_bp)
    print("✅ Ticket system routes registered successfully")
except ImportError as e:
    print(f"Warning: Could not import ticket routes: {e}")

# Register analytics dashboard
try:
    from analytics_dashboard import analytics_bp
    app.register_blueprint(analytics_bp)
    print("✅ Analytics dashboard routes registered successfully")
except ImportError as e:
    print(f"Warning: Could not import analytics routes: {e}")

# Note: Calendar and payment routes are registered in register_routes()


if __name__ == '__main__':
    print("🚀 Starting EVENTSYNC - Event Management System...")
    print("📊 Features enabled:")
    print("  • AI-Powered Matching & Recommendations")
    print("  • Advanced Collaboration Tools")
    print("  • Immersive Virtual Events (VR/AR)")
    print("  • Comprehensive Analytics Dashboard")
    print("  • Seamless Third-party Integrations")
    print("  • Enhanced Security & Privacy (RBAC, 2FA, GDPR)")
    print("  • Real-time Communication (WebSockets)")
    print("  • Modern Drag-and-Drop UI/UX")
    print("\n🌐 Access your application at: http://localhost:5000")
    print("🔒 Admin Dashboard: http://localhost:5000/admin")
    print("🛡️ Security Dashboard: http://localhost:5000/admin/security")
    print("\n👤 Default Admin Login:")
    print("  Email: admin@eventsync.com")
    print("  Password: admin123")
    print("\n" + "="*60)
    
    try:
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000, 
                    debug=True,
                    allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n👋 EVENTSYNC stopped gracefully")
