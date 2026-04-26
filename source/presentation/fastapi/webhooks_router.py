import logging
import os
from datetime import datetime, UTC
from typing import Dict, Any

from aiogram import Bot
from dateutil.relativedelta import relativedelta
from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status, Request, BackgroundTasks

from source.application.payment.merge import MergePayment
from source.application.user import MergeUser, GetUserSchemaById
from source.core.schemas.payment_schema import PaymentSchema
from source.core.schemas.user_schema import UserSchema
from source.infrastructure.database.repository import PaymentRepository

logger = logging.getLogger(__name__)

webhooks_router = APIRouter(prefix="/v1/webhooks", route_class=DishkaRoute)


async def process_successful_payment(
        event_json: Dict[str, Any],
        payment_repo: PaymentRepository,
        get_user_id: GetUserSchemaById,
        merge_user: MergeUser,
        merge_payment: MergePayment,
        bot: Bot
):
    payment_object = event_json.get('object', {})
    purchase_id = payment_object.get('id')
    payment_status = payment_object.get('status')
    try:
        if payment_status != 'succeeded':
            return

        payment_log: PaymentSchema = await payment_repo.get_by_purchase_id(purchase_id)
        if not payment_log or payment_log.status == 'succeeded':
            return

        telegram_id = payment_log.telegram_id
        now = datetime.now(UTC)
        date_end = now + relativedelta(months=payment_log.month_sub)

        user: UserSchema = await get_user_id(telegram_id)
        if user:
            user.subscription = payment_log.subscription
            user.subscription_start = now
            user.subscription_date_end = date_end
            user.messages_used = 0
            user.daily_messages_used = 0
            await merge_user(user)

        payment_log.status = 'succeeded'
        await merge_payment(payment_log)

        await bot.send_message(chat_id=int(telegram_id), text="Ваша подписка успешно оформлена!")

    except Exception as e:
        logger.error(f"Error processing payment {purchase_id}: {e}")


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
    background_tasks.add_task(
        process_successful_payment,
        event_json, payment_repo, get_by_id,
        merge_user, merge_payment, bot
    )
    return {"status": "ok"}
