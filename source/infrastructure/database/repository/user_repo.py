from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from source.core.schemas.user_schema import UserSchema
from source.infrastructure.database.models.user_model import User
from source.infrastructure.database.repository.base_repo import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(model=User, session=session)

    async def get_schema_by_telegram_id(self, telegram_id: str) -> UserSchema | None:
        stmt: Select = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        model: User = result.scalar_one_or_none()
        return model.get_schema() if model is not None else None

    async def get_model_by_telegram_id(self, telegram_id: str) -> User | None:
        stmt: Select = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()