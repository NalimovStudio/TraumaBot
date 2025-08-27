from dishka import Provider, provide, Scope
from redis.asyncio import Redis

from source.application.user import CreateUser, GetUserById, GetUserSchemaById, MergeUser
from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.application.payment.payment_service import PaymentService
from source.application.subscription.subscription_service import SubscriptionService

from source.core.lexicon.rules import HISTORY_MAX_LEN


class InteractorsProvider(Provider):
    scope = Scope.REQUEST

    create_user_service = provide(CreateUser)
    get_user_service = provide(GetUserById)
    get_user_schema_service = provide(GetUserSchemaById)
    merge_user = provide(MergeUser)
    asisstant_service = provide(AssistantService)
    payment_service = provide(PaymentService)
    subscription_service = provide(SubscriptionService)


    @provide
    def get_message_history(self, redis_client: Redis) -> MessageHistoryService:
        return MessageHistoryService(redis_client=redis_client, history_max_len=HISTORY_MAX_LEN)