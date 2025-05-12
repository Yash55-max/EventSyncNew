# Event Management System - XAMPP Setup Guide for Beginners

This guide will walk you through setting up and running the Event Management System using XAMPP. Follow these steps carefully, and you'll have the application up and running in no time!

## Part 1: Setting Up XAMPP

### Step 1: Download and Install XAMPP

1. Visit the [Apache Friends website](https://www.apachefriends.org/index.html)
2. Download the latest version of XAMPP for your operating system (Windows, macOS, or Linux)
3. Run the installer and follow the on-screen instructions
   - On Windows: Accept the default installation location (usually `C:\xampp`)
   - On macOS: Install to the Applications folder
   - On Linux: Install to `/opt/lampp`

### Step 2: Start XAMPP Control Panel

1. Launch the XAMPP Control Panel:
   - Windows: Start menu → XAMPP → XAMPP Control Panel
   - macOS: Open Applications folder → XAMPP → XAMPP Control Panel
   - Linux: Open terminal and run `sudo /opt/lampp/lampp start`

2. Start the following services by clicking their "Start" buttons:
   - Apache (web server)
   - MySQL (database server)

3. Verify services are running properly (the status should turn green)

## Part 2: Database Setup

### Step 1: Access phpMyAdmin

1. Open your web browser and navigate to `http://localhost/phpmyadmin`
2. You should see the phpMyAdmin interface for managing databases

### Step 2: Create a Database

1. Click on "Databases" in the top menu
2. In the "Create database" field, enter `event_management`
3. For the "Collation" dropdown, select `utf8mb4_unicode_ci`
4. Click "Create" button

## Part 3: Setting Up the Event Management Application

### Step 1: Download the Application

1. Download the Event Management System files from the provided source (zip file or repository)
2. Extract the files (if needed)

### Step 2: Place Files in Web Server Directory

1. Locate your XAMPP web server directory:
   - Windows: `C:\xampp\htdocs`
   - macOS: `/Applications/XAMPP/htdocs`
   - Linux: `/opt/lampp/htdocs`

2. Create a new folder named `event_management` in the htdocs directory
3. Copy all the downloaded application files into this folder

### Step 3: Configure Database Connection

1. Open the file `app.py` in a text editor (like Notepad, TextEdit, or VS Code)
2. Find the following line:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
   ```
3. Change it to:
   ```python
   app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/event_management"
   ```
   (This assumes the default XAMPP MySQL settings with username 'root' and no password)

## Part 4: Installing Python and Dependencies

### Step 1: Install Python

1. Download and install Python 3.11 from [python.org](https://python.org/downloads/)
2. During installation, make sure to check "Add Python to PATH"

### Step 2: Install Required Python Packages

1. Open a command prompt or terminal
2. Navigate to your project directory:
   ```
   cd C:\xampp\htdocs\event_management  # Windows
   cd /Applications/XAMPP/htdocs/event_management  # macOS
   cd /opt/lampp/htdocs/event_management  # Linux
   ```
3. Install the required packages:
   ```
   pip install flask flask-login flask-sqlalchemy flask-wtf email-validator gunicorn mysql-connector-python werkzeug
   ```

## Part 5: Running the Application

### Step 1: Initialize the Database

1. Open a command prompt or terminal
2. Navigate to your project directory (as shown in the previous step)
3. Run the following command to create database tables:
   ```
   python -c "from app import db; db.create_all()"
   ```

### Step 2: Start the Application

1. In the same command prompt or terminal, run:
   ```
   python main.py
   ```
2. You should see output indicating that the server is running

### Step 3: Access the Application

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. You should see the Event Management System homepage!

## Using the Application

1. **Register an Account**: 
   - Click on "Register" in the navigation bar
   - Fill in your details
   - Choose "Organizer" or "Attendee" based on your role
   - Click "Register"

2. **Login**:
   - Enter your email and password
   - Click "Sign In"

3. **Creating Events (Organizers Only)**:
   - Only organizers can create events
   - Click on "Create Event" in the navigation bar
   - Fill in the event details
   - Click "Create Event"

4. **Exploring Events**:
   - Click on "Explore Events" to see all upcoming events
   - Use filters to find specific events
   - Click on an event to view details

5. **Managing Tickets**:
   - After registering for an event, go to "My Tickets"
   - View and manage your ticket information

## Troubleshooting Common Issues

### Database Connection Issues

If you see "Database connection error" or similar:
1. Verify MySQL is running in XAMPP Control Panel
2. Check that the database name in your configuration matches the one you created
3. Make sure the MySQL username and password are correct

### Port Already in Use

If you see "Port 5000 already in use":
1. Edit `main.py` and change the port number in the line:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)
   ```
   to another port, such as 5001 or 8080

### Python Package Installation Problems

If you encounter errors installing packages:
1. Make sure you're using Python 3.11 or newer
2. Try running pip with administrator privileges:
   - Windows: Run Command Prompt as Administrator
   - macOS/Linux: Use `sudo pip install <package-name>`

### File Permission Issues

If you see "Permission denied" errors:
1. Make sure you have write permissions to the project directory
2. On macOS/Linux, you might need to run the server with `sudo`

## Need Further Help?

If you encounter any other issues or need additional assistance, please:
1. Check the documentation folder for more specific guides
2. Reach out to our support team
3. Post in the user forums

Happy event organizing!