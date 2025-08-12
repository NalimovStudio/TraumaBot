
from dishka import Provider, provide, Scope
from typing import AsyncIterable
from contextlib import asynccontextmanager 
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession, create_async_engine

from source.infrastructure.config import DatabaseConfig


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    async def get_engine(self, config: DatabaseConfig) -> AsyncIterable[AsyncEngine]:
        engine = create_async_engine(config.build_connection_url())
        try:
            yield engine
        finally:
            await engine.dispose(True)

    @provide
    async def get_pool(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)
    
    @provide(scope=Scope.REQUEST)
    async def get_session(self, pool: async_sessionmaker[AsyncSession]) -> AsyncIterable[AsyncSession]:
        async with pool() as session:
            try:
                yield session
            finally:
                pass

    #TODO PROVIDE UOW