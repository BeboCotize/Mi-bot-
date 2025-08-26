import os
import logging
from telegram.ext import Application, CommandHandler
from handlers import start, gen  # ✅ Importamos los comandos

# --- Configuración del logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- TOKEN del bot ---
TOKEN = os.getenv("BOT_TOKEN")  # ⚡ Se toma de Railway (Variable de entorno)

def main():
    # Crear aplicación
    application = Application.builder().token(TOKEN).build()

    # Handlers (comandos)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", gen))

    # Ejecutar bot
    application.run_polling()

if __name__ == "__main__":
    main()