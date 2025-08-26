import os
import logging
import random
import string
import time
import requests  # se mantiene aunque no lo usemos, por compatibilidad
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

# Admins
ADMINS = [6629555218]  # <-- pon aquí tus IDs de admin

# Dominio público (puedes setear en ENV como WEBHOOK_URL)
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or f"https://mi-bot-bottoken.up.railway.app/{TOKEN}"

# ======================
# LOGGING
# ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ======================
# VARIABLES GLOBALES
# ======================
KEYS_DB = {}   # { "KEYCODE": fecha_expiracion_timestamp }
USERS_KEYS = {}  # { user_id: key }

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
# IMPORTAR GATE.PY
# ======================
import gate  # debe existir gate.py con la función process_card(tarjeta: str)

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

# ===============================
# 🔹 Nuevo comando .pay adaptado al gate.py
# ===============================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        # ✅ Verificar si el usuario tiene una key válida
        if user_id not in USERS_KEYS or USERS_KEYS[user_id] not in KEYS_DB:
            await update.message.reply_text("⛔ Necesitas reclamar una key válida con `.claim` antes de usar este comando.")
            return

        expira_en = KEYS_DB[USERS_KEYS[user_id]]
        if time.time() > expira_en:
            await update.message.reply_text("⛔ Tu key ya expiró.")
            return

        if not context.args:
            await update.message.reply_text("⚠️ Uso correcto: `.pay CC|MM|YYYY|CVV`")
            return

        tarjetas = context.args  # permite varias tarjetas separadas por espacio
        resultados = []

        regex_cc = re.compile(r"^(\d{15,16})\|((0[1-9])|(1[0-2]))\|(\d{4})\|(\d{3,4})$")

        for tarjeta in tarjetas:
            if not regex_cc.match(tarjeta):
                resultados.append(f"{tarjeta} → ⚠️ Formato inválido. Usa CC|MM|YYYY|CVV")
                continue

            try:
                resultado = gate.process_card(tarjeta)  # 🔹 se llama a gate.py
                resultados.append(f"{tarjeta} → {resultado}")
            except Exception as e:
                resultados.append(f"{tarjeta} → ❌ Error interno: {str(e)}")

        await update.message.reply_text("\n".join(resultados))

    except Exception as e:
        await update.message.reply_text(f"❌ Error en .pay: {str(e)}")

# ===============================
# CALLBACKS
# ===============================
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

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("pay", pay))   # ✅ cambiado a CommandHandler

    # Handlers de mensajes
    application.add_handler(MessageHandler(filters.Regex(r"^\.genkey(?:\s|$)"), genkey))
    application.add_handler(MessageHandler(filters.Regex(r"^\.gen(?:\s|$)"), gen))
    application.add_handler(MessageHandler(filters.Regex(r"^\.claim(?:\s|$)"), claim))

    application.add_handler(CallbackQueryHandler(button_callback))

    # Webhook config para Railway
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()