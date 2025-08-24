import os
import psycopg2
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========================
# CONEXIÓN A LA BASE DE DATOS
# ========================
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:vrAKnRQCIRHAwxMozKTLPNKlEzmnxPHE@switchback.proxy.rlwy.net:54815/railway")

conn = psycopg2.connect(DB_URL, sslmode="require")
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL
);
""")
conn.commit()

# Insertar películas de ejemplo (solo si la tabla está vacía)
cursor.execute("SELECT COUNT(*) FROM movies;")
count = cursor.fetchone()[0]
if count == 0:
    cursor.executemany("INSERT INTO movies (title) VALUES (%s);", [
        ("Inception",),
        ("The Matrix",),
        ("Interstellar",),
        ("Avengers: Endgame",)
    ])
    conn.commit()


# ========================
# BOT TELEGRAM
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # en Railway pon tu token como variable de entorno

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎬 Ver películas", callback_data="ver_peliculas")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Bienvenido al Bot de Películas", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "ver_peliculas":
        cursor.execute("SELECT id, title FROM movies LIMIT 4;")
        movies = cursor.fetchall()

        keyboard = []
        for mid, title in movies:
            keyboard.append([InlineKeyboardButton(title, callback_data=f"pelicula_{mid}")])
        keyboard.append([InlineKeyboardButton("⬅️ Volver atrás", callback_data="volver")])

        await query.edit_message_text("📽️ Selecciona una película:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("pelicula_"):
        movie_id = int(query.data.split("_")[1])
        cursor.execute("SELECT title FROM movies WHERE id = %s;", (movie_id,))
        movie = cursor.fetchone()
        await query.edit_message_text(f"🍿 Elegiste: *{movie[0]}*", parse_mode="Markdown")

    elif query.data == "volver":
        keyboard = [
            [InlineKeyboardButton("🎬 Ver películas", callback_data="ver_peliculas")]
        ]
        await query.edit_message_text("👋 Bienvenido al Bot de Películas", reply_markup=InlineKeyboardMarkup(keyboard))


# ========================
# MAIN
# ========================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🤖 Bot corriendo...")
    app.run_polling()


if __name__ == "__main__":
    main()