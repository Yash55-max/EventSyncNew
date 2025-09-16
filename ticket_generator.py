#!/usr/bin/env python3
"""
PDF Ticket Generation System
Generates professional PDF tickets with QR codes for event check-ins
"""

import io
import qrcode
import uuid
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from PIL import Image as PILImage

class TicketGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.create_custom_styles()
        
    def create_custom_styles(self):
        """Create custom styles for the ticket"""
        self.styles.add(ParagraphStyle(
            name='TicketTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='EventTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='TicketInfo',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='TicketFooter',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))

    def generate_qr_code(self, data):
        """Generate QR code for ticket verification"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer

    def create_ticket_pdf(self, booking_data, event_data, user_data):
        """Generate a PDF ticket for a booking"""
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        
        # Generate unique ticket ID
        ticket_id = str(uuid.uuid4())[:8].upper()
        
        # QR Code data (JSON string with booking info)
        qr_data = {
            'ticket_id': ticket_id,
            'booking_id': booking_data.get('id'),
            'event_id': event_data.get('id'),
            'user_id': user_data.get('id'),
            'timestamp': datetime.now().isoformat()
        }
        
        qr_code_buffer = self.generate_qr_code(str(qr_data))
        
        # Story elements for PDF
        story = []
        
        # Header
        story.append(Paragraph("🎟️ EVENT TICKET", self.styles['TicketTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Event Information
        story.append(Paragraph(f"<b>{event_data.get('title', 'Event Title')}</b>", self.styles['EventTitle']))
        story.append(Spacer(1, 0.1*inch))
        
        # Create ticket details table
        ticket_data = [
            ['📅 Date:', event_data.get('date', 'TBD')],
            ['🕐 Time:', event_data.get('time', 'TBD')],
            ['📍 Location:', event_data.get('location', 'TBD')],
            ['👤 Attendee:', user_data.get('full_name', user_data.get('username', 'N/A'))],
            ['✉️ Email:', user_data.get('email', 'N/A')],
            ['🎫 Ticket ID:', ticket_id],
            ['🎭 Tickets:', str(booking_data.get('ticket_quantity', 1))],
            ['💰 Total:', f"${booking_data.get('total_price', '0.00')}"]
        ]
        
        ticket_table = Table(ticket_data, colWidths=[2*inch, 4*inch])
        ticket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(ticket_table)
        story.append(Spacer(1, 0.3*inch))
        
        # QR Code Section
        story.append(Paragraph("<b>Scan for Check-in</b>", self.styles['EventTitle']))
        story.append(Spacer(1, 0.1*inch))
        
        # Add QR code image
        qr_image = Image(qr_code_buffer, width=2*inch, height=2*inch)
        qr_image.hAlign = 'CENTER'
        story.append(qr_image)
        
        story.append(Spacer(1, 0.2*inch))
        
        # Event Description
        if event_data.get('description'):
            story.append(Paragraph("<b>Event Description:</b>", self.styles['TicketInfo']))
            story.append(Paragraph(event_data.get('description'), self.styles['TicketInfo']))
            story.append(Spacer(1, 0.1*inch))
        
        # Terms and Conditions
        terms = """
        <b>Terms & Conditions:</b><br/>
        • This ticket is valid for one entry to the specified event<br/>
        • Please arrive 15 minutes before the event starts<br/>
        • This ticket is non-transferable and non-refundable<br/>
        • Present this ticket (digital or printed) at the venue<br/>
        • Lost tickets cannot be replaced<br/>
        """
        story.append(Paragraph(terms, self.styles['TicketInfo']))
        story.append(Spacer(1, 0.2*inch))
        
        # Footer
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | EVENTSYNC Event Management System",
            self.styles['TicketFooter']
        ))
        
        # Build PDF
        doc.build(story)
        
        buffer.seek(0)
        return buffer, ticket_id

    def verify_qr_code(self, qr_data_string):
        """Verify QR code data for check-in"""
        try:
            # In a real system, you'd parse the QR data and verify against database
            # For now, we'll return basic validation
            return {
                'valid': True,
                'message': 'Ticket verified successfully',
                'data': qr_data_string
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Invalid ticket: {str(e)}',
                'data': None
            }

# Utility functions for integration with Flask app
def generate_ticket_for_booking(booking_id):
    """Generate ticket PDF for a specific booking ID"""
    from models import Booking, Event, User
    from flask import current_app
    
    try:
        # Fetch booking data
        booking = Booking.query.get(booking_id)
        if not booking:
            return None, "Booking not found"
        
        event = Event.query.get(booking.event_id)
        user = User.query.get(booking.user_id)
        
        if not event or not user:
            return None, "Event or user not found"
        
        # Prepare data for ticket generation
        booking_data = {
            'id': booking.id,
            'ticket_quantity': booking.ticket_quantity,
            'total_price': str(booking.total_price),
            'booking_date': booking.booking_timestamp.strftime('%Y-%m-%d')
        }
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date.strftime('%Y-%m-%d'),
            'time': event.time.strftime('%H:%M') if event.time else 'TBD',
            'location': event.location
        }
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        }
        
        # Generate PDF
        generator = TicketGenerator()
        pdf_buffer, ticket_id = generator.create_ticket_pdf(booking_data, event_data, user_data)
        
        return pdf_buffer, ticket_id
        
    except Exception as e:
        current_app.logger.error(f"Error generating ticket: {str(e)}")
        return None, str(e)

# Test function
def test_ticket_generation():
    """Test ticket generation with sample data"""
    sample_booking = {
        'id': 123,
        'ticket_quantity': 2,
        'total_price': '50.00',
        'booking_date': '2025-09-13'
    }
    
    sample_event = {
        'id': 456,
        'title': 'Tech Conference 2025',
        'description': 'Annual technology conference featuring the latest innovations',
        'date': '2025-10-15',
        'time': '09:00',
        'location': 'Convention Center, Tech City'
    }
    
    sample_user = {
        'id': 789,
        'username': 'john_doe',
        'email': 'john@example.com',
        'full_name': 'John Doe'
    }
    
    generator = TicketGenerator()
    pdf_buffer, ticket_id = generator.create_ticket_pdf(sample_booking, sample_event, sample_user)
    
    # Save test PDF
    with open('test_ticket.pdf', 'wb') as f:
        f.write(pdf_buffer.read())
    
    print(f"✅ Test ticket generated: test_ticket.pdf (Ticket ID: {ticket_id})")
    return True

if __name__ == "__main__":
    test_ticket_generation()