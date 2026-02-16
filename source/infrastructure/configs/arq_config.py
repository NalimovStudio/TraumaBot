import logging

from arq.connections import RedisSettings
import os

from source.application.arq.arq_tasks.mailing import mailing
from source.core.logging.logging_config import configure_logging


class WorkerSettings:
    # Функции которые может выполнять worker
    functions = [
        mailing
    ]

    # Настройки Redis
    redis_settings = RedisSettings.from_dsn(os.getenv('ARQ_REDIS_URL'))

    # Настройки worker
    queue_name = os.getenv('ARQ_REDIS_QUEUE')
    max_jobs = os.getenv('ARQ_MAX_JOBS')
    job_timeout = 600  # 10 минут timeout на задачу
    keep_result = 600  # Хранить результат 10 мин

    # [ Logger ]
    async def on_startup(self):
        """Вызывается при запуске worker"""
        configure_logging()
        logger = logging.getLogger(__name__)
        logger.info("ARQ worker started with logging configured")

    # Retry политика
    retry_jobs = True
    max_tries = 3
