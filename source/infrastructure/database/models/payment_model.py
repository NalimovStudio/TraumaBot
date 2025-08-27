from datetime import datetime
from typing import Optional, Type

from sqlalchemy import String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from source.core.enum import SubscriptionType
from source.core.schemas.payment_schema import PaymentSchema
from source.infrastructure.database.models.base_model import BaseModel, TimestampCreatedAtMixin, S


class PaymentLogs(BaseModel):
    __tablename__="paymentlogs"

    purchase_id: Mapped[str] = mapped_column(String, comment="ID Заказа", unique=True)

    telegram_id: Mapped[str] = mapped_column(String, comment="telegram id")
    username: Mapped[str] = mapped_column(String, comment="telegram username")

    amount: Mapped[int] = mapped_column(Integer, comment="Цена за заказ")
    month_sub: Mapped[int] = mapped_column(Integer, comment="Время подписки")
    description: Mapped[str] = mapped_column(String, comment="Описание заказа")
    status: Mapped[str] = mapped_column(String, comment="Статус заказа")
    subscription: Mapped[SubscriptionType] = mapped_column(
        postgresql.ENUM(SubscriptionType, name="subscription_type_enum", create_type=True),
        default=SubscriptionType.FREE,
        nullable=False,
        comment="Тип подписки пользователя"
    )
    link: Mapped[str] = mapped_column(String, comment="Ссылка для оплаты заказа")

    timestamp: Mapped[datetime] = mapped_column(DateTime, comment="Время покупки")


    @property
    def schema_class(cls) -> Type[S]:
        return PaymentSchema