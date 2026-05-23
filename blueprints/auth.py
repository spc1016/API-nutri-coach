import re
import threading
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from jsonschema import validate
from werkzeug.security import check_password_hash, generate_password_hash
from utils import db
from email_service import (
    generate_verification_code, send_verification_email,
    store_pending_verification, verify_code, get_pending_data, delete_pending
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        login_data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string" }
            },
            "required": ["email", "password"],
            "additionalProperties": False
        }
        validate(instance=login_data, schema=schema)
        
        # Buscar primero en nutricionistas solo por email
        user = db.nutricionistas.find_one({'email': login_data['email']})
        if user and check_password_hash(user['password_hash'], login_data['password']):
            role = 'nutricionista'
        else:
            # Si no es nutricionista, buscar en clientes solo por email
            user = db.clientes.find_one({'email': login_data['email']})
            if user and check_password_hash(user['password_hash'], login_data['password']):
                role = 'cliente'
            else:
                return jsonify({'error': 'Email o contraseña incorrectos'}), 401
        
        data:dict = {'role': role}
        token = create_access_token(identity=str(user['_id']), additional_claims=data)
        return jsonify({'token': token, 'role': role}), 200
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({'error': 'Datos de login inválidos'}), 400


# ──────────────────────────────────────────────
# Endpoints de registro con verificación por email
# ──────────────────────────────────────────────

GMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@gmail\.com$')

@auth_bp.route('/register/send-code', methods=['POST'])
def register_send_code():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string", "minLength": 6 }
            },
            "required": ["nombre", "email", "password"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        email = data['email'].strip().lower()
        
        # Validar que sea un email de Gmail
        if not GMAIL_REGEX.match(email):
            return jsonify({'error': 'Se requiere un email de gmail válido (@gmail.com)'}), 400
        
        # Verificar que el email no esté registrado
        if db.clientes.find_one({'email': email}) or db.nutricionistas.find_one({'email': email}):
            return jsonify({'error': 'Este email ya está registrado'}), 400
        
        # Generar código y hashear contraseña
        code = generate_verification_code()
        password_hash = generate_password_hash(data['password'])
        
        # Guardar datos pendientes de verificación
        store_pending_verification(email, code, data['nombre'].strip(), password_hash)
        
        # Enviar correo con el código en segundo plano
        def run_async_send():
            try:
                send_verification_email(email, code)
                print(f"✅ [SMTP] Código enviado con éxito a {email}")
            except Exception as e:
                print(f"❌ [SMTP_ERROR] Fallo al enviar código a {email}: {e}")

        threading.Thread(target=run_async_send).start()
        
        return jsonify({'message': 'Código de verificación enviado a ' + email}), 200
    except Exception as e:
        print(f"Error en register/send-code: {e}")
        return jsonify({'error': 'Error al enviar el código de verificación'}), 500


@auth_bp.route('/register/verify-code', methods=['POST'])
def register_verify_code():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "email": { "type": "string", "minLength": 3 },
                "code": { "type": "string", "minLength": 6, "maxLength": 6 }
            },
            "required": ["email", "code"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        email = data['email'].strip().lower()
        
        # Verificar el código
        if not verify_code(email, data['code']):
            # Comprobar si expiró o si es incorrecto
            pending = get_pending_data(email)
            if not pending:
                return jsonify({'error': 'No hay verificación pendiente o el código ha expirado. Solicita uno nuevo.'}), 400
            return jsonify({'error': 'Código de verificación incorrecto'}), 400
        
        # Obtener datos pendientes
        pending = get_pending_data(email)
        if not pending:
            return jsonify({'error': 'Datos de verificación no encontrados'}), 400
        
        # Crear el cliente en la colección clientes (solo campos obligatorios)
        new_client = {
            'nombre': pending['nombre'],
            'email': email,
            'password_hash': pending['password_hash']
        }
        result = db.clientes.insert_one(new_client)
        
        # Limpiar datos pendientes
        delete_pending(email)
        
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error en register/verify-code: {e}")
        return jsonify({'error': 'Error al verificar el código'}), 500


@auth_bp.route('/register/resend-code', methods=['POST'])
def register_resend_code():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "email": { "type": "string", "minLength": 3 }
            },
            "required": ["email"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        email = data['email'].strip().lower()
        
        # Verificar que existe una verificación pendiente
        pending = get_pending_data(email)
        if not pending:
            return jsonify({'error': 'No hay verificación pendiente para este email'}), 400
        
        # Generar nuevo código
        code = generate_verification_code()
        
        # Actualizar el código pendiente (mantener nombre y password_hash)
        store_pending_verification(email, code, pending['nombre'], pending['password_hash'])
        
        # Enviar nuevo correo en segundo plano
        def run_async_resend():
            try:
                send_verification_email(email, code)
                print(f"✅ [SMTP] Código reenviado con éxito a {email}")
            except Exception as e:
                print(f"❌ [SMTP_ERROR] Fallo al reenviar código a {email}: {e}")

        threading.Thread(target=run_async_resend).start()
        
        return jsonify({'message': 'Nuevo código de verificación enviado a ' + email}), 200
    except Exception as e:
        print(f"Error en register/resend-code: {e}")
        return jsonify({'error': 'Error al reenviar el código'}), 500
