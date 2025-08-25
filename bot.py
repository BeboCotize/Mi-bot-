from telegram.ext import Updater, CommandHandler
from antispam import ban_handler, unban_handler
from db import init_db, is_banned

TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"

def start(update, context):
    user_id = update.effective_user.id
    if is_banned(user_id):
        update.message.reply_text("🚫 No puedes usar este bot porque estás baneado.")
        return
    update.message.reply_text("✅ Bienvenido al bot. Usa /help para ver los comandos.")

def help_command(update, context):
    update.message.reply_text("Comandos disponibles:\n/start - Iniciar\n/help - Ayuda\n/ban - (solo admin)\n/unban - (solo admin)")

def main():
    # inicializar DB
    init_db()

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    # Handlers principales
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))

    # Handlers de antispam
    dp.add_handler(ban_handler)
    dp.add_handler(unban_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()