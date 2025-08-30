# app.py (главный ASGI файл)
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramRetryAfter
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi_security_telegram_webhook import OnlyTelegramNetworkWithSecret

from source.core.logging.logging_config import configure_logging
from source.infrastructure.dishka import make_dishka_container
from source.presentation.fastapi.webhooks_router import webhooks_router

configure_logging()
logger = logging.getLogger(__name__)

dishka_container = make_dishka_container()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for creating Dishka container and setting Telegram webhook"""

    async def set_webhook_with_retry(bot: Bot, webhook_url: str, max_attempts: int = 3):
        for attempt in range(1, max_attempts + 1):
            try:
                await bot.set_webhook(webhook_url)
                logger.info(f"✅ Webhook successfully set to: {webhook_url}")
                return True
            except TelegramRetryAfter as e:
                logger.warning(
                    f"Rate limit hit: retry after {e.retry_after} seconds (attempt {attempt}/{max_attempts})")
                await asyncio.sleep(e.retry_after)
                if attempt == max_attempts:
                    logger.error(f"❌ Failed to set webhook after {max_attempts} attempts: {e}")
                    return False
            except Exception as e:
                logger.error(f"❌ Failed to set webhook: {e}")
                return False

    try:
        logger.info("🔄 Starting Dishka container...")

        # Получаем зависимости из контейнера
        bot: Bot = await dishka_container.get(Bot)
        dp: Dispatcher = await dishka_container.get(Dispatcher)

        # install webhook secret

        secret = OnlyTelegramNetworkWithSecret(
            real_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET")
        )
        webhook_url = f"https://траума.рф/v1/webhooks/telegram/{secret}"

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

    app = FastAPI(
        title="TraumaBot API",
        description="API for TraumaBot Telegram bot and fastapi",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
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
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )
