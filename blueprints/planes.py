from flask import Blueprint, jsonify, request
from bson import ObjectId
from jsonschema import validate
from utils import db, check_auth, check_auth_owner_or_nutricionista, check_auth_any
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity

planes_bp = Blueprint('planes', __name__)

def _oid_to_str(obj):
    """Convierte recursivamente todos los ObjectId a string."""
    if isinstance(obj, list):
        return [_oid_to_str(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _oid_to_str(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Obtener dietas por cliente
@planes_bp.route('/clientes/<id>/dietas', methods=['GET'])
def obtener_dietas_cliente(id):
    try:
        try:
            oid = ObjectId(id)
            dietas = list(db.dietas.find({'$or': [{'cliente_id': oid}, {'cliente_id': id}]}))
        except Exception:
            dietas = list(db.dietas.find({'cliente_id': id}))
        return jsonify(_oid_to_str(dietas)), 200
    except Exception as e:
        print(f"Error en obtener_dietas_cliente: {e}")
        return jsonify({'error': str(e)}), 400

# Obtener rutinas por cliente
@planes_bp.route('/clientes/<id>/rutinas', methods=['GET'])
def obtener_rutinas_cliente(id):
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
        role = claims.get('role')
        user_id = get_jwt_identity()

        is_owner_or_nutri = False
        if role == 'nutricionista' or (role == 'cliente' and str(user_id) == str(id)):
            is_owner_or_nutri = True

        try:
            oid = ObjectId(id)
            query = {'$or': [{'cliente_id': oid}, {'cliente_id': id}]}
        except Exception:
            query = {'cliente_id': id}
            
        if not is_owner_or_nutri:
            query = {'$and': [query, {'publica': True}]}
            
        rutinas = list(db.rutinas.find(query))
        return jsonify(_oid_to_str(rutinas)), 200
    except Exception as e:
        print(f"Error en obtener_rutinas_cliente: {e}")
        return jsonify({'error': str(e)}), 400
# Obtener ACTIVAS dieta por cliente
@planes_bp.route('/clientes/<id>/dietas-activas', methods=['GET'])
def obtener_dietas_activas_cliente(id):
    try:
        try:
            oid = ObjectId(id)
            dietas = list(db.dietas.find({'$or': [{'cliente_id': oid}, {'cliente_id': id}], 'activa': {'$ne': False}}))
        except Exception:
            dietas = list(db.dietas.find({'cliente_id': id, 'activa': {'$ne': False}}))
        return jsonify(_oid_to_str(dietas)), 200
    except Exception as e:
        print(f"Error en obtener_dietas_cliente: {e}")
        return jsonify({'error': str(e)}), 400

# Obtener ACTIVAS rutinas por cliente
@planes_bp.route('/clientes/<id>/rutinas-activas', methods=['GET'])
def obtener_rutinas_activas_cliente(id):
    try:
        verify_jwt_in_request(optional=True)
        claims = get_jwt() or {}
        role = claims.get('role')
        user_id = get_jwt_identity()

        is_owner_or_nutri = False
        if role == 'nutricionista' or (role == 'cliente' and str(user_id) == str(id)):
            is_owner_or_nutri = True

        try:
            oid = ObjectId(id)
            query = {'$or': [{'cliente_id': oid}, {'cliente_id': id}], 'activa': {'$ne': False}}
        except Exception:
            query = {'cliente_id': id, 'activa': {'$ne': False}}

        if not is_owner_or_nutri:
            query = {'$and': [query, {'publica': True}]}

        rutinas = list(db.rutinas.find(query))
        return jsonify(_oid_to_str(rutinas)), 200
    except Exception as e:
        print(f"Error en obtener_rutinas_activas_cliente: {e}")
        return jsonify({'error': str(e)}), 400

# Obtener todas las dietas públicas
@planes_bp.route('/dietas/publicas', methods=['GET'])
def obtener_dietas_publicas():
    try:
        dietas = list(db.dietas.find({'publica': True, 'activa': {'$ne': False}}))
        return jsonify(_oid_to_str(dietas)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Obtener todas las rutinas públicas
@planes_bp.route('/rutinas/publicas', methods=['GET'])
def obtener_rutinas_publicas():
    try:
        rutinas = list(db.rutinas.find({'publica': True, 'activa': {'$ne': False}}))
        return jsonify(_oid_to_str(rutinas)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Agregar dieta (requiere autenticación)
@planes_bp.route('/dietas', methods=['POST'])
@check_auth('nutricionista')
def agregar_dieta():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "kcal_objetivo": { "type": "integer" },
                "notas_generales": { "type": "string" },
                "cliente_id": { "type": "string" },
                "comidas": { "type": "array" },
                "activa": { "type": "boolean" },
                "publica": { "type": "boolean" }
            },
            "required": ["nombre", "cliente_id"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        data['activa'] = data.get('activa', True)
        data['publica'] = data.get('publica', False)
        data['cliente_id'] = ObjectId(data['cliente_id'])
        result = db.dietas.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos para crear dieta'}), 400

# Agregar rutina (requiere autenticación)
@planes_bp.route('/rutinas', methods=['POST'])
@check_auth_any()
def agregar_rutina():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "cliente_id": { "type": "string" },
                "dias": { "type": "array" },
                "activa": { "type": "boolean" },
                "publica": { "type": "boolean" }
            },
            "required": ["nombre", "cliente_id"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != data['cliente_id']:
            return jsonify({'error': 'No puedes crear rutinas para otro usuario'}), 403

        data['activa'] = data.get('activa', True)
        data['publica'] = data.get('publica', False)
        data['cliente_id'] = ObjectId(data['cliente_id'])
        result = db.rutinas.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos para crear rutina'}), 400

# Eliminar dieta (requiere autenticación) - marca como inactiva
@planes_bp.route('/dietas/<id>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_dieta(id):
    try:
        result = db.dietas.update_one({'_id': ObjectId(id)}, {'$set': {'activa': False}})
        if result.matched_count == 0:
            return jsonify({'error': 'Dieta no encontrada'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Eliminar rutina (requiere autenticación) - marca como inactiva
@planes_bp.route('/rutinas/<id>', methods=['DELETE'])
@check_auth_any()
def eliminar_rutina(id):
    try:
        rutina = db.rutinas.find_one({'_id': ObjectId(id)})
        if not rutina:
            return jsonify({'error': 'Rutina no encontrada'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != str(rutina.get('cliente_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        result = db.rutinas.update_one({'_id': ObjectId(id)}, {'$set': {'activa': False}})
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Modificar dieta (requiere autenticación)
@planes_bp.route('/dietas/<id>', methods=['PUT'])
@check_auth('nutricionista')
def modificar_dieta(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "comidas": { "type": "array" },
                "activa": { "type": "boolean" },
                "publica": { "type": "boolean" }
            },
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        result = db.dietas.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Dieta no encontrada'}), 404
        return jsonify({'mensaje': 'Dieta actualizada'}), 200
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Modificar rutina (requiere autenticación)
@planes_bp.route('/rutinas/<id>', methods=['PUT'])
@check_auth_any()
def modificar_rutina(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "dias": { "type": "array" },
                "activa": { "type": "boolean" },
                "publica": { "type": "boolean" }
            },
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        rutina = db.rutinas.find_one({'_id': ObjectId(id)})
        if not rutina:
            return jsonify({'error': 'Rutina no encontrada'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != str(rutina.get('cliente_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        result = db.rutinas.update_one({'_id': ObjectId(id)}, {'$set': data})
        return jsonify({'mensaje': 'Rutina actualizada'}), 200
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Agregar comida a dieta (requiere autenticación)
@planes_bp.route('/dietas/<id>/comidas', methods=['POST'])
@check_auth('nutricionista')
def agregar_comida_a_dieta(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "hora": { "type": "string" },
                "alimentos": { "type": "array" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        data['alimentos'] = data.get('alimentos', [])
        result = db.dietas.update_one(
            {'_id': ObjectId(id)},
            {'$push': {'comidas': data}}
        )
        if result.matched_count == 0:
            return jsonify({'error': 'Dieta no encontrada'}), 404
        return jsonify({'mensaje': 'Comida agregada'}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Agregar alimento a comida dentro de una dieta (requiere autenticación)
@planes_bp.route('/dietas/<id>/comidas/<int:comida_index>/alimentos', methods=['POST'])
@check_auth('nutricionista')
def agregar_alimento_a_comida(id, comida_index):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "alimento_id": { "type": "string" },
                "nombre_snapshot": { "type": "string" },
                "cantidad": { "type": "number" },
                "unidad": { "type": "string" }
            },
            "required": ["alimento_id"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        data['alimento_id'] = ObjectId(data['alimento_id'])
        result = db.dietas.update_one(
            {'_id': ObjectId(id)},
            {'$push': {f'comidas.{comida_index}.alimentos': data}}
        )
        if result.matched_count == 0:
            return jsonify({'error': 'Dieta o comida no encontrada'}), 404
        return jsonify({'mensaje': 'Alimento agregado a la comida'}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Agregar día a rutina (requiere autenticación)
@planes_bp.route('/rutinas/<id>/dias', methods=['POST'])
@check_auth_any()
def agregar_dia_a_rutina(id):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "ejercicios": { "type": "array" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)

        rutina = db.rutinas.find_one({'_id': ObjectId(id)})
        if not rutina:
            return jsonify({'error': 'Rutina no encontrada'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != str(rutina.get('cliente_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        data['ejercicios'] = data.get('ejercicios', [])
        result = db.rutinas.update_one(
            {'_id': ObjectId(id)},
            {'$push': {'dias': data}}
        )
        return jsonify({'mensaje': 'Día agregado a la rutina'}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Agregar ejercicio a día dentro de una rutina (requiere autenticación)
@planes_bp.route('/rutinas/<id>/dias/<int:dia_index>/ejercicios', methods=['POST'])
@check_auth_any()
def agregar_ejercicio_a_dia(id, dia_index):
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "ejercicio_id": { "type": "string" },
                "nombre_snapshot": {"type": "string"},
                "series": { "type": "integer" },
                "repeticiones": { "type": "integer" },
                "descanso_segundos": { "type": "integer" }
            },
            "required": ["ejercicio_id"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)

        rutina = db.rutinas.find_one({'_id': ObjectId(id)})
        if not rutina:
            return jsonify({'error': 'Rutina no encontrada'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != str(rutina.get('cliente_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        data['ejercicio_id'] = ObjectId(data['ejercicio_id'])
        result = db.rutinas.update_one(
            {'_id': ObjectId(id)},
            {'$push': {f'dias.{dia_index}.ejercicios': data}}
        )
        return jsonify({'mensaje': 'Ejercicio agregado al día'}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Eliminar alimento de comida dentro de una dieta (requiere autenticación)
@planes_bp.route('/dietas/<id>/comidas/<int:comida_index>/alimentos/<int:alimento_index>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_alimento_de_comida(id, comida_index, alimento_index):
    try:
        dieta = db.dietas.find_one({'_id': ObjectId(id)})
        if not dieta:
            return jsonify({'error': 'Dieta no encontrada'}), 404
        
        comidas = dieta.get('comidas', [])
        if comida_index < 0 or comida_index >= len(comidas):
            return jsonify({'error': 'Índice de comida fuera de rango'}), 404
            
        alimentos = comidas[comida_index].get('alimentos', [])
        if alimento_index < 0 or alimento_index >= len(alimentos):
            return jsonify({'error': 'Índice de alimento fuera de rango'}), 404
            
        alimentos.pop(alimento_index)
        
        db.dietas.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'comidas.{comida_index}.alimentos': alimentos}}
        )
            
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Eliminar ejercicio de día dentro de una rutina (requiere autenticación)
@planes_bp.route('/rutinas/<id>/dias/<int:dia_index>/ejercicios/<int:ejercicio_index>', methods=['DELETE'])
@check_auth_any()
def eliminar_ejercicio_de_dia(id, dia_index, ejercicio_index):
    try:
        rutina = db.rutinas.find_one({'_id': ObjectId(id)})
        if not rutina:
            return jsonify({'error': 'Rutina no encontrada'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        if claims.get('role') == 'cliente' and str(user_id) != str(rutina.get('cliente_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403
        
        dias = rutina.get('dias', [])
        if dia_index < 0 or dia_index >= len(dias):
            return jsonify({'error': 'Índice de día fuera de rango'}), 404
            
        ejercicios = dias[dia_index].get('ejercicios', [])
        if ejercicio_index < 0 or ejercicio_index >= len(ejercicios):
            return jsonify({'error': 'Índice de ejercicio fuera de rango'}), 404
            
        ejercicios.pop(ejercicio_index)
        
        db.rutinas.update_one(
            {'_id': ObjectId(id)},
            {'$set': {f'dias.{dia_index}.ejercicios': ejercicios}}
        )
            
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400
