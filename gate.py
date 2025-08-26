import random
from faker import Faker
from random import choice
from curl_cffi import requests
from colorama import init, Fore
from fake_useragent import UserAgent
import time

def usuario() -> dict:
    number = random.randint(1111, 9999)
    postal = random.choice(['10080', '14925', '71601', '86556', '19980'])
    return {
        'name' : Faker().name(),
        'email' : Faker().email().replace('@', '{}@'.format(number)),
        'username' : Faker().user_name(),
        'phone' : '512678{}'.format(number),
        'city' : Faker().city(),
        'code' : postal
    }

def capture(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]
    except ValueError:  
        return None

def get_bin_info(bin_number):
    try:
        res = requests.get(f"https://binlist.io/lookup/{bin_number}")
        if res.status_code == 200:
            data = res.json()
            return {
                "bin": data.get("scheme", "N/A").upper() + " " + data.get("type", "").upper(),
                "bank": data.get("bank", {}).get("name", "Unknown"),
                "country": f"{data.get('country', {}).get('name', 'Unknown')} {data.get('country', {}).get('emoji', '')}"
            }
    except Exception as e:
        print("BIN error:", e)
    return {"bin": "N/A", "bank": "N/A", "country": "N/A"}

def ccn_gate(card):
    max_retries = 10
    retry_count = 0
    start_time = time.time()

    while retry_count < max_retries:
        try:
            init(autoreset=True)
            cliente = requests.Session(impersonate=choice(["chrome124", "chrome123", "safari17_0", "safari17_2_ios", "safari15_3"]))
            cc_number, mes, ano_number, cvv = card.split('|')
            if len(ano_number) == 4: 
                ano_number = ano_number[2:4]
            agente_user = UserAgent().random

            #============[Fake user info]============#
            name  = usuario()['name'].split(' ')[0]  
            last  = usuario()['name'].split(' ')[1]  
            number = random.randint(1111, 9999)  
            street = f"{name}+street+{number}"  
            email = usuario()['email']  
            phone = usuario()['phone']  

            #============[Request simulation]============#
            # ... Aquí van tus requests reales como ya lo tienes en tu gate ...

            # Para demo, inventamos un response simulado
            result_json = {
                "paymentresponse": '{"message":"CVV2 MISMATCH","code":"0000N7"}'
            }

            message_text = capture(result_json['paymentresponse'], '"message":"', '"')  
            message_code = capture(result_json['paymentresponse'], '"code":"', '"')  

            elapsed = round(time.time() - start_time, 2)

            # Obtener BIN info
            bin_info = get_bin_info(cc_number[:6])

            #=========== JSON RESPONSE ===========#
            return {
                "card": card,
                "status": "APPROVED" if "approved" in (message_text or "").lower() or "CVV2 MISMATCH" in (message_text or "") else "DECLINED",
                "message": message_text,
                "code": message_code,
                "bin": bin_info["bin"],
                "bank": bin_info["bank"],
                "country": bin_info["country"],
                "time": f"{elapsed} Segs",
                "retries": retry_count + 1
            }

        except Exception as e:  
            print(e)  
            retry_count += 1  
    else:  
        return {"card": card, "status": "ERROR", "resp":  f"Retries: {retry_count}"}

if __name__ == "__main__":
    file = open('cards.txt', 'r')
    lines = file.readlines()
    for position, x in enumerate(lines):
        cc, mes, ano, cvv = x.split("|")
        gateway = ccn_gate(f"{cc}|{mes}|{ano}|{cvv.strip()}")
        print(gateway)  # <-- imprime JSON con BIN info
        with open('cards.txt', "w")as f:
            f.writelines(lines[position+1:])
            f.close()