import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from utils import db

def generate_verification_code():
    """Generate a 6-digit random code"""
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    """Send verification email via Gmail SMTP"""
    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_address or not gmail_app_password:
        raise Exception('Email configuration missing. Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD env vars.')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'NutriCoach - Código de verificación'
    msg['From'] = gmail_address
    msg['To'] = email
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <h1 style="text-align: center; color: #2D2D2D; margin-bottom: 10px;">NutriCoach</h1>
            <p style="text-align: center; color: #666; font-size: 16px;">Tu código de verificación es:</p>
            <div style="text-align: center; margin: 30px 0;">
                <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #4CAF50; background: #f0f9f0; padding: 15px 30px; border-radius: 8px; display: inline-block;">{code}</span>
            </div>
            <p style="text-align: center; color: #999; font-size: 14px;">Este código expira en 10 minutos.<br/>Si no solicitaste este código, ignora este correo.</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(gmail_address, gmail_app_password)
        server.send_message(msg)

def store_pending_verification(email, code, nombre, password_hash):
    """Store pending verification in MongoDB. Replaces existing entry for same email."""
    db.verificaciones_pendientes.delete_many({'email': email})
    db.verificaciones_pendientes.insert_one({
        'email': email,
        'code': code,
        'nombre': nombre,
        'password_hash': password_hash,
        'created_at': datetime.now(timezone.utc)
    })

def verify_code(email, code):
    """Verify the code for a given email. Returns True if valid, False otherwise."""
    pending = db.verificaciones_pendientes.find_one({'email': email})
    if not pending:
        return False
    # Check expiration (10 minutes)
    elapsed = (datetime.now(timezone.utc) - pending['created_at']).total_seconds()
    if elapsed > 600:
        db.verificaciones_pendientes.delete_one({'email': email})
        return False
    return pending['code'] == code

def get_pending_data(email):
    """Get the pending verification data for creating the user."""
    return db.verificaciones_pendientes.find_one({'email': email})

def delete_pending(email):
    """Delete pending verification data after successful registration."""
    db.verificaciones_pendientes.delete_many({'email': email})
