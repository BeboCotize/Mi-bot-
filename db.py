# db.py
import datetime

# Simulamos la base de datos con un diccionario
users = {}       # user_id: {"registered": True/False, "banned": True/False, "admin": True/False, "key_expiry": datetime}
keys = {}        # key: {"days": X, "used": False}


# ---------- USUARIOS ----------
def add_user(user_id):
    """Registrar un usuario nuevo"""
    if user_id not in users:
        users[user_id] = {
            "registered": False,
            "banned": False,
            "admin": False,
            "key_expiry": None
        }

def is_user_registered(user_id):
    """Verifica si el usuario está registrado con key"""
    return users.get(user_id, {}).get("registered", False)

def set_registered(user_id, days):
    """Activa la cuenta del usuario con días de validez"""
    if user_id in users:
        users[user_id]["registered"] = True
        users[user_id]["key_expiry"] = datetime.datetime.now() + datetime.timedelta(days=days)


# ---------- BANEOS ----------
def ban_user(user_id):
    """Banea al usuario"""
    if user_id in users:
        users[user_id]["banned"] = True

def unban_user(user_id):
    """Desbanea al usuario"""
    if user_id in users:
        users[user_id]["banned"] = False

def is_banned(user_id):
    """Revisa si el usuario está baneado"""
    return users.get(user_id, {}).get("banned", False)


# ---------- ADMINS ----------
def add_admin(user_id):
    """Convierte a un usuario en admin"""
    if user_id in users:
        users[user_id]["admin"] = True

def is_admin(user_id):
    """Verifica si el usuario es admin"""
    return users.get(user_id, {}).get("admin", False)


# ---------- KEYS ----------
def generate_key(key, days):
    """Genera una key válida por X días"""
    keys[key] = {"days": days, "used": False}

def redeem_key(user_id, key):
    """Canjea una key y activa al usuario"""
    if key in keys and not keys[key]["used"]:
        days = keys[key]["days"]
        set_registered(user_id, days)
        keys[key]["used"] = True
        return True
    return False