import os
import re
import requests
import time
from flask import Flask, request
from telebot import TeleBot, types
from cc_gen import cc_gen
from sagepay import ccn_gate as sagepay
from gateway import ccn_gate as bb_gateway_check 
 
# ==============================
# CONFIGURACIÓN 
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')

USERS = [
    '6116275760', '6622385429']

# Diccionario para almacenar el último uso del comando /bb por usuario
BB_COOLDOWN = {} 
COOLDOWN_TIME = 20 # Tiempo de espera en segundos para reintentar

# 🚨 NUEVO: Diccionario y tiempo para el Modo Mantenimiento Forzado
BB_MAINTENANCE = {}
MAINTENANCE_TIME = 600 # 10 minutos en segundos (10 * 60)

# 🚨 NUEVO: Cooldown para el comando masivo
MASS_COOLDOWN = {} 
MASS_COOLDOWN_TIME = 120 # 2 minutos de espera para el comando masivo

# Fotos en Imgur (cambia por tus enlaces)
IMG_PHOTO1 = "https://i.imgur.com/XXXXXXX.jpg"
IMG_PHOTO2 = "https://i.imgur.com/YYYYYYY.jpg"

# Flask app para webhook
app = Flask(__name__)

# 📌 NUEVO: Prefijos personalizados que el bot aceptará
CUSTOM_PREFIXES = ['.', '&']
# Lista de todos tus comandos (sin prefijo)
ALL_COMMANDS = ['bin', 'rnd', 'gen', 'bb', 'sagepay', 'cmds', 'start', 'deluxe', 'mass'] # 👈 'mass' agregado


# ==============================
# FUNCIONES AUXILIARES
# ==============================

def ver_user(iduser: str) -> bool:
    return iduser in USERS

def binlist(bin: str) -> tuple | bool:
    try:
        result = requests.get(f'https://binlist.io/lookup/{bin}/').json()
        return (
            result['number']['iin'],
            result['scheme'],
            result['type'],
            result['category'],
            result['country']['name'],
            result['country']['emoji'],
            result['bank']['name']
        )
    except:
        return False

