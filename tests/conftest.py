# conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from source.core.enum import UserType, SubscriptionType
from source.infrastructure.database.models.user_model import User


@pytest.fixture(scope="session")
def event_loop():
    """Фикстура для event loop"""
    import asyncio
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


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
    """Репозиторий с моковой сессией"""
    from source.infrastructure.database.repository.user_repo import UserRepository
    return UserRepository(session=mock_session)


@pytest.fixture
def user_schema():
    """Фикстура пользователя"""
    from source.core.schemas.user_schema import UserSchema
    return UserSchema(
        telegram_id="1488",
        username="sperma",
        dialogs_completed=0,
        user_type=UserType.USER,
        subscription=SubscriptionType.FREE
    )


@pytest.fixture
def mock_user_model(user_schema):
    """Мок модели User с методом get_schema"""
    mock_model = MagicMock(spec=User)
    mock_model.id = user_schema.id # Пример, если id нужен для refresh или других операций
    mock_model.get_schema.return_value = user_schema
    return mock_model
