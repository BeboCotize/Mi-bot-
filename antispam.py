import datetime
from db import ban_user, is_banned, unban_user
from telegram import Update
from telegram.ext import ContextTypes

# Diccionario en memoria para contar mensajes
user_messages = {}

ADMIN_ID = 123456789  # <-- cámbialo por tu ID de admin
BAN_DURATION = datetime.timedelta(hours=5)

async def antispam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Verificar si ya está baneado
    if is_banned(user_id):
        await update.message.delete()
        return

    now = datetime.datetime.utcnow()
    msgs = user_messages.get(user_id, [])
    msgs = [t for t in msgs if (now - t).seconds < 30]  # últimos 30s
    msgs.append(now)
    user_messages[user_id] = msgs

    if len(msgs) >= 20:
        until = now + BAN_DURATION
        ban_user(user_id, until)
        await update.message.chat.ban_member(user_id, until_date=until)

        # Notificar al admin
        await context.bot.send_message(ADMIN_ID, f"🚨 Usuario {user_id} baneado por spam hasta {until}.")

# /unban
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Uso: /unban <user_id>")
        return

    user_id = int(context.args[0])
    unban_user(user_id)

    await update.effective_chat.unban_member(user_id)
    await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")