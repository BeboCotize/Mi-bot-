import random
import requests

def luhn_checksum(card_number: str) -> int:
    """Devuelve el dígito de control usando el algoritmo Luhn"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(digits_of(d*2))
    return total % 10

def completar_luhn(base: str) -> str:
    """Completa la tarjeta con dígito válido"""
    checksum = luhn_checksum(base + "0")
    return base + str((10 - checksum) % 10)

def generar_cc(bin_format: str, cantidad: int = 10) -> list:
    """Genera tarjetas ficticias basadas en un BIN con formato"""
    tarjetas = []
    for _ in range(cantidad):
        tarjeta = ""
        for c in bin_format:
            if c == "x":
                tarjeta += str(random.randint(0, 9))
            else:
                tarjeta += c
        tarjeta = completar_luhn(tarjeta[:-1]) if "x" not in tarjeta else completar_luhn(tarjeta)
        tarjetas.append(tarjeta)
    return tarjetas

def bin_info(bin_number: str) -> dict:
    """Consulta información básica del BIN (ejemplo educativo)"""
    try:
        r = requests.get(f"https://lookup.binlist.net/{bin_number}")
        if r.status_code == 200:
            data = r.json()
            return {
                "pais": data.get("country", {}).get("name", "N/A"),
                "esquema": data.get("scheme", "N/A"),
                "tipo": data.get("type", "N/A"),
                "clase": data.get("brand", "N/A"),
                "moneda": data.get("country", {}).get("currency", "N/A"),
            }
    except:
        return {}
    return {}