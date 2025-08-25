import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from dishka.integrations.aiogram import FromDishka

from source.presentation.telegram.callbacks.method_callbacks import MethodCallback
from source.presentation.telegram.keyboards.keyboards import get_venting_summary_keyboard, get_main_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.core.schemas.assistant_schemas import ContextMessage
from source.application.subscription.subscription_service import SubscriptionService 
from source.presentation.telegram.middlewares.limit_check_middleware import LimitCheckMiddleware
from source.presentation.telegram.utils import convert_markdown_to_html

logger = logging.getLogger(__name__)
router = Router(name=__name__)

# Register middleware for messages (применится ко всем message handlers в этом router)
router.message.middleware(LimitCheckMiddleware())

@router.callback_query(MethodCallback.filter(F.name == "vent"), SupportStates.METHOD_SELECT)
async def handle_vent_out_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'vent' method.")
    await state.set_state(SupportStates.VENTING)
    text = "Можешь просто писать всё, как идёт. Я буду отвечать коротко и бережно.\n\nКогда захочешь закончить, отправь команду /stop."
    await query.message.edit_text(text, reply_markup=None)
    await query.answer()

@router.message(Command("stop"), SupportStates.VENTING)
async def handle_stop_venting(message: Message, state: FSMContext, history: FromDishka[MessageHistoryService]):
    user_id = message.from_user.id
    context_scope = "venting"
    logger.info(f"User {user_id} stopped venting session.")
    
    await state.clear()
    await history.clear_history(user_id, context_scope)
    
    await message.answer(
        "Хорошо, мы закончили. Что бы ты хотел сделать с этой беседой?",
        reply_markup=get_venting_summary_keyboard()
    )
    await message.answer("Возвращаю в главное меню.", reply_markup=get_main_keyboard())

@router.message(SupportStates.VENTING)
async def handle_venting_message(
        message: Message,
        state: FSMContext,
        assistant: FromDishka[AssistantService],
        history: FromDishka[MessageHistoryService],
        subscription_service: FromDishka[SubscriptionService]
):
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
            # Пытаемся отправить с форматированием HTML
            await message.answer(response_text_html, parse_mode=ParseMode.HTML)
        except TelegramBadRequest:
            # Если Telegram не смог распознать форматирование,
            # отправляем сообщение как обычный текст.
            logger.warning(f"Failed to parse HTML for user {user_id}. Sending plain text.")
            await message.answer(response_text)
        
        telegram_id = str(user_id)
        await subscription_service.increment_message_count(telegram_id)
        
    except Exception as e:
        logger.error(f"Error when scraping user {user_id} in scope {context_scope}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз.")