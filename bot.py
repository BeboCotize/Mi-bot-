# Importar módulos necesarios
import os # Para acceder a las variables de entorno (como el Token del bot)
import re # Para expresiones regulares (buscar patrones de números/CCs en el texto)
import requests # Para hacer peticiones HTTP (consultar BINs y generar direcciones falsas)
import time # Para gestionar los tiempos de espera (cooldowns)
from flask import Flask, request # Para configurar el servidor web (Webhook de Telegram)
from telebot import TeleBot, types # Librería principal de Telegram (pyTelegramBotAPI)
from cc_gen import cc_gen # Importa la función para generar tarjetas (debe existir cc_gen.py)

# Asegúrate de que tu archivo 'gateway.py' esté subido junto con este código
from gateway import ccn_gate as bb_gateway_check # Importa la función del checker/gateway (debe existir gateway.py)

# ====================================================================================================
# NUEVA IMPORTACIÓN PARA LOS COMANDOS /ty y /massty (SAGEPAY)
# ====================================================================================================
# Asegúrate de que tu archivo 'sagepay.py' esté subido junto con este código
from sagepay import ccn_gate # Importa la función ccn_gate de sagepay.py
# ====================================================================================================

# ==============================
# CONFIGURACIÓN DEL BOT Y COOLDOWNS
# ==============================

# Obtiene el Token del bot de las variables de entorno de Railway
TOKEN = os.getenv("BOT_TOKEN")
# Inicializa el bot con el Token y establece el modo de parseo a HTML para formato de texto
bot = TeleBot(TOKEN, parse_mode='HTML')

# 📌 ID de usuarios autorizados (solo estos IDs pueden usar los comandos)
USERS = [
    '6116275760', '8470094114', '1073258864', '7457808814', '5551626715', '7973321076']

# Diccionario para almacenar el último uso del comando /bb por usuario
BB_COOLDOWN = {}
COOLDOWN_TIME = 20 # Tiempo de espera en segundos para /bb

# 🚨 Diccionario para mantenimiento forzado (bloquea el /bb si el gateway falla muchas veces)
BB_MAINTENANCE = {}
MAINTENANCE_TIME = 600 # 10 minutos en segundos

# 🚨 Cooldown específico para el comando masivo /mass bb
MASS_COOLDOWN = {}
MASS_COOLDOWN_TIME = 120 # 2 minutos de espera para el comando masivo BB

# 🚨 Cooldown específico para el comando /ty (SagePay)
TY_COOLDOWN = {}
TY_COOLDOWN_TIME = 40 # 40 segundos de espera para el comando /ty

# 🚨 Cooldown específico para el comando masivo /massty
MASS_TY_COOLDOWN = {}
MASS_TY_COOLDOWN_TIME = 120 # 2 minutos de espera para el comando masivo TY

# Fotos en Telegram (Usar FILE_ID para máxima estabilidad y velocidad)
# **⚠️ REEMPLAZA ESTOS CON TUS FILE_ID REALES ⚠️**
IMG_PHOTO1 = "AgAD0QADlKxIL0z7_cT67p7pAASwzY020A4ABu8k9hFjI_TU_file_id_1_placeholder"
IMG_PHOTO2 = "AgACAgEAAxkBAAE81YRo-UuWDmD16N0u1UZNGYRb3bp9kQACjgtrGy6KyUfGuhk5n4wzYQEAAwIAA3gAAzYE"

# Flask app para configurar el webhook (servidor web)
app = Flask(__name__)

# 📌 Prefijos personalizados que el bot aceptará, además de '/'
CUSTOM_PREFIXES = ['.', '&']

# Lista de todos tus comandos (sin prefijo) para el router
ALL_COMMANDS = ['bin', 'rnd', 'gen', 'bb', 'mass', 'cmds', 'start', 'deluxe', 'ty', 'massty']

# ==============================
# FUNCIONES AUXILIARES
# ==============================

def ver_user(iduser: str) -> bool:
    """Verifica si el ID del usuario está en la lista de USERS autorizados."""
    return iduser in USERS

