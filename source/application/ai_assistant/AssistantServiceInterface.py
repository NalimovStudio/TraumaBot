from abc import ABC, abstractmethod

from source.core.schemas.assistant_schemas import AssistantResponse, ContextMessage


class AssistantServiceInterface(ABC):
    @abstractmethod
    async def get_calm_response(
            self,
            message: str,
            prompt: str,
            context_messages: list[ContextMessage]
    ) -> AssistantResponse:
        """Режим успокоения. Максимальная эмпатия."""
        pass

    @abstractmethod
    async def get_kpt_diary_response(
            self,
            message: str,
            prompt: str,
            context_messages: list[ContextMessage]
    ) -> AssistantResponse:
        """Дневник эмоций КПТ."""  # TODO
        pass

    @abstractmethod
    async def get_problems_solver_response(
            self,
            message: str,
            prompt: str,
            context_messages: list[ContextMessage],
            temperature: float = 0.65
    ) -> AssistantResponse:
        """Решение проблем. Строгий промпт, ниже температура."""
        pass

    @abstractmethod
    async def get_speak_out_response(
            self,
            message: str,
            prompt: str,
            context_messages: list[ContextMessage]
    ) -> AssistantResponse:
        """Высказаться. Баланс между эмпатией и решением проблемы."""
        pass
