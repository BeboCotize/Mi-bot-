from db import ban_user, is_banned, unban_user
from telegram import Update
from telegram.ext import CallbackContext

def antispam_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Verifica si el usuario está baneado
    if is_banned(user_id):
        update.message.delete()
        return

    # Ejemplo: si el mensaje contiene "spam" => banear
    if "spam" in update.message.text.lower():
        ban_user(user_id)
        update.message.reply_text("⛔ Has sido baneado por spam.")