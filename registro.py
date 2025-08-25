from telegram import Update
from telegram.ext import ContextTypes
from db import register_user, is_registered, is_banned

# /start (sin prefijo)
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bienvenido, usa .registrar para comenzar.")

# .registrar (con prefijo)
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