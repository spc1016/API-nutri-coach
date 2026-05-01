from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from jsonschema import validate
from werkzeug.security import check_password_hash
from utils import db

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
