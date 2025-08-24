import logging
import random
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "TU_TOKEN_AQUI"   # ⚠️ pon aquí tu token de BotFather

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==============================
# FUNCIONES DEL BOT
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comida":
        keyboard = [[InlineKeyboardButton("↩️ Volver", callback_data="volver")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🍔 Lista de comidas:\n- Pizza\n- Hamburguesa\n- Tacos", reply_markup=reply_markup)

    elif query.data == "peliculas":
        keyboard = [[InlineKeyboardButton("↩️ Volver", callback_data="volver")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🎬 Lista de películas:\n- Acción\n- Terror\n- Comedia", reply_markup=reply_markup)

    elif query.data == "volver":
        keyboard = [
            [InlineKeyboardButton("TOOLS", callback_data="comida")],
            [InlineKeyboardButton("GATES", callback_data="peliculas")],
            [InlineKeyboardButton("❌ Cerrar", callback_data="cerrar")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("👋 Hola! Bienvenido de nuevo\n\nSelecciona una opción:", reply_markup=reply_markup)

    elif query.data == "cerrar":
        await query.edit_message_text("✅ Conversación cerrada.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == "__main__":
    main()