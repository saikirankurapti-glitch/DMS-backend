"""
Email Service
Handles SMTP email sending using fastapi-mail
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

# Email configuration singleton
_email_config: Optional[ConnectionConfig] = None
_fastmail: Optional[FastMail] = None


def get_email_config() -> Optional[ConnectionConfig]:
    """Get or create email configuration"""
    global _email_config
    
    if not settings.EMAIL_ENABLED:
        logger.warning("Email notifications are disabled. Set EMAIL_ENABLED=true to enable.")
        return None
    
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP configuration incomplete. Email notifications will be disabled.")
        return None
    
    if _email_config is None:
        logger.info(f"Initializing email config: host={settings.SMTP_HOST}, port={settings.SMTP_PORT}, user={settings.SMTP_USER}, tls={settings.SMTP_USE_TLS}, ssl={settings.SMTP_USE_SSL}")
        _email_config = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USER,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=settings.SMTP_FROM_EMAIL or settings.SMTP_USER,
            MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=settings.SMTP_USE_TLS,
            MAIL_SSL_TLS=settings.SMTP_USE_SSL,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        logger.info("Email config initialized successfully")
    
    return _email_config


def get_fastmail() -> Optional[FastMail]:
    """Get or create FastMail instance"""
    global _fastmail
    
    config = get_email_config()
    if config is None:
        return None
    
    if _fastmail is None:
        _fastmail = FastMail(config)
    
    return _fastmail


async def send_email(
    to: List[str],
    subject: str,
    html_body: str,
    db: Optional[Session] = None,
    document_id: Optional[int] = None,
    version_id: Optional[int] = None,
    event_type: Optional[str] = None,
    recipient_user_id: Optional[int] = None
) -> bool:
    """
    Send email notification
    
    Args:
        to: List of recipient email addresses
        subject: Email subject
        html_body: HTML email body
        db: Database session for logging
        document_id: Document ID for logging
        version_id: Version ID for logging
        event_type: Event type for logging
        recipient_user_id: User ID for logging
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.EMAIL_ENABLED:
        logger.info(f"Email disabled. Would send to {to}: {subject}")
        return False
    
    logger.info(f"Attempting to send email to {to}: {subject}")
    fastmail = get_fastmail()
    if fastmail is None:
        logger.error("FastMail not configured. Email not sent. Check SMTP settings.")
        return False
    
    try:
        message = MessageSchema(
            subject=subject,
            recipients=to,
            body=html_body,
            subtype=MessageType.html,
        )
        
        await fastmail.send_message(message)
        
        # Log successful send
        if db and document_id:
            from app.models.notification_log import NotificationLog, NotificationStatus
            for email in to:
                log_entry = NotificationLog(
                    document_id=document_id,
                    version_id=version_id,
                    event_type=event_type,
                    recipient_email=email,
                    recipient_user_id=recipient_user_id,
                    subject=subject,
                    body_html=html_body,
                    status=NotificationStatus.SENT,
                    sent_at=datetime.utcnow()
                )
                db.add(log_entry)
            db.commit()
        
        logger.info(f"Email sent successfully to {to}: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}", exc_info=True)
        
        # Log failed send
        if db and document_id:
            from app.models.notification_log import NotificationLog, NotificationStatus
            for email in to:
                log_entry = NotificationLog(
                    document_id=document_id,
                    version_id=version_id,
                    event_type=event_type,
                    recipient_email=email,
                    recipient_user_id=recipient_user_id,
                    subject=subject,
                    body_html=html_body,
                    status=NotificationStatus.FAILED,
                    error_message=str(e),
                    sent_at=None
                )
                db.add(log_entry)
            db.commit()
        
        return False

