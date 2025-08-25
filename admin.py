from telegram import Update
from telegram.ext import CallbackContext
from db import is_user_registered, is_banned, ban_user, unban_user, add_admin_db, create_key

# 🚫 Comando .ban
def ban(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Responde al mensaje del usuario que quieras banear con .ban")
        return

    user_id = update.message.reply_to_message.from_user.id
    if is_user_registered(user_id):
        ban_user(user_id)
        update.message.reply_text(f"🚫 Usuario {user_id} baneado con éxito.")
    else:
        update.message.reply_text("⚠️ Ese usuario no está registrado.")

# ✅ Comando .unban
def unban(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Responde al mensaje del usuario que quieras desbanear con .unban")
        return

    user_id = update.message.reply_to_message.from_user.id
    if is_user_registered(user_id):
        unban_user(user_id)
        update.message.reply_text(f"✅ Usuario {user_id} desbaneado con éxito.")
    else:
        update.message.reply_text("⚠️ Ese usuario no está registrado.")

# 👑 Comando .admin
def add_admin(update: Update, context: CallbackContext):
    if not update.message.reply_to_message:
        update.message.reply_text("⚠️ Responde al mensaje del usuario que quieras hacer admin con .admin")
        return

    user_id = update.message.reply_to_message.from_user.id
    if is_user_registered(user_id):
        add_admin_db(user_id)
        update.message.reply_text(f"👑 Usuario {user_id} ahora es administrador.")
    else:
        update.message.reply_text("⚠️ Ese usuario no está registrado.")

# 🔑 Comando .genkey <días>
def genkey(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        update.message.reply_text("⚠️ Uso correcto: `.genkey <días>`")
        return

    try:
        days = int(context.args[0])
        key = create_key(days)
        update.message.reply_text(f"🔑 Key generada (válida por {days} días):\n`{key}`", parse_mode="Markdown")
    except ValueError:
        update.message.reply_text("⚠️ Los días deben ser un número entero.")