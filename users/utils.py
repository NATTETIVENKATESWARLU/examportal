# utils.py
import random
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generates a random OTP of specified length."""
    return "".join([str(random.randint(0, 9)) for _ in range(length)])

def send_otp_email(email, otp_code, user_name="User"):
    """Sends an OTP email to the user."""
    subject = f'Your One-Time Password (OTP) for {getattr(settings, "APP_NAME", "Our Service")}'
    
    message = f"""
Hi {user_name},

Your One-Time Password (OTP) to proceed with your request is: {otp_code}

This OTP is valid for {getattr(settings, 'OTP_EXPIRY_MINUTES', 5)} minutes.

If you did not request this OTP, please ignore this email or contact support if you suspect suspicious activity.

Thank you,
The {getattr(settings, "APP_NAME", "Application")} Team
"""
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    try:
        send_mail(subject, message, email_from, recipient_list, fail_silently=False)
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {e}")
        return False