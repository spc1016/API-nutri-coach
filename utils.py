from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request
from pymongo import MongoClient
import os       
from redis import Redis
from rq import Queue

# Configuración de base de datos compartida
client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))
db = client.NutricionDB

# Configuración de Redis y RQ (Redis Queue)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_conn = Redis.from_url(redis_url)
    task_queue = Queue('emails', connection=redis_conn)
except Exception as e:
    print(f"Error al conectar con Redis: {e}")
    redis_conn = None
    task_queue = None

# Helper para extraer paginación (limite por defecto a 50)
def get_pagination(request, default_limit=50):
    try:
        skip = int(request.args.get('skip', 0))
    except ValueError:
        skip = 0
    try:
        limit = int(request.args.get('limit', default_limit))
        if limit < 0:
            limit = default_limit
    except ValueError:
        limit = default_limit
    return skip, limit


# Decorador para verificar autenticación y rol (compartido entre Blueprints)
def check_auth(required_role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != required_role:
                return jsonify({'error': 'Acceso no autorizado'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Decorador: cualquier usuario logueado (cliente o nutricionista)
def check_auth_any():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Decorador: solo el propio cliente (por su ID) o un nutricionista
def check_auth_owner_or_nutricionista():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_id = get_jwt_identity()
            role = claims.get('role')
            # El nutricionista siempre tiene acceso
            if role == 'nutricionista':
                return fn(*args, **kwargs)
            # El cliente solo puede acceder a sus propios datos
            resource_id = kwargs.get('id', '')
            if role == 'cliente' and user_id == resource_id:
                return fn(*args, **kwargs)
            return jsonify({'error': 'Acceso no autorizado'}), 403
        return wrapper
    return decorator
