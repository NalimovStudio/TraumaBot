import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from source.application.arq.arq_service import TaskService
from source.core.lexicon.rules import ADMINS_TG_ID

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command("send"))
async def mailing(
        message: Message,
        task_service: FromDishka[TaskService]
):
    if message.from_user.id not in ADMINS_TG_ID:
        await message.reply(
            "Для этой команды нужно быть <b>Налимовым</b>."
        )
        return

    await task_service.enqueue_mailing(
        message.text
    )

    await message.reply("рассылка создана.")
