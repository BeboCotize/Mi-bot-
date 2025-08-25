from telegram.ext import Application, CommandHandler
import os

TOKEN = os.getenv("BOT_TOKEN")  # 🔑 Pon tu token en variables de entorno en Railway

app = Application.builder().token(TOKEN).build()

# --- Comandos básicos ---
async def start(update, context):
    await update.message.reply_text("🚀 ¡Hola! Estoy vivo en Railway.")

async def ping(update, context):
    await update.message.reply_text("🏓 Pong!")

# --- Handlers ---
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ping", ping))

if __name__ == "__main__":
    print("✅ Bot iniciado en Railway...")
    app.run_polling()