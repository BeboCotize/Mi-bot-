import os
import time
import requests
import re
import datetime
import pytz
import json
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from cc_gen import cc_gen
from sqldb import *
from braintree import bw
import enums

# ==============================
# CONFIGURACIÓN
# ==============================

# Token desde variables de entorno en Railway
TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')

# Lista de usuarios autorizados
USERS = [
    '6629555218']

# Imágenes en Imgur (cambia por tus links)
IMG_PHOTO1 = "https://i.imgur.com/XXXXXXX.jpg"  # reemplazar
IMG_PHOTO2 = "https://i.imgur.com/YYYYYYY.jpg"  # reemplazar


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
        return bot.reply_to(message, 'No estás autorizado. Contacta al admin.')

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
    𝐛𝐢𝐧𝐬 𝐢𝐧𝐟𝐨
 ───π──────── ✓
𝗕𝗜𝗡𝗦 -: {data[0]}

───π──────── 
⚙️𝗜𝗡𝗙𝗢 -: {data[1]} - {data[2]} - {data[3]}
⚙️𝗕𝗮𝗻𝗸 -: {data[6]}
⚙️𝗖𝗼𝘂𝗻𝘁𝗿𝘆: - {data[4]} - [{data[5]}]
∆───────π────
@colale1k
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
══𝐫𝐚𝐧𝐝𝐨𝐦 𝐚𝐝𝐫𝐞𝐬𝐬══
𝗳𝘂𝗹𝗹 𝗻𝗮𝗺𝗲: {data[0]} {data[1]}
𝗽𝗵𝗼𝗻𝗲 𝗻𝘂𝗺𝗯𝗲𝗿: {data[2]}
𝗰𝗶𝘁𝘆: {data[3]}
𝘀𝘁𝗿𝗲𝗲𝘁 𝗻𝗮𝗺𝗲: {data[4]}
𝗮𝗱𝗱𝗿𝗲𝘀𝘀: {data[5]}
𝗣𝗼𝘀𝘁𝗮𝗹 𝗖𝗼𝗱𝗲: {data[6]}
𝘀𝘁𝗮𝘁𝗲: {data[7]}
𝗰𝗼𝘂𝗻𝘁𝗿𝘆: {data[8]}
════════════════════════════
@colale1k
"""
    bot.reply_to(message, texto)


@bot.message_handler(commands=['cmds'])
def cmds(message):
    buttons_cmds = [
        [
            InlineKeyboardButton('Gateways', callback_data='gates'),
            InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [InlineKeyboardButton('Cerrar', callback_data='close')]
    ]

    markup_buttom = InlineKeyboardMarkup(buttons_cmds)
    text = "<b>𝐄𝐒𝐓𝐀𝐒 𝐄𝐍 𝐋𝐀 𝐒𝐄𝐒𝐈𝐎𝐍  𝐃𝐄 𝐂𝐎𝐌𝐀𝐍𝐃𝐎𝐒</b>"

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
<b>⚠️𝐁𝐢𝐞𝐧𝐯𝐞𝐧𝐢𝐝𝐨 𝐚 𝐃𝐮𝐥𝐮𝐱𝐞𝐂𝐡𝐤⚠️</b>
╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸
<b>• | Para ver la sesión de tools y Gateways escribe /cmds</b>

<b>• | Mira acerca del bot con el comando /Deluxe</b>
╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸
<b>🚸 Referencias/Info: @DuluxeChk</b>
"""
    bot.send_photo(
        chat_id=message.chat.id,
        photo=IMG_PHOTO2,
        caption=text,
        reply_to_message_id=message.id
    )


@bot.message_handler(commands=['Deluxe'])
def deluxe(message):
    text = f"""
⚠️¡Duluxe Chk (términos y condiciones)  

 El uso de macro o scripts no está permitido → ban permanente  
 Reembolsos con saldo bineado en PayPal → ban instantáneo  
 Difamación hacia el bot → ban permanente  
 Intento de robo de Gates → ban permanente  

Actualizaciones/Referencias: (https://t.me/DuluxeChk)
"""
    bot.send_photo(
        chat_id=message.chat.id,
        photo=IMG_PHOTO1,
        caption=text,
        reply_to_message_id=message.id
    )


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    bot.infinity_polling()
