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
    send_image_user,send_audio_user,send_template_message_user,get_interactive_response_flow
)
#Messages of the bot for send
# from src.utils.messages import msg1, msg2, msg3, msg4, msg5, msg6, msg7, msg8, msg9, msg10, msgcomunaerror, msg11, msg12, msg13, msg14, msg15, msg16, msg17, msg18, msgpresencial, msgpresencialconfirmacion_no, msgpresencialconfirmacion_si, msg19, msg20, msg21, msg22, msg23, msg24, msg25, msg26, msg27, msg28, msg29, certificadopeoneta, msg30, msg31, msg32, msg33, msg34, msg35, msg36, msg37, msg38, msg39, msg40, msg41, msg42, msg43, msg44, msg45, documento_corregido,
from src.utils.messages import message1, message2, message3, message4, message5, urlWeFleet ,message_error1, message_error2
#Utils
from src.utils.utils import button_reply,comuna_en_lista

whatsapp_routes = Blueprint('webhook_whatsapp', __name__)



# Ruta para recibir mensajes / 
@whatsapp_routes.route("/whatsapp/webhook", methods=["POST", "GET"])
def webhook_whatsapp():
    # Imprime todo el cuerpo de la solicitud
    # print("Raw request data:", request.data)
    # print("JSON request data:", json.dumps(request.get_json(), indent=4))
     
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
    
    #3-  Verificar el token de verificación
    if request.method == "GET":
        verify_token = token_verified
        print("Token de verificacion", verify_token)
       
        if request.args.get('hub.verify_token') == verify_token: 
            return request.args.get('hub.challenge')
        else:
            return "Invalid verification token"
    
    # Handle Webhook Subscriptions
    data = request.get_json()
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
                # Capturar el texto del formulario y pasarlo como mensaje a "save_user_message"
                message_received = get_interactive_response(data)
                message_received_flow = get_interactive_response_flow(data)
                print("Mensaje Obtenido Flow/Formulario", json.dumps(message_received_flow, indent=4))

                if message_received:  # Verificar si el mensaje recibido no está vacío
                    form_data = get_form_data(message_received)

                # 🔹 EXTRAER NOMBRE DEL FORMULARIO (FLOW) DESDE message_received_flow
                form_name = message_received_flow.get("name", "UNKNOWN_FORM_NAME")  # Extraer Nombre del Flow

                # ✅ IMPRIMIR INFORMACIÓN COMPLETA DEL FLOW
                print(f"🔍 Datos completos del Flow recibido: {json.dumps(message_received_flow, indent=4)}")
                print(f"📝 Flow Respondido: Nombre={form_name}")

                save_user_daily_production(mobile, form_data, id_bot) 

            
            
            #3-  Capturar mensajes con Stickers
            if message_type == "sticker":
                if message_received:
                    save_user_message(id_bot,mobile, message_received, name,message_type)
                     
            # Capturar y enviar documentos
            elif message_type == "document":
                handle_file(id_bot,data, mobile, name, message_type, is_image=False)

            # Capturar y enviar imágenes
            elif message_type == "image":
                handle_file(id_bot,data, mobile, name, message_type, is_image=True)

            # Capturar y enviar audios
            elif message_type == "audio":
                handle_file(id_bot,data, mobile, name, message_type, is_image=False)
         
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

    id_config = userData['id_config']  # asegúrate de que no haya una coma al final
    recipient = userData['phone']      # asegúrate de que no haya una coma al final
    template_name = messageData['template_name'] # removed comma
    template_parameters = messageData['template_parameters']  # assuming this is always present
    template_type = messageData['template_type']  # assuming this is always present
    
    
 
    try:
        
        response = send_template_message_user(
            id_config,
            recipient,
            template_name,
            template_parameters,
            template_type
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
