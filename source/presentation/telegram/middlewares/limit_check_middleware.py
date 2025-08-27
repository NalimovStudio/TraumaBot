import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, User as TelegramUser
from dishka import AsyncContainer
from dishka.integrations.aiogram import CONTAINER_NAME
from source.application.subscription.subscription_service import SubscriptionService
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.keyboards.keyboards import get_subscriptions_menu_keyboard

logger = logging.getLogger(__name__)

class LimitCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        logger.debug(f"Processing event: {type(event)}")

        # Пропускаем команду /start
        if event.text and event.text.startswith("/start"):
            logger.info(f"Skipping limit check for /start command for user {event.from_user.id}")
            return await handler(event, data)

        # Проверяем, является ли событие сообщением
        if not isinstance(event, Message):
            logger.info(f'Event is not a message: {type(event)}')
            return await handler(event, data)
        
        state = data.get("state")
        if not state:
            logger.info('No state provided')
            return await handler(event, data)
            
        current_state = await state.get_state()
        
        # Список состояний, для которых нужно применять лимиты
        limitable_states = [
            SupportStates.VENTING.state,
            SupportStates.PROBLEM_S2_GOAL.state,
            SupportStates.CALMING_TALK.state
        ]

        # Пропускаем, если состояние не в списке
        if current_state not in limitable_states:
            logger.info(f'User {event.from_user.id} not in limitable state: {current_state}')
            return await handler(event, data)

        # Получаем сервис подписки
        dishka: AsyncContainer = data[CONTAINER_NAME]
        subscription_service: SubscriptionService = await dishka.get(SubscriptionService)
        aiogram_user: TelegramUser = data["event_from_user"]
        
        telegram_id = str(aiogram_user.id)
        
        limit_reached = await subscription_service.check_message_limit(telegram_id)
        logger.info(f'User {telegram_id} in state {current_state}. Limit reached: {limit_reached}')

        if limit_reached:
            await event.answer(
                "Вы достигли лимита сообщений за день. Подпишитесь для продолжения или выберите тариф в меню.",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            return  # Останавливаем дальнейшую обработку

        return await handler(event, data)