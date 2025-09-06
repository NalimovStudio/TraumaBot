import uvicorn
from fastapi import APIRouter, status, Request, BackgroundTasks
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from typing import Dict, Any
import logging

from aiogram import Bot
from source.application.subscription.subscription_service import SubscriptionService 
from source.infrastructure.database.repository import PaymentRepository
from source.infrastructure.database.models.payment_model import PaymentLogs
from source.infrastructure.database.models.user_model import User
from source.application.user import GetUserSchemaById, MergeUser
from source.application.payment.merge import MergePayment
from source.core.schemas.user_schema import UserSchema
from dateutil.relativedelta import relativedelta
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/parser", route_class=DishkaRoute)

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

        #если уже processed, skip
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

@router.post("/yookassa_webhook", status_code=status.HTTP_200_OK)
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