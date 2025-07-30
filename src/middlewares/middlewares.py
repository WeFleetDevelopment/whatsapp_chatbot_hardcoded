from functools import wraps
from flask import request, jsonify
import os

# Middleware personalizado para la Auth del Chatbot
def require_auth_chatbot(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        expected_token = os.getenv('TOKEN_CHATBOT_WHATSAPP_BUSINESS')
        received_token = request.headers.get('auth-chatbot')

        if not received_token:
            return jsonify({"error": "Token de autenticación inválido'"}), 401
        if received_token != expected_token:
            return jsonify({"error": "Token de autenticación inválido"}), 403

        return f(*args, **kwargs)
    return decorated_function
