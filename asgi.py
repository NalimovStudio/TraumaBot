# app.py (главный ASGI файл)
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dishka.integrations.fastapi import setup_dishka

from source.infrastructure.dishka import make_webhook_container
from source.presentation.fastapi.webhooks_router import webhooks_router
from source.core.logging.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app_container = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager для создания и закрытия контейнера"""
    global app_container

    try:
        logger.info("🔄 Creating Dishka container...")
        app_container = make_webhook_container()

        logger.info("✅ Dishka container created successfully")
        yield

    except Exception as e:
        logger.error(f"❌ Failed to create container: {e}")
        raise
    finally:
        if app_container:
            logger.info("🔄 Closing Dishka container...")
            await app_container.close()
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

    app.include_router(webhooks_router, prefix="", tags=["payment"])

    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "trauma-bot-api",
            "version": "1.0.0",
            "container_status": str(bool(app_container))
        }

    if app_container:
        setup_dishka(container=app_container, app=app)

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