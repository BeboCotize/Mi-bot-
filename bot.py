from telegram.ext import ApplicationBuilder, CommandHandler
from admin import ban, unban, add_admin, genkey
from generador import gen_full

TOKEN = "8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM"

app = ApplicationBuilder().token(TOKEN).build()

# Comandos admin
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("admin", add_admin))
app.add_handler(CommandHandler("genkey", genkey))

# Comando gen
async def gen(update, context):
    if not context.args:
        return await update.message.reply_text("Uso: .gen <bin_pattern> [MM] [YYYY] [CVV]")
    bin_pattern = context.args[0]
    mm = context.args[1] if len(context.args) > 1 else None
    yyyy = context.args[2] if len(context.args) > 2 else None
    cvv = context.args[3] if len(context.args) > 3 else None
    card = gen_full(bin_pattern, mm, yyyy, cvv)
    await update.message.reply_text(f"💳 {card}")

app.add_handler(CommandHandler("gen", gen))

if __name__ == "__main__":
    app.run_polling()