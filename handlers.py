from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("⬅️ Volver atrás", callback_data="volver")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Bienvenido, elige una opción:", reply_markup=reply_markup)

# Botones
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "peliculas":
        await query.edit_message_text("🎬 Aquí irían tus películas...")
    elif query.data == "comida":
        await query.edit_message_text("🍔 Aquí iría la lista de comida...")
    elif query.data == "volver":
        await start(update, context)