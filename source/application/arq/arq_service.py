import hashlib
import logging
from enum import Enum

from arq import ArqRedis
from arq.jobs import Job

logger = logging.getLogger(__name__)


class ARQ_JOBS(str, Enum):
    """
    Функции из arq_tasks.py
    """
    MAILING = "mailing"


class TaskService:
    def __init__(self, arq_pool: ArqRedis):
        self.arq_pool = arq_pool

    @staticmethod
    def generate_job_id(query: str) -> str:
        """Возвращает закодированную строку (приведенную к байтам)"""
        normalized: str = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    async def enqueue_mailing(
            self,
            message: str
    ):
        job: Job = await self.arq_pool.enqueue_job(
            ARQ_JOBS.MAILING.value,
            message
        )
        logger.info(f"Задача на рассылку поставлена в очередь!")

        return {
            "status": str(await job.status()),
            "message": message
        }
