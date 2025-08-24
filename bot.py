import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"   # ⚠️ Cambia por tu token
ADMIN_ID = 6629555218         # ⚠️ Cambia por tu ID de admin
DB_FILE = "users.db"

PREFIXES = [".", "!", "?", "#"]

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
    c.execute("CREATE TABLE IF NOT EXISTS banned (id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_registered(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_banned(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM banned WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def register_user(user_id: int):
    if is_banned(user_id):
        return False
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return True

def delete_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    c.execute("INSERT OR IGNORE INTO banned (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def ban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    c.execute("INSERT OR IGNORE INTO banned (id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM banned WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def list_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users")
    users = c.fetchall()
    conn.close()
    return [u[0] for u in users]

def list_banned():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM banned")
    banned = c.fetchall()
    conn.close()
    return [u[0] for u in banned]

# ==============================
# COMANDOS PRINCIPALES
# ==============================
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.message.reply_text("🚫 Estás baneado permanentemente. No puedes usar este bot.")
        return

    if register_user(user_id):
        await update.message.reply_text("✅ Te has registrado correctamente. Ahora puedes usar el bot con /start.")
    else:
        await update.message.reply_text("⚠️ Ya estás registrado o no es posible registrarte.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("🚫 No estás registrado. Usa /register para registrarte.")
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

# ==============================
# ADMIN PANEL
# ==============================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No eres admin.")
        return

    users = list_users()
    banned = list_banned()

    text = "👑 Panel de Admin\n\n"
    text += "Usuarios registrados:\n"
    text += "\n".join(f"• {u}" for u in users) or "📭 Ninguno"