def binlist(bin: str) -> tuple | bool:
    """Consulta la información de un BIN (primeros 6 dígitos) usando binlist.io."""
    try:
        # Petición a binlist.io para obtener detalles del BIN
        result = requests.get(f'https://binlist.io/lookup/{bin}/').json()
        return (
            result['number']['iin'], # BIN completo (por si devuelve más de 6)
            result['scheme'], # Visa, Mastercard, etc.
            result['type'], # Debit, Credit, etc.
            result['category'], # Commercial, Gold, etc.
            result['country']['name'], # País
            result['country']['emoji'], # Bandera emoji
            result['bank']['name'] # Nombre del banco
        )
    except:
        # Retorna False si falla la conexión o no encuentra el BIN
        return False

def dir_fake():
    """Genera una dirección y datos personales usando randomuser.me."""
    try:
        r = requests.get("https://randomuser.me/api/", timeout=10)
        if r.status_code != 200:
            return None # Retorna None si la API no responde bien
        data = r.json()["results"][0]
        # Devuelve un diccionario con los datos
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
# HANDLERS (COMANDOS)
# ==============================

def bin_cmd(message):
    """Maneja el comando /bin para chequear información de un BIN."""
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
    """Maneja el comando /rnd para generar datos aleatorios (fake address)."""
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
    """Maneja el comando /gen para generar tarjetas a partir de un BIN y formato."""
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
    
    𝗘𝗫𝗧𝗥𝗔: {cc}|{mes}|{ano}|{cvv}
    """
    bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)

def gate_bb(message):
    """Maneja el comando /bb para chequear una tarjeta con el BB Gateway."""
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
        # Actualizar cooldown si el formato es inválido, para evitar penalizar al usuario
        BB_COOLDOWN[userid] = time.time()
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
        # LLAMADA A TU GATEWAY MODIFICADO
        status_message = bb_gateway_check(f"{cc}|{mes}|{ano}|{cvv}") 
        
        # 3. Parseamos el resultado
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
                BB_MAINTENANCE[userid] = time.time() + MAINTENANCE_TIME 
            else: 
                message_detail = status_message 
        
        # 4. Obtenemos información adicional para el formato
        bin_number = cc[0:6] 
        binsito = binlist(bin_number) 
        
        # 5. Creamos el mensaje final
        final_text = f"""
        
        {emoji} CARD --> {cc}|{mes}|{ano}|{cvv}
        {emoji} STATUS --> {status} {emoji}
        {emoji} MESSAGE --> {message_detail}
        [GATEWAY] [BB Gateway]
        
        [BIN INFO]
        {emoji} BIN --> {binsito[1]} {binsito[2]}
        {emoji} BANK --> {binsito[6]}
        {emoji} COUNTRY --> {binsito[4]} {binsito[5]}
        """
    except Exception as e:
        final_text = f"❌ Error ejecutando BB Gateway:\n{e}"
        print(f"Error en gate_bb: {e}")

    # === ACTUALIZAR EL COOLDOWN === 
    BB_COOLDOWN[userid] = time.time() 
    
    # 6. EDITAR el mensaje inicial con la respuesta final (Live Editing)
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
    """Maneja el comando /mass para chequear múltiples tarjetas con el BB Gateway."""
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
            f"🛠️ Comando /mass bb en mantenimiento forzado (Max Retries). Por favor, espera {minutes} minutos y {seconds} segundos." 
        ) 
    
    # === LÓGICA DE COOLDOWN PARA MASS === 
    if userid in MASS_COOLDOWN: 
        time_elapsed = current_time - MASS_COOLDOWN[userid] 
        if time_elapsed < MASS_COOLDOWN_TIME: 
            remaining = int(MASS_COOLDOWN_TIME - time_elapsed) 
            return bot.reply_to( 
                message, 
                f"🚫 ¡Calma! Debes esperar {remaining} segundos antes de volver a usar .mass bb." 
            ) 
    
    # 1. Extraer el texto de las CCs
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/mass", "").strip() if not message.reply_to_message else raw_text.strip() 
    cc_lines = re.split(r'[\n\s]+', clean) 
    
    # 2. Parsear y validar las tarjetas
    cards_to_check = [] 
    cc_pattern = re.compile(r'(\d{12,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})') 
    
    for line in cc_lines: 
        match = cc_pattern.search(line) 
        if match and len(cards_to_check) < 10:
            cc, mes, ano, cvv = match.groups() 
            cards_to_check.append(f"{cc}|{mes}|{ano}|{cvv}") 
    
    if not cards_to_check: 
        MASS_COOLDOWN[userid] = time.time()
        return bot.reply_to( 
            message, 
            "⚠️ Formato inválido o tarjetas no detectadas. Asegúrate de usar el formato:\n" 
            "`/mass 4111...|12|2026|123` (hasta 10 líneas)", 
            parse_mode="Markdown" 
        ) 
    
    total_cards = len(cards_to_check) 
    
    # 3. ENVIAR MENSAJE INICIAL
    initial_message = bot.reply_to( 
        message, 
        f"⚙️ Iniciando chequeo masivo de {total_cards} tarjetas con BB Gateway..." 
    ) 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    results = []
    maintenance_triggered = False
    
    # 4. Procesar cada tarjeta con LIVE EDITING 
    for i, full_cc in enumerate(cards_to_check, 1): 
        cc, mes, ano, cvv = full_cc.split('|') 
        
        # 4.1. Intentar editar el mensaje antes del check para mostrar la CC actual 
        try: 
            current_result_text = "\n".join(results) 
            progress_text = f"""
            
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
🌐 PROGRESO: {i}/{total_cards}
💳 TARJETA: <code>{full_cc}</code>
━━━━━━━━━━━━━━━
**Resultados Previos:**
{current_result_text}"""
            
            bot.edit_message_text( 
                chat_id=chat_id, 
                message_id=message_id, 
                text=progress_text, 
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
            
{status_emoji} STATUS: {status_bold}
💳 CARD: <code>{full_cc}</code>
📄 MESSAGE: {message_detail}
🏦 BANK: {binsito[6]}
🌎 COUNTRY: {binsito[4]} {binsito[5]}
━━━━━━━━━━━━━━━"""
            
            results.append(result_line) 
            
            if maintenance_triggered: 
                break 
        
        except Exception as e: 
            error_line = f"💳 <code>{full_cc}</code> | ❌ ERROR (Excepción: {str(e)})" 
            results.append(error_line) 
            print(f"Error en mass_bb para {full_cc}: {e}") 
    
    # 5. Aplicar mantenimiento si se detectó el error "Max Retries"
    if maintenance_triggered: 
        BB_MAINTENANCE[userid] = time.time() + MAINTENANCE_TIME 
        results.append("\n\n⚠️ MANTENIMIENTO FORZADO ACTIVADO: Comando /bb y /mass bb bloqueados por 10 minutos.") 
    
    # 6. Formatear y enviar resultado FINAL 
    final_text = f"""
    
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━
🌐 Total Chequeado: {total_cards}
"""
    
    # === ACTUALIZAR EL COOLDOWN === 
    MASS_COOLDOWN[userid] = time.time() 
    
    # 7. EDITAR el mensaje por última vez con el resultado final 
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

