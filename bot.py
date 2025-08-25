import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from db import init_db
from registro import start, registrar
from comandos import custom_commands

# 🔹 Configura tu TOKEN aquí
TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"

logging.basicConfig(level=logging.INFO)

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # Comandos principales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))

    # Prefijos personalizados (. ! * ?)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_commands))

    logging.info("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()