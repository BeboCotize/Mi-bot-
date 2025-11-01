# Importar módulos necesarios
import os 
import re 
import requests 
import time 
from flask import Flask, request 
from telebot import TeleBot, types 
from cc_gen import cc_gen # Importa la función para generar tarjetas (DEBE existir cc_gen.py)

# ====================================================================================================
# IMPORTACIÓN DEL GATEWAY /gay
# ====================================================================================================
# 📌 Asegúrate de que tu archivo 'gay.py' esté subido y que contenga la función 'check_gay'
from gay import check_gay 
# ====================================================================================================

# ==============================
# CONFIGURACIÓN DEL BOT Y COOLDOWNS
# ==============================

# Obtiene el Token del bot de las variables de entorno de Railway
TOKEN = os.getenv("BOT_TOKEN")
# Inicializa el bot
bot = TeleBot(TOKEN, parse_mode='HTML')

# 📌 ID de usuarios autorizados (solo estos IDs pueden usar los comandos)
USERS = [
    '6116275760', '8470094114']

# 🚨 Cooldown específico para el comando /gay
GAY_COOLDOWN = {}
GAY_COOLDOWN_TIME = 30 # 30 segundos de espera para el comando /gay

# Fotos en Telegram (Usar FILE_ID para máxima estabilidad y velocidad)
# ⚠️ REEMPLAZA ESTOS CON TUS FILE_ID REALES ⚠️
IMG_PHOTO1 = "AgAD0QADlKxIL0z7_cT67p7pAASwzY020A4ABu8k9hFjI_TU_file_id_1_placeholder"
IMG_PHOTO2 = "AgACAgEAAxkBAAE81YRo-UuWDmD16N0u1UZNGYRb3bp9kQACjgtrGy6KyUfGuhk5n4wzYQEAAwIAA3gAAzYE"

# Flask app para configurar el webhook (servidor web)
app = Flask(__name__)

# 📌 Prefijos personalizados que el bot aceptará, además de '/'
CUSTOM_PREFIXES = ['.', '&']

# Lista de todos tus comandos para el router
ALL_COMMANDS = ['bin', 'gen', 'start', 'gay']

# ==============================
# FUNCIONES AUXILIARES
# ==============================

def ver_user(iduser: str) -> bool:
    """Verifica si el ID del usuario está en la lista de USERS autorizados."""
    return iduser in USERS

def binlist(bin: str) -> tuple | bool:
    """Consulta la información de un BIN (primeros 6 dígitos) usando binlist.io."""
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

# ==============================
# HANDLERS (COMANDOS)
# ==============================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    """Maneja el comando /start."""
    bot.reply_to(message, "¡Hola! Soy tu bot de chequeo. Mis comandos disponibles son: /start, /bin, /gen, /gay")


@bot.message_handler(commands=['bin'])
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


