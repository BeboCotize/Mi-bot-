from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from db import ban_user, unban_user

ADMIN_ID = 123456789  # <-- tu ID de Telegram

def ban(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        update.message.reply_text("❌ Debes poner un ID de usuario.")
        return
    user_id = int(context.args[0])
    ban_user(user_id)
    update.message.reply_text(f"🚫 Usuario {user_id} baneado.")

def unban(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ No tienes permisos.")
        return
    if not context.args:
        update.message.reply_text("❌ Debes poner un ID de usuario.")
        return
    user_id = int(context.args[0])
    unban_user(user_id)
    update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")

ban_handler = CommandHandler("ban", ban)
unban_handler = CommandHandler("unban", unban)