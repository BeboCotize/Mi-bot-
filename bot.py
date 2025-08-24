import os
import sqlite3
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Base de datos SQLite
DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            banned INTEGER DEFAULT 0,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (user_id, username))
    conn.commit()
    conn.close()

def is_banned(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT banned, reason FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else (0, None)

def ban_user(user_id, reason="Sin razón"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET banned=1, reason=? WHERE user_id=?", (reason, user_id))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users SET banned=0, reason=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id, username, banned, reason FROM users")
    users = c.fetchall()
    conn.close()
    return users

# Panel admin (cambia tu ID aquí)
ADMIN_ID = 123456789

# Mensaje principal
def main_menu(username):
    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    return (
        f"👋 Bienvenido {username}!\n\n"
        "Usa el menú para navegar."
    ), InlineKeyboardMarkup(keyboard)

# Botón de películas
def peliculas_menu():
    keyboard = [
        [InlineKeyboardButton("🎥 Acción", callback_data="accion")],
        [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
        [InlineKeyboardButton("😱 Terror", callback_data="terror")],
        [InlineKeyboardButton("❤️ Romance", callback_data="romance")],
        [InlineKeyboardButton("⬅️ Volver atrás", callback_data="volver")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    return "🎬 Elige una categoría de películas:", InlineKeyboardMarkup(keyboard)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    banned, reason = is_banned(user.id)

    if banned:
        await update.message.reply_text(f"🚫 Estás baneado.\nRazón: {reason}")
        return

    add_user(user.id, user.username or "Sin username")
    text, keyboard = main_menu(user.first_name)
    await update.message.reply_text(text, reply_markup=keyboard)

# Panel admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = get_all_users()
    msg = "👑 Panel Admin\n\nUsuarios:\n"
    for u in users:
        status = "🚫 Baneado" if u[2] else "✅ Activo"
        reason = f" (Razón: {u[3]})" if u[3] else ""
        msg += f"• {u[1]} [{u[0]}] - {status}{reason}\n"
    await update.message.reply_text(msg or "📭 No hay usuarios")

# Ban user
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "Sin razón"
        ban_user(user_id, reason)
        await update.message.reply_text(f"🚫 Usuario {user_id} baneado.\nRazón: {reason}")
    except:
        await update.message.reply_text("Uso: .ban <user_id> <razón>")

# Unban user
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        unban_user(user_id)
        await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")
    except:
        await update.message.reply_text("Uso: .unban <user_id>")

# CallbackQueryHandler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if query.data == "peliculas":
        text, keyboard = peliculas_menu()
        await query.edit_message_text(text, reply_markup=keyboard)

    elif query.data == "volver":
        text, keyboard = main_menu(user.first_name)
        await query.edit_message_text(text, reply_markup=keyboard)

    elif query.data == "cerrar":
        await query.edit_message_text("❌ Conversación cerrada.")

    elif query.data in ["accion", "comedia", "terror", "romance"]:
        await query.edit_message_text(f"🎬 Has elegido *{query.data.capitalize()}*", parse_mode="Markdown")

# Main
def main():
    init_db()
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("⚠️ No se encontró BOT_TOKEN en las variables de entorno")

    application = Application.builder().token(TOKEN).build()

    # Handlers de start con prefijos
    for cmd in ["start", ".start", "!start", "?start"]:
        application.add_handler(CommandHandler(cmd, start))

    # Admin commands
    application.add_handler(CommandHandler(".admin", admin_panel))
    application.add_handler(CommandHandler(".ban", ban_command))
    application.add_handler(CommandHandler(".unban", unban_command))

    # Botones
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()