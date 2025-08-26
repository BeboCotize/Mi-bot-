import requests
from generator import cc_gen

async def gen(update, context):
    try:
        args = update.message.text.split(" ", 1)
        if len(args) < 2:
            await update.message.reply_text("❌ Uso correcto: /gen <bin>")
            return

        bin_input = args[1]

        # 🔍 Lookup del BIN con tu API
        binsito = ["", "", "", "", "", "", ""]
        try:
            res = requests.get(f"https://binlist.io/lookup/{bin_input[:6]}")
            if res.status_code == 200:
                data = res.json()
                binsito[1] = data.get("scheme", "N/A").upper()
                binsito[2] = data.get("type", "N/A").upper()
                binsito[3] = data.get("brand", "N/A").upper()
                binsito[4] = data.get("country", {}).get("name", "N/A")
                binsito[5] = data.get("country", {}).get("emoji", "")
                binsito[6] = data.get("bank", {}).get("name", "N/A")
        except Exception:
            pass

        # 🔢 Generar 10 tarjetas
        tarjetas = cc_gen(bin_input)

        # Aseguramos 10 cc separadas
        cc1, cc2, cc3, cc4, cc5, cc6, cc7, cc8, cc9, cc10 = tarjetas[:10]

        # Extra CC
        extra = tarjetas[0].strip().split("|")
        extra_num = extra[0]
        mes_2 = extra[1]
        ano_2 = extra[2]
        cvv_2 = extra[3]

        # 📋 Mensaje con formato bonito
        text = f"""
🇩🇴insuer generator🇩🇴
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
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

𝗘𝗫𝗧𝗥𝗔: <code>{extra_num}|{mes_2}|{ano_2}|{cvv_2}</code>
"""

        await update.message.reply_text(text, parse_mode="HTML")

    except Exception as e:
        await update.message.reply_text(f"❌ Error interno: {e}")