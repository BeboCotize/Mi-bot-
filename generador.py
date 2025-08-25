import random

def luhn_checksum(card_number: str) -> int:
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def calculate_luhn(card_number: str) -> str:
    check_digit = luhn_checksum(card_number + "0")
    return card_number + str((10 - check_digit) % 10)

def generate_card(pattern: str, month=None, year=None, cvv_random=True):
    # Reemplazar x y rnd
    base = ""
    for c in pattern:
        if c.lower() == "x":
            base += str(random.randint(0,9))
        elif c.lower() == "r":
            base += str(random.randint(0,9))
        elif c.isdigit():
            base += c
        else:
            continue
    
    # Luhn
    card = calculate_luhn(base[:-1])
    
    mm = month if month else str(random.randint(1,12)).zfill(2)
    yy = year if year else str(random.randint(2025,2030))
    cvv = str(random.randint(100,999)) if cvv_random else "000"
    
    return f"{card}|{mm}|{yy}|{cvv}"