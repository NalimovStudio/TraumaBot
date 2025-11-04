from typing import TypeVar

from pydantic import BaseModel as BaseModelSchema

from source.application.base import Interactor
from source.core.schemas.payment_schema import PaymentSchema
from source.infrastructure.database.repository import PaymentRepository
from source.infrastructure.database.uow import UnitOfWork

S = TypeVar("S", bound=BaseModelSchema)


class MergePayment(Interactor[PaymentSchema, S]):
    def __init__(self, repository: PaymentRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, payment: PaymentSchema) -> None:
        try:
            async with self.uow:
                payment = await self.repository.merge(
                    payment
                )
                await self.uow.commit()
                return payment
        except Exception as exc:
            pass
