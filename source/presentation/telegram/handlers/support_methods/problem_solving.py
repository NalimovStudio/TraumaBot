import json
import logging

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka import AsyncContainer

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.message_history.message_history_service import MessageHistoryService
from source.application.subscription.subscription_service import SubscriptionService
from source.core.schemas.assistant_schemas import ContextMessage
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, ProblemSolvingCallback
from source.core.lexicon.prompts import PATHWAYS_TO_SOLVE_PROBLEM_PROMPT
from source.core.lexicon.prompts import PATHWAYS_TO_SOLVE_PROBLEM_PROMPT
from source.infrastructure.database.repository.dialogs_logging_repo import UserDialogsLoggingRepository
from source.infrastructure.database.repository.user_repo import UserRepository
from source.infrastructure.database.uow import UnitOfWork
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard, get_problem_solutions_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, extract_json_from_markdown, convert_markdown_to_html, \
    log_support_dialog

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
async def handle_ps_s1_define(message: Message, state: FSMContext, **data):
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
async def handle_ps_s2_goal(message: Message, state: FSMContext, bot: Bot, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)

    user_id = message.from_user.id
    context_scope = "problem_solving"

    await message.answer("Спасибо. Я подумаю и предложу варианты действий. Минутку...")

    user_message = ContextMessage(role="user", message=message.text)
    await history.add_message_to_history(user_id, context_scope, user_message)
    message_history = await history.get_history(user_id, context_scope)

    await state.update_data(problem_goal=message.text)
    await state.set_state(SupportStates.PROBLEM_S3_OPTIONS)

    try:
        raw_response = await assistant.get_problems_solver_response(
            message=message.text,
            context_messages=message_history
        )

        logger.info(f"Запрос к нейронке для юзера {user_id} в скопе {context_scope}: {raw_response.message}")

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
        logger.error(f"Ошибка когда парсит {user_id} в скопе {context_scope}: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Попробуйте сформулировать проблему немного иначе.")
        await state.set_state(SupportStates.METHOD_SELECT)
    except Exception as e:
        logger.error(f"Неизвестная ошибка {user_id} В колледж {context_scope}: {e}")
        await message.answer("Что-то пошло не так. Пожалуйста, попробуйте позже.")
        await state.clear()
        await history.clear_history(user_id, context_scope)


@router.message(SupportStates.PROBLEM_S3_OPTIONS)
async def handle_ps_s3_text_instead_of_button(message: Message):
    await message.answer("Пожалуйста, выберите один из вариантов выше, нажав на кнопку.")


@router.callback_query(ProblemSolvingCallback.filter(F.action == "choose_option"), SupportStates.PROBLEM_S3_OPTIONS)
async def handle_ps_s3_choice(query: CallbackQuery, callback_data: ProblemSolvingCallback, state: FSMContext, bot: Bot,
                              **data):
    await query.message.edit_text("Отличный выбор. Генерирую первые шаги, минутку...")
    await query.answer()

    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)

    user_id = query.from_user.id
    context_scope = "problem_solving"

    state_data = await state.get_data()
    chosen_option_data = state_data["solutions"][callback_data.option_id]
    chosen_option_text = chosen_option_data.get('option', 'N/A')
    await state.update_data(chosen_option=chosen_option_data)

    choice_message = f"Выбран вариант: {chosen_option_text}"
    await history.add_message_to_history(
        user_id, context_scope, ContextMessage(role="user", message=choice_message)
    )

    prompt = PATHWAYS_TO_SOLVE_PROBLEM_PROMPT.format(
        problem_definition=state_data.get("problem_definition", "не определена"),
        problem_goal=state_data.get("problem_goal", "не определена"),
        chosen_option=chosen_option_text
    )

    try:
        response = await assistant.get_pathways_to_solve_problem_response(
            prompt=prompt,
            context_messages=await history.get_history(user_id, context_scope)
        )
        logger.info(f"Сгенерировало шаги для юзера {user_id}: {response.message}")


        await history.add_message_to_history(
            user_id, context_scope, ContextMessage(role="assistant", message=response.message)
        )

 
        response_text = f"{response.message}\n\nЧто думаешь об этих шагах? Какой из них кажется наиболее реальным для начала?"
        await send_long_message(
            message=query.message,
            text=convert_markdown_to_html(response_text),
            bot=bot,
            keyboard=None
        )
        await state.set_state(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)

    except Exception as e:
        logger.error(f"Ошибка при генерации для юзера {user_id}: {e}")
        await query.message.answer("Произошла ошибка при генерации шагов. Попробуйте выбрать другой вариант или начать заново.")
        await state.set_state(SupportStates.METHOD_SELECT)


@router.message(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
async def handle_ps_s4_discussion_and_log(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
    dialogs_repo: UserDialogsLoggingRepository,
    uow: UnitOfWork,
    **data
):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    user_id = message.from_user.id
    context_scope = "problem_solving"

    await history.add_message_to_history(
        user_id, context_scope, ContextMessage(role="user", message=message.text)
    )

    await log_support_dialog(
        user_id=user_id,
        context_scope=context_scope,
        history_service=history,
        user_repo=user_repo,
        dialogs_repo=dialogs_repo,
        uow=uow
    )

    text = "Договорились! Я верю, у тебя получится. Если хочешь, я могу напомнить тебе об этом. (Функция напоминаний в разработке).\n\nВозвращаю в главное меню."
    await message.answer(text, reply_markup=get_main_keyboard())

    await state.clear()
    await history.clear_history(user_id, context_scope)
