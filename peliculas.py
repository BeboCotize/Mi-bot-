from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# 🎬 Menú de categorías de películas
async def peliculas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Acción", callback_data="accion")],
        [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
        [InlineKeyboardButton("😱 Terror", callback_data="terror")],
        [InlineKeyboardButton("❤️ Romance", callback_data="romance")],
        [InlineKeyboardButton("⬅️ Volver al menú", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Si viene desde /peliculas → es update.message
    if update.message:
        await update.message.reply_text("📽️ Elige una categoría de películas:", reply_markup=reply_markup)
    # Si viene desde un botón → es update.callback_query
    elif update.callback_query:
        await update.callback_query.edit_message_text("📽️ Elige una categoría de películas:", reply_markup=reply_markup)


# 🎬 Respuestas por categoría
async def peliculas_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "accion":
        await query.edit_message_text("🔥 Recomendación de Acción: *John Wick*", parse_mode="Markdown")
    elif query.data == "comedia":
        await query.edit_message_text("😂 Recomendación de Comedia: *The Hangover*", parse_mode="Markdown")
    elif query.data == "terror":
        await query.edit_message_text("😱 Recomendación de Terror: *El Conjuro*", parse_mode="Markdown")
    elif query.data == "romance":
        await query.edit_message_text("❤️ Recomendación de Romance: *Titanic*", parse_mode="Markdown")
    elif query.data == "menu":
        from menu import menu
        await menu(update, context)