import json
import os
import datetime
import random
import string
from datetime import timedelta

KEYS_FILE = "keys.json"
USERS_FILE = "users.json"


def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        return json.load(f)


def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def load_keys():
    return load_json(KEYS_FILE)


def save_keys(keys):
    save_json(KEYS_FILE, keys)


def load_users():
    return load_json(USERS_FILE)


def save_users(users):
    save_json(USERS_FILE, users)


def generate_key(nombre: str, dias: int):
    keys = load_keys()
    key = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    expira = datetime.datetime.now() + timedelta(days=dias)

    keys[key] = {
        "nombre": nombre,
        "expires": expira.isoformat(),
        "claimed": False,
        "claimed_by": None
    }
    save_keys(keys)

    return key, expira


def claim_key(user_id: str, username: str, key: str):
    keys = load_keys()
    users = load_users()

    if key not in keys:
        return False, "🚫 Key inválida."

    expira = datetime.datetime.fromisoformat(keys[key]["expires"])
    if expira < datetime.datetime.now():
        return False, "🚫 Esa key ya expiró."

    if keys[key].get("claimed", False):
        return False, "🚫 Esa key ya fue usada."

    # ✅ asignamos al usuario
    users[user_id] = {
        "username": username,
        "key": key,
        "expires": keys[key]["expires"]
    }
    save_users(users)

    # ✅ marcamos como usada
    keys[key]["claimed"] = True
    keys[key]["claimed_by"] = username
    save_keys(keys)

    return True, f"✅ Key aceptada {username}, ya puedes usar /gen y /sg."


def list_keys():
    keys = load_keys()
    now = datetime.datetime.now()

    lista = []
    for k, v in keys.items():
        expira = datetime.datetime.fromisoformat(v["expires"])
        estado = "✅ Activa"
        if v.get("claimed", False):
            estado = f"⚠️ Usada por {v.get('claimed_by', 'Desconocido')}"
        elif expira < now:
            estado = "❌ Expirada"

        lista.append(
            f"`{k}` - {v['nombre']} - expira {expira.strftime('%Y-%m-%d')} - {estado}"
        )

    if not lista:
        return "No hay keys registradas."
    return "\n".join(lista)
