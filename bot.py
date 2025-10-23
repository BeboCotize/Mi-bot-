import os
import re
import requests
import time
from flask import Flask, request
from telebot import TeleBot, types
from cc_gen import cc_gen
# Asegúrate de que tus archivos 'gateway.py' y 'sagepay.py' estén subidos
from sagepay import ccn_gate as sagepay_check # <--- CORREGIDO: Importa ccn_gate y la renombra
 
from sagepay import sagepay_check # <--- FUNCIÓN NECESARIA PARA /ty
 
# ==============================
# CONFIGURACIÓN 
# ==============================

TOKEN = os.getenv("BOT_TOKEN")
bot = TeleBot(TOKEN, parse_mode='HTML')

# 📌 LISTAS DE USUARIOS PARA CONTROL DE SPAM Y ACCESO
# WHITELIST: IDs con acceso al bot Y SIN spam (cooldown)
WHITELIST = [
    '6116275760', '8470094114', '1073258864', '1337313600', '247556916']
# BLACKLIST: IDs con acceso al bot PERO CON spam (cooldown)
BLACKLIST = [
    '0000000000' # Ejemplo: Agrega aquí los IDs que deben tener spam
]

# Cooldowns y Tiempos
BB_COOLDOWN = {} 
MASS_COOLDOWN = {}
TY_COOLDOWN = {} 
COOLDOWN_TIME = 20 
MASS_COOLDOWN_TIME = 120 

# Mantenimiento Forzado
BB_MAINTENANCE = {}
MAINTENANCE_TIME = 600 

# Fotos en Telegram
IMG_PHOTO1 = "AgAD0QADlKxIL0z7_cT67p7pAASwzY020A4ABu8k9hFjI_TU_file_id_1_placeholder" 
IMG_PHOTO2 = "AgACAgEAAxkBAAE81YRo-UuWDmD16N0u1UZNGYRb3bp9kQACjgtrGy6KyUfGuhk5n4wzYQEAAwIAA3gAAzYE" 

# Flask app para webhook
app = Flask(__name__)

# Prefijos y Comandos
CUSTOM_PREFIXES = ['.', '&']
ALL_COMMANDS = ['bin', 'rnd', 'gen', 'bb', 'mass', 'cmds', 'start', 'deluxe', 'ty'] 


# ==============================
# FUNCIONES AUXILIARES DE AUTORIZACIÓN
# ==============================

def is_authorized_access(iduser: str) -> bool:
    """Verifica si el ID tiene acceso general al bot (debe estar en la WHITELIST)."""
    # Solo los IDs en WHITELIST tienen acceso general
    return iduser in WHITELIST

def should_apply_cooldown(iduser: str) -> bool:
    """
    Determina si se debe aplicar el cooldown a un ID.
    El cooldown se aplica a:
    1. IDs en la BLACKLIST.
    2. Cualquier ID que NO esté en la WHITELIST (pero que haya pasado el filtro de acceso general, aunque el filtro está arriba).
    
    Simplificamos: Si NO está en WHITELIST, se aplica el cooldown. 
    (Si no está en WHITELIST, no debería llegar aquí por el filtro de acceso, pero es más seguro).
    Adicionalmente, si está en BLACKLIST, TAMBIÉN se aplica.
    """
    # Si está en la WHITELIST, NO se aplica cooldown
    if iduser in WHITELIST:
        return False
    # Si está en la BLACKLIST, SÍ se aplica cooldown
    if iduser in BLACKLIST:
        return True
    
    # Por defecto, si el usuario no es ni WL ni BL, y de alguna manera llega, le aplicamos.
    # Pero el filtro de acceso general debería ser suficiente.
    # La manera más clara es: Cooldown si está en BL O si no está en WL.
    return iduser in BLACKLIST or iduser not in WHITELIST


# ==============================
# MIDDLEWARE DE ACCESO GENERAL (BLOQUEO)
# ==============================

@bot.message_handler(func=lambda message: not is_authorized_access(str(message.from_user.id)))
def unauthorized_access(message):
    """Bloquea CUALQUIER comando o mensaje si no está en la WHITELIST."""
    if message.chat.type == 'private':
        text = "❌ **Acceso Denegado.**\nTu ID no está autorizado para usar este bot."
        bot.reply_to(message, text)

