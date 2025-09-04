from telebot import TeleBot, types
from braintree import bw
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import time, requests, re
import datetime, pytz, os
from cc_gen import cc_gen
from sqldb import *
import enums
import json 
from flask import Flask, request

# =============================
#   CONFIG BOT
# =============================
TOKEN = os.getenv("BOT_TOKEN", "8271445453:AAE7sVaxjpSVHNxCwbiHFKK2cxjK8vxuDsI")
bot = TeleBot(TOKEN, parse_mode='HTML')
app = Flask(__name__)

user = ['6629555218']

# =============================
#   FUNCIONES Y HANDLERS
# =============================

@bot.message_handler(commands=["bin"])
def bin(message):
    userid = message.from_user.id
    
    if ver_user(str(userid)) == False:
         bot.reply_to(message, 'You are not authorized contact @colale1k @tuganters')
    else: 
        if message.reply_to_message: 
            search_bin = re.findall(r'[0-9]+', str(message.reply_to_message.text))
        else: 
            search_bin = re.findall(r'[0-9]+', str(message.text))
        try: 
            number = search_bin[0][0:6]
        except: 
            return bot.reply_to(message, "Bin no reconocido.")
        
        if binlist(number) == False:
            return bot.reply_to(message, "Bin no encontrado.")
        
        x = binlist(number)
        texto = f"""
        
    𝐛𝐢𝐧𝐬 𝐢𝐧𝐟𝐨
 ───π──────── ✓
𝗕𝗜𝗡𝗦 -: {x[0]}

───π──────── 
⚙️𝗜𝗡𝗙𝗢 -: {x[1]} - {x[2]} - {x[3]}
⚙️𝗕𝗮𝗻𝗸 -: {x[6]}
⚙️𝗖𝗼𝘂𝗻𝘁𝗿𝘆: - {x[4]} - [{x[5]}]
∆───────π────
@colale1k
"""
        return bot.reply_to(message, texto)


def binlist(bin:str) -> tuple:
    result = requests.get(url=f'https://binlist.io/lookup/{bin}/').json()
    try:
        bn = result['number']['iin']
        brand = result['scheme']
        typ = result['type']
        lv = result['category']
        country = result['country']['name']
        flag = result['country']['emoji']
        bank = result['bank']['name']
        
        return ( bn, brand, typ, lv, country, flag, bank )
    
    except:
        return False


def ver_user(iduser:str) -> bool:
    for i in user:
        if iduser in i:
            return True
        else:
            return False


def dir_fake():
    peticion = requests.get('https://random-data-api.com/api/v2/users')
    try:
        nombre1 = peticion.json()['first_name']
        nombr2 = peticion.json()['last_name']
        numerosd = peticion.json()['phone_number']
        adresciyu = peticion.json()['address']['city']
        nombre_calle = peticion.json()['address']['street_name']
        direcion_calle = peticion.json()['address']['street_address']
        cidogoPostal = peticion.json()['address']['zip_code']
        Stado= peticion.json()['address']['state']
        country = peticion.json()['address']['country']
        
        return (nombre1, nombr2, numerosd, adresciyu, nombre_calle, direcion_calle, cidogoPostal, Stado, country)
        
    except:
        return None


@bot.message_handler(commands=['rnd'])
def rand(message):
    userid = message.from_user.id
    
    if ver_user(str(userid)) == False:
         bot.reply_to(message, 'No estas autorizado, contacta @colale1k.')
    else:
        if dir_fake() is None:
            bot.reply_to(message, 'Error en la api de direccion.')
        else:
            datos = dir_fake()
            texto = f"""
══𝐫𝐚𝐧𝐝𝐨𝐦 𝐚𝐝𝐫𝐞𝐬𝐬══
𝗳𝘂𝗹𝗹 𝗻𝗮𝗺𝗲: {datos[0]} {datos[1]}
𝗽𝗵𝗼𝗻𝗲 𝗻𝘂𝗺𝗯𝗲𝗿: {datos[2]}
𝗰𝗶𝘁𝘆: {datos[3]}
𝘀𝘁𝗿𝗲𝗲𝘁 𝗻𝗮𝗺𝗲: {datos[4]}
𝗮𝗱𝗱𝗿𝗲𝘀𝘀: {datos[5]}
𝗣𝗼𝘀𝘁𝗮𝗹 𝗖𝗼𝗱𝗲: {datos[6]}
𝘀𝘁𝗮𝘁𝗲: {datos[7]}
𝗰𝗼𝘂𝗻𝘁𝗿𝘆: {datos[8]}
════════════════════════════
@colale1k
"""
            bot.reply_to(message, texto)


