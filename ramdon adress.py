import requests
import telebot





#API_ID = 21059313
#API_HASH = '281c2a2d8ccb7ee10f1374da03a566fe'
#token = "6149738734:AAFCvrBqYyoVuvA3RgUSMjcQIaE7BCIuhvs"



#bot = telebot(token, parse_mode="html")





url = "https://random-data-api.com/api/v2/users"
peticion = requests.get(url)

#print(peticion.json())




nombre1 = peticion.json()['first_name']
nombr2 = peticion.json()['last_name']
numerosd = peticion.json()['phone_number']
adresciyu = peticion.json()['address']['city']
nombre_calle = peticion.json()['address']['street_name']
direcion_calle = peticion.json()['address']['street_address']
cidogoPostal = peticion.json()['address']['zip_code']
Stado= peticion.json()['address']['state']
country = peticion.json()['address']['country']




#print(nombre1,nombr2,numerosd,adresciyu)


print("═══════random adress═════════ ")

print("nombre:",nombre1)
print("apellido:",{nombr2})
print("numero de telefono:",numerosd)
print("ciuda:",adresciyu)
print("nombre calle:",nombre_calle)
print("direcion:",direcion_calle)
print("codigo postal:",cidogoPostal)
print("estado:",Stado)
print("country:",country)

print("════════════════════════════")




