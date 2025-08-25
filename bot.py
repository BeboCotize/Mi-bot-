import os
from telegram.ext import Application, MessageHandler, filters, CallbackQueryHandler
import comandos
import menu  # 👈 importamos el menú

TOKEN = os.getenv("BOT_TOKEN")  

PREFIXES = [".", "!", "*", "?"]

def has_prefix(text: str, command: str) -> bool:
    return any(text.lower().startswith(p + command) for p in PREFIXES)

async def prefixed_command(update, context, command, func):
    text = update.message.text.strip()
    if has_prefix(text, command):
        await func(update, context)

def main():
    app = Application.builder().token(TOKEN).build()

    # ---------------- COMANDOS ----------------
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "ban", comandos.ban)))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "unban", comandos.unban)))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "admin", comandos.make_admin)))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "genkey", comandos.genkey)))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "redeem", comandos.redeem)))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "gen", comandos.gen)))
    
    # ---------------- MENÚ ----------------
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
        lambda u, c: prefixed_command(u, c, "menu", menu.menu)))
    
    app.add_handler(CallbackQueryHandler(menu.button_handler))

    print("🤖 Bot corriendo con prefijos + menú...")
    app.run_polling()

if __name__ == "__main__":
    main()