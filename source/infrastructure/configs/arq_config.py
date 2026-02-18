import logging
import os

from arq.connections import RedisSettings
from dishka.integrations.arq import setup_dishka

from source.application.services.arq_service.arq_tasks.mailing import mailing
from source.core.logging.logging_config import configure_logging
from source.infrastructure.dishka import make_dishka_container

logger = logging.getLogger(__name__)


class WorkerSettings:
    # Функции которые может выполнять worker
    functions = [
        mailing
    ]

    redis_settings = RedisSettings.from_dsn(os.getenv('ARQ_REDIS_URL'))

    queue_name = "arq_service:queue"
    max_jobs = 10
    job_timeout = 1800  # 100 минут timeout на задачу
    keep_result = 3600  # Хранить результат 100 мин

    retry_jobs = True
    max_tries = 3

    async def startup(self, ctx):
        """Инициализация при запуске воркера"""
        # Только логирование и другие runtime-инициализации (не Dishka!)
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.info("ARQ worker started with logging configured")

    async def shutdown(self, ctx):
        """Cleanup при остановке"""
        if "dishka_container" in ctx:
            await ctx["dishka_container"].close()
            logger.info("Dishka container closed on shutdown")


container = make_dishka_container()  # создаём контейнер заранее (он singleton)
setup_dishka(container=container, worker_settings=WorkerSettings)
