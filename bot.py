import logging
import sqlite3
import random
import requests
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
BOT_TOKEN = "8271445453:AAE4FX1Crb7sLJ4IkZ1O_5DB39c8XGHDpcc"   # ⚠️ cambia esto
ADMINS = [6629555218]          # <-- tu user_id de Telegram
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
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, username FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

def del_user(user_id: int):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ==============================
# GENERADOR DE TARJETAS
# ==============================
def cc_gen(pattern, mes="rnd", ano="rnd", cvv="rnd"):
    ccs = []
    while len(ccs) < 5:
        card = ""
        for ch in pattern:
            card += str(random.randint(0, 9)) if ch == "x" else ch
        card = card[:16]
        mes_gen = f"{random.randint(1,12):02d}" if mes == "rnd" else mes
        ano_gen = random.randint(2024, 2035) if ano == "rnd" else ano
        cvv_gen = random.randint(100, 999) if cvv == "rnd" else cvv
        ccs.append(f"{card}|{mes_gen}|{ano_gen}|{cvv_gen}")
    return ccs

# ==============================
# START / REGISTRO
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username or "")
    keyboard = [
        [InlineKeyboardButton("TOOLS", callback_data="tools")],
        [InlineKeyboardButton("GATES", callback_data="gates")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "👋 Bienvenido! Selecciona una opción:"
    if user.id in ADMINS:
        text += "\n\n⚙️ *Panel Admin disponible con comandos:*\n" \
                "- /ver_usuarios\n" \
                "- /broadcast <mensaje>\n" \
                "- /del_user <id>\n"

    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==============================
# CALLBACKS MENU
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "volver_menu":
        await start(update, context)

    elif query.data == "tools":
        keyboard = [
            [InlineKeyboardButton("↩️ Menú principal", callback_data="volver_menu")],
        ]
        await query.edit_message_text("🛠 Aquí irían tus herramientas", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "gates":
        keyboard = [
            [InlineKeyboardButton("Auth", callback_data="auth")],
            [InlineKeyboardButton("↩️ Menú principal", callback_data="volver_menu")],
        ]
        await query.edit_message_text("🎬 Categorías GATES:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cerrar":
        await query.delete_message()

# ==============================
# COMANDOS ADMIN
# ==============================
async def ver_usuarios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("🚫 No tienes permisos.")
    users = get_users()
    if not users:
        await update.message.reply_text("📭 No hay usuarios registrados.")
    else:
        msg = "👥 Usuarios:\n" + "\n".join([f"• {uid} | @{uname}" for uid, uname in users])
        await update.message.reply_text(msg)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("🚫 No tienes permisos.")
    if not context.args:
        return await update.message.reply_text("Uso: /broadcast <mensaje>")
    msg = " ".join(context.args)
    users = get_users()
    count = 0
    for uid, _ in users:
        try:
            await context.bot.send_message(uid, f"📢 {msg}")
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Mensaje enviado a {count} usuarios.")

async def del_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        return await update.message.reply_text("🚫 No tienes permisos.")
    if not context.args:
        return await update.message.reply_text("Uso: /del_user <id>")
    try:
        uid = int(context.args[0])
        del_user(uid)
        await update.message.reply_text(f"🗑 Usuario {uid} eliminado.")
    except:
        await update.message.reply_text("❌ ID inválido.")

# ==============================
# MAIN
# ==============================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler([p + "start" for p in PREFIXES], start))
    app.add_handler(CommandHandler("ver_usuarios", ver_usuarios))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("del_user", del_user_cmd))
    app.add_handler(CallbackQueryHandler(button))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()