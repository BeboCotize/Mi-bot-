import os
import re
import datetime
import pytz
import telebot
from flask import Flask, request
from db import init_db, add_user, user_has_access, claim_key, generate_key
from cc_gen import cc_gen  # tu archivo ya existente

TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")  # URL de Railway

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
server = Flask(__name__)

ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))  # cambia por tu ID

# Inicializar base de datos
init_db()

# ──────────────── COMANDOS ────────────────

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    add_user(user_id)
    bot.reply_to(message, "👋 Bienvenido, usa /claim <key> para activar tu acceso.")


@bot.message_handler(commands=['claim'])
def claim(message):
    user_id = str(message.from_user.id)
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "⚠️ Uso: /claim <key>")
    
    key = parts[1]
    if claim_key(user_id, key):
        bot.reply_to(message, "✅ Key aceptada, ahora tienes acceso.")
    else:
        bot.reply_to(message, "❌ Key inválida o expirada.")


@bot.message_handler(commands=['gen'])
def gen(message):
    user_id = str(message.from_user.id)

    if not user_has_access(user_id):
        return bot.reply_to(message, "🚫 No tienes acceso, reclama una key.")

    inputcc = re.findall(r'[0-9x]+', message.text)
    if not inputcc:
        return bot.reply_to(message, "⚠️ Extra no reconocida")
    
    # Aquí puedes usar tu mismo código largo que me pasaste para generar tarjetas
    cc = inputcc[0]
    mes, ano, cvv = "xx", "xxxx", "rnd"

    card = cc_gen(cc, mes, ano, cvv)
    if card:
        respuesta = "\n".join([f"<code>{c}</code>" for c in card])
        bot.reply_to(message, f"🇩🇴 DEMON SLAYER GENERATOR 🇩🇴\n\n{respuesta}")
    else:
        bot.reply_to(message, "⚠️ No se pudo generar.")


@bot.message_handler(commands=['genkey'])
def genkey(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "🚫 No tienes permisos.")

    parts = message.text.split()
    if len(parts) < 3:
        return bot.reply_to(message, "⚠️ Uso: /genkey <KEY> <DÍAS>")

    key = parts[1]
    dias = int(parts[2])
    exp_date = datetime.datetime.now() + datetime.timedelta(days=dias)
    generate_key(key, exp_date.isoformat())
    bot.reply_to(message, f"✅ Key generada:\n\n<code>{key}</code>\nExpira: {exp_date}")

# ──────────────── WEBHOOK ────────────────

@server.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.stream.read().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Bot funcionando!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))