import os
from telegram.ext import Application, CommandHandler, PrefixHandler
from registro import start_command, registrar_usuario
from db import init_db

# Prefijos permitidos
PREFIJOS = "..*':;!?#/)(-%"

def main():
    # Inicializar DB
    init_db()

    # Token desde variables de entorno
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN no configurado en Railway")

    app = Application.builder().token(TOKEN).build()

    # /start normal
    app.add_handler(CommandHandler("start", start_command))

    # Otros comandos con prefijos
    app.add_handler(PrefixHandler(PREFIJOS, "registrar", registrar_usuario))

    print("🤖 Bot iniciado correctamente...")
    app.run_polling()

if __name__ == "__main__":
    main()