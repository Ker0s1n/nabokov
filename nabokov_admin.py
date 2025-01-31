import logging
import os
from typing import Optional

from dotenv import load_dotenv
from telegram import Chat, ChatMember, ChatMemberUpdated, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Токен твоего бота
TOKEN = os.getenv("TOKEN")


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get(
        "is_member", (None, None)
    )

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def track_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tracks the chats the bot is in."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return
    was_member, is_member = result

    # Let's check who is responsible for the change
    cause_name = update.effective_user.full_name

    # Handle chat types differently:
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        if not was_member and is_member:
            # This may not be really needed in practice because most clients will automatically
            # send a /start command after the user unblocks the bot, and start_private_chat()
            # will add the user to "user_ids".
            # We're including this here for the sake of the example.
            logger.info("%s unblocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info("%s added the bot to the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s removed the bot from the group %s", cause_name, chat.title)
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    elif not was_member and is_member:
        logger.info("%s added the bot to the channel %s", cause_name, chat.title)
        context.bot_data.setdefault("channel_ids", set()).add(chat.id)
    elif was_member and not is_member:
        logger.info("%s removed the bot from the channel %s", cause_name, chat.title)
        context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


async def show_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shows which chats the bot is in"""
    user_ids = ", ".join(
        str(uid) for uid in context.bot_data.setdefault("user_ids", set())
    )
    group_ids = ", ".join(
        str(gid) for gid in context.bot_data.setdefault("group_ids", set())
    )
    channel_ids = ", ".join(
        str(cid) for cid in context.bot_data.setdefault("channel_ids", set())
    )
    text = (
        f"@{context.bot.username} is currently in a conversation with the user IDs {user_ids}."
        f" Moreover it is a member of the groups with IDs {group_ids} "
        f"and administrator in the channels with IDs {channel_ids}."
    )
    await update.effective_message.reply_text(text)


async def get_chat_admins(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE
) -> list[int]:
    """Возвращает список ID администраторов чата."""
    admins = await context.bot.get_chat_administrators(chat_id)
    # Исключаем ботов из списка администраторов
    return [admin.user.id for admin in admins if not admin.user.is_bot]


async def greet_chat_members(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Greets new users in chats and announces when someone leaves.
    Sends a notification to all admins."""
    logger.info("greet_chat_members triggered")
    # Проверка типа чата
    if update.effective_chat.type not in [Chat.GROUP, Chat.SUPERGROUP]:
        logger.info("Not a group chat. Skipping.")
        return

    result = extract_status_change(update.chat_member)
    if result is None:
        logger.info("No status change detected in greet_chat_members.")
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    # Получаем список администраторов чата
    admins = await get_chat_admins(update.effective_chat.id, context)

    if not was_member and is_member:
        # Уведомление в чат
        await update.effective_chat.send_message(
            f"{member_name} was added by {cause_name}. Welcome!",
            parse_mode=ParseMode.HTML,
        )
        # Уведомление всем администраторам
        for admin_id in admins:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🟢 {member_name} был добавлен в чат {update.effective_chat.title} пользователем {cause_name}.",
                parse_mode=ParseMode.HTML,
            )
    elif was_member and not is_member:
        # Уведомление в чат
        await update.effective_chat.send_message(
            f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )
        # Уведомление всем администраторам
        for admin_id in admins:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"🔴 {member_name} был удален из чата {update.effective_chat.title} пользователем {cause_name}.",
                parse_mode=ParseMode.HTML,
            )


# async def greet_chat_members(
#     update: Update, context: ContextTypes.DEFAULT_TYPE
# ) -> None:
#     """Greets new users in chats and announces when someone leaves"""
#     result = extract_status_change(update.chat_member)
#     if result is None:
#         return

#     was_member, is_member = result
#     cause_name = update.chat_member.from_user.mention_html()
#     member_name = update.chat_member.new_chat_member.user.mention_html()

#     if not was_member and is_member:
#         await update.effective_chat.send_message(
#             f"{member_name} was added by {cause_name}. Welcome!",
#             parse_mode=ParseMode.HTML,
#         )
#     elif was_member and not is_member:
#         await update.effective_chat.send_message(
#             f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
#             parse_mode=ParseMode.HTML,
#         )


async def start_private_chat(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Greets the user and records that they started a chat with the bot if it's a private chat.
    Since no `my_chat_member` update is issued when a user starts a private chat with the bot
    for the first time, we have to track it explicitly here.
    """
    user_name = update.effective_user.full_name
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE or chat.id in context.bot_data.get("user_ids", set()):
        return

    logger.info("%s started a private chat with the bot", user_name)
    context.bot_data.setdefault("user_ids", set()).add(chat.id)

    await update.effective_message.reply_text(
        f"Welcome {user_name}. Use /show_chats to see what chats I'm in."
    )


# Основная функция
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Keep track of which chats the bot is in
    application.add_handler(
        ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_handler(CommandHandler("show_chats", show_chats))
    # Handle members joining/leaving chats.
    application.add_handler(
        ChatMemberHandler(greet_chat_members, ChatMemberHandler.CHAT_MEMBER)
    )
    # Interpret any other command or text message as a start of a private chat.
    # This will record the user as being in a private chat with bot.
    application.add_handler(MessageHandler(filters.ALL, start_private_chat))

    application.run_polling()


if __name__ == "__main__":
    main()