# ==============================
# HANDLERS (COMANDOS) - LÓGICA COOLDOWN AJUSTADA
# ==============================

def bin_cmd(message):
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

    # === LÓGICA DE COOLDOWN (SPAM-LOCK) AJUSTADA ===
    if should_apply_cooldown(userid):
        if userid in BB_COOLDOWN:
            time_elapsed = current_time - BB_COOLDOWN[userid]
            if time_elapsed < COOLDOWN_TIME:
                remaining = int(COOLDOWN_TIME - time_elapsed)
                return bot.reply_to(
                    message, 
                    f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /bb."
                )
    
    # ... (Resto de la lógica de chequeo del BB Gateway) ...
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
    
    initial_message = bot.reply_to(message, "⚙️ Chequeando con BB Gateway...") 
    chat_id = initial_message.chat.id
    message_id = initial_message.message_id

    try:
        status_message = bb_gateway_check(f"{cc}|{mes}|{ano}|{cvv}")
        
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
            
            if "Max Retries" in status_message:
                message_detail = "Fallo de conexión o límite de intentos. Comando bloqueado por 10 min."
                BB_MAINTENANCE[userid] = time.time() + MAINTENANCE_TIME
            else:
                message_detail = status_message
            
        bin_number = cc[0:6]
        binsito = binlist(bin_number)
        
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
        
    # === ACTUALIZAR EL COOLDOWN (SOLO si debe aplicarse) ===
    if should_apply_cooldown(userid):
        BB_COOLDOWN[userid] = time.time()

    # ... (Edición del mensaje) ...
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
    current_time = time.time()
    
    # 🚨 LÓGICA DE MANTENIMIENTO FORZADO 🚨
    if userid in BB_MAINTENANCE and current_time < BB_MAINTENANCE[userid]:
        remaining = int(BB_MAINTENANCE[userid] - current_time)
        minutes = remaining // 60
        seconds = remaining % 60
        return bot.reply_to(
            message, 
            f"🛠️ Comando /mass bb en mantenimiento forzado (Max Retries). Por favor, espera {minutes} minutos y {seconds} segundos."
        )

    # === LÓGICA DE COOLDOWN PARA MASS AJUSTADA ===
    if should_apply_cooldown(userid):
        if userid in MASS_COOLDOWN:
            time_elapsed = current_time - MASS_COOLDOWN[userid]
            if time_elapsed < MASS_COOLDOWN_TIME:
                remaining = int(MASS_COOLDOWN_TIME - time_elapsed)
                return bot.reply_to(
                    message, 
                    f"🚫 ¡Calma! Debes esperar {remaining} segundos antes de volver a usar .mass bb."
                )
    
    # ... (Resto de la lógica de chequeo masivo) ...
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/mass", "").strip() if not message.reply_to_message else raw_text.strip()
    
    cc_lines = re.split(r'[\n\s]+', clean)

    cards_to_check = []
    cc_pattern = re.compile(r'(\d{12,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})')
    
    for line in cc_lines:
        match = cc_pattern.search(line)
        if match and len(cards_to_check) < 10:
            cc, mes, ano, cvv = match.groups()
            cards_to_check.append(f"{cc}|{mes}|{ano}|{cvv}")
    
    if not cards_to_check:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido o tarjetas no detectadas. Asegúrate de usar el formato:\n"
            "`/mass 4111...|12|2026|123` (hasta 10 líneas)",
            parse_mode="Markdown"
        )
    
    total_cards = len(cards_to_check)
    
    initial_message = bot.reply_to(
        message, 
        f"⚙️ Iniciando chequeo masivo de {total_cards} tarjetas con BB Gateway..."
    ) 
    chat_id = initial_message.chat.id
    message_id = initial_message.message_id
    
    results = []
    maintenance_triggered = False
    
    for i, full_cc in enumerate(cards_to_check, 1):
        cc, mes, ano, cvv = full_cc.split('|')
        
        progress_msg_base = f"⚙️ Chequeando Tarjeta {i}/{total_cards}: <code>{full_cc}</code>"
        
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"{progress_msg_base}\n\n**Resultados Chequeados:**\n{chr(10).join(results)}",
                parse_mode='HTML'
            )
        except:
            pass
        
        
        try:
            status_message = bb_gateway_check(full_cc)
            
            if "APROBADO" in status_message or "APPROVED" in status_message:
                status_emoji = "✅"
                status_bold = "APROBADA"
                message_detail = status_message.split(":")[-1].strip()
            elif "DECLINADO" in status_message or "DECLINED" in status_message:
                status_emoji = "❌"
                status_bold = "DECLINADA"
                message_detail = status_message.split(":")[-1].strip()
            else:
                status_emoji = "⚠️"
                status_bold = "ERROR"
                if "Max Retries" in status_message:
                    message_detail = "Fallo de conexión. Bloqueo activado."
                    maintenance_triggered = True 
                else:
                    message_detail = status_message
            
            bin_number = cc[0:6]
            binsito = binlist(bin_number)
            
            result_line = f"""
{status_emoji} <b>STATUS: {status_bold}</b>
💳 CARD: <code>{full_cc}</code>
📄 MESSAGE: <b>{message_detail}</b>
🏦 BANK: {binsito[6]}
🌎 COUNTRY: {binsito[4]} {binsito[5]}
━━━━━━━━━━━━━━━"""

            results.append(result_line)
            
            current_result_text = "\n".join(results)
            
            progress_text = f"""
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
🌐 <b>PROGRESO: {i}/{total_cards}</b>
━━━━━━━━━━━━━━━
{current_result_text}
"""
            try:
                bot.edit_message_text(
                    chat_id=chat_id, 
                    message_id=message_id, 
                    text=progress_text, 
                    parse_mode='HTML'
                )
            except Exception as edit_error:
                print(f"Error al editar mensaje de progreso: {edit_error}")


            if maintenance_triggered:
                break
            
        except Exception as e:
            error_line = f"💳 <code>{full_cc}</code> | ❌ ERROR (Excepción: {str(e)})"
            results.append(error_line)
            print(f"Error en mass_bb para {full_cc}: {e}")
            
    if maintenance_triggered:
        BB_MAINTENANCE[userid] = time.time() + MAINTENANCE_TIME
        results.append("\n\n⚠️ MANTENIMIENTO FORZADO ACTIVADO: Comando /bb y /mass bb bloqueados por 10 minutos.")
        
    final_text = f"""
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━
🌐 **Total Chequeado:** {total_cards}
"""
    
    # === ACTUALIZAR EL COOLDOWN (SOLO si debe aplicarse) ===
    if should_apply_cooldown(userid):
        MASS_COOLDOWN[userid] = time.time()

    try:
        bot.edit_message_text(
            chat_id=chat_id, 
            message_id=message_id, 
            text=final_text, 
            parse_mode='HTML'
        )
    except Exception as edit_error:
        bot.send_message(chat_id=chat_id, text=final_text, parse_mode='HTML')
        print(f"Error al editar mensaje final: {edit_error}")