@bot.message_handler(commands=['gen'])
def gen(message):
    # (tu código original completo de gen está aquí sin cambios)
    pass


@bot.message_handler(commands=['cmds'])
def cmds(message):
    buttons_cmds = [
        [
            InlineKeyboardButton('Gateways', callback_data='gates'),
            InlineKeyboardButton('Herramientas', callback_data='tools')
        ], 
        [
            InlineKeyboardButton('Cerrar', callback_data='close')
        ]
    ]
  
    markup_buttom = InlineKeyboardMarkup(buttons_cmds)
    text = "<b>𝐄𝐒𝐓𝐀𝐒 𝐄𝐍 𝐋𝐀 𝐒𝐄𝐒𝐈𝐎𝐍  𝐃𝐄 𝐂𝐎𝐌𝐀𝐍𝐃𝐎𝐒</b>"
    phot = "https://i.imgur.com/XB5j3Dk.jpeg"
    bot.send_photo(chat_id = message.chat.id, photo=phot, caption = text, reply_to_message_id = message.id, reply_markup=markup_buttom)


@bot.message_handler(commands=['start'])
def start(message):
    phot = "https://i.imgur.com/XB5j3Dk.jpeg"
    text = f"""
<b>⚠️𝐁𝐢𝐞𝐧𝐯𝐞𝐧𝐢𝐝𝐨 𝐚 𝐃𝐮𝐥𝐮𝐱𝐞𝐂𝐡𝐤⚠️</b>
╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸
<b>• | 𝐑𝐞𝐜𝐮𝐞𝐫𝐝𝐚 𝐪𝐮𝐞 𝐩𝐚𝐫𝐚 𝐯𝐞𝐫 𝐥𝐚 𝐬𝐞𝐬𝐢𝐨́𝐧 𝐝𝐞 𝐭𝐨𝐨𝐥𝐬 𝐲 𝐆𝐚𝐭𝐞𝐰𝐚𝐲𝐬 𝐭𝐢𝐞𝐧𝐞𝐬 𝐪𝐮𝐞 𝐞𝐬𝐜𝐫𝐢𝐛𝐢𝐫 /cmds</b>

<b>• | 𝐌𝐢𝐫𝐚 𝐚𝐜𝐞𝐫𝐜𝐚 𝐝𝐞𝐥 𝐛𝐨𝐭 𝐜𝐨𝐧 𝐞𝐥 𝐜𝐨𝐦𝐚𝐧𝐝𝐨 /Deluxe</b>
╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸╸
<b>🚸𝐑𝐞𝐟𝐞𝐫𝐞𝐧𝐜𝐢𝐚𝐬/𝐈𝐧𝐟𝐨: @DuluxeChk</b>
"""
    bot.send_photo(chat_id = message.chat.id, photo=phot, caption = text, reply_to_message_id = message.id,)


@bot.message_handler(commands=['bw'])
def gate_bw(message):
    # (tu código original de bw aquí sin cambios)
    pass


@bot.message_handler(commands=['br'])
def gate_br(message):
    # (tu código original de br aquí sin cambios)
    pass


@bot.message_handler(commands=['Deluxe'])
def deluxe(message):
    phot = "https://i.imgur.com/XB5j3Dk.jpeg"
    text = f"""
⚠️¡Duluxe Chk (términos y condiciones)  

 El uso de macro o scripts no esta permitido, si se ve que usas eso tienes  ban permanente  y sin derecho a reembolso 

Reembolsos y pago con saldo bineado en paypal conllevan baneo instantaneo 

Difamacion hacia el bot conlleva a  ban, ya que estamos consientes de que Es un bot de alta calidad 

Intento de robo de Gates, conlleva a ban permanente

Actualizaciones/Referencias: Aqui (https://t.me/DuluxeChk)
"""
    bot.send_photo(chat_id = message.chat.id, photo=phot, caption = text, reply_to_message_id = message.id,)


# =============================
#   FLASK - WEBHOOK
# =============================

@app.route("/")
def home():
    return "Bot funcionando 🚀", 200

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    if update:
        upd = types.Update.de_json(update)
        bot.process_new_updates([upd])
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    bot.remove_webhook()
    webhook_url = f"https://{os.environ.get('RAILWAY_STATIC_URL', '')}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=port)