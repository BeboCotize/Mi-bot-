from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def peliculas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Acción", callback_data="accion")],
        [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
        [InlineKeyboardButton("😱 Terror", callback_data="terror")],
        [InlineKeyboardButton("❤️ Romance", callback_data="romance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📽️ Elige una categoría de películas:", reply_markup=reply_markup)

async def peliculas_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "accion":
        await query.edit_message_text("🔥 Recomendación de Acción: John Wick")
    elif query.data == "comedia":
        await query.edit_message_text("😂 Recomendación de Comedia: The Hangover")
    elif query.data == "terror":
        await query.edit_message_text("😱 Recomendación de Terror: El Conjuro")
    elif query.data == "romance":
        await query.edit_message_text("❤️ Recomendación de Romance: Titanic")