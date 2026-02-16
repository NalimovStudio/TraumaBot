import asyncio
import time
from typing import Sequence, Generator

from source.application.container_deps import get_service_container
from source.application.telegram_service.telegram_service import TelegramService
from source.core.lexicon.rules import ADMINS_TG_ID
from source.core.schemas import UserSchema
from source.infrastructure.database.repository import UserRepository


async def mailing(
        ctx,  # noqa
        message: str
):
    time_start: float = time.time()

    async with get_service_container() as container:
        # [ deps ]
        user_repo: UserRepository = await container.get_user_repo()
        telegram_service: TelegramService = await container.telegram_service

        # [ variables ]
        users: Sequence[UserSchema] = await user_repo.get_all()
        users_telegram_id: Generator[str] = (user.telegram_id for user in users)
        banned_users = 0

        # [ logic ]
        for i, user_telegram_id in enumerate(users_telegram_id):

            # каждые 30 сообщений задержка 1 сек
            if i % 30 == 0:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(0.05)  # 50ms между обычными сообщениями

            try:
                await telegram_service.send_message(
                    user_telegram_id,
                    message=message
                )
            except ValueError:
                banned_users += 1

        message: str = f"""
        Отправка закончена.

        <b>Всего отправлено:</b> {users.__len__()}
        <b>Заблокировали бота:</b> {banned_users} человек

        <b>Прошло времени:</b> {time.time() - time_start:.2f} секунд.
        """

        for admin_id in ADMINS_TG_ID:
            await telegram_service.send_message(
                user_telegram_id=admin_id,
                message=message
            )
