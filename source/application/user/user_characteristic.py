import uuid
from datetime import datetime

from source.application.base import Interactor
from source.core.lexicon.rules import MIN_DAYS_AFTER_LAST_CHARACTERISTIC_GENERATION
from source.core.schemas.assistant_schemas import UserCharacteristicAssistantResponse
from source.core.schemas.user_schema import UserCharacteristicSchema
from source.infrastructure.database.models.base_model import S
from source.infrastructure.database.models.user_model import User
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork


class GetUserCharacteristics(Interactor[User, S]):
    """Возвращает последнюю характеристику если есть"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> list[UserCharacteristicSchema] | None:
        try:
            async with self.uow:
                characteristics: list[UserCharacteristicSchema] | None = await self.repository.get_user_characteristics(
                    telegram_id=telegram_id
                )
                return characteristics
        except Exception as exc:
            pass


class PutGeneratedUserCharacteristic(
    Interactor[tuple[uuid.UUID, UserCharacteristicSchema], UserCharacteristicSchema | None]):
    """Записывает характеристику юзера"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self,
                       data: tuple[uuid.UUID, UserCharacteristicAssistantResponse]) -> UserCharacteristicSchema | None:
        try:
            user_id, generated_characteristic = data
            async with self.uow:
                characteristic: UserCharacteristicSchema | None = await self.repository.put_user_characteristic(
                    user_characteristics=generated_characteristic,
                    user_id=user_id
                )
                await self.uow.commit()
                return characteristic
        except Exception as exc:
            pass


class MayGenerateCharacteristic(Interactor[str, bool]):
    """Проверяет, можно ли генерировать новую характеристику для пользователя"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow
        self.MIN_DAYS_TO_GENERATE_CHARACTERISTIC = MIN_DAYS_AFTER_LAST_CHARACTERISTIC_GENERATION

    async def __call__(self, telegram_id: str) -> bool:
        try:
            async with self.uow:
                # Получаем последнюю характеристику пользователя
                characteristics: list[UserCharacteristicSchema] | None = await self.repository.get_user_characteristics(
                    telegram_id=telegram_id
                )

                # Если характеристик нет, можно генерировать
                if not characteristics:
                    return True

                # Берем последнюю запись (они отсортированы по дате)
                last_characteristic = characteristics[0]

                days_since_last = (datetime.now().date() - last_characteristic.created_at.date()).days

                return days_since_last >= self.MIN_DAYS_TO_GENERATE_CHARACTERISTIC

        except Exception as exc:
            # В случае ошибки возвращаем False для безопасности
            return False
