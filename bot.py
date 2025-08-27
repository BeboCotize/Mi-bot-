import os
import re
import pytz
import datetime
from flask import Flask, request
import telebot
from cc_gen import cc_gen  # tu archivo
from autorizados import ver_user  # tu verificación
from binlist import binlist       # tu función binlist

# ─────────────────────────────
#   📌 BOT CONFIG
# ─────────────────────────────
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
server = Flask(__name__)

# ─────────────────────────────
#   📌 HANDLER GEN
# ─────────────────────────────
@bot.message_handler(commands=['gen'])
def gen(message):
    userid = message.from_user.id
    
    if ver_user(str(userid)) == False:
        bot.reply_to(message, 'No estas autorizado, contacta @colale1k.')
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
                    if len(ano) == 2: 
                        ano = '20'+ano
                    IST = pytz.timezone('US/Central')
                    now = datetime.datetime.now(IST)
                    if ((datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") <= datetime.datetime.strptime(f'{mes}-{ano}', "%m-%Y"))) == False:
                        bot.reply_to(message, "fecha incorrecta")
                
                card = cc_gen(cc, mes, ano, cvv)
                if card:
                    cc1,cc2,cc3,cc4,cc5,cc6,cc7,cc8,cc9,cc10 = card
                    extra = str(cc) + 'xxxxxxxxxxxxxxxxxxxxxxx'

                    mes_2 = mes if mes in ['xx', 'rnd'] else mes
                    if ano in ['xxxx', 'rnd']:
                        ano_2 = ano
                    else:
                        ano_2 = '20'+ano if len(ano)==2 else ano
                    cvv_2 = cvv if cvv in ['xxx','rnd'] or ano=='xxxx' else cvv

                    binsito = binlist(bin_number)
                    if binsito[0] != None:
                        text = f"""
🇩🇴DEMON SLAYER GENERATOR🇩🇴
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
#   📌 FLASK WEBHOOK
# ─────────────────────────────
@server.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def index():
    return "Bot funcionando con webhook!", 200

if __name__ == "__main__":
    # URL pública de tu servidor (Railway, Render, etc.)
    URL = os.getenv("WEBHOOK_URL")  
    bot.remove_webhook()
    bot.set_webhook(url=f"{URL}/{TOKEN}")
    server.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))