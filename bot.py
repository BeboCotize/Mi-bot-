import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# === CONFIGURACIÓN ===
TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # tu id de Telegram

# Bases de datos en memoria
registered_users = {}
banned_users = {}

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# === FUNCIONES DE ADMINISTRACIÓN ===
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: .ban <user_id> <razón>")
        return

    user_id = int(context.args[0])
    reason = " ".join(context.args[1:])

    banned_users[user_id] = {
        "reason": reason,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    if user_id in registered_users:
        del registered_users[user_id]

    await update.message.reply_text(f"🚫 Usuario {user_id} baneado por: {reason}")


async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if len(context.args) < 1:
        await update.message.reply_text("Uso: .unban <user_id>")
        return

    user_id = int(context.args[0])
    if user_id in banned_users:
        del banned_users[user_id]
        await update.message.reply_text(f"✅ Usuario {user_id} desbaneado")
    else:
        await update.message.reply_text("⚠ Usuario no estaba baneado")


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 Usuarios registrados:\n"
    if registered_users:
        for uid, data in registered_users.items():
            name = data.get("name", "Desconocido")
            date = data.get("date", "N/A")
            text += f"• {uid} → {name} (📅 {date})\n"
    else:
        text += "📭 Ninguno\n"

    text += "\n🚫 Usuarios baneados:\n"
    if banned_users:
        for uid, data in banned_users.items():
            reason = data.get("reason", "Sin motivo")
            date = data.get("date", "N/A")
            text += f"• {uid} → {reason} (📅 {date})\n"
    else:
        text += "📭 Ninguno\n"

    await update.message.reply_text(text)


# === MENSAJE PRINCIPAL ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # si está baneado
    if user.id in banned_users:
        reason = banned_users[user.id]["reason"]
        date = banned_users[user.id]["date"]
        await update.message.reply_text(f"🚫 Estás baneado.\nMotivo: {reason}\nFecha: {date}")
        return

    # registrar usuario si no está
    if user.id not in registered_users:
        registered_users[user.id] = {
            "name": user.first_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Hola {user.first_name}, bienvenido al bot.\nSelecciona una opción:",
        reply_markup=reply_markup
    )


# === CALLBACKS ===
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "Aquí tienes comida deliciosa 🍕🍔🌮",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎞 Opción 1", callback_data="pelicula1")],
            [InlineKeyboardButton("📽 Opción 2", callback_data="pelicula2")],
            [InlineKeyboardButton("🍿 Opción 3", callback_data="pelicula3")],
            [InlineKeyboardButton("🎥 Opción 4", callback_data="pelicula4")],
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "🎬 Menú de películas, elige una opción:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("pelicula"):
        opcion = query.data.replace("pelicula", "")
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver a películas", callback_data="peliculas")],
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            f"Has seleccionado la película opción {opcion} 🍿",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "menu":
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "🏠 Menú principal:\nSelecciona una opción:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "cerrar":
        await query.edit_message_text("👋 Conversación cerrada.")


# === MANEJADOR DE MENSAJES ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(text.startswith(prefix + "start") for prefix in [".", "/", "!", "?"]):
        await start(update, context)


# === MAIN ===
def main():
    app = Application.builder().token(TOKEN).build()

    # Prefijos para admin
    app.add_handler(CommandHandler("ban", ban_user, filters=filters.User(user_id=ADMIN_ID)))
    app.add_handler(CommandHandler("unban", unban_user, filters=filters.User(user_id=ADMIN_ID)))
    app.add_handler(CommandHandler("users", list_users, filters=filters.User(user_id=ADMIN_ID)))

    # Start y callbacks
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()