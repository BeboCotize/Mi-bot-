import telebot
import json
import os 
import re
import pytz 
import datetime
from cc_gen import cc_gen  # tu cc_gen.py debe tener las funciones que pasaste
from datetime import timedelta, datetime
from flask import Flask, request
import requests
from sagepay import ccn_gate   # ✅ importamos tu nuevo archivo
from telebot import types
import random

# =============================
#   CONFIG BOT
# =============================
TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")  # ej: https://mi-bot-production.up.railway.app
ADMIN_ID = os.getenv("ADMIN_ID", "6629555218")  # ⚠️ se mantiene como string
bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.json"
KEYS_FILE = "keys.json"


# =============================
#   HELPERS JSON
# =============================
def load_keys():
    try:
        with open("keys.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open("keys.json", "w") as f:
        json.dump(keys, f, indent=4)

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)


# =============================
#   START
# =============================
@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(telebot.types.InlineKeyboardButton("📂 Gates", callback_data="gates"),
               telebot.types.InlineKeyboardButton("🛠 Tools", callback_data="tools"))
    markup.row(telebot.types.InlineKeyboardButton("❌ Exit", callback_data="exit"))

    bot.send_photo(
        message.chat.id,
        "https://i.imgur.com/ExdKOOz.png",
        caption="👋 Bienvenido a Demon Slayer Bot\n\nSelecciona una opción:",
        reply_markup=markup
    )


# =============================
#   GENKEY (solo admin)
# =============================
@bot.message_handler(commands=['genkey'])
def genkey_handler(message):
    user_id = str(message.from_user.id)
    if user_id != ADMIN_ID:
        bot.reply_to(message, "⛔ No tienes permiso para usar este comando.")
        return

    try:
        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, "Uso: /genkey <días>")
            return

        dias = int(args[0])
        nombre = "Demon"
        key = f"{nombre}{random.randint(1000,9999)}"
        expira = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")

        keys = load_keys()
        keys[key] = {"dias": dias, "expira": expira}
        save_keys(keys)

        bot.reply_to(message, f"✅ Key generada:\n\n🔑 {key}\n📅 Expira: {expira}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error interno: {e}")


