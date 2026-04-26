import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from dishka.integrations.aiogram import setup_dishka as setup_dishka_aiogram
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from source.core.logging.logging_config import configure_logging
from source.infrastructure.dishka import make_dishka_container
from source.presentation.fastapi.health_router import health_router

configure_logging()
logger = logging.getLogger(__name__)

dishka_container = make_dishka_container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    bot: Bot = await dishka_container.get(Bot)
    dp: Dispatcher = await dishka_container.get(Dispatcher)

    # ВАЖНО: setup до старта polling, не после
    setup_dishka_aiogram(dishka_container, dp, auto_inject=True)

    # Сносим webhook если остался
    try:
        webhook_info = await bot.get_webhook_info(request_timeout=15)
        if webhook_info.url:
            logger.info(f"Удаляем старый webhook: {webhook_info.url}")
            await bot.delete_webhook(drop_pending_updates=True, request_timeout=60)
            await asyncio.sleep(2)
            logger.info("Webhook удалён")
    except Exception as e:
        logger.warning(f"Не удалось проверить/удалить webhook: {e}")

    polling_task = asyncio.create_task(_run_polling(bot, dp))
    logger.info("Polling запущен")

    yield  # приложение живёт здесь

    # Завершение
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass

    await bot.session.close()
    await dishka_container.close()
    logger.info("Приложение остановлено")


async def _run_polling(bot: Bot, dp: Dispatcher):
    try:
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query",
                              "pre_checkout_query", "successful_payment"],
            handle_signals=False,   # сигналами управляет uvicorn
            close_bot_session=False,
        )
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.error(f"Polling упал: {e}", exc_info=True)
        raise


def create_app() -> FastAPI:
    docs_enabled = os.getenv("DOCS_ENABLE", "False") == "True"

    app = FastAPI(
        title="TraumaBot API",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
    )

    setup_dishka(dishka_container, app)
    app.include_router(health_router, tags=["health"])
    # webhooks_router НЕ подключаем — он больше не нужен для telegram

    return app


app = create_app()
