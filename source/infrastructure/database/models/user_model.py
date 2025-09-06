from datetime import datetime
from typing import Optional, Type
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source.core.enum import SubscriptionType, UserType
from source.core.schemas.user_schema import UserSchema, UserDialogsLoggingSchema
from source.infrastructure.database.models.base_model import BaseModel, TimestampCreatedAtMixin, S


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

    @property
    def schema_class(cls) -> Type[S]:
        return UserSchema


class UserDialogsLogging(BaseModel, TimestampCreatedAtMixin):
    """Таблица для логирования сообщений в диалогах"""
    __tablename__ = "users_dialogs_logging"

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

    dialogue_id: Mapped[UUID] = mapped_column(postgresql.UUID(as_uuid=True), nullable=False, comment="ID сессии диалога")
    role: Mapped[str] = mapped_column(String, nullable=False, comment="Роль отправителя (user или assistant)")
    message_text: Mapped[str] = mapped_column(
        String,
        comment="Текст сообщения"
    )

    @property
    def schema_class(cls) -> Type[S]:
        return UserDialogsLoggingSchema
