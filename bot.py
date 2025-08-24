# bot.py
import os
import sqlite3
import logging
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ============ CONFIG ============
ADMIN_ID = 6629555218  # Tu ID

DB_PATH = "users.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("bot")

# ============ DB ============

def db_connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db_connect()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered INTEGER DEFAULT 0,
            banned INTEGER DEFAULT 0,
            reason TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id: int):
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, registered, banned, reason, created_at FROM users WHERE user_id=?",
              (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def add_or_update_user(user_id: int, username: str, first_name: str):
    now = datetime.utcnow().isoformat()
    conn = db_connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (user_id, username, first_name, registered, banned, reason, created_at)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name
    """, (user_id, username, first_name, 0, 0, None, now))
    conn.commit()
    conn.close()

def set_registered(user_id: int):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET registered=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def set_ban(user_id: int, reason: str = "Sin razón"):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET banned=1, reason=? WHERE user_id=?", (reason, user_id))
    conn.commit()
    conn.close()

def unset_ban(user_id: int):
    conn = db_connect()
    c = conn.cursor()
    c.execute("UPDATE users SET banned=0, reason=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

def stats():
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE registered=1")
    registered = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE banned=1")
    banned = c.fetchone()[0]
    conn.close()
    return total, registered, banned

def list_recent(limit=10):
    conn = db_connect()
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, registered, banned FROM users ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ============ UI Helpers ============

def keyboard_main():
    kb = [
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")],
    ]
    return InlineKeyboardMarkup(kb)

def keyboard_peliculas():
    kb = [
        [InlineKeyboardButton("🎥 Acción", callback_data="pelis_accion")],
        [InlineKeyboardButton("😂 Comedia", callback_data="pelis_comedia")],
        [InlineKeyboardButton("😱 Terror", callback_data="pelis_terror")],
        [InlineKeyboardButton("❤️ Romance", callback_data="pelis_romance")],
        [InlineKeyboardButton("⬅️ Volver atrás", callback_data="volver_peliculas_atras")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="volver_menu")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")],
    ]
    return InlineKeyboardMarkup(kb)

def keyboard_submenu():
    kb = [
        [InlineKeyboardButton("⬅️ Volver atrás", callback_data="peliculas")],
        [InlineKeyboardButton("🏠 Menú principal", callback_data="volver_menu")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")],
    ]
    return InlineKeyboardMarkup(kb)

def main_text(first_name: str) -> str:
    return (
        f"👋 ¡Bienvenido {first_name}!\n\n"
        "Usa el menú para navegar."
    )

# ============ Guards ============

def ensure_registered(user_id: int):
    """Devuelve (ok: bool, msg_error: str|None, banned: bool, reason: str|None)"""
    row = get_user(user_id)
    if not row:
        return False, "⚠️ Primero usa /start para registrarte.", False, None
    _, _, _, registered, banned, reason, _ = row
    if banned:
        return False, f"🚫 Estás baneado y no puedes usar el bot.\nRazón: {reason}", True, reason
    if not registered:
        return False, "⚠️ No estás registrado. Usa /start para registrarte.", False, None
    return True, None, False, None

# ============ Handlers ============

# /start (oficial, sin prefijos)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    uname = user.username or "sin_username"
    fname = user.first_name or "Usuario"

    # Crea/actualiza registro
    add_or_update_user(uid, uname, fname)
    row = get_user(uid)
    _, _, _, registered, banned, reason, _ = row

    if banned:
        await update.effective_message.reply_text(f"🚫 Estás baneado y no puedes usar el bot.\nRazón: {reason}")
        return

    if not registered:
        set_registered(uid)

    await update.effective_message.reply_text(main_text(fname), reply_markup=keyboard_main())

# Admin panel (/admin o .admin)
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    total, registered, banned = stats()
    rows = list_recent()
    recent = "\n".join(
        f"• {r[2] or 'Usuario'} (@{r[1] or 'sin_username'}) [{r[0]}] - "
        f"{'✅ Reg' if r[3] else '❌ NoReg'} | {'🚫 Ban' if r[4] else '🟢 OK'}"
        for r in rows
    ) or "—"
    msg = (
        "👑 *Panel Admin*\n\n"
        f"👥 Total usuarios: *{total}*\n"
        f"📝 Registrados: *{registered}*\n"
        f"⛔ Baneados: *{banned}*\n\n"
        f"🕒 Recientes:\n{recent}\n\n"
        "Comandos:\n"
        "`/ban <id> <razón>` o `.ban <id> <razón>`\n"
        "`/unban <id>` o `.unban <id>`"
    )
    await update.effective_message.reply_text(msg, parse_mode="Markdown")

# Ban (/ban o .ban)
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.effective_message.reply_text("Uso: /ban <user_id> <razón>\nTambién: .ban <user_id> <razón>")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("El user_id debe ser numérico.")
        return
    reason = " ".join(args[1:]) or "Sin razón"
    # Si el usuario no existe aún en DB, crearlo como no registrado pero baneado
    row = get_user(target_id)
    if not row:
        add_or_update_user(target_id, "sin_username", "Usuario")
    set_ban(target_id, reason)
    await update.effective_message.reply_text(f"🚫 Usuario `{target_id}` baneado.\nRazón: {reason}", parse_mode="Markdown")

# Unban (/unban o .unban)
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return
    args = context.args
    if not args:
        await update.effective_message.reply_text("Uso: /unban <user_id>\nTambién: .unban <user_id>")
        return
    try:
        target_id = int(args[0])
    except ValueError:
        await update.effective_message.reply_text("El user_id debe ser numérico.")
        return
    unset_ban(target_id)
    await update.effective_message.reply_text(f"✅ Usuario `{target_id}` desbaneado.", parse_mode="Markdown")

# Router para prefijos con punto (.admin .ban .unban)
async def dot_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    lower = text.lower()

    # .admin
    if lower.startswith(".admin"):
        await admin_command(update, context)
        return

    # .ban
    if lower.startswith(".ban"):
        if update.effective_user.id != ADMIN_ID:
            return
        # parse manual
        parts = text.split()
        if len(parts) < 2:
            await update.effective_message.reply_text("Uso: .ban <user_id> <razón>")
            return
        try:
            target_id = int(parts[1])
        except ValueError:
            await update.effective_message.reply_text("El user_id debe ser numérico.")
            return
        reason = " ".join(parts[2:]) or "Sin razón"
        row = get_user(target_id)
        if not row:
            add_or_update_user(target_id, "sin_username", "Usuario")
        set_ban(target_id, reason)
        await update.effective_message.reply_text(f"🚫 Usuario `{target_id}` baneado.\nRazón: {reason}", parse_mode="Markdown")
        return

    # .unban
    if lower.startswith(".unban"):
        if update.effective_user.id != ADMIN_ID:
            return
        parts = text.split()
        if len(parts) < 2:
            await update.effective_message.reply_text("Uso: .unban <user_id>")
            return
        try:
            target_id = int(parts[1])
        except ValueError:
            await update.effective_message.reply_text("El user_id debe ser numérico.")
            return
        unset_ban(target_id)
        await update.effective_message.reply_text(f"✅ Usuario `{target_id}` desbaneado.", parse_mode="Markdown")
        return

# Películas (acceso por botón, pero también podemos abrir con texto .pelis si quieres)
async def pelis_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permite abrir el menú de películas con .pelis (opcional)."""
    text = (update.effective_message.text or "").strip()
    if not text.lower().startswith(".pelis"):
        return
    ok, msg, banned, reason = ensure_registered(update.effective_user.id)
    if not ok:
        await update.effective_message.reply_text(msg)
        return
    await update.effective_message.reply_text("🎬 Elige una categoría de películas:", reply_markup=keyboard_peliculas())

# Callbacks (navegación por botones)
async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    # Guard de acceso
    ok, msg, banned, reason = ensure_registered(user.id)
    if not ok:
        await query.edit_message_text(msg)
        return

    data = query.data

    if data == "peliculas":
        await query.edit_message_text("🎬 Elige una categoría de películas:", reply_markup=keyboard_peliculas())
        return

    if data == "volver_peliculas_atras":
        # Vuelve al texto de películas (no al principal)
        await query.edit_message_text("🎬 Elige una categoría de películas:", reply_markup=keyboard_peliculas())
        return

    if data == "volver_menu":
        await query.edit_message_text(main_text(user.first_name or "Usuario"), reply_markup=keyboard_main())
        return

    if data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")
        return

    # Submenús de películas
    textos = {
        "pelis_accion": "💥 *Acción*\n- Misión Imposible\n- John Wick\n- Mad Max: Fury Road",
        "pelis_comedia": "😂 *Comedia*\n- Superbad\n- The Mask\n- The Hangover",
        "pelis_terror":  "😱 *Terror*\n- The Conjuring\n- It\n- Hereditary",
        "pelis_romance": "❤️ *Romance*\n- La La Land\n- The Notebook\n- Pride & Prejudice",
    }
    if data in textos:
        await query.edit_message_text(textos[data], reply_markup=keyboard_submenu(), parse_mode="Markdown")
        return

# ============ MAIN ============

def main():
    init_db()

    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("⚠️ No se encontró BOT_TOKEN en las variables de entorno")

    application = Application.builder().token(TOKEN).build()

    # Comando oficial /start (sin prefijos)
    application.add_handler(CommandHandler("start", start))

    # Admin (slash)
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("ban", ban_command))
    application.add_handler(CommandHandler("unban", unban_command))

    # Prefijos "." para admin & herramientas
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dot_router))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, pelis_text))  # opcional .pelis

    # Botones (callback queries)
    application.add_handler(CallbackQueryHandler(callbacks))

    application.run_polling()

if __name__ == "__main__":
    main()