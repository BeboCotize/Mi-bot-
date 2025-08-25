from db import init_db, add_user, is_user_registered

async def registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_user_registered(user_id):
        await update.message.reply_text("⚠️ Ya estabas registrado, puedes usar los comandos.")
    else:
        add_user(user_id)
        await update.message.reply_text("✅ Registro completado. ¡Ya puedes usar los comandos!")