import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from db import init_db, create_key, redeem_key, has_valid_key

init_db()

logging.basicConfig(level=logging.INFO)

# ----------------------------
# Solo para admin
# ----------------------------
ADMIN_ID = 6629555218  # <-- pon tu user_id de Telegram aquí

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ No tienes permiso para generar keys.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /genkey <días>")
        return

    try:
        days = int(context.args[0])
    except ValueError:
        await update.message.reply_text("El parámetro debe ser un número.")
        return

    key = create_key(days)
    await update.message.reply_text(f"🔑 Key generada: `{key}`\nValidez: {days} días", parse_mode="Markdown")

# ----------------------------
# Usuario canjea la key
# ----------------------------
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /redeem <key>")
        return

    key = context.args[0]
    success = redeem_key(update.effective_user.id, update.effective_user.username, key)

    if success:
        await update.message.reply_text("✅ Key canjeada con éxito, ya puedes usar el bot.")
    else:
        await update.message.reply_text("❌ Key inválida o ya usada.")

# ----------------------------
# Comando /start
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if has_valid_key(user.id):
        await update.message.reply_text("🎉 Bienvenido, tienes acceso activo al bot.")
    else:
        await update.message.reply_text("⚠️ No tienes una key válida. Solicita una al admin y usa /redeem <key>.")

# ----------------------------
# MAIN
# ----------------------------
def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genkey", genkey))
    app.add_handler(CommandHandler("redeem", redeem))

    app.run_polling()

if __name__ == "__main__":
    main()