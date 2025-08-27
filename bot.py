import os
import re
import pytz
import datetime
import telebot
from flask import Flask, request

# === IMPORTAMOS EL GENERADOR ===
from cc_gen import cc_gen, binlist

# === CONFIG ===
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")  # Railway -> Config Vars
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# 🔒 Usuarios permitidos
AUTHORIZED_USERS = ["123456789", "987654321"]  # IDs de Telegram

# === HANDLER /GEN ===
@bot.message_handler(commands=['gen'])
def gen(message):
    userid = str(message.from_user.id)

    # verificar usuario autorizado
    if userid not in AUTHORIZED_USERS:
        return bot.reply_to(message, "⛔ No estás autorizado, contacta al admin.")

    inputcc = re.findall(r'[0-9x]+', message.text)
    if not inputcc:
        return bot.reply_to(message, "❌ Extra no reconocida")

    # --- PARSEO DE INPUT ---
    if len(inputcc) == 1:
        cc, mes, ano, cvv = inputcc[0], "xx", "xxxx", "rnd"
    elif len(inputcc) == 2:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], "xxxx", "rnd"
    elif len(inputcc) == 3:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], inputcc[2], "rnd"
    else:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], inputcc[2], inputcc[3]

    if len(cc) < 6:
        return bot.reply_to(message, "❌ Extra incompleta")

    bin_number = cc[0:6]

    # limitar cc a 12 si es solo números
    if cc.isdigit():
        cc = cc[0:12]

    # validación de fecha
    if mes.isdigit() and ano.isdigit():
        if len(ano) == 2:
            ano = "20" + ano
        IST = pytz.timezone("US/Central")
        now = datetime.datetime.now(IST)
        if datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > datetime.datetime.strptime(f"{mes}-{ano}", "%m-%Y"):
            return bot.reply_to(message, "❌ Fecha incorrecta")

    # Generar tarjetas
    card = cc_gen(cc, mes, ano, cvv)
    if not card:
        return bot.reply_to(message, "❌ No se pudo generar la tarjeta.")

    cc1, cc2, cc3, cc4, cc5, cc6, cc7, cc8, cc9, cc10 = card

    extra = f"{cc}xxxxxxxxxxxxxxxxxxxxxxx"
    mes_2 = mes if mes not in ["xx", "rnd"] else mes
    ano_2 = ano if ano not in ["xxxx", "rnd"] else ano
    if len(ano_2) == 2:
        ano_2 = "20" + ano_2
    cvv_2 = cvv if cvv not in ["xxx", "rnd", "xxxx"] else cvv

    binsito = binlist(bin_number)

    if binsito[0] is not None:
        text = f"""
🇩🇴 <b>DEMON SLAYER GENERATOR</b> 🇩🇴
⚙️───π────────⚙️

<code>{cc1.strip()}</code>
<code>{cc2.strip()}</code>
<code>{cc3.strip()}</code>
<code>{cc4.strip()}</code>
<code>{cc5.strip()}</code>
<code>{cc6.strip()}</code>
<code>{cc7.strip()}</code>
<code>{cc8.strip()}</code>
<code>{cc9.strip()}</code>
<code>{cc10.strip()}</code>

<b>BIN INFO:</b> {binsito[1]} - {binsito[2]} - {binsito[3]}
<b>COUNTRY:</b> {binsito[4]} - {binsito[5]}
<b>BANK:</b> {binsito[6]}

<b>EXTRA:</b> <code>{extra[0:16]}|{mes_2}|{ano_2}|{cvv_2}</code>
"""
        bot.send_message(message.chat.id, text)

# === FLASK ROUTES ===
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "🤖 Bot funcionando con Webhook!", 200

# === MAIN ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    APP_URL = os.getenv("APP_URL")

    if APP_URL is None:
        raise RuntimeError("⚠️ Debes configurar la variable APP_URL en Railway")

    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

    print("🚀 Bot corriendo con Webhook...")
    app.run(host="0.0.0.0", port=port)