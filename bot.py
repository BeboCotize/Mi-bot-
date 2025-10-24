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
# 🆕 NUEVA IMPORTACIÓN PARA EL COMANDO /ty (SAGEPAY)
# ====================================================================================================
# Asegúrate de que tu archivo 'sagepay.py' esté subido junto con este código
from sagepay import ccn_gate # Importa la función ccn_gate de sagepay.py
# ====================================================================================================

# ==============================
# CONFIGURACIÓN DEL BOT Y WEBHOOK
# ==============================

# Obtiene el Token del bot de las variables de entorno de Railway
TOKEN = os.getenv("BOT_TOKEN")
# Inicializa el bot con el Token y establece el modo de parseo a HTML para formato de texto
bot = TeleBot(TOKEN, parse_mode='HTML')

# 📌 ID de usuarios autorizados (solo estos IDs pueden usar los comandos)
USERS = [
    '6116275760', '8470094114', '1073258864', '7457808814']

# Diccionario para almacenar el último uso del comando /bb por usuario (para evitar spam)
BB_COOLDOWN = {}
COOLDOWN_TIME = 20 # Tiempo de espera en segundos para reintentar el comando /bb

# 🚨 Diccionario para mantenimiento forzado (bloquea el /bb si el gateway falla muchas veces)
BB_MAINTENANCE = {}
MAINTENANCE_TIME = 600 # 10 minutos en segundos (10 * 60)

# 🚨 Cooldown específico para el comando masivo /mass
MASS_COOLDOWN = {}
MASS_COOLDOWN_TIME = 120 # 2 minutos de espera para el comando masivo

# Fotos en Telegram (Usar FILE_ID para máxima estabilidad y velocidad)
# **⚠️ REEMPLAZA ESTOS CON TUS FILE_ID REALES ⚠️**
IMG_PHOTO1 = "AgAD0QADlKxIL0z7_cT67p7pAASwzY020A4ABu8k9hFjI_TU_file_id_1_placeholder"
IMG_PHOTO2 = "AgACAgEAAxkBAAE81YRo-UuWDmD16N0u1UZNGYRb3bp9kQACjgtrGy6KyUfGuhk5n4wzYQEAAwIAA3gAAzYE"

# Flask app para configurar el webhook (servidor web)
app = Flask(__name__)

# 📌 Prefijos personalizados que el bot aceptará, además de '/'
CUSTOM_PREFIXES = ['.', '&']

