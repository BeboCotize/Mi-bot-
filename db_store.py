
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            registered_at TEXT,
            has_key INTEGER DEFAULT 0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            user_id INTEGER,
            expires_at TEXT,
            created_at TEXT,
            days INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS spam (
            user_id INTEGER PRIMARY KEY,
            last_action_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

# Registro de usuario
def registro_usuario(user_id: int, username: str):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, registered_at, has_key) VALUES (?, ?, ?, ?)",
              (user_id, username, now, 0))
    c.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
    conn.commit()
    conn.close()

def usuario_registrado(user_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    r = c.fetchone() is not None
    conn.close()
    return r

def usuario_tiene_key(user_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT has_key FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return bool(row[0]) if row else False

def asignar_key_a_usuario(user_id: int, key: str, days: int):
    conn = get_conn()
    c = conn.cursor()
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()
    created_at = datetime.utcnow().isoformat()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    c.execute("UPDATE users SET has_key=1 WHERE user_id=?", (user_id,))
    c.execute("INSERT OR REPLACE INTO keys (key, user_id, expires_at, created_at, days) VALUES (?, ?, ?, ?, ?)",
              (key, user_id, expires_at, created_at, days))
    conn.commit()
    conn.close()
    return expires_at

def get_user_keys(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT key, expires_at, days FROM keys WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"key": r[0], "expires_at": r[1], "days": r[2]} for r in rows]

def key_expirates(key: str) -> datetime | None:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT expires_at FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return datetime.fromisoformat(row[0])

def registrar_uso_spam(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("INSERT OR REPLACE INTO spam (user_id, last_action_at) VALUES (?, ?)", (user_id, now))
    conn.commit()
    conn.close()

def ultimo_tiempo_spam(user_id: int) -> datetime | None:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT last_action_at FROM spam WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row or not row[0]:
        return None
    return datetime.fromisoformat(row[0])

def limpiar_expiradas():
    conn = get_conn()
    c = conn.cursor()
    now = datetime.utcnow().isoformat()
    c.execute("DELETE FROM keys WHERE expires_at <= ?", (now,))
    c.execute("UPDATE users SET has_key = 0 WHERE user_id IN (SELECT user_id FROM keys WHERE expires_at <= ?)", (now,))
    conn.commit()
    conn.close()
