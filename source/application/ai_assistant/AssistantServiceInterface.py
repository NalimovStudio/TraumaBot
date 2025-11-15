from abc import ABC, abstractmethod

from source.core.schemas.assistant_schemas import AssistantResponse, ContextMessage
from source.core.lexicon.prompts import *
from source.core.schemas.user_schema import UserCharacteristicSchema
from source.infrastructure.database.models.base_model import S


class AssistantServiceInterface(ABC):
    @abstractmethod
    async def get_speaking_response(
            self,
            message: str,
            context_messages: list[ContextMessage],
            prompt: str = GET_CALM_PROMPT
    ) -> AssistantResponse:
        """Режим успокоения. Максимальная эмпатия."""
        pass

    @abstractmethod
    async def get_kpt_diary_response(
            self,
            message: str,
            context_messages: list[ContextMessage],
            prompt: str = KPT_DIARY_PROMPT
    ) -> AssistantResponse:
        """Дневник эмоций КПТ."""  # TODO
        pass

    @abstractmethod
    async def get_problems_solver_response(
            self,
            message: str,
            context_messages: list[ContextMessage],
            prompt: str = PROBLEMS_SOLVER_PROMPT,
            temperature: float = 0.65
    ) -> AssistantResponse:
        """Решение проблем. Строгий промпт, ниже температура."""
        pass

    @abstractmethod
    async def get_speaking_response(
            self,
            message: str,
            context_messages: list[ContextMessage],
            prompt: str = SPEAKING_PROMPT,
    ) -> AssistantResponse:
        """Поговорить. Баланс между эмпатией и решением проблемы."""
        pass

    @abstractmethod
    async def get_user_characteristic(
            self,
            user_message_history: list[str],
            user_mood_history: list[str],
            prompt: str = GET_USER_CHARACTERISTIC,
            response_schema: S = UserCharacteristicSchema
    ):
        """Получает JSON формат для таблицы user_characteristic"""
        pass
