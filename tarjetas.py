import random
from telegram import Update
from telegram.ext import ContextTypes

def generar_tarjeta():
    numero = " ".join(str(random.randint(0,9)) for _ in range(16))
    fecha = f"{random.randint(1,12):02d}/{random.randint(25,30)}"
    cvv = "".join(str(random.randint(0,9)) for _ in range(3))
    return f"""
💳 Tarjeta Generada
--------------------
Número: {numero}
Expira: {fecha}
CVV: {cvv}
"""

async def tarjeta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card = generar_tarjeta()
    await update.message.reply_text(card)