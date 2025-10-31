import logging
from typing import Any

from source.application.base import Interactor
from source.core.schemas.user_schema import UserMoodSchema
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork

logger = logging.getLogger(__name__)


class IsMoodSetToday(Interactor[str, bool]):  # TODO: in redis cache (24 hours expire)
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> bool | None:
        try:
            async with self.uow:
                is_mood_set: bool = await self.repository.is_mood_set_today(
                    telegram_id=telegram_id
                )
                return is_mood_set
        except Exception as exc:
            logger.error(f"Ошибка в интеракторе user_mood:\n{exc}")


class SetMood(Interactor[tuple[str, int], None]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, data: tuple[str, int]) -> None:
        telegram_id, mood = data
        try:
            async with self.uow:
                await self.repository.create_mood(
                    telegram_id=telegram_id,
                    mood_value=mood
                )
                await self.uow.commit()
        except Exception as exc:
            logger.error(f"Ошибка в интеракторе user_mood:\n{exc}")


class GetUserMoods(Interactor[Any, list[UserMoodSchema]]):  # TODO: in redis
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, *args: Any, **kwargs: Any) -> list[UserMoodSchema] | None:
        """Универсальная сигнатура, соответствующая базовому классу"""
        telegram_id = kwargs.get('telegram_id') or args[0]
        limit = kwargs.get('limit') or (args[1] if len(args) > 1 else None)

        try:
            async with self.uow:
                return await self.repository.get_recent_user_moods(
                    telegram_id=telegram_id,
                    limit=limit
                )
        except Exception as exc:
            logger.error(f"Ошибка в интеракторе user_mood:\n{exc}")
            return None
