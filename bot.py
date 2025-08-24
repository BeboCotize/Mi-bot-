import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# --- CONFIGURACIÓN ---
TOKEN = os.getenv("8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw")  # Usa variable de entorno en Railway
ADMIN_ID =6629555218  # Reemplázalo con tu ID de admin

USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FUNCIONES DE ARCHIVOS ---
def load_data(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

users = load_data(USERS_FILE)
banned = load_data(BANNED_FILE)

# --- REGISTRO DE USUARIOS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # Verificar si está baneado
    if user_id in banned:
        reason = banned[user_id]
        await update.message.reply_text(
            f"🚫 Estás baneado y no puedes usar este bot.\n\n❌ Razón: {reason}"
        )
        return

    # Registrar usuario si no existe
    if user_id not in users:
        users[user_id] = user.username or user.full_name
        save_data(USERS_FILE, users)

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    text = f"👋 Hola, *{user.full_name}*.\nBienvenido al bot!"
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# --- BOTONES ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        keyboard = [
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "💥 Películas de acción explosivas y llenas de adrenalina.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "comedia":
        keyboard = [
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "😂 Películas de comedia para reír sin parar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "terror":
        keyboard = [
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "😱 Películas de terror que te harán temblar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "romance":
        keyboard = [
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            "💘 Películas románticas para los más enamorados.",
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

# --- PANEL ADMIN ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return

    text = "⚙️ Panel de administración:\n\n"
    text += "/admin_users - Lista de usuarios\n"
    text += "/admin_ban <user_id> <razón> - Banear usuario\n"
    text += "/admin_unban <user_id> - Desbanear usuario\n"

    await update.message.reply_text(text)

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    text = "📋 Usuarios registrados:\n\n"
    text += "\n".join(f"• {u} ({uid})" for uid, u in users.items()) or "📭 Ninguno"
    await update.message.reply_text(text)

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /admin_ban <user_id> <razón>")
        return
    user_id, reason = context.args[0], " ".join(context.args[1:])
    if user_id in users:
        banned[user_id] = reason
        save_data(BANNED_FILE, banned)
        await update.message.reply_text(f"🚫 Usuario {user_id} baneado.\nRazón: {reason}")
    else:
        await update.message.reply_text("⚠️ Usuario no encontrado.")

async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != str(ADMIN_ID):
        return
    if not context.args:
        await update.message.reply_text("Uso: /admin_unban <user_id>")
        return
    user_id = context.args[0]
    if user_id in banned:
        del banned[user_id]
        save_data(BANNED_FILE, banned)
        await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")
    else:
        await update.message.reply_text("⚠️ El usuario no estaba baneado.")

# --- MAIN ---
def main():
    application = Application.builder().token(TOKEN).build()

    # Comandos
    application.add_handler(CommandHandler(["start", ".start"], start))
    application.add_handler(CallbackQueryHandler(buttons))

    # Panel admin
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("admin_users", admin_users))
    application.add_handler(CommandHandler("admin_ban", admin_ban))
    application.add_handler(CommandHandler("admin_unban", admin_unban))

    application.run_polling()

if __name__ == "__main__":
    main()