import telebot
import os 
import pytz 
from datetime import timedelta, datetime
from flask import Flask, request
from telebot import types
import random
import sqlite3 

from cc_gen import cc_gen
from sagepay import ccn_gate
from db import init_db, add_user, user_has_access, generate_key, claim_key

# =============================
#   CONFIG BOT
# =============================
TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")  # ej: https://mi-bot-production.up.railway.app
ADMIN_ID = os.getenv("ADMIN_ID", "6629555218")  # ⚠️ se mantiene como string
bot = telebot.TeleBot(TOKEN)

# Inicializar DB
init_db()


# =============================
#   START
# =============================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    add_user(user_id)  # lo agrega si no existe en DB

    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("📂 Gates", callback_data="gates"),
        telebot.types.InlineKeyboardButton("🛠 Tools", callback_data="tools")
    )
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
        return bot.reply_to(message, "⛔ No tienes permiso para usar este comando.")

    try:
        args = message.text.split()[1:]
        if len(args) != 1:
            return bot.reply_to(message, "Uso: /genkey <días>")

        dias = int(args[0])
        key = f"Demon{random.randint(1000,9999)}"
        expira = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")

        generate_key(key, expira)

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
            return bot.reply_to(message, "Uso: /claim <key>")

        key = args[0]
        user_id = str(message.from_user.id)

        if claim_key(user_id, key):
            bot.reply_to(message, f"✅ Key reclamada con éxito.\n👤 Usuario: @{message.from_user.username}")
        else:
            bot.reply_to(message, "❌ Key inválida o ya expirada.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error interno: {e}")


# =============================
#   MYINFO
# =============================
@bot.message_handler(commands=['myinfo'])
def myinfo(message):
    user_id = str(message.from_user.id)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT has_key, key_expiration FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return bot.reply_to(message, "❌ No estás registrado.")

    has_key, exp = row
    if not has_key or not exp:
        return bot.reply_to(message, "❌ No tienes ninguna key activa.")

    expira_dt = datetime.fromisoformat(exp)
    if expira_dt < datetime.now():
        return bot.reply_to(
            message,
            f"👤 Usuario: @{message.from_user.username}\n"
            f"⏳ Tu key expiró el: {expira_dt.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"⚠️ Reclama una nueva."
        )

    bot.reply_to(
        message,
        f"👤 Usuario: @{message.from_user.username}\n"
        f"⏳ Key activa hasta: {expira_dt.strftime('%Y-%m-%d %H:%M:%S')}"
    )


# =============================
#   LISTKEYS (solo admin)
# =============================
@bot.message_handler(commands=['listkeys'])
def listkeys(message):
    if str(message.from_user.id) != ADMIN_ID:
        return bot.reply_to(message, "⛔ No tienes permiso para usar este comando.")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT key, expiration FROM keys")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return bot.reply_to(message, "📂 No hay keys disponibles.")

    text = "🔑 Keys disponibles:\n\n"
    for k, exp in rows:
        text += f"• {k} → Expira: {exp}\n"

    bot.reply_to(message, text)


# =============================
#   /GEN (GENERATOR)
# =============================
@bot.message_handler(commands=['gen'])
def gen(message):
    try:
        userid = str(message.from_user.id)

        if not user_has_access(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, reclama una key.')

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
        
        if cc.isdigit():
            cc = cc[:12]

        if mes.isdigit() and ano.isdigit():
            if len(ano) == 2: 
                ano = '20' + ano
            IST = pytz.timezone('US/Central')
            now = datetime.now(IST)
            if (datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > 
                datetime.strptime(f'{mes}-{ano}', "%m-%Y")):
                return bot.reply_to(message, "❌ Fecha incorrecta")

        cards = cc_gen(cc, mes, ano, cvv)
        if not cards:
            return bot.reply_to(message, "❌ No se pudo generar tarjetas, revisa el BIN o formato.")

        text = "🇩🇴 DEMON SLAYER GENERATOR 🇩🇴\n⚙️──────────────⚙️\n"
        for c in cards:
            text += f"<code>{c.strip()}</code>\n"

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

        if not user_has_access(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, reclama una key.')

        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Uso correcto: /sg <cc|mm|yyyy|cvv>")

        card = args[1].strip()
        result = ccn_gate(card)

        if "Approved" in str(result):
            estado = "✅ Approved"
        else:
            estado = "❌ Declined"

        text = f"""
{estado}
Card: <code>{card}</code>


𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[2]} - {binsito[3]}
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