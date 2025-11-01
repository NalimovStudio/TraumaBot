import json
import logging
import re
from uuid import UUID
from functools import partial

from aiogram import Bot
from aiogram.types import Message

from source.core.schemas import UserDialogsLoggingCreateSchema, UserSchema
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.application.user import GetUserSchemaById
from source.infrastructure.database.uow import UnitOfWork

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


async def log_message(
    dialogue_id: UUID,
    telegram_id: str,  
    get_user: GetUserSchemaById,
    dialogs_repo: UserDialogsLoggingRepository,
    uow: UnitOfWork,
    text: str,
    role: str,
):
    """Сохраняет сообщение в бд"""
    logger = logging.getLogger(__name__)
    try:
        # Ищем пользователя по telegram_id
        user_in_db: UserSchema = await get_user(telegram_id)
        if user_in_db:
            log_schema = UserDialogsLoggingCreateSchema(
                user_id=user_in_db.id,  # Это UUID, а не telegram_id
                dialogue_id=dialogue_id,
                role=role,
                message_text=text
            )
            await dialogs_repo.create(log_schema)
            await uow.commit()
            logger.info(f"Saved message in DATABASE  for user {telegram_id} dialogue_id {dialogue_id}")
        else:
            logger.warning(f"User with telegram_id {telegram_id} not found in DB. Cannot save message.")

    except Exception as e:
        logger.error(f"Failed to save message for user {telegram_id}: {e}")
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

def json_default_serializer(obj):
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

custom_json_dumps = partial(json.dumps, default=json_default_serializer)
custom_json_loads = json.loads
