import os
import logging
import random
import string
import time
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

# ======================
# FUNCIONES AUXILIARES (keys)
# ======================
def generar_key(longitud: int = 16) -> str:
    """Genera una key aleatoria de letras y números."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))

def formatear_tiempo_restante(expira_en: float) -> str:
    """Devuelve texto legible del tiempo restante."""
    segundos = int(expira_en - time.time())
    if segundos <= 0:
        return "Expirada"
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60
    return f"{dias}d {horas}h {minutos}m restantes"

# ======================
# FUNCIONES AUXILIARES (tarjetas)
# ======================
def luhn_checksum(num_str: str) -> int:
    """Regresa el checksum Luhn de un número."""
    total = 0
    reverse = num_str[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:  # duplicar cada segundo dígito (contando desde 0)
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10

def luhn_digit(num_without_check: str) -> int:
    """Calcula el dígito verificador Luhn para 'num_without_check'."""
    checksum = luhn_checksum(num_without_check + "0")
    return (10 - checksum) % 10

def completar_pan_con_luhn(pan_pattern: str) -> str:
    """
    Completa un patrón con 'x' y ajusta Luhn.
    Ej: '451769865014xxxx' -> '4517698650141234' (válida por Luhn).
    """
    # Rellenar todas las 'x' con dígitos aleatorios
    provisional = ""
    for ch in pan_pattern:
        if ch.lower() == "x":
            provisional += str(random.randint(0, 9))
        else:
            provisional += ch

    # Si el último carácter del patrón era 'x', lo ajustamos al dígito Luhn correcto
    if pan_pattern and pan_pattern[-1].lower() == "x":
        base = provisional[:-1]
        check = luhn_digit(base)
        return base + str(check)

    # Si el último no era 'x', intentamos hasta que salga un número válido por Luhn
    # (reemplazando 'x' internos) para no alterar el último fijo.
    for _ in range(25):
        provisional = ""
        for i, ch in enumerate(pan_pattern):
            if ch.lower() == "x":
                provisional += str(random.randint(0, 9))
            else:
                provisional += ch
        if luhn_checksum(provisional) == 0:
            return provisional

    # Como último recurso, devolvemos el provisional (aunque no cumpla Luhn)
    return provisional

def generar_tarjeta_desde_patron(pattern: str) -> str | None:
    """
    Genera una tarjeta a partir de un patrón tipo:
      '451769865014xxxx|05|2031|rnd'
    Devuelve 'PAN|MM|YYYY|CVV'
    """
    parts = pattern.split("|")
    if len(parts) != 4:
        return None

    pan_pattern, mes, anio, cvv_fmt = parts

    # PAN válido por Luhn
    pan = completar_pan_con_luhn(pan_pattern)

    # Mes / Año tal como vienen (se asume válidos)
    mm = mes
    yyyy = anio

    # CVV aleatorio si es 'rnd'
    if cvv_fmt.lower() == "rnd":
        cvv = f"{random.randint(100, 999)}"
    else:
        cvv = cvv_fmt

    return f"{pan}|{mm}|{yyyy}|{cvv}"

# ======================
# HANDLERS
# ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Bienvenido! Usa `.gen`, `.genkey`, `.claim` o los comandos disponibles.")

# ---- GEN (10 tarjetas válidas + botón regenerar) ----
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = update.message.text.split(" ", 1)
    if len(args) < 2:
        await update.message.reply_text("❌ Usa el comando correctamente: `.gen BIN|MM|YYYY|CVV`")
        return

    bin_data = args[1].strip()

    tarjetas = []
    for _ in range(10):
        card = generar_tarjeta_desde_patron(bin_data)
        if card:
            tarjetas.append(card)

    if not tarjetas:
        await update.message.reply_text("❌ Formato inválido. Usa `.gen BIN|MM|YYYY|CVV` (ej: `4517xxxxxxxxxxxx|05|2031|rnd`).")
        return

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("\n".join(tarjetas), reply_markup=reply_markup)

# ---- GENKEY (una key con días de duración) ----
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

    # Generar una key única con expiración
    key = generar_key()
    expira_en = time.time() + dias * 86400
    KEYS_DB[key] = expira_en

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regenkey|{dias}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Key generada:\n{key}\n\n⏳ Expira en {dias} días.",
        reply_markup=reply_markup
    )

# ---- CLAIM (validar key) ----
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

    tiempo_restante = formatear_tiempo_restante(expira_en)
    await update.message.reply_text(f"✨ Key válida. {tiempo_restante}")

# ---- ADMIN ----
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return
    await update.message.reply_text("✅ Bienvenido admin, puedes usar los comandos especiales.")

# ---- CALLBACKS (regen .gen y regen .genkey) ----
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("regen|"):
        bin_data = query.data.split("|", 1)[1]
        tarjetas = []
        for _ in range(10):
            card = generar_tarjeta_desde_patron(bin_data)
            if card:
                tarjetas.append(card)
        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("\n".join(tarjetas), reply_markup=reply_markup)

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