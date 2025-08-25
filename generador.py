import random
from telegram import Update
from telegram.ext import ContextTypes

def luhn_checksum(card_number: str) -> int:
    """Calcula el dígito de control usando algoritmo de Luhn"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d*2))
    return checksum % 10

def completar_luhn(card_number: str) -> str:
    """Genera el último dígito válido para que el número pase Luhn"""
    for i in range(10):
        posible = card_number + str(i)
        if luhn_checksum(posible) == 0:
            return posible
    return card_number + "0"  # fallback

def generar_tarjeta(bin_pattern: str) -> str:
    """Genera una tarjeta a partir de un patrón con X, usando Luhn"""
    partes = bin_pattern.split("|")

    bin_code = partes[0]
    mes = partes[1] if len(partes) > 1 and partes[1] else str(random.randint(1, 12)).zfill(2)
    year = partes[2] if len(partes) > 2 and partes[2] else str(random.randint(2025, 2030))
    cvv = partes[3] if len(partes) > 3 else "rnd"

    # Reemplazar X por dígitos aleatorios excepto el último
    parcial = ""
    for c in bin_code:
        if c.lower() == "x":
            parcial += str(random.randint(0, 9))
        else:
            parcial += c

    # Si la longitud es <16, completamos con dígito Luhn
    if len(parcial) < 15:
        parcial = parcial.ljust(15, "0")  # rellena con 0 hasta tener 15
    numero_final = completar_luhn(parcial[:15])  # genera número válido de 16 dígitos

    # Generar CVV si es rnd
    if cvv.lower() == "rnd":
        cvv = str(random.randint(100, 999))

    return f"{numero_final}|{mes}|{year}|{cvv}"

async def generar_cc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usa el comando con un patrón válido.\n\nEjemplo:\n`.gen 402347070930xxxx|04|2028|rnd`")
        return

    bin_pattern = context.args[0]
    tarjetas = [generar_tarjeta(bin_pattern) for _