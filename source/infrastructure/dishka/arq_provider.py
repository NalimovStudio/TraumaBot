from typing import AsyncGenerator

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings
from dishka import Provider, provide, Scope

from source.application.services.arq_service.arq_service import TaskService


class ArqProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_arq_pool(self) -> AsyncGenerator[ArqRedis, None]:
        pool = await create_pool(
            RedisSettings(
                host="redis",
                port=6379,
                password="admin",
                database=0,
            )
        )
        try:
            yield pool
        finally:
            await pool.close()   # гарантированно закроется при выходе из scope

    @provide
    def get_task_service(self, pool: ArqRedis) -> TaskService:
        return TaskService(arq_pool=pool)
