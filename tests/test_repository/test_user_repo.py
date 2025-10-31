# test_user_repo.py
import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from source.core.schemas.user_schema import UserMoodSchema, UserCharacteristicSchema, UserLogSchema
from source.infrastructure.database.models.user_model import UserLog


@pytest.mark.asyncio
async def test_get_by_telegram_id(user_repo, user_schema, mock_user_model):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = mock_user_model

    # Вызываем тестируемый метод
    result = await user_repo.get_schema_by_telegram_id(user_schema.telegram_id)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()
    mock_user_model.get_schema.assert_called_once()

    # Проверяем результат
    assert result == user_schema
    assert result.telegram_id == user_schema.telegram_id


@pytest.mark.asyncio
async def test_get_by_telegram_id_returns_none(user_repo, user_schema):
    # Настраиваем мок для возврата None
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = None

    # Вызываем тестируемый метод
    result = await user_repo.get_schema_by_telegram_id(user_schema.telegram_id)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_get_model_by_telegram_id(user_repo, mock_user_model):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = mock_user_model

    # Вызываем тестируемый метод
    result = await user_repo.get_model_by_telegram_id("test_telegram_id")

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()

    # Проверяем результат
    assert result == mock_user_model


@pytest.mark.asyncio
async def test_get_model_by_telegram_id_returns_none(user_repo):
    # Настраиваем мок для возврата None
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = None

    # Вызываем тестируемый метод
    result = await user_repo.get_model_by_telegram_id("non_existent_id")

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_is_mood_set_today_true(user_repo, mock_user_mood):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = mock_user_mood

    # Вызываем тестируемый метод
    result = await user_repo.is_mood_set_today("test_telegram_id")

    # Проверяем результат
    assert result is True
    user_repo.session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_is_mood_set_today_false(user_repo):
    # Настраиваем мок для возврата None
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = None

    # Вызываем тестируемый метод
    result = await user_repo.is_mood_set_today("test_telegram_id")

    # Проверяем результат
    assert result is False


@pytest.mark.asyncio
async def test_get_recent_user_moods_with_limit(user_repo, mock_user_mood):
    # Настраиваем мок
    mock_moods = [mock_user_mood, mock_user_mood]
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.all.return_value = mock_moods

    # Вызываем тестируемый метод
    result = await user_repo.get_recent_user_moods("test_telegram_id", limit=2)

    # Проверяем результат
    assert len(result) == 2
    assert all(isinstance(item, UserMoodSchema) for item in result)
    user_repo.session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_user_moods_no_limit(user_repo, mock_user_mood):
    # Настраиваем мок
    mock_moods = [mock_user_mood]
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.all.return_value = mock_moods

    # Вызываем тестируемый метод
    result = await user_repo.get_recent_user_moods("test_telegram_id", limit=None)

    # Проверяем результат
    assert len(result) == 1
    user_repo.session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_user_moods_empty(user_repo):
    # Настраиваем мок для пустого результата
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.all.return_value = []

    # Вызываем тестируемый метод
    result = await user_repo.get_recent_user_moods("test_telegram_id")

    # Проверяем результат
    assert result == []


@pytest.mark.asyncio
async def test_create_mood_success(user_repo, mock_user_mood):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one.return_value = mock_user_mood

    # Вызываем тестируемый метод
    result = await user_repo.create_mood("test_telegram_id", 5)

    # Проверяем результат
    assert result == mock_user_mood
    user_repo.session.execute.assert_called_once()
    user_repo.session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_mood_invalid_value(user_repo):
    # Проверяем, что исключение выбрасывается при невалидном значении
    with pytest.raises(ValueError, match="Mood value must be between 0 and 10"):
        await user_repo.create_mood("test_telegram_id", 15)


@pytest.mark.asyncio
async def test_create_mood_user_not_found(user_repo):
    # Настраиваем мок для выброса исключения
    user_repo.session.execute.side_effect = Exception("violates foreign key constraint")

    # Проверяем, что исключение выбрасывается
    with pytest.raises(ValueError, match="User with telegram_id test_telegram_id not found"):
        await user_repo.create_mood("test_telegram_id", 5)


@pytest.mark.asyncio
async def test_get_user_characteristics_success(user_repo, mock_user_characteristic):
    # Настраиваем мок
    mock_characteristics = [mock_user_characteristic]
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.all.return_value = mock_characteristics

    # Вызываем тестируемый метод
    result = await user_repo.get_user_characteristics("test_telegram_id")

    # Проверяем результат
    assert len(result) == 1
    assert all(isinstance(item, UserCharacteristicSchema) for item in result)
    user_repo.session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_characteristics_empty(user_repo):
    # Настраиваем мок для пустого результата
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.all.return_value = []

    # Вызываем тестируемый метод
    result = await user_repo.get_user_characteristics("test_telegram_id")

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_create_user_characteristics_success(user_repo, user_characteristic_schema, mock_user_characteristic):
    """Тест успешного создания характеристики пользователя"""
    # Настраиваем мок сессии
    user_repo.session.add = MagicMock()
    user_repo.session.flush = AsyncMock()
    user_repo.session.refresh = AsyncMock()

    # Создаем тестовые данные
    user_id = uuid.uuid4()
    test_user_characteristics = user_characteristic_schema

    # Патчим создание модели чтобы вернуть наш мок
    with patch('source.infrastructure.database.repository.user_repo.UserCharacteristic') as mock_char_class:
        mock_char_class.return_value = mock_user_characteristic

        # Вызываем тестируемый метод с правильными параметрами
        result = await user_repo.put_user_characteristic(
            user_characteristics=test_user_characteristics,
            user_id=user_id
        )

    # Проверяем что модель была создана с правильными данными
    expected_data = test_user_characteristics.model_dump()
    expected_data.update({
        'user_id': user_id,
        'created_at': unittest.mock.ANY,  # datetime.now() будет вызываться
        'updated_at': unittest.mock.ANY  # datetime.now() будет вызываться
    })

    mock_char_class.assert_called_once_with(**expected_data)

    # Проверяем вызовы сессии
    user_repo.session.add.assert_called_once_with(mock_user_characteristic)
    user_repo.session.flush.assert_called_once()
    user_repo.session.refresh.assert_called_once_with(mock_user_characteristic)

    # Проверяем результат
    assert result == test_user_characteristics


