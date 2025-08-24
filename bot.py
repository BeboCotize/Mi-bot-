import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from antispam import antispam_handler

# Carga del token desde variable de entorno en Railway
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("⚠️ No se encontró la variable de entorno BOT_TOKEN en Railway.")

def start(update, context):
    update.message.reply_text("🤖 ¡Hola! Soy tu bot antispam funcionando en Railway.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comandos básicos
    dp.add_handler(CommandHandler("start", start))

    # Manejo de mensajes (antispam)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, antispam_handler))

    # Inicia el bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()