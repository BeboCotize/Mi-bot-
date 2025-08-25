import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from db import init_db, register_user, is_banned, ban_user, unban_user, is_admin, make_admin

# ----------------------------
# Inicializar base de datos
# ----------------------------
init_db()

# ----------------------------
# Configuración de logging
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------------------
# Comando /start
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.username)

    if is_banned(user.id):
        await update.message.reply_text("🚫 Estás baneado y no puedes usar el bot.")
    else:
        await update.message.reply_text(f"👋 Hola {user.first_name}, bienvenido al bot.")

# ----------------------------
# Comando /ban (solo admins)
# ----------------------------
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ No tienes permisos para banear usuarios.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /ban <user_id>")
        return

    target_id = int(context.args[0])
    ban_user(target_id)
    await update.message.reply_text(f"✅ Usuario {target_id} baneado.")

# ----------------------------
# Comando /unban (solo admins)
# ----------------------------
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ No tienes permisos para desbanear usuarios.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /unban <user_id>")
        return

    target_id = int(context.args[0])
    unban_user(target_id)
    await update.message.reply_text(f"✅ Usuario {target_id} desbaneado.")

# ----------------------------
# Comando /adminpanel
# ----------------------------
async def adminpanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ No tienes permisos para acceder al panel de admin.")
        return

    await update.message.reply_text(
        "🔧 Panel de Admin\n"
        "/ban <user_id> - Banear usuario\n"
        "/unban <user_id> - Desbanear usuario\n"
    )

# ----------------------------
# MAIN
# ----------------------------
def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("adminpanel", adminpanel))

    app.run_polling()

if __name__ == "__main__":
    main()