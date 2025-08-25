from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from db import register_user, is_registered, is_banned

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username or "SinUsuario"

    if is_banned(user_id):
        update.message.reply_text("🚫 Estás baneado del bot.")
        return

    if not is_registered(user_id):
        register_user(user_id, username)
        update.message.reply_text(f"✅ Bienvenido {user.first_name}, has sido registrado con éxito.")
    else:
        update.message.reply_text("👋 Ya estabas registrado.")

start_handler = CommandHandler("start", start)