import json
import random
import string
from datetime import datetime, timedelta

KEYS_FILE = "keys.json"
USERS_FILE = "users.json"

# =============================
#   KEYS STORAGE HELPERS
# =============================
def load_keys():
    try:
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# =============================
#   KEY FUNCTIONS
# =============================

def generate_key(days_valid=1):
    """Genera una nueva key con fecha de expiración"""
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    keys = load_keys()
    expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
    
    keys[key] = {
        "expires": expires_at,
        "claimed_by": None
    }
    save_keys(keys)
    return key, expires_at

def claim_key(user_id, username, key):
    """Permite a un usuario reclamar una key"""
    keys = load_keys()
    users = load_users()

    if key not in keys:
        return False, "❌ Key inválida."

    if keys[key]["claimed_by"] is not None:
        return False, "❌ Esta key ya fue reclamada."

    expira_dt = datetime.fromisoformat(keys[key]["expires"])
    if expira_dt < datetime.now():
        return False, "❌ Esta key ya expiró."

    # Guardar al usuario como dueño de la key
    keys[key]["claimed_by"] = user_id
    users[user_id] = {
        "username": username,
        "key": key,
        "expires": keys[key]["expires"]
    }

    save_keys(keys)
    save_users(users)
    return True, f"✅ Key reclamada correctamente. Expira el {keys[key]['expires']}"

def list_keys():
    """Devuelve todas las keys con su estado"""
    keys = load_keys()
    result = []
    for k, data in keys.items():
        claimed = data["claimed_by"]
        expires = data["expires"]
        status = "✅ Disponible" if claimed is None else f"👤 Reclamada por {claimed}"
        result.append(f"{k} | {expires} | {status}")
    return result