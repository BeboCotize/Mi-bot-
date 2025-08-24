import logging
import random
import requests
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8271445453:AAE4FX1Crb7sLJ4IkZ1O_5DB39c8XGHDpcc"   # ⚠️ Poner tu token real
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

def is_registered(user_id: int) -> bool:
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def register_user(user_id: int, username: str):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

# ==============================
# FUNCIONES DEL GENERADOR
# ==============================
def luhn_checksum(card_number):
    def digits_of(n): return [int(d) for d in str(n)]
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
        card = card[:16].ljust(16, str(random.randint(0, 9)))
        mes_gen = f"{random.randint(1,12):02d}" if mes in ["rnd", "xx"] else mes
        ano_gen = random.randint(2024, 2035) if ano in ["rnd", "xxxx"] else int(ano)
        cvv_gen = random.randint(100, 999) if cvv in ["rnd", "xxx", "xxxx"] else cvv
        if is_luhn_valid(card):
            ccs.append(f"{card}|{mes_gen}|{ano_gen}|{cvv_gen}")
    return ccs

def get_bin_info(bin_number: str) -> str:
    try:
        url = f"https://lookup.binlist.net/{bin_number}"
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
    user_id = update.effective_user.id
    username = update.effective_user.username or "SinUsername"

    if not is_registered(user_id):
        register_user(user_id, username)
        await update.message.reply_text("✅ Te has registrado con éxito!")

    keyboard = [
        [InlineKeyboardButton("TOOLS", callback_data="comida")],
        [InlineKeyboardButton("GATES", callback_data="peliculas")],
        [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Hola! Bienvenido a tu bot\n\nSelecciona una opción:",
        reply_markup=reply_markup
    )

# ==============================
# CALLBACKS
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_registered(update.effective_user.id):
        await query.edit_message_text("🚫 Debes registrarte usando /start")
        return

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
        await query.edit_message_text("🍔 Lista de comidas:\n- Pizza\n- Hamburguesa\n- Tacos",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "peliculas":
        keyboard = [
            [InlineKeyboardButton("AUTH", callback_data="accion")],
            [InlineKeyboardButton("CCN", callback_data="comedia")],
            [InlineKeyboardButton("CHARGED", callback_data="terror")],
            [InlineKeyboardButton("ESPECIAL", callback_data="romance")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text("🎬 Categorías de películas:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data in ["accion", "comedia", "terror", "romance"]:
        genero = query.data.capitalize()
        keyboard = [
            [InlineKeyboardButton("↩️ Volver a películas", callback_data="peliculas")],
            [InlineKeyboardButton("↩️ Volver al menú principal", callback_data="volver_menu")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        await query.edit_message_text(f"PRÓXIMAMENTE {genero}: AÚN NO HAY GATES.",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")
    elif query.data.startswith("regen|"):
        pattern, mes, ano, cvv = query.data.split("|")[1:]
        tarjetas = cc_gen(pattern, mes, ano, cvv)
        bin_info = get_bin_info(pattern[:6])
        text = "💳 Tarjetas generadas:\n\n" + "\n".join(tarjetas) + f"\n\n{bin_info}"
        keyboard = [[InlineKeyboardButton("🔄 Regenerar", callback_data=f"regen|{pattern}|{mes}|{ano}|{cvv}")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==============================
# GENERADOR
# ==============================
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_registered(update.effective_user.id):
        await update.message.reply_text("🚫 Debes registrarte usando /start")
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
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# ==============================
# PREFIJO CUSTOM
# ==============================
async def prefixed_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_router))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()

if __name__ == "__main__":
    main()