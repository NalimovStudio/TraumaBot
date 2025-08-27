from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from source.core.enum import UserType, SubscriptionType


class UserDialogsLoggingSchema(BaseModel):
    id: UUID = Field(..., description="ID диалога в формате UUID")
    user_id: UUID = Field(..., description="ID юзера в формате UUID")
    messages: list[str] = Field(..., description="Массив сообщений в диалоге")
    created_at: datetime = Field(..., description="когда сообщение отправлено")

    class Config:
        from_attributes = True


class UserSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID пользователя в формате UUID")

    telegram_id: str = Field(..., description="Телеграм айди в формате строки")
    username: str = Field(..., description="Телеграм юзернейм")
    first_name: Optional[str] = Field(None, description="Телеграм имя")
    last_name: Optional[str] = Field(None, description="Телеграм фамилия")

    dialogs_completed_today: Optional[int] = Field(0, description="сколько было диалогов сегодня")
    dialogs_completed: int = Field(..., description="сколько было диалогов в общем")

    user_type: UserType = Field(..., description="тип пользователя")

    subscription: SubscriptionType = Field(..., description="тип подписки")
    subscription_date_end: Optional[datetime] = Field(None, description="когда кончится подписка")

    messages_used: int = Field(0, description="Использумое количество сообщений")
    subscription_start: Optional[datetime] = Field(None, description="Начало подписки")
    daily_messages_used: int = Field(0, description="Количество сообщений в день")
    last_daily_reset: Optional[datetime] = Field(None, description="Последнея дата сброса сообщений")

    logging_requests: Optional[list[UserDialogsLoggingSchema]] = Field(None, description="массив со всеми запросами")

    class Config:
        from_attributes = True


class UserSchemaRequest(BaseModel):
    """Схема для создания юзера или обновления данных о юзере"""
    telegram_id: str = Field(..., description="Телеграм айди в формате строки")
    username: str = Field(..., description="Телеграм юзернейм")
    first_name: Optional[str] = Field(None, description="Телеграм имя")
    last_name: Optional[str] = Field(None, description="Телеграм фамилия")

    class Config:
        from_attributes = True
