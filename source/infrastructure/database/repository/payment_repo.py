from sqlalchemy import Select, select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from source.core.schemas.payment_schema import PaymentSchema
from source.infrastructure.database.models.payment_model import Payment
from source.infrastructure.database.repository.base_repo import BaseRepository
from source.infrastructure.database.repository.base_repo import S, M


class PaymentRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Payment, session=session)

    async def update_payment(self, purchase_id: int, **values) -> S:
        """Обновление модели по **values"""
        stmt = (update(self.model)
                .where(self.model.purchase_id == purchase_id)
                .values(**values)
                .returning(self.model)
                )
        result = await self.session.execute(stmt)

        model: Payment = result.scalar_one_or_none()
        return model.get_schema()

    async def get_by_purchase_id(self, purchase_id: str) -> PaymentSchema | None:
        stmt: Select = select(self.model).where(self.model.purchase_id == purchase_id)
        result = await self.session.execute(stmt)
        model: M = result.scalar_one_or_none()
        return model.get_schema()
