import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka, inject

from source.application.services.arq_service import TaskService
from source.core.lexicon.rules import ADMINS_TG_ID

router = Router(name=__name__)
logger = logging.getLogger(__name__)

@inject
@router.message(Command("send"))
async def mailing(
        message: Message,
        command: CommandObject,  # получаем объект команды
        task_service: FromDishka[TaskService]
):
    message_text = command.args

    if str(message.from_user.id) not in ADMINS_TG_ID:
        await message.reply(
            "Для этой команды нужно быть <b>Налимовым</b>."
        )
        return

    await task_service.enqueue_mailing(
        message_text
    )

    await message.reply("рассылка создана.")
