import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from source.core.enum import SubscriptionType, UserType
from source.core.schemas.user_schema import (
    UserSchema,
    UserMoodSchema,
    UserCharacteristicSchema,
    UserLogSchema,
    UserLogCreateSchema
)
from source.infrastructure.database.models.user_model import User, UserMood, UserCharacteristic, UserLog
from source.infrastructure.database.repository.user_repo import UserRepository


@pytest.fixture
def mock_session():
    """Мок сессии базы данных"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def user_repo(mock_session):
    """Фикстура репозитория пользователя"""
    return UserRepository(session=mock_session)


@pytest.fixture
def user_id():
    """ID пользователя"""
    return uuid4()


@pytest.fixture
def telegram_id():
    """Telegram ID пользователя"""
    return "123456789"


@pytest.fixture
def user_schema(user_id, telegram_id):
    """Схема пользователя"""
    return UserSchema(
        id=user_id,
        telegram_id=telegram_id,
        username="test_user",
        first_name="Test",
        last_name="User",
        user_type=UserType.USER,
        subscription=SubscriptionType.FREE,
        dialogs_completed_today=0,
        dialogs_completed=0,
        messages_used=0,
        daily_messages_used=0,
        subscription_date_end=None,
        subscription_start=None,
        last_daily_reset=None
    )


@pytest.fixture
def mock_user_model(user_schema):
    """Мок модели пользователя"""
    mock_model = MagicMock(spec=User)
    mock_model.id = user_schema.id
    mock_model.telegram_id = user_schema.telegram_id
    mock_model.username = user_schema.username
    mock_model.first_name = user_schema.first_name
    mock_model.last_name = user_schema.last_name
    mock_model.user_type = user_schema.user_type
    mock_model.subscription = user_schema.subscription
    mock_model.get_schema = MagicMock(return_value=user_schema)
    return mock_model


@pytest.fixture
def user_mood_schema(user_id):
    """Схема настроения пользователя"""
    return UserMoodSchema(
        id=uuid4(),
        user_id=user_id,
        mood=5,
        created_at=datetime.now()
    )


@pytest.fixture
def mock_user_mood(user_mood_schema):
    """Мок модели настроения пользователя"""
    mock_mood = MagicMock(spec=UserMood)
    mock_mood.id = user_mood_schema.id
    mock_mood.user_id = user_mood_schema.user_id
    mock_mood.mood = user_mood_schema.mood
    mock_mood.created_at = user_mood_schema.created_at
    mock_mood.get_schema = MagicMock(return_value=user_mood_schema)
    return mock_mood


@pytest.fixture
def user_characteristic_schema(user_id):
    """Схема характеристики пользователя"""
    return UserCharacteristicSchema(
        id=uuid4(),
        user_id=user_id,
        current_mood="neutral",
        mood_trend="stable",
        mood_stability="high",
        risk_group="low",
        stress_level="medium",
        anxiety_level="low",
        strengths=["communicative", "analytical"],
        weaknesses=["impulsive"],
        communication_style="direct",
        personal_insights=["tends to overthink"],
        recommendations=["practice mindfulness"],
        characteristic_accuracy="85%",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def mock_user_characteristic(user_characteristic_schema):
    """Мок модели характеристики пользователя"""
    mock_char = MagicMock(spec=UserCharacteristic)
    mock_char.id = user_characteristic_schema.id
    mock_char.user_id = user_characteristic_schema.user_id
    mock_char.current_mood = user_characteristic_schema.current_mood
    mock_char.mood_trend = user_characteristic_schema.mood_trend
    mock_char.mood_stability = user_characteristic_schema.mood_stability
    mock_char.risk_group = user_characteristic_schema.risk_group
    mock_char.stress_level = user_characteristic_schema.stress_level
    mock_char.anxiety_level = user_characteristic_schema.anxiety_level
    mock_char.strengths = user_characteristic_schema.strengths
    mock_char.weaknesses = user_characteristic_schema.weaknesses
    mock_char.communication_style = user_characteristic_schema.communication_style
    mock_char.personal_insights = user_characteristic_schema.personal_insights
    mock_char.recommendations = user_characteristic_schema.recommendations
    mock_char.characteristic_accuracy = user_characteristic_schema.characteristic_accuracy
    mock_char.created_at = user_characteristic_schema.created_at
    mock_char.updated_at = user_characteristic_schema.updated_at
    mock_char.get_schema = MagicMock(return_value=user_characteristic_schema)
    return mock_char


@pytest.fixture
def user_log_create_schema(user_id):
    """Схема создания лога пользователя"""
    return UserLogCreateSchema(
        user_id=user_id,
        dialog_id=uuid4(),
        message_text="Test message"
    )


@pytest.fixture
def user_log_schema(user_log_create_schema):
    """Схема лога пользователя"""
    return UserLogSchema(
        id=uuid4(),
        user_id=user_log_create_schema.user_id,
        dialog_id=user_log_create_schema.dialog_id,
        message_text=user_log_create_schema.message_text,
        created_at=datetime.now()
    )


@pytest.fixture
def mock_user_log(user_log_schema):
    """Мок модели лога пользователя - ИСПРАВЛЕННЫЙ"""
    mock_log = MagicMock(spec=UserLog)

    # Устанавливаем ВСЕ атрибуты из схемы
    for field, value in user_log_schema.model_dump().items():
        setattr(mock_log, field, value)

    # Убедимся что основные атрибуты установлены
    mock_log.id = user_log_schema.id
    mock_log.user_id = user_log_schema.user_id
    mock_log.dialog_id = user_log_schema.dialog_id
    mock_log.message = user_log_schema.message_text  # Обратите внимание: в модели поле 'message', в схеме 'message_text'
    mock_log.created_at = user_log_schema.created_at

    # Настраиваем метод для преобразования в схему
    mock_log.get_schema = MagicMock(return_value=user_log_schema)

    return mock_log


@pytest.fixture
def mock_user():
    """Мок пользователя для тестов логов"""
    mock_user = MagicMock(spec=User)
    mock_user.id = uuid4()
    mock_user.telegram_id = "123456789"
    return mock_user


# Фикстуры для асинхронного выполнения тестов
@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр цикла событий по умолчанию для тестовой сессии"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    return 'asyncio'


# Дополнительные утилитарные фикстуры
@pytest.fixture
def datetime_now():
    """Фикстура для текущего времени"""
    return datetime.now()


@pytest.fixture
def sample_uuid():
    """Фикстура для sample UUID"""
    return uuid4()


@pytest.fixture
def sample_telegram_ids():
    """Фикстура для sample Telegram IDs"""
    return ["123456789", "987654321", "555555555"]


@pytest.fixture
def sample_mood_values():
    """Фикстура для sample значений настроения"""
    return [0, 5, 10, 3, 7]


# Фикстуры для тестирования ошибок
@pytest.fixture
def integrity_error():
    """Фикстура для ошибки целостности"""
    from sqlalchemy.exc import IntegrityError
    return IntegrityError("violates foreign key constraint", {}, None)


@pytest.fixture
def value_error():
    """Фикстура для ошибки значения"""
    return ValueError("Invalid value")


# Фикстуры для тестирования разных сценариев подписки
@pytest.fixture
def premium_user_schema(user_schema):
    """Схема пользователя с премиум подпиской"""
    return user_schema.copy(update={
        "subscription": SubscriptionType.PRO,
        "subscription_date_end": datetime(2024, 12, 31)
    })


@pytest.fixture
def free_user_schema(user_schema):
    """Схема пользователя с бесплатной подпиской"""
    return user_schema.copy(update={
        "subscription": SubscriptionType.FREE,
        "subscription_date_end": None
    })
