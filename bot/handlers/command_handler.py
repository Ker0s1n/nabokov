from database.db import create_connection
from telegram import Update
from telegram.ext import ContextTypes
from utils.admin_check import is_admin


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ищет сообщения по хештегу (только для администраторов)."""
    if not await is_admin(update, context):
        await update.message.reply_text(
            "🚫 Эта команда доступна только администраторам."
        )
        return

    hashtag = context.args[0].lower() if context.args else None
    if not hashtag or "#" not in hashtag:
        await update.message.reply_text(
            "Пожалуйста, укажите хештег. Например: /find #example"
        )
        return

    conn = create_connection("bot.db")
    cur = conn.cursor()
    cur.execute(
        """
        SELECT messages.text, users.full_name
        FROM messages
        JOIN users ON messages.user_id = users.user_id
        WHERE messages.text LIKE ?
        """,
        (f"%{hashtag}%",),
    )
    messages = cur.fetchall()

    if messages:
        # Формируем ответ с автором и текстом сообщения
        response = "\n\n".join(
            [f"👤 {author}:\n{text}" for text, author in messages]
        )
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"Сообщений с хештегом {hashtag} не найдено."
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствует пользователя и показывает доступные команды."""
    welcome_text = "👋 Привет! Я бот, который помогает администратору."
    await update.message.reply_text(welcome_text)
