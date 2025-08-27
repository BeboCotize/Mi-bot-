import telebot
import json
import os
import re
import pytz 
import datetime
from cc_gen import cc_gen  # tu cc_gen.py debe tener estas funciones
from datetime import timedelta
from flask import Flask, request

# =============================
#   CONFIG BOT
# =============================
TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")  # ej: https://mi-bot-production.up.railway.app
ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))  # tu ID de admin

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
#   COMANDOS
# =============================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "👋 Bienvenido. Reclama tu key con /claim <key>\n"
                          "Cuando tengas acceso podrás usar /gen <bin>.")

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
    userid = str(message.from_user.id)
    
    if not ver_user(userid):
        return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')
    
    # Capturar argumento completo después de /gen
    args = message.text.split(" ", 1)
    if len(args) < 2:
        return bot.reply_to(message, "❌ Debes especificar un BIN o formato.")
    
    inputcc = args[1].strip()  # puede ser "47926100300xxxx|08|2030|rnd"
    partes = inputcc.split("|")

    cc  = partes[0] if len(partes) > 0 else ""
    mes = partes[1] if len(partes) > 1 else "xx"
    ano = partes[2] if len(partes) > 2 else "xxxx"
    cvv = partes[3] if len(partes) > 3 else "rnd"

    if len(cc) < 6:
        return bot.reply_to(message, "❌ extra incompleta")
    
    bin_number = cc[:6]
    if cc.isdigit():
        cc = cc[:12]

    if mes.isdigit():
        if ano.isdigit():
            if len(ano) == 2: 
                ano = '20' + ano
            IST = pytz.timezone('US/Central')
            now = datetime.datetime.now(IST)
            if (datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > 
                datetime.datetime.strptime(f'{mes}-{ano}', "%m-%Y")):
                return bot.reply_to(message, "❌ fecha incorrecta")

    card = cc_gen(cc, mes, ano, cvv)
    if card:
        cc1,cc2,cc3,cc4,cc5,cc6,cc7,cc8,cc9,cc10 = card

        extra = str(cc) + 'xxxxxxxxxxxxxxxxxxxxxxx'
        mes_2 = mes if mes not in ['xx', 'rnd'] else mes
        if ano not in ['xxxx','rnd']:
            ano_2 = '20'+ano if len(ano)==2 else ano
        else:
            ano_2 = ano
        cvv_2 = cvv if cvv not in ['xxx','rnd','xxxx'] else cvv

        binsito = binlist(bin_number)
        if binsito[0] != None:
            text = f"""
🇩🇴 DEMON SLAYER GENERATOR 🇩🇴
⚙️──────────────⚙️

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

𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} - {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

𝗘𝗫𝗧𝗥𝗔: <code>{extra[0:16]}|{mes_2}|{ano_2}|{cvv_2}</code>
"""
            bot.reply_to(message, text, parse_mode="HTML")

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
    # Si corres en local → usa polling
    if os.getenv("RAILWAY_ENVIRONMENT") is None:
        print("🤖 Bot en ejecución local con polling...")
        bot.infinity_polling()
    else:
        # Si corres en Railway → usa webhook
        port = int(os.environ.get("PORT", 5000))
        bot.remove_webhook()
        bot.set_webhook(url=f"{URL}/{TOKEN}")
        print(f"🚀 Bot corriendo en Railway en {URL}")
        app.run(host="0.0.0.0", port=port)