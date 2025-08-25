import logging

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.core.lexicon.bot import CALMING_EXERCISE_TEXT
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, CalmingCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_calming_keyboard,
    get_main_keyboard,
    get_support_methods_keyboard, get_back_to_menu_keyboard,
)
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message
from source.presentation.telegram.utils import convert_markdown_to_html


logger = logging.getLogger(__name__)
router = Router(name=__name__)



@router.callback_query(MethodCallback.filter(F.name == "calm"), SupportStates.METHOD_SELECT)
async def handle_calm_down_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'calm' method.")
    await state.set_state(SupportStates.CALMING)
    await query.message.edit_text(CALMING_EXERCISE_TEXT, reply_markup=get_calming_keyboard())
    await query.answer()


@router.callback_query(CalmingCallback.filter(), SupportStates.CALMING)
async def handle_calming_feedback(query: CallbackQuery, callback_data: CalmingCallback, state: FSMContext):
    action = callback_data.action
    logger.info(f"User {query.from_user.id} chose '{action}' in calming flow.")

    if action == "another_cycle":
        await query.answer("Хорошо, давай попробуем еще раз.")
        await query.message.edit_text(CALMING_EXERCISE_TEXT, reply_markup=get_calming_keyboard())

    elif action == "feel_better":
        await state.clear()
        await query.message.edit_text(
            "Я рад, что тебе стало немного легче. Помни, что ты можешь вернуться к этому упражнению в любой момент.",
            reply_markup=None
        )
        await query.message.answer(
            "Ты можешь выбрать другой метод или начать новый диалог.",
            reply_markup=get_main_keyboard()
        )
        await query.answer()

    elif action == "to_talk":
        await state.set_state(SupportStates.CALMING_TALK)
        await query.message.answer(
            "Конечно, я здесь, чтобы выслушать. Расскажи, что у тебя на уме. Когда захочешь закончить, просто нажми на кнопку ниже.",
            reply_markup=get_back_to_menu_keyboard()
        )
        await query.answer()


@router.message(SupportStates.CALMING_TALK)
async def handle_calming_talk(
    message: Message,
    state: FSMContext,
    assistant: FromDishka[AssistantService],
    history: FromDishka[MessageHistoryService],
    bot: Bot,
):
    user_id = message.from_user.id
    context_scope = "calming"

    if message.text == "Вернуться в меню":
        await state.clear()
        await history.clear_history(user_id, context_scope)
        await message.answer("Хорошо, возвращаю тебя в главное меню.", reply_markup=get_main_keyboard())
        return

    user_message_context = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message_context)
    message_history = await history.get_history(user_id, context_scope)

    try:
        response = await assistant.get_speak_out_response(
            message=message.text,
            context_messages=message_history
        )
        ai_response_text = response.message

        ai_message_context = ContextMessage(role="assistant", message=ai_response_text)
        await history.add_message_to_history(user_id, context_scope, ai_message_context)

        await send_long_message(message, convert_markdown_to_html(ai_response_text), bot, keyboard=get_back_to_menu_keyboard())

    except Exception as e:
        logger.error(f"Failed to get AI response for user {user_id} in scope {context_scope}: {e}")
        await message.answer(
            "Произошла ошибка. Пожалуйста, попробуй еще раз. Если проблема повторится, ты можешь вернуться в меню.",
            reply_markup=get_back_to_menu_keyboard()
        )
