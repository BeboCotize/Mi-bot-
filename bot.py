import logging
import random
import sqlite3
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "6629555218"   # ⚠️ pon tu token
ADMIN_ID = 6629555218         # tu ID de admin
DB_FILE = "users.db"

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# BASE DE DATOS
# ==============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_registered(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def register_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def delete_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# ==============================
# FUNCIONES BOT
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("🚫 No estás registrado. Usa /register para acceder.")
        return

    keyboard = [
        [InlineKeyboardButton("TOOLS", callback_data="comida")],
        [InlineKeyboardButton("GATES", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Hola! Bienvenido a tu bot\n\nSelecciona una opción:",
        reply_markup=reply_markup
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    register_user(user_id)
    await update.message.reply_text("✅ Te has registrado correctamente. Ahora puedes usar el bot con /start.")

# ==============================
# CALLBACKS
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if not is_registered(user_id):
        await query.answer("🚫 No estás registrado.", show_alert=True)
        return

    await query.answer()

    if query.data == "volver_menu":
        keyboard = [
            [InlineKeyboardButton("TOOLS", callback_data="comida")],
            [InlineKeyboardButton("GATES", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="👋 Hola! Bienvenido a tu bot\n\nSelecciona una opción:",
            reply_markup=reply_markup
        )

    elif query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🍔 Lista de comidas:\n- Pizza\n- Hamburguesa\n- Tacos",
            reply_markup=reply_markup
        )

    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("AUTH", callback_data="accion")],
            [InlineKeyboardButton("CCN", callback_data="comedia")],
            [InlineKeyboardButton("CHARGED", callback_data="terror")],
            [InlineKeyboardButton("ESPECIAL", callback_data="romance")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🎬 Categorías de películas:",
            reply_markup=reply_markup
        )

    elif query.data in ["accion", "comedia", "terror", "romance"]:
        textos = {
            "accion": "🔫 Películas de acción llenas de adrenalina!",
            "comedia": "😂 Ríe con estas comedias inolvidables!",
            "terror": "👻 Prepárate para asustarte con el terror!",
            "romance": "❤️ Disfruta de los mejores romances!"
        }
        genero = query.data
        keyboard = [
            [InlineKeyboardButton("↩️ Volver a películas", callback_data="peliculas")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=textos[genero],
            reply_markup=reply_markup
        )

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

# ==============================
# PANEL ADMIN (sin botones)
# ==============================
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("📭 No hay usuarios registrados.")
    else:
        await update.message.reply_text("👥 Usuarios registrados:\n" + "\n".join(map(str, users)))

async def admindelete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Uso: /admindelete <user_id>")
        return
    try:
        uid = int(context.args[0])
        delete_user(uid)
        await update.message.reply_text(f"🗑 Usuario {uid} eliminado.")
    except ValueError:
        await update.message.reply_text("⚠️ ID inválido.")

async def adminbroadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Uso: /adminbroadcast <mensaje>")
        return
    msg = " ".join(context.args)
    users = get_all_users()
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje a {uid}: {e}")
    await update.message.reply_text("📢 Mensaje enviado a todos los usuarios.")

# ==============================
# MAIN
# ==============================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))

    # Admin
    app.add_handler(CommandHandler("adminlist", adminlist))
    app.add_handler(CommandHandler("admindelete", admindelete))
    app.add_handler(CommandHandler("adminbroadcast", adminbroadcast))

    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()