@pytest.mark.asyncio
async def test_create_user_log_success(user_repo, user_log_create_schema, user_log_schema):
    """Тест успешного создания лога пользователя"""
    # Настраиваем мок сессии
    user_repo.session.add = MagicMock()
    user_repo.session.flush = AsyncMock()
    user_repo.session.refresh = AsyncMock()

    # Создаем реальный объект UserLog
    log_data = user_log_create_schema.model_dump()
    real_user_log = UserLog(**log_data)
    real_user_log.id = user_log_schema.id
    real_user_log.created_at = user_log_schema.created_at

    # Патчим создание модели
    with patch('source.infrastructure.database.repository.user_repo.UserLog', return_value=real_user_log):
        # Вызываем тестируемый метод
        result = await user_repo.create_user_log(user_log_create_schema)

    # Проверяем вызовы
    user_repo.session.add.assert_called_once_with(real_user_log)
    user_repo.session.flush.assert_called_once()
    user_repo.session.refresh.assert_called_once_with(real_user_log)

    # Проверяем результат
    assert result == user_log_schema


@pytest.mark.asyncio
async def test_get_user_logs_success(user_repo, mock_user, mock_user_log):
    # Настраиваем моки
    user_repo.session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),  # Первый вызов - поиск пользователя
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_user_log]))))
        # Второй вызов - логи
    ]

    # Вызываем тестируемый метод
    result = await user_repo.get_user_logs("test_telegram_id")

    # Проверяем результат
    assert len(result) == 1
    assert all(isinstance(item, UserLogSchema) for item in result)
    assert user_repo.session.execute.call_count == 2


@pytest.mark.asyncio
async def test_get_user_logs_user_not_found(user_repo):
    # Настраиваем мок для возврата None при поиске пользователя
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = None

    # Вызываем тестируемый метод
    result = await user_repo.get_user_logs("non_existent_telegram_id")

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_get_user_logs_empty(user_repo, mock_user):
    # Настраиваем моки
    user_repo.session.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user)),  # Пользователь найден
        MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))))  # Логов нет
    ]

    # Вызываем тестируемый метод
    result = await user_repo.get_user_logs("test_telegram_id")

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_create(user_repo, user_schema, mock_user_model):
    with patch.object(user_repo.model, 'from_pydantic', return_value=mock_user_model) as mock_from_pydantic:
        # Вызываем тестируемый метод
        result = await user_repo.create(user_schema)

        # Проверяем вызовы
        mock_from_pydantic.assert_called_once_with(schema=user_schema)
        user_repo.session.add.assert_called_once_with(mock_user_model)
        user_repo.session.refresh.assert_called_once_with(mock_user_model)
        mock_user_model.get_schema.assert_called_once()

        # Проверяем результат
        assert result == user_schema


@pytest.mark.asyncio
async def test_update(user_repo, user_schema):
    # Создаем обновленную схему
    updated_user_schema = user_schema.copy(update={"username": "updated_username", "first_name": "updated_first_name"})

    # Создаем мок модели, которая будет возвращена из БД после UPDATE
    mock_updated_model = MagicMock()
    mock_updated_model.get_schema.return_value = updated_user_schema

    # Настраиваем мок execute
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_updated_model
    user_repo.session.execute.return_value = mock_execute_result

    # Вызываем тестируемый метод
    result = await user_repo.update(user_schema.id, username="updated_username", first_name="updated_first_name")

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()
    mock_execute_result.scalar_one_or_none.assert_called_once()
    mock_updated_model.get_schema.assert_called_once()

    # Проверяем результат
    assert result == updated_user_schema
    assert result.username == "updated_username"
    assert result.first_name == "updated_first_name"


@pytest.mark.asyncio
async def test_delete(user_repo):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.rowcount = 1

    # Вызываем тестируемый метод
    await user_repo.delete(1)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_unique_violation(user_repo, user_schema):
    # Настраиваем мок для выброса исключения при нарушении уникальности
    user_repo.session.refresh.side_effect = IntegrityError("", "", "")

    # Проверяем, что исключение пробрасывается
    with pytest.raises(IntegrityError):
        await user_repo.create(user_schema)

    # Проверяем, что был выполнен rollback
    user_repo.session.rollback.assert_called_once()
