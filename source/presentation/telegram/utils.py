import json
import logging
import re
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.markdown import hbold

from source.application.message_history.message_history_service import MessageHistoryService
from source.core.schemas.user_schema import UserDialogsLoggingCreateSchema
from source.core.schemas.user_schema import UserSchema
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork


TELEGRAM_MAX_MESSAGE_LENGTH = 4096


async def log_support_dialog(
    user_id: int,
    context_scope: str,
    history_service: MessageHistoryService,
    user_repo: UserRepository,
    dialogs_repo: UserDialogsLoggingRepository,
    uow: UnitOfWork,
):
    logger = logging.getLogger(__name__)
    try:
        full_history = await history_service.get_history(user_id, context_scope)
        if not full_history:
            logger.info(f"No history to log for user {user_id} in scope {context_scope}.")
            return

        history_json = json.dumps([msg.model_dump() for msg in full_history], ensure_ascii=False, indent=2)

        user_in_db: UserSchema = await user_repo.get_schema_by_telegram_id(str(user_id))
        if user_in_db:
            log_schema = UserDialogsLoggingCreateSchema(user_id=user_in_db.id, message=history_json)
            await dialogs_repo.create(log_schema)
            await uow.commit()
            logger.info(f"Dialog for user {user_id} in scope {context_scope} saved successfully.")
        else:
            logger.warning(f"User with telegram_id {user_id} not found in DB. Cannot save dialog.")

    except Exception as e:
        logger.error(f"Failed to save dialog for user {user_id} in scope {context_scope}: {e}")
        await uow.rollback()


async def send_long_message(message: Message, text: str, bot: Bot, keyboard=None):
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        await bot.send_message(message.chat.id, text, reply_markup=keyboard, parse_mode="HTML")
        return

    parts = []
    while len(text) > 0:
        if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
            split_pos = text.rfind('\n', 0, TELEGRAM_MAX_MESSAGE_LENGTH)
            if split_pos == -1:
                split_pos = TELEGRAM_MAX_MESSAGE_LENGTH
            parts.append(text[:split_pos])
            text = text[split_pos:]
        else:
            parts.append(text)
            break

    for i, part in enumerate(parts):
        current_keyboard = keyboard if i == len(parts) - 1 else None
        await bot.send_message(message.chat.id, part, reply_markup=current_keyboard, parse_mode="HTML")


def extract_json_from_markdown(text: str) -> str:
    match = re.search(r'```(json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(2).strip()
    return text

import re

def convert_markdown_to_html(text: str) -> str:
    """
    Конвертирует базовые элементы Markdown в HTML.
    """
    # Заменяем **жирный** на <b>жирный</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    # Заменяем *курсив* на <i>курсив</i>
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    # Заменяем _курсив_ на <i>курсив</i>
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
    return text
