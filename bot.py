
import logging
from telegram.ext import Application, CommandHandler
from registro import start_command, registrar_usuario
from db import init_db

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 🚀 Función principal
def main():
    # Inicializar la base de datos
    init_db()

    # Crear la aplicación del bot
    application = Application.builder().token("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM").build()

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("registrar", registrar_usuario))

    # Ejecutar el bot
    application.run_polling()

if __name__ == "__main__":
    main()