import logging

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.core.lexicon.prompts import KPT_DIARY_PROMPT
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html, log_support_dialog

logger = logging.getLogger(__name__)
router = Router(name=__name__)

@router.callback_query(MethodCallback.filter(F.name == "cbt"), SupportStates.METHOD_SELECT)
async def handle_cbt_method(query: CallbackQuery, state: FSMContext):
    await query.answer("Эта функция находится в разработке.", show_alert=True)

@router.message(SupportStates.CBT_S1_SITUATION)
async def handle_cbt_s1_situation(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_situation=message.text)
    await state.set_state(SupportStates.CBT_S2_EMOTIONS)
    text = "Понял. Какие эмоции ты испытал? Назови их и оцени интенсивность от 0 до 100."
    await message.answer(text)

@router.message(SupportStates.CBT_S2_EMOTIONS)
async def handle_cbt_s2_emotions(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_emotions=message.text)
    await state.set_state(SupportStates.CBT_S3_THOUGHT)
    text = "Спасибо. Какая автоматическая мысль промелькнула у тебя в голове в тот момент?"
    await message.answer(text)

@router.message(SupportStates.CBT_S3_THOUGHT)
async def handle_cbt_s3_thought(message: Message, state: FSMContext, bot: Bot, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = message.from_user.id
    context_scope = "cbt"
    await state.update_data(cbt_thought=message.text)
    await state.set_state(SupportStates.CBT_S4_DISTORTIONS)

    user_message = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message)
    
    state_data = await state.get_data()
    message_history = await history.get_history(user_id, context_scope)

    cbt_prompt = KPT_DIARY_PROMPT.format(
        situation=state_data.get('cbt_situation', 'не указана'),
        emotions=state_data.get('cbt_emotions', 'не указаны'),
        thought=state_data.get('cbt_thought', 'не указана')
    )

    try:
        response = await assistant.get_kpt_diary_response(message=message.text, context_messages=message_history, prompt=cbt_prompt)
        ai_response_text = response.message
        
        ai_message = ContextMessage(role="assistant", message=ai_response_text)
        await history.add_message_to_history(user_id, context_scope, ai_message)

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot)
    except Exception as e:
        logger.error(f"Ошибка для получени ИИ запроса {user_id} в скопе {context_scope}: {e}")
        pass

    text = "Хорошо. А теперь, опираясь на сказанное, подумай, были ли в этой мысли когнитивные искажения? Например, 'чтение мыслей' или 'катастрофизация'. Можешь перечислить их."
    await message.answer(text)

@router.message(SupportStates.CBT_S4_DISTORTIONS)
async def handle_cbt_s4_distortions(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_distortions=message.text)
    await state.set_state(SupportStates.CBT_S5_EVIDENCE)
    text = "Принято. Какие есть доказательства, подтверждающие эту мысль? А какие — опровергающие?"
    await message.answer(text)

@router.message(SupportStates.CBT_S5_EVIDENCE)
async def handle_cbt_s5_evidence(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    
    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_evidence=message.text)
    await state.set_state(SupportStates.CBT_S6_ALTERNATIVE)
    text = "Отлично. А теперь попробуй сформулировать альтернативную, более сбалансированную мысль."
    await message.answer(text)

@router.message(SupportStates.CBT_S6_ALTERNATIVE)
async def handle_cbt_s6_alternative(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    await history.add_message_to_history(message.from_user.id, "cbt", ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_alternative=message.text)
    await state.set_state(SupportStates.CBT_S7_RERATING)
    text = "Супер. А теперь вернемся к твоим эмоциям. Оцени их интенсивность сейчас, от 0 до 100."
    await message.answer(text)

@router.message(SupportStates.CBT_S7_RERATING)
async def handle_cbt_s7_rerating(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
    dialogs_repo: UserDialogsLoggingRepository,
    uow: UnitOfWork,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = message.from_user.id
    context_scope = "cbt"
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    await state.update_data(cbt_rerating=message.text)
    cbt_data = await state.get_data()
    logger.info(f"User {user_id} finished CBT entry: {cbt_data}")

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

    text = "Спасибо, мы завершили запись в дневнике. Это был важный шаг. Я сохраню эту запись, если ты не против.\n\nВозвращаю тебя в главное меню."
    await message.answer(text, reply_markup=get_main_keyboard())