from telegram import Update
from telegram.ext import ContextTypes
from db import ban_user, unban_user, set_admin, add_key
from generator import generate_card

# .gen
async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: `.gen BINxxxx|MM|YYYY|rnd`")
        return
    
    pattern = context.args[0]
    try:
        results = [generate_card(pattern) for _ in range(10)]
        text = "\n".join(results)
        await update.message.reply_text(f"✅ Generadas:\n\n{text}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")


# .ban
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: `.ban user_id`")
        return
    user_id = int(context.args[0])
    ban_user(user_id)
    await update.message.reply_text(f"🚫 Usuario {user_id} baneado.")


# .unban
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: `.unban user_id`")
        return
    user_id = int(context.args[0])
    unban_user(user_id)
    await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")


# .admin
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: `.admin user_id`")
        return
    user_id = int(context.args[0])
    set_admin(user_id)
    await update.message.reply_text(f"👑 Usuario {user_id} ahora es administrador.")


# .genkey
import secrets, datetime

async def genkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: `.genkey <días>`")
        return
    
    days = int(context.args[0])
    key = secrets.token_hex(8)
    expires = datetime.datetime.now() + datetime.timedelta(days=days)
    add_key(key, expires)
    await update.message.reply_text(f"🔑 Key generada:\n`{key}`\nVence en {days} días.", parse_mode="Markdown")