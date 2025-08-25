import sqlite3

DB_NAME = "usuarios.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY,
            registrado INTEGER DEFAULT 0,
            baneado INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def register_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO usuarios (id, registrado, baneado) VALUES (?, 1, 0)", (user_id,))
    conn.commit()
    conn.close()

def is_registered(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT registrado FROM usuarios WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1

def is_banned(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT baneado FROM usuarios WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result and result[0] == 1