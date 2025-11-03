import json
from functools import partial
from uuid import UUID

from aiogram import Bot
from aiogram.types import Message

TELEGRAM_MAX_MESSAGE_LENGTH = 4096


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