# =============================
#   CLAIM KEY
# =============================
@bot.message_handler(commands=['claim'])
def claim(message):
    try:
        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, "Uso: /claim <key>")
            return

        key = args[0]
        keys = load_keys()
        users = load_users()
        user_id = str(message.from_user.id)

        if key not in keys:
            bot.reply_to(message, "❌ Key inválida.")
            return

        expira_str = keys[key]["expira"]
        expira_dt = datetime.fromisoformat(expira_str)

        if expira_dt < datetime.now():
            bot.reply_to(message, "⏳ Esta key ya expiró.")
            return

        users[user_id] = {
            "username": message.from_user.username or "SinUsername",
            "key": key,
            "expires": expira_str
        }
        save_users(users)

        del keys[key]
        save_keys(keys)

        bot.reply_to(
            message,
            f"✅ Key reclamada con éxito.\n\n👤 Usuario: @{message.from_user.username}\n🔑 Key: {key}\n📅 Expira: {expira_str}"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error interno: {e}")


# =============================
#   MYINFO
# =============================
@bot.message_handler(commands=['myinfo'])
def myinfo(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        bot.reply_to(message, "❌ No has reclamado ninguna key todavía.")
        return

    data = users[user_id]
    username = data["username"]
    key = data["key"]
    expires = data["expires"]

    try:
        expira_dt = datetime.fromisoformat(expires)
        expira_str = expira_dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        expira_dt = None
        expira_str = expires

    if expira_dt and expira_dt < datetime.now():
        bot.reply_to(
            message,
            f"👤 Usuario: @{username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expiró el: {expira_str}\n\n"
            f"⚠️ Tu key ha expirado, reclama una nueva."
        )
    else:
        bot.reply_to(
            message,
            f"👤 Usuario: @{username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expira: {expira_str}\n\n"
            f"✅ Tu key sigue activa."
        )


# =============================
#   LISTKEYS (solo admin)
# =============================
@bot.message_handler(commands=['listkeys'])
def listkeys(message):
    if str(message.from_user.id) != ADMIN_ID:
        bot.reply_to(message, "⛔ No tienes permiso para usar este comando.")
        return

    keys = load_keys()
    if not keys:
        bot.reply_to(message, "📂 No hay keys disponibles.")
        return

    text = "🔑 Keys disponibles:\n\n"
    for k, v in keys.items():
        text += f"• {k} → Expira: {v['expira']}\n"

    bot.reply_to(message, text, parse_mode="Markdown")


# =============================
#   (el resto de tu código sigue igual)
# =============================

# =============================
@bot.message_handler(commands=['gen'])
def gen(message):
    try:
        userid = str(message.from_user.id)
        
        if not ver_user(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')
        
        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Debes especificar un BIN o formato.")
        
        inputcc = args[1].strip()
        partes = inputcc.split("|")

        cc  = partes[0] if len(partes) > 0 else ""
        mes = partes[1] if len(partes) > 1 else "xx"
        ano = partes[2] if len(partes) > 2 else "xxxx"
        cvv = partes[3] if len(partes) > 3 else "rnd"

        if len(cc) < 6:
            return bot.reply_to(message, "❌ BIN incompleto")
        
        bin_number = cc[:6]
        if cc.isdigit():
            cc = cc[:12]

        if mes.isdigit() and ano.isdigit():
            if len(ano) == 2: 
                ano = '20' + ano
            IST = pytz.timezone('US/Central')
            now = datetime.datetime.now(IST)
            if (datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > 
                datetime.datetime.strptime(f'{mes}-{ano}', "%m-%Y")):
                return bot.reply_to(message, "❌ Fecha incorrecta")

        cards = cc_gen(cc, mes, ano, cvv)
        if not cards:
            return bot.reply_to(message, "❌ No se pudo generar tarjetas, revisa el BIN o formato.")
        
        binsito = binlist(bin_number)
        if not binsito[0]:
            binsito = (None, "Unknown", "Unknown", "Unknown", "Unknown", "", "Unknown")

        text = f"""
🇩🇴 DEMON SLAYER GENERATOR 🇩🇴
⚙️──────────────⚙️
"""        
        for c in cards:
            text += f"<code>{c.strip()}</code>\n"

        text += f"""
𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}
"""
        bot.reply_to(message, text, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error interno: {e}")

# =============================
#   FUNCIÓN /SG (SAGEPAY)
# =============================
@bot.message_handler(commands=['sg'])
def sagepay_cmd(message):
    try:
        userid = str(message.from_user.id)

        if not ver_user(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')

        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Uso correcto: /sg <cc|mm|yyyy|cvv>")

        card = args[1].strip()
        partes = card.split("|")

        cc  = partes[0] if len(partes) > 0 else ""
        mes = partes[1] if len(partes) > 1 else ""
        ano = partes[2] if len(partes) > 2 else ""
        cvv = partes[3] if len(partes) > 3 else ""

        # Extraer BIN y consultar info
        bin_number = cc[:6]
        binsito = binlist(bin_number)
        if not binsito[0]:
            binsito = (None, "Unknown", "Unknown", "Unknown", "Unknown", "", "Unknown")

        # Llamada a tu función en sagepay.py
        result = ccn_gate(card)

        # Revisar si está aprobado
        if "CVV2 MISMATCH|0000N7|" in str(result) or "Approved" in str(result):
            estado = "✅ Approved"
        else:
            estado = "❌ Declined"

        text = f"""
{estado}
Card: <code>{card}</code>


𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

<b>Respuesta:</b> <code>{result}</code>

Checked by: @{message.from_user.username or message.from_user.id}
"""
        bot.reply_to(message, text, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error interno en /sg: {e}")

# =============================
#   FLASK APP PARA RAILWAY
# =============================
app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def home():
    return "🤖 Bot funcionando en Railway!", 200


# =============================
#   MAIN
# =============================
if __name__ == "__main__":
    if os.getenv("RAILWAY_ENVIRONMENT") is None:
        print("🤖 Bot en ejecución local con polling...")
        bot.infinity_polling()
    else:
        port = int(os.environ.get("PORT", 5000))
        bot.remove_webhook()
        bot.set_webhook(url=f"{URL}/{TOKEN}")
        print(f"🚀 Bot corriendo en Railway en {URL}")
        app.run(host="0.0.0.0", port=port)