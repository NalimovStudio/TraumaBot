import logging
from collections.abc import Awaitable, Callable
from typing import Any

from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME
from source.core.schemas.user_schema import UserSchema


from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.types import User as TelegramUser

from source.application.user import CreateUser
from source.core.schemas.user_schema import UserSchemaRequest
from source.application.user.get_by_id import GetUserSchemaById


class LoadUserMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], 
        event: TelegramObject, 
        data: dict[str, Any]
    ):
        try:
            if data.get("event_from_user"):
                dishka: AsyncContainer = data[CONTAINER_NAME]
                create_user: CreateUser = await dishka.get(CreateUser)
                get_user: GetUserSchemaById = await dishka.get(GetUserSchemaById)
                aiogram_user: TelegramUser = data["event_from_user"]
                user: UserSchema = await create_user(
                    UserSchemaRequest(
                        telegram_id=str(aiogram_user.id),
                        username=aiogram_user.username
                    )
                )

                data["user"] = user
                return await handler(event, data)
                
        except Exception:
            logging.info("User already created")
            user: UserSchema = await get_user(str(aiogram_user.id))
            data["user"] = user
        
            return await handler(event, data)

        
            