# ==============================
# COMANDO /ty (SagePay) - CON COOLDOWN DE 40s
# ==============================

def gate_ty(message):
    """Maneja el comando /ty para chequear una tarjeta con la función ccn_gate (SagePay)."""
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    current_time = time.time() 
    
    # === LÓGICA DE COOLDOWN (SPAM-LOCK) === 
    if userid in TY_COOLDOWN: 
        time_elapsed = current_time - TY_COOLDOWN[userid] 
        if time_elapsed < TY_COOLDOWN_TIME: 
            remaining = int(TY_COOLDOWN_TIME - time_elapsed) 
            return bot.reply_to( 
                message, 
                f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /ty." 
            ) 

    # 1. Preparar el texto de entrada
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/ty", "").strip() if not message.reply_to_message else raw_text.strip() 
    parts = re.split(r"[| \n\t]+", clean) 
    
    if len(parts) < 4: 
        # Actualizar cooldown si el formato es inválido, para no penalizar al usuario
        TY_COOLDOWN[userid] = time.time() 
        return bot.reply_to( 
            message, 
            "⚠️ Formato inválido.\nEjemplo:\n" 
            "`/ty 4111111111111111|12|2026|123`", 
            parse_mode="Markdown" 
        ) 
    
    cc, mes, ano, cvv = parts[0:4] 
    full_cc_str = f"{cc}|{mes}|{ano}|{cvv}"
    
    # 2. ENVIAR EL MENSAJE INICIAL
    initial_message = bot.reply_to(message, "⚙️ Chequeando con SagePay Gateway...") 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    
    try:
        # LLAMADA A LA FUNCIÓN DE SAGEPAY (ccn_gate de sagepay.py)
        raw_output = ccn_gate(full_cc_str) # Llama a la función importada
        
        # 3. Parseamos el resultado
        output_parts = raw_output.strip().split('|')

        if len(output_parts) >= 3:
            status = output_parts[0].strip()
            message_detail = output_parts[1].strip()

            emoji = "⚠️"
            if "APPROVED" in status:
                status_text = "APPROVED"
                emoji = "✅"
            elif "DECLINED" in status:
                status_text = "DECLINED"
                emoji = "❌"
            elif "PROBABLE LIVE" in status:
                status_text = "PROBABLE LIVE"
                emoji = "⚡"
            elif "ERROR" in status:
                status_text = "ERROR"
                emoji = "⚠️"
            else:
                status_text = status

        else:
            status_text = "ERROR"
            emoji = "⚠️"
            message_detail = f"Formato de respuesta inválido: {raw_output}"
        
        # 4. Obtenemos información adicional
        bin_number = cc[0:6] 
        binsito = binlist(bin_number) 
        
        # 5. Creamos el mensaje final
        final_text = f"""
        
{emoji} CARD --> {full_cc_str}
{emoji} STATUS --> {status_text} {emoji}
{emoji} MESSAGE --> {message_detail}
[GATEWAY] [SagePay Gateway]

[BIN INFO]
{emoji} BIN --> {binsito[1]} {binsito[2]}
{emoji} BANK --> {binsito[6]}
{emoji} COUNTRY --> {binsito[4]} {binsito[5]}
"""
    except Exception as e:
        final_text = f"❌ Error ejecutando SagePay Gateway:\n{e}"
        print(f"Error en gate_ty: {e}")

    # 6. ACTUALIZAR EL COOLDOWN
    TY_COOLDOWN[userid] = time.time()
    
    # 7. EDITAR el mensaje inicial con la respuesta final
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

