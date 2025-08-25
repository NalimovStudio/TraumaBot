
from dishka import Provider, Scope, provide, AsyncContainer
from dishka.integrations.aiogram import setup_dishka
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.base import BaseStorage, BaseEventIsolation
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from typing import AsyncIterable

from source.infrastructure.config import BotConfig
from source.presentation.telegram.middlewares import LoadUserMiddleware, LimitCheckMiddleware
from source.presentation.telegram.handlers import handlers_router



class BotProvider(Provider):
    scope = Scope.APP
    
    @provide
    def get_bot(self, config: BotConfig) -> Bot:
        return Bot(token=config.token.get_secret_value(),
                   default=DefaultBotProperties(
                parse_mode=ParseMode.HTML))
    

class DispatcherProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_dispatcher(
        self, 
        dishka: AsyncContainer, 
        storage: BaseStorage,
        event_isolation: BaseEventIsolation
    ) -> Dispatcher:
        dp = Dispatcher(storage=storage, events_isolation=event_isolation)
        dp.include_router(handlers_router)
        dp.update.middleware(LoadUserMiddleware())
        dp.update.middleware(LimitCheckMiddleware())
        setup_dishka(dishka, dp, auto_inject=True)
        return dp
