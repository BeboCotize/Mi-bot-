# bot.py
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import comandos

TOKEN = os.getenv("BOT_TOKEN")  # tu token de Telegram Bot en Railway

# -------------------- Prefijos --------------------
PREFIXES = [".", "!", "*", "?"]

def with_prefix(command):
    """Agrega los prefijos válidos al comando"""
    return [p + command for p in PREFIXES]

# -------------------- Main --------------------
def main():
    app = Application.builder().token(TOKEN).build()

    # BAN / UNBAN / ADMIN
    for cmd in with_prefix("ban"):
        app.add_handler(CommandHandler(cmd, comandos.ban))
    for cmd in with_prefix("unban"):
        app.add_handler(CommandHandler(cmd, comandos.unban))
    for cmd in with_prefix("admin"):
        app.add_handler(CommandHandler(cmd, comandos.make_admin))

    # KEYS
    for cmd in with_prefix("genkey"):
        app.add_handler(CommandHandler(cmd, comandos.genkey))
    for cmd in with_prefix("redeem"):
        app.add_handler(CommandHandler(cmd, comandos.redeem))

    # GENERADOR
    for cmd in with_prefix("gen"):
        app.add_handler(CommandHandler(cmd, comandos.gen))

    print("🤖 Bot corriendo...")
    app.run_polling()

if __name__ == "__main__":
    main()