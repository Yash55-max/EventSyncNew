from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateTimeField, FloatField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError
from datetime import datetime
from models import User, EventCategory

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    user_type = SelectField('I am a', choices=[('attendee', 'Attendee'), ('organizer', 'Event Organizer')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already in use. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different one or log in.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', validators=[EqualTo('new_password')])
    submit = SubmitField('Update Profile')

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(max=120)])
    description = TextAreaField('Description', validators=[DataRequired()])
    category = SelectField('Category', choices=[(c.name, c.value) for c in EventCategory])
    location = StringField('Location', validators=[DataRequired(), Length(max=120)])
    start_date = DateTimeField('Start Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_date = DateTimeField('End Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    image_url = StringField('Image URL', validators=[Optional(), Length(max=255)])
    max_attendees = IntegerField('Maximum Attendees (0 for unlimited)', default=0, validators=[Optional()])
    price = FloatField('Ticket Price (0 for free)', default=0.0, validators=[Optional()])
    
    # UPI Payment Fields
    accept_upi_payments = BooleanField('Accept UPI Payments')
    upi_id = StringField('UPI ID (e.g., yourname@paytm)', validators=[Optional(), Length(max=255)])
    payment_mobile = StringField('Payment Mobile Number', validators=[Optional(), Length(max=15)])
    payment_instructions = TextAreaField('Payment Instructions', validators=[Optional()], render_kw={'placeholder': 'Additional instructions for attendees (e.g., "Send payment screenshot to WhatsApp")'})
    
    submit = SubmitField('Create Event')
    
    def validate_end_date(self, end_date):
        if end_date.data <= self.start_date.data:
            raise ValidationError('End date must be after start date.')
        
    def validate_start_date(self, start_date):
        if start_date.data < datetime.now():
            raise ValidationError('Start date cannot be in the past.')
    
    def validate_upi_id(self, upi_id):
        if self.accept_upi_payments.data:
            # Check if UPI is enabled for a free event (common mistake)
            if not self.price.data or self.price.data == 0:
                raise ValidationError('UPI payments are enabled but ticket price is ₹0. Set a price > ₹0 for paid events, or disable UPI payments for free events.')
            
            # Validate UPI requirements for paid events
            if self.price.data > 0:
                if not upi_id.data and not self.payment_mobile.data:
                    raise ValidationError('UPI ID or Payment Mobile Number is required for paid events with UPI payments.')
                if upi_id.data and '@' not in upi_id.data:
                    raise ValidationError('Please enter a valid UPI ID (e.g., yourname@paytm)')
    
    def validate_payment_mobile(self, payment_mobile):
        if self.accept_upi_payments.data and payment_mobile.data:
            if not payment_mobile.data.isdigit() or len(payment_mobile.data) != 10:
                raise ValidationError('Please enter a valid 10-digit mobile number.')

class SearchForm(FlaskForm):
    query = StringField('Search events', validators=[Optional()])
    category = SelectField('Category', choices=[('', 'All Categories')] + [(c.name, c.value) for c in EventCategory], validators=[Optional()])
    date_from = DateTimeField('From', format='%Y-%m-%d', validators=[Optional()])
    date_to = DateTimeField('To', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Search')

class TicketForm(FlaskForm):
    quantity = IntegerField('Number of tickets', default=1, validators=[DataRequired()])
    submit = SubmitField('Reserve Tickets')
