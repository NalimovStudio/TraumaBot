from abc import ABC, abstractmethod

from source.core.schemas.assistant_schemas import ContextMessage


class MessageHistoryServiceInterface(ABC):
    @abstractmethod
    async def add_message_to_history(self, user_id: int, context_scope: str, message: ContextMessage):
        """
        Добавляет сообщение пользователя в историю для специально "скопа" (e.g, 'cbt', 'venting')
        и сохраняет историтю до n сообщения
        """
        raise NotImplementedError

    @abstractmethod
    async def get_history(self, user_id: int, context_scope: str) -> list[ContextMessage]:
        """
        Получает историю по сообщениия по юзеру по скопу
        """
        raise NotImplementedError
    

    @abstractmethod
    async def clear_history(self, user_id: int, context_scope: str):
        """Очищает историю юзера по айди и его скопу"""
        raise NotImplementedError
