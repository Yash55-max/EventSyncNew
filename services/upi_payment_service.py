"""
UPI Payment Service for Indian Payment Methods
Handles UPI payments, QR code generation, and payment verification
"""

import qrcode
import io
import base64
from urllib.parse import quote
import re
from datetime import datetime
from decimal import Decimal


class UPIPaymentService:
    """Service for handling UPI payments in India"""
    
    @staticmethod
    def validate_upi_id(upi_id):
        """Validate UPI ID format"""
        if not upi_id:
            return False
        
        # UPI ID format: name@bank (e.g., john@paytm, user@ybl)
        upi_pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+$'
        return bool(re.match(upi_pattern, upi_id))
    
    @staticmethod
    def validate_mobile_number(mobile):
        """Validate Indian mobile number"""
        if not mobile:
            return False
        
        # Indian mobile number: 10 digits starting with 6-9
        mobile_pattern = r'^[6-9]\d{9}$'
        return bool(re.match(mobile_pattern, mobile))
    
    @staticmethod
    def generate_upi_payment_url(upi_id=None, mobile=None, amount=None, note="Event Payment", 
                                 merchant_name="EventSync", transaction_ref=None):
        """
        Generate UPI payment URL for QR code
        Format: upi://pay?pa=UPI_ID&pn=MERCHANT_NAME&am=AMOUNT&cu=INR&tn=NOTE&tr=REF
        """
        if not upi_id and not mobile:
            raise ValueError("Either UPI ID or mobile number is required")
        
        # Use UPI ID if provided, otherwise create one with mobile@upi
        payee_address = upi_id if upi_id else f"{mobile}@upi"
        
        # Build UPI URL
        upi_url = "upi://pay?"
        params = []
        
        # Payee address (required)
        params.append(f"pa={quote(payee_address)}")
        
        # Payee name (required)
        params.append(f"pn={quote(merchant_name)}")
        
        # Amount (optional, in INR)
        if amount and amount > 0:
            params.append(f"am={amount}")
            params.append("cu=INR")
        
        # Transaction note (optional)
        if note:
            params.append(f"tn={quote(note)}")
        
        # Transaction reference (optional)
        if transaction_ref:
            params.append(f"tr={quote(transaction_ref)}")
        
        upi_url += "&".join(params)
        return upi_url
    
    @staticmethod
    def generate_qr_code(upi_url, size=(300, 300)):
        """Generate QR code for UPI payment URL"""
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            qr.add_data(upi_url)
            qr.make(fit=True)
            
            # Create image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Resize if needed
            if size != (300, 300):
                qr_img = qr_img.resize(size)
            
            # Convert to base64 string
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_data = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{qr_data}"
            
        except Exception as e:
            raise ValueError(f"Failed to generate QR code: {str(e)}")
    
    @staticmethod
    def create_payment_data(event, amount=None):
        """Create comprehensive payment data for an event"""
        if not event.accept_upi_payments:
            return None
        
        # Use event price if amount not provided
        payment_amount = amount if amount is not None else event.price
        
        # Generate transaction reference
        transaction_ref = f"EVENT_{event.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Create payment note
        note = f"Payment for {event.title}"
        
        # Generate UPI URL
        try:
            upi_url = UPIPaymentService.generate_upi_payment_url(
                upi_id=event.upi_id,
                mobile=event.payment_mobile,
                amount=payment_amount,
                note=note,
                merchant_name=event.organizer.full_name or event.organizer.username,
                transaction_ref=transaction_ref
            )
            
            # Generate QR code
            qr_code_data = UPIPaymentService.generate_qr_code(upi_url)
            
            return {
                'upi_url': upi_url,
                'qr_code': qr_code_data,
                'amount': payment_amount,
                'currency': 'INR',
                'note': note,
                'transaction_ref': transaction_ref,
                'payee_name': event.organizer.full_name or event.organizer.username,
                'upi_id': event.upi_id,
                'mobile': event.payment_mobile,
                'instructions': event.payment_instructions,
                'event_title': event.title
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_popular_upi_apps():
        """Return list of popular UPI apps in India"""
        return [
            {
                'name': 'Google Pay',
                'package': 'com.google.android.apps.nbu.paisa.user',
                'icon': '📱',
                'deep_link_prefix': 'tez://upi/pay'
            },
            {
                'name': 'PhonePe',
                'package': 'com.phonepe.app',
                'icon': '💜',
                'deep_link_prefix': 'phonepe://pay'
            },
            {
                'name': 'Paytm',
                'package': 'net.one97.paytm',
                'icon': '💙',
                'deep_link_prefix': 'paytmmp://pay'
            },
            {
                'name': 'BHIM UPI',
                'package': 'in.org.npci.upiapp',
                'icon': '🏛️',
                'deep_link_prefix': 'bhim://pay'
            },
            {
                'name': 'Amazon Pay',
                'package': 'in.amazon.mShop.android.shopping',
                'icon': '🛒',
                'deep_link_prefix': 'amzn://pay'
            }
        ]
    
    @staticmethod
    def format_amount_display(amount):
        """Format amount for display in Indian format"""
        if not amount or amount == 0:
            return "Free"
        
        # Convert to decimal for precise formatting
        decimal_amount = Decimal(str(amount))
        
        # Format with 2 decimal places
        formatted = f"₹{decimal_amount:.2f}"
        
        # Add Indian number formatting for large amounts
        if decimal_amount >= 1000:
            # Convert to lakhs/crores format for very large amounts
            if decimal_amount >= 10000000:  # 1 crore
                crores = decimal_amount / 10000000
                formatted = f"₹{crores:.2f} Cr"
            elif decimal_amount >= 100000:  # 1 lakh
                lakhs = decimal_amount / 100000
                formatted = f"₹{lakhs:.2f} L"
            else:
                # Add thousand separators
                formatted = f"₹{decimal_amount:,.2f}"
        
        return formatted
    
    @staticmethod
    def create_payment_instructions(event):
        """Generate payment instructions for attendees"""
        instructions = []
        
        instructions.append("💳 UPI Payment Options:")
        
        if event.upi_id:
            instructions.append(f"📱 UPI ID: {event.upi_id}")
        
        if event.payment_mobile:
            instructions.append(f"📞 Mobile: +91 {event.payment_mobile}")
        
        if event.price and event.price > 0:
            formatted_amount = UPIPaymentService.format_amount_display(event.price)
            instructions.append(f"💰 Amount: {formatted_amount}")
        
        instructions.append("")
        instructions.append("📋 How to Pay:")
        instructions.append("1. Scan the QR code with any UPI app")
        instructions.append("2. Or tap on your preferred UPI app below")
        instructions.append("3. Verify the amount and complete payment")
        instructions.append("4. Take a screenshot of the transaction")
        
        if event.payment_instructions:
            instructions.append("")
            instructions.append("📝 Additional Instructions:")
            instructions.extend(event.payment_instructions.split('\n'))
        
        return '\n'.join(instructions)


# UPI Payment verification utilities
class UPIPaymentVerification:
    """Utilities for UPI payment verification"""
    
    @staticmethod
    def extract_transaction_id(payment_screenshot_text):
        """Extract transaction ID from payment screenshot OCR text"""
        # Common patterns for UPI transaction IDs
        patterns = [
            r'Transaction ID[:\s]+([A-Z0-9]{12,})',
            r'UPI Ref[:\s]+([A-Z0-9]{12,})',
            r'UTR[:\s]+([A-Z0-9]{12,})',
            r'TXN ID[:\s]+([A-Z0-9]{12,})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, payment_screenshot_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    @staticmethod
    def validate_payment_amount(screenshot_text, expected_amount):
        """Validate payment amount from screenshot OCR"""
        # Look for amount patterns
        amount_patterns = [
            r'₹\s*([0-9,]+\.?[0-9]*)',
            r'Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'INR\s*([0-9,]+\.?[0-9]*)',
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, screenshot_text)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if abs(amount - expected_amount) < 0.01:  # Allow for small rounding differences
                        return True
                except ValueError:
                    continue
        
        return False