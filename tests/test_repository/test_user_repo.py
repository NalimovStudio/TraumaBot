# test_user_repo.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from source.infrastructure.database.models.user_model import User


@pytest.mark.asyncio
async def test_get_by_telegram_id(user_repo, user_schema, mock_user_model):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalar_one_or_none.return_value = mock_user_model

    # Вызываем тестируемый метод
    result = await user_repo.get_by_telegram_id(user_schema.telegram_id)

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
    result = await user_repo.get_by_telegram_id(user_schema.telegram_id)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()

    # Проверяем результат
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id(user_repo, user_schema, mock_user_model):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.scalars.return_value.first.return_value = mock_user_model

    # Вызываем тестируемый метод
    result = await user_repo.get_by_id(1)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()
    mock_user_model.get_schema.assert_called_once()

    # Проверяем результат
    assert result == user_schema


@pytest.mark.asyncio
async def test_create(user_repo, user_schema, mock_user_model):
    with patch.object(user_repo.model, 'from_pydantic', return_value=mock_user_model) as mock_from_pydantic:
        # 2. Вызываем тестируемый метод
        result = await user_repo.create(user_schema)

        # 3. Проверяем вызовы
        # Проверяем, что from_pydantic был вызван с переданной схемой
        mock_from_pydantic.assert_called_once_with(schema=user_schema)

        # Проверяем, что model (наш mock_user_model_instance) был добавлен в сессию
        user_repo.session.add.assert_called_once_with(mock_user_model)

        # Проверяем, что commit был вызван
        user_repo.session.commit.assert_called_once()

        # Проверяем, что refresh был вызван с нашей моделью
        user_repo.session.refresh.assert_called_once_with(mock_user_model)

        # Проверяем, что get_schema был вызван на mock_user_model_instance
        mock_user_model.get_schema.assert_called_once()

        # 4. Проверяем результат
        assert result == user_schema


@pytest.mark.asyncio
async def test_update(user_repo, user_schema):
    # Создаем обновленную схему
    updated_user_schema = user_schema.copy(update={"username": "penis", "first_name": "govno"})

    # Создаем мок модели, которая будет возвращена из БД после UPDATE
    mock_updated_model = MagicMock()
    mock_updated_model.get_schema.return_value = updated_user_schema

    # Настраиваем мок execute
    mock_execute_result = MagicMock()
    mock_execute_result.scalar_one_or_none.return_value = mock_updated_model
    user_repo.session.execute.return_value = mock_execute_result

    # Вызываем тестируемый метод
    result = await user_repo.update(user_schema.id, username="penis", first_name="govno")

    # Проверяем вызов execute с правильным SQL statement
    user_repo.session.execute.assert_called_once()
    call_args = user_repo.session.execute.call_args[0][0]  # Получаем statement
    assert str(call_args).count("UPDATE") == 1  # Проверяем что это UPDATE

    # Проверяем вызов commit
    user_repo.session.commit.assert_called_once()

    # Проверяем что scalar_one_or_none был вызван
    mock_execute_result.scalar_one_or_none.assert_called_once()

    # Проверяем что get_schema был вызван у возвращенной модели
    mock_updated_model.get_schema.assert_called_once()

    # Проверяем конечный результат
    assert result == updated_user_schema
    assert result.username == "penis"
    assert result.first_name == "govno"

@pytest.mark.asyncio
async def test_delete(user_repo):
    # Настраиваем мок
    user_repo.session.execute.return_value = MagicMock()
    user_repo.session.execute.return_value.rowcount = 1

    # Вызываем тестируемый метод
    await user_repo.delete(1)

    # Проверяем вызовы
    user_repo.session.execute.assert_called_once()
    user_repo.session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_unique_violation(user_repo, user_schema):
    # Настраиваем мок для выброса исключения при нарушении уникальности
    from sqlalchemy.exc import IntegrityError
    user_repo.session.commit.side_effect = IntegrityError("", "", "")

    # Проверяем, что исключение пробрасывается
    with pytest.raises(IntegrityError):
        await user_repo.create(user_schema)

    # Проверяем, что был выполнен rollback
    user_repo.session.rollback.assert_called_once()
