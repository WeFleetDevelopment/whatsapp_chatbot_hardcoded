
#--------------- Configuracion de WhatsApp ---------------
from heyoo import WhatsApp
import logging
import os

#Original

token = os.getenv('TOKEN_CHATBOT_CONFIG')
idNumeroTelefono = os.getenv('ID_NUMBER_PHONE')
telefonoEnvia = os.getenv('PHONE_SEND') 
messenger = WhatsApp(token, idNumeroTelefono)     

# token = 'EAAGto3aumi0BOz7HfrZBgxQ4yw4Oelkk0X5hY6VFpuClfX0sJQup4PJgDAShkwpMqBd6nNA6b9J2G5rV412PzE87QtlItNhpWcOnzSxJqehNMRowrNbu38OEqhK6b0ZC5ZBjsw34cvfZCyBzlcSmOGi2MAERolcYjEMCiEDZBkURp4SAq9A9WZBrHJRLU0ZAqNATWbRbLj6RiPecPCXHwJZAFkNOqTdMblSZBChkQgTXo7s2nFZBRUWZBwZD'
# idNumeroTelefono = '439445745924654'
# telefonoEnvia = '56976740618'
# messenger = WhatsApp(token, idNumeroTelefono)  


                              
 
# Logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# )
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)