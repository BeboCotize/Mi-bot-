import random
import pytz
import datetime
import re


# --- Algoritmo de Luhn ---
def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10


def is_luhn_valid(card_number) -> bool:
    return luhn_checksum(card_number) == 0


# --- Generador de tarjetas ---
def cc_gen(cc, mes="xx", ano="xxxx", cvv="rnd"):
    ccs = []
    while len(ccs) < 10:  # Genera 10 por defecto
        card = str(cc)
        digits = "0123456789"
        list_digits = list(digits)
        random.shuffle(list_digits)
        string_digits = "".join(list_digits)
        card = card + string_digits
        new_list = list(card)
        list_emty = []

        for i in new_list:
            if i == "x":
                list_emty.append(str(random.randint(0, 9)))
            else:
                list_emty.append(i)

        card = "".join(list_emty)

        # VISA/MC/Amex length fix
        if card[0] == "3":
            card = card[:15]
        else:
            card = card[:16]

        # --- Mes ---
        if mes in ["xx", "rnd"]:
            mes_gen = random.randint(1, 12)
            mes_gen = f"{mes_gen:02d}"
        else:
            if int(mes) > 12:
                return False
            mes_gen = mes

        # --- Año ---
        if ano in ["rnd", "xxxx"]:
            ano_gen = random.randint(2023, 2040)
        else:
            ano_gen = ano
            if len(str(ano_gen)) == 2:
                ano_gen = "20" + str(ano_gen)

        # --- CVV ---
        if cvv in ["rnd", "xxx", "xxxx"]:
            cvv_gen = random.randint(1000, 9999) if card[0] == "3" else random.randint(100, 999)
        else:
            cvv = re.findall(r"[0-9]+", cvv)[0]
            if card[0] in ["4", "5", "6"]:
                cvv_gen = cvv if len(cvv) >= 3 else (cvv + str(random.randint(100, 999)))[:3]
            elif card[0] == "3":
                cvv_gen = cvv if len(cvv) >= 4 else (cvv + str(random.randint(1000, 9999)))[:4]
            else:
                cvv_gen = cvv

        # --- Validación con Luhn ---
        if is_luhn_valid(card):
            IST = pytz.timezone("US/Central")
            now = datetime.datetime.now(IST)
            max_reintentos = 10
            intentos = 0

            while intentos < max_reintentos:
                intentos += 1
                if datetime.datetime.strptime(now.strftime("%m-%Y"), "%m-%Y") <= datetime.datetime.strptime(
                    f"{mes_gen}-{ano_gen}", "%m-%Y"
                ):
                    x = f"{card}|{mes_gen}|{ano_gen}|{cvv_gen}\n"
                    ccs.append(x)
                    break
        else:
            continue

    return ccs