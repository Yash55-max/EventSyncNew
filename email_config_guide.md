# Email Configuration Guide for EventSync

## Setting Up Automated Ticket Emails

EventSync can automatically send ticket confirmation emails to attendees when they register for events. Follow this guide to configure email settings.

## Environment Variables

Create a `.env` file in your project root or set these environment variables:

```bash
# Gmail Configuration (Recommended)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

## Gmail Setup (Recommended)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password as `MAIL_PASSWORD`

## Alternative Email Providers

### Outlook/Hotmail
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

### Yahoo
```bash
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@yahoo.com
MAIL_PASSWORD=your-app-password
```

## Testing Email Configuration

Run this command to test your email setup:

```python
python -c "
from email_notifications import email_service
from app import app

with app.app_context():
    success = email_service.send_email_async(
        'Test Email - EventSync', 
        ['test@example.com'], 
        '<h1>Test successful!</h1><p>Your email configuration is working.</p>'
    )
    print('Email test:', 'SUCCESS' if success else 'FAILED')
"
```

## Features

✅ **Automatic ticket confirmation emails** - Sent immediately when users register
✅ **Event reminder emails** - Automated reminders 1 day and 7 days before events
✅ **Event update notifications** - Notify attendees of changes
✅ **EventSync branding** - Professional emails with logo
✅ **HTML templates** - Beautiful, mobile-responsive email design
✅ **Async sending** - Non-blocking email delivery

## Email Templates Include:

- 🎉 **Ticket Confirmation** - Welcome message with event details
- ⏰ **Event Reminders** - Countdown and preparation info  
- 📢 **Event Updates** - Important announcements
- ❌ **Event Cancellations** - Refund information

## Troubleshooting

**Emails not sending?**
1. Check environment variables are set correctly
2. Verify email credentials
3. Enable "Less secure app access" for older email providers
4. Check spam folder for test emails

**Gmail "Authentication failed"?**
- Use App Password instead of regular password
- Enable 2-Factor Authentication first

**Still having issues?**
- Check the console for error messages
- Ensure Flask-Mail is installed: `pip install Flask-Mail`