
from typing import AsyncIterable

from dishka import Provider, provide

from faststream.nats import NatsBroker


class Broker(Provider):

    @provide
    async def get_broker(self, config: BrokerConfig) -> AsyncIterable[NatsBroker]:
        broker = NatsBroker(config.build_connection_url())
        broker.include_router(main_router)
        await broker.connect()
        yield broker
        await broker.close()