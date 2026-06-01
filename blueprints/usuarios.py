from flask import Blueprint, jsonify, request
from bson import ObjectId
from jsonschema import validate
from werkzeug.security import generate_password_hash
from utils import db, check_auth, check_auth_owner_or_nutricionista, check_auth_any, get_pagination
from flask_jwt_extended import get_jwt_identity

usuarios_bp = Blueprint('usuarios', __name__)

# Crear nutricionista (requiere autenticación de nutricionista)
@usuarios_bp.route('/nutricionistas', methods=['POST'])
@check_auth('nutricionista')
def crear_nutricionista():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string" },
                "telefono": { "type": "string" }
            },
            "required": ["nombre", "email", "password"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Verificar que el email no esté registrado previamente
        if db.nutricionistas.find_one({'email': data['email']}) or db.clientes.find_one({'email': data['email']}):
            return jsonify({'error': 'El email ya está registrado'}), 400

        # Hash de la contraseña antes de guardar
        data['password_hash'] = generate_password_hash(data.pop('password'))
        result = db.nutricionistas.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error creando nutricionista: {e}")
        return jsonify({'error': 'Datos inválidos para crear nutricionista'}), 400

# Crear cliente (no requiere autenticación)
@usuarios_bp.route('/clientes', methods=['POST'])
def crear_cliente():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string" },
                "telefono": { "type": "string" },
                "edad": { "type": "integer" },
                "peso": { "type": "number" },
                "altura": { "type": "number" },
                "nutricionista_id": {"type": "string"},
                "genero": {"type": "string"},
                "objetivo": {"type": "string"},
                "foto_perfil": { "type": ["string", "null"] }
            },
            "required": ["nombre", "email", "password"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Verificar que el email no esté registrado previamente
        if db.nutricionistas.find_one({'email': data['email']}) or db.clientes.find_one({'email': data['email']}):
            return jsonify({'error': 'El email ya está registrado'}), 400

        # Hash de la contraseña antes de guardar
        data['password_hash'] = generate_password_hash(data.pop('password'))
        if 'nutricionista_id' in data:
            data["nutricionista_id"] = ObjectId(data["nutricionista_id"])
        result = db.clientes.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error creando cliente: {e}")
        return jsonify({'error': 'Datos inválidos para crear cliente'}), 400

# Eliminar nutricionista (requiere autenticación de nutricionista)
@usuarios_bp.route('/nutricionistas/<id>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_nutricionista(id):
    try:
        result = db.nutricionistas.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Nutricionista no encontrado'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Eliminar cliente (requiere autenticación de nutricionista)
@usuarios_bp.route('/clientes/<id>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_cliente(id):
    try:
        result = db.clientes.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Modificar nutricionista (requiere autenticación de nutricionista)
@usuarios_bp.route('/nutricionistas/<id>', methods=['PUT'])
@check_auth('nutricionista')
def modificar_nutricionista(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string" },
                "telefono": { "type": "string" }, 
            },
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Verificar que el nuevo email no esté registrado
        if 'email' in data:
            if db.nutricionistas.find_one({'email': data['email'], '_id': {'$ne': ObjectId(id)}}) or \
               db.clientes.find_one({'email': data['email']}):
                return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Si se envía password, hay que hashearlo
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data.pop('password'))
        
        result = db.nutricionistas.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Nutricionista no encontrado'}), 404
        return jsonify({'mensaje': 'Nutricionista actualizado'}), 200
    except Exception as e:
        print(f"Error modificando nutricionista: {e}")
        return jsonify({'error': 'Datos inválidos'}), 400

# Modificar cliente (requiere ser el propio cliente o nutricionista)
@usuarios_bp.route('/clientes/<id>', methods=['PUT'])
@check_auth_owner_or_nutricionista()
def modificar_cliente(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "email": { "type": "string", "minLength": 3 },
                "password": { "type": "string" },
                "telefono": { "type": "string" },
                "edad": { "type": "integer" },
                "peso": { "type": "number" },
                "altura": { "type": "number" },
                "objetivo": {"type": "string"},
                "nutricionista_id": {"type": "string"},
                "foto_perfil": { "type": ["string", "null"] }
            },
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Verificar que el nuevo email no esté registrado
        if 'email' in data:
            if db.clientes.find_one({'email': data['email'], '_id': {'$ne': ObjectId(id)}}) or \
               db.nutricionistas.find_one({'email': data['email']}):
                return jsonify({'error': 'El email ya está registrado'}), 400
        
        # Si se envía password, hay que hashearlo
        if 'password' in data:
            data['password_hash'] = generate_password_hash(data.pop('password'))
        if 'nutricionista_id' in data:
            data['nutricionista_id'] = ObjectId(data['nutricionista_id'])
            
        result = db.clientes.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        return jsonify({'mensaje': 'Cliente actualizado'}), 200
    except Exception as e:
        print(f"Error modificando cliente: {e}")
        return jsonify({'error': 'Datos inválidos'}), 400

@usuarios_bp.route('/clientes/<id>', methods=['GET'])
def obtener_cliente(id):
    try:
        cliente = db.clientes.find_one({'_id': ObjectId(id)}, {'password_hash': 0})
        if not cliente:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        cliente['_id'] = str(cliente['_id'])
        if 'nutricionista_id' in cliente and cliente['nutricionista_id']:
            cliente['nutricionista_id'] = str(cliente['nutricionista_id'])
            
        # Contar seguidores y seguidos
        seguidores_count = db.seguimientos.count_documents({'seguido_id': ObjectId(id)})
        seguidos_count = db.seguimientos.count_documents({'seguidor_id': ObjectId(id)})
        cliente['seguidores_count'] = seguidores_count
        cliente['seguidos_count'] = seguidos_count
            
        return jsonify(cliente), 200
    except Exception as e:
        print(f"Error cargando cliente: {e}")
        return jsonify({'error': 'ID inválido'}), 400

# Obtener todos los nutricionistas
@usuarios_bp.route('/nutricionistas', methods=['GET'])
def obtener_nutricionistas():
    try:
        skip, limit = get_pagination(request)
        nutricionistas = list(db.nutricionistas.find({}, {'password_hash': 0}).skip(skip).limit(limit))
        for n in nutricionistas:
            n['_id'] = str(n['_id'])
        return jsonify(nutricionistas), 200
    except Exception:
        return jsonify({'error': 'Error al obtener nutricionistas'}), 400
    
# Obtener todos los clientes
@usuarios_bp.route('/clientes', methods=['GET'])
def obtener_clientes():
    try:
        skip, limit = get_pagination(request)
        clientes = list(db.clientes.find({}, {'password_hash': 0}).skip(skip).limit(limit))
        for c in clientes:
            c['_id'] = str(c['_id'])
            if 'nutricionista_id' in c:
                c['nutricionista_id'] = str(c['nutricionista_id'])
            # Contar seguidores y seguidos
            oid = ObjectId(c['_id'])
            c['seguidores_count'] = db.seguimientos.count_documents({'seguido_id': oid})
            c['seguidos_count'] = db.seguimientos.count_documents({'seguidor_id': oid})
        return jsonify(clientes), 200
    except Exception as e:
        print(f"Error en obtener_clientes: {e}")
        return jsonify({'error': 'Error al obtener clientes'}), 400

# Obtener clientes por nutricionista (requiere autenticación)
@usuarios_bp.route('/nutricionistas/<id>/clientes', methods=['GET'])
@check_auth('nutricionista')
def obtener_clientes_por_nutricionista(id):
    try:
        skip, limit = get_pagination(request)
        clientes = list(db.clientes.find({'nutricionista_id': ObjectId(id)}, {'password_hash': 0}).skip(skip).limit(limit))
        for c in clientes:
            c['_id'] = str(c['_id'])
            if 'nutricionista_id' in c:
                c['nutricionista_id'] = str(c['nutricionista_id'])
        return jsonify(clientes), 200
    except Exception as e:
        print(f"Error en obtener_clientes_por_nutricionista: {e}")
        return jsonify({'error': 'Error al obtener clientes del nutricionista'}), 400

# Seguir a un usuario
@usuarios_bp.route('/clientes/<id>/seguir', methods=['POST'])
@check_auth_any()
def seguir_usuario(id):
    try:
        seguidor_id = get_jwt_identity()
        if seguidor_id == id:
            return jsonify({'error': 'No puedes seguirte a ti mismo'}), 400
            
        # Verificar que ambos existan
        seguido = db.clientes.find_one({'_id': ObjectId(id)})
        if not seguido:
            return jsonify({'error': 'Usuario a seguir no encontrado'}), 404
            
        # Verificar si ya lo sigue
        existente = db.seguimientos.find_one({
            'seguidor_id': ObjectId(seguidor_id),
            'seguido_id': ObjectId(id)
        })
        if existente:
            return jsonify({'error': 'Ya sigues a este usuario'}), 400
            
        db.seguimientos.insert_one({
            'seguidor_id': ObjectId(seguidor_id),
            'seguido_id': ObjectId(id)
        })
        return jsonify({'mensaje': 'Usuario seguido exitosamente'}), 200
    except Exception as e:
        print(f"Error al seguir usuario: {e}")
        return jsonify({'error': 'Error interno'}), 500

# Dejar de seguir a un usuario
@usuarios_bp.route('/clientes/<id>/seguir', methods=['DELETE'])
@check_auth_any()
def dejar_de_seguir_usuario(id):
    try:
        seguidor_id = get_jwt_identity()
        result = db.seguimientos.delete_one({
            'seguidor_id': ObjectId(seguidor_id),
            'seguido_id': ObjectId(id)
        })
        if result.deleted_count == 0:
            return jsonify({'error': 'No sigues a este usuario'}), 404
            
        return jsonify({'mensaje': 'Dejaste de seguir al usuario'}), 200
    except Exception as e:
        print(f"Error al dejar de seguir: {e}")
        return jsonify({'error': 'Error interno'}), 500

# Obtener seguidores
@usuarios_bp.route('/clientes/<id>/seguidores', methods=['GET'])
def obtener_seguidores(id):
    try:
        skip, limit = get_pagination(request)
        seguimientos = list(db.seguimientos.find({'seguido_id': ObjectId(id)}).skip(skip).limit(limit))
        seguidores_ids = [s['seguidor_id'] for s in seguimientos]
        
        seguidores = list(db.clientes.find({'_id': {'$in': seguidores_ids}}, {'password_hash': 0}))
        for s in seguidores:
            s['_id'] = str(s['_id'])
            if 'nutricionista_id' in s and s['nutricionista_id']:
                s['nutricionista_id'] = str(s['nutricionista_id'])
                
        return jsonify(seguidores), 200
    except Exception as e:
        print(f"Error al obtener seguidores: {e}")
        return jsonify({'error': 'Error interno'}), 500

# Obtener seguidos
@usuarios_bp.route('/clientes/<id>/seguidos', methods=['GET'])
def obtener_seguidos(id):
    try:
        skip, limit = get_pagination(request)
        seguimientos = list(db.seguimientos.find({'seguidor_id': ObjectId(id)}).skip(skip).limit(limit))
        seguidos_ids = [s['seguido_id'] for s in seguimientos]
        
        seguidos = list(db.clientes.find({'_id': {'$in': seguidos_ids}}, {'password_hash': 0}))
        for s in seguidos:
            s['_id'] = str(s['_id'])
            if 'nutricionista_id' in s and s['nutricionista_id']:
                s['nutricionista_id'] = str(s['nutricionista_id'])
                
        return jsonify(seguidos), 200
    except Exception as e:
        print(f"Error al obtener seguidos: {e}")
        return jsonify({'error': 'Error interno'}), 500
