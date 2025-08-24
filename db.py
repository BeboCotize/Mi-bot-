# db.py
import psycopg2
import os

DB_URL = os.getenv("DB_URL")

def get_connection():
    return psycopg2.connect(DB_URL, sslmode="require")

def ban_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO banned_users (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def is_banned(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM banned_users WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def unban_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM banned_users WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()