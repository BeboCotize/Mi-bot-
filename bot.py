import os
import random
import string
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CallbackContext
from telegram.ext import CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "data.json"

# Prefijos permitidos
PREFIXES = [".", "!", "*", "?"]

# Base de datos en memoria
users = {}
banned_users = {}
keys = []

# Lista de administradores (tu ID aquí)
ADMINS = [6629555218]

# ---------------- Persistencia ----------------
def save_data():
    data = {
        "users": users,
        "banned_users": banned_users,
        "keys": keys
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_data():
    global users, banned_users, keys
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            users = data.get("users", {})
            banned_users = data.get("banned_users", {})
            keys = data.get("keys", [])

# ---------------- Prefijos ----------------
def has_prefix(text: str, command: str) -> bool:
    return any(text.lower().startswith(p + command) for p in PREFIXES)

async def prefixed_command(update: Update, context: CallbackContext, command: str, func):
    text = update.message.text.strip()
    if has_prefix(text, command):
        await func(update, context)
        save_data()

# ---------------- Registro ----------------
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id in banned_users:
        await update.message.reply_text("🚫 Estás baneado y no puedes usar el bot.")
        return

    if user_id not in users:
        users[user_id] = {"registered": True, "key": None}
        save_data()

    keyboard = [
        [InlineKeyboardButton("🛠 Tools", callback_data="tools")],
        [InlineKeyboardButton("🌐 Gateway", callback_data="gateway")]
    ]
    await update.message.reply_text("✅ Registrado con éxito.\nElige una opción:",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🔧 Herramientas")

    elif query.data == "gateway":
        keyboard = [
            [InlineKeyboardButton("hola xd", callback_data="g1")],
            [InlineKeyboardButton("hola xd", callback_data="g2")],
            [InlineKeyboardButton("hola xd", callback_data="g3")],
            [InlineKeyboardButton("hola xd", callback_data="g4")],
        ]
        await query.edit_message_text("🌐 Gateway", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- Keys ----------------
async def genkey(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("🚫 Solo administradores pueden generar keys.")
        return
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    keys.append(key)
    save_data()
    await update.message.reply_text(f"🔑 Key generada: `{key}`", parse_mode="Markdown")

async def redeem(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Usa: .redeem <KEY>")
        return
    key = args[1]
    if key in keys:
        users[user_id]["key"] = key
        keys.remove(key)
        save_data()
        await update.message.reply_text("✅ Key canjeada con éxito. Ahora puedes usar todos los comandos.")
    else:
        await update.message.reply_text("❌ Key inválida o ya usada.")

# ---------------- Admin ----------------
async def ban(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("🚫 No autorizado.")
        return
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Usa: .ban <user_id>")
        return
    uid = args[1]
    banned_users[uid] = "Baneado por admin"
    save_data()
    await update.message.reply_text(f"🚫 Usuario {uid} baneado.")

async def unban(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("🚫 No autorizado.")
        return
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Usa: .unban <user_id>")
        return
    uid = args[1]
    banned_users.pop(uid, None)
    save_data()
    await update.message.reply_text(f"✅ Usuario {uid} desbaneado.")

async def users_list(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMINS:
        await update.message.reply_text("🚫 No autorizado.")
        return
    msg = "👥 Usuarios registrados:\n"
    for uid, data in users.items():
        msg += f"- {uid} | Key: {data['key']}\n"
    msg += "\n🚫 Baneados:\n"
    for uid, reason in banned_users.items():
        msg += f"- {uid} | {reason}\n"
    await update.message.reply_text(msg)

# ---------------- Generador tarjetas ----------------
def luhn_checksum(card_number):
    def digits_of(n): return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd = digits[-1::-2]
    even = digits[-2::-2]
    checksum = sum(odd)
    for d in even:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def generate_card(base):
    while True:
        num = base + ''.join(random.choices("0123456789", k=16-len(base)))
        if luhn_checksum(num) == 0:
            month = str(random.randint(1, 12)).zfill(2)
            year = str(random.randint(2025, 2030))
            cvv = str(random.randint(100, 999))
            return f"{num}|{month}|{year}|{cvv}"

async def gen(update: Update, context: CallbackContext):
    args = update.message.text.split()
    if len(args) < 2:
        await update.message.reply_text("❌ Usa: .gen <bin>")
        return
    base = args[1]
    card = generate_card(base)
    await update.message.reply_text(f"💳 {card}")

# ---------------- Main ----------------
def main():
    load_data()  # cargar datos guardados
    app = Application.builder().token(TOKEN).build()

    # Registro
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/start$"), start))
    app.add_handler(CallbackQueryHandler(buttons))

    # Prefijos
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "genkey", genkey)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "redeem", redeem)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "ban", ban)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "unban", unban)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "users", users_list)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "gen", gen)))

    print("🤖 Bot corriendo con persistencia en JSON...")
    app.run_polling()

if __name__ == "__main__":
    main()