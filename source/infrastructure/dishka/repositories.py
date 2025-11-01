
from dishka import Provider, provide, Scope

from source.infrastructure.database.repository import UserRepository, PaymentRepository
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    user_repository = provide(UserRepository)
    payment_repository = provide(PaymentRepository)
    dialogs_logging_repository = provide(UserDialogsLoggingRepository)
