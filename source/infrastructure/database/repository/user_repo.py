import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import Select, and_, insert
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from source.core.schemas.assistant_schemas import UserCharacteristicAssistantResponse
from source.core.schemas.user_schema import UserSchema, UserCharacteristicSchema, UserLogCreateSchema, UserLogSchema, \
    UserMoodSchema
from source.infrastructure.database.models.user_model import User, UserMood, UserCharacteristic, UserLog
from source.infrastructure.database.repository.base_repo import BaseRepository

logger = logging.getLogger(__name__)


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

    async def is_mood_set_today(self, telegram_id: str) -> bool:
        """Возвращает булевое значение оценивал ли настроение юзер или нет"""
        # Получаем начало и конец текущего дня в UTC
        now_utc = datetime.now(timezone.utc)
        start_of_day_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        end_of_day_utc = start_of_day_utc + timedelta(days=1)

        logger.info(f"Checking mood for user {telegram_id} today: {start_of_day_utc} — {end_of_day_utc}")

        stmt = (
            select(UserMood)
            .join(User, User.id == UserMood.user_id)
            .where(
                and_(
                    User.telegram_id == telegram_id,
                    UserMood.created_at >= start_of_day_utc,
                    UserMood.created_at < end_of_day_utc
                )
            )
            .order_by(UserMood.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_recent_user_moods(
            self,
            telegram_id: str,
            limit: int | None = None
    ) -> list[UserMoodSchema]:
        """Получить последние N настроений пользователя

        Args:
            limit: если None, то возвращает все записи
        """
        stmt = (
            select(UserMood)
            .join(User, UserMood.user_id == User.id)
            .where(User.telegram_id == telegram_id)
            .order_by(UserMood.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        moods: Sequence[UserMood] = result.scalars().all()
        return [mood.get_schema() for mood in moods]

    async def create_mood(self, telegram_id: str, mood_value: int) -> UserMood | None:
        """Записать настроение юзера"""
        if not (0 <= mood_value <= 10):
            raise ValueError("Mood value must be between 0 and 10")

        # Создаем подзапрос для получения user_id
        user_subquery = (
            select(User.id)
            .where(User.telegram_id == telegram_id)
            .scalar_subquery()
        )

        # Создаем запрос INSERT с RETURNING
        stmt = (
            insert(UserMood)
            .values(
                user_id=user_subquery,
                mood=mood_value
            )
            .returning(UserMood)
        )

        try:
            result = await self.session.execute(stmt)
            user_mood = result.scalar_one()
            await self.session.flush()
            return user_mood

        except Exception as exc:
            # Если пользователь не найден или другие ошибки
            if "violates foreign key constraint" in str(exc).lower():
                raise ValueError(f"User with telegram_id {telegram_id} not found")
            raise exc

    async def get_user_characteristics(self, telegram_id: str) -> list[UserCharacteristicSchema] | None:
        """Возвращает записи характеристики юзера"""

        stmt = (
            select(UserCharacteristic)
            .join(UserCharacteristic.user)
            .where(User.telegram_id == telegram_id)
            .order_by(desc(UserCharacteristic.created_at))
        )

        result = await self.session.execute(stmt)
        user_characteristics: Sequence[UserCharacteristic] = result.scalars().all()

        if user_characteristics:
            return [characteristic.get_schema() for characteristic in user_characteristics]
        return None

    async def put_user_characteristic(
            self,
            user_characteristics: UserCharacteristicAssistantResponse,
            user_id: uuid.UUID
    ) -> UserCharacteristicSchema:
        """Записать характеристику юзера"""
        # Получаем данные от AI
        characteristic_data = user_characteristics.model_dump()

        # Добавляем системные поля
        characteristic_data.update({
            'user_id': user_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })

        # Создаем и сохраняем запись в БД
        db_characteristic = UserCharacteristic(**characteristic_data)
        self.session.add(db_characteristic)
        await self.session.flush()
        await self.session.refresh(db_characteristic)

        # Возвращаем полную схему
        return UserCharacteristicSchema.model_validate(db_characteristic)

    async def create_user_log(self, user_log: UserLogCreateSchema) -> UserLogSchema | None:
        """Создает запись лога пользователя"""
        try:
            log_data = user_log.model_dump()
            db_log = UserLog(**log_data)
            self.session.add(db_log)
            await self.session.flush()
            await self.session.refresh(db_log)
            return UserLogSchema.model_validate(db_log)
        except Exception as exc:
            logger.error(f"Error creating user log: {exc}")
            await self.session.rollback()
            return None

    async def get_user_logs(self, telegram_id: str, days: int | None = None) -> list[UserLogSchema] | None:
        """Получает логи пользователя по telegram_id

        Args:
            telegram_id: ID пользователя в Telegram
            days: количество дней для фильтрации (берет логи за последние N дней включительно).
                  Если None - возвращает все логи
        """
        user = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            return None

        query = select(UserLog).where(UserLog.user_id == user.id)

        # Если указано количество дней, фильтруем по дате
        if days is not None:
            from datetime import datetime, timedelta
            start_date = datetime.now() - timedelta(days=days)
            query = query.where(UserLog.created_at >= start_date)

        # Сортируем по дате создания (сначала новые)
        query = query.order_by(UserLog.created_at.desc())

        logs = await self.session.execute(query)
        logs = logs.scalars().all()

        return [UserLogSchema.model_validate(log) for log in logs] if logs else None