# ==============================
# COMANDO /massty (SagePay Mass)
# ==============================

def mass_ty(message):
    """Maneja el comando /massty para chequear múltiples tarjetas con el SagePay Gateway."""
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    current_time = time.time() 
    
    # === LÓGICA DE COOLDOWN PARA MASS TY === 
    if userid in MASS_TY_COOLDOWN: 
        time_elapsed = current_time - MASS_TY_COOLDOWN[userid] 
        if time_elapsed < MASS_TY_COOLDOWN_TIME: 
            remaining = int(MASS_TY_COOLDOWN_TIME - time_elapsed) 
            return bot.reply_to( 
                message, 
                f"🚫 ¡Calma! Debes esperar {remaining} segundos antes de volver a usar /massty." 
            ) 
    
    # 1. Extraer el texto de las CCs
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/massty", "").strip() if not message.reply_to_message else raw_text.strip() 
    cc_lines = re.split(r'[\n\s]+', clean) 
    
    # 2. Parsear y validar las tarjetas
    cards_to_check = [] 
    cc_pattern = re.compile(r'(\d{12,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})') 
    
    for line in cc_lines: 
        match = cc_pattern.search(line) 
        if match and len(cards_to_check) < 10:
            cc, mes, ano, cvv = match.groups() 
            cards_to_check.append(f"{cc}|{mes}|{ano}|{cvv}") 
    
    if not cards_to_check: 
        MASS_TY_COOLDOWN[userid] = time.time()
        return bot.reply_to( 
            message, 
            "⚠️ Formato inválido o tarjetas no detectadas. Asegúrate de usar el formato:\n" 
            "`/massty 4111...|12|2026|123` (hasta 10 líneas)", 
            parse_mode="Markdown" 
        ) 
    
    total_cards = len(cards_to_check) 
    
    # 3. ENVIAR MENSAJE INICIAL
    initial_message = bot.reply_to( 
        message, 
        f"⚙️ Iniciando chequeo masivo de {total_cards} tarjetas con SagePay Gateway..." 
    ) 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    results = []
    
    # 4. Procesar cada tarjeta con LIVE EDITING 
    for i, full_cc in enumerate(cards_to_check, 1): 
        cc, mes, ano, cvv = full_cc.split('|') 
        
        # 4.1. Intentar editar el mensaje antes del check para mostrar la CC actual 
        try: 
            current_result_text = "\n".join(results) 
            progress_text = f"""
            
🔹 CHEQUEO MASIVO SAGEPAY GATEWAY 🔹
━━━━━━━━━━━━━━━
🌐 PROGRESO: {i}/{total_cards}
💳 TARJETA: <code>{full_cc}</code>
━━━━━━━━━━━━━━━
**Resultados Previos:**
{current_result_text}"""
            
            bot.edit_message_text( 
                chat_id=chat_id, 
                message_id=message_id, 
                text=progress_text, 
                parse_mode='HTML' 
            ) 
        except: 
            pass
        
        try: 
            # Llama al Gateway para chequear la CC (SagePay)
            raw_output = ccn_gate(full_cc)
            output_parts = raw_output.strip().split('|')

            emoji = "⚠️"
            if len(output_parts) >= 3:
                status = output_parts[0].strip()
                message_detail = output_parts[1].strip()

                if "APPROVED" in status:
                    status_emoji = "✅" 
                    status_bold = "APROBADA"
                elif "DECLINED" in status:
                    status_emoji = "❌" 
                    status_bold = "DECLINADA"
                elif "PROBABLE LIVE" in status:
                    status_emoji = "⚡"
                    status_bold = "PROBABLE LIVE"
                else:
                    status_emoji = "⚠️"
                    status_bold = "ERROR"
            else:
                status_emoji = "⚠️"
                status_bold = "ERROR"
                message_detail = f"Formato de respuesta inválido: {raw_output}"

            bin_number = cc[0:6] 
            binsito = binlist(bin_number) 
            
            # --- Formato PRO mejorado para cada resultado --- 
            result_line = f"""
{status_emoji} STATUS: {status_bold}
💳 CARD: <code>{full_cc}</code>
📄 MESSAGE: {message_detail}
🏦 BANK: {binsito[6]}
🌎 COUNTRY: {binsito[4]} {binsito[5]}
━━━━━━━━━━━━━━━"""
            
            results.append(result_line) 
            
            time.sleep(1) # Pequeña pausa
        
        except Exception as e: 
            error_line = f"💳 <code>{full_cc}</code> | ❌ ERROR (Excepción: {str(e)})" 
            results.append(error_line) 
            print(f"Error en mass_ty para {full_cc}: {e}") 
    
    # 5. Formatear y enviar resultado FINAL 
    final_text = f"""
    
🔹 CHEQUEO MASIVO SAGEPAY GATEWAY 🔹
━━━━━━━━━━━━━━━
{chr(10).join(results)}
━━━━━━━━━━━━━━━
🌐 Total Chequeado: {total_cards}
"""
    
    # === ACTUALIZAR EL COOLDOWN === 
    MASS_TY_COOLDOWN[userid] = time.time() 
    
    # 6. EDITAR el mensaje por última vez con el resultado final 
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

