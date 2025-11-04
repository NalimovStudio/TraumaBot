from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from source.core.enum import UserType, SubscriptionType


class UserLogSchema(BaseModel):
    id: UUID = Field(..., description="ID записи лога в формате UUID")
    user_id: UUID = Field(..., description="ID пользователя из таблицы users")
    dialog_id: UUID = Field(..., description="dialog id")
    message_text: str = Field(..., description="Текст сообщения")
    created_at: datetime = Field(..., description="когда сообщение отправлено")

    class Config:
        from_attributes = True


class UserLogCreateSchema(BaseModel):
    user_id: UUID
    dialog_id: UUID = Field(..., description="dialog id")
    message_text: str


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

    messages_used: int = Field(0, description="Используемое количество сообщений")
    subscription_start: Optional[datetime] = Field(None, description="Начало подписки")
    daily_messages_used: int = Field(0, description="Количество сообщений в день")
    last_daily_reset: Optional[datetime] = Field(None, description="Последняя дата сброса сообщений")

    logging_requests: Optional[list[UserLogSchema]] = Field(None, description="массив со всеми запросами")

    # Добавленные поля для настроений и характеристик
    user_moods: Optional[list["UserMoodSchema"]] = Field(None, description="История настроений пользователя")
    user_characteristics: Optional[list["UserCharacteristicSchema"]] = Field(
        None,
        description="Характеристики пользователя"
    )

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


class UserMoodSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID записи настроения")
    user_id: UUID = Field(..., description="ID пользователя")
    mood: int = Field(..., ge=0, le=10, description="Настроение пользователя от 0 до 10")
    created_at: datetime = Field(..., description="Дата и время записи настроения")

    class Config:
        from_attributes = True


class UserCharacteristicSchema(BaseModel):
    id: Optional[UUID] = Field(None, description="ID характеристики")
    user_id: UUID = Field(..., description="ID пользователя")

    # [ mood_analysis ]
    current_mood: str = Field(..., description="Эмоциональное состояние на момент записи")
    mood_trend: str = Field(..., description="Динамика настроения")
    mood_stability: str = Field(..., description="Эмоциональная стабильность")

    # [ risk_assessment ]
    risk_group: str = Field(..., description="Группа риска")
    stress_level: str = Field(..., description="Уровень стресса")
    anxiety_level: str = Field(..., description="Уровень тревожности")

    # [ personality_traits ]
    strengths: list[str] = Field(default_factory=list, description="Положительные черты характера")
    weaknesses: list[str] = Field(default_factory=list, description="Негативные черты характера")
    communication_style: str = Field(..., description="Стиль коммуникации")

    personal_insights: list[str] = Field(default_factory=list, description="Психологические инсайты и склонности")
    recommendations: list[str] = Field(default_factory=list, description="Рекомендации")

    characteristic_accuracy: str = Field(..., description="Точность оценки ИИ в процентах")

    created_at: datetime = Field(..., description="Дата создания характеристики")
    updated_at: datetime = Field(..., description="Дата последнего обновления характеристики")

    class Config:
        from_attributes = True
