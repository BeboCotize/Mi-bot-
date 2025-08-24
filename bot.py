import logging
import random
import requests
import sqlite3
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update
)
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
BOT_TOKEN = "8271445453:AAE4FX1Crb7sLJ4IkZ1O_5DB39c8XGHDpcc"   # ⚠️ Usa el token de BotFather
ADMIN_ID = 6629555218         # ID del admin
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
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            status TEXT DEFAULT 'registered'
        )
    """)
    conn.commit()
    conn.close()

def is_registered(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE id=? AND status='registered'", (user_id,))
    result = c.fetchone()
    conn.close()
    return bool(result)

def add_user(user_id, username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (id, username, status) VALUES (?, ?, 'registered')",
              (user_id, username))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def list_users():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username FROM users")
    result = c.fetchall()
    conn.close()
    return result

# ==============================
# FUNCIONES DEL GENERADOR
# ==============================
def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def is_luhn_valid(card_number) -> bool:
    return luhn_checksum(card_number) == 0

def cc_gen(pattern, mes="rnd", ano="rnd", cvv="rnd"):
    ccs = []
    while len(ccs) < 10:
        card = ""
        for ch in pattern:
            if ch == "x":
                card += str(random.randint(0, 9))
            else:
                card += ch

        if len(card) < 16:
            card += "".join(str(random.randint(0, 9)) for _ in range(16 - len(card)))

        card = card[:16]

        # Mes
        if mes in ["rnd", "xx"]:
            mes_gen = random.randint(1, 12)
            mes_gen = f"{mes_gen:02d}"
        else:
            mes_gen = mes

        # Año
        if ano in ["rnd", "xxxx"]:
            ano_gen = random.randint(2024, 2035)
        else:
            ano_gen = int(ano)

        # CVV
        if cvv in ["rnd", "xxx", "xxxx"]:
            cvv_gen = random.randint(100, 999)
        else:
            cvv_gen = cvv

        if is_luhn_valid(card):
            ccs.append(f"{card}|{mes_gen}|{ano_gen}|{cvv_gen}")
    return ccs

def get_bin_info(bin_number: str) -> str:
    try:
        url = f"https://binlist.io/lookup/{bin_number}/"
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return "❌ No se pudo obtener info del BIN"
        data = res.json()
        country = data.get("country", {}).get("name", "Desconocido")
        flag = data.get("country", {}).get("emoji", "")
        scheme = data.get("scheme", "N/A").upper()
        brand = data.get("brand", "N/A")
        card_type = data.get("type", "N/A").capitalize()
        currency = data.get("country", {}).get("currency", "N/A")

        return (f"🌍 BIN Info:\n"
                f"• País: {country} {flag}\n"
                f"• Esquema: {scheme}\n"
                f"• Clase: {brand}\n"
                f"• Tipo: {card_type}\n"
                f"• Moneda: {currency}")
    except Exception as e:
        return f"⚠️ Error obteniendo BIN info: {e}"

# ==============================
# MENSAJES PRINCIPALES
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_registered(user.id):
        await update.message.reply_text("🚫 No estás registrado. Contacta al admin.")
        return

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
    user = update.effective_user

    if not is_registered(user.id):
        await query.answer("🚫 No estás registrado", show_alert=True)
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
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="🎬 Categorías de películas:",
            reply_markup=reply_markup
        )

    elif query.data == "accion":
        keyboard = [
            [InlineKeyboardButton("↩️ Volver a películas", callback_data="peliculas")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="PRÓXIMAMENTE AUTH: AÚN NO HAY GATES.",
            reply_markup=reply_markup
        )

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

# ==============================
# GENERADOR
# ==============================
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_registered(user.id):
        await update.message.reply_text("🚫 No estás registrado.")
        return

    if not context.args:
        await update.message.reply_text("Uso: .gen 490129000329xxxx|10|2025|rnd")
        return

    try:
        raw = context.args[0]
        parts = raw.split("|")
        pattern = parts[0]
        mes = parts[1] if len(parts) > 1 else "rnd"
        ano = parts[2] if len(parts) > 2 else "rnd"
        cvv = parts[3] if len(parts) > 3 else "rnd"

        tarjetas = cc_gen(pattern, mes, ano, cvv)
        bin_info = get_bin_info(pattern[:6])

        text = "💳 Tarjetas generadas:\n\n" + "\n".join(tarjetas) + f"\n\n{bin_info}"
        keyboard = [[InlineKeyboardButton("🔄 Regenerar", callback_data=f"regen|{pattern}|{mes}|{ano}|{cvv}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ==============================
# ADMIN PANEL (sin botones)
# ==============================
async def add_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No eres admin.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /add_user <id>")
        return

    try:
        uid = int(context.args[0])
        username = f"user{uid}"
        add_user(uid, username)
        await update.message.reply_text(f"✅ Usuario {uid} agregado.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def del_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No eres admin.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /del_user <id>")
        return

    try:
        uid = int(context.args[0])
        delete_user(uid)
        await update.message.reply_text(f"🗑 Usuario {uid} eliminado.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

async def list_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 No eres admin.")
        return

    users = list_users()
    if not users:
        await update.message.reply_text("📭 No hay usuarios registrados.")
        return

    text = "👥 Usuarios registrados:\n" + "\n".join([f"{u[0]} ({u[1]})" for u in users])
    await update.message.reply_text(text)

# ==============================
# ROUTER DE PREFIJOS
# ==============================
async def prefixed_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    lower = text.lower()

    for p in PREFIXES:
        if lower.startswith(p + "start"):
            await start(update, context)
            return
        if lower.startswith(p + "gen"):
            args_str = lower[len(p + "gen"):].strip()
            context.args = args_str.split() if args_str else []
            await gen(update, context)
            return

# ==============================
# MAIN
# ==============================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Comandos oficiales
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("add_user", add_user_cmd))
    app.add_handler(CommandHandler("del_user", del_user_cmd))
    app.add_handler(CommandHandler("list_users", list_users_cmd))

    # Prefijos personalizados (. ! ? #)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_router))

    # Callbacks
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()