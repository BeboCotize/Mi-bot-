import os
import time
import requests
import re
import datetime
import pytz
import json
from flask import Flask, request
from telebot import TeleBot, types
from cc_gen import cc_gen
from sqldb import *
from braintree import bw
import enums

# ==============================
# CONFIGURACIÓN
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')

USERS = [
    '6629555218', '1073258864', '5147213203',
    '5566291364', '6312955408', '5692739235',
    '1934704808', '6011359218', '1944708963', '5111870793'
]

# Fotos (Imgur links)
IMG_PHOTO1 = "https://imgur.com/a/Lg1SmRY"  # reemplaza
IMG_PHOTO2 = "https://imgur.com/a/Lg1SmRY"  # reemplaza

# Flask app para webhook
app = Flask(__name__)


# ==============================
# FUNCIONES AUXILIARES
# ==============================

def ver_user(iduser: str) -> bool:
    return iduser in USERS

def binlist(bin: str) -> tuple | bool:
    try:
        result = requests.get(f'https://binlist.io/lookup/{bin}/').json()
        return (
            result['number']['iin'],
            result['scheme'],
            result['type'],
            result['category'],
            result['country']['name'],
            result['country']['emoji'],
            result['bank']['name']
        )
    except:
        return False

def dir_fake():
    peticion = requests.get('https://random-data-api.com/api/v2/users')
    try:
        data = peticion.json()
        return (
            data['first_name'],
            data['last_name'],
            data['phone_number'],
            data['address']['city'],
            data['address']['street_name'],
            data['address']['street_address'],
            data['address']['zip_code'],
            data['address']['state'],
            data['address']['country']
        )
    except:
        return None


# ==============================
# HANDLERS
# ==============================

@bot.message_handler(commands=["bin"])
def bin_cmd(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    if message.reply_to_message:
        search_bin = re.findall(r'[0-9]+', str(message.reply_to_message.text))
    else:
        search_bin = re.findall(r'[0-9]+', str(message.text))

    if not search_bin:
        return bot.reply_to(message, "Bin no reconocido.")

    number = search_bin[0][0:6]
    data = binlist(number)
    if not data:
        return bot.reply_to(message, "Bin no encontrado.")

    texto = f"""
𝗕𝗜𝗡: {data[0]}
𝗜𝗡𝗙𝗢: {data[1]} - {data[2]} - {data[3]}
𝗕𝗔𝗡𝗞: {data[6]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {data[4]} {data[5]}
"""
    return bot.reply_to(message, texto)


@bot.message_handler(commands=['rnd'])
def rand(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    data = dir_fake()
    if data is None:
        return bot.reply_to(message, 'Error en la API de dirección.')

    texto = f"""
👤 {data[0]} {data[1]}
📞 {data[2]}
🏙️ {data[3]}, {data[7]}, {data[8]}
📍 {data[5]}, {data[4]}, CP {data[6]}
"""
    bot.reply_to(message, texto)


@bot.message_handler(commands=['gen'])
def gen(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    inputcc = re.findall(r'[0-9x]+', message.text)
    if not inputcc:
        return bot.reply_to(message, "Formato incorrecto.")

    # Procesar inputs
    cc = inputcc[0]
    mes = inputcc[1][0:2] if len(inputcc) > 1 else "xx"
    ano = inputcc[2] if len(inputcc) > 2 else "xxxx"
    cvv = inputcc[3] if len(inputcc) > 3 else "rnd"

    if len(cc) < 6:
        return bot.reply_to(message, "CC incompleta.")

    bin_number = cc[0:6]
    card = cc_gen(cc, mes, ano, cvv)
    if not card:
        return bot.reply_to(message, "Error al generar.")

    binsito = binlist(bin_number)
    cards_text = "\n".join([f"<code>{c.strip()}</code>" for c in card])

    text = f"""
🔹 GENERADOR 🔹

{cards_text}

𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

𝗘𝗫𝗧𝗥𝗔: <code>{cc}|{mes}|{ano}|{cvv}</code>
"""
    bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)


@bot.message_handler(commands=['bw'])
def gate(message):
    if not ver_user(str(message.from_user.id)):
        return bot.reply_to(message, 'No estás autorizado.')

    if message.reply_to_message:
        CARD_INPUT = re.findall(r'[0-9]+', str(message.reply_to_message.text))
    else:
        CARD_INPUT = re.findall(r'[0-9]+', str(message.text))

    if len(CARD_INPUT) != 4:
        return bot.reply_to(message, "Formato: /bw 4111111111111111 12 2026 123")

    cc, mes, ano, cvv = CARD_INPUT
    sql = f"SELECT * FROM spam WHERE user = {int(message.from_user.id)}"
    consulta_dbq = consulta_db(sql)

    if consulta_dbq:
        SPAM_DEFINED = 30
        time_db = int(consulta_dbq[1])
        tiempo_spam = int(time.time()) - time_db
        if tiempo_spam < SPAM_DEFINED:
            tiempo_restante = SPAM_DEFINED - tiempo_spam
            return bot.reply_to(message, f'Espera {tiempo_restante}s para volver a usar.')

        sql = f"UPDATE spam SET spam_time = {int(time.time())} WHERE user = {int(message.from_user.id)}"
        update_into(sql)
    else:
        sql = f"INSERT INTO spam VALUES({int(message.from_user.id)}, {int(time.time())})"
        insert_into(sql)
        return bot.reply_to(message, 'Registrado en DB, vuelve a intentar.')

    gateway = bw(cc, mes, ano, cvv)
    text = f"""💳 {cc}|{mes}|{ano}|{cvv}
📌 STATUS: {gateway['status']}
📌 RESULT: {gateway['result']}"""
    bot.reply_to(message, text)


@bot.message_handler(commands=['cmds'])
def cmds(message):
    buttons_cmds = [
        [
            types.InlineKeyboardButton('Gateways', callback_data='gates'),
            types.InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [types.InlineKeyboardButton('Cerrar', callback_data='close')]
    ]
    markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
    text = "<b>📋 Lista de comandos</b>"

    bot.send_photo(
        chat_id=message.chat.id,
        photo=IMG_PHOTO1,
        caption=text,
        reply_to_message_id=message.id,
        reply_markup=markup_buttom
    )


@bot.message_handler(commands=['start'])
def start(message):
    text = f"""
<b>⚠️ Bienvenido a DuluxeChk ⚠️</b>
• Para ver tools/Gateways: /cmds
• Info: /Deluxe
🚸 @DuluxeChk
"""
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO2, caption=text)


@bot.message_handler(commands=['Deluxe'])
def deluxe(message):
    text = f"""
⚠️ Términos ⚠️
- Macros/scripts = ban
- Reembolsos con saldo bineado = ban
- Difamación = ban
- Robo de gates = ban
"""
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO1, caption=text)


# ==============================
# WEBHOOK CONFIG
# ==============================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5000))
    APP_URL = os.getenv("RAILWAY_URL")

    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
