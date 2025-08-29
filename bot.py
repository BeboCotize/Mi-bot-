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
from keys import generate_key, claim_key, list_keys


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
#   HELPERS JSON
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
#   COMANDO /MYINFO
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
        expira_dt = datetime.datetime.fromisoformat(expires)
        expira_str = expira_dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        expira_dt = None
        expira_str = expires

    # Verificar si expiró
    if expira_dt and expira_dt < datetime.datetime.now():
        bot.reply_to(
            message,
            f"👤 Usuario: {username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expiró el: {expira_str}\n\n"
            f"⚠️ Tu key ha expirado, reclama una nueva."
        )
    else:
        bot.reply_to(
            message,
            f"👤 Usuario: {username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expira: {expira_str}\n\n"
            f"✅ Tu key sigue activa."
        )

# =============================
#   COMANDO /LISTKEYS (solo admin)
# =============================
@bot.message_handler(commands=['listkeys'])
def cmd_listkeys(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "❌ No tienes permiso para usar este comando.")
        return
    keys = list_keys()
    if not keys:
        bot.reply_to(message, "⚠️ No hay keys registradas.")
    else:
        resp = "🔑 *Listado de Keys:*\n\n" + "\n".join(keys)
        bot.reply_to(message, resp, parse_mode="Markdown")

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
        photo_url = "https://i.imgur.com/ytDQfiM.png"  # imagen fija
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

# =============================
#   (AQUÍ SIGUE TU CÓDIGO ORIGINAL)
# =============================
# Ejemplo: otros handlers, gates, tools, etc.
@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def callback_menu(call):
    try:
        if call.data == "menu_gates":
            text = "📂 *Menú Gates*\n\nAquí irán tus gates disponibles."
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back"))
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
            markup.row(types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back"))
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
            markup.row(types.InlineKeyboardButton("❌ Exit", callback_data="menu_exit"))
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
#   KEYS SYSTEM
# =============================

@bot.message_handler(commands=["genkey"])
def genkey_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "🚫 No tienes permiso.")

    args = message.text.split()
    if len(args) < 3:
        return bot.reply_to(message, "Uso: /genkey <nombre> <días>")

    nombre = args[1]
    try:
        dias = int(args[2])
    except ValueError:
        return bot.reply_to(message, "🚫 Días debe ser un número.")

    key, expira = generate_key(nombre, dias)
    bot.reply_to(
        message,
        f"✅ Key generada:\n\n`{key}`\nExpira: {expira.strftime('%Y-%m-%d %H:%M:%S')}"
    )


@bot.message_handler(commands=["claim"])
def claim_cmd(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Uso: /claim <key>")

    key = args[1]
    user_id = str(message.from_user.id)
    username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

    ok, msg = claim_key(user_id, username, key)
    bot.reply_to(message, msg)


@bot.message_handler(commands=["keys"])
def listkeys_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "🚫 No tienes permiso.")

    msg = list_keys()
    bot.reply_to(message, msg)


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

        bin_number = cc[:6]
        binsito = binlist(bin_number)
        if not binsito[0]:
            binsito = (None, "Unknown", "Unknown", "Unknown", "Unknown", "", "Unknown")

        result = ccn_gate(card)

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