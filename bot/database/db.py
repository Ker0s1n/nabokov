import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """Создаёт соединение с базой данных SQLite."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Соединение с SQLite установлено: {db_file}")
    except Error as e:
        print(f"Ошибка при подключении к SQLite: {e}")
    return conn


def create_tables(conn):
    """Создаёт таблицы в базе данных."""
    sql_create_messages_table = """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        full_name TEXT
    );
    """

    try:
        c = conn.cursor()
        c.execute(sql_create_messages_table)
        c.execute(sql_create_users_table)
        print("Таблицы созданы успешно.")
    except Error as e:
        print(f"Ошибка при создании таблиц: {e}")
