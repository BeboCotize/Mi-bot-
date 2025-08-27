import telebot
import os

# === CONFIG ===
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")  # usa variable de entorno o ponlo directo
bot = telebot.TeleBot(TOKEN)

# === HANDLERS ===
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 Hola! Soy tu bot hecho con telebot.\nUsa /hola para saludarme.")

@bot.message_handler(commands=['hola'])
def send_hello(message):
    bot.send_message(message.chat.id, "¡Hola crack! 😎🔥")

@bot.message_handler(func=lambda message: True)  # cualquier mensaje
def echo_all(message):
    bot.reply_to(message, f"Dijiste: {message.text}")

# === LOOP ===
print("🤖 Bot corriendo...")
bot.infinity_polling()