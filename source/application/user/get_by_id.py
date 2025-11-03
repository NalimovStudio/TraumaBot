import logging
from typing import TypeVar

from pydantic import BaseModel as BaseModelSchema

from source.application.base import Interactor
from source.core.schemas.user_schema import UserSchema
from source.infrastructure.database.models.user_model import User
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork

S = TypeVar("S", bound=BaseModelSchema)

logger = logging.getLogger(__name__)


class GetUserSchemaById(Interactor[str, UserSchema]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> UserSchema | None:
        try:
            async with self.uow:
                user: UserSchema = await self.repository.get_schema_by_telegram_id(
                    telegram_id
                )
                return user
        except Exception as exc:
            logger.error(f"Error get_by_id.py:\n{exc}")


class GetUserById(Interactor[str, User]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> User | None:
        try:
            async with self.uow:
                user = await self.repository.get_model_by_telegram_id(
                    telegram_id
                )
                return user
        except Exception as exc:
            logger.error(f"Error get_by_id.py:\n{exc}")
