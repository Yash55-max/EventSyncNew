#!/usr/bin/env python3
"""
Ticket Routes for PDF Generation and QR Check-in System
Compatible with existing Ticket model
"""

from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify, make_response
from flask_login import login_required, current_user
from models import Ticket, Event, User, db
import json
from datetime import datetime
import qrcode
import io
import base64
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.barcode import qr
from PIL import Image as PILImage

ticket_bp = Blueprint('tickets', __name__, url_prefix='/tickets')

@ticket_bp.route('/my-tickets')
@login_required
def my_tickets():
    """View user's tickets"""
    if current_user.user_type.value != 'attendee':
        flash('This page is for attendees only.', 'error')
        return redirect(url_for('index'))
    
    # Get user's tickets
    tickets = Ticket.query.filter_by(attendee_id=current_user.id).all()
    
    # Get event details for each ticket
    tickets_data = []
    for ticket in tickets:
        event = Event.query.get(ticket.event_id)
        if event:
            tickets_data.append({
                'ticket': ticket,
                'event': event,
                'can_download': True
            })
    
    return render_template('tickets/my_tickets_simple.html', 
                         tickets_data=tickets_data,
                         title='My Tickets')

@ticket_bp.route('/check-in')
@login_required
def check_in_page():
    """QR code check-in page for organizers"""
    if current_user.user_type.value != 'organizer':
        flash('Access denied. Only organizers can access check-in.', 'error')
        return redirect(url_for('index'))
    
    # Get organizer's events
    user_events = Event.query.filter_by(organizer_id=current_user.id).all()
    
    return render_template('tickets/check_in_simple.html', 
                         user_events=user_events,
                         title='Event Check-in')

@ticket_bp.route('/verify-ticket', methods=['POST'])
@login_required
def verify_ticket():
    """Verify ticket for check-in"""
    try:
        if current_user.user_type.value != 'organizer':
            return jsonify({'success': False, 'message': 'Access denied'})
        
        data = request.get_json()
        ticket_number = data.get('ticket_number', '').strip()
        event_id = data.get('event_id')
        
        if not ticket_number or not event_id:
            return jsonify({'success': False, 'message': 'Missing ticket number or event ID'})
        
        # Find ticket by number
        ticket = Ticket.query.filter_by(ticket_number=ticket_number).first()
        
        if not ticket:
            return jsonify({'success': False, 'message': 'Ticket not found'})
        
        # Verify event matches
        if str(ticket.event_id) != str(event_id):
            return jsonify({'success': False, 'message': 'Ticket is not for this event'})
        
        # Get event and verify organizer
        event = Event.query.get(event_id)
        if not event or event.organizer_id != current_user.id:
            return jsonify({'success': False, 'message': 'You do not manage this event'})
        
        # Get attendee info
        attendee = User.query.get(ticket.attendee_id)
        
        # Check if ticket is already used
        if ticket.status.value == 'Used':
            return jsonify({
                'success': False, 
                'message': 'Ticket already used',
                'data': {
                    'attendee_name': attendee.full_name or attendee.username,
                    'ticket_number': ticket.ticket_number,
                    'status': 'Already Used'
                }
            })
        
        # Mark ticket as used
        ticket.set_used()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Check-in successful!',
            'data': {
                'attendee_name': attendee.full_name or attendee.username,
                'attendee_email': attendee.email,
                'ticket_number': ticket.ticket_number,
                'event_title': event.title,
                'check_in_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Checked In'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error verifying ticket: {str(e)}'})

@ticket_bp.route('/download/<int:ticket_id>')
@login_required
def download_ticket(ticket_id):
    """Generate and download ticket PDF"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if user owns this ticket
    if ticket.attendee_id != current_user.id:
        flash('Access denied. You can only download your own tickets.', 'error')
        return redirect(url_for('tickets.my_tickets'))
    
    try:
        # Generate PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        event_style = ParagraphStyle(
            'EventTitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=10
        )
        
        # Title
        story.append(Paragraph('🎫 Event Ticket', title_style))
        story.append(Spacer(1, 20))
        
        # Event Title
        story.append(Paragraph(f'<b>{ticket.event.title}</b>', event_style))
        story.append(Spacer(1, 20))
        
        # Generate QR Code
        qr_data = f'TICKET-{ticket.ticket_number}-EVENT-{ticket.event_id}'
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to buffer
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Add QR code to PDF
        qr_image = Image(qr_buffer, width=2*inch, height=2*inch)
        qr_image.hAlign = 'CENTER'
        story.append(qr_image)
        story.append(Spacer(1, 30))
        
        # Ticket Information
        story.append(Paragraph('<b>Ticket Information:</b>', info_style))
        story.append(Paragraph(f'<b>Ticket ID:</b> {ticket.ticket_number}', info_style))
        story.append(Paragraph(f'<b>Attendee:</b> {current_user.full_name or current_user.username}', info_style))
        story.append(Paragraph(f'<b>Status:</b> {ticket.status.value}', info_style))
        story.append(Spacer(1, 20))
        
        # Event Information
        story.append(Paragraph('<b>Event Details:</b>', info_style))
        story.append(Paragraph(f'<b>Date:</b> {ticket.event.start_date.strftime("%B %d, %Y")}', info_style))
        story.append(Paragraph(f'<b>Time:</b> {ticket.event.start_date.strftime("%I:%M %p")}', info_style))
        story.append(Paragraph(f'<b>Location:</b> {ticket.event.location}', info_style))
        story.append(Paragraph(f'<b>Organizer:</b> {ticket.event.organizer.username}', info_style))
        story.append(Spacer(1, 30))
        
        # Instructions
        story.append(Paragraph('<b>Instructions:</b>', info_style))
        story.append(Paragraph('• Present this QR code at the event entrance for check-in', info_style))
        story.append(Paragraph('• Arrive 15-30 minutes before the event starts', info_style))
        story.append(Paragraph('• Keep this ticket safe and do not share with others', info_style))
        story.append(Spacer(1, 20))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray,
            alignment=TA_CENTER
        )
        story.append(Paragraph(f'Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}', footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Create response
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="ticket-{ticket.ticket_number}.pdf"'
        
        return response
        
    except Exception as e:
        flash(f'Error generating ticket: {str(e)}', 'error')
        return redirect(url_for('tickets.my_tickets'))
