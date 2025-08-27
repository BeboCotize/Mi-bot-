import sqlite3
import datetime

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            has_key INTEGER DEFAULT 0,
            key_expiration TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            expiration TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def user_has_access(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT has_key, key_expiration FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if row:
        has_key, exp = row
        if has_key and exp:
            if datetime.datetime.now() < datetime.datetime.fromisoformat(exp):
                return True
    return False

def generate_key(key, expiration_date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO keys (key, expiration) VALUES (?, ?)", (key, expiration_date))
    conn.commit()
    conn.close()

def claim_key(user_id, key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT expiration FROM keys WHERE key=?", (key,))
    row = c.fetchone()
    if row:
        expiration = row[0]
        c.execute("UPDATE users SET has_key=1, key_expiration=? WHERE user_id=?", (expiration, user_id))
        c.execute("DELETE FROM keys WHERE key=?", (key,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False