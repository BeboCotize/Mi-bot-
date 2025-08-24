# bot.py
import os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from antispam import antispam_handler
from db import init_db

TOKEN = os.getenv("BOT_TOKEN")

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("⬅️ Volver atrás", callback_data="volver")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenido al bot 👋", reply_markup=reply_markup)

# Manejo de botones
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "peliculas":
        await query.edit_message_text("Aquí tienes la lista de películas 🎥")
    elif query.data == "volver":
        await query.edit_message_text("Has vuelto al menú principal ⬅️")

def main():
    init_db()

    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))

    # Botones
    app.add_handler(CallbackQueryHandler(button_handler))

    # Antispam
    app.add_handler(MessageHandler(filters.ALL, antispam_handler))

    print("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()