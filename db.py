import sqlite3
from datetime import datetime, timedelta
import secrets

DB_NAME = "db.sqlite"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        expire_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        expire_at TIMESTAMP,
        used INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

# --------------------------
# Funciones de keys
# --------------------------

def create_key(days: int) -> str:
    key = secrets.token_hex(8)  # genera key aleatoria
    expire_at = datetime.now() + timedelta(days=days)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keys (key, expire_at) VALUES (?, ?)", (key, expire_at))
    conn.commit()
    conn.close()

    return key

def redeem_key(user_id: int, username: str, key: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT key, expire_at, used FROM keys WHERE key = ?", (key,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False  # key no existe

    if row[2] == 1:  # ya usada
        conn.close()
        return False

    expire_at = row[1]

    # actualizar usuario con la expiración de la key
    cursor.execute("""
        INSERT INTO users (user_id, username, expire_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET expire_at=excluded.expire_at
    """, (user_id, username, expire_at))

    # marcar la key como usada
    cursor.execute("UPDATE keys SET used=1 WHERE key=?", (key,))
    conn.commit()
    conn.close()

    return True

def has_valid_key(user_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT expire_at FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    expire_at = datetime.fromisoformat(row[0])
    return expire_at > datetime.now()