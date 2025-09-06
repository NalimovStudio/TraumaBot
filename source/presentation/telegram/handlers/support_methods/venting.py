import logging

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.core.schemas.assistant_schemas import ContextMessage
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import convert_markdown_to_html, log_support_dialog

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "vent"), SupportStates.METHOD_SELECT)
async def handle_vent_out_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'vent' method.")
    await state.set_state(SupportStates.VENTING)
    text = "Можешь просто писать всё, как идёт. Я буду отвечать коротко и бережно. (в течении 5-10 сек)\n\n💢Когда захочешь закончить со мной общаться, отправь команду /stop."
    await query.message.edit_text(text, reply_markup=None)
    await query.answer()


@router.message(Command("stop"), SupportStates.VENTING)
async def handle_stop_venting(
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
    context_scope = "venting"
    logger.info(f"User {user_id} stopped venting session.")

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

    user_id = message.from_user.id
    context_scope = "venting"
    logger.info(f"User {user_id} is venting. Msg: '{message.text[:30]}...'")

    user_message = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message)
    message_history = await history.get_history(user_id, context_scope)

    try:
        response = await assistant.get_speak_out_response(
            message=message.text,
            context_messages=message_history
        )
        response_text = response.message
        response_text_html = convert_markdown_to_html(response_text)

        ai_message = ContextMessage(role="assistant", message=response_text)
        await history.add_message_to_history(user_id, context_scope, ai_message)

        try:
            await message.answer(response_text_html, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            logger.warning(f"Ошибка при парсинге HTML для юзера {user_id}. Отправляем обычный текст.")
            await message.answer(response_text)

        telegram_id = str(user_id)
        await subscription_service.increment_message_count(telegram_id)

    except Exception as e:
        logger.error(f"Ошибка при обработке информации юзера {user_id} в скопе {context_scope}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")
