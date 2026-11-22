from flask import current_app
from flask_mail import Message

from . import mail


def send_email(subject, recipients, text_body, html_body=None):
    """Send an email through the app's configured Flask-Mail instance."""
    if isinstance(recipients, str):
        recipients = [recipients]
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    mail.send(msg)
