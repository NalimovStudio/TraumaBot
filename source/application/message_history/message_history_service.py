import json
import logging
from typing import List

from redis.asyncio import Redis
from source.application.message_history.MessageHistoryServiceInterface import MessageHistoryServiceInterface
from source.core.schemas.assistant_schemas import ContextMessage

logger = logging.getLogger(__name__)


class MessageHistoryService(MessageHistoryServiceInterface):
    def __init__(self, redis_client: Redis, history_max_len: int):
        self._redis = redis_client
        self._prefix = "message_history"
        self.HISTORY_MAX_LEN = history_max_len

    def _get_user_key(self, user_id: int, context_scope: str) -> str:
        return f"{self._prefix}:{context_scope}:{user_id}"

    async def add_message_to_history(self, user_id: int, context_scope: str, message: ContextMessage):
        """
        Добавляет сообщение пользователя в историю для специально "скопа" (e.g, 'cbt', 'venting')
        и сохраняет историтю до n сообщения
        """
        key = self._get_user_key(user_id, context_scope)
        try:
            message_json = message.model_dump_json()
            await self._redis.lpush(key, message_json)
            await self._redis.ltrim(key, 0, self.HISTORY_MAX_LEN - 1)
            logger.debug(f"Saved message to history for user {user_id} in scope {context_scope}")
        except Exception as e:
            logger.error(f"Error saving message to history for user {user_id} in scope {context_scope}: {e}")

    async def get_history(self, user_id: int, context_scope: str) -> List[ContextMessage]:
        """
        Получает историю по сообщениия по юзеру и его скопу
        """
        key = self._get_user_key(user_id, context_scope)
        try:
            history_json = await self._redis.lrange(key, 0, -1)
            history = [ContextMessage.model_validate(json.loads(msg)) for msg in history_json]
            history.reverse()
            logger.debug(f"Retrieved {len(history)} messages from history for user {user_id} in scope {context_scope}")
            return history
        except Exception as e:
            logger.error(f"Error retrieving history for user {user_id} in scope {context_scope}: {e}")
            return []
        
    async def clear_history(self, user_id: int, context_scope: str):
        """Очищает историю юзера по айди пользователя и его скопу"""
        key = self._get_user_key(user_id, context_scope)
        try:
            await self._redis.delete(key)
            logger.info(f"Cleared history for user {user_id} in scope {context_scope}")
        except Exception as e:
            logger.error(f"Error clearing history for user {user_id} in scope {context_scope}: {e}")