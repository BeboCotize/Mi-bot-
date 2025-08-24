import os
import logging
import psycopg2
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# ------------------------------
# CONFIG
# ------------------------------
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)

TOKEN = os.getenv("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM")
ADMIN_ID = 6629555218  # Tu ID

DB_URL = os.getenv("DATABASE_URL")

# Conexión a PostgreSQL
conn = psycopg2.connect(DB_URL, sslmode="require")
cur = conn.cursor()

# Crear tablas si no existen
cur.execute("""
CREATE TABLE IF NOT EXISTS bans (
    user_id BIGINT PRIMARY KEY,
    reason TEXT,
    until TIMESTAMP
);
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS gens (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
""")
conn.commit()

# Control anti-spam (memoria)
user_activity = {}

# ------------------------------
# Funciones DB
# ------------------------------
def ban_user(user_id: int, reason: str, hours: int):
    until = datetime.utcnow() + timedelta(hours=hours)
    cur.execute("INSERT INTO bans (user_id, reason, until) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO UPDATE SET reason = EXCLUDED.reason, until = EXCLUDED.until",
                (user_id, reason, until))
    conn.commit()

def unban_user(user_id: int):
    cur.execute("DELETE FROM bans WHERE user_id = %s", (user_id,))
    conn.commit()

def is_banned(user_id: int):
    cur.execute("SELECT until FROM bans WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        until = row[0]
        if until > datetime.utcnow():
            return True
        else:
            unban_user(user_id)  # expiro
    return False

def save_gen(user_id: int):
    cur.execute("INSERT INTO gens (user_id) VALUES (%s)", (user_id,))
    conn.commit()

# ------------------------------
# Anti-Spam Middleware
# ------------------------------
async def check_spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.utcnow()

    if is_banned(user_id):
        await update.message.reply_text("🚫 Estás baneado temporalmente por spam.")
        return False

    # Registrar actividad
    history = user_activity.get(user_id, [])
    history = [t for t in history if (now - t).seconds < 30]  # solo últimos 30s
    history.append(now)
    user_activity[user_id] = history

    if len(history) > 20:
        ban_user(user_id, "Spam de comandos", 5)  # 5 horas
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⚠️ Usuario {user_id} baneado por spam (5h)."
        )
        await update.message.reply_text("🚫 Has sido bloqueado por spam (5 horas).")
        return False

    return True

# ------------------------------
# START
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_banned(update.effective_user.id):
        return await update.message.reply_text("🚫 Estás baneado temporalmente.")

    keyboard = [
        [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
        [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    await update.message.reply_text(
        f"👋 Hola {update.effective_user.first_name}, bienvenido al bot!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ------------------------------
# Botones
# ------------------------------
async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("🎥 Acción", callback_data="accion")],
            [InlineKeyboardButton("😂 Comedia", callback_data="comedia")],
            [InlineKeyboardButton("😭 Drama", callback_data="drama")],
            [InlineKeyboardButton("👽 Ciencia Ficción", callback_data="scifi")],
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="menu")],
        ]
        await query.edit_message_text("📂 Categoría: Películas", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "accion":
        await query.edit_message_text("💥 Recomendación de películas de Acción:\n- John Wick\n- Misión Imposible\n- Mad Max Fury Road")

    elif query.data == "comedia":
        await query.edit_message_text("😂 Recomendación de películas de Comedia:\n- ¿Qué pasó ayer?\n- Superbad\n- Scary Movie")

    elif query.data == "drama":
        await query.edit_message_text("😭 Recomendación de películas de Drama:\n- El Padrino\n- En busca de la felicidad\n- La lista de Schindler")

    elif query.data == "scifi":
        await query.edit_message_text("👽 Recomendación de películas de Ciencia Ficción:\n- Matrix\n- Star Wars\n- Interstellar")

    elif query.data == "comida":
        keyboard = [
            [InlineKeyboardButton("🍕 Pizza", callback_data="pizza")],
            [InlineKeyboardButton("🍔 Hamburguesa", callback_data="hamburguesa")],
            [InlineKeyboardButton("🍣 Sushi", callback_data="sushi")],
            [InlineKeyboardButton("🔙 Volver atrás", callback_data="menu")],
        ]
        await query.edit_message_text("📂 Categoría: Comida", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "pizza":
        await query.edit_message_text("🍕 Pizza: deliciosa con queso y pepperoni.")
    elif query.data == "hamburguesa":
        await query.edit_message_text("🍔 Hamburguesa: clásica con carne y papas.")
    elif query.data == "sushi":
        await query.edit_message_text("🍣 Sushi: fresco y saludable.")

    elif query.data == "menu":
        keyboard = [
            [InlineKeyboardButton("🎬 Películas", callback_data="peliculas")],
            [InlineKeyboardButton("🍔 Comida", callback_data="comida")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text("🏠 Menú principal", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

# ------------------------------
# Generador
# ------------------------------
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_spam(update, context):
        return

    save_gen(update.effective_user.id)
    await update.message.reply_text("💳 Generador: [Tarjeta Ficticia] 1234-5678-9012-3456")

# ------------------------------
# BAN / UNBAN (solo admin)
# ------------------------------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permiso.")

    try:
        user_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "Sin razón"
        ban_user(user_id, reason, 9999)  # prácticamente permanente
        await update.message.reply_text(f"✅ Usuario {user_id} baneado.\n📝 Razón: {reason}")
    except:
        await update.message.reply_text("⚠️ Uso: /ban <user_id> <razón>")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 No tienes permiso.")

    try:
        user_id = int(context.args[0])
        unban_user(user_id)
        await update.message.reply_text(f"✅ Usuario {user_id} desbaneado.")
    except:
        await update.message.reply_text("⚠️ Uso: /unban <user_id>")

# ------------------------------
# MAIN
# ------------------------------
def main():
    if not TOKEN:
        raise ValueError("⚠️ No se encontró BOT_TOKEN en las variables de entorno")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CallbackQueryHandler(botones))

    app.run_polling()

if __name__ == "__main__":
    main()