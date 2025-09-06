import json
import logging
import uuid

from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
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
    log_message

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "problem"), SupportStates.METHOD_SELECT)
async def handle_problem_solving_method(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} chose 'problem' method.")
    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)
    await state.set_state(SupportStates.PROBLEM_S1_DEFINE)
    text = "Давай разберем это по шагам. Сформулируй проблему в одном предложении."
    await query.message.edit_text(text)
    await query.answer()


@router.message(SupportStates.PROBLEM_S1_DEFINE)
async def handle_ps_s1_define(message: Message, state: FSMContext, **data):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)

    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    await log_message(dialogue_id, message.from_user.id, user_repo, dialogs_repo, uow, message.text, "user")
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
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)

    user_id = message.from_user.id
    context_scope = "problem_solving"
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    await message.answer("Спасибо. Я подумаю и предложу варианты действий. Минутку...")

    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=message.text))
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

        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, raw_response.message, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=raw_response.message))

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
        await subscription_service.increment_message_count(str(user_id))

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
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)

    user_id = query.from_user.id
    context_scope = "problem_solving"

    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    chosen_option_data = state_data["solutions"][callback_data.option_id]
    chosen_option_text = chosen_option_data.get('option', 'N/A')
    await state.update_data(chosen_option=chosen_option_data)
    
    choice_message = f"Выбран вариант: {chosen_option_text}"
    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, choice_message, "user")
    await history.add_message_to_history(user_id, context_scope, ContextMessage(role="user", message=choice_message))
    
    prompt = PATHWAYS_TO_SOLVE_PROBLEM_PROMPT.format(problem_definition=state_data.get("problem_definition"), problem_goal=state_data.get("problem_goal"), chosen_option=chosen_option_text)

    try:
        response = await assistant.get_pathways_to_solve_problem_response(prompt=prompt, context_messages=await history.get_history(user_id, context_scope))
        logger.info(f"Generated steps for user {user_id}: {response.message}")
        
        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, response.message, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=response.message))

        response_text = f"{response.message}\n\nЧто думаешь об этих шагах? Какой из них кажется наиболее реальным для начала? (Чтобы закончить, отправь /stop)"
        await send_long_message(query.message, convert_markdown_to_html(response_text), bot)
        await state.set_state(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
    except Exception as e:
        logger.error(f"Error generating steps for user {user_id}: {e}")
        await query.message.answer("Произошла ошибка при генерации шагов. Попробуйте выбрать другой вариант или начать заново.")
        await state.set_state(SupportStates.METHOD_SELECT)
    finally:
        await query.answer()


@router.message(Command("stop"), SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
async def handle_stop_problem_solving(
    message: Message,
    state: FSMContext,
    **data,
):
    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    user_id = message.from_user.id
    context_scope = "problem_solving"
    logger.info(f"User {user_id} stopped problem solving session.")

    await state.clear()
    await history.clear_history(user_id, context_scope)

    await message.answer(
        "Хорошо, мы закончили. Возвращаю в главное меню.",
        reply_markup=get_main_keyboard()
    )


@router.message(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
async def handle_ps_s4_discussion(message: Message, state: FSMContext, bot: Bot, **data):
    container: AsyncContainer = data["dishka_container"]
    assistant: AssistantService = await container.get(AssistantService)
    history: MessageHistoryService = await container.get(MessageHistoryService)
    subscription_service: SubscriptionService = await container.get(SubscriptionService)
    user_repo: UserRepository = await container.get(UserRepository)
    dialogs_repo: UserDialogsLoggingRepository = await container.get(UserDialogsLoggingRepository)
    uow: UnitOfWork = await container.get(UnitOfWork)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]

    user_id = message.from_user.id
    context_scope = "problem_solving"

    user_message = ContextMessage(role="user", message=message.text)
    await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, message.text, "user")
    await history.add_message_to_history(user_id, context_scope, user_message)
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
        response_text_html = convert_markdown_to_html(response_text)

        await log_message(dialogue_id, user_id, user_repo, dialogs_repo, uow, response_text, "assistant")
        await history.add_message_to_history(user_id, context_scope, ContextMessage(role="assistant", message=response_text))

        await send_long_message(message, response_text_html, bot)
        await subscription_service.increment_message_count(str(user_id))

    except Exception as e:
        logger.error(f"Ошибка во время дискуссии с пользователем в решении проблемы {user_id}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз или завершите сессию командой /stop.")
