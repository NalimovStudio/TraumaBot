from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel as BaseModelSchema


from source.application.base import Interactor
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork

S = TypeVar("S", bound=BaseModelSchema)


class GetUserSchemaById(Interactor[str, S]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork): 
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> S:
        try:
            async with self.uow:
                user = await self.repository.get_by_telegram_id(
                    telegram_id
                )
                await self.uow.commit() 
                return user
        except Exception as exc:
            pass 

class GetUserById(Interactor[str, S]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork): 
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> S:
        try:
            async with self.uow:
                user = await self.repository.get_model_by_telegram_id(
                    telegram_id
                )
                await self.uow.commit() 
                return user
        except Exception as exc:
            pass 