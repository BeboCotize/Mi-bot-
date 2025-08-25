import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import init_db, add_user, is_user_registered

# Inicializar la base de datos
init_db()

TOKEN = os.getenv("BOT_TOKEN")

# ---- HANDLERS ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡Hola! Estoy vivo en Railway.")

async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_user_registered(user_id):
        await update.message.reply_text("⚠️ Ya estabas registrado, puedes usar los comandos.")
    else:
        add_user(user_id)
        await update.message.reply_text("✅ Registro completado. ¡Ya puedes usar los comandos!")

# ---- MAIN ----
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registrar", registrar))

    print("🤖 Bot iniciado en Railway...")
    app.run_polling()

if __name__ == "__main__":
    main()