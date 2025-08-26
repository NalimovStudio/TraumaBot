import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, status, Request, HTTPException, Depends
from dishka.integrations.fastapi import FromDishka
from dishka.integrations.fastapi import DishkaRoute

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/v1/webhooks", route_class=DishkaRoute)


@webhooks_router.post("/yookassa", status_code=status.HTTP_200_OK)
async def yookassa_webhook(request: Request):
    event_json = await request.json()
    logger.info("Webhook received!")
    return {"status": "ok"}


@webhooks_router.post("/telegram")
async def telegram_webhook(request: Request):
    try:
        # Get container from app state
        container = request.app.state.dishka_container

        # Get dependencies manually
        bot = await container.get(Bot)
        dp = await container.get(Dispatcher)

        update_data = await request.json()
        update = Update(**update_data)
        await dp.feed_update(bot=bot, update=update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
