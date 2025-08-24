import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# =====================
# CONFIGURACIÓN
# =====================
TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # <-- pon tu ID de Telegram

# Bases de datos en memoria
registered_users = {}
banned_users = {}

# =====================
# LOGS
# =====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# =====================
# FUNCIONES AUXILIARES
# =====================
def is_registered(user_id):
    return user_id in registered_users and user_id not in banned_users

def get_prefixes():
    return [".", "/", "!", "?", "#"]

# =====================
# COMANDO START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name

    if user_id in banned_users:
        reason = banned_users[user_id]
        await update.message.reply_text(f"🚫 Estás baneado del bot.\nMotivo: {reason}")
        return

    if not is_registered(user_id):
        registered_users[user_id] = name
        text = f"✅ Te has registrado {name}, ahora puedes usar el bot.\n\n📍 Menú Principal:"
    else:
        text = "📍 Menú Principal:"

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=reply_markup)

# =====================
# CALLBACKS DE MENÚ
# =====================
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comida":
        text = "🍔 Aquí tienes el menú de comida"
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "peliculas":
        text = "🎬 Menú de películas"
        keyboard = [
            [InlineKeyboardButton("🎥 Acción", callback_data="pelicula_accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="pelicula_comedia")],
            [InlineKeyboardButton("😢 Drama", callback_data="pelicula_drama")],
            [InlineKeyboardButton("👻 Terror", callback_data="pelicula_terror")],
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pelicula_"):
        tipo = query.data.split("_")[1]
        text = f"🎥 Lista de películas de {tipo.capitalize()}"
        keyboard = [
            [InlineKeyboardButton("⬅️ Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("⬅️ Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "menu_principal":
        text = "📍 Menú Principal:"
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cerrar":
        await query.delete_message()

# =====================
# ADMIN
# =====================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    text = (
        "👑 Panel de administración:\n\n"
        "• Prefijos: . / ! ? #\n"
        "• Comandos disponibles:\n"
        "   .ban <id> <razón>\n"
        "   .unban <id>\n"
        "   .users"
    )
    await update.message.reply_text(text)

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "Sin especificar"
        banned_users[user_id] = reason
        if user_id in registered_users:
            del registered_users[user_id]
        await update.message.reply_text(f"🚫 Usuario {user_id} baneado.\nRazón: {reason}")
    except:
        await update.message.reply_text("Uso: .ban <id_usuario> <razón>")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        if user_id in banned_users:
            del banned_users[user_id]
            await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")
        else:
            await update.message.reply_text("Ese usuario no estaba baneado.")
    except:
        await update.message.reply_text("Uso: .unban <id_usuario>")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    text = "👥 Usuarios registrados:\n"
    text += "\n".join(f"• {u}" for u in registered_users.values()) or "📭 Ninguno"
    await update.message.reply_text(text)

# =====================
# MAIN
# =====================
def main():
    application = Application.builder().token(TOKEN).build()

    # Comandos con prefijos
    prefixes = get_prefixes()
    for prefix in prefixes:
        application.add_handler(CommandHandler(f"{prefix}start", start))
        application.add_handler(CommandHandler(f"{prefix}admin", admin))
        application.add_handler(CommandHandler(f"{prefix}ban", ban))
        application.add_handler(CommandHandler(f"{prefix}unban", unban))
        application.add_handler(CommandHandler(f"{prefix}users", list_users))

    # CallbackQuery
    application.add_handler(CallbackQueryHandler(menu_handler))

    application.run_polling()

if __name__ == "__main__":
    main()