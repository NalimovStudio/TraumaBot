import logging
import random

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.core.lexicon.bot import BLACKPILL_EXIT_TEXT, BLACKPILL_AFTER_READY_TEXT_ARRAY
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, BlackpillCallback
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, BlackpillCallback
from source.presentation.telegram.keyboards.keyboards import get_blackpill_exit_ready_keyboard
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard, \
    get_back_to_menu_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html, log_support_dialog

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "blackpill_exit"), SupportStates.METHOD_SELECT)
async def handle_blackpill_method(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} chose blackpill method")
    await state.set_state(SupportStates.BLACKPILL)
    await callback.message.edit_text(BLACKPILL_EXIT_TEXT, reply_markup=get_blackpill_exit_ready_keyboard())
    await callback.answer()


@router.callback_query(BlackpillCallback.filter(), SupportStates.BLACKPILL)
async def handle_ready_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.BLACKPILL_TALK)
    await callback.message.edit_text(random.choice(BLACKPILL_AFTER_READY_TEXT_ARRAY))
    await callback.answer()

@router.message(Command("stop"), SupportStates.BLACKPILL)
async def handle_stop_blackpill(
    message: Message,
    state: FSMContext,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = message.from_user.id
    context_scope = "blackpill_exit"
    logger.info(f"Пользователь {user_id} Остановил сессию blackpill.")

    await log_support_dialog(
            user_id=user_id,
            context_scope=context_scope,
            history_service=history,
            user_repo=user_repo,
            dialogs_repo=dialogs_repo,
            uow=uow,
        )
    
    await state.clear()
    await history.clear_history(user_id, context_scope)
    await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
    return

@router.message(SupportStates.BLACKPILL)
async def handle_blackpill_talking(
    message: Message,
    state: FSMContext,
    bot: Bot,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)

    user_id = message.from_user.id
    context_scope = "blackpill_exit" 

    user_message_context = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message_context)
    message_history = await history.get_history(user_id, context_scope)

    try:
        await message.answer(
        "Хорошо, думаю над ответом...\n\n💢Когда захочешь закончить со мной общаться, отправь команду /stop."
        )
        response = await assistant.get_blackpill_exit_response(message=message.text, context_messages=message_history)
        ai_response_text = response.message

        ai_message_context = ContextMessage(role="assistant", message=ai_response_text)
        await history.add_message_to_history(user_id, context_scope, ai_message_context)

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot,
                                keyboard=get_back_to_menu_keyboard())
        telegram_id = str(user_id)
        await subscription_service.increment_message_count(telegram_id)

    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_id} in scope {context_scope}: {e}")
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуй еще раз. Если проблема повторится, ты можешь вернуться в меню.",
            reply_markup=get_back_to_menu_keyboard()
        )
