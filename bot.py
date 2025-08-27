import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("📩 Llego un mensaje:", update.message.text)
    await update.message.reply_text("Hola! 👋 El bot está funcionando ✅")

def main():
    print("🚀 Iniciando bot con token:", TOKEN[:10], "...")  # Muestra parte del token
    app = Application.builder().token(TOKEN).build()

    # Comando /start
    app.add_handler(CommandHandler("start", start))

    # Corre el bot
    app.run_polling()

if __name__ == "__main__":
    main()