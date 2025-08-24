from telegram import Update
from telegram.ext import CallbackContext

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Hola! Soy tu bot.")

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text("ℹ️ Usa /start para iniciar. Evita enviar spam.")