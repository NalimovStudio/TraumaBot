import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, User as TelegramUser
from dishka import AsyncContainer

from source.application.subscription.subscription_service import SubscriptionService
from source.presentation.telegram.keyboards.keyboards import get_subscriptions_menu_keyboard
from source.presentation.telegram.states.user_states import SupportStates

logger = logging.getLogger(__name__)


class LimitCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        if event.text and event.text.startswith("/start"):
            return await handler(event, data)

        state = data.get("state")
        if not state:
            return await handler(event, data)

        current_state = await state.get_state()

        limitable_states = [
            SupportStates.VENTING.state,
            SupportStates.PROBLEM_S2_GOAL.state,
            SupportStates.CALMING_TALK.state,
            SupportStates.BLACKPILL_TALK.state
        ]

        if current_state not in limitable_states:
            return await handler(event, data)

        if "dishka_container" not in data:
            logger.error("Dishka container not found in middleware data!")
            return await handler(event, data)

        container: AsyncContainer = data["dishka_container"]
        subscription_service: SubscriptionService = await container.get(SubscriptionService)

        aiogram_user: TelegramUser = data.get("event_from_user")
        if not aiogram_user:
            return await handler(event, data)

        telegram_id = str(aiogram_user.id)

        limit_reached = await subscription_service.check_message_limit(telegram_id)
        logger.info(f'User {telegram_id} in state {current_state}. Limit reached: {limit_reached}')

        if limit_reached:
            await event.answer(
                "<b>Вы достигли лимита сообщений за сутки. Дождитесь завтра или приобретите подписку:</b>",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            return

        return await handler(event, data)
