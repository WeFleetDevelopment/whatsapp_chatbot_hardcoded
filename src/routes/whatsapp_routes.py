#---------------------- Logica para las peticiones de la API DE WHATSAPP BUSINESS ----------------------
from flask import Blueprint,request,jsonify
import json
import os
import requests
import pytz
#Config of the api of whatsapp    
# from src.config.config_Whatsapp import messenger,logging
import re
# Image
from PIL import Image
from io import BytesIO


#Services of WhtasApp
from src.services.whatsapp_services import ( 
    save_user_message,handle_file,get_form_data,save_user_daily_production,validate_business_chatbot,get_name,
    get_message,get_mobile,get_message_type,changed_field,is_message,get_delivery,get_interactive_response,send_message_user,send_document_user,
    send_image_user,send_audio_user,send_template_message_user,get_interactive_response_flow,send_lists_files_user,send_forms_to_save,get_phone_chatbot_id
)

# Middlewares
from src.middlewares.middlewares import (
    require_auth_chatbot
)

#Messages of the bot for send
# from src.utils.messages import msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8, msg9, msg10, msgcomunaerror, msg11, msg12, msg13, msg14, msg15, msg16, msg17, msg18, msgpresencial, msgpresencialconfirmacion_no, msgpresencialconfirmacion_si, msg19, msg20, msg21, msg22, msg23, msg24, msg25, msg26, msg27, msg28, msg29, certificadopeoneta, msg30, msg31, msg32, msg33, msg34, msg35, msg36, msg37, msg38, msg39, msg40, msg41, msg42, msg43, msg44, msg45, documento_corregido,
from src.utils.messages import message1, message2, message3, message4, message5, urlWeFleet ,message_error1, message_error2
#Utils
from src.utils.utils import button_reply,comuna_en_lista

whatsapp_routes = Blueprint('webhook_whatsapp', __name__)

# Types of files
file_types = {
    "document": False,
    "image": True,
    "audio": False
}



