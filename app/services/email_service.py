"""
Email service for sending verification codes, password reset, etc.
"""
from app.core.logging import get_logger

logger = get_logger("services.email_service")


async def send_verification_code(email: str, code: str) -> bool:
    """
    Send verification code to user's email.
    
    Args:
        email: Recipient email address
        code: 6-digit verification code
    
    Returns:
        bool: True if sent successfully
    
    TODO: Implement with actual email provider (SMTP, SendGrid, etc.)
    """
    # Temporary: just log the code
    print(f"🔐 Verification code for {email}: {code}")
    
    # In production, you would use:
    # - SMTP (smtplib)
    # - SendGrid API
    # - Amazon SES
    # - Iranian services like Mailgun, etc.
    
    return True


async def send_password_reset_code(email: str, code: str) -> bool:
    """
    Send password reset code to user's email.
    
    Args:
        email: Recipient email address
        code: 6-digit reset code
    
    Returns:
        bool: True if sent successfully
    
    TODO: Implement with actual email provider
    """
    print(f"🔑 Password reset code for {email}: {code}")
    return True


async def send_welcome_email(email: str, name: str) -> bool:
    """
    Send welcome email to new user.
    
    Args:
        email: Recipient email address
        name: User's name
    
    Returns:
        bool: True if sent successfully
    """
    print(f"👋 Welcome email sent to {email} ({name})")
    return True