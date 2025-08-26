import os
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler
)
from handlers import gen_command, ban_command, unban_command, admin_command, genkey_command
from menu import menu, button_handler
from peliculas import peliculas, peliculas_callback
from registro import start, registrar
from tarjetas import tarjeta

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

def main():
    app = Application.builder().token(TOKEN).build()

    # Registro / start
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))

    # Comandos principales
    app.add_handler(CommandHandler("gen", gen_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("genkey", genkey_command))

    # Tarjetas simples
    app.add_handler(CommandHandler("tarjeta", tarjeta))

    # Menús
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("peliculas", peliculas))
    app.add_handler(CallbackQueryHandler(peliculas_callback))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()