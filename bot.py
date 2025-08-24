import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ---------------------------
# CONFIGURACIÓN DEL BOT
# ---------------------------
TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # Reemplaza con tu ID de admin

# Base de datos en memoria
users = set()        # usuarios registrados
banned_users = {}    # {user_id: reason}

# Prefijos permitidos
PREFIXES = [".", "!", "?", "#", "/"]

# ---------------------------
# FUNCIONES DE REGISTRO
# ---------------------------
def is_banned(user_id: int) -> bool:
    return user_id in banned_users

def is_registered(user_id: int) -> bool:
    return user_id in users

# ---------------------------
# MENÚ PRINCIPAL
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.message.reply_text(f"🚫 Estás baneado.\nRazón: {banned_users[user_id]}")
        return

    # Registrar si no existe
    if not is_registered(user_id):
        users.add(user_id)
        await update.message.reply_text("✅ Te has registrado correctamente.")

    keyboard = [
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("🛠️ Tools", callback_data="tools")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        text="📍 Menú Principal:",
        reply_markup=reply_markup
    )

# ---------------------------
# CALLBACKS DE BOTONES
# ---------------------------
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if is_banned(user_id):
        await query.edit_message_text(f"🚫 Estás baneado.\nRazón: {banned_users[user_id]}")
        return

    # Menú Comida
    if query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text="🍕 Texto de comida.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Menú Películas
    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎥 Acción", callback_data="pelicula_accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="pelicula_comedia")],
            [InlineKeyboardButton("😱 Terror", callback_data="pelicula_terror")],
            [InlineKeyboardButton("🎭 Drama", callback_data="pelicula_drama")],
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text="🎬 Selecciona un tipo de película:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data in ["pelicula_accion", "pelicula_comedia", "pelicula_terror", "pelicula_drama"]:
        nombre = query.data.replace("pelicula_", "").capitalize()
        keyboard = [
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="peliculas")],
            [InlineKeyboardButton("🏠 Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text=f"🎥 Lista de películas de {nombre}.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Menú Tools
    elif query.data == "tools":
        keyboard = [
            [InlineKeyboardButton("⚡ Gates", callback_data="gates")],
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text="🛠️ Menú de Tools:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Menú Gates
    elif query.data == "gates":
        keyboard = [
            [InlineKeyboardButton("AUTH", callback_data="gate_auth")],
            [InlineKeyboardButton("CCN", callback_data="gate_ccn")],
            [InlineKeyboardButton("CHARGED", callback_data="gate_charged")],
            [InlineKeyboardButton("ESPECIAL", callback_data="gate_especial")],
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="tools")],
            [InlineKeyboardButton("🏠 Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text="⚡ Selecciona un Gate:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data.startswith("gate_"):
        nombre = query.data.replace("gate_", "").upper()
        keyboard = [
            [InlineKeyboardButton("↩️ Volver atrás", callback_data="gates")],
            [InlineKeyboardButton("🏠 Volver al menú principal", callback_data="menu_principal")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text=f"🔐 {nombre} Gate en desarrollo...",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Menú principal
    elif query.data == "menu_principal":
        keyboard = [
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("🛠️ Tools", callback_data="tools")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(
            text="📍 Menú Principal:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

# ---------------------------
# COMANDOS DE ADMIN
# ---------------------------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ Registrar usuario", callback_data="admin_registrar")],
        [InlineKeyboardButton("⛔ Banear usuario", callback_data="admin_banear")],
        [InlineKeyboardButton("♻️ Desbanear usuario", callback_data="admin_desbanear")],
        [InlineKeyboardButton("📋 Lista de usuarios", callback_data="admin_lista")],
    ]
    await update.message.reply_text(
        "⚙️ Panel de administración:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ No tienes permisos para usar el panel admin.")
        return

    if query.data == "admin_lista":
        text = "📋 Usuarios registrados:\n"
        text += "\n".join(f"• {u}" for u in users) or "📭 Ninguno"
        text += "\n\n🚫 Baneados:\n"
        text += "\n".join(f"• {u} (razón: {r})" for u, r in banned_users.items()) or "📭 Ninguno"
        await query.edit_message_text(text)

# ---------------------------
# MAIN
# ---------------------------
def main():
    logging.basicConfig(level=logging.INFO)

    app = Application.builder().token(TOKEN).build()

    # Start con prefijos
    for p in PREFIXES:
        app.add_handler(CommandHandler(f"{p}start", start))

    # Panel admin
    for p in PREFIXES:
        app.add_handler(CommandHandler(f"{p}admin", admin))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CallbackQueryHandler(admin_buttons))

    app.run_polling()

if __name__ == "__main__":
    main()