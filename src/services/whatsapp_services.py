import requests
import os
import json
import time
import random
import string
import base64
# Time Chile - Santiago
from datetime import datetime
import pytz
 
# Image
from PIL import Image
from io import BytesIO

#Database of MySql
from sqlalchemy import text
from flask import current_app
from contextlib import contextmanager
from src.database.mysql.mysql_config import db 

#Tenacy
from tenacity import retry, wait_fixed, stop_after_attempt
from sqlalchemy.exc import OperationalError
 
# #Config of the api of whatsapp    
# from src.config.config_Whatsapp impor t messenger,logging

# Carpeta Temp
TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')

# Define la URL base como una variable global
#Original
BASE_URL = 'https://hoktus-api-messages-prod-production.up.railway.app'
BASE_URL_CHATBOT= 'https://business-whatsapp-chatbot-prod-production.up.railway.app'


#Prueba 1
# BASE_URL = 'https://hoktus-api-messages-test-production.up.railway.app'
# BASE_URL_CHATBOT= 'https://business-whatsapp-chatbot-test-production.up.railway.app'


@contextmanager
def session_scope():
    """Proporciona un scope transaccional alrededor de una serie de operaciones."""
    session = db.session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


# ------------------------------------ Funciones para capturar valores en la peticion que envia whatsapp al webhook ---------------------------------

def changed_field(data):
    """
    Identifica qué campo cambió en el payload recibido.
    Esta función es útil para determinar si el cambio fue en mensajes, estados u otro tipo de actualización.
    """
    try:
        return data["entry"][0]["changes"][0]["field"]
    except (KeyError, IndexError):
        return None

def is_message(data):
    """
    Determina si el payload recibido corresponde a un mensaje.
    Esto es crucial para procesar únicamente eventos de mensajes y no otros tipos de eventos como cambios de estado.
    """
    message_data = preprocess(data)
    return "messages" in message_data

def get_mobile(data):
    """
    Extrae el número de teléfono del remitente del mensaje.
    Este número es esencial para identificar quién envía el mensaje y posiblemente vincularlo con un usuario registrado.
    """
    message_data = preprocess(data)
    try:
        return message_data["contacts"][0]["wa_id"]
    except (KeyError, IndexError):
        return None

def get_name(data):
    """
    Extrae el nombre del remitente del mensaje.
    Este nombre es útil para personalizar respuestas o para registros de actividad.
    """
    message_data = preprocess(data)
    try:
        return message_data["contacts"][0]["profile"]["name"]
    except (KeyError, IndexError):
        return None

def get_message_type(data):
    """
    Obtiene el tipo del mensaje recibido, como texto, imagen, video, etc.
    Saber el tipo de mensaje permite que el sistema maneje adecuadamente el contenido según su formato.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["type"]
    except (KeyError, IndexError):
        return None

def get_message(data): 
    """
    Extrae el mensaje de texto del payload recibido.
    Esta es la información central que se utiliza para responder o procesar las solicitudes del usuario.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["text"]["body"]
    except (KeyError, IndexError):
        return None
    
def get_image(data):
    """
    Extrae el ID de la imagen enviada por el remitente a partir de los datos recibidos del webhook.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["image"]
    except (KeyError, IndexError):
        return None

def get_document(data):
    """
    Extrae el ID del documento enviado por el remitente a partir de los datos recibidos del webhook.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["document"]
    except (KeyError, IndexError):
        return None

