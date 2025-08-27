import sqlite3
import datetime
import uuid

DB_FILE = "database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, expira TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, expira TEXT, usado INTEGER)")
    conn.commit()
    conn.close()

def ver_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT expira FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row: return False
    expira = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now() <= expira

def claim_key(user_id, key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT expira, usado FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False, "❌ Key inválida"
    expira, usado = row
    if usado == 1:
        conn.close()
        return False, "❌ Esta key ya fue usada"
    # Guardar user
    c.execute("INSERT OR REPLACE INTO users (user_id, expira) VALUES (?,?)", (str(user_id), expira))
    c.execute("UPDATE keys SET usado=1 WHERE key=?", (key,))
    conn.commit()
    conn.close()
    return True, f"✅ Key aceptada, expira el {expira}"

def create_key(dias):
    expira = (datetime.datetime.now() + datetime.timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
    key = str(uuid.uuid4())[:8]
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO keys (key, expira, usado) VALUES (?,?,0)", (key, expira))
    conn.commit()
    conn.close()
    return key

def is_admin(user_id):
    # 🚨 pon tu propio ID de admin aquí
    return str(user_id) in ["123456789"]