# Ruta para recibir mensajes / 
@whatsapp_routes.route("/whatsapp/webhook", methods=["POST", "GET"])
def webhook_whatsapp():
    # Imprime todo el cuerpo de la solicitud
    # print("Raw request data:", request.data)
    # print("JSON request data:", json.dumps(request.get_json(), indent=4))

    # 📌 IMPRIMIR TODO EL CUERPO DE LA SOLICITUD PARA DEPURACIÓN
    # print("🔍 RAW JSON RECIBIDO EN WEBHOOK:")
    # print(json.dumps(request.get_json(), indent=4))  # Formatea el JSON para que sea legible

    
    #1- Verificar el id de la configuracion de la empresa, que exista en la url
    id_bot = request.args.get('id_bot', None)
    if not id_bot:
        return "Missing configuration ID", 400
    
    # Validar que el id_bot no sea None y cumpla con el formato permitido
    # if not id_bot or not re.fullmatch(r'^[A-Z0-9]+$', id_bot):
    #     return jsonify({"error": "Invalid configuration ID"}), 400
    
    #2- Validamos que la empresa exista
    token_verified = validate_business_chatbot(id_bot)
    if not token_verified:
        return "Invalid configuration ID", 400
    
    
    #3-  Verificar el token de verificación - 
    if request.method == "GET":
       verify_token = token_verified
       print("Token de verificación:", verify_token)

       if request.args.get("hub.verify_token") == verify_token:
           challenge = request.args.get("hub.challenge")
           if challenge:
               return challenge, 200, {"Content-Type": "text/plain"} 
           else:
               return "Missing challenge parameter", 400
       else:
           return "Invalid verification token", 403
       


    
    # Handle Webhook Subscriptions
    data = request.get_json()
    # Extraer el ID del número receptor (del chatbot)
    phone_number_id = data['entry'][0]['changes'][0]['value']['metadata']['phone_number_id']
    print(f"🔍 ID del número receptor (phone_number_id): {phone_number_id}")
   
    # ✅ Validar que el número del mensaje corresponde con el id_config usado
    phone_number_expected = get_phone_chatbot_id(id_bot)
    if phone_number_id != phone_number_expected:
       print(f"❌ ID del número recibido ({phone_number_id}) no corresponde con el ID esperado para este bot ({phone_number_expected}). Ignorando mensaje.")
       return "Ignored valid", 200

    if changed_field(data) == "messages":
        if is_message(data):
            mobile = get_mobile(data)
            name = get_name(data)
            message_type = get_message_type(data)
            message = get_message(data)
            print(f"New Message; sender:{mobile} name:{name} type:{message_type}, message:{message}")
              
            debug_message = "TJN2SVVG" 
            if message_type == "text":     
                debug_message = get_message(data) 
            
            #1-  Capturar  mensajes de Texto    
            if message_type == "text":
                message_received =  get_message(data)  
                print("Mensaje recibido", message_received) 
                if message_received:  # Verificar si el mensaje recibido no está vacío
                    save_user_message(id_bot, mobile, message_received, name,message_type)  # Pasar el nombre del usuario
             
            #2-  Capturar mensajes, como Botones  
            if message_type == "button":
                # Capturar el texto del botón cuando se presiona y pasarlo como mensaje a "save_user_message"
                message_received = button_reply(data)
                print("Mensaje Obtenido", message_received)
                if message_received:  # Verificar si el mensaje recibido no está vacío
                    save_user_message(id_bot,mobile, message_received, name, message_type)  # Pasar el nombre del usuario

            # Capturar mensajes con Formularios interactivos
            if message_type == "interactive":
                try:
                    # ✅ Obtener los datos correctamente
                    message_received = get_interactive_response(data)

                    if message_received:  # Verificar si el mensaje recibido no está vacío
                       form_data = get_form_data(message_received)

                       # 🔹 Extraer `response_json` y convertirlo a diccionario
                       response_json_str = message_received["nfm_reply"]["response_json"]  # Extraer JSON en string
                       form_data_dict = json.loads(response_json_str)  # Convertimos a JSON
                       form_name = form_data_dict.get("form_name", "UNKNOWN_FORM_NAME")  # Extraer nombre del formulario

                       # ✅ Imprimir los datos extraídos en consola para depuración
                       print(f"📝 Nombre del formulario recibido: {form_name}")
                       print(f"📲 Número de usuario: {mobile}")
                       print(f"🆔 ID del bot: {id_bot}")
                       print(f"🔍 Datos del formulario:")
                       print(json.dumps(form_data_dict, indent=4))

                       # ✅ Enviar los datos a `send_forms_to_save`
                       send_forms_to_save(id_bot, mobile, form_data_dict, form_name)

                except Exception as e:
                    print(f"❌ Error al procesar el formulario interactivo: {e}")

            
            
            #3-  Capturar mensajes con Stickers
            if message_type == "sticker":
                if message_received:
                    save_user_message(id_bot,mobile, message_received, name,message_type)
            

            # Capturar y enviar documentos
            if message_type in file_types:
                handle_file(id_bot, data, mobile, name, message_type, is_image=file_types[message_type])
         
            delivery = get_delivery(data)
            if delivery:
                print(f"Message : {delivery}")
            else:
                print("No new message")
    return "OK", 200



# # Ruta para recibir mensajes / 
# @whatsapp_routes.route("/whatsapp/webhook", methods=["POST", "GET"])
# def webhook_whatsapp():
     
#     #1- Verificar el id de la configuracion de la empresa, que exista en la url
#     id_bot = request.args.get('id_bot', None)
#     if not id_bot:
#         return "Missing configuration ID", 400
    
#     #2- Validamos que la empresa exista
#     token_verified = validate_business_chatbot(id_bot)
#     if not token_verified:
#         return "Invalid configuration ID", 400
    
#     #3-  Verificar el token de verificación
#     if request.method == "GET":
#         verify_token = token_verified
#         print("Token de verificacion", verify_token)
       
#         if request.args.get('hub.verify_token') == verify_token: 
#             return request.args.get('hub.challenge')
#         else:
#             return "Invalid verification token"

#     # Handle Webhook Subscriptions
#     data = request.get_json()
#     changed_field = messenger.changed_field(data)
#     print("Mensaje Recibido")
#     if changed_field == "messages":
#         new_message = messenger.is_message(data)
#         if new_message:  
#             mobile = messenger.get_mobile(data) 
#             name = messenger.get_name(data)  # Capturar el nombre del usuario
#             message_type = messenger.get_message_type(data) # Capturar el tipo de mensaje
             
#             debug_message = "TJN2SVVG"
#             if message_type == "text":
#                 debug_message = messenger.get_message(data)
#             logging.info( 
#                 f"New Message; sender:{mobile} name:{name} type:{message_type}"
#             )
#             print("Tipo de mensaje", message_type)
             
