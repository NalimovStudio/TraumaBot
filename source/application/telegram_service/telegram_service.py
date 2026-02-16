import json
import logging

import aiohttp
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from os import environ

logger = logging.getLogger(__name__)


class TelegramService:
    """Сервис для отправки сообщений через Telegram Bot API"""

    def __init__(self):
        """Инициализация сервиса"""
        self.api_url = f"https://api.telegram.org/bot{environ.get('TELEGRAM_TOKEN')}"

    @staticmethod
    def _clean_html_text(text: str) -> str:
        """Заменяет умные кавычки на обычные для HTML"""
        replacements = {
            '“': '"',  # левая умная кавычка
            '”': '"',  # правая умная кавычка
            '‘': "'",  # левая одинарная умная
            '’': "'",  # правая одинарная умная
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    async def send_message(
            self,
            user_telegram_id: str,
            message: str,
            reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup = None  # keyboard
    ):
        """Отправляет сообщение юзеру"""
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": user_telegram_id,
            "text": self._clean_html_text(message),
            "parse_mode": "HTML",
            "disable_web_page_preview": "true"
        }

        if reply_markup:
            import json
            data["reply_markup"] = json.dumps(reply_markup)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 403:
                    response_text = await response.text()
                    raise ValueError(f"Ошибка отправки сообщения в Telegram: {response.status} - {response_text}")

    async def edit_message(
            self,
            old_message_id: str,
            user_telegram_id: str,
            message_text: str,
            reply_markup: InlineKeyboardMarkup | None = None,
            parse_mode: str = "HTML"
    ):
        """Редактирует сообщение"""
        url: str = f"{self.api_url}/editMessageText"
        data = {
            "chat_id": user_telegram_id,
            "message_id": old_message_id,
            "text": message_text,
            "parse_mode": parse_mode
        }

        if reply_markup:
            # Ручная сериализация, чтобы избежать проблем с None значениями
            keyboard_data = {
                "inline_keyboard": [
                    [
                        {
                            "text": button.text,
                            "callback_data": button.callback_data
                            # Не включаем url, web_app и другие поля если они None
                        }
                        for button in row
                    ]
                    for row in reply_markup.inline_keyboard
                ]
            }
            data["reply_markup"] = json.dumps(keyboard_data)

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise ValueError(f"Ошибка отправки сообщения в Telegram: {response.status} - {response_text}")
