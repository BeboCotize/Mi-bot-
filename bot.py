import os
import telebot
import sqlite3
import datetime
import pytz
import re
from database import init_db, ver_user, claim_key, create_key, is_admin
from cc_gen import cc_gen   # tu archivo ya lo tiene

TOKEN = os.getenv("BOT_TOKEN", "AQUI_TU_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ─────────────────────────────
#   📌 START
# ─────────────────────────────
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Bienvenido al bot!\nUsa /gen para generar, pero necesitas una KEY válida.")

# ─────────────────────────────
#   📌 GEN
# ─────────────────────────────
@bot.message_handler(commands=['gen'])
def gen(message):
    userid = message.from_user.id
    
    if ver_user(str(userid)) == False:
        return bot.reply_to(message, '❌ No estás autorizado. Contacta @colale1k.')

    inputcc = re.findall(r'[0-9x]+', message.text)
    if not inputcc:
        return bot.reply_to(message, "⚠️ Extra no reconocida")
    else:
        if len(inputcc) == 1:
            cc  = inputcc[0]; mes = 'xx'; ano = 'xxxx'; cvv = 'rnd'
        elif len(inputcc) == 2:
            cc  = inputcc[0]; mes = inputcc[1][0:2]; ano = 'xxxx'; cvv = 'rnd'
        elif len(inputcc) == 3:
            cc  = inputcc[0]; mes = inputcc[1][0:2]; ano = inputcc[2]; cvv = 'rnd'
        elif len(inputcc) == 4:
            cc  = inputcc[0]; mes = inputcc[1][0:2]; ano = inputcc[2]; cvv = inputcc[3]
        else:
            cc  = inputcc[0]; mes = inputcc[1][0:2]; ano = inputcc[2]; cvv = inputcc[3]
        
        if len(inputcc[0]) < 6:
            return bot.reply_to(message, "⚠️ Extra incompleta")

        bin_number = cc[0:6]
        if cc.isdigit():
            cc = cc[0:12]

        if mes.isdigit() and ano.isdigit():
            if len(ano) == 2: ano = '20'+ano
            IST = pytz.timezone('US/Central')
            now = datetime.datetime.now(IST)
            if not (datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") 
                    <= datetime.datetime.strptime(f'{mes}-{ano}', "%m-%Y")):
                return bot.reply_to(message, "❌ Fecha incorrecta")

        # 🚀 Generar tarjetas
        card = cc_gen(cc, mes, ano, cvv)
        if card:
            cc1,cc2,cc3,cc4,cc5,cc6,cc7,cc8,cc9,cc10 = card

            extra = str(cc) + 'xxxxxxxxxxxxxxxxxxxxxxx'
            mes_2 = mes if mes not in ['xx','rnd'] else mes
            if ano in ['xxxx','rnd']: ano_2 = ano
            else: ano_2 = '20'+ano if len(ano)==2 else ano
            cvv_2 = cvv if cvv not in ['xxx','rnd'] and ano != 'xxxx' else cvv

            text = f"""
🇩🇴 DEMON SLAYER GENERATOR 🇩🇴
⚙️───π────────⚙️
⚙️───π────────⚙️

<code>{cc1.strip()}</code>
<code>{cc2.strip()}</code>
<code>{cc3.strip()}</code>
<code>{cc4.strip()}</code>
<code>{cc5.strip()}</code>
<code>{cc6.strip()}</code>
<code>{cc7.strip()}</code>
<code>{cc8.strip()}</code>
<code>{cc9.strip()}</code>
<code>{cc10.strip()}</code>

𝗘𝗫𝗧𝗥𝗔: <code>{extra[0:16]}|{mes_2}|{ano_2}|{cvv_2}</code>
"""
            bot.reply_to(message, text)

# ─────────────────────────────
#   📌 CLAIM KEY
# ─────────────────────────────
@bot.message_handler(commands=['claim'])
def claim(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "⚠️ Uso: /claim TU_KEY")
    key = args[1]
    success, msg = claim_key(message.from_user.id, key)
    bot.reply_to(message, msg)

# ─────────────────────────────
#   📌 CREATE KEY (admin)
# ─────────────────────────────
@bot.message_handler(commands=['newkey'])
def newkey(message):
    if not is_admin(message.from_user.id):
        return bot.reply_to(message, "⛔ No eres admin.")
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "⚠️ Uso: /newkey DIAS")
    try:
        dias = int(args[1])
        key = create_key(dias)
        bot.reply_to(message, f"✅ Key creada:\n<code>{key}</code>\nExpira en {dias} días.")
    except:
        bot.reply_to(message, "⚠️ Error en formato, usa: /newkey 5")

# ─────────────────────────────
#   📌 MAIN
# ─────────────────────────────
if __name__ == "__main__":
    init_db()
    print("🤖 Bot corriendo...")
    bot.infinity_polling()