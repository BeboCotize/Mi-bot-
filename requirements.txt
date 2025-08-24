import logging
import random
import requests
import sqlite3
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
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
BOT_TOKEN = "AQUI_TU_TOKEN"  # ⚠️ cambia este
ADMIN_ID = 6629555218        # tu ID personal de admin
DB_FILE = "usuarios.db"

# ==============================
# BASE DE DATOS
# ==============================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        username TEXT,
        activo INTEGER DEFAULT 1
    )""")
    conn.commit()
    conn.close()

def registrar_usuario(user_id: int, username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO usuarios (id, username, activo) VALUES (?, ?, 1)",
              (user_id, username))
    conn.commit()
    conn.close()

def usuario_registrado(user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT activo FROM usuarios WHERE id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None and result[0] == 1

def listar_usuarios():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, activo FROM usuarios")
    rows = c.fetchall()
    conn.close()
    return rows

def bloquear_usuario(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET activo=0 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def desbloquear_usuario(user_id: int, username: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO usuarios (id, username, activo) VALUES (?, ?, 1)",
              (user_id, username))
    conn.commit()
    conn.close()

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# DECORADORES
# ==============================
async def check_access(update: Update) -> bool:
    user_id = update.effective_user.id
    if not usuario_registrado(user_id):
        await update.effective_message.reply_text("🚫 No estás registrado o fuiste bloqueado.\nUsa /registro para registrarte.")
        return False
    return True

def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

# ==============================
# COMANDOS
# ==============================
async def registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    registrar_usuario(user.id, user.username or "SinUsername")
    await update.message.reply_text("✅ Te has registrado correctamente. Ahora puedes usar el bot.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update):
        return
    keyboard = [
        [InlineKeyboardButton("TOOLS", callback_data="comida")],
        [InlineKeyboardButton("GATES", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "👋 Hola! Bienvenido a tu bot\n\nSelecciona una opción:",
        reply_markup=reply_markup
    )

# ADMIN: lista usuarios
async def usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 No tienes permiso para este comando.")
        return
    rows = listar_usuarios()
    if not rows:
        await update.message.reply_text("📭 No hay usuarios registrados.")
        return
    msg = "📋 Usuarios registrados:\n\n"
    for uid, uname, activo in rows:
        estado = "✅ Activo" if activo == 1 else "⛔ Bloqueado"
        msg += f"• {uid} (@{uname}) - {estado}\n"
    await update.message.reply_text(msg)

# ADMIN: bloquear usuario
async def bloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 No tienes permiso para este comando.")
        return
    if not context.args:
        await update.message.reply_text("Uso: /bloquear <id_usuario>")
        return
    try:
        user_id = int(context.args[0])
        bloquear_usuario(user_id)
        await update.message.reply_text(f"⛔ Usuario {user_id} bloqueado.")
    except:
        await update.message.reply_text("⚠️ Error bloqueando usuario.")

# ADMIN: desbloquear usuario
async def desbloquear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("🚫 No tienes permiso para este comando.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /desbloquear <id_usuario> <username>")
        return
    try:
        user_id = int(context.args[0])
        username = context.args[1]
        desbloquear_usuario(user_id, username)
        await update.message.reply_text(f"✅ Usuario {user_id} desbloqueado.")
    except:
        await update.message.reply_text("⚠️ Error desbloqueando usuario.")

# ==============================
# MAIN
# ==============================
def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("registro", registro))

    # admin
    app.add_handler(CommandHandler("usuarios", usuarios))
    app.add_handler(CommandHandler("bloquear", bloquear))
    app.add_handler(CommandHandler("desbloquear", desbloquear))

    app.run_polling()

if __name__ == "__main__":
    main()