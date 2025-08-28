from dishka import make_async_container, AsyncContainer
from dishka.integrations.aiogram import AiogramProvider
from dishka.integrations.fastapi import FastapiProvider

from .bot import BotProvider, DispatcherProvider
from .config import ConfigProvider
from .db import DatabaseProvider
from .interactors import InteractorsProvider
from .neuron import AssistantProvider
from .payment import PaymentProvider
from .repositories import RepositoryProvider
from .storage_redis import RedisProvider


def make_dishka_container() -> AsyncContainer:
    return make_async_container(
        *[
            RedisProvider(),
            ConfigProvider(),
            DatabaseProvider(),
            RepositoryProvider(),
            InteractorsProvider(),
            AssistantProvider(),
            PaymentProvider(),
            BotProvider(),
            DispatcherProvider(),
            AiogramProvider(),
            FastapiProvider()
        ]
    )