def dir_fake():
    """Genera una dirección usando randomuser.me (más estable)."""
    try:
        r = requests.get("https://randomuser.me/api/", timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()["results"][0]
        return {
            "first_name": data["name"]["first"],
            "last_name": data["name"]["last"],
            "phone": data["phone"],
            "city": data["location"]["city"],
            "street_name": data["location"]["street"]["name"],
            "street_address": str(data["location"]["street"]["number"]),
            "zip": str(data["location"]["postcode"]),
            "state": data["location"]["state"],
            "country": data["location"]["country"],
        }
    except Exception as e:
        print("Error en dir_fake:", e)
        return None


# ==============================
# HANDLERS (SIN DECORADORES @bot.message_handler(commands=...) AHORA)
# ==============================

def bin_cmd(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    if message.reply_to_message:
        search_bin = re.findall(r'[0-9]+', str(message.reply_to_message.text))
    else:
        text_after_command = " ".join(message.text.split()[1:])
        search_bin = re.findall(r'[0-9]+', text_after_command)

    if not search_bin:
        return bot.reply_to(message, "Bin no reconocido.")

    number = search_bin[0][0:6]
    data = binlist(number)
    if not data:
        return bot.reply_to(message, "Bin no encontrado.")

    texto = f"""
𝗕𝗜𝗡: {data[0]}
𝗜𝗡𝗙𝗢: {data[1]} - {data[2]} - {data[3]}
𝗕𝗔𝗡𝗞: {data[6]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {data[4]} {data[5]}
"""
    return bot.reply_to(message, texto)


def rand(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    data = dir_fake()
    if not data:
        return bot.reply_to(message, '⚠️ Error obteniendo dirección.')

    texto = f"""
👤 {data['first_name']} {data['last_name']}
📞 {data['phone']}
🏙️ {data['city']}, {data['state']}, {data['country']}
📍 {data['street_address']} {data['street_name']}
🆔 CP: {data['zip']}
"""
    bot.reply_to(message, texto)


def gen(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    text_after_command = " ".join(message.text.split()[1:])
    inputcc = re.findall(r'[0-9x]+', text_after_command)
    
    if not inputcc:
        return bot.reply_to(message, "Formato incorrecto.")

    cc = inputcc[0]
    mes = inputcc[1][0:2] if len(inputcc) > 1 else "xx"
    ano = inputcc[2] if len(inputcc) > 2 else "xxxx"
    cvv = inputcc[3] if len(inputcc) > 3 else "rnd"

    if len(cc) < 6:
        return bot.reply_to(message, "CC incompleta.")

    bin_number = cc[0:6]
    card = cc_gen(cc, mes, ano, cvv)
    if not card:
        return bot.reply_to(message, "Error al generar.")

    binsito = binlist(bin_number)
    cards_text = "\n".join([f"<code>{c.strip()}</code>" for c in card])

    text = f"""
🔹 GENERADOR 🔹

{cards_text}

𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1]} - {binsito[2]} - {binsito[3]}
𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4]} {binsito[5]}
𝗕𝗔𝗡𝗞: {binsito[6]}

𝗘𝗫𝗧𝗥𝗔: <code>{cc}|{mes}|{ano}|{cvv}</code>
"""
    bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)


def gate_bb(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')
    
    current_time = time.time()
    
    # 🚨 LÓGICA DE MANTENIMIENTO FORZADO 🚨
    if userid in BB_MAINTENANCE and current_time < BB_MAINTENANCE[userid]:
        remaining = int(BB_MAINTENANCE[userid] - current_time)
        minutes = remaining // 60
        seconds = remaining % 60
        return bot.reply_to(
            message, 
            f"🛠️ Comando /bb en mantenimiento forzado (Max Retries). Por favor, espera {minutes} minutos y {seconds} segundos."
        )

    # === LÓGICA DE COOLDOWN (SPAM-LOCK) ===
    if userid in BB_COOLDOWN:
        time_elapsed = current_time - BB_COOLDOWN[userid]
        if time_elapsed < COOLDOWN_TIME:
            remaining = int(COOLDOWN_TIME - time_elapsed)
            return bot.reply_to(
                message, 
                f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /bb."
            )
    
    # 1. Preparar el texto de entrada
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/bb", "").strip() if not message.reply_to_message else raw_text.strip()
    
    parts = re.split(r"[| \n\t]+", clean)

    if len(parts) < 4:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido.\nEjemplo:\n"
            "`/bb 4111111111111111|12|2026|123`",
            parse_mode="Markdown"
        )

    cc, mes, ano, cvv = parts[0:4]
    
    # 2. ENVIAR EL MENSAJE INICIAL Y CAPTURAR SU ID
    initial_message = bot.reply_to(message, "⚙️ Chequeando con BB Gateway...") 
    chat_id = initial_message.chat.id
    message_id = initial_message.message_id

    try:
        # LLAMADA A TU GATEWAY MODIFICADO (devuelve string con status)
        status_message = bb_gateway_check(f"{cc}|{mes}|{ano}|{cvv}")
        
        # 3. Parseamos el resultado para el formato final
        if "APROBADO" in status_message or "APPROVED" in status_message:
            status = "APPROVED"
            emoji = "✅"
            message_detail = status_message.split(":")[-1].strip()
        elif "DECLINADO" in status_message or "DECLINED" in status_message:
            status = "DECLINED"
            emoji = "❌"
            message_detail = status_message.split(":")[-1].strip()
        else:
            status = "ERROR"
            emoji = "⚠️"
            
            # 🚨 GESTIÓN DE ERROR Y MANTENIMIENTO
            if "Max Retries" in status_message:
                message_detail = "Fallo de conexión o límite de intentos. Comando bloqueado por 10 min."
                
                # ACTIVAR MANTENIMIENTO FORZADO POR 10 MINUTOS
                BB_MAINTENANCE[userid] = time.time() + MAINTENANCE_TIME
                
            else:
                message_detail = status_message
            
        # 4. Obtenemos información adicional para el formato
        bin_number = cc[0:6]
        binsito = binlist(bin_number)
        
        # 5. Creamos el mensaje final con el formato deseado
        final_text = f"""
{emoji} CARD --> <code>{cc}|{mes}|{ano}|{cvv}</code>
{emoji} STATUS --> <b>{status}</b> {emoji}
{emoji} MESSAGE --> <b>{message_detail}</b>
[GATEWAY] <b>[BB Gateway]</b>

[BIN INFO]
{emoji} BIN --> <b>{binsito[1]} {binsito[2]}</b>
{emoji} BANK --> <b>{binsito[6]}</b>
{emoji} COUNTRY --> <b>{binsito[4]} {binsito[5]}</b>
"""
    except Exception as e:
        final_text = f"❌ Error ejecutando BB Gateway:\n{e}"
        print(f"Error en gate_bb: {e}")
        
    # === ACTUALIZAR EL COOLDOWN (SOLO SI EL CHECK SE EJECUTÓ) ===
    BB_COOLDOWN[userid] = time.time()

    # 6. EDITAR el mensaje inicial con la respuesta final
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=final_text, 
            parse_mode='HTML'
        )
    except Exception as edit_error:
        bot.send_message(chat_id=chat_id, text=final_text, parse_mode='HTML')
        print(f"Error al editar mensaje: {edit_error}")

def mass_bb(message):
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    current_time = time.time()
    
    # === LÓGICA DE COOLDOWN PARA MASS ===
    if userid in MASS_COOLDOWN:
        time_elapsed = current_time - MASS_COOLDOWN[userid]
        if time_elapsed < MASS_COOLDOWN_TIME:
            remaining = int(MASS_COOLDOWN_TIME - time_elapsed)
            return bot.reply_to(
                message, 
                f"🚫 ¡Calma! Debes esperar {remaining} segundos antes de volver a usar .mass bb."
            )
    
    # 1. Extraer el texto de la CCs
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    # Limpiamos el /mass o .mass si no es un reply
    clean = raw_text.replace("/mass", "").strip() if not message.reply_to_message else raw_text.strip()
    
    # Dividir el texto para encontrar las tarjetas (separadas por línea, espacio o barra)
    cc_lines = re.split(r'[\n\s]+', clean)

    # 2. Parsear y validar las tarjetas
    cards_to_check = []
    
    # Las tarjetas deben tener el formato CC|MM|AAAA|CVV o similar
    cc_pattern = re.compile(r'(\d{12,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})')
    
    for line in cc_lines:
        match = cc_pattern.search(line)
        if match and len(cards_to_check) < 10: # Limitamos a 10 tarjetas
            cc, mes, ano, cvv = match.groups()
            cards_to_check.append(f"{cc}|{mes}|{ano}|{cvv}")
    
    if not cards_to_check:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido o tarjetas no detectadas. Asegúrate de usar el formato:\n"
            "`/mass 4111...|12|2026|123` (hasta 10 líneas)",
            parse_mode="Markdown"
        )
    
    # 3. ENVIAR MENSAJE INICIAL
    initial_message = bot.reply_to(
        message, 
        f"⚙️ Iniciando chequeo masivo de {len(cards_to_check)} tarjetas con BB Gateway...\n"
        "Esto podría tomar unos momentos."
    ) 
    chat_id = initial_message.chat.id
    message_id = initial_message.message_id
    
    results = []
    
    # 4. Procesar cada tarjeta
    for full_cc in cards_to_check:
        cc, mes, ano, cvv = full_cc.split('|')
        
        try:
            status_message = bb_gateway_check(full_cc)
            
            if "APROBADO" in status_message or "APPROVED" in status_message:
                status = "✅ APROBADA"
                message_detail = status_message.split(":")[-1].strip()
            elif "DECLINADO" in status_message or "DECLINED" in status_message:
                status = "❌ DECLINADA"
                message_detail = status_message.split(":")[-1].strip()
            else:
                status = "⚠️ ERROR"
                if "Max Retries" in status_message:
                    # Aquí no activamos el mantenimiento forzado para no bloquear a todos los usuarios
                    # si solo una tarjeta falla por conexión en el mass check.
                    message_detail = "Fallo de conexión."
                else:
                    message_detail = status_message
            
            bin_number = cc[0:6]
            binsito = binlist(bin_number)
            
            result_line = (
                f"💳 <code>{full_cc}</code> | <b>{status}</b>\n"
                f"└─ **{message_detail}** ({binsito[6]} - {binsito[4]} {binsito[5]})"
            )
            results.append(result_line)
            
        except Exception as e:
            results.append(f"💳 <code>{full_cc}</code> | ❌ ERROR (Excepción)")
            print(f"Error en mass_bb para {full_cc}: {e}")
            
    # 5. Formatear y enviar resultado final
    final_text = f"""
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━
🌐 **Total Chequeado:** {len(cards_to_check)}
"""
    
    # === ACTUALIZAR EL COOLDOWN ===
    MASS_COOLDOWN[userid] = time.time()

    # 6. EDITAR el mensaje inicial con la respuesta final
    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=final_text, 
            parse_mode='HTML'
        )
    except Exception as edit_error:
        bot.send_message(chat_id=chat_id, text=final_text, parse_mode='HTML')
        print(f"Error al editar mensaje: {edit_error}")


