import requests
from generator import cc_gen
from telegram import Update
from telegram.ext import ContextTypes

# ─────────────────────────────
#   📌 Comando: /start
# ─────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🇩🇴 Bienvenido! Usa /gen <bin> para generar tarjetas.")

# ─────────────────────────────
#   📌 Comando: /gen
# ─────────────────────────────
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Validación de argumentos
        if not context.args:
            await update.message.reply_text("❌ Uso correcto: /gen <BIN>")
            return

        bin_code = context.args[0]

        # Llamada a la API de BINLIST
        url = f"https://binlist.io/lookup/{bin_code}/"
        response = requests.get(url)
        if response.status_code != 200:
            await update.message.reply_text("❌ BIN inválido o API caída.")
            return

        data = response.json()
        binsito = [
            data.get("scheme", "N/A"),
            data.get("type", "N/A"),
            data.get("brand", "N/A"),
            data.get("country", {}).get("name", "N/A"),
            data.get("country", {}).get("emoji", ""),
            data.get("bank", {}).get("name", "N/A"),
        ]

        # Generar tarjetas con tu función cc_gen
        tarjetas = cc_gen(bin_code)
        if not tarjetas:
            await update.message.reply_text("❌ No se pudieron generar tarjetas válidas.")
            return

        # Asignamos las 10 tarjetas
        cc1, cc2, cc3, cc4, cc5, cc6, cc7, cc8, cc9, cc10 = [c.strip() for c in tarjetas[:10]]

        # Generamos un extra random
        extra = cc_gen(bin_code)[0].strip()
        extra_num, mes_2, ano_2, cvv_2 = extra.split("|")

        # Formato final del mensaje
        text = f"""
🇩🇴 Insuer Generator 🇩🇴
⚙️─────────────⚙️
⚙️─────────────⚙️

<code>{cc1}</code>
<code>{cc2}</code>
<code>{cc3}</code>
<code>{cc4}</code>
<code>{cc5}</code>
<code>{cc6}</code>
<code>{cc7}</code>
<code>{cc8}</code>
<code>{cc9}</code>
<code>{cc10}</code>

BIN INFO: {binsito[0]} - {binsito[1]} - {binsito[2]}
COUNTRY: {binsito[4]} {binsito[3]}
BANK: {binsito[5]}

EXTRA: <code>{extra_num}|{mes_2}|{ano_2}|{cvv_2}</code>
"""

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"❌ Error interno: {str(e)}")