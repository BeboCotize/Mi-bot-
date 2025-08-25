import random

def luhn_complete(number: str) -> str:
    digits = [int(d) for d in number]
    for i in range(len(digits)-1, -1, -2):
        d = digits[i] * 2
        if d > 9:
            d -= 9
        digits[i] = d
    total = sum(digits)
    return str((10 - (total % 10)) % 10)

def generate_card(bin_pattern: str, amount: int = 10):
    cards = []
    for _ in range(amount):
        parts = bin_pattern.split("|")
        bin_base = parts[0]

        # Completar X con random
        while "x" in bin_base:
            bin_base = bin_base.replace("x", str(random.randint(0, 9)), 1)

        # Luhn
        check_digit = luhn_complete(bin_base[:-1])
        card_number = bin_base[:-1] + check_digit if len(bin_base) == 16 else bin_base

        # Fecha
        if len(parts) > 1 and parts[1]:
            month = parts[1]
        else:
            month = f"{random.randint(1,12):02d}"

        if len(parts) > 2 and parts[2]:
            year = parts[2]
        else:
            year = str(random.randint(2024, 2029))

        # CVV
        cvv = str(random.randint(100, 999))

        cards.append(f"{card_number}|{month}|{year}|{cvv}")
    return cards