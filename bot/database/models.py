from datetime import datetime


class Message:
    def __init__(self, chat_id, user_id, text, timestamp=None):
        self.chat_id = chat_id
        self.user_id = user_id
        self.text = text
        self.timestamp = timestamp or datetime.now()


class User:
    def __init__(self, user_id, username=None, full_name=None):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
