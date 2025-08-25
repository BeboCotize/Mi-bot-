from telegram import Update
from telegram.ext import ContextTypes
from db import ban_user, unban_user
import random

ADMIN_ID = 6629555218  # tu ID de admin

async def custom_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # BAN
    if text.startswith("!ban"):
        if update.effective_user.id != ADMIN_ID:
            return await update.message.reply_text("❌ No tienes permiso")
        try:
            _, user_id = text.split(" ")
            ban_user(int(user_id), reason="Baneado por admin")
            await update.message.reply_text(f"🚫 Usuario {user_id} baneado")
        except:
            await update.message.reply_text("⚠️ Uso: !ban <user_id>")

    # UNBAN
    elif text.startswith("%unban"):
        if update.effective_user.id != ADMIN_ID:
            return
        try:
            _, user_id = text.split(" ")
            unban_user(int(user_id))
            await update.message.reply_text(f"✅ Usuario {user_id} desbaneado")
        except:
            await update.message.reply_text("⚠️ Uso: %unban <user_id>")

    # CARD
    elif text.startswith(";card"):
        number = "".join([str(random.randint(0, 9)) for _ in range(16)])
        expiry = f"{random.randint(1,12):02d}/{random.randint(24,29)}"
        cvv = f"{random.randint(100,999)}"
        await update.message.reply_text(
            f"💳 **Tarjeta Generada**\n\nNúmero: {number}\nExpira: {expiry}\nCVV: {cvv}"
        )

    # MOVIES
    elif text.startswith("#movies"):
        await update.message.reply_text("🎬 Menú de películas:\n1️⃣ Acción\n2️⃣ Comedia\n3️⃣ Terror\n4️⃣ Drama")

    # FOOD
    elif text.startswith("*food"):
        await update.message.reply_text("🍔 Menú de comida:\n1️⃣ Pizza\n2️⃣ Hamburguesa\n3️⃣ Tacos\n4️⃣ Sushi")