import logging
import random
import string
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# --- CONFIG ---
TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"
ADMIN_ID = 6629555218  # tu ID de admin
USERS_FILE = "users.json"
KEYS_FILE = "keys.json"

# --- LOG ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- DATA ---
try:
    with open(USERS_FILE, "r") as f:
        users = json.load(f)
except:
    users = {}

try:
    with open(KEYS_FILE, "r") as f:
        keys = json.load(f)
except:
    keys = {}

# --- SAVE ---
def save_data():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

# --- LUHN ---
def luhn(card_number):
    digits = [int(d) for d in str(card_number)]
    for i in range(len(digits)-2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    return sum(digits) % 10 == 0

# --- GENERADOR DE TARJETAS ---
def generar_tarjetas(bin_code, cantidad=10):
    tarjetas = []
    for _ in range(cantidad):
        base = bin_code
        while len(base) < 15:
            base += str(random.randint(0, 9))
        for i in range(10):
            check_digit = str(i)
            if luhn(base + check_digit):
                cc = base + check_digit
                break
        mes = str(random.randint(1, 12)).zfill(2)
        año = str(random.randint(2025, 2030))
        cvv = str(random.randint(100, 999))
        tarjetas.append(f"{cc}|{mes}|{año}|{cvv}")
    return "\n".join(tarjetas)

# --- ADMIN ---
def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ No eres admin.")
        return
    update.message.reply_text(f"Usuarios:\n{list(users.keys())}")

# --- GENKEY ---
def genkey(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ No eres admin.")
        return
    if len(context.args) == 0:
        update.message.reply_text("Usa: .genkey <días>")
        return
    dias = int(context.args[0])
    key = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    expira = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
    keys[key] = expira
    save_data()
    update.message.reply_text(f"🔑 Key generada: {key} ({dias} días)")

# --- CLAIM ---
def claim(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if len(context.args) == 0:
        update.message.reply_text("Usa: .claim <key>")
        return
    key = context.args[0]
    if key in keys:
        expira = keys[key]
        users[user_id] = expira
        del keys[key]
        save_data()
        update.message.reply_text(f"✅ Key activada! Expira el: {expira}")
    else:
        update.message.reply_text("❌ Key inválida.")

# --- VERIFICAR USER ---
def check_user(user_id):
    if str(user_id) not in users:
        return False
    expira = datetime.strptime(users[str(user_id)], "%Y-%m-%d %H:%M:%S")
    return datetime.now() < expira

# --- GEN ---
def gen(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not check_user(user_id):
        update.message.reply_text("❌ Debes activar el bot con una key.\nUsa .claim <key>")
        return
    if len(context.args) == 0:
        update.message.reply_text("Usa: .gen <bin>")
        return

    bin_code = context.args[0]
    tarjetas = generar_tarjetas(bin_code, 10)

    keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen:{bin_code}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(f"💳 Generadas 10 tarjetas:\n\n{tarjetas}", reply_markup=reply_markup)

# --- BOTÓN DE REGENERAR ---
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data.startswith("regen:"):
        bin_code = query.data.split(":")[1]
        tarjetas = generar_tarjetas(bin_code, 10)
        keyboard = [[InlineKeyboardButton("🔄 Regenerar 10 más", callback_data=f"regen:{bin_code}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"💳 Nuevas 10 tarjetas:\n\n{tarjetas}", reply_markup=reply_markup)

# --- MAIN ---
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("admin", admin))
    dp.add_handler(CommandHandler("genkey", genkey))
    dp.add_handler(CommandHandler("claim", claim))
    dp.add_handler(CommandHandler("gen", gen))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()