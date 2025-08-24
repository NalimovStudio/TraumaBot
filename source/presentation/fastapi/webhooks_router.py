from aiogram import Bot
import logging

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status, Request, HTTPException

logger = logging.getLogger(__name__)


webhooks_router = APIRouter(prefix="/v1/fastapi", route_class=DishkaRoute)


@webhooks_router.post("/yookassa", status_code=status.HTTP_200_OK)
async def yookassa_webhook(
    request: Request,
):
    event_json = await request.json()
    logger.info("Webhook received!")


"""@webhooks_router.post("/telegram")
async def telegram_webhook(
    update: Update,
    dp: Dispatcher = FromDishka(),
    bot: Bot = FromDishka()
):
    try:
        await dp.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")"""
    