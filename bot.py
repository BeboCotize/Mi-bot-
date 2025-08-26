import os
import logging
import random
import string
import time
import requests  # se mantiene aunque no lo usemos, por compatibilidad
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
# MOCK GATE (SIMULADO)
# ======================
def _luhn_ok(cc: str) -> bool:
    """Chequeo de Luhn para la tarjeta."""
    digits = [int(d) for d in cc if d.isdigit()]
    if len(digits) < 12:  # muy corta
        return False
    checksum = 0
    parity = (len(digits) - 2) % 2
    for i, d in enumerate(digits[:-1]):
        if i % 2 == parity:
            d = d * 2
            if d > 9:
                d -= 9
        checksum += d
    return (checksum + digits[-1]) % 10 == 0

def _exp_ok(mes: str, ano: str) -> bool:
    """Valida que no esté expirada (mes entre 1-12, año >= actual)."""
    try:
        m = int(mes)
        y = int(ano)
        if y < 100:  # permitir YY
            y += 2000
        if not (1 <= m <= 12):
            return False
        ahora = datetime.utcnow()
        # tarjeta válida hasta fin del mes
        vence = datetime(y, m, 28)  # día dummy suficiente para comparar mes/año
        return (y > ahora.year) or (y == ahora.year and m >= ahora.month)
    except Exception:
        return False

def _cvv_ok(cvv: str) -> bool:
    return cvv.isdigit() and (len(cvv) in (3, 4))

def gate(cc: str, mes: str, ano: str, cvv: str) -> str:
    """
    Gate simulado (no hace requests externos).
    Reglas:
    - Luhn inválido -> Declined (invalid number)
    - Expirada -> Declined (expired)
    - CVV mal formado -> Error en la tarjeta
    - Si todo ok, resultado determinista según últimos dígitos:
        * termina en 0/5 -> AVS FAILURE (aprobado parcial)
        * termina en 2/7 -> CVV2 MISMATCH (aprobado parcial)
        * termina en 4/8 -> Insufficient funds (decline)
        * otro -> Approved
    """
    cc = cc.strip().replace(" ", "")
    mes = mes.strip()
    ano = ano.strip()
    cvv = cvv.strip()

    if not _luhn_ok(cc):
        return "❌ Declined (invalid number)"

    if not _exp_ok(mes, ano):
        return "❌ Declined (expired)"

    if not _cvv_ok(cvv):
        return "⚠️ Error en la tarjeta (CVV)"

    # mapa determinista por último dígito
    last = int(cc[-1])
    if last in (0, 5):
        return "✅ Approved (AVS FAILURE)"
    if last in (2, 7):
        return "✅ Approved (CVV2 MISMATCH)"
    if last in (4, 8):
        return "❌ Declined (insufficient funds)"

    return "✅ Approved"

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

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS_KEYS or USERS_KEYS[user_id] not in KEYS_DB:
        await update.message.reply_text("⛔ Necesitas reclamar una key válida con `.claim`.")
        return

    expira_en = KEYS_DB[USERS_KEYS[user_id]]
    if time.time() > expira_en:
        await update.message.reply_text("⛔ Tu key ya expiró.")
        return

    args = update.message.text.split()
    if len(args) != 2 or "|" not in args[1]:
        await update.message.reply_text("❌ Usa: `.pay CC|MM|YYYY|CVV`")
        return

    try:
        cc, mes, ano, cvv = args[1].split("|")
        result = gate(cc, mes, ano, cvv)
        await update.message.reply_text(f"💳 Resultado: {result}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error al procesar: {e}")

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

    # Handlers de mensajes
    application.add_handler(MessageHandler(filters.Regex(r"^\.genkey(?:\s|$)"), genkey))
    application.add_handler(MessageHandler(filters.Regex(r"^\.gen(?:\s|$)"), gen))
    application.add_handler(MessageHandler(filters.Regex(r"^\.claim(?:\s|$)"), claim))
    application.add_handler(MessageHandler(filters.Regex(r"^\.pay(?:\s|$)"), pay))

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