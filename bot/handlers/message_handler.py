def save_message(conn, message):
    """Сохраняет сообщение в базу данных."""
    sql = """
    INSERT INTO messages(chat_id, user_id, text)
    VALUES(?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (message.chat_id, message.user_id, message.text))
    conn.commit()


def save_user(conn, user):
    """Сохраняет пользователя в базу данных."""
    sql = """
    INSERT OR IGNORE INTO users(user_id, username, full_name)
    VALUES(?, ?, ?)
    """
    cur = conn.cursor()
    cur.execute(sql, (user.user_id, user.username, user.full_name))
    conn.commit()
