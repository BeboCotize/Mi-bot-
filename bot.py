import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ---------------- CONFIG ----------------
TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # Cambia esto por tu ID de Telegram
PREFIXES = [".", "!", "?", "#"]

# Usuarios registrados y baneados
registered_users = {}
banned_users = {}

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- HELPERS ----------------
def is_registered(user_id):
    return user_id in registered_users and user_id not in banned_users

def is_admin(user_id):
    return user_id == ADMIN_ID

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name

    if user_id in banned_users:
        reason = banned_users[user_id]
        await update.message.reply_text(f"🚫 Estás baneado del bot.\nMotivo: {reason}")
        return

    if not is_registered(user_id):
        registered_users[user_id] = name
        await update.message.reply_text(f"✅ Te has registrado {name}, ahora puedes usar el bot.")

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📍 Menú Principal:", reply_markup=reply_markup)

# ---------------- ADMIN ----------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("🚫 No tienes acceso al panel admin.")
        return

    text = "⚙️ Panel Admin:\n"
    text += "👥 Usuarios registrados:\n"
    text += "\n".join(f"• {u}" for u in registered_users.values()) or "📭 Ninguno"

    await update.message.reply_text(text)

# ---------------- CALLBACKS ----------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_registered(user_id):
        await query.edit_message_text("🚫 No estás registrado. Usa /start para registrarte.")
        return

    if query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu_principal")]
        ]
        await query.edit_message_text("🍔 Texto sobre comida.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎞️ Acción", callback_data="peliculas_accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="peliculas_comedia")],
            [InlineKeyboardButton("😱 Terror", callback_data="peliculas_terror")],
            [InlineKeyboardButton("💘 Romance", callback_data="peliculas_romance")],
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu_principal")]
        ]
        await query.edit_message_text("🎬 Selecciona un género:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("peliculas_"):
        genero = query.data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("🏠 Volver al menú principal", callback_data="menu_principal")]
        ]
        await query.edit_message_text(f"🎞️ Lista de películas de {genero}.", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_principal":
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text("📍 Menú Principal:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada. Usa /start si quieres volver a abrir el menú.")

# ---------------- PREFIJO HANDLER ----------------
async def prefixed_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if any(text.startswith(p + "start") for p in PREFIXES):
        await start(update, context)

async def prefixed_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if any(text.startswith(p + "admin") for p in PREFIXES):
        await admin(update, context)

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    # Handlers válidos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))

    # Prefijos alternativos (.start, !start, etc)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_admin))

    # Callbacks
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()