# Lista de todos tus comandos (sin prefijo) para el router
# ⬆️ AÑADIDO 'ty'
ALL_COMMANDS = ['bin', 'rnd', 'gen', 'bb', 'mass', 'cmds', 'start', 'deluxe', 'ty']

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

    # Intenta obtener el BIN del mensaje al que se responde o del texto después del comando
    if message.reply_to_message: 
        search_bin = re.findall(r'[0-9]+', str(message.reply_to_message.text)) 
    else: 
        text_after_command = " ".join(message.text.split()[1:]) 
        search_bin = re.findall(r'[0-9]+', text_after_command) 
    
    if not search_bin: 
        return bot.reply_to(message, "Bin no reconocido.") 
    
    number = search_bin[0][0:6] # Toma solo los primeros 6 dígitos
    data = binlist(number) # Llama a la función para buscar el BIN
    
    if not data: 
        return bot.reply_to(message, "Bin no encontrado.") 
    
    # Formato de la respuesta con los datos obtenidos
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

    data = dir_fake() # Llama a la función para generar la dirección
    if not data: 
        return bot.reply_to(message, '⚠️ Error obteniendo dirección.') 
    
    # Formato de la respuesta con los datos aleatorios
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

    # Extrae el texto después del comando para buscar el formato CC|MM|YYYY|CVV
    text_after_command = " ".join(message.text.split()[1:]) 
    inputcc = re.findall(r'[0-9x]+', text_after_command) # Busca secuencias de números y 'x'
    
    if not inputcc: 
        return bot.reply_to(message, "Formato incorrecto.") 
    
    # Asigna las partes de la CC, usando valores por defecto si no se encuentran
    cc = inputcc[0] 
    mes = inputcc[1][0:2] if len(inputcc) > 1 else "xx" 
    ano = inputcc[2] if len(inputcc) > 2 else "xxxx" 
    cvv = inputcc[3] if len(inputcc) > 3 else "rnd" 
    
    if len(cc) < 6: 
        return bot.reply_to(message, "CC incompleta.") 
    
    bin_number = cc[0:6] 
    card = cc_gen(cc, mes, ano, cvv) # Llama a la función de generación de CCs
    
    if not card: 
        return bot.reply_to(message, "Error al generar.") 
    
    binsito = binlist(bin_number) # Obtiene info del BIN
    # Formatea las CCs generadas, usando <code> para que se vean como código
    cards_text = "\n".join([f"<code>{c.strip()}</code>" for c in card]) 
    
    # Formato de la respuesta final
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
    
    # 🚨 LÓGICA DE MANTENIMIENTO FORZADO 🚨 (Revisa si el usuario está bloqueado por muchos fallos)
    if userid in BB_MAINTENANCE and current_time < BB_MAINTENANCE[userid]: 
        remaining = int(BB_MAINTENANCE[userid] - current_time) 
        minutes = remaining // 60 
        seconds = remaining % 60 
        return bot.reply_to( 
            message, 
            f"🛠️ Comando /bb en mantenimiento forzado (Max Retries). Por favor, espera {minutes} minutos y {seconds} segundos." 
        ) 
    
    # === LÓGICA DE COOLDOWN (SPAM-LOCK) === (Revisa si ha pasado el tiempo de espera)
    if userid in BB_COOLDOWN: 
        time_elapsed = current_time - BB_COOLDOWN[userid] 
        if time_elapsed < COOLDOWN_TIME: 
            remaining = int(COOLDOWN_TIME - time_elapsed) 
            return bot.reply_to( 
                message, 
                f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /bb." 
            ) 
    
    # 1. Preparar el texto de entrada (puede ser un reply o el texto directo)
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/bb", "").strip() if not message.reply_to_message else raw_text.strip() 
    # Separa los campos de la tarjeta (CC, mes, año, CVV)
    parts = re.split(r"[| \n\t]+", clean) 
    
    if len(parts) < 4: 
        return bot.reply_to( 
            message, 
            "⚠️ Formato inválido.\nEjemplo:\n" 
            "`/bb 4111111111111111|12|2026|123`", 
            parse_mode="Markdown" 
        ) 
    
    cc, mes, ano, cvv = parts[0:4] 
    
    # 2. ENVIAR EL MENSAJE INICIAL Y CAPTURAR SU ID (para editarlo después)
    initial_message = bot.reply_to(message, "⚙️ Chequeando con BB Gateway...") 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    
    try:
        # LLAMADA A TU GATEWAY MODIFICADO (función importada de gateway.py) 
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
            
            # 🚨 GESTIÓN DE ERROR Y MANTENIMIENTO (si el gateway devuelve "Max Retries")
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
        # Manejo de cualquier otro error durante la ejecución del checker
        final_text = f"❌ Error ejecutando BB Gateway:\n{e}"
        print(f"Error en gate_bb: {e}")

    # === ACTUALIZAR EL COOLDOWN (SOLO SI EL CHECK SE EJECUTÓ) === 
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
        # Si falla la edición, envía la respuesta como un mensaje nuevo
        bot.send_message(chat_id=chat_id, text=final_text, parse_mode='HTML') 
        print(f"Error al editar mensaje: {edit_error}") 

