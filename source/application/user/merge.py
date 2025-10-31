from typing import TypeVar

from pydantic import BaseModel as BaseModelSchema

from source.application.base import Interactor
from source.infrastructure.database.models.user_model import User
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork

S = TypeVar("S", bound=BaseModelSchema)


class MergeUser(Interactor[User, S]):
    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, user: User) -> None:
        try:
            async with self.uow:
                user = await self.repository.merge(
                    user
                )
                await self.uow.commit()
                return user
        except Exception as exc:
            pass
