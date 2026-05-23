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

def _oid_to_str(obj):
    """Convierte recursivamente todos los ObjectId a string."""
    if isinstance(obj, list):
        return [_oid_to_str(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _oid_to_str(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Agregar un registro de entrenamiento completado
@seguimiento_bp.route('/clientes/<cliente_id>/historial-entrenamientos', methods=['POST'])
@check_auth_any()
def registrar_entrenamiento(cliente_id):
    try:
        data: dict = request.get_json()
        schema: dict = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "rutina_nombre": { "type": "string" },
                "dia_nombre": { "type": "string" },
                "fecha": { "type": "string" },
                "ejercicios": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ejercicio_id": { "type": "string" },
                            "nombre_snapshot": { "type": "string" },
                            "series": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "repeticiones": { "type": "string" },
                                        "peso": { "type": "number" },
                                        "descanso_segundos": { "type": "integer" }
                                    },
                                    "required": ["repeticiones", "peso"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["nombre_snapshot", "series"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["fecha", "ejercicios"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)
        
        # Verificar autorización
        claims = get_jwt()
        if claims.get('role') == 'cliente':
            user_id = get_jwt_identity()
            if cliente_id != user_id:
                return jsonify({'error': 'No puedes registrar un entrenamiento para otro cliente'}), 403
        
        # Añadir ID del cliente y guardar
        data['cliente_id'] = ObjectId(cliente_id)
        # Convertir ejercicio_id a ObjectId si se proporciona
        for ejer in data.get('ejercicios', []):
            if 'ejercicio_id' in ejer and ejer['ejercicio_id'] and ejer['ejercicio_id'] != "000000000000000000000000":
                try:
                    ejer['ejercicio_id'] = ObjectId(ejer['ejercicio_id'])
                except Exception:
                    pass
        
        result = db.historial_entrenamientos.insert_one(data)
        return jsonify({'id': str(result.inserted_id)}), 201
    except Exception as e:
        print(f"Error al registrar entrenamiento: {e}")
        return jsonify({'error': 'Datos inválidos para registrar entrenamiento'}), 400

# Obtener historial de entrenamientos de un cliente
@seguimiento_bp.route('/clientes/<cliente_id>/historial-entrenamientos', methods=['GET'])
@check_auth_any()
def obtener_historial_entrenamientos(cliente_id):
    try:
        # Verificar autorización
        claims = get_jwt()
        if claims.get('role') == 'cliente':
            user_id = get_jwt_identity()
            if cliente_id != user_id:
                return jsonify({'error': 'No puedes ver el historial de otro cliente'}), 403
        
        try:
            oid = ObjectId(cliente_id)
            query = {'$or': [{'cliente_id': oid}, {'cliente_id': cliente_id}]}
        except Exception:
            query = {'cliente_id': cliente_id}
            
        historial = list(db.historial_entrenamientos.find(query).sort('fecha', -1))
        return jsonify(_oid_to_str(historial)), 200
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return jsonify({'error': 'Error al recuperar historial'}), 400

