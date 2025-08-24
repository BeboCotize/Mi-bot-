from . import db
from telegram import Update
from telegram.ext import CallbackContext

def antispam_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Verifica si el usuario está baneado
    if db.is_banned(user_id):
        update.message.delete()
        return

    # Ejemplo: si el mensaje contiene "spam" => banear
    if "spam" in update.message.text.lower():
        db.ban_user(user_id)
        update.message.reply_text("🚫 Has sido baneado por spam.")