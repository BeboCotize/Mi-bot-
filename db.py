# db.py
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registered_at TEXT,
            expires_at TEXT,
            banned INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def register_user(user_id, username, days=1):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    expires_at = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT OR REPLACE INTO users (user_id, username, registered_at, expires_at) VALUES (?, ?, ?, ?)", 
              (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), expires_at))
    conn.commit()
    conn.close()

def is_registered(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user is not None

def is_banned(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT banned FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None and result[0] == 1