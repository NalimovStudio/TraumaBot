import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.flags import get_flag
from aiogram.types import TelegramObject
from dishka import AsyncContainer

from source.application.user.user_mood import IsMoodSetToday

logger = logging.getLogger(__name__)


class LoadUserMood(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ):
        """сохраняет is_mood_was_set_today в data если есть нужный флаг у роутера"""
        # [ check flag ]
        is_mood_flag: bool = get_flag(data, "user_mood")
        logger.info(f"Need mood check: {is_mood_flag}")

        if not is_mood_flag:
            return await handler(event, data)

        # Проверяем, что пользователь уже загружен
        user = data.get("user")
        if not user:
            logger.warning("User not found in context, skipping mood check")
            return await handler(event, data)

        container: AsyncContainer = data["dishka_container"]
        is_mood_set_interactor: IsMoodSetToday = await container.get(IsMoodSetToday)

        # Используем telegram_id из уже загруженного пользователя
        telegram_id = user.telegram_id

        is_mood_set: bool = await is_mood_set_interactor(telegram_id)
        data["is_mood_was_set_today"] = is_mood_set

        logger.info(f"Is mood set for user {telegram_id}: {is_mood_set}")
        return await handler(event, data)
