# comandos.py
import random
import datetime
from telegram import Update
from telegram.ext import ContextTypes
from db import (
    add_user, is_user_registered, is_banned, ban_user, unban_user,
    is_admin, add_admin, generate_key, redeem_key
)

# -------------------- Luhn --------------------
def luhn_resolve(number):
    digits = [int(x) for x in str(number)]
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    total = sum(digits)
    return (10 - (total % 10)) % 10


def generate_card(bin_pattern):
    """Generador de tarjetas reales con Luhn"""
    if "x" in bin_pattern.lower():
        card = ""
        for ch in bin_pattern:
            if ch.lower() == "x":
                card += str(random.randint(0, 9))
            else:
                card += ch
        check_digit = luhn_resolve(card)
        card = card[:-1] + str(check_digit)
    else:
        card = bin_pattern
        if len(card) < 16:
            while len(card) < 15:
                card += str(random.randint(0, 9))
            card += str(luhn_resolve(card))

    # Fecha y CVV
    month = str(random.randint(1, 12)).zfill(2)
    year = str(random.randint(2025, 2030))
    cvv = str(random.randint(100, 999))
    return f"{card}|{month}|{year}|{cvv}"


# -------------------- COMANDOS --------------------

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    try:
        target = int(context.args[0])
        ban_user(target)
        await update.message.reply_text(f"🚫 Usuario {target} baneado.")
    except:
        await update.message.reply_text("Uso: .ban <user_id>")


async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    try:
        target = int(context.args[0])
        unban_user(target)
        await update.message.reply_text(f"✅ Usuario {target} desbaneado.")
    except:
        await update.message.reply_text("Uso: .unban <user_id>")


async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    try:
        target = int(context.args[0])
        add_admin(target)
        await update.message.reply_text(f"👑 Usuario {target} ahora es administrador.")
    except:
        await update.message.reply_text("Uso: .admin <user_id>")


async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos para usar este comando.")
        return
    try:
        days = int(context.args[0])
        key = f"KEY-{random.randint(10000,99999)}"
        generate_key(key, days)
        await update.message.reply_text(f"🔑 Key generada:\n`{key}`\nValidez: {days} días", parse_mode="Markdown")
    except:
        await update.message.reply_text("Uso: .genkey <días>")


async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        key = context.args[0]
        if redeem_key(user_id, key):
            await update.message.reply_text("✅ Key canjeada correctamente. Acceso activado.")
        else:
            await update.message.reply_text("❌ Key inválida o ya usada.")
    except:
        await update.message.reply_text("Uso: .redeem <key>")


async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not is_user_registered(user_id):
        await update.message.reply_text("❌ Debes canjear una key para usar este comando.")
        return
    try:
        bin_pattern = context.args[0]
        results = [generate_card(bin_pattern) for _ in range(10)]
        msg = "💳 Tarjetas generadas:\n\n" + "\n".join(results)
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("Uso: .gen <BIN/Pattern>")