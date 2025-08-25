from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
from db import is_registered, is_banned

ADMIN_ID = 6629555218  # <-- tu ID de Telegram

def admin(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        update.message.reply_text("❌ Solo el administrador puede acceder a este panel.")
        return

    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="admin_peliculas")],
        [InlineKeyboardButton("💳 Generar tarjeta", callback_data="admin_tarjeta")],
        [InlineKeyboardButton("🚫 Banear usuario", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Desbanear usuario", callback_data="admin_unban")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("⚙️ Panel de administración:", reply_markup=reply_markup)

def admin_menu(query, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="admin_peliculas")],
        [InlineKeyboardButton("💳 Generar tarjeta", callback_data="admin_tarjeta")],
        [InlineKeyboardButton("🚫 Banear usuario", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ Desbanear usuario", callback_data="admin_unban")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text("⚙️ Panel de administración:", reply_markup=reply_markup)

def admin_button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        query.edit_message_text("❌ No tienes permisos.")
        return

    if query.data == "admin_peliculas":
        from peliculas import peliculas
        peliculas(query, context)
    elif query.data == "admin_tarjeta":
        from tarjetas import tarjeta
        tarjeta(query, context)
    elif query.data == "admin_ban":
        query.edit_message_text("✍️ Usa /ban <ID>")
    elif query.data == "admin_unban":
        query.edit_message_text("✍️ Usa /unban <ID>")

admin_handler = CommandHandler("admin", admin)
admin_button_handler = CallbackQueryHandler(admin_button, pattern="^admin_")