from flask import Blueprint, jsonify, request
from bson import ObjectId
from jsonschema import validate
from flask_jwt_extended import get_jwt, get_jwt_identity
from utils import db, check_auth, check_auth_any

seguimiento_bp = Blueprint('seguimiento', __name__)

# Obtener seguimiento por ID
@seguimiento_bp.route('/seguimientos/<id>', methods=['GET'])
@check_auth_any()
def obtener_seguimiento(id):
    try:
        seguimiento = db.seguimientos.find_one({'_id': ObjectId(id)})
        if not seguimiento:
            return jsonify({'error': 'Seguimiento no encontrado'}), 404
        
        # Si es cliente, solo puede ver sus propios seguimientos
        claims = get_jwt()
        if claims.get('role') == 'cliente':
            user_id = get_jwt_identity()
            seg_cliente_id = str(seguimiento.get('cliente_id', ''))
            if seg_cliente_id != user_id:
                return jsonify({'error': 'No puedes ver seguimientos de otro cliente'}), 403
        
        seguimiento['_id'] = str(seguimiento['_id'])
        if 'cliente_id' in seguimiento:
            seguimiento['cliente_id'] = str(seguimiento['cliente_id'])
        return jsonify(seguimiento), 200
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Agregar seguimiento (requiere autenticación, cualquier rol)
@seguimiento_bp.route('/seguimientos', methods=['POST'])
@check_auth_any()
def agregar_seguimiento():
    try:
        data:dict = request.get_json()
        schema:dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "cliente_id": { "type": "string" },
                "fecha": { "type": "string" },
                "peso": { "type": "number" },
                "notas": { "type": "string" }
            },
            "required": ["cliente_id", "fecha"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Si es cliente, solo puede crear seguimientos para sí mismo
        claims = get_jwt()
        if claims.get('role') == 'cliente':
            user_id = get_jwt_identity()
            if data['cliente_id'] != user_id:
                return jsonify({'error': 'No puedes crear un seguimiento para otro cliente'}), 403
        
        data['cliente_id'] = ObjectId(data['cliente_id'])
        result = db.seguimientos.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos para crear seguimiento'}), 400
