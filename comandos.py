import random
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db import (
    ban_user, unban_user, is_user_admin, create_key, redeem_key,
    user_has_access, is_user_banned
)
from utils import luhn_complete, generate_card

ADMIN_ID = 6629555218  # tu ID admin principal

# ---------------------------
# BOTONES
# ---------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not user_has_access(user_id):
        keyboard = [[
            InlineKeyboardButton("🛠 Tools", callback_data="tools"),
            InlineKeyboardButton("🌐 Gateway", callback_data="gateway")
        ]]
        return await update.message.reply_text(
            "👋 Bienvenido!\n\nPara usar el bot debes registrarte.\n"
            "Usa `/redeem <KEY>` para canjear una key.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text("✅ Ya tienes acceso, usa los comandos con prefijo .")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "tools":
        await query.edit_message_text("🛠 Aquí están tus herramientas.")

    elif query.data == "gateway":
        keyboard = [[
            InlineKeyboardButton("Hola 1", callback_data="hola"),
            InlineKeyboardButton("Hola 2", callback_data="hola"),
            InlineKeyboardButton("Hola 3", callback_data="hola"),
            InlineKeyboardButton("Hola 4", callback_data="hola"),
        ]]
        await query.edit_message_text("🌐 Gateway:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "hola":
        await query.answer("hola xd", show_alert=True)

# ---------------------------
# ADMIN COMMANDS
# ---------------------------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")
    try:
        _, uid = update.message.text.split()
        ban_user(int(uid))
        await update.message.reply_text(f"🚫 Usuario {uid} baneado")
    except:
        await update.message.reply_text("Uso: .ban <user_id>")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")
    try:
        _, uid = update.message.text.split()
        unban_user(int(uid))
        await update.message.reply_text(f"✅ Usuario {uid} desbaneado")
    except:
        await update.message.reply_text("Uso: .unban <user_id>")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_user_admin(update.effective_user.id):
        return await update.message.reply_text("❌ No tienes permisos.")
    try:
        _, days = update.message.text.split()
        key = create_key(int(days))
        await update.message.reply_text(f"🔑 Key generada válida por {days} días:\n`{key}`", parse_mode="Markdown")
    except:
        await update.message.reply_text("Uso: .genkey <días>")

# ---------------------------
# USER COMMANDS
# ---------------------------
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        _, key = update.message.text.split()
        if redeem_key(update.effective_user.id, key):
            await update.message.reply_text("✅ Key canjeada, ahora tienes acceso.")
        else:
            await update.message.reply_text("❌ Key inválida o ya usada.")
    except:
        await update.message.reply_text("Uso: /redeem <KEY>")

async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not user_has_access(user_id):
        return await update.message.reply_text("⚠️ Necesitas canjear una key para usar este comando.")

    text = update.message.text.strip().split(" ", 1)
    if len(text) == 1:
        return await update.message.reply_text("Uso: .gen <BIN/PATRÓN>")

    bin_input = text[1]
    cards = generate_card(bin_input, amount=10)
    msg = "💳 **Tarjetas generadas**:\n\n" + "\n".join(cards)
    await update.message.reply_text(msg, parse_mode="Markdown")