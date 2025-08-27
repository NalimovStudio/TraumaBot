from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from source.core.enum import SubscriptionType

class PaymentSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID пользователя в формате UUID")

    purchase_id: str = Field(..., description="ID Заказа")

    telegram_id: str = Field(..., description="Телеграм айди в формате строки")
    username: str = Field(..., description="Телеграм юзернейм")

    amount: int = Field(..., description="Цена за заказ")
    month_sub: int = Field(..., description="Время подписки")
    description: str = Field(..., description="Описание заказа")
    status: str = Field(..., description="Статус заказа")
    subscription: SubscriptionType = Field(..., description="тип подписки")
    link: str = Field(..., description="Ссылка для оплаты заказа")

    timestamp: datetime = Field(..., description="Время покупки")
