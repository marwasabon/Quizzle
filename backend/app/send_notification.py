import requests
from flask_mail import Mail, Message
from flask import Flask 
from flask import current_app as app
from flask_mail import Message
from app import mail
from .config import Config  # Import the Config class


  
 
 # this is to unify the sending mails 
def send_email(subject, recipients, text_body, html_body=None):
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipients])
    msg.body = text_body
    if html_body:
        msg.html = html_body
        mail.send(msg)