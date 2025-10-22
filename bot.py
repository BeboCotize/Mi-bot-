import os
import re
import requests
from flask import Flask, request
from telebot import TeleBot, types
from cc_gen import cc_gen
from sagepay import ccn_gate as sagepay   # Importación de SagePay
from gateway import ccn_gate as bb_gateway_check # 👈 NUEVA IMPORTACIÓN (Asumiendo bb_gateway.py)
 
# ==============================
# CONFIGURACIÓN 
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')

USERS = [
    '6116275760']

# Fotos en Imgur (cambia por tus enlaces)
IMG_PHOTO1 = "https://i.imgur.com/XXXXXXX.jpg"
IMG_PHOTO2 = "https://i.imgur.com/YYYYYYY.jpg"

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
    """Genera una dirección usando randomuser.me (más estable)."""
    try:
        r = requests.get("https://randomuser.me/api/", timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()["results"][0]
        return {
            "first_name": data["name"]["first"],
            "last_name": data["name"]["last"],
            "phone": data["phone"],
            "city": data["location"]["city"],
            "street_name": data["location"]["street"]["name"],
            "street_address": str(data["location"]["street"]["number"]),
            "zip": str(data["location"]["postcode"]),
            "state": data["location"]["state"],
            "country": data["location"]["country"],
        }
    except Exception as e:
        print("Error en dir_fake:", e)
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
    if not data:
        return bot.reply_to(message, '⚠️ Error obteniendo dirección.')

    texto = f"""
👤 {data['first_name']} {data['last_name']}
📞 {data['phone']}
🏙️ {data['city']}, {data['state']}, {data['country']}
📍 {data['street_address']} {data['street_name']}
🆔 CP: {data['zip']}
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


@bot.message_handler(commands=['bb'])
def gate_bb(message):
    # Lógica de autorización
    if not ver_user(str(message.from_user.id)):
        return bot.reply_to(message, 'No estás autorizado.')

    # 1. Preparar el texto de entrada (asume el formato CC|MM|AAAA|CVV)
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/bb", "").strip() # Quitamos el comando /bb del texto
    parts = re.split(r"[| \n\t]+", clean)

    if len(parts) < 4:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido.\nEjemplo:\n"
            "`/bb 4111111111111111|12|2026|123`",
            parse_mode="Markdown"
        )

    cc, mes, ano, cvv = parts[0:4]

    # 2. Llamar a la NUEVA función del gateway
    bot.reply_to(message, "⚙️ Chequeando con BB Gateway...") # Opción: avisar al usuario que se está procesando

    try:
        # LLAMADA A TU NUEVO GATEWAY BB
        result = bb_gateway_check(f"{cc}|{mes}|{ano}|{cvv}")
        print("DEBUG bb_gateway_check() ->", result)

        # Usamos el resultado devuelto por tu función
        text = f"""
💳 <code>{cc}|{mes}|{ano}|{cvv}</code>
📌 RESULT (BB GATEWAY): <b>¡Revisa tus logs o el archivo live.txt!</b>
"""
    except Exception as e:
        text = f"❌ Error ejecutando BB Gateway:\n{e}"

    # 3. Enviar la respuesta
    bot.reply_to(message, text)


@bot.message_handler(commands=['sagepay'])
def gate_sagepay(message):
    if not ver_user(str(message.from_user.id)):
        return bot.reply_to(message, 'No estás autorizado.')

    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/sagepay", "").strip()
    parts = re.split(r"[| \n\t]+", clean)

    if len(parts) < 4:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido.\nEjemplos:\n"
            "`/sagepay 4111111111111111 12 2026 123`\n"
            "`/sagepay 4111111111111111|12|2026|123`",
            parse_mode="Markdown"
        )

    cc, mes, ano, cvv = parts[0:4]

    try:
        result = sagepay(f"{cc}|{mes}|{ano}|{cvv}")   # ahora devuelve solo el resultado limpio
        print("DEBUG sagepay() ->", result)

        text = f"""
💳 <code>{cc}|{mes}|{ano}|{cvv}</code>
📌 RESULT: <b>{result}</b>
"""
    except Exception as e:
        text = f"❌ Error ejecutando gateway SagePay:\n{e}"

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
    APP_URL = os.getenv("APP_URL")

    if not APP_URL:
        raise ValueError("APP_URL no está definida en Railway Variables")

    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
