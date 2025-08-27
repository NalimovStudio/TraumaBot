import logging
from collections.abc import Awaitable, Callable
from typing import Any

from dishka import AsyncContainer
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser

from source.application.user import CreateUser
from source.core.schemas.user_schema import UserSchemaRequest, UserSchema
from source.application.user.get_by_id import GetUserSchemaById

class LoadUserMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]], 
        event: TelegramObject, 
        data: dict[str, Any]
    ):
        if not data.get("event_from_user"):
            return await handler(event, data)

        aiogram_user: TelegramUser = data["event_from_user"]
        
        try:
            # Manually get container from data dict
            # We assume it was passed in dp.feed_update(..., dishka_container=container)
            container: AsyncContainer = data["dishka_container"]
            get_user: GetUserSchemaById = await container.get(GetUserSchemaById)

            user = await get_user(str(aiogram_user.id))

            if not user:
                # If user does not exist, create them
                create_user: CreateUser = await container.get(CreateUser)
                user = await create_user(
                    UserSchemaRequest(
                        telegram_id=str(aiogram_user.id),
                        username=aiogram_user.username
                    )
                )
                logging.info(f"User {aiogram_user.id} created.")
            
            data["user"] = user
            return await handler(event, data)
                
        except Exception as e:
            logging.error(f"Error in LoadUserMiddleware for user {aiogram_user.id}: {e}", exc_info=True)
            # You might want to prevent access if the user can't be loaded/created
            return None # Or some error message