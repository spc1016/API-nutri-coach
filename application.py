import os
from datetime import timedelta
from flask import Flask, send_file
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint


# Importar Blueprints
from blueprints.auth import auth_bp
from blueprints.usuarios import usuarios_bp
from blueprints.catalogos import catalogos_bp
from blueprints.planes import planes_bp
from blueprints.seguimiento import seguimiento_bp

application = Flask(__name__)
application.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY")
application.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(application)

# Registrar Blueprints sin prefijo para mantener compatibilidad
application.register_blueprint(auth_bp)
application.register_blueprint(usuarios_bp)
application.register_blueprint(catalogos_bp)
application.register_blueprint(planes_bp)
application.register_blueprint(seguimiento_bp)

# Swagger UI
SWAGGER_URL = '/docs'
API_URL = '/docs/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'API Nutrición'}
)
application.register_blueprint(swaggerui_blueprint)

@application.route('/docs/swagger.yaml')
def swagger_yaml():
    yaml_path = os.path.join(os.path.dirname(__file__), 'documentation.yaml')
    return send_file(yaml_path, mimetype='application/yaml')

@application.route('/', methods=['GET'])
def index():
    return "<h1>API LEVANTADA CON BLUEPRINTS</h1>"

if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0')