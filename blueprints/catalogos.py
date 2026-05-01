from flask import Blueprint, jsonify, request
from bson import ObjectId
from jsonschema import validate
from utils import db, check_auth

catalogos_bp = Blueprint('catalogos', __name__)

# Obtener todos los alimentos
@catalogos_bp.route('/alimentos', methods=['GET'])
def obtener_alimentos():
    try:
        alimentos = list(db.alimentos.find())
        for a in alimentos:
            a['_id'] = str(a['_id'])
        return jsonify(alimentos), 200
    except Exception:
        return jsonify({'error': 'Error al obtener alimentos'}), 400

# Obtener alimento por ID
@catalogos_bp.route('/alimentos/<id>', methods=['GET'])
def obtener_alimento(id):
    try:
        alimento = db.alimentos.find_one({'_id': ObjectId(id)})
        if not alimento:
            return jsonify({'error': 'Alimento no encontrado'}), 404
        alimento['_id'] = str(alimento['_id'])
        return jsonify(alimento), 200
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Obtener todos los ejercicios
@catalogos_bp.route('/ejercicios', methods=['GET'])
def obtener_ejercicios():
    try:
        ejercicios = list(db.ejercicios.find())
        for e in ejercicios:
            e['_id'] = str(e['_id'])
        return jsonify(ejercicios), 200
    except Exception:
        return jsonify({'error': 'Error al obtener ejercicios'}), 400

# Obtener ejercicio por ID
@catalogos_bp.route('/ejercicios/<id>', methods=['GET'])
def obtener_ejercicio(id):
    try:
        ejercicio = db.ejercicios.find_one({'_id': ObjectId(id)})
        if not ejercicio:
            return jsonify({'error': 'Ejercicio no encontrado'}), 404
        ejercicio['_id'] = str(ejercicio['_id'])
        return jsonify(ejercicio), 200
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Agregar alimento (requiere autenticación)
@catalogos_bp.route('/alimentos', methods=['POST'])
@check_auth('nutricionista')
def agregar_alimento():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "calorias": { "type": "number" },
                "proteinas": { "type": "number" },
                "carbohidratos": { "type": "number" },
                "grasas": { "type": "number" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        result = db.alimentos.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos para crear alimento'}), 400

# Agregar ejercicio (requiere autenticación)
@catalogos_bp.route('/ejercicios', methods=['POST'])
@check_auth('nutricionista')
def agregar_ejercicio():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "descripcion": { "type": "string" },
                "grupo_muscular": { "type": "string" },
                "duracion_minutos": { "type": "integer" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        result = db.ejercicios.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos para crear ejercicio'}), 400

# Modificar alimento (requiere autenticación)
@catalogos_bp.route('/alimentos/<id>', methods=['PUT'])
@check_auth('nutricionista')
def modificar_alimento(id):
    try:
        data: dict = request.get_json()
        schema: dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "calorias": { "type": "number" },
                "proteinas": { "type": "number" },
                "carbohidratos": { "type": "number" },
                "grasas": { "type": "number" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        result = db.alimentos.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Alimento no encontrado'}), 404
        alimento = db.alimentos.find_one({'_id': ObjectId(id)})
        alimento['_id'] = str(alimento['_id'])
        return jsonify(alimento), 200
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Modificar ejercicio (requiere autenticación)
@catalogos_bp.route('/ejercicios/<id>', methods=['PUT'])
@check_auth('nutricionista')
def modificar_ejercicio(id):
    try:
        data: dict = request.get_json()
        schema: dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "nombre": { "type": "string", "minLength": 1 },
                "descripcion": { "type": "string" },
                "grupo_muscular": { "type": "string" },
                "duracion_minutos": { "type": "integer" }
            },
            "required": ["nombre"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        result = db.ejercicios.update_one({'_id': ObjectId(id)}, {'$set': data})
        if result.matched_count == 0:
            return jsonify({'error': 'Ejercicio no encontrado'}), 404
        ejercicio = db.ejercicios.find_one({'_id': ObjectId(id)})
        ejercicio['_id'] = str(ejercicio['_id'])
        return jsonify(ejercicio), 200
    except Exception:
        return jsonify({'error': 'Datos inválidos'}), 400

# Eliminar alimento (requiere autenticación)
@catalogos_bp.route('/alimentos/<id>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_alimento(id):
    try:
        result = db.alimentos.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Alimento no encontrado'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Eliminar ejercicio (requiere autenticación)
@catalogos_bp.route('/ejercicios/<id>', methods=['DELETE'])
@check_auth('nutricionista')
def eliminar_ejercicio(id):
    try:
        result = db.ejercicios.delete_one({'_id': ObjectId(id)})
        if result.deleted_count == 0:
            return jsonify({'error': 'Ejercicio no encontrado'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400
