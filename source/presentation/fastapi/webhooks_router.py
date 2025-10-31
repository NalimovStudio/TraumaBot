import logging
import os
from datetime import datetime
from typing import Dict, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from dateutil.relativedelta import relativedelta
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status, Request, HTTPException, BackgroundTasks, Depends, Path
from source.application.payment.merge import MergePayment

from source.application.user import MergeUser, GetUserSchemaById
from source.core.schemas.user_schema import UserSchema
from source.infrastructure.database.models.payment_model import PaymentLogs
from source.infrastructure.database.repository import PaymentRepository

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/v1/webhooks", route_class=DishkaRoute)

real_secret: str = os.getenv("TELEGRAM_WEBHOOK_SECRET")


def check_secret(secret: str = Path(..., include_in_schema=False)):
    if secret != real_secret:
        raise HTTPException(status_code=404, detail="Неверный секрет вебхука!")
    return secret


async def process_successful_payment(
    event_json: Dict[str, Any],
    payment_repo: PaymentRepository,
    get_user_id: GetUserSchemaById,
    merge_user: MergeUser,
    merge_payment: MergePayment,
    bot: Bot
):
    """Асинхронная обработка успешной оплаты (в background)."""
    try:
        payment_object = event_json.get('object', {})
        purchase_id = payment_object.get('id')  # ID платежа от Yookassa
        status = payment_object.get('status')

        if status != 'succeeded':
            logger.info(f"Payment {purchase_id} not succeeded: {status}")
            return

        # Найти PaymentLog по purchase_id
        payment_log: PaymentLogs = await payment_repo.get_model_by_purchase_id(purchase_id)
        if not payment_log:
            logger.error(f"PaymentLog not found for {purchase_id}")
            return

        # если уже processed, skip
        if payment_log.status == 'succeeded':
            logger.info(f"Payment {purchase_id} already succeeded")
            return

        telegram_id = payment_log.telegram_id
        now = datetime.utcnow()
        date_end = now + relativedelta(months=payment_log.month_sub)

        user: UserSchema = await get_user_id(telegram_id)  # Получить User
        if user:
            user.subscription = payment_log.subscription
            user.subscription_start = now
            user.subscription_date_end = date_end
            user.messages_used = 0
            user.daily_messages_used = 0
            await merge_user(user)  # Merge для сохранения

        payment_log.status = 'succeeded'
        await merge_payment(payment_log)


        await bot.send_message(
            chat_id=int(telegram_id),
            text="Ваша подписка успешно оформлена!"
        )
        logger.info(f"Payment {purchase_id} succeeded and notification sent to {telegram_id}")

    except Exception as e:
        logger.error(f"Error processing payment {purchase_id}: {e}")
        # Здесь можно добавить retry или лог в DLQ, но для простоты - log


@webhooks_router.post("/yookassa_webhook", status_code=status.HTTP_200_OK)
async def handle_yookassa_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    payment_repo: FromDishka[PaymentRepository],
    get_by_id: FromDishka[GetUserSchemaById],
    merge_payment: FromDishka[MergePayment],
    merge_user: FromDishka[MergeUser],
    bot: FromDishka[Bot]
):
    event_json = await request.json()
    logger.info("Webhook received!")

    # Быстро отвечаем 200 OK, обработку в background
    background_tasks.add_task(
        process_successful_payment,
        event_json,
        payment_repo,
        get_by_id,
        merge_payment,
        merge_user,
        bot
    )

    return {"status": "ok"}


@webhooks_router.post("/telegram/{secret}", include_in_schema=False)
async def telegram_webhook(
        request: Request,
        secret: str = Depends(check_secret)
):
    try:
        # Get container from app state
        container = request.app.state.dishka_container

        # Get dependencies manually
        bot: Bot = await container.get(Bot)
        dp: Dispatcher = await container.get(Dispatcher)

        update_data = await request.json()
        update = Update(**update_data)

        await dp.feed_update(bot=bot, update=update, dishka_container=container)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")