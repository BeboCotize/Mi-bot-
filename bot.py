import logging
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"   # ⚠️ Reemplaza con tu token real
ADMIN_ID = 6629555218         # ID del admin principal
PREFIXES = [".", "!", "?", "#"]

# ==============================
# BASE DE DATOS
# ==============================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY, reason TEXT)")
conn.commit()

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def is_registered(user_id: int) -> bool:
    c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return c.fetchone() is not None

def is_banned(user_id: int) -> bool:
    c.execute("SELECT 1 FROM banned WHERE user_id=?", (user_id,))
    return c.fetchone() is not None

def register_user(user_id: int):
    if not is_registered(user_id):
        c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

# ==============================
# START
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if is_banned(uid):
        c.execute("SELECT reason FROM banned WHERE user_id=?", (uid,))
        reason = c.fetchone()
        reason = reason[0] if reason else "Sin razón especificada"
        await update.effective_message.reply_text(f"⛔ Estás baneado.\n📌 Razón: {reason}")
        return

    if not is_registered(uid):
        register_user(uid)
        await update.effective_message.reply_text("✅ Te has registrado correctamente.")

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

# ==============================
# CALLBACKS
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id

    if is_banned(uid):
        c.execute("SELECT reason FROM banned WHERE user_id=?", (uid,))
        reason = c.fetchone()
        reason = reason[0] if reason else "Sin razón especificada"
        await query.edit_message_text(f"⛔ Estás baneado.\n📌 Razón: {reason}")
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
        genero = query.data.capitalize()
        keyboard = [
            [InlineKeyboardButton("↩️ Volver a películas", callback_data="peliculas")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"📽️ {genero} → PRÓXIMAMENTE GATES.",
            reply_markup=reply_markup
        )

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

# ==============================
# ADMIN PANEL (CON PREFIJO)
# ==============================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, args: list):
    uid = update.effective_user.id
    if uid != ADMIN_ID:
        await update.effective_message.reply_text("🚫 No eres admin.")
        return

    if not args:
        text = "📋 Panel Admin\n\n"
        text += ".admin list → Lista de usuarios\n"
        text += ".admin ban <id> <razón> → Banear usuario con razón\n"
        text += ".admin unban <id> → Desbanear usuario\n"
        text += ".admin del <id> → Eliminar usuario (puede registrarse de nuevo)\n"
        await update.effective_message.reply_text(text)
        return

    cmd = args[0].lower()

    if cmd == "list":
        c.execute("SELECT user_id FROM users")
        users = c.fetchall()
        text = "👥 Usuarios registrados:\n"
        text += "\n".join(f"• {u[0]}" for u in users) or "📭 Ninguno"

        c.execute("SELECT user_id, reason FROM banned")
        banned = c.fetchall()
        text += "\n\n🚫 Baneados:\n"
        text += "\n".join(f"• {u[0]} → {u[1]}" for u in banned) or "📭 Ninguno"

        await update.effective_message.reply_text(text)

    elif cmd == "ban" and len(args) > 2:
        try:
            target = int(args[1])
            reason = " ".join(args[2:])
            c.execute("DELETE FROM users WHERE user_id=?", (target,))
            c.execute("INSERT OR REPLACE INTO banned (user_id, reason) VALUES (?, ?)", (target, reason))
            conn.commit()
            await update.effective_message.reply_text(
                f"⛔ Usuario {target} baneado.\n📌 Razón: {reason}"
            )
        except:
            await update.effective_message.reply_text("⚠️ ID inválido o error en el ban.")

    elif cmd == "unban" and len(args) > 1:
        try:
            target = int(args[1])
            c.execute("DELETE FROM banned WHERE user_id=?", (target,))
            conn.commit()
            await update.effective_message.reply_text(f"✅ Usuario {target} desbaneado.")
        except:
            await update.effective_message.reply_text("⚠️ ID inválido.")

    elif cmd == "del" and len(args) > 1:
        try:
            target = int(args[1])
            c.execute("DELETE FROM users WHERE user_id=?", (target,))
            conn.commit()
            await update.effective_message.reply_text(f"🗑️ Usuario {target} eliminado (puede registrarse de nuevo).")
        except:
            await update.effective_message.reply_text("⚠️ ID inválido.")

# ==============================
# ROUTER DE PREFIJOS PERSONALIZADOS
# ==============================
async def prefixed_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    lower = text.lower()
    uid = update.effective_user.id

    if is_banned(uid):
        c.execute("SELECT reason FROM banned WHERE user_id=?", (uid,))
        reason = c.fetchone()
        reason = reason[0] if reason else "Sin razón especificada"
        await update.effective_message.reply_text(f"⛔ Estás baneado.\n📌 Razón: {reason}")
        return

    if not is_registered(uid) and not lower.startswith(tuple(p + "start" for p in PREFIXES)):
        await update.effective_message.reply_text("🚫 No estás registrado. Usa .start para registrarte.")
        return

    for p in PREFIXES:
        if lower.startswith(p + "start"):
            await start(update, context)
            return
        if lower.startswith(p + "admin"):
            parts = text[len(p):].split()
            await admin_command(update, context, parts[1:])
            return

# ==============================
# MAIN
# ==============================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_router))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()