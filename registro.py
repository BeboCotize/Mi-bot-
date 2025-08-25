from telegram import Update
from telegram.ext import ContextTypes
from db import register_user, is_registered, is_banned

# /start (se envía al entrar al bot)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al bot.\n\n"
        "👉 Para registrarte usa:\n"
        " • `.registrar`\n"
        " • `!registrar`\n"
        " • `*registrar`\n"
        " • `?registrar`\n"
        " • o también `/registrar`"
    )

# .registrar o /registrar
async def registrar_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if is_banned(user_id):
        await update.message.reply_text("🚫 Estás baneado del bot.")
        return
    
    if is_registered(user_id):
        await update.message.reply_text("✅ Ya estás registrado.")
        return
    
    register_user(user_id)
    await update.message.reply_text("🎉 Registro completado. Ya puedes usar el bot.")