import logging
import uuid

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.core.lexicon.bot import CALMING_EXERCISE_TEXT
from source.core.schemas.assistant_schemas import ContextMessage
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, CalmingCallback
from source.presentation.telegram.keyboards.keyboards import get_calming_keyboard, get_main_keyboard, \
    get_back_to_menu_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html, log_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "calm"), SupportStates.METHOD_SELECT)
async def handle_calm_down_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'calm' method.")
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    await state.set_state(SupportStates.CALMING)
    await query.message.edit_text(CALMING_EXERCISE_TEXT, reply_markup=get_calming_keyboard())
    await query.answer()


@router.callback_query(CalmingCallback.filter(), SupportStates.CALMING)
async def handle_calming_feedback(query: CallbackQuery, callback_data: CalmingCallback, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    action = callback_data.action
    logger.info(f"User {query.from_user.id} chose '{action}' in calming flow.")
    user_id = query.from_user.id
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    
    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, f"User action: {action}", "user")

    if action == "another_cycle":
        await query.answer("Хорошо, давай попробуем еще раз.")
        await query.message.edit_text(CALMING_EXERCISE_TEXT, reply_markup=get_calming_keyboard())

    elif action == "feel_better":
        await state.clear()
        await query.message.edit_text("Я рад, что тебе стало немного легче. Помни, что ты можешь вернуться к этому упражнению в любой момент.", reply_markup=None)
        await query.message.answer("Ты можешь выбрать другой метод или начать новый диалог.", reply_markup=get_main_keyboard())
        await query.answer()

    elif action == "to_talk":
        await state.set_state(SupportStates.CALMING_TALK)
        await query.message.answer("Конечно, я здесь, чтобы выслушать. Расскажи, что у тебя на уме. Когда захочешь закончить, просто нажми на кнопку ниже.", reply_markup=get_back_to_menu_keyboard())
        await query.answer()


@router.message(SupportStates.CALMING_TALK)
async def handle_calming_talk(message: Message, state: FSMContext, bot: Bot, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_id = message.from_user.id
    context_scope = "calming"

    if message.text == "Вернуться в меню":
        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, "User action: Вернуться в меню", "user")
        await state.clear()
        await history.clear_history(user_id, context_scope)
        await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
        return

    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    message_history = await history.get_history(user_id, context_scope)

    try:
        response = await assistant.get_calm_response(message=message.text, context_messages=message_history)
        ai_response_text = response.message
        
        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, ai_response_text, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=ai_response_text))
        
        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot, keyboard=get_back_to_menu_keyboard())
        await subscription_service.increment_message_count(str(user_id))

    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_id} in scope {context_scope}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуй еще раз. Если проблема повторится, ты можешь вернуться в меню.", reply_markup=get_back_to_menu_keyboard())