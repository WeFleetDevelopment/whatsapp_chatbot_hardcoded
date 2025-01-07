##Aqui Hacemos que la aplicacion Corra de manera correcta y pueda funcionar
import os
from src import create_app

app = create_app()

print("-------------- Aplicacion Corriendo Exitosamente de Chatbot de  Business ------------------")

if __name__ == '__main__':
    app.run()