def cmds(message):
    """Maneja el comando /cmds para mostrar el menú de comandos con botones."""
    buttons_cmds = [
        [
            types.InlineKeyboardButton('Gateways', callback_data='gates'),
            types.InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [types.InlineKeyboardButton('Cerrar', callback_data='close')]
    ]
    markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
    text = "📋 Lista de comandos"

    bot.send_photo( 
        chat_id=message.chat.id, 
        photo=IMG_PHOTO1,
        caption=text, 
        reply_to_message_id=message.id, 
        reply_markup=markup_buttom 
    ) 

def start(message):
    """Maneja el comando /start (mensaje de bienvenida)."""
    text = f"""
    ⚠️ Bienvenido a DuluxeChk ⚠️
    • Para ver tools/Gateways: /cmds
    • Info: /Deluxe
    🚸 @DuluxeChk
    """
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO2, caption=text)

def deluxe(message):
    """Maneja el comando /deluxe para mostrar términos o información."""
    text = f"""
    ⚠️ Términos ⚠️

    Macros/scripts = ban

    Reembolsos con saldo bineado = ban

    Difamación = ban

    Robo de gates = ban
    """
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO1, caption=text)

# ==============================
# ROUTER DE COMANDOS CON PREFIJOS
# ==============================

# Mapeo de nombres de comandos a sus funciones handler
COMMAND_MAP = {
    'bin': bin_cmd,
    'rnd': rand,
    'gen': gen,
    'bb': gate_bb,
    'mass': mass_bb, 
    'cmds': cmds,
    'start': start,
    'deluxe': deluxe,
    'ty': gate_ty, 
    'massty': mass_ty,
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

# Decorador que usa la función anterior para filtrar mensajes de comandos
@bot.message_handler(func=is_command_with_prefix)
def handle_all_commands(message):
    """Función que dirige el mensaje a la función handler correcta (router)."""
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
        # Modifica el mensaje para que el handler interno lo reciba como un comando normal
        new_text_parts = [f"/{command_name}"] 
        if len(text_parts) > 1: 
            new_text_parts.extend(text_parts[1:]) 
        message.text = " ".join(new_text_parts) 
        COMMAND_MAP[command_name](message)

# ==============================
# HANDLER DE INLINE KEYBOARD (Callback Queries)
# ==============================

@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    """Maneja las interacciones con los botones Inline del menú /cmds."""
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    data = call.data

    if data == 'close':
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
    elif data == 'gates':
        text_gates = """
        💳 𝗚𝗔𝗧𝗘𝗪𝗔𝗬𝗦 𝗔𝗖𝗧𝗜𝗩𝗢𝗦 💳
        
        • `/bb` - Chequeador BB Gateway (Cooldown 20s)
        • `/ty` - Chequeador SagePay Gateway (Cooldown 40s)
        • `/mass` - Chequeador masivo BB (Max 10 CCs, Cooldown 120s)
        • `/massty` - Chequeador masivo SagePay (Nuevo, Max 10 CCs, Cooldown 120s)
        
        🚨 Nota: Usa el formato `CC|MM|YYYY|CVV`
        """
        buttons = [[types.InlineKeyboardButton('🔙 Volver', callback_data='start_menu')]]
        markup = types.InlineKeyboardMarkup(buttons)
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id, 
                message_id=message_id, 
                caption=text_gates, 
                reply_markup=markup,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error al editar mensaje de Gateways: {e}")

    elif data == 'tools':
        text_tools = """
        🛠️ 𝗛𝗘𝗥𝗥𝗔𝗠𝗜𝗘𝗡𝗧𝗔𝗦 🛠️
        
        • `/bin` - Info de un BIN (Primeros 6 dígitos de la CC)
        • `/gen` - Generador de CCs con formato (Ej: `/gen 4111xxxxxxxxx|xx|xxxx|rnd`)
        • `/rnd` - Generador de direcciones falsas
        """
        buttons = [[types.InlineKeyboardButton('🔙 Volver', callback_data='start_menu')]]
        markup = types.InlineKeyboardMarkup(buttons)
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id, 
                message_id=message_id, 
                caption=text_tools, 
                reply_markup=markup,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error al editar mensaje de Herramientas: {e}")
            
    elif data == 'start_menu':
        text = "📋 Lista de comandos"
        buttons_cmds = [
            [
                types.InlineKeyboardButton('Gateways', callback_data='gates'),
                types.InlineKeyboardButton('Herramientas', callback_data='tools')
            ],
            [types.InlineKeyboardButton('Cerrar', callback_data='close')]
        ]
        markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
        
        try:
            bot.edit_message_caption(
                chat_id=chat_id, 
                message_id=message_id, 
                caption=text, 
                reply_markup=markup_buttom,
                parse_mode='HTML'
            )
        except Exception as e:
            print(f"Error al editar mensaje a start_menu: {e}")
            
    bot.answer_callback_query(call.id)

# ==============================
# WEBHOOK CONFIG (Ejecución en Railway)
# ==============================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Ruta para recibir las actualizaciones de Telegram (Webhook)."""
    json_str = request.get_data().decode("UTF-8")
    update = types.Update.de_json(json_str) 
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    """Punto de entrada principal para ejecutar la aplicación."""
    PORT = int(os.getenv("PORT", 5000))
    APP_URL = os.getenv("APP_URL")

    if not APP_URL: 
        raise ValueError("APP_URL no está definida en Railway Variables") 
        
    bot.remove_webhook() 
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}") 
    app.run(host="0.0.0.0", port=PORT)
