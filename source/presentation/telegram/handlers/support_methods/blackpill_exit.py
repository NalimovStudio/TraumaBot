import logging
import random
import uuid

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from dishka import AsyncContainer
from dishka.integrations.aiogram import inject, FromDishka

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.redis_services.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.application.user import GetUserSchemaById
from source.application.user.user_logs import CreateUserLog
from source.core.lexicon import message_templates
from source.core.schemas import UserLogCreateSchema, UserSchema
from source.core.schemas.assistant_schemas import ContextMessage
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.application.user import GetUserSchemaById
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, BlackpillCallback
from source.presentation.telegram.keyboards.keyboards import get_blackpill_exit_ready_keyboard, get_main_keyboard, \
    get_back_to_menu_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html, log_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "blackpill_exit"), SupportStates.METHOD_SELECT)
async def handle_blackpill_method(callback: CallbackQuery, state: FSMContext):
    logger.info(f"User {callback.from_user.id} chose blackpill method")
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    await state.set_state(SupportStates.BLACKPILL)

    text = message_templates.BLACKPILL_START
    photo_logo = get_file_by_name("побегБП.jpg")

@router.callback_query(BlackpillCallback.filter(), SupportStates.BLACKPILL)
async def handle_ready_callback(callback: CallbackQuery, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    user_repo: GetUserSchemaById = await container.get(GetUserSchemaById)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_id = callback.from_user.id
    
    response_text = random.choice(BLACKPILL_AFTER_READY_TEXT_ARRAY)
    
    await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, "User action: Ready", "user")
    await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, response_text, "assistant")

    await callback.message.edit_text(response_text)
    await callback.answer()

@router.message(Command("stop"), SupportStates.BLACKPILL)
async def handle_stop_blackpill(
    message: Message,
    state: FSMContext,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = message.from_user.id
    context_scope = "blackpill_exit"
    logger.info(f"Пользователь {user_id} Остановил сессию blackpill.")
    
    await state.clear()
    await history.clear_history(user_id, context_scope)
    await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
    return




@router.message(Command("stop"), SupportStates.BLACKPILL)
async def handle_stop_blackpill(
        message: Message,
        state: FSMContext,
        **data,
):
    """
    Остановка сессии
    """
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)
    user_repo: GetUserSchemaById = await container.get(GetUserSchemaById)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_id = message.from_user.id
    context_scope = "blackpill_exit"

    if message.text == "Вернуться в меню":
        await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, "User action: Вернуться в меню", "user")
        await state.clear()
        await message_history_service.clear_history(user_telegram_id, context_scope)
        await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
        return

    await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    message_history = await history.get_history(user_id, context_scope)

    try:
        await message.answer(
        "Хорошо, думаю над ответом...\n\n💢Когда захочешь закончить со мной общаться, отправь команду /stop."
        )
        response = await assistant.get_blackpill_exit_response(message=message.text, context_messages=message_history)
        ai_response_text = response.message
        
        await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, ai_response_text, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=ai_response_text))
        
        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot, keyboard=get_back_to_menu_keyboard())
        await subscription_service.increment_message_count(str(user_id))

    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_id} in scope {context_scope}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуй еще раз. Если проблема повторится, ты можешь вернуться в меню.", reply_markup=get_back_to_menu_keyboard())
