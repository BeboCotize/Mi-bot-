import logging
from telegram.ext import Application, CommandHandler
from handlers import start, gen   # ✅ Importamos los comandos

# --- Configuración del logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- TOKEN del bot ---
TOKEN = "8271445453:AAEu6ZKovCOrFIdiWHNpOklgu-Va_nZ_zB8"   # 🔑 Reemplaza con tu token real


def main():
    # Crear aplicación
    application = Application.builder().token(TOKEN).build()

    # Handlers (comandos)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", gen))

    # Iniciar bot
    logging.info("🤖 Bot en ejecución...")
    application.run_polling()


if __name__ == "__main__":
    main()