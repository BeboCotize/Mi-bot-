import telebot
import datetime
import random
import string
import re
import pytz
from db import init_db, add_key, use_key, ver_user
from cc_gen import cc_gen #binlist  # asumo que tu cc_gen.py trae estas funciones

TOKEN = "8271445453:AAE7sVaxjpSVHNxCwbiHFKK2cxjK8vxuDsI"
ADMIN_ID = 123456789  # 🔴 cámbialo por tu ID real
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# Inicializa DB
init_db()

# ─────────────────────────────
#   📌 START
# ─────────────────────────────
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 Bienvenido al bot!\nUsa /gen pero necesitas una KEY válida.\nReclámala con /claim <KEY>.")

# ─────────────────────────────
#   📌 GENKEY (solo admin)
# ─────────────────────────────
@bot.message_handler(commands=['genkey'])
def genkey(message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "⛔ No autorizado.")
    try:
        args = message.text.split()
        days = int(args[1])
    except:
        return bot.reply_to(message, "Uso: /genkey <días>")
    
    expire_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
    add_key(key, expire_date)
    bot.reply_to(message, f"✅ KEY generada:\n<code>{key}</code>\n📅 Expira: {expire_date}")

# ─────────────────────────────
#   📌 CLAIM
# ─────────────────────────────
@bot.message_handler(commands=['claim'])
def claim(message):
    try:
        key = message.text.split()[1]
    except:
        return bot.reply_to(message, "Uso: /claim <KEY>")
    success, msg = use_key(key, str(message.from_user.id))
    bot.reply_to(message, msg)

# ─────────────────────────────
#   📌 GEN (tu código adaptado con ver_user)
# ─────────────────────────────
@bot.message_handler(commands=['gen'])
def gen(message):
    userid = message.from_user.id

    if ver_user(str(userid)) == False:  
        bot.reply_to(message, '❌ No estas autorizado, contacta @colale1k.')  
    else:  
        inputcc = re.findall(r'[0-9x]+', message.text)  
        if not inputcc: 
            return bot.reply_to(message, "extra no reconocida")  
        else:  
            if len(inputcc) == 1:  
                cc  = inputcc[0]  
                mes = 'xx'  
                ano = 'xxxx'  
                cvv = 'rnd'  
            elif len(inputcc) == 2:  
                cc  = inputcc[0]  
                mes = inputcc[1][0:2]  
                ano = 'xxxx'  
                cvv = 'rnd'  
            elif len(inputcc) == 3:  
                cc  = inputcc[0]  
                mes = inputcc[1][0:2]  
                ano = inputcc[2]  
                cvv = 'rnd'  
            elif len(inputcc) == 4:  
                cc  = inputcc[0]  
                mes = inputcc[1][0:2]  
                ano = inputcc[2]  
                cvv = inputcc[3]  
            else:  
                cc  = inputcc[0]  
                mes = inputcc[1][0:2]  
                ano = inputcc[2]  
                cvv = inputcc[3]  
              
            if len(inputcc[0]) < 6: 
                return bot.reply_to(message, "extra incompleta")  
            else:  
                bin_number = cc[0:6]  
                if cc.isdigit():  
                    cc = cc[0:12]  
                if mes.isdigit() and ano.isdigit():  
                    if len(ano) == 2: ano = '20'+ano  
                    IST = pytz.timezone('US/Central')  
                    now = datetime.datetime.now(IST)  
                    if (datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") > datetime.datetime.strptime(f'{mes}-{ano}', "%m-%Y")):  
                        return bot.reply_to(message, "fecha incorrecta")  
              
                card = cc_gen(cc, mes, ano, cvv)  
                if card:  
                    cc1,cc2,cc3,cc4,cc5,cc6,cc7,cc8,cc9,cc10 = card  

                    extra = str(cc) + 'xxxxxxxxxxxxxxxxxxxxxxx'  
                    if mes in ['xx','rnd']: mes_2 = mes  
                    else: mes_2 = mes  
                    if ano in ['xxxx','rnd']: ano_2 = ano  
                    else:   
                        ano_2 = '20'+ano if len(ano) == 2 else ano  
                    if cvv in ['xxx','rnd'] or ano == 'xxxx': cvv_2 = cvv  
                    else: cvv_2 = cvv  

                    binsito = binlist(bin_number)  
                    if binsito[0] != None:  
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

𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} - {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

𝗘𝗫𝗧𝗥𝗔: <code>{extra[0:16]}|{mes_2}|{ano_2}|{cvv_2}</code>
"""
                        bot.reply_to(message, text)

# ─────────────────────────────
#   📌 RUN
# ─────────────────────────────
print("🤖 Bot corriendo...")
bot.infinity_polling()