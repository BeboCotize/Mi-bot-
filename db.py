import json
import os

USERS_FILE = "data/users.json"
KEYS_FILE = "data/keys.json"

# 🔹 Helpers
def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# 🔹 Usuarios
def registrar_usuario(user_id, username):
    users = load_json(USERS_FILE)
    users[str(user_id)] = {"username": username, "registrado": False, "admin": False, "baneado": False}
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

# 🔹 Keys
def add_key(key, expires):
    keys = load_json(KEYS_FILE)
    keys[key] = {"expires": expires}
    save_json(KEYS_FILE, keys)