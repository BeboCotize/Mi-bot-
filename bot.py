import os
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from db import init_db
import comandos

TOKEN = os.getenv("BOT_TOKEN")

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()

    # HANDLERS
    app.add_handler(CommandHandler("start", commands.start))
    app.add_handler(CallbackQueryHandler(commands.buttons))
    app.add_handler(CommandHandler("redeem", commands.redeem))

    # Prefijo .
    app.add_handler(MessageHandler(filters.Regex(r"^\.ban"), commands.ban))
    app.add_handler(MessageHandler(filters.Regex(r"^\.unban"), commands.unban))
    app.add_handler(MessageHandler(filters.Regex(r"^\.genkey"), commands.genkey))
    app.add_handler(MessageHandler(filters.Regex(r"^\.gen"), commands.gen))

    app.run_polling()

if __name__ == "__main__":
    main()