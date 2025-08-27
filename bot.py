import os
import telebot

# ⚙️ Configuración
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")  # 👈 HTML activado

# 📣 ÚNICO COMANDO
@bot.message_handler(commands=["info"])
def cmd_info(message):
    bot.send_message(
        message.chat.id,
        (
            "<b>🔔 Información:</b>\n\n"
            "Este es un <i>texto de ejemplo</i> que puedes editar.\n"
            "Puedes usar <code>negritas</code>, <i>cursivas</i>, "
            "<u>subrayado</u> y <code>monospace</code>.\n\n"
            "✍️ Edita este mensaje en el código para personalizarlo."
        )
    )

# 🚀 Loop principal
if __name__ == "__main__":
    print("🤖 Bot corriendo...")
    bot.infinity_polling()