def ty_cmd(message):
    userid = str(message.from_user.id)
    current_time = time.time()
    
    # === LÓGICA DE COOLDOWN (SPAM-LOCK) AJUSTADA ===
    if should_apply_cooldown(userid):
        if userid in TY_COOLDOWN:
            time_elapsed = current_time - TY_COOLDOWN[userid]
            if time_elapsed < COOLDOWN_TIME:
                remaining = int(COOLDOWN_TIME - time_elapsed)
                return bot.reply_to(
                    message, 
                    f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /ty."
                )
    
    # ... (Resto de la lógica del SagePay Gateway) ...
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text
    clean = raw_text.replace("/ty", "").strip() if not message.reply_to_message else raw_text.strip()
    
    parts = re.split(r"[| \n\t]+", clean)

    if len(parts) < 4:
        return bot.reply_to(
            message,
            "⚠️ Formato inválido.\nEjemplo:\n"
            "`/ty 4111111111111111|12|2026|123`",
            parse_mode="Markdown"
        )

    cc, mes, ano, cvv = parts[0:4]
    
    initial_message = bot.reply_to(message, "⚙️ Chequeando con SagePay Gateway...") 
    chat_id = initial_message.chat.id
    message_id = initial_message.message_id

    try:
        status_message = sagepay_check(f"{cc}|{mes}|{ano}|{cvv}")
        
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
            message_detail = status_message
            
        bin_number = cc[0:6]
        binsito = binlist(bin_number)
        
        final_text = f"""
{emoji} CARD --> <code>{cc}|{mes}|{ano}|{cvv}</code>
{emoji} STATUS --> <b>{status}</b> {emoji}
{emoji} MESSAGE --> <b>{message_detail}</b>
[GATEWAY] <b>[SagePay Gateway]</b>

[BIN INFO]
{emoji} BIN --> <b>{binsito[1]} {binsito[2]}</b>
{emoji} BANK --> <b>{binsito[6]}</b>
{emoji} COUNTRY --> <b>{binsito[4]} {binsito[5]}</b>
"""
    except Exception as e:
        final_text = f"❌ Error ejecutando SagePay Gateway:\n{e}"
        print(f"Error en ty_cmd: {e}")
        
    # === ACTUALIZAR EL COOLDOWN (SOLO si debe aplicarse) ===
    if should_apply_cooldown(userid):
        TY_COOLDOWN[userid] = time.time()

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
        
