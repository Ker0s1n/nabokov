import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    CallbackContext,
    MessageHandler,
    Updater,
    filters,
)

load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


# Функция для уведомления администраторов
async def notify_admins(update: Update, context: CallbackContext):
    user = update.message.left_chat_member
    chat_id = update.message.chat_id

    # Получаем список администраторов группы
    admins = await context.bot.get_chat_administrators(chat_id)

    # Формируем сообщение
    message = (
        f"Пользователь {user.first_name} вышел из группы и хлопнул дверью."
    )

    # Отправляем сообщение каждому администратору
    for admin in admins:
        await context.bot.send_message(chat_id=admin.user.id, text=message)


# Основная функция для запуска бота
def main():
    # Вставьте сюда ваш токен
    TOKEN = os.getenv("TOKEN")

    # Создаем Updater и передаем ему токен вашего бота
    updater = Updater(TOKEN, update_queue=None)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher()

    # Регистрируем обработчик для события выхода пользователя из группы
    dp.add_handler(
        MessageHandler(filters.status_update.left_chat_member, notify_admins)
    )

    # Запускаем бота
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
