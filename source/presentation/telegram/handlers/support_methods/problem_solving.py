import logging
import json

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, ProblemSolvingCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard, get_problem_solutions_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.utils import send_long_message, extract_json_from_markdown, convert_markdown_to_html
from source.application.subscription.subscription_service import SubscriptionService 

logger = logging.getLogger(__name__)
router = Router(name=__name__)

@router.callback_query(MethodCallback.filter(F.name == "problem"), SupportStates.METHOD_SELECT)
async def handle_problem_solving_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'problem' method.")
    await state.set_state(SupportStates.PROBLEM_S1_DEFINE)
    text = "Давай разберем это по шагам. Сформулируй проблему в одном предложении."
    await query.message.edit_text(text)
    await query.answer()

@router.message(SupportStates.PROBLEM_S1_DEFINE)
async def handle_ps_s1_define(message: Message, state: FSMContext, data: dict):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    
    await history.add_message_to_history(
        message.from_user.id, "problem_solving", ContextMessage(role="user", message=message.text)
    )
    await state.update_data(problem_definition=message.text)
    await state.set_state(SupportStates.PROBLEM_S2_GOAL)
    text = "Хорошо. А как ты поймешь, что проблема решена? Что будет твоим критерием успеха?"
    await message.answer(text)

@router.message(SupportStates.PROBLEM_S2_GOAL)
async def handle_ps_s2_goal(message: Message, state: FSMContext, bot: Bot, data: dict):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)
    
    user_id = message.from_user.id
    context_scope = "problem_solving"

    user_message = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message)
    message_history = await history.get_history(user_id, context_scope)

    await state.update_data(problem_goal=message.text)
    await state.set_state(SupportStates.PROBLEM_S3_OPTIONS)
    await message.answer("Спасибо. Я подумаю и предложу варианты действий. Минутку...")

    try:
        raw_response = await assistant.get_problems_solver_response(
            message=message.text,
            context_messages=message_history
        )
        
        logger.info(f"Raw AI response for user {user_id} in scope {context_scope}: {raw_response.message}")
        
        json_string = extract_json_from_markdown(raw_response.message)
        solutions = json.loads(json_string)

        ai_message = ContextMessage(role="assistant", message=raw_response.message)
        await history.add_message_to_history(user_id, context_scope, ai_message)

        await state.update_data(solutions=solutions)

        response_text = "Вот несколько вариантов:\n\n"
        for i, sol in enumerate(solutions):
            response_text += f"<b>Вариант {i + 1}:</b> {sol.get('option', 'N/A')}\n"
            response_text += f"<i>Плюсы:</i> {sol.get('pros', 'N/A')}\n"
            response_text += f"<i>Риски:</i> {sol.get('cons', 'N/A')}\n\n"

        response_text += "Какой из вариантов тебе кажется наиболее подходящим сейчас?"
        await send_long_message(
            message=message,
            text=convert_markdown_to_html(response_text),
            bot=bot,
            keyboard=get_problem_solutions_keyboard()
        )
        telegram_id = str(user_id)
        await subscription_service.increment_message_count(telegram_id)
        
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        logger.error(f"Error when scraping {user_id} in scope {context_scope}: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Попробуйте сформулировать проблему немного иначе.")
        await state.set_state(SupportStates.METHOD_SELECT)
    except Exception as e:
        logger.error(f"Unknown error {user_id} in scope {context_scope}: {e}")
        await message.answer("Что-то пошло не так. Пожалуйста, попробуйте позже.")
        await state.clear()
        await history.clear_history(user_id, context_scope)

@router.callback_query(ProblemSolvingCallback.filter(F.action == "choose_option"), SupportStates.PROBLEM_S3_OPTIONS)
async def handle_ps_s3_choice(query: CallbackQuery, callback_data: ProblemSolvingCallback, state: FSMContext):
    await state.set_state(SupportStates.PROBLEM_S4_CHOICE)
    data = await state.get_data()
    chosen_option = data["solutions"][callback_data.option_id]
    await state.update_data(chosen_option=chosen_option)

    text = f"Отличный выбор. Теперь давай разобьем '{chosen_option['option']}' на самый маленький первый шаг, который можно сделать за 10-15 минут."
    await query.message.edit_text(text)
    await query.answer()

@router.message(SupportStates.PROBLEM_S4_CHOICE)
async def handle_ps_s4_step(message: Message, state: FSMContext, data: dict):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    await history.add_message_to_history(
        message.from_user.id, "problem_solving", ContextMessage(role="user", message=message.text)
    )
    await state.update_data(problem_step=message.text)
    await state.set_state(SupportStates.PROBLEM_S5_PACT)
    text = "Супер. Это звучит как отличный, выполнимый шаг. Давай заключим 'пакт'. Когда ты планируешь это сделать? (Например, 'сегодня вечером' или 'завтра в 12:00')."
    await message.answer(text)

@router.message(SupportStates.PROBLEM_S5_PACT)
async def handle_ps_s5_pact(message: Message, state: FSMContext, data: dict):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = message.from_user.id
    context_scope = "problem_solving"
    await history.add_message_to_history(
        user_id, context_scope, ContextMessage(role="user", message=message.text)
    )
    await state.update_data(problem_pact=message.text)
    logger.info(f"User {user_id} finished Problem-Solving entry: {await state.get_data()}")
    
    await state.clear()
    await history.clear_history(user_id, context_scope)
    
    text = "Договорились! Я верю, у тебя получится. Если хочешь, я могу напомнить тебе об этом. (Функция напоминаний в разработке).\n\nВозвращаю в главное меню."
    await message.answer(text, reply_markup=get_main_keyboard())