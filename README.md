<<<<<<< HEAD
# Event Management System

A comprehensive Event Management System with separate interfaces for organizers and attendees. The system allows both user types to create and manage events, handle registrations, and process tickets through a colorful and intuitive web interface.

## Features

- **User Authentication System**
  - Separate registration for organizers and attendees
  - Secure login and password management
  - User profile management

- **Event Management**
  - Create events with detailed information
  - Manage event details, capacity, and pricing
  - Upload event images

- **Ticket Management**
  - Register for events and receive tickets
  - View and manage tickets
  - Cancel registrations

- **Dashboard and Analytics**
  - Visualize event statistics
  - Track attendance and registrations
  - Monitor popular event categories

## Quick Start Guide

For first-time users, we've provided a comprehensive guide to set up the application using XAMPP. Please see the [XAMPP Setup Guide for Beginners](XAMPP_SETUP_GUIDE.md) for detailed instructions.

### Prerequisites

- Python 3.11 or higher
- XAMPP (for beginners) or equivalent (MySQL, Apache)
- Modern web browser

### Running the Application

1. Start MySQL database service
2. Create a database named 'event_management'
3. Install Python dependencies:
   ```
   pip install flask flask-login flask-sqlalchemy flask-wtf email-validator gunicorn mysql-connector-python werkzeug
   ```
4. Configure the database connection in app.py
5. Run the application:
   ```
   python main.py
   ```
6. Open your browser and navigate to http://localhost:5000

## Using the Application

### Registration & Login

1. Create an account by clicking 'Register'
2. Choose your user type (Organizer or Attendee)
3. Fill in your details and submit
4. Login using your email and password

### Creating Events (Organizers Only)

Only organizers have permission to create events:

1. Click on 'Create Event' in the navigation bar
2. Fill in the event details (title, description, date/time, location, etc.)
3. Set capacity and pricing options
4. Submit the form to create your event

### Managing Events (Organizers)

1. Go to 'My Events' to see all your created events
2. Edit or delete events as needed
3. View registration statistics

### Browsing and Registering for Events (Attendees)

1. Click on 'Explore Events' to browse all available events
2. Use filters to find specific events
3. Click on an event to view details
4. Register for the event by clicking 'Get Tickets'

### Managing Tickets

1. Go to 'My Tickets' to view all your registered events
2. See event details and ticket information
3. Cancel tickets for events you can no longer attend

## Technology Stack

- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Backend**: Python, Flask
- **Database**: MySQL (via SQLAlchemy)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Visualization**: Chart.js

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FontAwesome for icons
- Bootstrap for UI components
- Chart.js for data visualization
=======
# EventSync
A web-application for managing events
>>>>>>> 59590de54fea62af6eb1206a4752b85feab8a80b
