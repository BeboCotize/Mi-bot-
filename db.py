import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
cursor = conn.cursor()

# Crear tablas
cursor.execute("""
CREATE TABLE IF NOT EXISTS banned_users (
    user_id BIGINT PRIMARY KEY
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS registered_users (
    user_id BIGINT PRIMARY KEY,
    username TEXT
);
""")
conn.commit()

# 🚫 Ban
def ban_user(user_id: int):
    cursor.execute("INSERT INTO banned_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING;", (user_id,))
    conn.commit()

def unban_user(user_id: int):
    cursor.execute("DELETE FROM banned_users WHERE user_id = %s;", (user_id,))
    conn.commit()

def is_banned(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM banned_users WHERE user_id = %s;", (user_id,))
    return cursor.fetchone() is not None

# ✅ Registro
def register_user(user_id: int, username: str):
    cursor.execute("INSERT INTO registered_users (user_id, username) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (user_id, username))
    conn.commit()

def is_registered(user_id: int) -> bool:
    cursor.execute("SELECT 1 FROM registered_users WHERE user_id = %s;", (user_id,))
    return cursor.fetchone() is not None