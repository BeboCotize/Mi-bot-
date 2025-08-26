import json
import os
from datetime import datetime

# Rutas de los archivos
USERS_FILE = "data/users.json"
KEYS_FILE = "data/keys.json"

# Asegurar que la carpeta data existe
os.makedirs("data", exist_ok=True)

# --- Funciones auxiliares ---
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# --- Usuarios ---
def registrar_usuario(user_id, username):
    users = load_json(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "registrado": False,
            "admin": False,
            "baneado": False
        }
        save_json(USERS_FILE, users)

def marcar_registrado(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["registrado"] = True
        save_json(USERS_FILE, users)

def ban_user(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["baneado"] = True
        save_json(USERS_FILE, users)

def unban_user(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["baneado"] = False
        save_json(USERS_FILE, users)

def set_admin(user_id):
    users = load_json(USERS_FILE)
    if str(user_id) in users:
        users[str(user_id)]["admin"] = True
        save_json(USERS_FILE, users)


# --- Keys ---
def add_key(key, expires):
    keys = load_json(KEYS_FILE)
    keys[key] = {"expires": expires.isoformat()}
    save_json(KEYS_FILE, keys)

def is_key_valid(key):
    keys = load_json(KEYS_FILE)
    if key not in keys:
        return False
    expires = datetime.fromisoformat(keys[key]["expires"])
    return datetime.now() < expires