@bot.message_handler(commands=['gen'])
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
    
    𝗕𝗜𝗡 𝗜𝗡𝗙𝗢: {binsito[1] if binsito else 'Desconocido'} - {binsito[2] if binsito else ''} - {binsito[3] if binsito else ''}
    𝗖𝗢𝗨𝗡𝗧𝗥𝗬: {binsito[4] if binsito else 'Desconocido'} {binsito[5] if binsito else ''}
    𝗕𝗔𝗡𝗞: {binsito[6] if binsito else 'Desconocido'}
    
    𝗘𝗫𝗧𝗥𝗔: {cc}|{mes}|{ano}|{cvv}
    """
    bot.send_message(chat_id=message.chat.id, text=text, reply_to_message_id=message.id)


@bot.message_handler(commands=['gay'])
def gate_gay(message):
    """Maneja el comando /gay para chequear una tarjeta con tu función check_gay."""
    userid = str(message.from_user.id)
    if not ver_user(userid):
        return bot.reply_to(message, 'No estás autorizado.')

    current_time = time.time() 
    
    # === LÓGICA DE COOLDOWN (SPAM-LOCK) ===
    if userid in GAY_COOLDOWN: 
        time_elapsed = current_time - GAY_COOLDOWN[userid] 
        if time_elapsed < GAY_COOLDOWN_TIME: 
            remaining = int(GAY_COOLDOWN_TIME - time_elapsed) 
            return bot.reply_to( 
                message, 
                f"🚫 ¡Alto ahí! Debes esperar {remaining} segundos antes de volver a usar /gay." 
            ) 
    
    # 1. Preparar el texto de entrada
    raw_text = message.reply_to_message.text if message.reply_to_message else message.text 
    clean = raw_text.replace("/gay", "").strip() if not message.reply_to_message else raw_text.strip() 
    parts = re.split(r"[| \n\t]+", clean) 
    
    if len(parts) < 4: 
        GAY_COOLDOWN[userid] = time.time()
        return bot.reply_to( 
            message, 
            "⚠️ Formato inválido.\nEjemplo:\n" 
            "`/gay 4111111111111111|12|2026|123`", 
            parse_mode="Markdown" 
        ) 
    
    cc, mes, ano, cvv = parts[0:4] 
    full_cc = f"{cc}|{mes}|{ano}|{cvv}"
    
    # 2. ENVIAR EL MENSAJE INICIAL Y CAPTURAR SU ID
    initial_message = bot.reply_to(message, "⚙️ Chequeando con GAY Gateway...") 
    chat_id = initial_message.chat.id 
    message_id = initial_message.message_id 
    
    try:
        # LLAMADA A LA FUNCIÓN DE GAY.PY
        status_message = check_gay(full_cc)
        
        # 3. Parseamos el resultado (ADAPTA ESTA LÓGICA SI TU FUNCIÓN DEVUELVE OTRA COSA)
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
        
        # 4. Obtenemos información adicional para el formato
        bin_number = cc[0:6] 
        binsito = binlist(bin_number) 
        
        # 5. Creamos el mensaje final
        final_text = f"""
        
        {emoji} CARD --> {full_cc}
        {emoji} STATUS --> {status} {emoji}
        {emoji} MESSAGE --> {message_detail}
        [GATEWAY] [GAY Gateway]
        
        [BIN INFO]
        {emoji} BIN --> {binsito[1] if binsito else 'Desconocido'} {binsito[2] if binsito else ''}
        {emoji} BANK --> {binsito[6] if binsito else 'Desconocido'}
        {emoji} COUNTRY --> {binsito[4] if binsito else 'Desconocido'} {binsito[5] if binsito else ''}
        """
    except Exception as e:
        final_text = f"❌ Error ejecutando GAY Gateway:\n{e}"
        print(f"Error en gate_gay: {e}")

    # === ACTUALIZAR EL COOLDOWN === 
    GAY_COOLDOWN[userid] = time.time() 
    
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

# ==============================
# CONFIGURACIÓN DEL WEBHOOK Y ROUTING
# ==============================

# Manejador genérico para comandos con prefijos personalizados ('.', '&')
@bot.message_handler(func=lambda message: any(message.text.startswith(prefix) for prefix in CUSTOM_PREFIXES))
def handle_custom_prefix_commands(message):
    text = message.text[1:]  # Elimina el prefijo
    parts = text.split()
    if not parts:
        return
    
    command = parts[0]
    
    # Crea un objeto mensaje temporal para simular un comando /
    new_message = message
    new_message.text = f'/{command} {" ".join(parts[1:])}'
    
    # Llama a la función de manejo correspondiente
    if command == 'bin':
        bin_cmd(new_message)
    elif command == 'gen':
        gen(new_message)
    elif command == 'gay':
        gate_gay(new_message)


# 📌 Webhook: Recibe el tráfico POST de Telegram
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    """Recibe las actualizaciones del Webhook de Telegram."""
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# 📌 La ruta raíz es la que ejecutará el Webhook
@app.route("/", methods=['GET'])
def index():
    """Ruta de inicio para Railway."""
    return "Bot is running.", 200

# ===================================================================================
# 🔑 BLOQUE DE ARRANQUE CRÍTICO PARA RAILWAY (Tu adición)
# ===================================================================================

if __name__ == "__main__":
    """Punto de entrada principal para ejecutar la aplicación."""
    # Railway provee la variable PORT que es necesaria para Flask
    PORT = int(os.getenv("PORT", 5000)) 
    # APP_URL debe ser configurada en las variables de Railway (ej: RAILWAY_STATIC_URL)
    APP_URL = os.getenv("APP_URL") # Asegúrate de que esta variable exista en Railway

    if not APP_URL:
        # Esto asegura que si no hay URL, el programa no continúe y el error sea visible
        raise ValueError("APP_URL no está definida en Railway Variables. Es necesaria para el Webhook.")

    # 1. Quitar cualquier Webhook anterior
    bot.remove_webhook()
    
    # 2. Configurar el nuevo Webhook (la URL completa a la que Telegram enviará las actualizaciones)
    webhook_url = f"{APP_URL}/{TOKEN}"
    bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook configurado en: {webhook_url}")

    # 3. Iniciar el servidor Flask
    app.run(host="0.0.0.0", port=PORT)
