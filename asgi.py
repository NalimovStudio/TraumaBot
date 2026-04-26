import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from dishka.integrations.aiogram import setup_dishka as setup_dishka_aiogram
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from source.core.logging.logging_config import configure_logging
from source.infrastructure.dishka import make_dishka_container
from source.presentation.fastapi.webhooks_router import webhooks_router

configure_logging()
logger = logging.getLogger(__name__)

dishka_container = make_dishka_container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for creating Dishka container and setting Telegram webhook"""

    async def delete_webhook(bot: Bot):
        """Удаляет вебхук с увеличенным таймаутом"""
        try:
            logger.info("🔄 Пытаемся удалить старый webhook...")
            await bot.delete_webhook(
                drop_pending_updates=True,
                request_timeout=30  # ← увеличил таймаут
            )
            logger.info("✅ Old webhook deleted successfully")
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить webhook: {e} (это не критично, продолжаем)")

    async def set_webhook_with_retry(bot: Bot, webhook_url: str, max_attempts: int = 5):
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 Попытка {attempt}/{max_attempts} установить webhook: {webhook_url}")

                current = await bot.get_webhook_info(request_timeout=15)
                logger.info(f"Текущий webhook: {current.url or 'None'}")

                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=os.getenv("TELEGRAM_WEBHOOK_SECRET"),
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query", "pre_checkout_query", "successful_payment"],
                    request_timeout=30  # ← важно!
                )
                logger.info("✅ Webhook успешно установлен!")
                return True

            except Exception as e:
                logger.error(f"❌ Ошибка {attempt}: {type(e).__name__} — {e}", exc_info=True)
                if attempt == max_attempts:
                    return False
                await asyncio.sleep(5)

        return False

    try:
        logger.info("🔄 Starting Dishka container...")

        # Получаем зависимости из контейнера
        bot: Bot = await dishka_container.get(Bot)
        dp: Dispatcher = await dishka_container.get(Dispatcher)

        setup_dishka_aiogram(dishka_container, dp, auto_inject=True)

        await dp.emit_startup()

        # Удаляем вебхук перед запуском
        await delete_webhook(bot)

        secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if not secret:
            raise ValueError("TELEGRAM_WEBHOOK_SECRET is not set in environment variables")

        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL") + f"/{secret}"

        success = await set_webhook_with_retry(bot, webhook_url)
        if not success:
            raise RuntimeError("Failed to set Telegram webhook")
        logger.info("✅ Application startup complete")
        yield

    except Exception as e:
        logger.error(f"❌ Failed to set webhook: {e}")
        raise
    finally:
        logger.info("🔄 Closing Dishka container...")
        await dishka_container.close()
        logger.info("✅ Dishka container closed")


def create_app() -> FastAPI:
    """Factory для создания FastAPI приложения"""

    # для прода — отключить
    docs_enabled: bool = os.getenv("DOCS_ENABLE", "False") == "True"

    app = FastAPI(
        title="TraumaBot API",
        description="API for TraumaBot Telegram bot and fastapi",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None
    )

    # Настраиваем Dishka
    setup_dishka(dishka_container, app)

    app.include_router(webhooks_router, prefix="", tags=["webhooks"])

    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "trauma-bot-api",
            "version": "1.0.0"
        }

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "production") == "development"

    logger.info(f"🚀 Starting TraumaBot API on {host}:{port}")

    uvicorn.run(
        "asgi:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )