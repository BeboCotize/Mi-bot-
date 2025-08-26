import json
import random 
import string
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
 
TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"
ADMIN_IDS = [6629555218]  # <-- pon aquí tu ID de admin

# ================== Manejo de archivos ==================

def load_json(filename, default):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

users = load_json("users.json", {})
keys = load_json("keys.json", {})

# ================== Funciones auxiliares ==================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_banned(user_id):
    return users.get(str(user_id), {}).get("banned", False)

def has_active_key(user_id):
    u = users.get(str(user_id), {})
    if "expires" in u:
        exp = datetime.datetime.fromisoformat(u["expires"])
        return exp > datetime.datetime.now()
    return False

def luhn_resolve(partial_number):
    digits = [int(d) for d in partial_number]
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    checksum = sum(digits) % 10
    return (10 - checksum) % 10

def generate_card(bin_input):
    bin_input = bin_input.replace("x", "0")
    number = bin_input
    while len(number) < 15:
        number += str(random.randint(0, 9))
    check = luhn_resolve(number)
    cc = number + str(check)

    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(2025, 2030))
    cvv = str(random.randint(100, 999))

    return f"{cc}|{month}|{year}|{cvv}"

def generate_cards(bin_input, count=10):
    return [generate_card(bin_input) for _ in range(count)]

# ================== Comandos ==================

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usa: .claim <key>")
        return
    key = context.args[0]
    if key not in keys or keys[key]["used"]:
        await update.message.reply_text("❌ Key inválida o usada")
        return
    exp_date = datetime.datetime.now() + datetime.timedelta(days=keys[key]["days"])
    users[str(update.effective_user.id)] = {
        "expires": exp_date.isoformat(),
        "banned": False
    }
    keys[key]["used"] = True
    save_json("users.json", users)
    save_json("keys.json", keys)
    await update.message.reply_text(f"✅ Key activada! Expira el: {exp_date}")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usa: .genkey <días>")
        return
    try:
        days = int(context.args[0])
    except:
        await update.message.reply_text("❌ Número inválido")
        return
    key = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    keys[key] = {"days": days, "used": False}
    save_json("keys.json", keys)
    await update.message.reply_text(f"🔑 Key generada: {key} ({days} días)")

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_banned(user_id):
        await update.message.reply_text("🚫 Estás baneado.")
        return
    if not has_active_key(user_id):
        await update.message.reply_text("❌ Debes activar el bot con una key. Usa .claim <key>")
        return
    if not context.args:
        await update.message.reply_text("❌ Usa: .gen <BIN>")
        return

    bin_input = context.args[0]
    cards = generate_cards(bin_input, 10)
    msg = "\n".join(cards)

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_input}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] == "regen":
        bin_input = data[1]
        cards = generate_cards(bin_input, 10)
        msg = "\n".join(cards)
        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen|{bin_input}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup)

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No tienes permiso.")
        return
    text = "📋 Usuarios:\n"
    for uid, info in users.items():
        estado = "🚫 Baneado" if info.get("banned", False) else "✅ Activo"
        text += f"{uid} - {estado}\n"
    await update.message.reply_text(text)

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usa: .ban <id>")
        return
    uid = context.args[0]
    if uid in users:
        users[uid]["banned"] = True
        save_json("users.json", users)
        await update.message.reply_text(f"🚫 Usuario {uid} baneado")
    else:
        await update.message.reply_text("❌ Usuario no encontrado")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ No tienes permiso.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usa: .unban <id>")
        return
    uid = context.args[0]
    if uid in users:
        users[uid]["banned"] = False
        save_json("users.json", users)
        await update.message.reply_text(f"✅ Usuario {uid} desbaneado")
    else:
        await update.message.reply_text("❌ Usuario no encontrado")

# ================== MAIN ==================

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("claim", claim))
    application.add_handler(CommandHandler("genkey", genkey))
    application.add_handler(CommandHandler("gen", gen))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == "__main__":
    main()