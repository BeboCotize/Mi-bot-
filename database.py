import sqlite3
import datetime

DB_NAME = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabla de usuarios
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        has_key INTEGER DEFAULT 0,
        expire_date TEXT
    )
    """)
    # Tabla de keys
    c.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        expire_date TEXT,
        used INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def add_key(key, expire_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, expire_date) VALUES (?,?)", (key, expire_date))
    conn.commit()
    conn.close()

def use_key(key, user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT expire_date, used FROM keys WHERE key = ?", (key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "❌ La key no existe."
    expire_date, used = row
    if used == 1:
        conn.close()
        return False, "❌ La key ya fue usada."
    # Marcar como usada
    c.execute("UPDATE keys SET used = 1 WHERE key = ?", (key,))
    # Registrar usuario autorizado
    c.execute("INSERT OR REPLACE INTO users (user_id, has_key, expire_date) VALUES (?,?,?)", 
              (user_id, 1, expire_date))
    conn.commit()
    conn.close()
    return True, f"✅ Key reclamada! Expira el {expire_date}"

def check_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT has_key, expire_date FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    has_key, expire_date = row
    if has_key == 1:
        if datetime.datetime.strptime(expire_date, "%Y-%m-%d") >= datetime.datetime.now():
            return True
    return False

# Alias para que tu código se lea igual
def ver_user(user_id):
    return check_user(user_id)