def get_audio(data):
    """
    Extrae el ID del audio enviado por el remitente a partir de los datos recibidos del webhook.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["audio"]
    except (KeyError, IndexError):
        return None

def get_video(data):
    """
    Extrae el ID del video enviado por el remitente a partir de los datos recibidos del webhook.
    """
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["video"]
    except (KeyError, IndexError):
        return None


def get_interactive_response(data):
    """Extrae la respuesta interactiva del mensaje."""
    message_data = preprocess(data)
    try:
        return message_data["messages"][0]["interactive"]
    except (KeyError, IndexError):
        return None
    
def get_interactive_response_flow(data):
    """Extrae la respuesta interactiva o NFM reply del mensaje."""
    message_data = preprocess(data)
    try:
        if "nfm_reply" in message_data["messages"][0]:  # Verificar si es un NFM Reply
            return message_data["messages"][0]["nfm_reply"]
        elif "interactive" in message_data["messages"][0]:  # Si es un mensaje interactivo
            return message_data["messages"][0]["interactive"]
        else:
            return None
    except (KeyError, IndexError):
        return None
    

def get_delivery(data):
    """Obtiene la información de entrega del mensaje."""
    try:
        delivery_info = data["entry"][0]["changes"][0]["value"]["delivery"]
        return f"Delivered message ID: {delivery_info['mids']}, Status: {delivery_info['status']}"
    except (KeyError, IndexError):
        return None

def preprocess(data):
    """
    Procesa el payload para facilitar el acceso a los datos contenidos.
    Esta función simplifica la extracción de datos organizando el JSON para un acceso más directo y seguro.
    """
    try:
        return data["entry"][0]["changes"][0]["value"]
    except (KeyError, IndexError):
        return {}


#-------------------------------------- Funciones para enviar mensajes a WhatsApp ---------------------------------
def send_document(token, url, document, recipient_id, caption=None, link=True, filename=None):
    """Sends a document message to a WhatsApp user."""

    print(f"Enviando documento a {url} con token {token} y document {document} y  recipient_id {recipient_id} y caption {caption} y link {link} y filename {filename}") 
    if link:
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id, 
            "type": "document",
            "document": {"link": document, "caption": caption, "filename": filename},
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "document",
            "document": {"id": document, "caption": caption},
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def send_message(token, url, message, recipient_id, recipient_type="individual", preview_url=True):
    """Sends a text message to a WhatsApp user."""

    print("Datos para enviar mensaje", token, url, message, recipient_id, recipient_type, preview_url)
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": recipient_type,
        "to": recipient_id,
        "type": "text",
        "text": {"preview_url": preview_url, "body": message},
    } 
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def send_image(token, url, image, recipient_id, recipient_type="individual", caption=None, link=True):
    """Sends an image message to a WhatsApp user."""
    print(f"Enviando imagen a {url} con token {token} y image {image} y  recipient_id {recipient_id}") 
    if link:
        data = { 
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "image",
            "image": {"link": image, "caption": caption},
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": recipient_id,
            "type": "image",
            "image": {"id": image, "caption": caption},
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()



def send_audio(token, url, audio, recipient_id, link=True):
    """Sends an audio message to a WhatsApp user."""
    if link:
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "audio",
            "audio": {"link": audio},
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "audio",
            "audio": {"id": audio},
        }
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers, json=data)
    print("Response from WhatsApp API:", response.text)
    return response.json()


#-------------------------------------- Validations WhatsApp Chatbot y obtencion de datos importantes ---------------------------------

# Function for validate the business chatbot and return token verified of aplication of business
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry_error_callback=lambda retry_state: False, reraise=True)
def validate_business_chatbot(id_bot):
    if not id_bot:
        return False
    with session_scope() as session:
        result = session.execute(text("SELECT token_verified FROM business_whatsapp_config WHERE id_config = :id"), {'id': id_bot}).fetchone()
        return result[0] if result else False

# Function to obtain the token of each business chatbot
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry_error_callback=lambda retry_state: False, reraise=True)
def get_token_chatbot(id_bot):
    if not id_bot:
        return False
    with session_scope() as session:
        result = session.execute(text("SELECT token FROM business_whatsapp_config WHERE id_config = :id"), {'id': id_bot}).fetchone()
        return result[0] if result else False

# Function to obtain the phone identifier of the business chatbot via the id_config/id_bot
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry_error_callback=lambda retry_state: False, reraise=True)
def get_phone_chatbot_id(id_bot):
    if not id_bot:
        return False
    with session_scope() as session:
        result = session.execute(text("SELECT identification_phone FROM business_whatsapp_config WHERE id_config = :id"), {'id': id_bot}).fetchone()
        return result[0] if result else False

# Function for validate id_bot and id number whatsapp id
# def get_phone_id_from_config(id_bot):
#     if not id_bot:
#         return False
#     with session_scope() as session:
#         result = session.execute(text("SELECT identification_phone FROM business_whatsapp_config WHERE id_config = :id"), {'id': id_bot}).fetchone()
#         return result[0] if result else False


  

#-------------------------------------- Funciones para enviar mensajes a WhatsApp ---------------------------------

# Function for Send message to user
def send_message_user(id_bot, message, recipient):
    # 1- Obtener el token de la empresa mediante el id_bot
    token = get_token_chatbot(id_bot)
    phone_send = get_phone_chatbot_id(id_bot)
    print("Token obtenido:", token)
    print("Id del teléfono:", phone_send)
    print("Mensaje a enviar:", message)
    url_chatbot = f'https://graph.facebook.com/v21.0/{phone_send}/messages'

    # 2- Enviar el mensaje al usuario
    response = send_message(token, url_chatbot, message, recipient)
   
    # 3- Mostrar en consola si el mensaje fue enviado correctamente
    if response.get("messages"):
        print(f"Mensaje enviado a {recipient}: {message}")
    else:
        print(f"Error al enviar mensaje a {recipient}: {response.get('error', 'Error desconocido')}")


# Function for send document to user
def send_document_user(id_bot, file_url, recipient, name_file):
    
    #1- Obtener token de la empresa mediante el id_bot
    token =  get_token_chatbot(id_bot)
    phone_send =  get_phone_chatbot_id(id_bot)  
    url_chatbot = f'https://graph.facebook.com/v21.0/{phone_send}/messages' 

    #2- Enviar el documento al usuario

    response = send_document(token, url_chatbot, file_url, recipient, caption=name_file, link=True, filename=name_file)

    #3- Mostrar en consola si el documento fue enviado correctamente
    if response.get("messages"):
        print(f"Documento enviado a {recipient}: {name_file}")
    else:
        print(f"Error al enviar documento a {recipient}: {response.get('error', 'Error desconocido')}")
  
 
# Funcion para enviar imagen al usuario
def send_image_user(id_bot, file_url, recipient):

    #1- Obtener token de la empresa mediante el id_bot
    token =   get_token_chatbot(id_bot)
    phone_send =  get_phone_chatbot_id(id_bot)
    url_chatbot = f'https://graph.facebook.com/v21.0/{phone_send}/messages'

    print("Token obtenido:", token)
    print("Id del teléfono:", phone_send)
    print("Url de la imagen:", file_url)  

    #2- Enviar la imagen al usuario
    response =  send_image(token, url_chatbot, file_url, recipient, caption=None, link=True)  
 
    #3- Mostrar en consola si la imagen fue enviada correctamente
    if response.get("messages"):
        print(f"Imagen enviada a {recipient}: {file_url}")
    else:
        print(f"Error al enviar imagen a {recipient}: {response.get('error', 'Error desconocido')}")


# Funcion para enviar audio al usuario
def send_audio_user(id_bot, file_url, recipient):

    #1- Obtener token de la empresa mediante el id_bot
    token =  get_token_chatbot(id_bot)
    phone_send =  get_phone_chatbot_id(id_bot)
    url_chatbot = f'https://graph.facebook.com/v21.0/{phone_send}/messages'
 
    #2- Enviar el audio al usuario
    response = send_audio(token, url_chatbot, file_url, recipient, link=True)
 
    #3- Mostrar en consola si el audio fue enviado correctamente
    if response.get("messages"):
        print(f"Audio enviado a {recipient}: {file_url}")
    else:
        print(f"Error al enviar audio a {recipient}: {response.get('error', 'Error desconocido')}")

#-------------------- Extra Functions ----------------------------
def generate_random_id_upper(length):
    """ Generate a random uppercase ID with digits of specified length. """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))


def generate_filename():
    tz = pytz.timezone('America/Santiago')
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S") 
    unique_id = generate_random_id_upper(10)
    return f"WhatsApp_Hoktus_image_{formatted_time}_{unique_id}"
 

# Función para generar nombres personalizados para audios
def generate_audio_filename():
    tz = pytz.timezone('America/Santiago')
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    unique_id = generate_random_id_upper(10)
    return f"WhatsApp_Hoktus_audio_{formatted_time}_{unique_id}" 
 
# Función para generar nombres personalizados para archivos PDF
def generate_pdf_filename(original_name):
    tz = pytz.timezone('America/Santiago')
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    unique_id = generate_random_id_upper(10)

    # Reemplazar espacios por guiones bajos
    sanitized_name = original_name.replace(" ", "_")

    # Eliminar la extensión si existe, para evitar duplicar ".pdf"
    if sanitized_name.lower().endswith('.pdf'):
        sanitized_name = sanitized_name[:-4]

    return f"{sanitized_name}_{formatted_time}_{unique_id}.pdf"


# Function for Obtein message of user in whatsapp and send to the back-end to save it
def save_user_message(id_bot, phone, message, name, type_message):

    print("Datos obtenidos para guardar mensaje soporte",id_bot, phone, message,name,type_message)
    
    #1- Validat si el id_config/id_bot existe para una empresa
    validate = validate_business_chatbot(id_bot)
    if (validate == False):
        print("No se encontró la configuración de la empresa con el ID proporcionado.",id_bot)
        return False 
         
    
    #1- Create the url to Save the message
    url = f'{BASE_URL}/api/messages/business/chat/user/save-message'
    data = { 
        'id_config': id_bot,
        'phone': phone,
        'message': message, 
        'name': name,  
        'type_message': type_message,
        'platform': 'API'
    }  
    token = os.getenv('TOKEN_CHATBOT_WHATSAPP_BUSINESS') 
    headers = {
        'Content-Type': 'application/json',
        'auth-chatbot-business': token
    } 
 
    response = requests.post(url, headers=headers, json=data)

    if(response.status_code >= 200 and response.status_code <= 204):
       print('Mensaje guardado correctamente')
    else:
         print('Error al guardar el mensaje')
         print('Mensaje de error:', response.text)
 

#1- Function for download file of user in whatsapp 
def download_media(url, mime_type, custom_filename):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        extension = mime_type.split('/')[-1]
        filename = f"{custom_filename}.{extension}"
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        return filename
    else:
        print("Error al descargar el archivo:", response.status_code)
        return None
    
def download_file_with_retries(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error al descargar el archivo (intento {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
    return None



#Function for send  for save it in the back-end
# def save_image_file(id_bot,phone, file_info, name, type_message):
#     print("Datos obtenidos para guardar imagen", id_bot,phone, file_info, name, type_message)

#     file_id = file_info['id']
#     file_url = messenger.query_media_url(file_id)
#     if not file_url:
#         print('Error: No se pudo obtener la URL de la imagen')
#         return
 
#     original_filename = file_info.get('filename', 'imagen_sin_nombre.jpeg')
#     temp_path = os.path.join(TEMP_DIR, original_filename)

#     if not os.path.exists(TEMP_DIR):
#         os.makedirs(TEMP_DIR)

#     try: 
#         response = download_file_with_retries(file_url)
#         if response:
#             with open(temp_path, 'wb') as out_file:
#                 out_file.write(response.content)
#             send_file_to_backend(id_bot,temp_path, phone, name, type_message, original_filename)
#         else:
#             print("Error: No se pudo descargar la imagen después de varios intentos.")
#     except Exception as e:
#         print(f"Error al manejar la imagen: {e}")

# Function for send documents file to save it in the back-end
# def save_document_file(id_bot,phone, file_info, name, type_message):
#     print("Datos obtenidos para guardar documento", id_bot, phone, file_info, name, type_message)
 
#     file_id = file_info['id'] 
#     file_url = messenger.query_media_url(file_id)
#     if not file_url:
#         print('Error: No se pudo obtener la URL del documento')
#         return

#     original_filename = file_info.get('filename', 'documento_sin_nombre.pdf')
#     temp_path = os.path.join(TEMP_DIR, original_filename)

#     if not os.path.exists(TEMP_DIR):
#         os.makedirs(TEMP_DIR)

#     try:
#         response = download_file_with_retries(file_url)
#         if response:
#             with open(temp_path, 'wb') as out_file:
#                 out_file.write(response.content)
#             send_file_to_backend(id_bot,temp_path, phone, name, type_message, original_filename)
#         else:
#             print("Error: No se pudo descargar el documento después de varios intentos.")
#     except Exception as e:
#         print(f"Error al manejar el documento: {e}")



# Función para convertir imágenes a JPG
# Función para convertir imágenes a JPG correctamente
def convert_image_to_jpg(original_path):
    try:
        base = os.path.splitext(os.path.basename(original_path))[0]
        new_path = os.path.join(TEMP_DIR, f"{base}.jpg")

        with Image.open(original_path) as img:
            img.convert('RGB').save(new_path, 'JPEG')

        if os.path.exists(original_path):
            os.remove(original_path)

        print(f"Imagen convertida a JPG. Tamaño del archivo convertido: {os.path.getsize(new_path)} bytes")
        return new_path
    except Exception as e:
        print(f"❌ Error al convertir imagen a JPG: {e}")
        raise

# Función para probar la descarga de archivos

# def handle_file(data, mobile, name, message_type, is_image):
#     file_info = messenger.get_image(data) if is_image else messenger.get_document(data)
#     file_id = file_info['id']  # ID del archivo
#     mime_type = file_info['mime_type']
#     original_filename = file_info.get('filename', generate_filename() + ".jpg" if is_image else "archivo_desconocido")

#     print('file_info', file_info)
#     print('file_id', file_id)
#     print('mime_type', mime_type)
#     print('original_filename', original_filename)

#     # Paso 1: Hacer la primera petición para obtener la URL del archivo
#     url_query = f"https://graph.facebook.com/v21.0/{file_id}"
#     headers = {
#         'Authorization': f'Bearer {os.getenv("TOKEN_CHATBOT_CONFIG")}'
#     }
#     try:
#         response = requests.get(url_query, headers=headers)
#         if response.status_code == 200:
#             file_data = response.json()
#             print("Primera petición exitosa. Datos obtenidos:")
#             print(file_data)
#             file_url = file_data.get('url')  # Obtener la URL del archivo

#             # Paso 2: Descargar el archivo usando la URL obtenida
#             if file_url:
#                 file_response = requests.get(file_url, headers=headers, stream=True)
#                 if file_response.status_code == 200:
#                     temp_path = os.path.join(TEMP_DIR, original_filename)
#                     with open(temp_path, 'wb') as temp_file:
#                         for chunk in file_response.iter_content(chunk_size=8192):
#                             temp_file.write(chunk)

#                     # Verificar tamaño del archivo
#                     print(f"Archivo descargado correctamente: {temp_path}")
#                     print(f"Tamaño del archivo descargado: {os.path.getsize(temp_path)} bytes")
#                 else:
#                     print(f"Error al descargar el archivo. Código de estado: {file_response.status_code}")
#             else:
#                 print("No se pudo obtener la URL del archivo en la primera petición.")
#         else:
#             print(f"Error al obtener datos del archivo. Código de estado: {response.status_code}")
#             print(response.json())
#     except requests.exceptions.RequestException as e:
#         print(f"Error durante las peticiones al API de WhatsApp: {e}")
 

# Función para descargar y manejar documentos e imágenes
def handle_file(id_bot, data, mobile, name, message_type, is_image):
    print("Datos obtenidos para manejar archivo:", id_bot, data, mobile, name, message_type, is_image)

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
        print(f"📁 Carpeta temporal creada: {TEMP_DIR}")

    file_info = get_image(data) if is_image else (
        get_document(data) if message_type == "document" else get_audio(data)
    )
    file_id = file_info['id']
    mime_type = file_info['mime_type']

    image_mime_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp']
    if message_type == "document" and mime_type in image_mime_types:
        is_image = True
        message_type = "image"
        print("📸 Documento con mimetype de imagen detectado. Tratando como imagen.")
        original_filename = generate_filename() + ".jpg"
    else:
        if message_type == "audio":
            original_filename = generate_audio_filename()
        elif is_image:
            original_filename = generate_filename() + ".jpg"
        else:
            original_name = file_info.get('filename', "archivo_desconocido.pdf")
            original_filename = generate_pdf_filename(original_name)

    token = get_token_chatbot(id_bot)
    print("Token obtenido handle_file:", token)
    url_query = f"https://graph.facebook.com/v21.0/{file_id}"
    headers = {'Authorization': f'Bearer {token}'}

    try:
        response = requests.get(url_query, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            print("Primera petición exitosa. Datos obtenidos:")
            print(file_data)
            file_url = file_data.get('url')

            if file_url:
                file_response = requests.get(file_url, headers=headers, stream=True)
                if file_response.status_code == 200:
                    temp_path = os.path.join(TEMP_DIR, original_filename)
                    with open(temp_path, 'wb') as temp_file:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            temp_file.write(chunk)

                    # 🔄 Convertimos y actualizamos la ruta real del archivo
                    if is_image and mime_type.split('/')[1] != 'jpeg':
                        temp_path = convert_image_to_jpg(temp_path)

                    # ⚠️ Este es el nombre real final
                    final_filename = os.path.basename(temp_path)

                    send_file_to_backend(
                        id_bot,
                        temp_path,
                        mobile,
                        name,
                        message_type,
                        final_filename,
                        "image/jpeg" if is_image else mime_type
                    )
                else:
                    print(f"Error al descargar el archivo. Código: {file_response.status_code}")
            else:
                print("❌ No se obtuvo la URL del archivo.")
        else:
            print(f"❌ Error al obtener datos del archivo. Código: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición al API de WhatsApp: {e}")

# Función para enviar archivos al backend
def send_file_to_backend(id_bot, temp_path, phone, name, type_message, original_filename, mime_type):
    url = f'{BASE_URL}/api/messages/business/chat/user/save-file'
    with open(temp_path, 'rb') as file:
        file_content = file.read() 
         
        # Verificar tamaño antes de enviar
        print(f"Tamaño del archivo a enviar al backend: {len(file_content)} bytes")
        
        files = {'files': (original_filename, file_content, mime_type)}
        data = {
            'id_config': id_bot, 
            'phone': phone,
            'name': name,
            'type_message': type_message,
            'file_name': original_filename,
            'file_type': mime_type,
            'platform': 'API'
        }
        token = os.getenv('TOKEN_CHATBOT_WHATSAPP_BUSINESS')
        headers = {
            'auth-chatbot-business': token
        }
 
        try:
            response = requests.post(url, files=files, headers=headers, data=data)
            print(f"Response status code: {response.status_code}")
            if 200 <= response.status_code <= 204:
                print("El archivo se ha enviado correctamente.")
                os.remove(temp_path)
                print(f"Archivo {original_filename} eliminado correctamente.")
            else:
                print("Error al enviar el archivo:", response.json())
        except requests.exceptions.RequestException as e:
            print("Error de conexión:", e)
  


#1- Transformar el formulario en un formato JSON
def get_form_data(data):
    response_json = data.get('nfm_reply', {}).get('response_json')
    if response_json:
        form_data = json.loads(response_json)
        return form_data
    return {}


# Función para registrar la cuenta del usuario a través del formulario de WhatsApp
def registerAccountUser(id_bot,phone, data):
    try:
        # Imprimir datos recibidos para diagnóstico
        print("Datos obtenidos para guardar la creación de cuenta de usuario:", id_bot,phone, data)

        # Crear la URL y obtener el token del entorno
        url = f'{BASE_URL}/api/messages/business/chat/user/create-account'
        token = os.getenv('TOKEN_CHATBOT_WHATSAPP_BUSINESS')
      
        # Encabezados para la solicitud HTTP
        headers = {
            'Content-Type': 'application/json',
            'auth-chatbot-business': token
        }

        # Preparar datos a enviar
        payload = {
            "phone": phone,
            "data": data
        }

        # # Enviar la solicitud POST al backend
        # response = requests.post(url, headers=headers, json=payload)

        # if response.status_code >= 200 and response.status_code <= 204:
        #     # Mensaje de éxito
        #     newMessage = (
        #         "¡Cuenta creada con éxito! 🎉 "
        #         "Gracias por confiar en Fletzy. En unos minutos recibirás un correo electrónico "
        #         "con tus credenciales para iniciar sesión en https://fletzy.com/login. "
        #         "Completa tu perfil para continuar con el proceso. 😊"
        #     )

        #     # URL para enviar el mensaje al usuario
        #     url_message = f'{BASE_URL_CHATBOT}/whatsapp/send_message'

        #     message_payload = {
        #         "recipient": phone,
        #         "message": newMessage
        #     }

        #     # Enviar mensaje de agradecimiento al usuario
        #     message_response = requests.post(url_message, json=message_payload)

        #     if message_response.status_code >= 200 and message_response.status_code <= 204:
        #         print("Mensaje de agradecimiento enviado correctamente.")
        #     else:
        #         print("Error al enviar el mensaje de agradecimiento.")
        # else:
        #     print(f"Error en la creación de cuenta: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error en la función registerAccountUser: {str(e)}")
    
    

#-------------------------------------- Function of Flows/Forms Sendings ---------------------------------#
# Function to verify which type of form and send the data correctly
def send_forms_to_save(id_bot, phone, form_data, form_name):
    try:
        # ✅ Imprimir los datos para verificar que se reciben correctamente
        print("📩 [send_forms_to_save] Recibiendo datos...")
        print(f"🆔 ID del bot: {id_bot}")
        print(f"📲 Número de usuario: {phone}")
        print(f"📝 Nombre del formulario: {form_name}")
        print(f"🔍 Datos del formulario:")
        print(json.dumps(form_data, indent=4))  # Formatear JSON para que sea legible

        # ✅ Usamos un switch para manejar distintos formularios
        match form_name:
            case "form_cierre_op_bs":
                save_user_daily_production(phone, form_data, id_bot)
            
            case "form_otro_proceso":
                print("⚠ Formulario 'form_otro_proceso' no implementado.")
            
            case _:
                print(f"⚠ Formulario '{form_name}' no reconocido. No se procesará.")
    
    except Exception as e:
        print(f"❌ Error en send_forms_to_save: {str(e)}")






#2- Guardar la produccion diaria del usuario y mostrarla por consola
def save_user_daily_production(phone, data, id_bot):
    print("Datos obtenidos para guardar producción diaria", phone, data)
    
    

    #1- Create the url to Save the daily production and obtain token to send
    # url = f'{BASE_URL}/administrator/operations/chat/whatsapp/user/save-user-daily-production/{phone}'
    url = f'{BASE_URL}/api/messages/operations/chat/whatsapp/user/save-user-daily-production/{phone}'
    token = os.getenv('TOKEN_CHATBOT_WHATSAPP_OPERATION')
    
    #2- Send datas to back-end to save it
    headers = {
        'Content-Type': 'application/json',
        'auth-chatbot': token
    }
    response = requests.post(url, headers=headers, json=data)
    
    

    if(response.status_code >= 200 and response.status_code <= 204):
        newMessage = '¡Gracias por completar la producción diaria!'
        url = f'{BASE_URL_CHATBOT}/whatsapp/send_message'
        data = {
           'id_config': id_bot,
           'recipient': phone,
           'message': newMessage
        }
        response = requests.post(url, json=data)
        if response.status_code >= 200 and response.status_code <= 204:
           print('Mensaje de finalizacion de produccion enviado correctamente')
        else:
           print('Error al enviar el mensaje de agradecimiento')
    
    
#--------------------------------------- Templates ---------------------------------------------#

# 🔹 Función para codificar la URL en Base64 (seguro para WhatsApp)
def encode_url_for_whatsapp(original_url):
    return base64.urlsafe_b64encode(original_url.encode()).decode()


# Function for send message of template to user
def send_template_message_user(id_bot, phone, template_name, template_parameters, template_type, template_parameters_buttons, url_image=None,):
    print("Datos obtenidos template en service", id_bot, phone, template_name, template_parameters, template_type, url_image,template_parameters_buttons)

    # 1- Obtener el identificador del teléfono del chatbot de la empresa
    identification_phone_chatbot = get_phone_chatbot_id(id_bot)
    print("Identificación del teléfono del chatbot:", identification_phone_chatbot)

    url = f'https://graph.facebook.com/v21.0/{identification_phone_chatbot}/messages'
    tokenChatbot = get_token_chatbot(id_bot)

    print("Token obtenido:", tokenChatbot)

    headers = { 
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {tokenChatbot}'
    }

    components = []

    # 🔹 1️⃣ Si hay una imagen, agregarla al header
    if url_image:
        components.append({
            'type': 'header',
            'parameters': [{
                'type': 'image',
                'image': {'link': url_image}
            }]
        })

    # 🔹 2️⃣ Agregar parámetros del cuerpo de la plantilla solo si existen
    if template_parameters:
        components.append({
            'type': 'body',
            'parameters': template_parameters
        })

    # 🔹 3️⃣ Si el tipo de plantilla es "form", agregar botón de flujo
    if template_type == 'form':
        components.append({
            'type': 'button',
            'sub_type': 'FLOW',
            'index': 0,
            'parameters': [
                {
                    'type': 'text',
                    'text': 'Completar producción'
                }
            ]
        })

    # 🔹 4️⃣ Si hay parámetros para botones tipo URL, codificarlos y agregarlos
    if template_parameters_buttons:
        for index, button in enumerate(template_parameters_buttons):
            if "url" in button:
                components.append({
                    'type': 'button',
                    'sub_type': 'URL',
                    'index': index,  
                    'parameters': [
                        {
                            'type': 'text',
                            'text': button["url"]  
                        }
                    ]
                })

    # 🔹 4️⃣ Construcción final del mensaje
    data = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual', 
        'to': phone,
        'type': 'template',
        'template': {
            'name': template_name,
            'language': {'code': 'es'}
        }
    }

    # 🔹 5️⃣ Solo agregar `components` si hay algo que enviar
    if components:
        data['template']['components'] = components

    # 🔹 6️⃣ Enviar la solicitud
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 🔹 7️⃣ Manejo de la respuesta de WhatsApp
    if response.status_code == 200:
        print('✅ Mensaje de plantilla enviado correctamente')
        return response.status_code
    else:
        print('❌ Error al enviar el mensaje de plantilla') 
        print('📌 Mensaje de error:', response.text)
        return response.status_code