# -----------------------------------
## COMANDOS GENERALES
# -----------------------------------

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
# ROUTER Y MAPEO DE COMANDOS
# ==============================

COMMAND_MAP = {
    'bin': bin_cmd,
    'rnd': rand,
    'gen': gen,
    'bb': gate_bb,
    'mass': mass_bb, 
    'cmds': cmds,
    'start': start,
    'deluxe': deluxe,
    'ty': ty_cmd,
}

def is_command_with_prefix(message):
    """Verifica si el mensaje comienza con '/', '.', o '&' y tiene un comando válido."""
    if message.text is None:
        return False
        
    parts = message.text.split()
    if not parts:
        return False

    first_word = parts[0].lower()
    
    # 🚨 LÍNEA CORREGIDA PARA INDENTACIÓN 🚨
    prefixes = ['/'] + CUSTOM_PREFIXES
    for prefix in prefixes:
        if first_word.startswith(prefix):
            # Lógica corregida y bien indentada
            command = first_word[len(prefix):]
            if '@' in command:
                command = command.split('@')[0]
                
            return command in ALL_COMMANDS
            
    return False

@bot.message_handler(func=is_command_with_prefix)
def handle_all_commands(message):
    # La autorización ya fue verificada por el middleware 'unauthorized_access'

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


# -----------------------------------
## CALLBACK QUERY HANDLER
# -----------------------------------

@bot.callback_query_handler(func=lambda call: is_authorized_access(str(call.from_user.id)))
def callback_query_handler(call):
    # Definir los botones para poder reutilizarlos en las ediciones
    buttons_cmds = [
        [
            types.InlineKeyboardButton('Gateways', callback_data='gates'),
            types.InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [types.InlineKeyboardButton('Cerrar', callback_data='close')]
    ]
    markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
    
    if call.data == 'gates':
        text_gateways = """
🌐 **LISTA DE GATEWAYS** 🌐
 
- 💳 **/bb** → BB Gateway (Solo tarjeta)
- 💳 **/ty** → SagePay Gateway (Solo tarjeta)
- 🍔 **/mass bb** → Chequeo masivo (Hasta 10 tarjetas)
"""
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text_gateways,
                reply_markup=markup_buttom,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, text="Mostrando Gateways.")
        except Exception:
            bot.answer_callback_query(call.id, text="⚠️ No se pudo editar el mensaje.")
            
    elif call.data == 'tools':
        text_tools = """
🛠️ **HERRAMIENTAS** 🛠️

- 🔢 **/gen** → Generador de CCs por BIN (Con BIN info)
- 🔍 **/bin** → Buscador de BIN
"""
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=text_tools,
                reply_markup=markup_buttom,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, text="Mostrando Herramientas.")
        except Exception:
            bot.answer_callback_query(call.id, text="⚠️ No se pudo editar el mensaje.")
            
    elif call.data == 'close':
        try:
            bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption="<b>⚠️ Botonera cerrada. Vuelve a usar /cmds.</b>",
                reply_markup=None, 
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, text="Botonera cerrada.")
        except Exception:
            bot.answer_callback_query(call.id, text="⚠️ No se pudo editar el mensaje.")


# ==============================
# WEBHOOK CONFIG
# ==============================

def binlist(bin: str) -> tuple | bool:
    try:
        # Nota: binlist.io es más rápido y estable que binlist.net o similar
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
        # En Railway, esta variable debe estar definida en las variables de entorno
        raise ValueError("APP_URL no está definida en Railway Variables") 

    bot.remove_webhook()
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}")

    app.run(host="0.0.0.0", port=PORT)
