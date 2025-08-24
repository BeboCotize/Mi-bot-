import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from antispam import antispam_handler
from handlers import start, help_command

# Configuración de logs
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comandos
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Anti-spam (mensajes normales)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, antispam_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()