from telegram import Update
from telegram.ext import ContextTypes
from generador import generar_cc, bin_info

async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Uso: `.gen 456789xxxxxx|MM|YYYY|rnd`")
        return

    entrada = context.args[0]  # Ejemplo: 496623087004xxxx|3|2027|rnd
    partes = entrada.split("|")

    if len(partes) < 4:
        await update.message.reply_text("⚠️ Formato incorrecto. Usa: `.gen BIN|MM|YYYY|rnd`")
        return

    bin_format, mes, anio, cvv_mode = partes
    tarjetas = generar_cc(bin_format, cantidad=10)

    # Datos BIN
    info = bin_info(bin_format[:6])

    # Respuesta
    msg = "💳 **Tarjetas generadas:**\n\n"
    for t in tarjetas:
        cvv = random.randint(100, 999) if cvv_mode.lower() == "rnd" else "000"
        msg += f"{t}|{mes}|{anio}|{cvv}\n"

    msg += "\n🌍 **BIN Info:**\n"
    msg += f"• País: {info.get('pais', 'N/A')}\n"
    msg += f"• Esquema: {info.get('esquema', 'N/A')}\n"
    msg += f"• Clase: {info.get('clase', 'N/A')}\n"
    msg += f"• Tipo: {info.get('tipo', 'N/A')}\n"
    msg += f"• Moneda: {info.get('moneda', 'N/A')}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")