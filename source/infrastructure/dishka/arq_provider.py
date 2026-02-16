from dishka import Provider, provide, Scope
from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from source.application.arq.arq_service import TaskService


class ArqProvider(Provider):
    scope = Scope.APP   # или Scope.REQUEST, если хочешь новый пул на каждый запрос

    @provide
    async def get_arq_pool(self) -> ArqRedis:
        pool = await create_pool(
            RedisSettings(
                host="redis",           # или брать из env через os.getenv / pydantic-settings
                port=6379,
                password="admin",
                database=0,
            )
        )
        yield pool
        await pool.close()          # важно закрывать при остановке

    @provide
    def get_task_service(self, pool: ArqRedis) -> TaskService:
        return TaskService(arq_pool=pool)
