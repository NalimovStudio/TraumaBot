from dishka import Provider, provide, Scope

from source.infrastructure.configs import PaymentConfig
from source.infrastructure.yookassa import YooKassaClient


class PaymentProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_payment_client(self, config: PaymentConfig) -> YooKassaClient:
        return YooKassaClient(store_id=config.store_id.get_secret_value(),
                              store_token=config.store_token.get_secret_value())
