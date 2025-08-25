from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from db import add_user, is_user_registered, init_db
import sqlite3

ADMIN_ID = 6629555218  # <-- tu ID de Telegram

# Inicializar DB
init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ¡Hola! Estoy vivo en Railway.")

async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_user_registered(user_id):
        add_user(user_id)
        await update.message.reply_text("✅ Registro completado. ¡Ya puedes usar los comandos!")
    else:
        await update.message.reply_text("⚠️ Ya estabas registrado, puedes usar los comandos.")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("❌ No tienes permisos para ver el panel.")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"📊 *Panel de administración*\n\n"
        f"👥 Usuarios registrados: {total}\n\n"
        f"Comandos:\n"
        f"🔒 .ban <id>\n"
        f"🔓 .unban <id>\n"
        f"👀 .users (listar usuarios)",
        parse_mode="Markdown"
    )

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return await update.message.reply_text("❌ No tienes permisos.")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    all_users = cursor.fetchall()
    conn.close()

    lista = "\n".join([f"• {u[0]}" for u in all_users])
    await update.message.reply_text(f"👥 Usuarios registrados:\n\n{lista}")

# Configuración del bot
app = Application.builder().token("TU_TOKEN_AQUI").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("registrar", registrar))
app.add_handler(CommandHandler("panel", panel))
app.add_handler(CommandHandler("users", users))

if __name__ == "__main__":
    app.run_polling()