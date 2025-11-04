import logging

from source.application.base import Interactor
from source.core.lexicon.rules import MIN_DAYS_AFTER_LAST_CHARACTERISTIC_GENERATION
from source.core.schemas import UserLogCreateSchema
from source.core.schemas.user_schema import UserLogSchema
from source.infrastructure.database.repository import UserRepository
from source.infrastructure.database.uow import UnitOfWork

logger = logging.getLogger(__name__)


class CreateUserLog(Interactor[UserLogCreateSchema, UserLogSchema | None]):
    """Записывает лог пользователя"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, user_log: UserLogCreateSchema) -> UserLogSchema | None:
        try:
            async with self.uow:
                created_log: UserLogSchema | None = await self.repository.create_user_log(
                    user_log=user_log
                )
                await self.uow.commit()
                logger.info(f"User log created: {user_log}")
                return created_log
        except Exception as exc:
            logger.error(exc)


class GetAllUserLogs(Interactor[str, list[UserLogSchema] | None]):
    """Возвращает все логи пользователя"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> list[UserLogSchema] | None:
        try:
            async with self.uow:
                logs: list[UserLogSchema] | None = await self.repository.get_user_logs(
                    telegram_id=telegram_id
                )
                return logs
        except Exception as exc:
            logger.error(exc)


class GetLastUserLogs(Interactor[str, list[UserLogSchema] | None]):
    """Возвращает логи пользователя за последние N дней"""

    def __init__(self, repository: UserRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

    async def __call__(self, telegram_id: str) -> list[UserLogSchema] | None:
        try:
            async with self.uow:
                logs: list[UserLogSchema] | None = await self.repository.get_user_logs(
                    telegram_id=telegram_id,
                    days=MIN_DAYS_AFTER_LAST_CHARACTERISTIC_GENERATION
                )
                return logs
        except Exception as exc:
            logger.error(exc)
