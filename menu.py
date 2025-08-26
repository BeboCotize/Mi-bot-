from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# 📌 Menú principal
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛠 Tools", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("👋 Saludo", callback_data="hola")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 Menú principal:", reply_markup=reply_markup)


# 📌 Manejo de botones
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🛠 Aquí van las herramientas...")
    elif query.data == "gateway":
        await query.edit_message_text("🌐 Gateway activo...")
    elif query.data == "peliculas":
        # Reutilizamos el menú de películas
        from peliculas import peliculas
        await peliculas(update, context)
    elif query.data == "hola":
        await query.edit_message_text("👋 Hola, ¿cómo estás?")