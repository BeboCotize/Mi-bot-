import os
import re
import random
import asyncio
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatAction
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ApplicationHandlerStop
)
import asyncpg

# -------------------- CONFIG --------------------
load_dotenv()  # opcional: permite usar .env localmente

BOT_TOKEN = os.getenv("8271445453:AAGkEThWtDCPRfEFOUfzLBxc3lIriZ9SvsM") or os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6629555218"))

# Postgres desde Railway (auto-variables)
PGHOST = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE")

# Antispam
SPAM_WINDOW_SEC = 30     # ventana
SPAM_MAX_CMDS = 20       # umbral
BAN_HOURS = 5            # duración ban

# ------------------------------------------------

# Conexión global a Postgres (pool)
db_pool: asyncpg.Pool | None = None


# -------------------- DB UTILS --------------------
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=PGHOST, port=PGPORT, user=PGUSER,
        password=PGPASSWORD, database=PGDATABASE,
        min_size=1, max_size=5
    )
    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_bans (
            user_id BIGINT PRIMARY KEY,
            reason TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL
        );
        CREATE TABLE IF NOT EXISTS spam_log (
            user_id BIGINT NOT NULL,
            ts TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_spamlog_user_ts ON spam_log (user_id, ts);
        """)


async def is_banned(user_id: int) -> tuple[bool, str | None, datetime | None]:
    """Devuelve (ban_activo, razon, expira_en)"""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT reason, expires_at FROM user_bans WHERE user_id=$1", user_id
        )
        if not row:
            return False, None, None
        reason, expires = row["reason"], row["expires_at"]
        now = datetime.now(timezone.utc)
        if expires > now:
            return True, reason, expires
        # Si ya expiró, limpia
        await conn.execute("DELETE FROM user_bans WHERE user_id=$1", user_id)
        return False, None, None


async def ban_user(user_id: int, reason: str, hours: int = BAN_HOURS):
    until = datetime.now(timezone.utc) + timedelta(hours=hours)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO user_bans (user_id, reason, expires_at)
            VALUES ($1,$2,$3)
            ON CONFLICT (user_id) DO UPDATE
            SET reason=EXCLUDED.reason, expires_at=EXCLUDED.expires_at
        """, user_id, reason, until)
    return until


async def unban_user(user_id: int) -> bool:
    async with db_pool.acquire() as conn:
        res = await conn.execute("DELETE FROM user_bans WHERE user_id=$1", user_id)
    return res and res.lower().startswith("delete")


async def log_event(user_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO spam_log (user_id, ts) VALUES ($1, $2)",
            user_id, datetime.now(timezone.utc)
        )


async def count_recent(user_id: int, seconds: int) -> int:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT COUNT(*) as c
            FROM spam_log
            WHERE user_id=$1 AND ts > (NOW() AT TIME ZONE 'UTC') - $2::INTERVAL
        """, user_id, f"{seconds} seconds")
    return int(row["c"]) if row else 0


# -------------------- ANTISPAM (middleware) --------------------
async def guard_antispam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Corre antes que todo. Checa ban y antispam para TODOS los comandos/msgs."""
    user = update.effective_user
    if not user:
        return

    uid = user.id

    # 1) Si ya está baneado, corta
    banned, reason, expires = await is_banned(uid)
    if banned:
        if update.effective_message:
            await update.effective_message.reply_text(
                f"🚫 Estás bloqueado.\nMotivo: {reason}\n"
                f"⏳ Expira: {expires.astimezone().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        raise ApplicationHandlerStop

    # 2) Log + cuenta ventana
    await log_event(uid)
    n = await count_recent(uid, SPAM_WINDOW_SEC)

    if n > SPAM_MAX_CMDS:
        reason = f"Spam: más de {SPAM_MAX_CMDS} comandos en {SPAM_WINDOW_SEC}s"
        until = await ban_user(uid, reason, BAN_HOURS)

        # Avisar al usuario
        if update.effective_message:
            await update.effective_message.reply_text(
                f"🚫 Has sido bloqueado por *{BAN_HOURS} horas*.\n"
                f"Motivo: {reason}",
                parse_mode="Markdown"
            )

        # Avisar al admin
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "⚠️ *Usuario bloqueado por SPAM*\n"
                    f"• ID: `{uid}`\n"
                    f"• Motivo: {reason}\n"
                    f"• Expira: {until.astimezone().strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass

        raise ApplicationHandlerStop


# -------------------- HELPERS UI --------------------
def main_menu(admin: bool = False) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🎬 Películas", callback_data="menu_movies")],
        [InlineKeyboardButton("🍔 Comida", callback_data="menu_food")],
    ]
    if admin:
        buttons.append([InlineKeyboardButton("🛡️ Panel admin", callback_data="menu_admin")])
    return InlineKeyboardMarkup(buttons)


def movies_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎞️ Estrenos", url="https://www.imdb.com/movies-in-theaters/")],
        [InlineKeyboardButton("⭐ Top 250", url="https://www.imdb.com/chart/top/")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_home")]
    ])


