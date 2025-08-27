from datetime import datetime, timezone

from source.application.payment.PaymentServiceInterface import PaymentServiceInterface
from source.infrastructure.yookassa import YooKassaClient
from source.infrastructure.database.repository import PaymentRepository
from source.core.schemas.payment_schema import PaymentSchema
from source.core.enum import SubscriptionType



class PaymentService(PaymentServiceInterface):

    def __init__(self, yookassa_client: YooKassaClient, repository: PaymentRepository):
        self.yokassa_client = yookassa_client
        self.repository = repository
    
    async def create_payment(self, amount: int,
                              description: str,
                                months_sub: int,
                                  telegram_id: str,
                                    username: str,
                                    customer_contact: dict,
                                    sub_type: SubscriptionType) -> PaymentSchema:
        
        payment_url, purchase_id = await self.yokassa_client.create_payment(amount=amount,
                                                            description=description, customer_contact=customer_contact)
      
        
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
                subscription=sub_type,
                timestamp=datetime.now()
            )
        )
        return payment