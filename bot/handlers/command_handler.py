from database.db import create_connection
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ищет сообщения по хештегу."""
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
    welcome_text = (
        "👋 Привет! Я бот, который помогает управлять группой и искать сообщения.\n\n"
        "Вот список доступных команд:"
    )
    commands = [["/start", "/find #info"],]
    reply_markup = ReplyKeyboardMarkup(commands, resize_keyboard=True)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