#             #1-  Capturar mensajes de Texto  
#             if message_type == "text":
#                 message_received = messenger.get_message(data)
#                 print("Mensaje recibido", message_received)
#                 if message_received:  # Verificar si el mensaje recibido no está vacío
#                     save_user_message(id_bot, mobile, message_received, name,message_type)  # Pasar el nombre del usuario
             
#             #2-  Capturar mensajes, como Botones 
#             if message_type == "button":
#                 # Capturar el texto del botón cuando se presiona y pasarlo como mensaje a "save_user_message"
#                 message_received = button_reply(data)
#                 print("Mensaje Obtenido", message_received)
#                 if message_received:  # Verificar si el mensaje recibido no está vacío
#                     save_user_message(id_bot,mobile, message_received, name, message_type)  # Pasar el nombre del usuario

#             # Capturar mensajes con Formularios interactivos
#             if message_type == "interactive":
#                 # Capturar el texto del formulario y pasarlo como mensaje a "save_user_message"
#                 message_received = messenger.get_interactive_response(data)
#                 print("Mensaje Obtenido",message_received)
#                 if message_received:  # Verificar si el mensaje recibido no está vacío
#                     form_data = get_form_data(message_received)
#                     registerAccountUser(mobile, form_data)  

             

#             #3-  Capturar mensajes con Stickers
#             if message_type == "sticker":
#                 if message_received:
#                     save_user_message(id_bot,mobile, message_received, name,message_type)
                     
#             # Capturar y enviar documentos
#             elif message_type == "document":
#                 handle_file(data, mobile, name, message_type, is_image=False)

#             # Capturar y enviar imágenes
#             elif message_type == "image":
#                 handle_file(data, mobile, name, message_type, is_image=True)

#             # Capturar y enviar audios
#             elif message_type == "audio":
#                 handle_file(data, mobile, name, message_type, is_image=False)
         
#             delivery = messenger.get_delivery(data)
#             if delivery:
#                 logging.info(f"Message : {delivery}")
#             else:
#                 logging.info("No new message")
#     return "OK", 200




