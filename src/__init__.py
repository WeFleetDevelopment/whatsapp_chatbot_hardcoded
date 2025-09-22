import os
from flask import Flask
from flask_cors import CORS

# Rutas
from src.routes.whatsapp_routes import whatsapp_routes

# Data Base of MySql
from src.database.mysql.mysql_config import db, Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 🔓 CORS abierto para cualquier origen
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Definir la ruta de la carpeta temporal
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
    
    # Verificar si la carpeta existe, si no, crearla
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    # Inicializamos la base de datos de MySql
    db.init_app(app)
    
    # Inicializamos las rutas
    app.register_blueprint(whatsapp_routes)
    
    return app
