"""
Email service for sending emails via SMTP
"""
import logging
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config.settings import settings
from app.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)


class EmailService(metaclass=SingletonMeta):
    """Service for sending emails"""
    
    def __init__(self):
        logger.info("EmailService initialized")
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.smtp_from_email = settings.smtp_from_email or settings.smtp_username
        self.smtp_from_name = settings.smtp_from_name
        self.smtp_use_tls = settings.smtp_use_tls
    
    async def send_email(
        self, 
        to_email: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Check if SMTP is configured
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP not configured. Email not sent.")
                logger.info(f"Would have sent email to {to_email}:")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body: {body}")
                return False
            
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add plain text part
            text_part = MIMEText(body, "plain")
            message.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, "html")
                message.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                use_tls=self.smtp_use_tls,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_password_reset_email(
        self, 
        to_email: str, 
        username: str, 
        reset_token: str
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            username: User's username
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully
        """
        # Create reset link
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
        
        # Plain text body
        body = f"""Hello {username},

You have requested to reset your password for your DAAV account.

Click the link below to reset your password:
{reset_link}

This link will expire in {settings.password_reset_token_expire_hours} hour(s).

If you did not request this password reset, please ignore this email.

Best regards,
The DAAV Team
"""
        
        # HTML body
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #3880ff;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 5px 5px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 30px;
            background-color: #3880ff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{username}</strong>,</p>
            
            <p>You have requested to reset your password for your DAAV account.</p>
            
            <p>Click the button below to reset your password:</p>
            
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all; background-color: #e9ecef; padding: 10px; border-radius: 3px;">
                {reset_link}
            </p>
            
            <div class="warning">
                <strong>⚠️ Important:</strong> This link will expire in {settings.password_reset_token_expire_hours} hour(s).
            </div>
            
            <p>If you did not request this password reset, please ignore this email and your password will remain unchanged.</p>
            
            <p>Best regards,<br>
            The DAAV Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        subject = "Reset Your Password - DAAV Application"
        
        return await self.send_email(to_email, subject, body, html_body)