def gate_sagepay(message):
    if not ver_user(str(message.from_user.id)):
        return bot.reply_to(message, 'No estás autorizado.')

    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/sagepay", "").strip() if not message.reply_to_message else raw_text.strip()
    
    parts = re.split(r"[| \n\t]+", clean)

    if len(parts) < 4:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido.\nEjemplos:\n"
            "`/sagepay 4111111111111111 12 2026 123`\n"
            "`/sagepay 4111111111111111|12|2026|123`",
            parse_mode="Markdown"
        )

    cc, mes, ano, cvv = parts[0:4]

    try:
        result = sagepay(f"{cc}|{mes}|{ano}|{cvv}")
        print("DEBUG sagepay() ->", result)

        text = f"""
💳 <code>{cc}|{mes}|{ano}|{cvv}</code>
📌 RESULT: <b>{result}</b>
"""
    except Exception as e:
        text = f"❌ Error ejecutando gateway SagePay:\n{e}"

    bot.reply_to(message, text)


def cmds(message):
    buttons_cmds = [
        [
            types.InlineKeyboardButton('Gateways', callback_data='gates'),
            types.InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [types.InlineKeyboardButton('Cerrar', callback_data='close')]
    ]
    markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
    text = "<b>📋 Lista de comandos</b>"

    bot.send_photo(
        chat_id=message.chat.id,
        photo=IMG_PHOTO1,
        caption=text,
        reply_to_message_id=message.id,
        reply_markup=markup_buttom
    )


def start(message):
    text = f"""
<b>⚠️ Bienvenido a DuluxeChk ⚠️</b>
• Para ver tools/Gateways: /cmds
• Info: /Deluxe
🚸 @DuluxeChk
"""
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO2, caption=text)


