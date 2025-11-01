import logging
import uuid

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
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
from source.core.lexicon.message_templates import VENTING_START
from source.core.schemas import UserLogCreateSchema, UserSchema
from source.core.schemas.assistant_schemas import ContextMessage
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.application.user import GetUserSchemaById
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import convert_markdown_to_html, log_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "vent"), SupportStates.METHOD_SELECT)
async def handle_vent_out_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'vent' method.")
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    await state.set_state(SupportStates.VENTING)

    text = VENTING_START
    photo_logo = get_file_by_name("высказаться.jpg")

    await query.message.delete()

    await query.message.answer_photo(
        caption=text,
        photo=photo_logo
    )
    await query.answer()

@router.message(Command("stop"), SupportStates.VENTING)
async def handle_stop_venting(
    message: Message,
    state: FSMContext,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_telegram_id = str(message.from_user.id)
    context_scope = "venting"
    logger.info(f"Пользователь {user_id} Остановил сессию высказаться.")

    await state.clear()
    await history.clear_history(user_telegram_id, context_scope)

    await message.answer(
        "Хорошо, мы закончили. Возвращаю в главное меню.",
        reply_markup=get_main_keyboard()
    )


@router.message(SupportStates.VENTING)
async def handle_venting_message(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)
    user_repo: GetUserSchemaById = await container.get(GetUserSchemaById)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)

    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    user_id = message.from_user.id
    context_scope = "venting"
    logger.info(f"User {user_telegram_id} is venting. Msg: '{message.text[:30]}...'")

    # [ сохраняем лог в БД]
    await create_user_log(
        user_log=UserLogCreateSchema(
            dialog_id=dialogue_id,
            message_text=message.text,
            user_id=user.id
        )
    )
    logger.info(f"User log created: dialog_id = {dialogue_id}")


    await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
    message_history = await history.get_history(user_id, context_scope)

    try:
        await message.answer(
        "Хорошо, думаю над ответом...\n\n💢Когда захочешь закончить со мной общаться, отправь команду /stop."
        )
        response = await assistant.get_speak_out_response(
            message=message.text,
            context_messages=message_history
        )
        response_text = response.message

        await message_history_service.add_message_to_history(
            user_telegram_id, context_scope, ContextMessage(role="assistant", message=response_text)
        )

        response_text_html = convert_markdown_to_html(response_text)

        await log_message(dialogue_id, str(user_id), user_repo, dialogs_repo, uow, response_text, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=response_text))

        try:
            await message.answer(response_text_html, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            logger.warning(f"Ошибка при парсинге HTML для юзера {user_id}. Отправляем обычный текст.")
            await message.answer(response_text)

        await subscription_service.increment_message_count(str(user_id))

    except Exception as e:
        logger.error(f"Ошибка при обработке информации юзера {user_id} в скопе {context_scope}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
