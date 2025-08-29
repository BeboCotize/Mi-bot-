import random
import string
from datetime import datetime, timedelta
import json
import os

KEYS_FILE = "keys.json"
USERS_FILE = "users.json"

# =============================
#   UTILIDADES
# =============================
def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_keys(keys):
    with open(KEYS_FILE, "w") as f:
        json.dump(keys, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# =============================
#   GENERAR KEY
# =============================
def generate_key(dias):
    keys = load_keys()

    # Generar key con prefijo Demon + 4 números + 1 letra aleatoria
    numeros = str(random.randint(1000, 9999))
    letra = random.choice(string.ascii_lowercase)
    key = f"Demon{numeros}{letra}"

    expires = (datetime.now() + timedelta(days=int(dias))).isoformat()

    keys[key] = {
        "expires": expires,
        "claimed": False,
        "claimed_by": None
    }
    save_keys(keys)

    return f"✅ Key generada: `{key}`\n⏳ Expira el: {expires}"

# =============================
#   CLAIM KEY
# =============================
def claim_key(user_id, username, key):
    keys = load_keys()
    users = load_users()
    user_id = str(user_id)

    if key not in keys:
        return "❌ Esa key no existe."

    if keys[key]["claimed"]:
        return "❌ Esa key ya fue reclamada."

    # Marcar como reclamada
    keys[key]["claimed"] = True
    keys[key]["claimed_by"] = user_id

    # Guardar usuario con su key
    users[user_id] = {
        "username": username,
        "key": key,
        "expires": keys[key]["expires"]
    }

    save_keys(keys)
    save_users(users)

    return f"🎉 Felicidades @{username}, reclamaste la key: `{key}`"

# =============================
#   LIST KEYS
# =============================
def list_keys():
    keys = load_keys()
    if not keys:
        return "📭 No hay keys generadas."

    msg = "🔑 *Listado de Keys:*\n\n"
    for k, v in keys.items():
        estado = "✅ Libre" if not v["claimed"] else f"❌ Reclamada por {v['claimed_by']}"
        msg += f"- `{k}` | Expira: {v['expires']} | {estado}\n"
    return msg

# =============================
#   MYINFO
# =============================
def myinfo(user_id):
    users = load_users()
    user_id = str(user_id)

    if user_id not in users:
        return "❌ No has reclamado ninguna key todavía."

    data = users[user_id]
    username = data["username"]
    key = data["key"]
    expires = data["expires"]

    try:
        expira_dt = datetime.fromisoformat(expires)
        expira_str = expira_dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        expira_dt = None
        expira_str = expires

    if expira_dt and expira_dt < datetime.now():
        return (
            f"👤 Usuario: @{username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expiró el: {expira_str}\n\n"
            f"⚠️ Tu key ha expirado, reclama una nueva."
        )
    else:
        return (
            f"👤 Usuario: @{username}\n"
            f"🔑 Key: {key}\n"
            f"⏳ Expira: {expira_str}\n\n"
            f"✅ Tu key sigue activa."
        )