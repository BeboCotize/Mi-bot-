import os
import re
import pytz
import datetime
import telebot

from cc_gen import cc_gen   # 👈 importa tu archivo cc_gen.py (debe estar en la misma carpeta)

# ⚙️ Configuración
TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# === función de verificación simple (puedes editarla) ===
def ver_user(user_id: str) -> bool:
    # ✅ Aquí defines tus usuarios autorizados
    allowed_users = ["123456789", "987654321"]  # reemplaza con tus IDs de Telegram
    return user_id in allowed_users

# === función para binlist (dummy, edítala si tienes tu versión real) ===
def binlist(bin_number: str):
    # Simulación: devuelve lista con info de ejemplo
    return [bin_number, "VISA", "CREDIT", "CLASSIC", "US", "United States", "BANK DEMO"]

# === comando GEN ===
@bot.message_handler(commands=["gen"])
def gen(message):
    userid = message.from_user.id

    if not ver_user(str(userid)):
        return bot.reply_to(message, "⛔ No estás autorizado, contacta con el admin.")

    inputcc = re.findall(r"[0-9x]+", message.text)
    if not inputcc:
        return bot.reply_to(message, "⚠️ Extra no reconocida.")

    # --- parsing de parámetros ---
    if len(inputcc) == 1:
        cc, mes, ano, cvv = inputcc[0], "xx", "xxxx", "rnd"
    elif len(inputcc) == 2:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], "xxxx", "rnd"
    elif len(inputcc) == 3:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], inputcc[2], "rnd"
    else:
        cc, mes, ano, cvv = inputcc[0], inputcc[1][0:2], inputcc[2], inputcc[3]

    if len(cc) < 6:
        return bot.reply_to(message, "⚠️ Extra incompleta.")

    bin_number = cc[0:6]
    if cc.isdigit():
        cc = cc[0:12]

    if mes.isdigit() and ano.isdigit():
        if len(ano) == 2: 
            ano = "20" + ano
        IST = pytz.timezone("US/Central")
        now = datetime.datetime.now(IST)
        if datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > datetime.datetime.strptime(f"{mes}-{ano}", "%m-%Y"):
            return bot.reply_to(message, "⚠️ Fecha incorrecta.")

    # --- generar tarjetas ---
    cards = cc_gen(cc, mes, ano, cvv)
    if not cards:
        return bot.reply_to(message, "❌ No se pudo generar CCs válidas.")

    # separar cada tarjeta
    cc_lines = "\n".join([f"<code>{c.strip()}</code>" for c in cards])

    # preparar extras
    extra = str(cc) + "xxxxxxxxxxxxxxxxxxxxxxx"
    mes_2 = mes
    ano_2 = ano if len(ano) == 4 else "20" + ano
    cvv_2 = cvv

    binsito = binlist(bin_number)

    # --- respuesta final en HTML ---
    text = f"""
<b>🇩🇴 DEMON SLAYER GENERATOR 🇩🇴</b>
⚙️────────────⚙️
{cc_lines}

<b>𝗕𝗜𝗡 𝗜𝗡𝗙𝗢:</b> {binsito[1]} - {binsito[2]} - {binsito[3]}
<b>𝗖𝗢𝗨𝗡𝗧𝗥𝗬:</b> {binsito[4]} - {binsito[5]}
<b>𝗕𝗔𝗡𝗞:</b> {binsito[6]}

<b>𝗘𝗫𝗧𝗥𝗔:</b> <code>{extra[0:16]}|{mes_2}|{ano_2}|{cvv_2}</code>
"""
    bot.send_message(message.chat.id, text)

# 🚀 Loop
if __name__ == "__main__":
    print("🤖 Bot corriendo...")
    bot.infinity_polling()