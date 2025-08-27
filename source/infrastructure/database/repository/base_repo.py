from typing import TypeVar, Generic, Type, Optional, Sequence
from uuid import UUID

from psycopg2 import IntegrityError

from pydantic import BaseModel as BaseModelSchema
from sqlalchemy import select, update, delete, Delete, Result
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, RelationshipProperty

from source.infrastructure.database.models.base_model import BaseModel

M = TypeVar("M", bound=BaseModel)
S = TypeVar("S", bound=BaseModelSchema)


class BaseRepository(Generic[M]):
    def __init__(self, model: Type[M], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_with_relationships(self, model_id: UUID) -> S:
        """Получение модели T со всеми отношениями."""
        # загрузка всех зависимостей
        relationships = [
            attr.key for attr in self.model.__mapper__.attrs
            if isinstance(attr, RelationshipProperty)  # проходит по всем ключам проверяя, RelationshipProperty ли это
        ]
        stmt = select(self.model).where(self.model.id == model_id)
        for rel in relationships:
            stmt = stmt.options(selectinload(getattr(self.model, rel)))

        result = await self.session.execute(stmt)
        model = result.scalars().first()

        if model is None:
            raise ValueError(f"{self.model.__name__} with id {model_id} not found")

        return model.get_schema()

    async def get_all(self) -> list[S]:
        stmt = select(self.model)

        result = await self.session.execute(stmt)
        models: Sequence[M] = result.scalars().all()

        if models is None:
            raise ValueError(f"{self.model.__name__} models not found")

        return [model.get_schema() for model in models]

    async def get_by_id(self, model_id: UUID) -> Optional[S]:
        stmt = select(self.model).where(self.model.id == model_id)

        result = await self.session.execute(stmt)
        model: M = result.scalars().first()

        if model is None:
            raise ValueError(f"{self.model.__name__} with id {model_id} not found")

        return model.get_schema()

    async def update(self, model_id: UUID, **values) -> S:
        """Обновление модели по **values"""
        stmt = (update(self.model)
                .where(self.model.id == model_id)
                .values(**values)
                .returning(self.model)
                )
        result = await self.session.execute(stmt)

        model: M = result.scalar_one_or_none()
        return model.get_schema()

    async def delete(self, model_id: UUID) -> None:
        stmt: Delete = delete(self.model).where(self.model.id == model_id)
        await self.session.execute(stmt)

    async def create(self, model_schema: S) -> S:
        """Создание модели model: M"""
        try:
            model: M = self.model.from_pydantic(schema=model_schema)
            self.session.add(model)
            await self.session.flush()
            await self.session.refresh(model)
            return model.get_schema()
        except IntegrityError:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            raise e

    async def merge(self, model: M) -> None:
        await self.session.merge(model)