import json
import random
import string
import os
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------
# Archivos de datos
# ---------------------------
USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

def load_json(filename, default):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump(default, f)
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

users = load_json(USERS_FILE, {})
keys = load_json(KEYS_FILE, {})

# ---------------------------
# Helpers
# ---------------------------
ADMINS = [6629555218]  # IDs de admins aquí

def is_admin(user_id):
    return user_id in ADMINS

def is_banned(user_id):
    return users.get(str(user_id), {}).get("banned", False)

def is_active(user_id):
    user = users.get(str(user_id))
    if not user:
        return False
    if user.get("banned", False):
        return False
    exp = user.get("exp")
    if not exp:
        return False
    return datetime.now() < datetime.fromisoformat(exp)

def activate_user(user_id, days):
    exp_date = datetime.now() + timedelta(days=days)
    users[str(user_id)] = {"exp": exp_date.isoformat(), "banned": False}
    save_json(USERS_FILE, users)

def generate_key(days=1):
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    exp = datetime.now() + timedelta(days=days)
    keys[key] = exp.isoformat()
    save_json(KEYS_FILE, keys)
    return key

def use_key(key, user_id):
    if key not in keys:
        return False, "❌ Key inválida."
    exp_date = datetime.fromisoformat(keys[key])
    if datetime.now() > exp_date:
        return False, "❌ Key expirada."
    activate_user(user_id, (exp_date - datetime.now()).days)
    del keys[key]
    save_json(KEYS_FILE, keys)
    return True, "✅ Key activada con éxito."

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd = digits[-1::-2]
    even = digits[-2::-2]
    checksum = sum(odd)
    for d in even:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def generate_luhn(base_number):
    check_digit = (10 - luhn_checksum(base_number + "0")) % 10
    return base_number + str(check_digit)

# ---------------------------
# Middlewares
# ---------------------------
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        return True
    if is_banned(user_id):
        await update.message.reply_text("⛔ Estás baneado.")
        return False
    if not is_active(user_id):
        await update.message.reply_text("❌ Debes activar el bot con una key. Usa `.claim <key>`")
        return False
    return True

# ---------------------------
# Handlers
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔧 Tools", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")]
    ]
    await update.message.reply_text("👋 Bienvenido al bot!", reply_markup=InlineKeyboardMarkup(keyboard))

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🔧 Herramientas")
    elif query.data == "gateway":
        keyboard = [
            [InlineKeyboardButton("hola xd", callback_data="h1")],
            [InlineKeyboardButton("hola xd", callback_data="h2")],
            [InlineKeyboardButton("hola xd", callback_data="h3")],
            [InlineKeyboardButton("hola xd", callback_data="h4")],
        ]
        await query.edit_message_text("🌐 Gateway", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text("hola xd")

# ---- CLAIM / REDEEM ----
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Usa `.claim <key>`")
        return
    key = context.args[0]
    ok, msg = use_key(key, user_id)
    await update.message.reply_text(msg)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Alias antiguo
    return await claim(update, context)

# ---- GENKEY ----
async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Solo admins.")
        return
    days = 1
    if context.args:
        try:
            days = int(context.args[0])
        except:
            pass
    key = generate_key(days)
    await update.message.reply_text(f"🔑 Key generada: `{key}`", parse_mode="Markdown")

# ---- BAN / UNBAN / ADMIN ----
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Solo admins.")
        return
    if not context.args:
        await update.message.reply_text("Uso: .ban <id>")
        return
    target = context.args[0]
    if target in users:
        users[target]["banned"] = True
        save_json(USERS_FILE, users)
        await update.message.reply_text(f"🚫 Usuario {target} baneado.")
    else:
        await update.message.reply_text("Usuario no encontrado.")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Solo admins.")
        return
    if not context.args:
        await update.message.reply_text("Uso: .unban <id>")
        return
    target = context.args[0]
    if target in users:
        users[target]["banned"] = False
        save_json(USERS_FILE, users)
        await update.message.reply_text(f"✅ Usuario {target} desbaneado.")
    else:
        await update.message.reply_text("Usuario no encontrado.")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Solo admins.")
        return
    text = "👑 Lista de usuarios:\n"
    for uid, data in users.items():
        status = "BANEADO" if data.get("banned") else "Activo"
        exp = data.get("exp", "N/A")
        text += f"- {uid} → {status} (expira {exp})\n"
    await update.message.reply_text(text)

# ---- GEN ----
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return

    if not context.args:
        await update.message.reply_text("Uso: `.gen <bin|base_number|pattern>`")
        return

    inp = context.args[0]
    results = []

    if "x" in inp.lower():
        for _ in range(10):
            card = ""
            for ch in inp:
                if ch.lower() == "x":
                    card += str(random.randint(0, 9))
                else:
                    card += ch
            card = generate_luhn(card[:-1])
            mm = str(random.randint(1, 12)).zfill(2)
            yy = str(random.randint(2025, 2030))
            cvv = str(random.randint(100, 999))
            results.append(f"{card}|{mm}|{yy}|{cvv}")
    else:
        for _ in range(10):
            base = inp
            while len(base) < 15:
                base += str(random.randint(0, 9))
            card = generate_luhn(base)
            mm = str(random.randint(1, 12)).zfill(2)
            yy = str(random.randint(2025, 2030))
            cvv = str(random.randint(100, 999))
            results.append(f"{card}|{mm}|{yy}|{cvv}")

    await update.message.reply_text("\n".join(results))

# ---------------------------
# Main
# ---------------------------
def main():
    app = ApplicationBuilder().token("TU_TOKEN_AQUI").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.claim"), claim))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.redeem"), redeem))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.genkey"), genkey))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.ban"), ban))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.unban"), unban))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.admin"), admin))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex(r"^\.gen"), gen))

    app.add_handler(MessageHandler(filters.Regex(r"^/claim"), claim))
    app.add_handler(MessageHandler(filters.Regex(r"^/redeem"), redeem))
    app.add_handler(MessageHandler(filters.Regex(r"^/genkey"), genkey))
    app.add_handler(MessageHandler(filters.Regex(r"^/ban"), ban))
    app.add_handler(MessageHandler(filters.Regex(r"^/unban"), unban))
    app.add_handler(MessageHandler(filters.Regex(r"^/admin"), admin))
    app.add_handler(MessageHandler(filters.Regex(r"^/gen"), gen))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_access))
    app.add_handler(MessageHandler(filters.ALL, check_access))
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, check_access))
    app.add_handler(MessageHandler(filters.UpdateType.CALLBACK_QUERY, buttons))

    print("🤖 Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()