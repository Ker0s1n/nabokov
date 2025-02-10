from telegram import Update
from telegram.ext import ContextTypes


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором группы."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Кэшируем список администраторов
    if "admins" not in context.bot_data:
        context.bot_data["admins"] = {}

    if chat_id not in context.bot_data["admins"]:
        admins = await context.bot.get_chat_administrators(chat_id)
        context.bot_data["admins"][chat_id] = [
            admin.user.id for admin in admins if not admin.user.is_bot
        ]

    # Проверяем, есть ли пользователь среди администраторов
    return user_id in context.bot_data["admins"][chat_id]
