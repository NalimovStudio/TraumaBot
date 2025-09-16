from datetime import datetime
from typing import Optional, Type

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source.core.enum import SubscriptionType, UserType
from source.core.schemas.user_schema import UserSchema, UserDialogsLoggingSchema, UserCharacteristicSchema
from source.infrastructure.database.models.base_model import BaseModel, TimestampCreatedAtMixin, S, \
    TimestampUpdatedAtMixin


class User(BaseModel):
    __tablename__ = "users"

    telegram_id: Mapped[str] = mapped_column(String, comment="telegram id", unique=True)
    username: Mapped[str] = mapped_column(String, comment="telegram username")
    first_name: Mapped[Optional[str]] = mapped_column(String, comment="telegram first name")
    last_name: Mapped[Optional[str]] = mapped_column(String, comment="telegram last name")

    dialogs_completed_today: Mapped[Optional[int]] = mapped_column(Integer, comment="Количество завершенных диалогов сегодня")
    dialogs_completed: Mapped[Optional[int]] = mapped_column(Integer, default=0, comment="Количество завершенных диалогов за все время")

    user_type: Mapped[UserType] = mapped_column(
        postgresql.ENUM(UserType, name="user_type_enum", create_type=True),
        default=UserType.USER,
        nullable=False,
        comment="Тип пользователя"
    )

    subscription: Mapped[SubscriptionType] = mapped_column(
        postgresql.ENUM(SubscriptionType, name="subscription_type_enum", create_type=True),
        default=SubscriptionType.FREE,
        nullable=False,
        comment="Тип подписки пользователя"
    )
    subscription_date_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    messages_used: Mapped[int] = mapped_column(Integer, default=0, comment="Количество использованных сообщений в текущем периоде подписки (для STANDARD)")
    subscription_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="Дата начала текущей подписки")

    daily_messages_used: Mapped[int] = mapped_column(Integer, default=0, comment="Daily использованные сообщения (для FREE)")
    last_daily_reset: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), comment="Дата последнего daily reset (для FREE)")

    logging_requests: Mapped[list["UserDialogsLogging"]] = relationship(
        "UserDialogsLogging",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    user_moods: Mapped[list["UserMood"]] = relationship(
        "UserMood",
        back_populates="user",
        lazy="selectin"
    )

    user_characteristics: Mapped[list["UserCharacteristic"]] = relationship(
        "UserCharacteristic",
        back_populates="user",
        lazy="selectin"
    )

    @property
    def schema_class(cls) -> Type[S]:
        return UserSchema


class UserDialogsLogging(BaseModel, TimestampCreatedAtMixin):
    """Таблица с прошлыми диалогами"""
    __tablename__ = "user_dialogs_logging"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="ID пользователя, совершившего запрос"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="logging_requests",
        lazy="selectin"
    )

    message: Mapped[str] = mapped_column(
        String,
        comment="Сообщение юзера"
    )

    @property
    def schema_class(cls) -> Type[S]:
        return UserDialogsLoggingSchema


class UserMood(BaseModel, TimestampCreatedAtMixin):
    """Таблица с настроением юзера"""
    __tablename__ = "user_mood"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="ID пользователя, совершившего запрос"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="logging_requests",
        lazy="selectin"
    )

    mood: Mapped[int] = mapped_column(Integer, comment="Настроение юзера от 0 до 10")


class UserCharacteristic(BaseModel, TimestampCreatedAtMixin, TimestampUpdatedAtMixin):
    """
    Таблица с характеристикой юзера.

    Отношения:
    — User (by users.id)
    — UserMood (by user_mood.id)
    """

    __tablename__ = "user_characteristic"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="ID пользователя, совершившего запрос"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="logging_requests",
        lazy="selectin"
    )

    # mood_analysis
    current_mood: Mapped[str] = mapped_column(String(50), comment="эмоциональное состояние на момент записи")
    mood_trend: Mapped[str] = mapped_column(String(50), comment="динамика настроения (если есть прошлые записи)")
    mood_stability: Mapped[str] = mapped_column(String(50), comment="эмоциональная стабильность")  # для оценки ПРЛ важный столбец, например

    # risk_assessment
    risk_group: Mapped[str] = mapped_column(String(50), comment="группа риска")
    stress_level: Mapped[str] = mapped_column(String(50), comment="уровень стресса")
    anxiety_level: Mapped[str] = mapped_column(String(50), comment="уровень тревожности")

    # personality_traits
    strengths: Mapped[list[str]] = mapped_column(ARRAY, comment="положительные трейты")
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY, comment="негативные трейты")
    communication_style: Mapped[str] = mapped_column(String(150), comment="стиль коммуникации")

    personal_insights: Mapped[list[str]] = mapped_column(ARRAY, comment="склонности к..")
    recommendations: Mapped[list[str]] = mapped_column(ARRAY, comment="рекомендации массив")

    characteristic_accuracy: Mapped[str] = mapped_column(String(10), comment="насколько точная была оценка ИИ в процентах")

    @property
    def schema_class(cls) -> Type[S]:
        return UserCharacteristicSchema