def food_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🍕 Pizza", url="https://www.google.com/maps/search/pizza+")],
        [InlineKeyboardButton("🍔 Hamburguesas", url="https://www.google.com/maps/search/hamburguesas+")],
        [InlineKeyboardButton("🍣 Sushi", url="https://www.google.com/maps/search/sushi+")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_home")]
    ])


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧹 Unban (escribe: unban <ID>)", callback_data="noop")],
        [InlineKeyboardButton("🔙 Volver", callback_data="back_home")]
    ])


# -------------------- COMANDOS --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("🔒 Bot privado.")
        return

    await update.message.reply_text(
        "¡Bienvenido, admin! 👑\nElige una opción:",
        reply_markup=main_menu(admin=True)
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "menu_movies":
        await q.edit_message_text("🎬 Navega películas:", reply_markup=movies_menu())

    elif q.data == "menu_food":
        await q.edit_message_text("🍔 Opciones de comida:", reply_markup=food_menu())

    elif q.data == "menu_admin":
        if q.from_user.id != ADMIN_ID:
            await q.edit_message_text("⛔ Solo admin.", reply_markup=main_menu())
            return
        await q.edit_message_text("🛡️ Panel de administración:", reply_markup=admin_menu())

    elif q.data == "back_home":
        is_admin = q.from_user.id == ADMIN_ID
        await q.edit_message_text("Menú principal:", reply_markup=main_menu(admin=is_admin))

    else:
        # noop
        pass


# ---------- Prefijo "." (solo start es sin prefijo) ----------
async def dot_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text.startswith("."):
        return

    cmd, *args = text[1:].split()
    cmd = cmd.lower()

    # .gen  -> generador de tarjeta
    if cmd == "gen":
        # Simulación de tarjeta (texto simple)
        brand = random.choice(["VISA", "MASTERCARD"])
        number = "".join(str(random.randint(0, 9)) for _ in range(16))
        exp_m = random.randint(1, 12)
        exp_y = random.randint(25, 32)
        cvv = random.randint(100, 999)
        await update.message.reply_text(
            f"💳 *Tarjeta Generada*\n"
            f"• Marca: {brand}\n"
            f"• Número: `{number}`\n"
            f"• Expira: {exp_m:02d}/{exp_y}\n"
            f"• CVV: `{cvv}`",
            parse_mode="Markdown"
        )
        return

    # .ban <id> <razón...>  (solo admin)
    if cmd == "ban":
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("⛔ Solo admin.")
            return
        if not args:
            await update.message.reply_text("Uso: `.ban <user_id> <razón opcional>`")
            return
        try:
            uid = int(args[0])
        except ValueError:
            await update.message.reply_text("ID inválido.")
            return
        reason = " ".join(args[1:]).strip() or "Ban manual por admin"
        until = await ban_user(uid, reason, BAN_HOURS)
        await update.message.reply_text(
            f"✅ Usuario `{uid}` bloqueado hasta {until.astimezone().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode="Markdown"
        )
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"⛔ Has sido bloqueado por el admin.\nMotivo: {reason}"
            )
        except Exception:
            pass
        return

    # .unban <id> (alias de /unban)
    if cmd == "unban":
        await unban_cmd(update, context, args_only=True)
        return

    await update.message.reply_text("❓ Comando desconocido con prefijo '.'")


# /unban <id>  o texto simple: "unban <id>"
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, args_only: bool = False):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Solo admin.")
        return

    # cuando viene de .unban ya nos pasan los args en message
    args = context.args if not args_only else (update.message.text.split()[1:] if len(update.message.text.split()) > 1 else [])

    target_id = None
    if args:
        try:
            target_id = int(args[0])
        except ValueError:
            pass
    else:
        # quizá vino como texto "unban 123"
        m = re.match(r"^\s*unban\s+(\d+)\s*$", (update.message.text or ""), re.I)
        if m:
            target_id = int(m.group(1))

    if not target_id:
        await update.message.reply_text("Uso: `/unban <user_id>` o `unban <user_id>`", parse_mode="Markdown")
        return

    ok = await unban_user(target_id)
    if ok:
        await update.message.reply_text(f"✅ Usuario `{target_id}` desbaneado.", parse_mode="Markdown")
        try:
            await context.bot.send_message(chat_id=target_id, text="✅ Has sido desbaneado por el admin.")
        except Exception:
            pass
    else:
        await update.message.reply_text("ℹ️ Ese usuario no estaba baneado.")


# Para que “unban <ID>” como texto simple funcione
async def plain_unban_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if re.match(r"^unban\s+\d+\s*$", text, re.I):
        await unban_cmd(update, context)


# -------------------- MAIN --------------------
async def on_startup(app):
    await init_db()
    print("DB lista ✅")

def build_application():
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    # Middleware de antispam/bans (grupo 0)
    app.add_handler(MessageHandler(filters.ALL, guard_antispam), group=0)

    # Comandos
    app.add_handler(CommandHandler("start", start), group=1)
    app.add_handler(CommandHandler("unban", unban_cmd), group=1)

    # Texto simple “unban <id>”
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), plain_unban_listener), group=1)

    # Prefijo "."
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\."), dot_commands), group=1)

    # Botones
    app.add_handler(CallbackQueryHandler(handle_buttons), group=1)

    return app


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("❌ Faltó BOT_TOKEN en variables de entorno.")
    app = build_application()
    app.run_polling(close_loop=False)