def deluxe(message):
    text = f"""
⚠️ Términos ⚠️
- Macros/scripts = ban
- Reembolsos con saldo bineado = ban
- Difamación = ban
- Robo de gates = ban
"""
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO1, caption=text)


# ==============================
# ROUTER DE COMANDOS CON PREFIJOS
# ==============================

COMMAND_MAP = {
    'bin': bin_cmd,
    'rnd': rand,
    'gen': gen,
    'bb': gate_bb,
    'sagepay': gate_sagepay,
    'cmds': cmds,
    'start': start,
    'deluxe': deluxe,
    'mass': mass_bb, # 👈 Nuevo comando masivo
}

def is_command_with_prefix(message):
    """Verifica si el mensaje comienza con '/', '.', o '&' y tiene un comando válido."""
    if message.text is None:
        return False
        
    parts = message.text.split()
    if not parts:
        return False

    first_word = parts[0].lower()
    
    prefixes = ['/'] + CUSTOM_PREFIXES
    for prefix in prefixes:
        if first_word.startswith(prefix):
            command = first_word[len(prefix):]
            if '@' in command:
                command = command.split('@')[0]
                
            return command in ALL_COMMANDS
            
    return False

@bot.message_handler(func=is_command_with_prefix)
def handle_all_commands(message):
    text_parts = message.text.split()
    command_with_prefix = text_parts[0].lower()
    
    command_name = ""
    prefixes = ['/'] + CUSTOM_PREFIXES
    for prefix in prefixes:
        if command_with_prefix.startswith(prefix):
            command_name = command_with_prefix[len(prefix):]
            if '@' in command_name:
                command_name = command_name.split('@')[0]
            break

    if command_name in COMMAND_MAP:
        new_text_parts = [f"/{command_name}"]
        if len(text_parts) > 1:
            new_text_parts.extend(text_parts[1:])
        
        message.text = " ".join(new_text_parts)
        
        COMMAND_MAP[command_name](message)


# ==============================
# WEBHOOK CONFIG
# ==============================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200


if __name__ == "__main__":
    PORT = int(os.getenv("PORT", 5000))
    APP_URL = os.getenv("APP_URL")

    if not APP_URL:
        raise ValueError("APP_URL no está definida en Railway Variables") 

    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
