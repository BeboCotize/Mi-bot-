import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from handlers import start, button_handler
from antispam import antispam_handler
from db import init_db
import os

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM")

def main():
    init_db()  # Crear tablas si no existen

    app = Application.builder().token(BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("unban", lambda u, c: None))  # Se añade en antispam.py

    # Botones
    app.add_handler(CallbackQueryHandler(button_handler))

    # Mensajes normales -> antispam
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antispam_handler))

    logging.info("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()