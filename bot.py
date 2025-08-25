# bot.py
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from registro import start_command, registrar_usuario
from admin import admin_commands
from peliculas import peliculas_command
from tarjetas import tarjeta_command
from antispam import antispam_middleware
from custom_commands import custom_commands

# Configuración del logging (para ver errores y actividad del bot)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Aquí pega tu TOKEN real
TOKEN = "6629555218"


def main():
    app = Application.builder().token(TOKEN).build()

    # --- Comandos básicos ---
    app.add_handler(CommandHandler("start", start_command))   # Registro inicial
    app.add_handler(CommandHandler("peliculas", peliculas_command))  # Menú películas
    app.add_handler(CommandHandler("tarjeta", tarjeta_command))      # Generar tarjeta
    app.add_handler(CommandHandler("admin", admin_commands))         # Panel admin

    # --- Registro automático de usuarios ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_usuario))

    # --- AntiSpam ---
    app.add_handler(MessageHandler(filters.ALL, antispam_middleware))

    # --- Custom commands con prefijos (!, %, ;, *, #) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_commands))

    # Inicia el bot
    print("🤖 Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()