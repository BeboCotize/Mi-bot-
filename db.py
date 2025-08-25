import sqlite3

DB_NAME = "usuarios.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            registrado INTEGER DEFAULT 0,
            baneado INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def registrar_usuario(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO usuarios (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def marcar_registrado(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET registrado = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def ban_user(user_id: int, reason: str = "Baneado"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET baneado = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET baneado = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()