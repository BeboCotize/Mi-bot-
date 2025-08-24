import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Leer la variable de entorno DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ No se encontró la variable de entorno DATABASE_URL. Verifica en Railway.")

# Función para obtener conexión
def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# Crear tablas si no existen
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            user_id BIGINT PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# Banear usuario
def ban_user(user_id: int, reason: str = "No reason"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO bans (user_id, reason) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING", (user_id, reason))
    conn.commit()
    cur.close()
    conn.close()


# Verificar si está baneado
def is_banned(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM bans WHERE user_id = %s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None


# Desbanear usuario
def unban_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM bans WHERE user_id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()