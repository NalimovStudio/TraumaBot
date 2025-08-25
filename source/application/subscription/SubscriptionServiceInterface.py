from abc import ABC, abstractmethod



class SubscriptionServiceInterface(ABC):

    @abstractmethod
    async def check_message_limit(self, telegram_id: str):
        ...

    @abstractmethod
    async def increment_message_count(self, telegram_id: str):
        ...