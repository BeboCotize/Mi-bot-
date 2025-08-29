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


def claim_key(user_id: int, username: str, key: str):
    keys = load_keys()
    users = load_users()

    if key not in keys:
        return False, "❌ Key inválida."
    if keys[key]["usado"]:
        return False, "❌ Esta key ya fue reclamada."
    
    expira = datetime.datetime.fromisoformat(keys[key]["expira"])
    if expira < datetime.datetime.now():
        return False, "❌ Esta key ya expiró."

    # 🔹 Aseguramos que el user_id sea string (para JSON)
    user_id_str = str(user_id)

    # Guardamos al usuario
    users[user_id_str] = {
        "username": username,
        "key": key,
        "expires": keys[key]["expira"]
    }
    save_users(users)

    # Marcamos la key como usada
    keys[key]["usado"] = True
    save_keys(keys)

    return True, f"✅ Key válida.\nExpira: {expira.strftime('%Y-%m-%d %H:%M:%S')}"