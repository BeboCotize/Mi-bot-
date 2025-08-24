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
BOT_TOKEN = "8271445453:AAFt-Hxd-YBlVWi5pRnAPhGcYPjvKILTNJw"
ADMIN_ID = 6629555218  # tu ID como admin
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
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
c.execute("CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)")
conn.commit()


def is_registered(user_id: int) -> bool:
    c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    return c.fetchone() is not None


def is_banned(user_id: int) -> bool:
    c.execute("SELECT 1 FROM banned WHERE user_id=?", (user_id,))
    return c.fetchone() is not None


def register_user(user_id: int) -> bool:
    if is_banned(user_id):
        return False
    if not is_registered(user_id):
        c.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
    return True


def delete_user(user_id: int):
    c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    c.execute("INSERT OR IGNORE INTO banned (user_id) VALUES (?)", (user_id,))
    conn.commit()


def get_all_users():
    c.execute("SELECT user_id FROM users")
    return [row[0] for row in c.fetchall()]


def get_all_banned():
    c.execute("SELECT user_id FROM banned")
    return [row[0] for row in c.fetchall()]


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
        checksum += sum(digits_of(d * 2))
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
        mes_gen = f"{random.randint(1,12):02d}" if mes in ["rnd", "xx"] else mes
        # Año
        ano_gen = random.randint(2024, 2035) if ano in ["rnd", "xxxx"] else int(ano)
        # CVV
        cvv_gen = random.randint(100, 999) if cvv in ["rnd", "xxx", "xxxx"] else cvv

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
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.effective_message.reply_text("🚫 Estás baneado y no puedes usar este bot.")
        return

    if not is_registered(user_id):
        await update.effective_message.reply_text("🔑 No estás registrado. Escribe /register para registrarte.")
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


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.effective_message.reply_text("🚫 Estás baneado y no puedes registrarte.")
        return
    if register_user(user_id):
        await update.effective_message.reply_text("✅ Registro exitoso. Ahora puedes usar el bot con .start")
    else:
        await update.effective_message.reply_text("⚠️ No se pudo registrar.")


# ==============================
# CALLBACKS
# ==============================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # MENU PRINCIPAL
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

    # COMIDA
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

    # PELICULAS (GATES)
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
            text="🎬 Categorías de Gates:",
            reply_markup=reply_markup
        )

    elif query.data == "accion":
        await query.edit_message_text("⚡ AUTH: Aquí irían las pruebas de autorización.")
    elif query.data == "comedia":
        await query.edit_message_text("💳 CCN: Aquí irían las pruebas de tarjetas sin saldo.")
    elif query.data == "terror":
        await query.edit_message_text("🔥 CHARGED: Aquí irían las pruebas con cargos reales.")
    elif query.data == "romance":
        await query.edit_message_text("✨ ESPECIAL: Aquí irían gates únicos o raros.")

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")


# ==============================
# GENERADOR
# ==============================
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id) or is_banned(user_id):
        await update.effective_message.reply_text("🚫 No puedes usar este comando.")
        return

    if not context.args:
        await update.effective_message.reply_text("Uso: .gen 490129000329xxxx|10|2025|rnd")
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

        await update.effective_message.reply_text(text, reply_markup=reply_markup)

    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Error: {e}")


# ==============================
# PANEL ADMIN
# ==============================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.effective_message.reply_text("🚫 No tienes permiso.")
        return

    args = context.args
    if not args:
        text = "📊 Panel Admin\n\nComandos disponibles:\n"
        text += "/admin users → Lista de usuarios\n"
        text += "/admin banned → Lista de baneados\n"
        text += "/admin del <id> → Banear usuario\n"
        await update.effective_message.reply_text(text)
        return

    cmd = args[0]
    if cmd == "users":
        users = get_all_users()
        text = "👥 Usuarios registrados:\n"
        text += "\n".join(f"• {u}" for u in users) or "📭 Ninguno"
        await update.effective_message.reply_text(text)

    elif cmd == "banned":
        banned = get_all_banned()
        text = "🚫 Usuarios baneados:\n"
        text += "\n".join(f"• {b}" for b in banned) or "📭 Ninguno"
        await update.effective_message.reply_text(text)

    elif cmd == "del" and len(args) > 1:
        try:
            uid = int(args[1])
            delete_user(uid)
            await update.effective_message.reply_text(f"✅ Usuario {uid} eliminado y baneado.")
        except:
            await update.effective_message.reply_text("⚠️ ID inválido.")
    else:
        await update.effective_message.reply_text("⚠️ Comando inválido.")


# ==============================
# ROUTER DE PREFIJOS PERSONALIZADOS
# ==============================
async def prefixed_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.effective_message.text or "").strip()
    lower = text.lower()
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.effective_message.reply_text("🚫 Estás baneado.")
        return
    if not is_registered(user_id) and not lower.startswith((".register", "/register")):
        await update.effective_message.reply_text("🔑 No estás registrado. Usa /register")
        return

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
    app = Application.builder().token(BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("admin", admin))

    # Prefijos personalizados
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prefixed_router))

    # Callbacks
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()


if __name__ == "__main__":
    main()