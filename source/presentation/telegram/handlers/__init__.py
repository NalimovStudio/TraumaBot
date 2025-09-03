from aiogram import Router

from .check_in import router as check_in_router
from .main_menu import router as main_menu_router
from .risk_protocol import router as risk_protocol_router
from .start import router as start_router
from .subscription import router as subscription_router
from .support_methods import (
    calming_router,
    cbt_router,
    problem_solving_router,
    venting_router,
    blackpill_exit_router
)

handlers_router = Router(name="main_handlers_router")

# Порядок подключения роутеров важен, если их фильтры пересекаются.
# В нашем случае большинство хендлеров привязаны к разным состояниям,
# командам или колбэкам, поэтому конфликтов быть не должно.
# Группируем для логической читаемости.
handlers_router.include_routers(
    # Команды (самый высокий приоритет)
    start_router,
    # Навигация по главному меню (Reply-кнопки)
    main_menu_router,
    # Обработка колбэков подписки
    subscription_router,
    # Начальный диалог
    check_in_router,
    # Потоки поддержки
    calming_router,
    cbt_router,
    problem_solving_router,
    venting_router,
    blackpill_exit_router,
    # Протокол безопасности (срабатывает только в своем состоянии)
    risk_protocol_router,
)

__all__ = ["handlers_router"]