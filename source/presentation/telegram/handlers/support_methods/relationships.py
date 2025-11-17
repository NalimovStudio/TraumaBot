import logging
import random
import uuid

from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
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
from source.materials.get_file import get_file_by_name
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard, \
    get_back_to_menu_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, convert_markdown_to_html

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "relationships"), SupportStates.METHOD_SELECT)
async def handle_relationships_method(
        callback_query: CallbackQuery,
        state: FSMContext
):
    """
    Старт режима Отношения.
    """
    logger.info(f"User {callback_query.from_user.id} chose relationships method")

    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    await state.set_state(SupportStates.RELATIONSHIPS)

    text = message_templates.RELATIONSHIPS_START
    photo_logo = get_file_by_name("relationships.jpeg")

    await callback_query.message.delete()

    await callback_query.message.answer_photo(
        caption=text,
        photo=photo_logo
    )
    await callback_query.answer()


@router.message(Command("stop"), SupportStates.RELATIONSHIPS)
async def handle_stop_relationships(
        message: Message,
        state: FSMContext,
        **data,
):
    """
    Остановка сессии
    """
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = str(message.from_user.id)
    context_scope = "relationships"
    logger.info(f"Пользователь {user_id} Остановил сессию relationships.")

    await state.clear()
    await history.clear_history(user_id, context_scope)
    await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
    return


@router.message(SupportStates.RELATIONSHIPS)
@inject
async def handle_relationships_talking(
        message: Message,
        state: FSMContext,
        bot: FromDishka[Bot],
        create_user_log: FromDishka[CreateUserLog],
        assistant_service: FromDishka[AssistantService],
        message_history_service: FromDishka[MessageHistoryService],
        subscription_service: FromDishka[SubscriptionService],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
):
    """
    процесс разговора с ассистентом
    """

    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)  # TODO: get from redis

    context_scope = "relationships"

    if message.text == "Вернуться в меню":
        await state.clear()
        await message_history_service.clear_history(user_telegram_id, context_scope)
        await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
        return

    # [ сохраняем лог в БД]
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
    message_history = await message_history_service.get_history(user_telegram_id, context_scope)

    try:
        message_waiting_response: Message = await message.answer(random.choice(message_templates.RELATIONSHIPS_WAITING_RESPONSE))
        # TODO: utils.get_waiting_message(support_method: SUPPORT_METHODS) + lexicon

        response = await assistant_service.get_relationships_response(message=message.text,
                                                                      context_messages=message_history)
        ai_response_text = response.message

        await message_waiting_response.delete()

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot,
                                keyboard=get_back_to_menu_keyboard())

        ai_message_context = ContextMessage(role="assistant", message=ai_response_text)
        await message_history_service.add_message_to_history(user_telegram_id, context_scope, ai_message_context)

        await subscription_service.increment_message_count(user_telegram_id)

    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_telegram_id} in scope {context_scope}: {e}")
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуй еще раз. Если проблема повторится, ты можешь вернуться в меню.",
            reply_markup=get_back_to_menu_keyboard()
        )
