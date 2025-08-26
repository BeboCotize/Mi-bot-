from telegram import Update
from telegram.ext import ContextTypes
from db import registrar_usuario, marcar_registrado

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    registrar_usuario(user.id, user.username or "Desconocido")
    await update.message.reply_text(
        f"👋 Bienvenido {user.first_name}!\n\n"
        "Para comenzar, usa `.registrar` o `/registrar`."
    )

# /registrar
async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    marcar_registrado(user.id)
    await update.message.reply_text(
        "✅ Registro completado. ¡Ya puedes usar los comandos!"
    )