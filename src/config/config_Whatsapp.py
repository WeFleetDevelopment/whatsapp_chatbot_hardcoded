
#--------------- Configuracion de WhatsApp ---------------
from heyoo import WhatsApp
import logging
import os

#Original 
 
#token = os.getenv('TOKEN_CHATBOT_CONFIG')
#idNumeroTelefono = os.getenv('ID_NUMBER_PHONE')
#telefonoEnvia = os.getenv('PHONE_SEND') 
#messenger = WhatsApp(token, idNumeroTelefono)     
  


# Valores de configuracion para chatbot Hardcoded
idConfig = 'GJSS738FJSK829FHS82JT93JG9DH2859129FH29FUF034929KJC8278598HH'
tokenChatbot = os.getenv('CONFIG_TOKEN_CHATBOT')
tokenVerified = os.getenv('CONFIG_TOKEN_VERIFIED_CHATBOT')
idNumberPhone = os.getenv('CONFIG_ID_PHONE_CHATBOT')
idAccountWhatsApp = os.getenv('CONFIG_ID_ACCOUNT_WHATSAPP_CHATBOT')
phoneSend = os.getenv('CONFIG_PHONE_SEND_CHATBOT')

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) 