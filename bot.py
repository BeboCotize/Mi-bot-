import os
from telegram.ext import Application, CommandHandler, PrefixHandler
from registro import start_command, registrar_usuario
from db import init_db

# Prefijos permitidos
PREFIJOS = ".!*?"

def main():
    # Inicializar DB
    init_db()

    # Token desde variables de entorno
    TOKEN = os.getenv("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM")
    if not TOKEN:
        raise ValueError("❌ BOT_TOKEN no configurado en Railway")

    app = Application.builder().token(TOKEN).build()

    # /start normal (mensaje de bienvenida)
    app.add_handler(CommandHandler("start", start_command))

    # /registrar también válido
    app.add_handler(CommandHandler("registrar", registrar_usuario))

    # Prefijos (. ! * ?) para registrar
    app.add_handler(PrefixHandler(PREFIJOS, "registrar", registrar_usuario))

    print("🤖 Bot iniciado correctamente...")
    app.run_polling()

if __name__ == "__main__":
    main()