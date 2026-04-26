from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/health", tags=["health"])
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "service": "trauma-bot-api",
        "version": "1.0.0",
        "mode": "polling"
    }
