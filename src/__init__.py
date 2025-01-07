import os
from flask import Flask
from flask_cors import CORS

# Rutas
from src.routes.whatsapp_routes import whatsapp_routes

#Data Base of MySql
from src.database.mysql.mysql_config import Database

def create_app():
    app = Flask(__name__)
    # CORS(app, resources={r"/*": {"origins": ["http://localhost:9302","https://fletzy-back-admin-test-production.up.railway.app"]}}, supports_credentials=True)
    CORS(app, resources={r"/*": {"origins": ["https://hoktus-api-messages-test-production.up.railway.app","http://localhost:9000"]}}, supports_credentials=True)
    
    # Definir la ruta de la carpeta temporal
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
    
    # Verificar si la carpeta existe, si no, crearla
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
        
    # Inicializamos la base de datos de MySql
    db = Database()
    db.init_app(app)
    
    # Inicializamos las rutas
    app.register_blueprint(whatsapp_routes)
    
    return app   