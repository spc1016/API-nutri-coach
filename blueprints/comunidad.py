from flask import Blueprint, jsonify, request
from bson import ObjectId
from jsonschema import validate
from utils import db, check_auth_any
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from datetime import datetime

comunidad_bp = Blueprint('comunidad', __name__)

def _oid_to_str(obj):
    """Convierte recursivamente todos los ObjectId a string."""
    if isinstance(obj, list):
        return [_oid_to_str(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _oid_to_str(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj

# Obtener todos los posts (públicos y activos) con paginación
@comunidad_bp.route('/posts', methods=['GET'])
def obtener_posts():
    try:
        limit = request.args.get('limit', default=10, type=int)
        limit = min(max(1, limit), 50)  # Limitar entre 1 y 50 para evitar abusos
        
        cursor = request.args.get('cursor')
        
        filtro = {'activa': {'$ne': False}}
        if cursor:
            filtro['fecha_creacion'] = {'$lt': cursor}

        # Ordenados por fecha descendente (más recientes primero)
        posts = list(db.posts.find(filtro).sort('fecha_creacion', -1).limit(limit))
        return jsonify(_oid_to_str(posts)), 200
    except Exception as e:
        print(f"Error en obtener_posts: {e}")
        return jsonify({'error': str(e)}), 400

# Obtener un post por su ID
@comunidad_bp.route('/posts/<id>', methods=['GET'])
def obtener_post(id):
    try:
        post = db.posts.find_one({'_id': ObjectId(id), 'activa': {'$ne': False}})
        if not post:
            return jsonify({'error': 'Post no encontrado'}), 404
        return jsonify(_oid_to_str(post)), 200
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Crear un nuevo post
@comunidad_bp.route('/posts', methods=['POST'])
@check_auth_any()
def crear_post():
    try:
        data = request.get_json()
        schema = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "texto": { "type": "string", "minLength": 1 },
                "rutina_id": { "type": ["string", "null"] },
                "dieta_id": { "type": ["string", "null"] },
                "imagen_url": { "type": ["string", "null"] }
            },
            "required": ["texto"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)

        claims = get_jwt()
        user_id = get_jwt_identity()
        role = claims.get('role')

        # Obtener el nombre del autor
        autor_nombre = "Usuario Anónimo"
        usuario = None
        if role == 'cliente':
            usuario = db.clientes.find_one({'_id': ObjectId(user_id)})
        elif role == 'nutricionista':
            usuario = db.nutricionistas.find_one({'_id': ObjectId(user_id)})
            
        if usuario and 'nombre' in usuario:
            autor_nombre = usuario['nombre']

        nuevo_post = {
            "autor_id": ObjectId(user_id),
            "autor_nombre": autor_nombre,
            "texto": data["texto"],
            "rutina_id": ObjectId(data["rutina_id"]) if data.get("rutina_id") else None,
            "dieta_id": ObjectId(data["dieta_id"]) if data.get("dieta_id") else None,
            "imagen_url": data.get("imagen_url"),
            "likes": 0,
            "liked_by": [],
            "comentarios": [],
            "fecha_creacion": datetime.utcnow().isoformat(),
            "activa": True
        }

        result = db.posts.insert_one(nuevo_post)
        return jsonify({'id': str(result.inserted_id)}), 201

    except Exception as e:
        print(f"Error en crear_post: {e}")
        return jsonify({'error': 'Datos inválidos o error al crear post'}), 400

# Eliminar un post (soft delete)
@comunidad_bp.route('/posts/<id>', methods=['DELETE'])
@check_auth_any()
def eliminar_post(id):
    try:
        post = db.posts.find_one({'_id': ObjectId(id)})
        if not post:
            return jsonify({'error': 'Post no encontrado'}), 404

        user_id = get_jwt_identity()
        
        # Solo el autor del post puede eliminarlo
        if str(user_id) != str(post.get('autor_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        db.posts.update_one({'_id': ObjectId(id)}, {'$set': {'activa': False}})
        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Dar o quitar like a un post
@comunidad_bp.route('/posts/<id>/like', methods=['POST'])
@check_auth_any()
def toggle_like_post(id):
    try:
        post = db.posts.find_one({'_id': ObjectId(id), 'activa': {'$ne': False}})
        if not post:
            return jsonify({'error': 'Post no encontrado'}), 404

        user_id = get_jwt_identity()
        liked_by = [str(u) for u in post.get('liked_by', [])]

        if user_id in liked_by:
            # Ya dio like, se lo quitamos
            db.posts.update_one(
                {'_id': ObjectId(id)},
                {
                    '$pull': {'liked_by': ObjectId(user_id)},
                    '$inc': {'likes': -1}
                }
            )
            return jsonify({'mensaje': 'Like removido', 'liked': False}), 200
        else:
            # Dar like
            db.posts.update_one(
                {'_id': ObjectId(id)},
                {
                    '$addToSet': {'liked_by': ObjectId(user_id)},
                    '$inc': {'likes': 1}
                }
            )
            return jsonify({'mensaje': 'Like agregado', 'liked': True}), 200

    except Exception:
        return jsonify({'error': 'ID inválido'}), 400

# Agregar comentario a un post
@comunidad_bp.route('/posts/<id>/comentarios', methods=['POST'])
@check_auth_any()
def agregar_comentario(id):
    try:
        data = request.get_json()
        schema = {
            "$schema": "http://json-schema.org",
            "type": "object",
            "properties": {
                "texto": { "type": "string", "minLength": 1 }
            },
            "required": ["texto"],
            "additionalProperties": False
        }
        validate(instance=data, schema=schema)

        post = db.posts.find_one({'_id': ObjectId(id), 'activa': {'$ne': False}})
        if not post:
            return jsonify({'error': 'Post no encontrado'}), 404

        claims = get_jwt()
        user_id = get_jwt_identity()
        role = claims.get('role')

        autor_nombre = "Usuario Anónimo"
        usuario = None
        if role == 'cliente':
            usuario = db.clientes.find_one({'_id': ObjectId(user_id)})
        elif role == 'nutricionista':
            usuario = db.nutricionistas.find_one({'_id': ObjectId(user_id)})
            
        if usuario and 'nombre' in usuario:
            autor_nombre = usuario['nombre']

        nuevo_comentario = {
            "autor_id": ObjectId(user_id),
            "autor_nombre": autor_nombre,
            "texto": data["texto"],
            "fecha": datetime.utcnow().isoformat()
        }

        db.posts.update_one(
            {'_id': ObjectId(id)},
            {'$push': {'comentarios': nuevo_comentario}}
        )

        return jsonify({'mensaje': 'Comentario agregado'}), 201
    except Exception:
        return jsonify({'error': 'Datos inválidos o ID inválido'}), 400

# Eliminar un comentario de un post
@comunidad_bp.route('/posts/<id>/comentarios/<int:comentario_index>', methods=['DELETE'])
@check_auth_any()
def eliminar_comentario(id, comentario_index):
    try:
        post = db.posts.find_one({'_id': ObjectId(id), 'activa': {'$ne': False}})
        if not post:
            return jsonify({'error': 'Post no encontrado'}), 404

        comentarios = post.get('comentarios', [])
        if comentario_index < 0 or comentario_index >= len(comentarios):
            return jsonify({'error': 'Índice de comentario fuera de rango'}), 404

        comentario = comentarios[comentario_index]
        user_id = get_jwt_identity()

        # Solo el autor del comentario o el autor del post pueden eliminarlo
        if str(user_id) != str(comentario.get('autor_id')) and str(user_id) != str(post.get('autor_id')):
            return jsonify({'error': 'Acceso no autorizado'}), 403

        comentarios.pop(comentario_index)
        
        db.posts.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'comentarios': comentarios}}
        )

        return '', 204
    except Exception:
        return jsonify({'error': 'ID inválido'}), 400
