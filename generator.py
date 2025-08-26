import random
import pytz
import datetime
import re

# --- Algoritmo Luhn ---
def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = 0
    checksum += sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10

def is_luhn_valid(card_number) -> bool:
    return luhn_checksum(card_number) == 0


# --- Generador de tarjetas ---
def cc_gen(cc, mes='xx', ano='xxxx', cvv='rnd'):
    ccs = []
    while len(ccs) < 10:  # Genera 10 tarjetas por defecto
        card = str(cc)

        # Rellena los 'x' con dígitos aleatorios
        list_emty = []
        for i in card:
            if i == 'x':
                list_emty.append(str(random.randint(0, 9)))
            else:
                list_emty.append(i)
        card = ''.join(list_emty)

        # Longitud según tipo de tarjeta
        if card[0] == '3':
            card = card[:15]
        else:
            card = card[:16]

        # Generar mes
        if mes in ['xx', 'rnd']:
            mes_gen = random.randint(1, 12)
            mes_gen = f"{mes_gen:02d}"
        else:
            if int(mes) > 12:
                return []
            mes_gen = mes

        # Generar año
        if ano in ['rnd', 'xxxx']:
            ano_gen = random.randint(2023, 2040)
        else:
            ano_gen = int(ano)
            if len(str(ano_gen)) == 2:
                ano_gen = int("20" + str(ano_gen))

        # Generar CVV
        if cvv in ['rnd', 'xxx', 'xxxx']:
            cvv_gen = random.randint(1000, 9999) if card[0] == '3' else random.randint(100, 999)
        else:
            cvv = re.findall(r"[0-9]+", cvv)[0]
            if card[0] == '3':
                cvv_gen = cvv[:4].zfill(4)
            else:
                cvv_gen = cvv[:3].zfill(3)

        # Validación con Luhn
        if is_luhn_valid(card):
            IST = pytz.timezone('US/Central')
            now = datetime.datetime.now(IST)

            if datetime.datetime.strptime(
                now.strftime("%m-%Y"), "%m-%Y"
            ) <= datetime.datetime.strptime(f"{mes_gen}-{ano_gen}", "%m-%Y"):
                x = f"{card}|{mes_gen}|{ano_gen}|{cvv_gen}"
                ccs.append(x)

    return ccs