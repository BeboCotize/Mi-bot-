import os
import telebot
from telebot import types
from db import user_has_access, add_user, claim_key
from cc_gen import cc_gen, bin_lookup
from sagepay import ccn_gate

# 🔑 TOKEN desde variable de entorno (Railway/Heroku) o local
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


# ────────────────
#   /start
# ────────────────
@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    add_user(user_id)
    text = (
        "👋 Bienvenido!\n\n"
        "🔐 Debes tener una <b>key activa</b> para usar los comandos.\n\n"
        "Comandos disponibles:\n"
        "/gen <bin> → Generar tarjetas\n"
        "/bin <bin> → Info del BIN\n"
        "/sg <cc|mm|yyyy|cvv> → Check Sagepay\n"
        "/claim <key> → Reclamar key"
    )
    bot.reply_to(message, text)


# ────────────────
#   /claim
# ────────────────
@bot.message_handler(commands=['claim'])
def claim(message):
    user_id = str(message.from_user.id)
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "❌ Uso: /claim <key>")

    key = parts[1]
    if claim_key(user_id, key):
        bot.reply_to(message, "✅ Key activada correctamente. Ya puedes usar los comandos.")
    else:
        bot.reply_to(message, "❌ Key inválida o ya usada.")


# ────────────────
#   /gen
# ────────────────
@bot.message_handler(commands=['gen'])
def gen(message):
    user_id = str(message.from_user.id)
    if not user_has_access(user_id):
        return bot.reply_to(message, "🚫 Necesitas una key activa para usar este comando.")

    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "❌ Uso: /gen 457173xxxxxxxxxx|mm|yyyy|cvv")

    base = parts[1]
    result = cc_gen(base)
    bot.reply_to(message, "<b>Generated CCs:</b>\n" + "".join(result))


# ────────────────
#   /bin
# ────────────────
@bot.message_handler(commands=['bin'])
def bin_info(message):
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "❌ Uso: /bin 457173")

    bin_number = parts[1][:6]
    data = bin_lookup(bin_number)

    if "error" in data:
        return bot.reply_to(message, f"❌ Error: {data['error']}")

    text = f"""💳 BIN: <b>{bin_number}</b>
🏦 Banco: {data['bank']}
🌍 País: {data['country']} {data['emoji']}
💠 Marca: {data['brand']}
📌 Tipo: {data['scheme']} - {data['type']}"""

    bot.reply_to(message, text)


# ────────────────
#   /sg
# ────────────────
@bot.message_handler(commands=['sg'])
def sagepay_cmd(message):
    user_id = str(message.from_user.id)
    if not user_has_access(user_id):
        return bot.reply_to(message, "🚫 Necesitas una key activa para usar este comando.")

    args = message.text.split(" ", 1)
    if len(args) < 2:
        return bot.reply_to(message, "❌ Uso: /sg <cc|mm|yyyy|cvv>")

    card = args[1].strip()
    result = ccn_gate(card)

    estado = "✅ Approved" if "CVV2 MISMATCH|0000N7|" in str(result) or "Approved" in str(result) else "❌ Declined"

    bin_number = card.split("|")[0][:6]
    bininfo = bin_lookup(bin_number)
    if "error" in bininfo:
        bin_text = f"⚠️ {bininfo['error']}"
    else:
        bin_text = (
            f"𝗕𝗜𝗡: {bininfo['scheme']} - {bininfo['type']} - {bininfo['brand']}\n"
            f"🌍 {bininfo['country']} {bininfo['emoji']}\n"
            f"🏦 {bininfo['bank']}\n"
        )

    text = f"""
{estado}
Card: <code>{card}</code>

{bin_text}
<b>Respuesta:</b> <code>{result}</code>

Checked by: @{message.from_user.username or message.from_user.id}
"""
    bot.reply_to(message, text)


# ────────────────
#   RUN
# ────────────────
print("🤖 Bot corriendo...")
bot.infinity_polling()