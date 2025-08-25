import json
import os
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Archivos de datos
USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

# Admins
ADMINS = ["6629555218"]  # 👉 Pon aquí tus IDs de admin

# ==========================
# Utils
# ==========================

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(user_id):
    return str(user_id) in ADMINS

def is_user_active(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users and users[str(user_id)]["status"] == "active":
        exp = datetime.fromisoformat(users[str(user_id)]["expire"])
        return exp > datetime.now()
    return False

# ==========================
# Keys
# ==========================

def generate_key(days):
    keys = load_json(KEYS_FILE)
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    expire = datetime.now() + timedelta(days=days)
    keys[key] = {"expire": expire.isoformat(), "used": False}
    save_json(KEYS_FILE, keys)
    return key, expire

async def claim(update: Update, context: CallbackContext, args):
    user_id = str(update.effective_user.id)
    if not args:
        await update.message.reply_text("❌ Usa: .claim <key>")
        return
    key = args[0]
    keys = load_json(KEYS_FILE)
    if key in keys and not keys[key]["used"]:
        expire = datetime.fromisoformat(keys[key]["expire"])
        if expire > datetime.now():
            users = load_json(USERS_FILE)
            users[user_id] = {"status": "active", "expire": expire.isoformat(), "banned": False}
            save_json(USERS_FILE, users)
            keys[key]["used"] = True
            save_json(KEYS_FILE, keys)
            await update.message.reply_text(f"✅ Key activada! Expira el: {expire}")
        else:
            await update.message.reply_text("❌ La key ya expiró.")
    else:
        await update.message.reply_text("❌ Key inválida o ya usada.")

# ==========================
# Admin commands
# ==========================

async def genkey(update: Update, context: CallbackContext, args):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not args:
        await update.message.reply_text("❌ Usa: .genkey <días>")
        return
    days = int(args[0])
    key, expire = generate_key(days)
    await update.message.reply_text(f"🔑 Key generada: {key} ({days} días)")

async def ban(update: Update, context: CallbackContext, args):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not args:
        await update.message.reply_text("❌ Usa: .ban <id>")
        return
    target_id = args[0]
    users = load_json(USERS_FILE)
    if target_id in users:
        users[target_id]["banned"] = True
        save_json(USERS_FILE, users)
        await update.message.reply_text(f"🚫 Usuario {target_id} baneado.")
    else:
        await update.message.reply_text("❌ Usuario no encontrado.")

async def unban(update: Update, context: CallbackContext, args):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    if not args:
        await update.message.reply_text("❌ Usa: .unban <id>")
        return
    target_id = args[0]
    users = load_json(USERS_FILE)
    if target_id in users:
        users[target_id]["banned"] = False
        save_json(USERS_FILE, users)
        await update.message.reply_text(f"✅ Usuario {target_id} desbaneado.")
    else:
        await update.message.reply_text("❌ Usuario no encontrado.")

async def admin(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos.")
        return
    users = load_json(USERS_FILE)
    msg = "📋 Usuarios:\n"
    for uid, data in users.items():
        estado = "⛔ Baneado" if data.get("banned", False) else "✅ Activo"
        msg += f"ID: {uid} | Estado: {estado} | Expira: {data['expire']}\n"
    await update.message.reply_text(msg)

# ==========================
# Botones
# ==========================

async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🔧 Herramientas", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Bienvenido! Usa los botones:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == "tools":
        await query.edit_message_text("🛠 Herramientas")
    elif query.data == "gateway":
        keyboard = [
            [InlineKeyboardButton("Hola xd 1", callback_data="h1")],
            [InlineKeyboardButton("Hola xd 2", callback_data="h2")],
            [InlineKeyboardButton("Hola xd 3", callback_data="h3")],
            [InlineKeyboardButton("Hola xd 4", callback_data="h4")]
        ]
        await query.edit_message_text("🌐 Gateway:", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================
# Generador de tarjetas
# ==========================

def luhn_resolver(number):
    digits = [int(x) for x in number]
    for i in range(len(digits)-2, -1, -2):
        d = digits[i] * 2
        if d > 9:
            d -= 9
        digits[i] = d
    return (10 - (sum(digits) % 10)) % 10

def generar_tarjeta(bin_input=None, mes=None, anio=None, cvv=None):
    if not bin_input:
        bin_input = str(random.randint(400000, 499999))

    bin_input = ''.join([str(random.randint(0,9)) if c in ['x','X'] else c for c in bin_input])

    if len(bin_input) < 15:
        while len(bin_input) < 15:
            bin_input += str(random.randint(0,9))

    check_digit = luhn_resolver(bin_input[:15])
    tarjeta = bin_input[:15] + str(check_digit)

    if not mes:
        mes = str(random.randint(1,12)).zfill(2)
    if not anio:
        anio = str(random.randint(2025,2032))
    if not cvv or cvv.lower() == "rnd":
        cvv = str(random.randint(100,999))

    return f"{tarjeta}|{mes}|{anio}|{cvv}"

async def gen(update: Update, context: CallbackContext, args):
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE)

    if user_id not in users or not is_user_active(user_id) or users[user_id].get("banned", False):
        await update.message.reply_text("❌ Debes activar el bot con una key. Usa .claim <key>")
        return

    results = []
    if not args:
        for _ in range(10):
            results.append(generar_tarjeta())
    else:
        parts = args[0].split("|")
        bin_input = parts[0] if len(parts) > 0 else None
        mes = parts[1] if len(parts) > 1 else None
        anio = parts[2] if len(parts) > 2 else None
        cvv = parts[3] if len(parts) > 3 else None
        cantidad = 10 if "x" in (bin_input or "") else 1
        for _ in range(cantidad):
            results.append(generar_tarjeta(bin_input, mes, anio, cvv))

    await update.message.reply_text("\n".join(results))

# ==========================
# Handler central (para comandos con ".")
# ==========================

async def message_handler(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if not text.startswith("."):
        return

    parts = text.split()
    command = parts[0][1:].lower()
    args = parts[1:]

    if command == "claim":
        await claim(update, context, args)
    elif command == "genkey":
        await genkey(update, context, args)
    elif command == "ban":
        await ban(update, context, args)
    elif command == "unban":
        await unban(update, context, args)
    elif command == "admin":
        await admin(update, context)
    elif command == "gen":
        await gen(update, context, args)

# ==========================
# Main
# ==========================

def main():
    app = Application.builder().token("AQUI_TU_TOKEN").build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.COMMAND, message_handler))  # fallback por si alguien usa "/"
    app.add_handler(MessageHandler(filters.Regex(r"^\.start$"), start))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()