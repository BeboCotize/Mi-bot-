
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
URL = os.getenv("APP_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))

bot = telebot.TeleBot(TOKEN)

# Inicializar DB
init_db()

# =============================
#   HELPERS (mantén o elimina si ya no usas JSON)
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
#   NUEVO /START CON MENÚ (igual que antes)
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
    # Ejemplo básico adaptado a tu flujo. Aquí podría integrarse la verificación de spam y keys.
    try:
        user_id = message.from_user.id
        # Verificar si el usuario está registrado y tiene key para limitar spam
        registrado = True  # asumiendo que /start ya registra
        con_key = usuario_tiene_key(user_id)
        # Lógica existente de /gen (tu implementación actual debe ir aquí)
        bot.reply_to(message, "Función /gen integrada con DB (completa según tu lógica).")
    except Exception as e:
        bot.reply_to(message, f"❌ Error en /gen: {e}")

# =============================
#   FUNCIÓN /SG (SAGEPAY)
# =============================
@bot.message_handler(commands=['sg'])
def sagepay_cmd(message):
    try:
        user_id = message.from_user.id
        # Permite usar solo si está registrado (opcional) y con control de spam
        # Reutiliza tu flujo existente de /sg, con puntos para DB si quieres verificar key/permiso
        bot.reply_to(message, "Ejecutando SagePay (sg) — integrada con DB (aquí va tu flujo).")
    except Exception as e:
        bot.reply_to(message, f"❌ Error en /sg: {e}")

# Inicio del polling
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    bot = telebot.TeleBot(TOKEN)
    bot.infinity_polling()
