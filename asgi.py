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
polling_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для инициализации и управления polling'ом"""

    async def start_polling(bot: Bot, dp: Dispatcher):
        """Запускает polling для получения обновлений от Telegram"""
        try:
            logger.info("🔄 Проверяем webhook...")

            # Сначала проверяем текущий webhook
            try:
                webhook_info = await bot.get_webhook_info(request_timeout=15)
                if webhook_info.url:
                    logger.info(f"📍 Найден старый webhook: {webhook_info.url}")
                    logger.info("🔄 Удаляем старый webhook...")
                    try:
                        await bot.delete_webhook(drop_pending_updates=True, request_timeout=60)
                        logger.info("✅ Webhook удален успешно")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка при удалении webhook: {type(e).__name__}: {e}")
                        logger.info("⚠️ Продолжаем с polling несмотря на ошибку удаления")

                    # Даем время Telegram на обновление
                    await asyncio.sleep(3)
                else:
                    logger.info("✅ Webhook не установлен, готовы к polling")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось проверить webhook: {type(e).__name__}: {e}")
                logger.info("⚠️ Продолжаем с polling")

            logger.info("🔄 Начинаем polling обновлений от Telegram...")
            # Запускаем polling
            await dp.start_polling(
                bot,
                allowed_updates=["message", "callback_query", "pre_checkout_query", "successful_payment"],
                skip_updates=False  # Обрабатываем все обновления (включая накопленные)
            )
        except asyncio.CancelledError:
            logger.info("✅ Polling прерван (приложение закрывается)")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка при polling'е: {type(e).__name__}: {e}", exc_info=True)
            raise

    async def stop_polling():
        """Останавливает polling"""
        if polling_task and not polling_task.done():
            logger.info("🔄 Останавливаем polling...")
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                logger.info("✅ Polling успешно остановлен")

    try:
        logger.info("=" * 60)
        logger.info("🔄 Запускаем Dishka container...")

        # Получаем зависимости из контейнера
        bot: Bot = await dishka_container.get(Bot)
        dp: Dispatcher = await dishka_container.get(Dispatcher)

        setup_dishka_aiogram(dishka_container, dp, auto_inject=True)

        await dp.emit_startup()

        # Запускаем polling в фоновой задаче
        global polling_task
        polling_task = asyncio.create_task(start_polling(bot, dp))

        logger.info("✅ Приложение успешно запущено с polling'ом")
        logger.info("=" * 60)
        yield

    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске: {type(e).__name__}: {e}", exc_info=True)
        raise
    finally:
        logger.info("=" * 60)
        logger.info("🔄 Закрываем приложение...")
        await stop_polling()
        await dishka_container.close()
        logger.info("✅ Приложение полностью закрыто")
        logger.info("=" * 60)


def create_app() -> FastAPI:
    """Factory для создания FastAPI приложения"""

    # для прода — отключить
    docs_enabled: bool = os.getenv("DOCS_ENABLE", "False") == "True"

    app = FastAPI(
        title="TraumaBot API",
        description="API for TraumaBot Telegram bot (polling mode)",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None
    )

    # Настраиваем Dishka
    setup_dishka(dishka_container, app)

    # Включаем маршрут для health check
    app.include_router(health_router, tags=["health"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "production") == "development"

    logger.info(f"🚀 Запускаем TraumaBot API на {host}:{port} (polling mode)")

    uvicorn.run(
        "asgi:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )
