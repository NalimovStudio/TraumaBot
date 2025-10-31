from typing import AsyncIterable

from collections.abc import AsyncIterable

from aiogram.fsm.storage.base import BaseEventIsolation, BaseStorage, DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage

from dishka import AnyOf, Provider, Scope, provide

from redis.asyncio import Redis

from source.infrastructure.config import RedisConfig
from source.presentation.telegram.utils import custom_json_loads, custom_json_dumps


class RedisProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_redis(self, config: RedisConfig) -> AsyncIterable[Redis]:
        async with Redis.from_url(
            config.build_url()
        ) as redis:
            yield redis

    @provide
    def get_redis_storage(self, redis: Redis) -> AnyOf[BaseStorage, RedisStorage]:
        return RedisStorage(
            redis=redis,
            key_builder=DefaultKeyBuilder(with_destiny=True),
            json_loads=custom_json_loads,
            json_dumps=custom_json_dumps
        )
    
    @provide
    def get_redis_event_isolation(
        self,
        redis_storage: RedisStorage
    ) -> AnyOf[RedisEventIsolation, BaseEventIsolation]:
        return redis_storage.create_isolation()