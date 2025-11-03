
from dishka import Provider, provide, Scope

from source.infrastructure.database.repository import UserRepository, PaymentRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    user_repository = provide(UserRepository)
    payment_repository = provide(PaymentRepository)
