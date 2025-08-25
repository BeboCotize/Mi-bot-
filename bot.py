import json
import os
import random
import string
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================== CONFIG ==================
TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"   # <-- pon tu token aquí
ADMIN_IDS = [6629555218]      # <-- IDs de admins

# Archivos de almacenamiento
USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

# ================== UTILIDADES ==================

def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        try:
            return json.load(f)
        except:
            return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_users():
    return load_json(USERS_FILE, {})

def save_users(data):
    save_json(USERS_FILE, data)

def get_keys():
    return load_json(KEYS_FILE, {})

def save_keys(data):
    save_json(KEYS_FILE, data)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def is_banned(user_id: int) -> bool:
    users = get_users()
    return users.get(str(user_id), {}).get("banned", False)

def is_active(user_id: int) -> bool:
    users = get_users()
    info = users.get(str(user_id), {})
    return info.get("active", False) and not info.get("banned", False)

# ================== HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_active(user_id):
        await update.message.reply_text("❌ Debes activar el bot con una key.\nUsa: `.claim <key>`")
        return
    await update.message.reply_text("✅ Bienvenido! Usa `.gen` para generar tarjetas.")

# --- CLAIM KEY ---
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) != 1:
        await update.message.reply_text("Uso: `.claim <key>`")
        return

    key = context.args[0]
    keys = get_keys()
    if key not in keys:
        await update.message.reply_text("❌ Key inválida.")
        return

    data = keys[key]
    if data["used"]:
        await update.message.reply_text("❌ Esa key ya fue usada.")
        return

    expiry = datetime.now() + timedelta(days=int(data["days"]))
    users = get_users()
    users[user_id] = {"active": True, "banned": False, "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S")}
    save_users(users)

    keys[key]["used"] = True
    save_keys(keys)

    await update.message.reply_text(f"✅ Key activada! Expira el: {expiry.strftime('%Y-%m-%d %H:%M:%S')}")

# --- GENERAR KEYS (admin) ---
async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return await update.message.reply_text("❌ No tienes permisos.")

    if len(context.args) != 1:
        return await update.message.reply_text("Uso: `.genkey <días>`")

    try:
        days = int(context.args[0])
    except:
        return await update.message.reply_text("❌ Debes poner un número de días.")

    key = "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys = get_keys()
    keys[key] = {"days": days, "used": False}
    save_keys(keys)

    await update.message.reply_text(f"🔑 Key generada:\n`{key}` ({days} días)", parse_mode="Markdown")

# --- BAN ---
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")

    if len(context.args) != 1:
        return await update.message.reply_text("Uso: `.ban <user_id>`")

    uid = context.args[0]
    users = get_users()
    if uid not in users:
        users[uid] = {"active": False, "banned": True}
    else:
        users[uid]["banned"] = True
    save_users(users)

    await update.message.reply_text(f"🚫 Usuario {uid} baneado.")

# --- UNBAN ---
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")

    if len(context.args) != 1:
        return await update.message.reply_text("Uso: `.unban <user_id>`")

    uid = context.args[0]
    users = get_users()
    if uid not in users:
        return await update.message.reply_text("Ese usuario no existe en la base de datos.")

    users[uid]["banned"] = False
    save_users(users)

    await update.message.reply_text(f"✅ Usuario {uid} desbaneado.")

# --- ADMIN LIST ---
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")

    users = get_users()
    msg = "📋 Lista de usuarios:\n\n"
    for uid, info in users.items():
        estado = "🚫 Baneado" if info.get("banned") else "✅ Activo" if info.get("active") else "❌ Inactivo"
        msg += f"👤 {uid} → {estado}\n"
    await update.message.reply_text(msg)

# --- GEN (tarjetas random con Luhn simple) ---
def luhn_reservado(cc: str) -> bool:
    total = 0
    reverse = cc[::-1]
    for i, num in enumerate(reverse):
        n = int(num)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0

def generar_tarjeta():
    while True:
        cc = "".join(random.choice(string.digits) for _ in range(16))
        if luhn_reservado(cc):
            mes = str(random.randint(1, 12)).zfill(2)
            ano = str(random.randint(2025, 2030))
            cvv = str(random.randint(100, 999))
            return f"{cc}|{mes}|{ano}|{cvv}"

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_active(user_id):
        return await update.message.reply_text("❌ Debes activar el bot con una key.\nUsa `.claim <key>`")
    card = generar_tarjeta()
    await update.message.reply_text(f"💳 {card}")

# --- BOTONES ---
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_active(update.effective_user.id):
        return await update.message.reply_text("❌ Debes activar el bot con una key.\nUsa `.claim <key>`")

    keyboard = [
        [InlineKeyboardButton("🔧 Herramientas", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📌 Menú principal:", reply_markup=reply_markup)

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🔧 Aquí están las herramientas disponibles.")
    elif query.data == "gateway":
        keyboard = [
            [InlineKeyboardButton("Hola xd 1", callback_data="xd1")],
            [InlineKeyboardButton("Hola xd 2", callback_data="xd2")],
            [InlineKeyboardButton("Hola xd 3", callback_data="xd3")],
            [InlineKeyboardButton("Hola xd 4", callback_data="xd4")]
        ]
        await query.edit_message_text("🌐 Gateway:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text(f"Hiciste click en: {query.data}")

# ================== MAIN ==================
def main():
    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("gen", gen))
    app.add_handler(CommandHandler("menu", menu))

    # Handler de botones
    app.add_handler(CallbackQueryHandler(buttons))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()