import os
import logging
import random
import string
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

# ======================
# LOGGING
# ======================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ======================
# FUNCIONES AUXILIARES
# ======================
def generar_key(longitud: int = 16) -> str:
    """Genera una key aleatoria de letras y números."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=longitud))


# ======================
# HANDLERS
# ======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Bienvenido! Usa .gen, .genkey, /claim o los comandos disponibles.")


async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ejemplo de generador
    args = context.args
    if not args:
        await update.message.reply_text("❌ Usa el comando correctamente: `.gen BIN|MM|YYYY|CVV`")
        return

    bin_data = args[0]
    response = f"{bin_data}123456|04|2027|127"

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(response, reply_markup=reply_markup)


async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ No tienes permisos para generar keys.")
        return

    args = context.message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await update.message.reply_text("❌ Usa el comando correctamente: `.genkey cantidad`")
        return

    cantidad = int(args[1])
    keys = [generar_key() for _ in range(cantidad)]
    await update.message.reply_text("✅ Keys generadas:\n" + "\n".join(keys))


async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Has reclamado tu recompensa.")


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("⛔ No tienes permisos de administrador.")
        return
    await update.message.reply_text("✅ Bienvenido admin, puedes usar los comandos especiales.")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("regen|"):
        bin_data = query.data.split("|", 1)[1]
        results = "\n".join([f"{bin_data}{i}23456|04|2027|127" for i in range(10)])

        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_data}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(results, reply_markup=reply_markup)


# ======================
# MAIN
# ======================
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("claim", claim))
    application.add_handler(CommandHandler("admin", admin))

    # Muy importante: primero .genkey, después .gen
    application.add_handler(MessageHandler(filters.Regex(r"^\.genkey(?:\s|$)"), genkey))
    application.add_handler(MessageHandler(filters.Regex(r"^\.gen\s+"), gen))

    application.add_handler(CallbackQueryHandler(button_callback))

    # Webhook config para Railway
    WEBHOOK_URL = f"https://mi-bot-bottoken.up.railway.app/{TOKEN}"

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=WEBHOOK_URL
    )


if __name__ == "__main__":
    main()