import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from pathlib import Path

# ----------------- LOGGING -----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ----------------- TOKEN -----------------
TOKEN = os.getenv("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM")  # En Railway lo pasas como variable de entorno

# ----------------- BASE DE DATOS -----------------
DB_FILE = Path("users.json")

def load_db():
    if DB_FILE.exists():
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "banned": {}}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

db = load_db()

# ----------------- FUNCIONES DE USUARIO -----------------
def is_registered(user_id: int) -> bool:
    return str(user_id) in db["users"]

def is_banned(user_id: int) -> bool:
    return str(user_id) in db["banned"]

def register_user(user_id: int, username: str):
    db["users"][str(user_id)] = {"username": username}
    save_db(db)

def ban_user(user_id: int, reason: str):
    db["banned"][str(user_id)] = {"reason": reason}
    if str(user_id) in db["users"]:
        del db["users"][str(user_id)]
    save_db(db)

def unban_user(user_id: int):
    if str(user_id) in db["banned"]:
        del db["banned"][str(user_id)]
    save_db(db)

# ----------------- HANDLERS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if is_banned(user.id):
        reason = db["banned"][str(user.id)]["reason"]
        await update.message.reply_text(f"🚫 Estás baneado.\nMotivo: {reason}")
        return

    if not is_registered(user.id):
        register_user(user.id, user.username or user.first_name)
        await update.message.reply_text(f"✅ Bienvenido {user.first_name}, estás registrado.")

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Hola {user.first_name}, usa el menú de abajo:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comida":
        await query.edit_message_text("🍔 Aquí tienes comida deliciosa.\n\n🔙 Usa el menú para volver.")
    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎥 Acción", callback_data="accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
            [InlineKeyboardButton("😱 Terror", callback_data="terror")],
            [InlineKeyboardButton("🎭 Drama", callback_data="drama")],
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="volver")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text("🎬 Selecciona un género de películas:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "volver":
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text("⬅️ Has vuelto al menú principal.", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "cerrar":
        await query.delete_message()
    else:
        await query.edit_message_text(f"📌 Has elegido {query.data.capitalize()}.")

# ----------------- ADMIN -----------------
ADMIN_ID = 123456789  # pon tu ID de Telegram aquí

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    keyboard = [
        [InlineKeyboardButton("👥 Lista de usuarios", callback_data="list_users")],
        [InlineKeyboardButton("🚫 Banear", callback_data="ban")],
        [InlineKeyboardButton("♻️ Desbanear", callback_data="unban")]
    ]
    await update.message.reply_text("⚙️ Panel de administrador:", reply_markup=InlineKeyboardMarkup(keyboard))

# ----------------- MAIN -----------------
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler(["start", ".start"], start))
    application.add_handler(CommandHandler(["admin", ".admin"], admin))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()