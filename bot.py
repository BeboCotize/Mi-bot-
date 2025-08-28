import telebot
import json
import os 
import re
import pytz 
import datetime
from cc_gen import cc_gen  # tu cc_gen.py debe tener las funciones que pasaste
from datetime import timedelta
from flask import Flask, request
import requests
from sagepay import ccn_gate   # ✅ importamos tu nuevo archivo
from telebot import types

# =============================
#   CONFIG BOT
# =============================
TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")  # ej: https://mi-bot-production.up.railway.app
ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))  # tu ID de admin fijo

bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

# =============================
#   HELPERS
# =============================

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE, users)

def load_keys():
    return load_json(KEYS_FILE)

def save_keys(keys):
    save_json(KEYS_FILE, keys)

def ver_user(user_id: str):
    """Verifica si el usuario tiene key válida"""
    users = load_users()
    if user_id not in users:
        return False
    expira = datetime.datetime.fromisoformat(users[user_id]["expires"])
    return expira > datetime.datetime.now()

# =============================
#   BINLIST LOOKUP (ANTIPUBLIC)
# =============================
def binlist(bin_number: str):
    try:
        r = requests.get(f"https://bins.antipublic.cc/bins/{bin_number}")
        if r.status_code == 200:
            data = r.json()
            brand = data.get("scheme", "Unknown").upper()
            tipo = data.get("type", "Unknown").upper()
            level = data.get("brand", "Unknown").upper()
            country_name = data.get("country_name", "Unknown")
            flag = data.get("country_flag", "")
            bank = data.get("bank", "Unknown")
            return (True, brand, tipo, level, country_name, flag, bank)
        else:
            return (False, None, None, None, None, None, None)
    except Exception:
        return (False, None, None, None, None, None, None)

# =============================
#   NUEVO /START CON MENÚ
# =============================
@bot.message_handler(commands=["start"])
def start(message):
    try:
        chat_id = message.chat.id

        # Cambia esta URL por la imagen que quieras
        photo_url = "https://imgur.com/a/ytDQfiM"

        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📂 Gates", callback_data="menu_gates"),
            types.InlineKeyboardButton("🛠 Tools", callback_data="menu_tools")
        )
        markup.row(
            types.InlineKeyboardButton("❌ Exit", callback_data="menu_exit")
        )

        bot.send_photo(
            chat_id,
            photo=photo_url,
            caption="👋 Bienvenido a *Demon Slayer Bot*\n\nSelecciona una opción:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error en /start: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def callback_menu(call):
    try:
        if call.data == "menu_gates":
            text = "📂 *Menú Gates*\n\nAquí irán tus gates disponibles."
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back")
            )
            bot.edit_message_caption(
                caption=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )

        elif call.data == "menu_tools":
            text = "🛠 *Menú Tools*\n\nAquí estarán tus herramientas."
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back")
            )
            bot.edit_message_caption(
                caption=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )

        elif call.data == "menu_back":
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("📂 Gates", callback_data="menu_gates"),
                types.InlineKeyboardButton("🛠 Tools", callback_data="menu_tools")
            )
            markup.row(
                types.InlineKeyboardButton("❌ Exit", callback_data="menu_exit")
            )
            bot.edit_message_caption(
                caption="👋 Bienvenido a *Demon Slayer Bot*\n\nSelecciona una opción:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )

        elif call.data == "menu_exit":
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error en menú: {e}")

# =============================
#   COMANDOS EXISTENTES
# =============================

# Generar key (solo admin)
@bot.message_handler(commands=["genkey"])
def genkey(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "🚫 No tienes permiso para usar este comando.")

        args = message.text.split()
        if len(args) < 3:
            return bot.reply_to(message, "Uso: /genkey <nombre> <días>")
        nombre = args[1]
        dias = int(args[2])

        keys = load_keys()
        import random, string
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        expira = datetime.datetime.now() + timedelta(days=dias)

        keys[key] = {
            "nombre": nombre,
            "expires": expira.isoformat()
        }
        save_keys(keys)

        bot.reply_to(message, f"✅ Key generada:\n\n`{key}`\nExpira: {expira}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# Reclamar key
@bot.message_handler(commands=["claim"])
def claim(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            return bot.reply_to(message, "Uso: /claim <key>")

        key = args[1]
        keys = load_keys()
        users = load_users()
        user_id = str(message.from_user.id)

        if key not in keys:
            return bot.reply_to(message, "🚫 Key inválida.")

        expira = datetime.datetime.fromisoformat(keys[key]["expires"])
        if expira < datetime.datetime.now():
            return bot.reply_to(message, "🚫 Esa key ya expiró.")

        users[user_id] = {
            "key": key,
            "expires": keys[key]["expires"]
        }
        save_users(users)

        bot.reply_to(message, "✅ Key aceptada, ya puedes usar /gen.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# =============================
#   FUNCIÓN /GEN
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
def sg(message):
    try:
        userid = str(message.from_user.id)

        if not ver_user(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')

        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Uso correcto: /sg <cc|mm|yyyy|cvv>")

        card = args[1].strip()
        result = ccn_gate(card)  # ✅ llamada a tu función en sagepay.py

        if isinstance(result, dict):
            text = f"""
💳 <b>Resultado Sagepay</b>
Card: <code>{result.get('card','')}</code>
Estado: {result.get('status','')}</code>
Respuesta: {result.get('resp','')}
"""
        else:
            text = f"<b>Respuesta Sagepay</b>\n<code>{result}</code>"

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