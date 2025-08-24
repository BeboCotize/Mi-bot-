from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
import logging
import sqlite3
import datetime

# 🚀 Configuración
TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # tu ID de admin
PREFIXES = [".", "?", "!", "#"]

# 📦 Base de datos SQLite
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    name TEXT,
    banned INTEGER DEFAULT 0,
    reason TEXT,
    date TEXT
)""")
conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================
# 🔹 Helpers
# ============================
def check_prefix(text: str, cmd: str):
    return any(text.startswith(p + cmd) for p in PREFIXES)

def is_registered(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def is_banned(user_id):
    cursor.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

def register_user(user_id, name):
    if not is_registered(user_id):
        cursor.execute("INSERT INTO users (user_id, name, date) VALUES (?, ?, ?)",
                       (user_id, name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

# ============================
# 🔹 Handlers
# ============================
async def start_handler(update: Update, context):
    user = update.effective_user

    if is_banned(user.id):
        await update.message.reply_text("🚫 Estás baneado y no puedes usar este bot.")
        return

    register_user(user.id, user.first_name)

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Bienvenido {user.first_name}, selecciona una opción:",
        reply_markup=reply_markup
    )

# Para prefijos (.start, ?start, !start, #start)
async def prefix_handler(update: Update, context):
    text = update.message.text
    if check_prefix(text, "start"):
        await start_handler(update, context)

async def buttons(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("🔙 Volver al menú principal", callback_data="menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "🍔 Aquí tienes comida deliciosa",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎥 Acción", callback_data="accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
            [InlineKeyboardButton("😱 Terror", callback_data="terror")],
            [InlineKeyboardButton("💘 Romance", callback_data="romance")],
            [InlineKeyboardButton("🔙 Volver al menú principal", callback_data="menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "🎬 Selecciona un género:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "menu":
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "👋 Menú principal:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "cerrar":
        await query.delete_message()

# ============================
# 🔹 Main
# ============================
def main():
    app = Application.builder().token(TOKEN).build()

    # ✅ /start oficial
    app.add_handler(CommandHandler("start", start_handler))

    # ✅ prefijos (.start, ?start, !start, #start)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^[\.\?!#]start"), prefix_handler))

    app.add_handler(CallbackQueryHandler(buttons))

    logger.info("✅ Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()