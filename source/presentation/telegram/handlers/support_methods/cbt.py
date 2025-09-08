import logging
import uuid

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.core.lexicon.prompts import KPT_DIARY_PROMPT
from source.core.schemas.assistant_schemas import ContextMessage
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html, log_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "cbt"), SupportStates.METHOD_SELECT)
async def handle_cbt_method(query: CallbackQuery, state: FSMContext):
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    # TODO CBT
    await query.answer("Эта функция находится в разработке.", show_alert=True)


@router.message(SupportStates.CBT_S1_SITUATION)
async def handle_cbt_s1_situation(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    
    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_situation=message.text)
    await state.set_state(SupportStates.CBT_S2_EMOTIONS)
    text = "Понял. Какие эмоции ты испытал? Назови их и оцени интенсивность от 0 до 100."
    await message.answer(text)


@router.message(SupportStates.CBT_S2_EMOTIONS)
async def handle_cbt_s2_emotions(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_emotions=message.text)
    await state.set_state(SupportStates.CBT_S3_THOUGHT)
    text = "Спасибо. Какая автоматическая мысль промелькнула у тебя в голове в тот момент?"
    await message.answer(text)


@router.message(SupportStates.CBT_S3_THOUGHT)
async def handle_cbt_s3_thought(message: Message, state: FSMContext, bot: Bot, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    user_id = message.from_user.id
    context_scope = "cbt"
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_thought=message.text)
    await state.set_state(SupportStates.CBT_S4_DISTORTIONS)
    
    message_history = await history.get_history(user_id, context_scope)
    cbt_prompt = KPT_DIARY_PROMPT.format(
        situation=state_data.get('cbt_situation', 'не указана'),
        emotions=state_data.get('cbt_emotions', 'не указаны'),
        thought=state_data.get('cbt_thought', 'не указана')
    )

    try:
        response = await assistant.get_kpt_diary_response(message=message.text, context_messages=message_history, prompt=cbt_prompt)
        ai_response_text = response.message
        
        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, ai_response_text, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=ai_response_text))

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot)
    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_id} in scope {context_scope}: {e}")
        pass

    text = "Хорошо. А теперь, опираясь на сказанное, подумай, были ли в этой мысли когнитивные искажения? Например, 'чтение мыслей' или 'катастрофизация'. Можешь перечислить их."
    await message.answer(text)


@router.message(SupportStates.CBT_S4_DISTORTIONS)
async def handle_cbt_s4_distortions(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    
    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_distortions=message.text)
    await state.set_state(SupportStates.CBT_S5_EVIDENCE)
    text = "Принято. Какие есть доказательства, подтверждающие эту мысль? А какие — опровергающие?"
    await message.answer(text)


@router.message(SupportStates.CBT_S5_EVIDENCE)
async def handle_cbt_s5_evidence(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    
    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_evidence=message.text)
    await state.set_state(SupportStates.CBT_S6_ALTERNATIVE)
    text = "Отлично. А теперь попробуй сформулировать альтернативную, более сбалансированную мысль."
    await message.answer(text)


@router.message(SupportStates.CBT_S6_ALTERNATIVE)
async def handle_cbt_s6_alternative(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_alternative=message.text)
    await state.set_state(SupportStates.CBT_S7_RERATING)
    text = "Супер. А теперь вернемся к твоим эмоциям. Оцени их интенсивность сейчас, от 0 до 100."
    await message.answer(text)


@router.message(SupportStates.CBT_S7_RERATING)
async def handle_cbt_s7_rerating(message: Message, state: FSMContext, user_repo: UserRepository, dialogs_repo: UserDialogsLoggingRepository, uow: UnitOfWork, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_id = message.from_user.id
    context_scope = "cbt"

    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    
    await state.update_data(cbt_rerating=message.text)
    cbt_data = await state.get_data()
    logger.info(f"User {user_id} finished CBT entry: {cbt_data}")
    
    await state.clear()
    await history.clear_history(user_id, context_scope)
    
    text = "Спасибо, мы завершили запись в дневнике. Это был важный шаг.\n\nВозвращаю тебя в главное меню."
    await message.answer(text, reply_markup=get_main_keyboard())