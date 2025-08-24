# antispam.py
from telegram import Update
from telegram.ext import CallbackContext
from db import ban_user, is_banned

# Diccionario para contar mensajes por usuario
user_messages = {}

def antispam_handler(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Si el usuario ya está baneado, no responder
    if is_banned(user_id):
        return

    # Contar mensajes
    if user_id not in user_messages:
        user_messages[user_id] = 1
    else:
        user_messages[user_id] += 1

    # Si supera el límite, se banea
    if user_messages[user_id] > 5:  # Puedes ajustar el número
        ban_user(user_id)
        update.message.reply_text("🚫 Has sido baneado por spam.")