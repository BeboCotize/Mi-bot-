import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========================
# CONFIG
# ========================
TOKEN = os.environ.get("BOT_TOKEN")  # token del bot en variable de entorno
PORT = int(os.environ.get("PORT", 0))  # si no hay PORT -> polling
WEBHOOK_URL = f"https://TU_DOMINIO/{TOKEN}"  # ⚡ cambia TU_DOMINIO

# ========================
# LOGGING
# ========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========================
# FUNCIONES AUXILIARES
# ========================
def generar_tarjetas():
    """Genera 10 tarjetas con tu formato"""
    return [f"4098480017386953|04|2027|{i:03d}" for i in range(1, 11)]

# ========================
# HANDLERS
# ========================

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Claim", callback_data="claim")],
        [InlineKeyboardButton("Regenerar 10 más", callback_data="regen10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "¡Bienvenido! Usa los botones:",
        reply_markup=reply_markup
    )

# Claim
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Has hecho tu *claim* correctamente.", parse_mode="Markdown")

# Regenerar
async def regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    generados = generar_tarjetas()

    await query.edit_message_text("🔄 Aquí tienes 10 nuevos generados:\n" + "\n".join(generados))

# /gen
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    generados = generar_tarjetas()
    await update.message.reply_text("🔄 Generando tus códigos...\n" + "\n".join(generados))

    keyboard = [
        [InlineKeyboardButton("Claim", callback_data="claim")],
        [InlineKeyboardButton("Regenerar 10 más", callback_data="regen10")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elige una acción:", reply_markup=reply_markup)

# ========================
# MAIN
# ========================
def main():
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gen", gen))
    application.add_handler(CallbackQueryHandler(claim, pattern="^claim$"))
    application.add_handler(CallbackQueryHandler(regenerate, pattern="^regen10$"))

    if PORT == 0:
        # Local -> Polling
        logger.info("▶️ Iniciando en modo POLLING")
        application.run_polling()
    else:
        # Hosting -> Webhook
        logger.info(f"🌍 Iniciando en modo WEBHOOK en puerto {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=WEBHOOK_URL
        )

# ========================
# RUN
# ========================
if __name__ == "__main__":
    main()