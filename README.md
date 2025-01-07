# README - Microservicio API Chatbot

Este microservicio gestiona un webhook para recibir y manejar mensajes provenientes del servidor de Meta (WhatsApp Business API). El sistema está diseñado para responder automáticamente a los usuarios en "tiempo real" y almacenar los mensajes en una base de datos MySQL. Además, se utilizan endpoints para que el frontend pueda enviar mensajes a través de la API.

## Funcionalidades

- **Manejo de mensajes entrantes:** Utiliza un webhook para recibir mensajes enviados por los usuarios.
- **Respuestas automáticas:** Envía respuestas basadas en la lógica predefinida para la comunicación.
- **Endpoints para el envío de mensajes:** Permite al frontend enviar mensajes a través de la API.
- **Validación de seguridad:** Utiliza un token de seguridad para validar los mensajes enviados y las solicitudes recibidas.

## Requisitos

Las siguientes bibliotecas son necesarias para el funcionamiento del microservicio:

- **Heyoo:** Librería para interactuar con la API de WhatsApp.
- **Flask:** Framework para el servidor web.
- **Unidecode:** Para la normalización y validación de caracteres en los mensajes.
- **Flask-CORS:** Para manejar el control de acceso entre el servidor y otras APIs.

## Instalación

Para instalar las dependencias necesarias, ejecuta los siguientes comandos:

```bash
pip install heyoo
pip install unidecode
pip install flask
pip install flask-cors
pip install gunicorn  # Para iniciar el servidor


Estas bibliotecas deben ser instaladas en el entorno de desarrollo y en el servidor de producción.

Estructura del Proyecto
El archivo principal __init__.py contiene la configuración base del servidor utilizando Flask. Los módulos adicionales están organizados de la siguiente manera:

messages.py: Define los mensajes predeterminados que se envían a los usuarios, almacenándolos en variables para mejorar la velocidad de respuesta.
services.py: Maneja la lógica de negocio y la interacción con la base de datos MySQL a través de endpoints específicos.
utils.py: Incluye funciones auxiliares para organizar el código y mantener la limpieza en __init__.py.
Observaciones Importantes
Validación de Seguridad: Se requiere un token de seguridad para autenticar las solicitudes y los mensajes enviados. Esto garantiza que solo los mensajes válidos sean procesados.
Migración de Servidores: En caso de cambiar de servidor, asegúrate de actualizar la URL del webhook y las credenciales del sistema.