import logging
import os
from typing import Optional
from uuid import uuid4

from dotenv import load_dotenv
from telegram import (
    Chat,
    ChatMember,
    ChatMemberUpdated,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=os.getenv("BOT_DESCRIPTION")
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=update.message.text
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = " ".join(context.args).upper()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text_caps
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="Caps",
            input_message_content=InputTextMessageContent(query.upper()),
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


def extract_status_change(
    chat_member_update: ChatMemberUpdated,
) -> Optional[tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member'
    was a member of the chat and whether the 'new_chat_member' is a member of the chat.
    Returns None, if the status didn't change.
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


async def track_chats(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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
            # This may not be really needed in practice because most clients
            # will automatically send a /start command after the user unblocks the bot,
            # and start_private_chat() will add the user to "user_ids".
            # We're including this here for the sake of the example.
            logger.info("%s unblocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info("%s blocked the bot", cause_name)
            context.bot_data.setdefault("user_ids", set()).discard(chat.id)
    elif chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        if not was_member and is_member:
            logger.info(
                "%s added the bot to the group %s", cause_name, chat.title
            )
            context.bot_data.setdefault("group_ids", set()).add(chat.id)
        elif was_member and not is_member:
            logger.info(
                "%s removed the bot from the group %s", cause_name, chat.title
            )
            context.bot_data.setdefault("group_ids", set()).discard(chat.id)
    elif not was_member and is_member:
        logger.info(
            "%s added the bot to the channel %s", cause_name, chat.title
        )
        context.bot_data.setdefault("channel_ids", set()).add(chat.id)
    elif was_member and not is_member:
        logger.info(
            "%s removed the bot from the channel %s", cause_name, chat.title
        )
        context.bot_data.setdefault("channel_ids", set()).discard(chat.id)


async def show_chats(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
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


async def greet_chat_members(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()

    if not was_member and is_member:
        await update.effective_chat.send_message(
            f"{member_name} was added by {cause_name}. Welcome!",
            parse_mode=ParseMode.HTML,
        )
    elif was_member and not is_member:
        await update.effective_chat.send_message(
            f"{member_name} is no longer with us. Thanks a lot, {cause_name} ...",
            parse_mode=ParseMode.HTML,
        )


async def start_private_chat(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Greets the user and records that they started a chat with the bot
    if it's a private chat. Since no `my_chat_member` update is issued when
    a user starts a private chat with the bot for the first time,
    we have to track it explicitly here.
    """
    user_name = update.effective_user.full_name
    chat = update.effective_chat
    if chat.type != Chat.PRIVATE or chat.id in context.bot_data.get(
        "user_ids", set()
    ):
        return

    logger.info("%s started a private chat with the bot", user_name)
    context.bot_data.setdefault("user_ids", set()).add(chat.id)

    await update.effective_message.reply_text(
        f"Welcome {user_name}. Use /show_chats to see what chats I'm in."
    )


# async def notify_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user = update.message.left_chat_member
#     chat_id = update.message.chat_id

#     # Получаем список администраторов группы
#     admins = await context.bot.get_chat_administrators(chat_id)

#     # Формируем сообщение
#     message = f"Пользователь {user.first_name} вышел из группы."

#     # Отправляем сообщение каждому администратору
#     for admin in admins:
#         await context.bot.send_message(chat_id=admin.user.id, text=message)


def main() -> None:
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    start_handler = CommandHandler("start", start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler("caps", caps)
    inline_caps_handler = InlineQueryHandler(inline_caps)
    # leave_handler = MessageHandler(
    #     filters.StatusUpdate._LeftChatMember, notify_admins
    # )
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
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
    # application.add_handler(leave_handler)
    application.add_handler(unknown_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
