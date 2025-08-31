import telebot
import json
import os 
import re
import pytz 
import datetime
from cc_gen import cc_gen
from datetime import timedelta
from flask import Flask, request
import requests
from sagepay import ccn_gate
from telebot import types
from db_store import init_db, registro_usuario, usuario_registrado, usuario_tiene_key, asignar_key_a_usuario, get_user_keys, registrar_uso_spam, ultimo_tiempo_spam, key_expirates

# Configuración 
TOKEN = os.getenv("BOT_TOKEN")
URL = os.getenv("APP_URL")   # 👈 Ejemplo: https://mi-bot.up.railway.app
ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Inicializar DB
init_db()

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

def ver_user(user_id: str):
    """Verifica si el usuario tiene key válida en DB o JSON (prioriza DB)"""
    if usuario_registrado(int(user_id)) and usuario_tiene_key(int(user_id)):
        return True
    users = load_json("users.json")
    if user_id in users:
        expira = datetime.datetime.fromisoformat(users[user_id]["expires"])
        return expira > datetime.datetime.now()
    return False

# =============================
#   COMANDOS Y MENÚS
# =============================
@bot.message_handler(commands=["start"])
def start(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        username = message.from_user.username or ""

        # Registrar usuario en DB
        registro_usuario(user_id, username)

        photo_url = "https://imgur.com/a/ytDQfiM"
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("📂 Gates", callback_data="menu_gates"),
            types.InlineKeyboardButton("🛠 Tools", callback_data="menu_tools")
        )
        markup.row(
            types.InlineKeyboardButton("❌ Exit", callback_data="menu_exit")
        )

        bot.send_message(
            chat_id,
            text="👋 Bienvenido a *Demon Slayer Bot*\n\nSelecciona una opción:",
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
            markup.row(types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back"))
            bot.edit_message_text(
                text=text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
        elif call.data == "menu_tools":
            text = "🛠 *Menú Tools*\n\nAquí estarán tus herramientas."
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🔙 Volver", callback_data="menu_back"))
            bot.edit_message_text(
                text=text,
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
            bot.edit_message_text(
                text="👋 Bienvenido a *Demon Slayer Bot*\n\nSelecciona una opción:",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown",
                reply_markup=markup
            )
        elif call.data == "menu_exit":
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Error en menú: {e}")

# Generar key (solo admin)
@bot.message_handler(commands=["genkey"])
def genkey(message):
    try:
        if message.from_user.id != ADMIN_ID:
            return bot.reply_to(message, "🚫 No tienes permiso para usar este comando.")

        args = message.text.split()
        days = 1
        if len(args) >= 2:
            try:
                days = int(args[1])
                if days < 1:
                    days = 1
            except ValueError:
                return bot.reply_to(message, "Uso: /genkey <días> (ej. /genkey 3)")

        import random, string
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        expires = asignar_key_a_usuario(ADMIN_ID, key, days)

        bot.reply_to(message, f"✅ Key generada:\n\n{key}\nExpira: {expires} (UTC)")
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
        expira_dt = key_expirates(key)
        if expira_dt is None:
            return bot.reply_to(message, "🚫 Key inválida.")
        if expira_dt < datetime.datetime.utcnow():
            return bot.reply_to(message, "🚫 Esa key ya expiró.")

        user_id = message.from_user.id
        registro_usuario(user_id, message.from_user.username or "")
        asignar_key_a_usuario(user_id, key, 1)  # 1 día

        bot.reply_to(message, "✅ Key aceptada, ya puedes usar /gen.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

# =============================
#   FUNCIÓN /GEN
# =============================
@bot.message_handler(commands=['gen'])
def gen(message):
    try:
        user_id = str(message.from_user.id)

        # 🔒 Verificar si el usuario tiene key válida
        if not ver_user(user_id):
            return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')

        # ⏳ Control antispam
        last_time = ultimo_tiempo_spam(user_id)
        if last_time:
            diff = (datetime.datetime.utcnow() - last_time).total_seconds()
            if diff < 10:  # por ejemplo 10 segundos de cooldown
                return bot.reply_to(message, f"⏳ Espera {int(10 - diff)}s antes de usar /gen otra vez.")

        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Uso correcto: /gen <bin> (ej. /gen 411111)")

        bin_input = args[1].strip()

        # 🔥 Generar tarjetas (usa tu función cc_gen)
        cards = cc_gen(bin_input, cantidad=10)  # genera 10 tarjetas por defecto

        if not cards:
            return bot.reply_to(message, "❌ No se pudo generar tarjetas con ese BIN.")

        # 👁️‍🗨️ Info de BIN
        try:
            from cc_gen import bin_lookup
            binsito = bin_lookup(bin_input[:6])
        except Exception:
            binsito = ("Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "🏳️", "Unknown")

        # ✅ Marcar uso para control de spam
        registrar_uso_spam(user_id)

        # 📤 Preparar respuesta
        card_list = "\n".join([f"<code>{c}</code>" for c in cards])

        text = f"""
✅ Tarjetas generadas con éxito

𝗕𝗜𝗡: {bin_input[:6]}
𝗦𝗰𝗵𝗲𝗺𝗲: {binsito[0]}
𝗧𝘆𝗽𝗲: {binsito[2]}
𝗟𝗲𝘃𝗲𝗹: {binsito[3]}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {binsito[4]} {binsito[5]}
𝗕𝗮𝗻𝗸: {binsito[6]}

<b>Tarjetas:</b>
{card_list}

👤 Checked by: @{message.from_user.username or message.from_user.id}
"""

        bot.reply_to(message, text, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error en /gen: {e}")

# =============================
#   FUNCIÓN /SG (SAGEPAY)
# =============================
@bot.message_handler(commands=['sg'])
def sagepay_cmd(message):
    try:
        userid = str(message.from_user.id)

        # 🔒 Verificar si el usuario tiene acceso
        if not ver_user(userid):
            return bot.reply_to(message, '🚫 No estás autorizado, contacta @colale1k.')

        args = message.text.split(" ", 1)
        if len(args) < 2:
            return bot.reply_to(message, "❌ Uso correcto: /sg <cc|mm|yyyy|cvv>")

        card = args[1].strip()
        partes = card.split("|")

        if len(partes) < 4:
            return bot.reply_to(message, "❌ Formato inválido. Ejemplo: /sg 4111111111111111|12|2026|123")

        cc  = partes[0]
        mes = partes[1]
        ano = partes[2]
        cvv = partes[3]

        # 🔎 Extraer BIN (primeros 6 dígitos)
        bin_number = cc[:6]

        try:
            from cc_gen import bin_lookup
            binsito = bin_lookup(bin_number)
            # binsito debería devolver algo tipo (scheme, brand, type, level, country, emoji, bank)
        except Exception:
            binsito = ("Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "🏳️", "Unknown")

        # 🔥 Llamar a tu función en sagepay.py
        result = ccn_gate(card)

        # ✅ / ❌ Detectar si aprobado
        if any(ok in str(result) for ok in ["CVV2 MISMATCH", "Approved", "APPROVED", "0000N7"]):
            estado = "✅ Approved"
        else:
            estado = "❌ Declined"

        text = f"""
{estado}
𝗖𝗮𝗿𝗱: <code>{card}</code>

𝗕𝗜𝗡: {bin_number}
𝗦𝗰𝗵𝗲𝗺𝗲: {binsito[0]}
𝗧𝘆𝗽𝗲: {binsito[2]}
𝗟𝗲𝘃𝗲𝗹: {binsito[3]}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {binsito[4]} {binsito[5]}
𝗕𝗮𝗻𝗸: {binsito[6]}

<b>Respuesta:</b> <code>{result}</code>

👤 Checked by: @{message.from_user.username or message.from_user.id}
"""

        bot.reply_to(message, text, parse_mode="HTML")

    except Exception as e:
        bot.reply_to(message, f"❌ Error en /sg: {e}")
# =============================
#   FLASK ROUTES (WEBHOOK)
# =============================
@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    return "Webhook set!", 200

# =============================
#   MAIN
# =============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))