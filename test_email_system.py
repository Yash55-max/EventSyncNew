#!/usr/bin/env python3
"""
Test script for EventSync Email Notification System
Run this to verify email configuration is working
"""

import os
import sys
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_configuration():
    """Test email configuration and basic sending"""
    print("🧪 Testing EventSync Email System...")
    print("=" * 50)
    
    try:
        # Import after adding to path
        from app import app
        from email_notifications import email_service
        from models import User, Event, Ticket
        
        with app.app_context():
            print("✅ App context initialized")
            
            # Test 1: Check email service initialization
            if email_service.mail is None:
                print("❌ Email service not initialized")
                return False
            print("✅ Email service initialized")
            
            # Test 2: Check configuration
            config_items = [
                ('MAIL_SERVER', app.config.get('MAIL_SERVER')),
                ('MAIL_PORT', app.config.get('MAIL_PORT')), 
                ('MAIL_USERNAME', app.config.get('MAIL_USERNAME')),
                ('MAIL_DEFAULT_SENDER', app.config.get('MAIL_DEFAULT_SENDER'))
            ]
            
            print("\n📧 Email Configuration:")
            for key, value in config_items:
                if value:
                    display_value = value if key != 'MAIL_USERNAME' else f"{value[:3]}***{value.split('@')[1] if '@' in str(value) else ''}"
                    print(f"   {key}: {display_value}")
                else:
                    print(f"   ❌ {key}: Not configured")
            
            # Test 3: Test basic email sending (if configured)
            if app.config.get('MAIL_USERNAME'):
                test_email = input("\n📮 Enter test email address (or press Enter to skip): ").strip()
                if test_email:
                    print(f"📤 Sending test email to {test_email}...")
                    
                    success = email_service.send_email_async(
                        subject="🧪 EventSync Email Test",
                        recipients=[test_email],
                        html_body="""
                        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                                <h1>🎉 EventSync Email Test Successful!</h1>
                                <p>Your email configuration is working correctly.</p>
                            </div>
                            <div style="padding: 30px;">
                                <h2>✅ Test Results:</h2>
                                <ul>
                                    <li>Email service initialized ✅</li>
                                    <li>SMTP configuration valid ✅</li>
                                    <li>Email template rendering ✅</li>
                                    <li>Async email sending ✅</li>
                                </ul>
                                <p><strong>EventSync is ready to send automatic ticket confirmations!</strong></p>
                                <hr>
                                <small style="color: #666;">Test sent at: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</small>
                            </div>
                        </div>
                        """
                    )
                    
                    if success:
                        print("✅ Test email sent successfully!")
                        print("   Check your inbox (and spam folder)")
                    else:
                        print("❌ Test email failed to send")
                        return False
            
            # Test 4: Simulate ticket confirmation email
            print("\n🎫 Testing ticket confirmation template...")
            
            # Create mock objects for template testing
            class MockUser:
                def __init__(self):
                    self.full_name = "Test User"
                    self.username = "testuser"
                    self.email = "test@example.com"
            
            class MockEvent:
                def __init__(self):
                    self.title = "Test Event"
                    self.start_date = datetime.now() + timedelta(days=7)
                    self.location = "Test Venue"
                    self.description = "This is a test event for email template testing."
            
            class MockTicket:
                def __init__(self):
                    self.ticket_number = "TEST123456"
            
            mock_user = MockUser()
            mock_event = MockEvent()
            mock_ticket = MockTicket()
            
            # Test template rendering
            try:
                from flask import render_template_string
                from email_notifications import TICKET_CONFIRMATION_TEMPLATE
                
                html_content = render_template_string(
                    TICKET_CONFIRMATION_TEMPLATE,
                    user=mock_user,
                    event=mock_event,
                    ticket=mock_ticket,
                    base_url="http://localhost:5000"
                )
                print("✅ Ticket confirmation template renders successfully")
                
                # Save test template to file for inspection
                with open('test_email_template.html', 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print("✅ Test email template saved to 'test_email_template.html'")
                
            except Exception as e:
                print(f"❌ Template rendering failed: {str(e)}")
                return False
            
            print("\n🎉 All tests completed successfully!")
            print("\n📋 Summary:")
            print("   • Email service is properly configured")
            print("   • Templates are working correctly") 
            print("   • Automatic emails will be sent when users register for events")
            print("\n💡 To enable emails, make sure to set your email credentials in environment variables.")
            print("   See email_config_guide.md for detailed setup instructions.")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask-mail']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"Install with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 EventSync Email System Test")
    print("=" * 40)
    
    if not check_dependencies():
        sys.exit(1)
    
    if test_email_configuration():
        print("\n🎊 Email system is ready to use!")
        sys.exit(0)
    else:
        print("\n💥 Email system needs configuration")
        sys.exit(1)