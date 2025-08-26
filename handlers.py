from telegram import Update
from telegram.ext import ContextTypes
from generator import cc_gen   # ✅ Usamos el nuevo generador


# --- Comando /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bienvenido al bot.\n\n"
        "👉 Usa `.gen <bin>` para generar tarjetas.\n\n"
        "Ejemplo: `.gen 4539xxxxxxxxxxxx`\n\n"
        "También puedes añadir mes, año y cvv:\n"
        "`.gen 4539xxxxxxxxxxxx 05 2028 123`"
    )


# --- Comando .gen ---
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args  # argumentos del comando

        if not args:
            await update.message.reply_text(
                "❌ Debes proporcionar un BIN.\n\n"
                "Ejemplo: `.gen 4539xxxxxxxxxxxx`\n"
                "O con fecha/cvv: `.gen 4539xxxxxxxxxxxx 05 2028 123`"
            )
            return

        # Leer argumentos
        bin_input = args[0]
        mes = args[1] if len(args) > 1 else 'xx'
        ano = args[2] if len(args) > 2 else 'xxxx'
        cvv = args[3] if len(args) > 3 else 'rnd'

        # Generar tarjetas
        tarjetas = cc_gen(bin_input, mes, ano, cvv)

        if not tarjetas:
            await update.message.reply_text("❌ No se pudieron generar tarjetas, revisa los parámetros.")
            return

        # Respuesta formateada
        resultado = "✅ Tarjetas generadas:\n\n" + "\n".join(tarjetas)
        await update.message.reply_text(f"```{resultado}```", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error interno: {e}")