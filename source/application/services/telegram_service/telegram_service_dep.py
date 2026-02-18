from source.application.services.telegram_service.telegram_service import TelegramService

telegram_service: TelegramService = TelegramService()


async def get_telegram_service() -> TelegramService:
    """singletone telegram"""
    return telegram_service
