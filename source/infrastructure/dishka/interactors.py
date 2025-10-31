from dishka import Provider, provide, Scope
from redis.asyncio import Redis

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.payment.payment_service import PaymentService
from source.application.redis_services.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.application.user import CreateUser, GetUserById, GetUserSchemaById, MergeUser
from source.application.user.user_characteristic import GetUserCharacteristics, PutGeneratedUserCharacteristic, \
    MayGenerateCharacteristic
from source.application.user.user_logs import CreateUserLog, GetAllUserLogs, GetLastUserLogs
from source.application.user.user_mood import IsMoodSetToday, GetUserMoods, SetMood
from source.core.lexicon.rules import HISTORY_MAX_LEN


class InteractorsProvider(Provider):
    scope = Scope.REQUEST

    assistant_service = provide(AssistantService)
    payment_service = provide(PaymentService)
    subscription_service = provide(SubscriptionService)
    
    # [ user ]
    create_user = provide(CreateUser)
    get_user_interactor = provide(GetUserById)
    get_user_schema_interactor = provide(GetUserSchemaById)
    merge_user = provide(MergeUser)

    # [ mood ]
    is_mood_set = provide(IsMoodSetToday)
    get_moods_interactor = provide(GetUserMoods)
    set_mood = provide(SetMood)

    # [ logs ]
    get_all_logs = provide(GetAllUserLogs)
    get_weekly_logs = provide(GetLastUserLogs)
    create_user_log = provide(CreateUserLog)

    # [ characteristics ]
    get_user_characteristics_interactor = provide(GetUserCharacteristics)
    put_user_characteristics = provide(PutGeneratedUserCharacteristic)
    may_generate_characteristic = provide(MayGenerateCharacteristic)

    @provide
    def get_message_history(self, redis_client: Redis) -> MessageHistoryService:
        return MessageHistoryService(redis_client=redis_client, history_max_len=HISTORY_MAX_LEN)
