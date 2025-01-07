import requests
import os
import json
import time

# Time Chile - Santiago
from datetime import datetime
import pytz
 
# Image
from PIL import Image
from io import BytesIO

#Database of MySql
from flask import current_app 
from sqlalchemy import text
from src.database.mysql.mysql_config import db

# #Config of the api of whatsapp    
# from src.config.config_Whatsapp impor t messenger,logging
 
# Carpeta Temp
TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')

# Define la URL base como una variable global
#Original
BASE_URL = 'https://hoktus-api-messages-test-production.up.railway.app'
BASE_URL_CHATBOT= 'https://business-whatsapp-chatbot-test-production.up.railway.app'
#Prueba 1
# BASE_URL = 'https://wefleetdeveloperbackendtest.alwaysdata.net'
#Prueba 2
# BASE_URL = 'https://c679-2803-c600-5117-8006-95f3-f3b0-484d-30d.ngrok-free.app'

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
    return response.json()

# Function for send message of template to user
def send_template_message(id_bot, phone, template_name, template_parameters, template_type):
    print("Datos obtenidos", id_bot, phone, template_name, template_parameters, template_type)

    if(id_bot == None or id_bot == ''):
        return False

    #1- Obtener el identificador del telefono del chatbot de la empresa
    identification_phone_chatbot = get_phone_chatbot_id(id_bot)
     
    url = f'https://graph.facebook.com/v21.0/{identification_phone_chatbot}/messages'
    tokenChatbot = get_token_chatbot(id_bot)
       
    headers = { 
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {tokenChatbot}'
    }

    components = []

    # Agregar parámetros de la plantilla solo si no están vacíos
    if template_parameters:
        components.append({
            'type': 'body',
            'parameters': template_parameters
        })

    # Si el tipo de plantilla es "form", agregar un componente de botón de flujo
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

    data = {
        'messaging_product': 'whatsapp',
        'recipient_type': 'individual', 
        'to': phone,
        'type': 'template',
        'template': {
            'name': template_name,
            'language': {
                'code': 'es'  # Asume que el idioma es español de España, ajusta según sea necesario
            },
            'components': components if components else None  # Solo agregar componentes si no están vacíos
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print('Mensaje de plantilla enviado correctamente')
        return response.status_code
    else:
        print('Error al enviar el mensaje de plantilla') 
        print('Mensaje de error:', response.text)  # Imprime el mensaje de error
        return response.status_code 

#-------------------------------------- Validations WhatsApp Chatbot y obtencion de datos importantes ---------------------------------

# Function for validate the business chatbot and return token verified of aplication of business
def validate_business_chatbot(id_bot):
    if not id_bot:
        return False

    try:
        result = db.session.execute(
            text("SELECT token_verified FROM business_whatsapp_config WHERE id_config = :id"),
            {'id': id_bot}
        ).fetchone() 
        db.session.commit()
        
        if result:
            token_verified = result[0]  # Access the first element of the tuple
            print("Token verificado desde la base de datos:", token_verified)
            return token_verified
        else:
            print("No se encontró la configuración de la empresa con el ID proporcionado.")
            return False
    except Exception as e: 
        db.session.rollback()
        print("Error accessing database:", e)
        return False

# Function to obtain the token of each business chatbot
def get_token_chatbot(id_bot):
    if not id_bot:
        return False

    try: 
        result = db.session.execute(
            text("SELECT token FROM business_whatsapp_config WHERE id_config = :id"),
            {'id': id_bot}
        ).fetchone()
        db.session.commit()

        if result: 
            token = result[0]  # Access the first element of the tuple
            print('Token jwt Perma: ', token)
            return token
        else:
            print("No se encontró la configuración de la empresa con el ID proporcionado.")
            return False
    except Exception as e:
        db.session.rollback()
        print("Error accessing database:", e)
        return False

# Function to obtain the phone identifier of the business chatbot via the id_config/id_bot
def get_phone_chatbot_id(id_bot):
    if not id_bot:
        return False

    try: 
        result = db.session.execute(
            text("SELECT identification_phone FROM business_whatsapp_config WHERE id_config = :id"),
            {'id': id_bot}
        ).fetchone()
        db.session.commit()

        if result: 
            phone = result[0]  # Access the first element of the tuple
            print('Id del teléfono: ', phone)
            return phone
        else:
            print("No se encontró la configuración de la empresa con el ID proporcionado.")
            return False
    except Exception as e:
        db.session.rollback()
        print("Error accessing database:", e)
        return False

 

 

  

#-------------------- Extra Functions ----------------------------
def generate_filename():
    tz = pytz.timezone('America/Santiago')
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M")
    return f"WhatsApp_Fletzy_{formatted_time}"


# Función para generar nombres personalizados para audios
def generate_audio_filename():
    tz = pytz.timezone('America/Santiago')
    current_time = datetime.now(tz)
    formatted_time = current_time.strftime("%Y-%m-%d_%H:%M:%S")
    return f"WhatsApp_Fletzy_audio_{formatted_time}"



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
        'type_message': type_message
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
def convert_image_to_jpg(temp_path, original_filename):
    with Image.open(temp_path) as img:
        temp_path_jpg = os.path.join(TEMP_DIR, f"{os.path.splitext(original_filename)[0]}.jpg")
        img.convert('RGB').save(temp_path_jpg, 'JPEG')
    os.remove(temp_path)
    print(f"Imagen convertida a JPG. Tamaño del archivo convertido: {os.path.getsize(temp_path_jpg)} bytes")
    return temp_path_jpg

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
     
    #Obtener información del archivo  
    file_info = get_image(data) if is_image else (
        get_document(data) if message_type == "document" else get_audio(data)
    ) 
    file_id = file_info['id']  # ID del archivo 
    mime_type = file_info['mime_type'] 

    # Generar nombres personalizados para los archivos
    if message_type == "audio":
        original_filename = generate_audio_filename()
    elif is_image:
        original_filename = generate_filename() + ".jpg"
    else:
        original_filename = file_info.get('filename', "archivo_desconocido.pdf")
    
    # print('file_info', file_info)
    # print('file_id', file_id)
    # print('mime_type', mime_type)
    # print('original_filename', original_filename)

    # Paso 1: Hacer la primera petición para obtener la URL del archivo
    token = get_token_chatbot(id_bot)
    url_query = f"https://graph.facebook.com/v21.0/{file_id}"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    try: 
        response = requests.get(url_query, headers=headers)
        if response.status_code == 200:
            file_data = response.json()
            print("Primera petición exitosa. Datos obtenidos:")
            print(file_data)
            file_url = file_data.get('url')  # Obtener la URL del archivo

            # Paso 2: Descargar el archivo usando la URL obtenida
            if file_url: 
                file_response = requests.get(file_url, headers=headers, stream=True)
                if file_response.status_code == 200: 
                    temp_path = os.path.join(TEMP_DIR, original_filename)
                    with open(temp_path, 'wb') as temp_file:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            temp_file.write(chunk)
                  
                    # # Verificar tamaño del archivo
                    # print(f"Archivo descargado correctamente: {temp_path}")
                    # print(f"Tamaño del archivo descargado: {os.path.getsize(temp_path)} bytes")

                    # Convertir a JPG si es una imagen y no está ya en formato JPEG
                    if is_image and mime_type.split('/')[1] != 'jpeg':
                        temp_path = convert_image_to_jpg(temp_path, original_filename)
  
                    # Enviar el archivo al backend 
                    send_file_to_backend(
                        id_bot,
                        temp_path, 
                        mobile, 
                        name,  
                        message_type, 
                        original_filename, 
                        "image/jpeg" if is_image else mime_type
                    )
                else:
                    print(f"Error al descargar el archivo. Código de estado: {file_response.status_code}")
            else:
                print("No se pudo obtener la URL del archivo en la primera petición.")
        else:
            print(f"Error al obtener datos del archivo. Código de estado: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error durante las peticiones al API de WhatsApp: {e}")

      

# Función para enviar archivos al backend
def send_file_to_backend(id_bot, temp_path, phone, name, type_message, original_filename, mime_type):
    url = f'{BASE_URL}/api/messages/business/chat/user/save-file'
    with open(temp_path, 'rb') as file:
        file_content = file.read() 
         
        # Verificar tamaño antes de enviar
        print(f"Tamaño del archivo a enviar al backend: {len(file_content)} bytes")
        
        files = {'files': (original_filename, file_content, mime_type)}
        data = {
            'id_bot': id_bot, 
            'phone': phone,
            'name': name,
            'type_message': type_message,
            'file_name': original_filename,
            'file_type': mime_type
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

        # Enviar la solicitud POST al backend
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code >= 200 and response.status_code <= 204:
            # Mensaje de éxito
            newMessage = (
                "¡Cuenta creada con éxito! 🎉 "
                "Gracias por confiar en Fletzy. En unos minutos recibirás un correo electrónico "
                "con tus credenciales para iniciar sesión en https://fletzy.com/login. "
                "Completa tu perfil para continuar con el proceso. 😊"
            )

            # URL para enviar el mensaje al usuario
            url_message = f'{BASE_URL_CHATBOT}/whatsapp/send_message'

            message_payload = {
                "recipient": phone,
                "message": newMessage
            }

            # Enviar mensaje de agradecimiento al usuario
            message_response = requests.post(url_message, json=message_payload)

            if message_response.status_code >= 200 and message_response.status_code <= 204:
                print("Mensaje de agradecimiento enviado correctamente.")
            else:
                print("Error al enviar el mensaje de agradecimiento.")
        else:
            print(f"Error en la creación de cuenta: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error en la función registerAccountUser: {str(e)}")
    
    




#------ Nuevas funciones -------------