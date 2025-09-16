# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Install required Python packages
pip install flask flask-login flask-sqlalchemy flask-wtf email-validator gunicorn mysql-connector-python werkzeug

# Alternative: if using MySQL (production setup)
# Start MySQL service and create database 'event_management'
# Configure DATABASE_URL environment variable if needed
```

### Database Management
```bash
# Initialize/create database tables
python init_db.py

# Alternative database setup script
python setup_db.py

# Reset database (dev only - will lose all data)
# Delete event_management.db file and run init_db.py again
```

### Running the Application
```bash
# Start development server
python main.py

# Server runs on http://localhost:5000 by default
# Debug mode is enabled by default in development
```

### Environment Variables
```bash
# Optional environment variables for configuration:
# SESSION_SECRET - Secret key for Flask sessions (defaults to 'dev-secret-key')
# DATABASE_URL - Database connection string (defaults to SQLite: 'sqlite:///event_management.db')
```

## Architecture Overview

### Application Structure
This is a Flask-based Event Management System with a **role-based architecture** supporting two primary user types: **Organizers** and **Attendees**.

#### Core Components:
- **`app.py`** - Flask application factory, database initialization, and configuration
- **`main.py`** - Application entry point 
- **`models.py`** - SQLAlchemy ORM models defining the data schema
- **`routes.py`** - All Flask routes with role-based access control
- **`forms.py`** - WTForms for form validation and rendering
- **`utils.py`** - Helper functions for statistics, formatting, and data processing

#### Database Models:
- **User** - Authentication and profile data with UserType enum (ORGANIZER/ATTENDEE)
- **Event** - Event details with categories, pricing, and capacity management
- **Ticket** - Booking/registration system with ticket statuses
- **Enums** - UserType, EventCategory, TicketStatus for type safety

#### Template Structure:
```
templates/
├── layout.html          # Base template with navigation
├── index.html           # Public homepage  
├── login.html, register.html
├── attendee/            # Attendee-specific views
│   ├── events.html      # Browse/search events
│   ├── event_details.html
│   ├── my_tickets.html  # Ticket management
│   └── profile.html
└── organizer/           # Organizer-specific views
    ├── dashboard.html   # Statistics overview
    ├── create_event.html
    ├── manage_events.html
    └── event_details.html # Event analytics
```

### Role-Based Access Control
The application enforces strict role separation:

**Organizers can:**
- Create, edit, and delete their own events
- View event analytics and attendee lists
- Access organizer dashboard with statistics

**Attendees can:**
- Browse and search all events
- Register for events (with capacity validation)
- Manage their tickets and registrations
- View personal statistics

**Access Control Implementation:**
- Flask-Login handles authentication
- Custom role checking in route decorators
- Template-level role-based content rendering

### Database Configuration
- **Development**: SQLite (`event_management.db`) - auto-created
- **Production**: Supports MySQL via DATABASE_URL environment variable
- **Connection Pooling**: Configured for production with pool recycling
- **Migrations**: Manual via `db.create_all()` - no Flask-Migrate currently

### Key Business Logic Areas

#### Event Capacity Management
- Events can have unlimited or limited attendance (`max_attendees`)
- Real-time capacity checking during registration
- Status tracking: upcoming, ongoing, past events

#### Ticket System
- Unique ticket number generation (`utils.generate_ticket_number()`)
- Multiple ticket statuses: RESERVED, PAID, CANCELLED, USED
- Bulk ticket creation for multi-ticket registrations

#### Statistics and Analytics
- **Organizer stats**: Event counts, revenue, ticket sales
- **Event stats**: Attendance, capacity utilization, revenue
- **Attendee stats**: Tickets purchased, spending, category preferences

## Development Guidelines

### Code Organization Patterns
- **Flat structure**: All main Python modules in root directory
- **Role-based routes**: Routes grouped by user type in single `routes.py`
- **Utility functions**: Statistics and formatting helpers in `utils.py`
- **Form validation**: Centralized in `forms.py` with custom validators

### Database Access Patterns
- Use SQLAlchemy ORM relationships for data access
- Models include helper methods for business logic (e.g., `is_full()`, `is_upcoming()`)
- Statistics calculations use aggregation queries for performance

### Template and Static Files
- **Bootstrap-based UI**: Located in `templates/` with role-specific subdirectories
- **JavaScript**: Located in `static/js/` for interactive features
- **Form handling**: Uses Flask-WTF with CSRF protection

### Security Considerations
- Password hashing via Werkzeug
- CSRF protection on all forms
- Role-based authorization on sensitive routes
- Input validation through WTForms validators

### Common Development Tasks

#### Adding New Event Categories
1. Update `EventCategory` enum in `models.py`
2. Update form choices in `forms.py`
3. No database migration needed - enum changes are automatic

#### Modifying User Roles
1. Update `UserType` enum in `models.py`
2. Add role-checking methods to User model
3. Update route decorators and templates

#### Adding New Statistics
1. Create new stat calculation function in `utils.py`
2. Update relevant dashboard templates
3. Call from appropriate route handlers

#### Database Schema Changes
1. Modify models in `models.py`
2. Delete existing SQLite database file
3. Run `python init_db.py` to recreate with new schema
4. For production: implement proper migration strategy

## Important Notes

- **No automated testing framework** is currently set up
- **No requirements.txt** file - dependencies listed in README.md
- **Session management**: Uses Flask-Login with server-side sessions
- **File uploads**: Not currently implemented for event images (URLs only)
- **Email notifications**: Not implemented (would require additional setup)
- **Payment processing**: Simplified - tickets are marked as PAID immediately