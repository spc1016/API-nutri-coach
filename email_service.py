import os
import random
import requests
from datetime import datetime, timezone
from utils import db

def generate_verification_code():
    """Generate a 6-digit random code"""
    return str(random.randint(100000, 999999))

def send_verification_email(email, code):
    """Send verification email via Google Apps Script Web App API"""
    gas_web_app_url = os.getenv('GMAIL_WEB_APP_URL')
    gas_secret_token = os.getenv('GMAIL_SECRET_TOKEN', 'nutricoach-secret-token')
    
    if not gas_web_app_url:
        raise Exception('Email configuration missing. Set GMAIL_WEB_APP_URL env var.')
    
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
    
    payload = {
        "to": email,
        "subject": "NutriCoach - Código de verificación",
        "htmlBody": html,
        "token": gas_secret_token
    }
    
    try:
        response = requests.post(gas_web_app_url, json=payload, timeout=15)
        response.raise_for_status()
        response_data = response.json()
        
        if "error" in response_data:
            raise Exception(response_data["error"])
            
    except Exception as e:
        raise Exception(f"Fallo al conectar con Google Apps Script: {e}")

def store_pending_verification(email, code, nombre, password_hash):
    """Store pending verification in MongoDB. Replaces existing entry for same email."""
    db.verificaciones_pendientes.delete_many({'email': email})
    db.verificaciones_pendientes.insert_one({
        'email': email,
        'code': code,
        'nombre': nombre,
        'password_hash': password_hash,
        'created_at': datetime.now(timezone.utc).replace(tzinfo=None)
    })

def verify_code(email, code):
    """Verify the code for a given email. Returns True if valid, False otherwise."""
    pending = db.verificaciones_pendientes.find_one({'email': email})
    if not pending:
        return False
    
    # Check expiration (10 minutes) - robust comparison avoiding naive/aware issues
    created_at = pending['created_at']
    if created_at.tzinfo is not None:
        created_at = created_at.replace(tzinfo=None)
        
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    elapsed = (now - created_at).total_seconds()
    
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