def mass_bb(message):
    """Maneja el comando /mass para chequear múltiples tarjetas con el BB Gateway."""
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    current_time = time.time() 
    
    # 🚨 LÓGICA DE MANTENIMIENTO FORZADO (Chequeo compartido con /bb) 🚨 
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
    
    # 1. Extraer el texto de las CCs (del reply o del mensaje directo)
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/mass", "").strip() if not message.reply_to_message else raw_text.strip() 
    
    # Dividir el texto para encontrar las tarjetas (separadas por línea, espacio o barra) 
    cc_lines = re.split(r'[\n\s]+', clean) 
    
    # 2. Parsear y validar las tarjetas
    cards_to_check = [] 
    # Patrón para encontrar tarjetas en formato CC|MM|YYYY|CVV
    cc_pattern = re.compile(r'(\d{12,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})') 
    
    for line in cc_lines: 
        match = cc_pattern.search(line) 
        if match and len(cards_to_check) < 10: # Limita el chequeo masivo a 10 tarjetas 
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
    
    # 3. ENVIAR MENSAJE INICIAL (para luego editarlo y mostrar el progreso)
    initial_message = bot.reply_to( 
        message, 
        f"⚙️ Iniciando chequeo masivo de {total_cards} tarjetas con BB Gateway..." 
    ) 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    results = [] # Lista para guardar los resultados de cada tarjeta
    maintenance_triggered = False # Flag para saber si se activó el mantenimiento
    
    # 4. Procesar cada tarjeta con LIVE EDITING 
    for i, full_cc in enumerate(cards_to_check, 1): 
        cc, mes, ano, cvv = full_cc.split('|') 
        
        # 4.1. Mensaje base de progreso 
        progress_msg_base = f"⚙️ Chequeando Tarjeta {i}/{total_cards}: <code>{full_cc}</code>" 
        
        # 4.2. Intentar editar el mensaje antes del check para mostrar la CC actual 
        try: 
            bot.edit_message_text( 
                chat_id=chat_id, 
                message_id=message_id, 
                # Muestra el progreso y los resultados acumulados
                text=f"{progress_msg_base}\n\n**Resultados Chequeados:**\n{chr(10).join(results)}", 
                parse_mode='HTML' 
            ) 
        except: 
            pass # Ignorar errores de edición si ocurren 
        
        try: 
            # Llama al Gateway para chequear la CC
            status_message = bb_gateway_check(full_cc) 
            
            # Lógica para determinar el status y el mensaje
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
                    maintenance_triggered = True # Activa el flag de mantenimiento
                else: 
                    message_detail = status_message 
            
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
            
            # 4.3. Editar el mensaje con el resultado acumulado de la CC recién chequeada 
            current_result_text = "\n".join(results) 
            progress_text = f"""
            
🔹 CHEQUEO MASIVO BB GATEWAY 🔹
━━━━━━━━━━━━━━━
🌐 PROGRESO: {i}/{total_cards}
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
                # Si falla la edición, ignorar y continuar
                print(f"Error al editar mensaje de progreso: {edit_error}")

            # Si se activa el mantenimiento, salimos del bucle para no seguir chequeando
            if maintenance_triggered: 
                break 
        
        except Exception as e: 
            # Manejo de excepciones durante el chequeo de la CC
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
        # Si la edición final falla, envía uno nuevo como respaldo. 
        bot.send_message(chat_id=chat_id, text=final_text, parse_mode='HTML') 
        print(f"Error al editar mensaje final: {edit_error}") 

# ==============================
# 🆕 NUEVA FUNCIÓN: Comando /ty (SagePay) - ¡CORREGIDA!
# ==============================

def gate_ty(message):
    """Maneja el comando /ty para chequear una tarjeta con la función ccn_gate (SagePay)."""
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    # 1. Preparar el texto de entrada (puede ser un reply o el texto directo)
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/ty", "").strip() if not message.reply_to_message else raw_text.strip() 
    # Separa los campos de la tarjeta (CC, mes, año, CVV)
    parts = re.split(r"[| \n\t]+", clean) 
    
    if len(parts) < 4: 
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
        # ccn_gate devuelve: STATUS|MESSAGE|CODE|
        raw_output = ccn_gate(full_cc_str) # Llama a la función importada
        
        # 3. Parseamos el resultado (CORRECCIÓN CRÍTICA AQUÍ)
        output_parts = raw_output.strip().split('|')

        # Se espera: [STATUS, MESSAGE, CODE, ''] -> 4 partes
        if len(output_parts) >= 3:
            status = output_parts[0].strip()
            message_detail = output_parts[1].strip()
            # code = output_parts[2].strip() # Opcionalmente puedes usar el código

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
            # Fallback si el formato no es el esperado
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
        # Manejo de cualquier otro error durante la ejecución del checker
        final_text = f"❌ Error ejecutando SagePay Gateway:\n{e}"
        print(f"Error en gate_ty: {e}")

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

def cmds(message):
    """Maneja el comando /cmds para mostrar el menú de comandos con botones."""
    # Define la estructura de los botones Inline
    buttons_cmds = [
        [
            types.InlineKeyboardButton('Gateways', callback_data='gates'),
            types.InlineKeyboardButton('Herramientas', callback_data='tools')
        ],
        [types.InlineKeyboardButton('Cerrar', callback_data='close')]
    ]
    markup_buttom = types.InlineKeyboardMarkup(buttons_cmds)
    text = "📋 Lista de comandos"

    # Envía un mensaje con una foto y el menú de botones
    bot.send_photo( 
        chat_id=message.chat.id, 
        photo=IMG_PHOTO1, # Usa el FILE_ID de la foto
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
    # Envía un mensaje con una foto
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO2, caption=text) # Usa el FILE_ID

def deluxe(message):
    """Maneja el comando /deluxe para mostrar términos o información."""
    text = f"""
    ⚠️ Términos ⚠️

    Macros/scripts = ban

    Reembolsos con saldo bineado = ban

    Difamación = ban

    Robo de gates = ban
    """
    # Envía un mensaje con una foto
    bot.send_photo(chat_id=message.chat.id, photo=IMG_PHOTO1, caption=text) # Usa el FILE_ID

# ==============================
# ROUTER DE COMANDOS CON PREFIJOS
# ==============================

# Mapeo de nombres de comandos a sus funciones handler
# ⬆️ AÑADIDO el nuevo comando 'ty'
COMMAND_MAP = {
    'bin': bin_cmd,
    'rnd': rand,
    'gen': gen,
    'bb': gate_bb,
    'mass': mass_bb, # Comando masivo
    'cmds': cmds,
    'start': start,
    'deluxe': deluxe,
    'ty': gate_ty, # <<<<--- NUEVO COMANDO MAPEADO
}

def is_command_with_prefix(message):
    """Verifica si el mensaje comienza con '/', '.', o '&' y tiene un comando válido."""
    if message.text is None:
        return False

    parts = message.text.split() 
    if not parts: 
        return False 
    
    first_word = parts[0].lower() 
    prefixes = ['/'] + CUSTOM_PREFIXES # Lista de prefijos válidos
    
    for prefix in prefixes: 
        if first_word.startswith(prefix): 
            command = first_word[len(prefix):] 
            if '@' in command: 
                command = command.split('@')[0] # Elimina el nombre del bot si está (ej: /bin@BotName)
            return command in ALL_COMMANDS # Verifica si el comando está en la lista de comandos
    
    return False 

# Decorador que usa la función anterior para filtrar mensajes de comandos
@bot.message_handler(func=is_command_with_prefix)
def handle_all_commands(message):
    """Función que dirige el mensaje a la función handler correcta (router)."""
    text_parts = message.text.split()
    command_with_prefix = text_parts[0].lower()

    command_name = "" 
    prefixes = ['/'] + CUSTOM_PREFIXES 
    
    # Extrae el nombre del comando quitando el prefijo
    for prefix in prefixes: 
        if command_with_prefix.startswith(prefix): 
            command_name = command_with_prefix[len(prefix):] 
            if '@' in command_name: 
                command_name = command_name.split('@')[0] 
            break 
    
    if command_name in COMMAND_MAP: 
        # Modifica el mensaje para que el handler interno lo reciba como un comando normal (/comando ...)
        new_text_parts = [f"/{command_name}"] 
        if len(text_parts) > 1: 
            new_text_parts.extend(text_parts[1:]) 
        message.text = " ".join(new_text_parts) 
        COMMAND_MAP[command_name](message) # Llama a la función handler mapeada

# ==============================
# WEBHOOK CONFIG (Ejecución en Railway)
# ==============================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Ruta para recibir las actualizaciones de Telegram (Webhook)."""
    json_str = request.get_data().decode("UTF-8")
    # ✅ CORREGIDO: Se usa .de_json() para parsear el string JSON a un objeto Update
    update = types.Update.de_json(json_str) 
    # Procesa la actualización recibida
    bot.process_new_updates([update])
    return "!", 200 # Respuesta de éxito para Telegram

if __name__ == "__main__":
    """Punto de entrada principal para ejecutar la aplicación."""
    # Obtiene el puerto asignado por Railway (por defecto 5000)
    PORT = int(os.getenv("PORT", 5000))
    # Obtiene la URL de la aplicación en Railway
    APP_URL = os.getenv("APP_URL")

    if not APP_URL: 
        # **⚠️ Este es un error común. Asegúrate de definir APP_URL en tus variables de Railway ⚠️**
        raise ValueError("APP_URL no está definida en Railway Variables") 
        
    # 1. Elimina cualquier Webhook anterior
    bot.remove_webhook() 
    # 2. Configura el nuevo Webhook (Telegram enviará las actualizaciones a esta URL)
    bot.set_webhook(url=f"{APP_URL}/{TOKEN}") 
    # 3. Inicia el servidor Flask para escuchar en el puerto y host definidos
    app.run(host="0.0.0.0", port=PORT)