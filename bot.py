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
    return any(text.lower().startswith(p + cmd) for p in PREFIXES)

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
# 🔹 Handlers Usuario
# ============================
async def start_handler(update: Update, context):
    user = update.effective_user

    if is_banned(user.id):
        cursor.execute("SELECT reason FROM users WHERE user_id = ?", (user.id,))
        reason = cursor.fetchone()
        reason = reason[0] if reason else "Sin motivo"
        await update.message.reply_text(f"🚫 Estás baneado.\nMotivo: {reason}")
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
            "🍔 Aquí tienes comida deliciosa 🍕🌮🍩",
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

    elif query.data == "accion":
        await query.edit_message_text("💥 Películas de acción explosivas y llenas de adrenalina.")
    elif query.data == "comedia":
        await query.edit_message_text("😂 Películas de comedia para reír sin parar.")
    elif query.data == "terror":
        await query.edit_message_text("😱 Películas de terror que te harán temblar.")
    elif query.data == "romance":
        await query.edit_message_text("💘 Películas románticas para los más enamorados.")

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
# 🔹 Panel Admin
# ============================
async def ban(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Sin motivo"
        cursor.execute("UPDATE users SET banned = 1, reason = ? WHERE user_id = ?", (reason, user_id))
        conn.commit()
        await update.message.reply_text(f"✅ Usuario {user_id} baneado.\nMotivo: {reason}")
    except:
        await update.message.reply_text("⚠️ Uso: /ban <user_id> <motivo>")

async def unban(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        cursor.execute("UPDATE users SET banned = 0, reason = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")
    except:
        await update.message.reply_text("⚠️ Uso: /unban <user_id>")

async def users(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT user_id, name, banned FROM users")
    data = cursor.fetchall()
    if not data:
        await update.message.reply_text("📭 No hay usuarios registrados.")
        return
    text = "📋 Lista de usuarios:\n\n"
    for u in data:
        status = "🚫 Baneado" if u[2] == 1 else "✅ Activo"
        text += f"• {u[1]} ({u[0]}) - {status}\n"
    await update.message.reply_text(text)

async def broadcast(update: Update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("⚠️ Uso: /broadcast <mensaje>")
        return
    cursor.execute("SELECT user_id FROM users WHERE banned = 0")
    for (uid,) in cursor.fetchall():
        try:
            await context.bot.send_message(uid, f"📢 {msg}")
        except:
            pass
    await update.message.reply_text("✅ Mensaje enviado a todos los usuarios.")

# ============================
# 🔹 Main
# ============================
def main():
    app = Application.builder().token(TOKEN).build()

    # ✅ Start oficial
    app.add_handler(CommandHandler("start", start_handler))

    # ✅ Prefijos para start
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^[\.\?!#]start"), prefix_handler))

    # ✅ Botones
    app.add_handler(CallbackQueryHandler(buttons))

    # ✅ Comandos admin + prefijos
    for cmd, func in {
        "ban": ban, "unban": unban, "users": users, "broadcast": broadcast
    }.items():
        app.add_handler(CommandHandler(cmd, func))
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex(rf"^[\.\?!#]{cmd}"), func))

    logger.info("✅ Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()