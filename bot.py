import os
import logging
import random
import string
import time
import requests
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8443))

ADMINS = [6629555218]

WEBHOOK_URL = os.getenv("WEBHOOK_URL") or f"https://mi-bot-bottoken.up.railway.app/{TOKEN}"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================
# VARIABLES GLOBALES
# ======================
KEYS_DB = {}
USERS_KEYS = {}

# ======================
# FUNCIONES AUXILIARES
# ======================
def generar_key(longitud: int = 16) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))

def formatear_tiempo_restante(expira_en: float) -> str:
    segundos = int(expira_en - time.time())
    if segundos <= 0:
        return "Expirada"
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60
    return f"{dias}d {horas}h {minutos}m restantes"

# ======================
# IMPORTAR GATE
# ======================
import gate  # asegúrate que gate.py tenga ccn_gate()

# ======================
# BINLIST API
# ======================
def get_bin_info(card_number: str):
    bin_number = card_number[:6]
    url = f"https://binlist.io/lookup/{bin_number}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        scheme = data.get("scheme", "").upper()
        tipo = data.get("type", "").upper()
        brand = f"{scheme} {tipo}".strip() if scheme or tipo else "N/A"

        banco = data.get("bank", {}).get("name", "N/A")
        country = data.get("country", {}).get("name", "N/A")
        flag = data.get("country", {}).get("emoji", "")

        return {
            "bin": brand,
            "bank": banco,
            "country": f"{country} {flag}".strip()
        }
    except Exception:
        return {"bin": "N/A", "bank": "N/A", "country": "N/A"}

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Bienvenido! Usa `.gen`, `.genkey`, `.claim` o `.pay` si tienes una key válida.")

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(" ", 1)
    if len(args) < 2:
        await update.message.reply_text("❌ Usa el comando correctamente: `.gen BIN|MM|YYYY|CVV`")
        return

    bin_data = args[1]
    response = f"{bin_data}123456|04|2027|127"

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ No tienes permisos para generar keys.")
        return

    args = update.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.message.reply_text("❌ Usa el comando correctamente: `.genkey días`")
        return

    dias = int(args[1])
    if dias < 1:
        await update.message.reply_text("❌ Los días deben ser mayor que 0.")
        return

    key = generar_key()
    expira_en = time.time() + dias * 86400
    KEYS_DB[key] = expira_en

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regenkey|{dias}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Key generada:\n{key}\n\n⏳ Expira en {dias} días.",
        reply_markup=reply_markup
    )

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Usa: `.claim KEY`")
        return

    key = args[1].strip().upper()
    if key not in KEYS_DB:
        await update.message.reply_text("❌ Key inválida o no existe.")
        return

    expira_en = KEYS_DB[key]
    if time.time() > expira_en:
        await update.message.reply_text("⛔ Esta key ya expiró.")
        return

    user_id = update.effective_user.id
    USERS_KEYS[user_id] = key

    tiempo_restante = formatear_tiempo_restante(expira_en)
    await update.message.reply_text(f"✨ Key válida y activada. {tiempo_restante}")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return
    await update.message.reply_text("✅ Bienvenido admin, puedes usar los comandos especiales.")

# ======================
# PAY HANDLER (sirve para /pay y .pay)
# ======================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if user_id not in USERS_KEYS or USERS_KEYS[user_id] not in KEYS_DB:
            await update.message.reply_text("⛔ Necesitas reclamar una key válida con `.claim` antes de usar este comando.")
            return

        expira_en = KEYS_DB[USERS_KEYS[user_id]]
        if time.time() > expira_en:
            await update.message.reply_text("⛔ Tu key ya expiró.")
            return

        text_input = update.message.text.strip()
        if text_input.startswith(".pay"):
            args = text_input.replace(".pay", "").strip().split()
        else:
            args = context.args

        if not args:
            await update.message.reply_text("⚠️ Uso correcto: `.pay CC|MM|YYYY|CVV`")
            return

        tarjeta = args[0]
        regex_cc = re.compile(r"^(\d{15,16})\|((0[1-9])|(1[0-2]))\|(\d{4})\|(\d{3,4})$")
        if not regex_cc.match(tarjeta):
            await update.message.reply_text(f"{tarjeta} → ⚠️ Formato inválido. Usa CC|MM|YYYY|CVV")
            return

        procesando_msg = await update.message.reply_text("⏳ Procesando, espera...")

        try:
            resultado = gate.ccn_gate(tarjeta)
            bin_info = get_bin_info(tarjeta.replace("|", ""))

            estado = "✅ Aprobada" if resultado["status"].lower() == "aprobada" else "❌ Declined"

            texto = f"""
💳 𝗥𝗘𝗦𝗨𝗟𝗧𝗔𝗗𝗢 𝗖𝗔𝗥𝗗

• 𝗧𝗮𝗿𝗷𝗲𝘁𝗮: {tarjeta}
• 𝗘𝘀𝘁𝗮𝗱𝗼: {estado}
• 𝗠𝗲𝗻𝘀𝗮𝗷𝗲: {resultado.get("message", "N/A")}
• 𝗖𝗼́𝗱𝗶𝗴𝗼: {resultado.get("code", "N/A")}

🏦 𝗕𝗔𝗡𝗖𝗢 𝗬 𝗣𝗔Í𝗦
• BIN: {bin_info['bin']}
• Banco: {bin_info['bank']}
• País: {bin_info['country']}

⏱ 𝗧𝗶𝗲𝗺𝗽𝗼: {resultado.get("time", "0.00 Segs")}
🔁 Reintentos: {resultado.get("tries", 1)}
"""
            await procesando_msg.edit_text(texto.strip())

        except Exception as e:
            await procesando_msg.edit_text(f"❌ Error interno: {str(e)}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error en .pay: {str(e)}")

# ======================
# CALLBACKS
# ======================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("regen|"):
        bin_data = query.data.split("|", 1)[1]
        results = "\n".join([f"{bin_data}{i}23456|04|2027|127" for i in range(10)])
        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(results, reply_markup=reply_markup)

    elif query.data.startswith("regenkey|"):
        dias = int(query.data.split("|", 1)[1])
        keys = []
        for _ in range(10):
            key = generar_key()
            expira_en = time.time() + dias * 86400
            KEYS_DB[key] = expira_en
            keys.append(f"{key} (⏳ {dias} días)")

        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regenkey|{dias}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("✅ Keys generadas:\n" + "\n".join(keys), reply_markup=reply_markup)

# ======================
# MAIN
# ======================
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("pay", pay))  # /pay
    application.add_handler(MessageHandler(filters.Regex(r"^\.pay(?:\s|$)"), pay))  # .pay

    application.add_handler(MessageHandler(filters.Regex(r"^\.genkey(?:\s|$)"), genkey))
    application.add_handler(MessageHandler(filters.Regex(r"^\.gen(?:\s|$)"), gen))
    application.add_handler(MessageHandler(filters.Regex(r"^\.claim(?:\s|$)"), claim))

    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()