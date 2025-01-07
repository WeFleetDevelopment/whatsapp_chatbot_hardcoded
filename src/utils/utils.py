from unidecode import unidecode
import os    

# #Extraer el texto del mensaje creado por el boton
# def button_reply(data):
#     print("Datos recividos en la funcion del boton", data)
#     try:
#         if 'entry' in data and len(data['entry']) > 0 and 'changes' in data['entry'][0]:
#             for change in data['entry'][0]['changes']:
#                 if 'value' in change and 'messages' in change['value']:
#                     for message in change['value']['messages']:
#                         if 'interactive' in message and 'type' in message['interactive'] and message['interactive']['type'] == 'button_reply':
#                             return message['interactive']['button_reply']['title']
#     except Exception as e:
#         print("Error:", e)
#     return None

# ------ Funcion para obtener los datos del boton cuando se presiona
def button_reply(data):
    print("Datos recibidos en la función del botón", data)
    try:
        if 'entry' in data and len(data['entry']) > 0 and 'changes' in data['entry'][0]:
            for change in data['entry'][0]['changes']:
                if 'value' in change and 'messages' in change['value']:
                    for message in change['value']['messages']:
                        if 'button' in message and 'text' in message['button']:
                            return message['button']['text']
    except Exception as e:
        print("Error:", e)
    return None

#Valudar comuna en el TXT
def comuna_en_lista(comuna):  
    if len(comuna) < 4:
        return False
    # Obtiene la ruta del directorio actual del script
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Construye la ruta del archivo 'comunas.txt'
    file_path = os.path.join(dir_path, 'comunas.txt')
    with open(file_path, 'r', encoding='utf-8') as f:
        comunas = f.read().splitlines()
        comuna = unidecode(comuna).lower()
        comunas = [unidecode(c).lower() for c in comunas]
        for c in comunas:
            if comuna in c or c in comuna:
                return True 
        return False