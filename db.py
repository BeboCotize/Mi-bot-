import sqlite3

DB_NAME = "bot.db"

# -------------------------------
# Inicializa la base de datos
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            is_banned INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

# -------------------------------
# Registrar usuario
# -------------------------------
def register_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username)
        VALUES (?, ?)
    ''', (user_id, username))

    conn.commit()
    conn.close()

# -------------------------------
# Verificar si un usuario está baneado
# -------------------------------
def is_banned(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0] == 1
    return False

# -------------------------------
# Banear usuario
# -------------------------------
def ban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET is_banned = 1 WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

# -------------------------------
# Desbanear usuario
# -------------------------------
def unban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET is_banned = 0 WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()

# -------------------------------
# Verificar si es admin
# -------------------------------
def is_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0] == 1
    return False

# -------------------------------
# Hacer admin a un usuario
# -------------------------------
def make_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET is_admin = 1 WHERE user_id = ?', (user_id,))

    conn.commit()
    conn.close()