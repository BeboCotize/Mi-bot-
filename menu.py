from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def menu(update, context):
    keyboard = [
        [InlineKeyboardButton("🛠 Tools", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")],
        [InlineKeyboardButton("👋 Hola xd", callback_data="hola")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 Menú principal:", reply_markup=reply_markup)

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🛠 Aquí van las herramientas...")
    elif query.data == "gateway":
        await query.edit_message_text("🌐 Gateway activo...")
    elif query.data == "hola":
        await query.edit_message_text("👋 Hola xd") 