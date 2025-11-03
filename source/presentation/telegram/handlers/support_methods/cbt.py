import logging
import uuid

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.redis_services.message_history.message_history_service import MessageHistoryService
from source.application.user import GetUserSchemaById
from source.application.user.user_logs import CreateUserLog
from source.core.lexicon.prompts import KPT_DIARY_PROMPT
from source.core.schemas import UserLogCreateSchema, UserSchema
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html
from dishka.integrations.aiogram import inject, FromDishka

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "cbt"), SupportStates.METHOD_SELECT)
async def handle_cbt_method(
        query: CallbackQuery,
        state: FSMContext,
):
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)

    # TODO CBT
    await query.answer("Эта функция находится в разработке.", show_alert=True)


@router.message(SupportStates.CBT_S1_SITUATION)
@inject
async def handle_cbt_s1_situation(
        message: Message,
        state: FSMContext,
        create_user_log: FromDishka[CreateUserLog],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
        message_history_service: FromDishka[MessageHistoryService],
):
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    context_scope = "cbt"

    # [ сохраняем лог сообщения пользователя в БД]
    await create_user_log(
        user_log=UserLogCreateSchema(
            dialog_id=dialogue_id,
            message_text=message.text,
            user_id=user.id
        )
    )
    logger.info(f"User log created: dialog_id = {dialogue_id}")

    await message_history_service.add_message_to_history(
        user_telegram_id, context_scope, ContextMessage(role="user", message=message.text)
    )

    await state.update_data(cbt_situation=message.text)
    await state.set_state(SupportStates.CBT_S2_EMOTIONS)
    text = "Понял. Какие эмоции ты испытал? Назови их и оцени интенсивность от 0 до 100."
    await message.answer(text)


@router.message(SupportStates.CBT_S2_EMOTIONS)
async def handle_cbt_s2_emotions(
        message: Message,
        state: FSMContext,
        create_user_log: FromDishka[CreateUserLog],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
        message_history_service: FromDishka[MessageHistoryService],
):
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    context_scope = "cbt"

    # [ сохраняем лог сообщения пользователя в БД]
    await create_user_log(
        user_log=UserLogCreateSchema(
            dialog_id=dialogue_id,
            message_text=message.text,
            user_id=user.id
        )
    )
    logger.info(f"User log created: dialog_id = {dialogue_id}")

    await message_history_service.add_message_to_history(
        user_telegram_id, context_scope, ContextMessage(role="user", message=message.text)
    )

    await state.update_data(cbt_emotions=message.text)
    await state.set_state(SupportStates.CBT_S3_THOUGHT)
    text = "Спасибо. Какая автоматическая мысль промелькнула у тебя в голове в тот момент?"
    await message.answer(text)


@router.message(SupportStates.CBT_S3_THOUGHT)
@inject
async def handle_cbt_s3_thought(
        message: Message,
        state: FSMContext,
        bot: Bot,
        create_user_log: FromDishka[CreateUserLog],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
        assistant_service: FromDishka[AssistantService],
        message_history_service: FromDishka[MessageHistoryService],
):
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)
    context_scope = "cbt"
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    # [ сохраняем лог сообщения пользователя в БД]
    await create_user_log(
        user_log=UserLogCreateSchema(
            dialog_id=dialogue_id,
            message_text=message.text,
            user_id=user.id
        )
    )
    logger.info(f"User log created: dialog_id = {dialogue_id}")

    await message_history_service.add_message_to_history(
        user_telegram_id, context_scope, ContextMessage(role="user", message=message.text)
    )

    await state.update_data(cbt_thought=message.text)
    await state.set_state(SupportStates.CBT_S4_DISTORTIONS)

    message_history = await message_history_service.get_history(user_telegram_id, context_scope)
    cbt_prompt = KPT_DIARY_PROMPT.format(
        situation=state_data.get('cbt_situation', 'не указана'),
        emotions=state_data.get('cbt_emotions', 'не указаны'),
        thought=state_data.get('cbt_thought', 'не указана')
    )

    try:
        response = await assistant_service.get_kpt_diary_response(
            message=message.text,
            context_messages=message_history,
            prompt=cbt_prompt
        )
        ai_response_text = response.message

        await message_history_service.add_message_to_history(
            user_telegram_id, context_scope, ContextMessage(role="assistant", message=ai_response_text)
        )

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot)
    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_telegram_id} in scope {context_scope}: {e}")
        pass

    text = "Хорошо. А теперь, опираясь на сказанное, подумай, были ли в этой мысли когнитивные искажения? Например, 'чтение мыслей' или 'катастрофизация'. Можешь перечислить их."
    await message.answer(text)

# Аналогично для остальных CBT шагов - применяем ту же логику