# Ruta para enviar mensajes Personalizados o Default dentro del protocolo de 24 Horas 
@whatsapp_routes.route("/whatsapp/send_message", methods=["POST"])
def send_message():
    data = request.json
    if "recipient" not in data or "message" not in data:
        return jsonify({"error": "El JSON debe contener 'recipient' y 'message'"}), 400
    id_bot = data["id_config"]
    recipient = data["recipient"]
    message = data["message"] 
    try:   
        print("Datos del mensaje recibido en endpoint send message", id_bot,recipient, message) 
          
        #Obtener datos del chatbot a enviar mensaje
        send_message_user(id_bot,message, recipient)
        print("Mensaje enviado de Fletzy al usuario",id_bot, recipient, message)
        return jsonify({"success": True, "message": f"Mensaje enviado correctamente al numero {recipient}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500 
  

# Ruta para enviar archivos personalizados o Default dentro del protocolo de 24 Horas
@whatsapp_routes.route('/whatsapp/send_file/<type>', methods=["POST"])
def send_file(type):
    data = request.json   
    if "recipient" not in data or "file_url" not in data:
        return jsonify({"error": "El JSON debe contener 'recipient' y 'file_url'"}), 400
    
    id_bot = data["id_config"]
    recipient = data["recipient"] 
    file_url = data["file_url"]
    name_file = data["name_file"] 
    print("Datos del archivo recibido", recipient, file_url, name_file, type)
    
    try:
        if type == "document":
            print("data document", data) 
            send_document_user(id_bot,file_url, recipient, name_file)
        elif type == "image":    
            print("data image", data) 
            send_image_user(id_bot, file_url, recipient)
  
        elif type == "audio": 
            print("data audio", data) 
            send_audio_user(id_bot, file_url, recipient)
                  
        else:
            return jsonify({"error": "Tipo de archivo no soportado"}), 400
        
        return jsonify({"success": True, "message": f"Archivo enviado correctamente al numero {recipient}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#Ruta para enviar un mensaje interactivo de listas con Archivos PDF O imagenes
@whatsapp_routes.route('/whatsapp/send_list_message', methods=["POST"])
@require_auth_chatbot
def send_list_message():
    data = request.json
    print("📥 Datos del mensaje interactivo recibido:", json.dumps(data, indent=4))

    required_keys = ['id_config', 'phone', 'message', 'lists']
    if not all(k in data for k in required_keys):
        return jsonify({"error": "Faltan campos requeridos: 'id_config', 'phone', 'message', 'lists'"}), 400

    id_config = data["id_config"]
    phone = data["phone"]
    title = data["title"]
    message = data["message"]
    lists = data["lists"]


    try:
        success = send_lists_files_user(id_config, phone,title, message, lists)
        if success:
            return jsonify({"status": "ok"}), 200
        else:
            return jsonify({"error": "No se pudo enviar el mensaje"}), 500
    except Exception as e:
        print("❌ Error en send_list_message:", str(e))
        return jsonify({"error": str(e)}), 500

#------------------------- Rutas para la comunicacion del servidor que guardara y enviara los mensajes --------------- #

# Ruta para obtener el usuario y la plantilla de mensaje para enviarle el mensaje de plantilla al usuario
@whatsapp_routes.route("/whatsapp/send_template_message", methods=["POST"])
def route_send_template_message():
    data = request.json
    print("Datos de la solicitud template en route:", json.dumps(data, indent=4))

    # Asegurarte de que 'data', 'userData' y 'messageData' estén en el cuerpo de la solicitud
    if "data" not in data or "userData" not in data["data"] or "messageData" not in data["data"]:
        return jsonify({"error": "El JSON debe contener 'data' con 'userData' y 'messageData'"}), 400

    # Acceder a userData y messageData a través del objeto 'data'
    userData = data["data"]["userData"]
    messageData = data["data"]["messageData"]

    print("Datos del usuario userData", userData)
    print("Datos del mensaje messageData", messageData)

    id_config = userData['id_config']  
    recipient = userData['phone']      
    template_name = messageData['template_name'] 
    template_parameters = messageData['template_parameters']  
    template_type = messageData['template_type']  
    template_parameters_buttons = messageData.get('template_parameters_buttons', [])

    # 🔹 1️⃣ Verificar si la plantilla es "marketing_2" para agregar la imagen de prueba
    url_image = None
    if template_name == "marketing_2":
        url_image = "https://firebasestorage.googleapis.com/v0/b/fletzy-page-prod.appspot.com/o/Fletzy-imgs%2FLogo%20Instagram%20Hoktus%20(1).png?alt=media&token=cb9f6c15-93e7-4934-8e7e-3897dd80659b"
        print(f"📸 Agregando imagen de prueba para la plantilla {template_name}")

 
    try:
        
        response = send_template_message_user(
            id_config,
            recipient,
            template_name,
            template_parameters,
            template_type,
            template_parameters_buttons,
            url_image
        )
        return jsonify({"success": True, "response": response}), 200
    except Exception as e:
        print("Error en send_template_message:", str(e))
        return jsonify({"error": str(e)}), 500

# @whatsapp_routes.route("/whatsapp/send_template_message", methods=["POST"])
# def route_send_template_message():
#     data = request.json
#     if "phone" not in data or "template_name" not in data:
#         return jsonify({"error": "El JSON debe contener 'phone' y 'template_name'"}), 400
     
#     id_bot = data["id_config"]
#     phone = data["phone"]
#     template_name = data["template_name"]
#     template_parameters = data.get("template_parameters", [])
#     template_type = data.get("template_type", None)
    
#     try:
#         response = send_template_message(id_bot,phone, template_name, template_parameters, template_type)
#         return jsonify({"success": True, "response": response}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# Ruta para obtener el usuario y la plantilla de mensaje para enviarle el mensaje de plantilla al usuario
# @whatsapp_routes.route("/whatsapp/send_template_message/prueba", methods=["GET"])
# def route_send_template_message():
#     phone = request.args.get("phone")
#     template_name = request.args.get("template_name")
#     template_type = request.args.get("template_type")

#     if not phone or not template_name or not template_type:
#         return jsonify({"error": "La URL debe contener 'phone', 'template_name' y 'template_type'"}), 400

#     # Establecer template_parameters con un valor por defecto
#     template_parameters = [
#         {
#             "type": "text",
#             "text": "Nombre prueba",
#         },
#     ]

#     try:
#         response = send_template_message(phone, template_name, template_parameters, template_type)
#         return jsonify({"success": True, "response": response}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# Ruta prueba en consola
# @whatsapp_routes.route("/whatsapp/prueba", methods=["GET"])
# def route_prueba():
#     return jsonify({"success": True, "response": "Prueba exitosa"}), 200
