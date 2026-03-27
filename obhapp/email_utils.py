"""Email utility module for Omega Beta Eta."""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Email configuration from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'omegabetaeta@umich.edu')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
SITE_URL = os.getenv('SITE_URL', 'https://omegabetaeta.org')


def _send_email(to, subject, body_html, bcc_self=True):
    """Send an email via SMTP. Returns True on success, False on failure."""
    if not EMAIL_PASSWORD:
        logger.warning("EMAIL_PASSWORD not set — skipping email to %s", to)
        return False

    msg = MIMEMultipart('alternative')
    msg['From'] = f"Omega Beta Eta <{EMAIL_ADDRESS}>"
    msg['To'] = to
    msg['Subject'] = subject
    msg['Reply-To'] = EMAIL_ADDRESS
    recipients = [to]
    if bcc_self:
        msg['Bcc'] = EMAIL_ADDRESS
        recipients.append(EMAIL_ADDRESS)
    msg.attach(MIMEText(body_html, 'html'))

    try:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, recipients, msg.as_string())
        logger.info("Email sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_default_password_email(to_email, fullname, username, password):
    """Send the default password to a brother."""
    subject = "ΩBH Portal — Your Account Credentials"
    body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 560px; margin: 0 auto; background: #1a1a2e; color: #e0e0e0; padding: 32px; border-radius: 12px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #c9a84c; font-size: 24px; margin: 0;">ΩBH Portal</h1>
        </div>
        <p>Hello {fullname},</p>
        <p>Your Omega Beta Eta portal account has been set up. Here are your login credentials:</p>
        <div style="background: #16213e; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #c9a84c;">
            <p style="margin: 4px 0;"><strong>Username:</strong> {username}</p>
            <p style="margin: 4px 0;"><strong>Temporary Password:</strong> {password}</p>
        </div>
        <p>You will be required to change your password on first login.</p>
        <p style="text-align: center; margin-top: 24px;">
            <a href="{SITE_URL}/login/" style="background: #c9a84c; color: #1a1a2e; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">Sign In to Portal</a>
        </p>
        <hr style="border: none; border-top: 1px solid #2a2a4a; margin: 24px 0;">
        <p style="font-size: 12px; color: #888;">This is an automated message from the ΩBH Portal. Do not reply to this email.</p>
    </div>
    """
    return _send_email(to_email, subject, body)


def send_contact_confirmation_email(to_email, name):
    """Send confirmation after a contact form submission."""
    subject = "ΩBH — We Received Your Message"
    body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 560px; margin: 0 auto; background: #1a1a2e; color: #e0e0e0; padding: 32px; border-radius: 12px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #c9a84c; font-size: 24px; margin: 0;">Omega Beta Eta</h1>
        </div>
        <p>Hello {name},</p>
        <p>Thank you for reaching out to Omega Beta Eta. We've received your message and will get back to you as soon as possible.</p>
        <hr style="border: none; border-top: 1px solid #2a2a4a; margin: 24px 0;">
        <p style="font-size: 12px; color: #888;">This is an automated confirmation. If you did not submit a message, you can safely ignore this email.</p>
    </div>
    """
    return _send_email(to_email, subject, body)


def send_application_confirmation_email(to_email, fullname):
    """Send confirmation after a recruitment application."""
    subject = "ΩBH — Application Received"
    body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 560px; margin: 0 auto; background: #1a1a2e; color: #e0e0e0; padding: 32px; border-radius: 12px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #c9a84c; font-size: 24px; margin: 0;">Omega Beta Eta</h1>
        </div>
        <p>Hello {fullname},</p>
        <p>Thank you for applying to join Omega Beta Eta! Your application has been received and is under review.</p>
        <p>We will be in contact with you soon regarding next steps.</p>
        <hr style="border: none; border-top: 1px solid #2a2a4a; margin: 24px 0;">
        <p style="font-size: 12px; color: #888;">This is an automated confirmation from the ΩBH recruitment system.</p>
    </div>
    """
    return _send_email(to_email, subject, body)


def send_message_reply_email(to_email, original_name, original_subject, original_message, reply_body, replier_name):
    """Send a reply to a contact message. Includes the original message for context."""
    subject = f"Re: {original_subject}"
    body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 560px; margin: 0 auto; background: #1a1a2e; color: #e0e0e0; padding: 32px; border-radius: 12px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #c9a84c; font-size: 24px; margin: 0;">Omega Beta Eta</h1>
        </div>
        <p>Hello {original_name},</p>
        <div style="white-space: pre-wrap;">{reply_body}</div>
        <hr style="border: none; border-top: 1px solid #2a2a4a; margin: 24px 0;">
        <div style="padding: 12px 16px; background: #16213e; border-left: 3px solid #c9a84c; border-radius: 6px; margin-bottom: 16px;">
            <p style="font-size: 12px; color: #888; margin: 0 0 8px 0;">Your original message:</p>
            <p style="font-size: 13px; color: #aaa; margin: 0 0 4px 0;"><strong>Subject:</strong> {original_subject}</p>
            <div style="white-space: pre-wrap; font-size: 13px; color: #aaa;">{original_message}</div>
        </div>
        <p style="font-size: 12px; color: #888;">Reply from {replier_name} via the ΩBH Portal.</p>
        <p style="font-size: 12px; color: #888;">You can respond directly to this email.</p>
    </div>
    """
    return _send_email(to_email, subject, body, bcc_self=False)
