import os
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Comando /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Hola! 👋 El bot con Telebot está funcionando ✅")

# Cualquier mensaje de texto
@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, f"Me escribiste: {message.text}")

if __name__ == "__main__":
    print("🚀 Iniciando bot con Telebot...")
    bot.infinity_polling()