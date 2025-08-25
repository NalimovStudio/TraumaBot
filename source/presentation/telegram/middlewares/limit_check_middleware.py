import logging

from aiogram import BaseMiddleware
from aiogram.types import Message
from dishka import AsyncContainer
from aiogram.types import User as TelegramUser
from dishka.integrations.aiogram import CONTAINER_NAME

from source.application.subscription.subscription_service import SubscriptionService
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.keyboards.keyboards import get_subscriptions_menu_keyboard
from source.core.schemas.user_schema import UserSchema


logger = logging.getLogger(__name__)

class LimitCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: Message,
        data: dict,
    ):
        if not isinstance(event, Message):
            # Если это не сообщение, пропускаем обработку этим middleware
            # и передаем управление следующему обработчику
            return await handler(event, data)
        
        state = data.get("state")
        current_state = await state.get_state() if state else None
        if current_state != SupportStates.VENTING:
            return await handler(event, data)

        dishka: AsyncContainer = data[CONTAINER_NAME]
        subscription_service: SubscriptionService = await dishka.get(SubscriptionService)
        aiogram_user: TelegramUser = data["event_from_user"]

        user_id = aiogram_user.id
        telegram_id = str(user_id)  # т.к. в модели str

        if not await subscription_service.check_message_limit(telegram_id):
            await event.answer(
                "Вы достигли лимита сообщений. Подпишитесь для продолжения или выберите тариф в меню.",
                reply_markup=get_subscriptions_menu_keyboard()
            )
            return 

        return await handler(event, data)