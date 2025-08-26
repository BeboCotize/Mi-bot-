from telegram import Update
from telegram.ext import ContextTypes
from generator import cc_gen  # ✅ Usamos el nuevo generador


# --- Comando /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al bot.\n\n"
        "👉 Usa `.gen <bin>` para generar tarjetas.\n"
        "Ejemplo: `.gen 4539xxxxxxxxxxxx`\n\n"
        "También puedes añadir mes, año y cvv:\n"
        "`.gen 4539xxxxxxxxxxxx 05 2028 123`"
    )


# --- Comando .gen ---
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args  # Leer argumentos
        if not args:
            await update.message.reply_text(
                "⚠️ Usa el formato:\n`.gen <bin>`\nEjemplo: `.gen 4539xxxxxxxxxxxx`",
                parse_mode="Markdown"
            )
            return

        bin_format = args[0]
        mes = args[1] if len(args) > 1 else "xx"
        ano = args[2] if len(args) > 2 else "xxxx"
        cvv = args[3] if len(args) > 3 else "rnd"

        # Generar tarjetas
        cards = cc_gen(bin_format, mes, ano, cvv)
        text = "".join(cards)

        await update.message.reply_text(f"✅ Generadas:\n\n{text}")

    except Exception as e:
        await update.message.reply_text(f"❌ Error en el generador: {e}")