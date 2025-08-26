import os
from telegram.ext import Application, CommandHandler
from handlers import start, gen

# ─────────────────────────────
#   📌 MAIN BOT
# ─────────────────────────────
def main():
    # Obtiene el token desde variable de entorno (Railway)
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ No se encontró la variable BOT_TOKEN en Railway.")

    # Inicializar aplicación
    application = Application.builder().token(TOKEN).build()

    # Handlers principales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", gen))

    # Inicia el bot
    print("✅ Bot iniciado correctamente...")
    application.run_polling()

if __name__ == "__main__":
    main()