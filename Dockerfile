# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем исходный код
COPY . .

# Устанавливаем зависимости
RUN build.sh

# Запускаем бота
CMD ["python", "bot/main.py"]