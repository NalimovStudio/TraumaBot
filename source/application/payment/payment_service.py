from datetime import datetime, timezone

from source.application.payment.PaymentServiceInterface import PaymentServiceInterface
from source.infrastructure.yookassa import YooKassaClient
from source.infrastructure.database.repository import PaymentRepository
from source.infrastructure.database.uow import UnitOfWork
from source.core.schemas.payment_schema import PaymentSchema
from source.core.enum import SubscriptionType



class PaymentService(PaymentServiceInterface):

    def __init__(self, yookassa_client: YooKassaClient, repository: PaymentRepository, uow: UnitOfWork):
        self.yokassa_client = yookassa_client
        self.repository = repository
        self.uow = uow
    
    async def create_payment(self, amount: int,
                              description: str,
                                months_sub: int,
                                  telegram_id: str,
                                    username: str,
                                    customer_contact: dict,
                                    subscription: SubscriptionType) -> PaymentSchema:
        
        payment_url, purchase_id = await self.yokassa_client.create_payment(amount=amount,
                                                            description=description, customer_contact=customer_contact)
      
        async with self.uow:
            payment: PaymentSchema = await self.repository.create(
                PaymentSchema(
                    purchase_id=purchase_id,
                    telegram_id=telegram_id,
                    username=username,
                    amount=amount,
                    month_sub=months_sub,
                    description=description,
                    status="pending",
                    link=payment_url,
                    subscription=subscription,
                    timestamp=datetime.now()
                )
            )
            await self.uow.commit()
            return payment