import logging
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta

from source.application.user import MergeUser, GetUserSchemaById
from source.core.enum import SubscriptionType
from source.core.lexicon.rules import LIMIT_MESSAGE_FREE, LIMIT_MESSAGE_STANDARD
from source.core.schemas.user_schema import UserSchema

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(self, get_by_id: GetUserSchemaById, merge: MergeUser):
        self.get_by_id = get_by_id
        self.merge = merge

    async def check_message_limit(self, telegram_id: str) -> bool:
        user: UserSchema = await self.get_by_id(telegram_id)
        if not user:
            return False

        now = datetime.now(timezone.utc)

        modified = False

        logger.info(f"check limit for {telegram_id}: {user.subscription} "
                    f"\ndaily messages used: {user.daily_messages_used}")

        # Смотрит истекла ли подписка и тогда обнуляем ее
        if user.subscription != SubscriptionType.FREE and user.subscription_date_end and now > user.subscription_date_end:
            user.subscription = SubscriptionType.FREE
            user.subscription_start = None
            user.subscription_date_end = None
            user.messages_used = 0
            user.daily_messages_used = 0
            user.last_daily_reset = now
            modified = True

        # Pro подписка
        if user.subscription == SubscriptionType.PRO:
            if modified:
                await self.merge(user)
            return False  # Безлимит

        elif user.subscription == SubscriptionType.DEFAULT:
            if not user.subscription_start or not user.subscription_date_end:
                return False
            delta = relativedelta(user.subscription_date_end, user.subscription_start)
            months = delta.months + (delta.years * 12) + (1 if delta.days > 0 else 0)
            limit = LIMIT_MESSAGE_STANDARD * max(months, 1)  # 1000 сообщений лимит в месяц для стандарта
            if modified:
                await self.merge(user)
            return user.messages_used > limit

        else:  # Бесплатная подписка
            # Дневной сброс
            if user.last_daily_reset is None or (now - user.last_daily_reset).days >= 1:
                user.daily_messages_used = 0
                user.last_daily_reset = now
                modified = True
            limit = LIMIT_MESSAGE_FREE
            if modified:
                await self.merge(user)
            return user.daily_messages_used >= limit

    async def increment_message_count(self, telegram_id: str):
        user: UserSchema = await self.get_by_id(telegram_id)
        if not user:
            return

        if user.subscription == SubscriptionType.FREE:
            user.daily_messages_used += 1
        elif user.subscription == SubscriptionType.DEFAULT:
            user.messages_used += 1
        await self.merge(user)
