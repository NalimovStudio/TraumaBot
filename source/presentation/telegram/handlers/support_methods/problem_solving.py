import json
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
from source.core.lexicon.message_templates import PROBLEM_SOLVING_START
from source.core.lexicon.prompts import PATHWAYS_TO_SOLVE_PROBLEM_PROMPT
from source.core.schemas import UserLogCreateSchema, UserSchema
from source.core.schemas.assistant_schemas import ContextMessage
from source.materials.get_file import get_file_by_name
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback, ProblemSolvingCallback
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard, get_problem_solutions_keyboard
from source.presentation.telegram.states.user_states import SupportStates
from source.presentation.telegram.utils import send_long_message, extract_json_from_markdown, convert_markdown_to_html

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(MethodCallback.filter(F.name == "problem"), SupportStates.METHOD_SELECT)
async def handle_problem_solving_method(
        query: CallbackQuery,
        state: FSMContext
):
    logger.info(f"User {query.from_user.id} chose 'problem' method.")

    dialogue_id = uuid.uuid4()
    await state.update_data(dialogue_id=dialogue_id)

    await state.set_state(SupportStates.PROBLEM_S1_DEFINE)

    text = PROBLEM_SOLVING_START
    photo_logo = get_file_by_name("решениепроблем.jpg")

    await query.message.delete()

    await query.message.answer_photo(
        caption=text,
        photo=photo_logo
    )
    await query.answer()


@router.message(SupportStates.PROBLEM_S1_DEFINE)
@inject
async def handle_ps_s1_define(
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
    context_scope = "problem_solving"

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

    await state.update_data(problem_definition=message.text)
    await state.set_state(SupportStates.PROBLEM_S2_GOAL)
    text = "Хорошо. А как ты поймешь, что проблема решена? Что будет твоим критерием успеха?"
    await message.answer(text)


@router.message(SupportStates.PROBLEM_S2_GOAL)
@inject
async def handle_ps_s2_goal(
        message: Message,
        state: FSMContext,
        bot: FromDishka[Bot],
        create_user_log: FromDishka[CreateUserLog],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
        assistant_service: FromDishka[AssistantService],
        message_history_service: FromDishka[MessageHistoryService],
        subscription_service: FromDishka[SubscriptionService],
):
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    context_scope = "problem_solving"

    # [ сохраняем лог сообщения пользователя в БД ]
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

    message: Message = await message.answer("Спасибо. Я подумаю и предложу варианты действий. Минутку...")

    message_waiting_response: Message = await message.answer(
        random.choice(message_templates.PROBLEMS_SOLVER_WAITING_RESPONSE)
    )
    # TODO: utils.get_waiting_message(support_method: SUPPORT_METHODS) + lexicon

    message_history = await message_history_service.get_history(user_telegram_id, context_scope)

    await state.update_data(problem_goal=message.text)
    await state.set_state(SupportStates.PROBLEM_S3_OPTIONS)

    try:
        raw_response = await assistant_service.get_problems_solver_response(
            message=message.text,
            context_messages=message_history
        )
        logger.info(f"Raw AI response for user {user_telegram_id} in scope {context_scope}: {raw_response.message}")

        await message_history_service.add_message_to_history(
            user_telegram_id, context_scope, ContextMessage(role="assistant", message=raw_response.message)
        )

        json_string = extract_json_from_markdown(raw_response.message)
        solutions = json.loads(json_string)
        await state.update_data(solutions=solutions)

        response_text = "Вот несколько вариантов:\n\n"
        for i, sol in enumerate(solutions):
            response_text += f"<b>Вариант {i + 1}:</b> {sol.get('option', 'N/A')}\n"
            response_text += f"<i>Плюсы:</i> {sol.get('pros', 'N/A')}\n"
            response_text += f"<i>Риски:</i> {sol.get('cons', 'N/A')}\n\n"
        response_text += "Какой из вариантов тебе кажется наиболее подходящим сейчас?"

        await message_waiting_response.delete()

        await send_long_message(message, convert_markdown_to_html(response_text), bot, get_problem_solutions_keyboard())
        await subscription_service.increment_message_count(user_telegram_id)

    except Exception as e:
        logger.error(f"Error in handle_ps_s2_goal for user {user_telegram_id}: {e}")
        await message.answer("Произошла ошибка при обработке ответа. Попробуйте сформулировать проблему немного иначе.")
        await state.set_state(SupportStates.METHOD_SELECT)


@router.callback_query(ProblemSolvingCallback.filter(F.action == "choose_option"), SupportStates.PROBLEM_S3_OPTIONS)
@inject
async def handle_ps_s3_choice(
        query: CallbackQuery,
        callback_data: ProblemSolvingCallback,
        state: FSMContext,
        bot: FromDishka[Bot],
        assistant_service: FromDishka[AssistantService],
        message_history_service: FromDishka[MessageHistoryService],
):
    await query.message.edit_text("Отличный выбор. Генерирую первые шаги, минутку...")

    user_telegram_id = str(query.from_user.id)
    context_scope = "problem_solving"
    state_data = await state.get_data()

    chosen_option_data = state_data["solutions"][callback_data.option_id]
    chosen_option_text = chosen_option_data.get('option', 'N/A')
    await state.update_data(chosen_option=chosen_option_data)

    choice_message = f"Выбран вариант: {chosen_option_text}"

    await message_history_service.add_message_to_history(
        user_telegram_id, context_scope, ContextMessage(role="user", message=choice_message)
    )

    prompt = PATHWAYS_TO_SOLVE_PROBLEM_PROMPT.format(
        problem_definition=state_data.get("problem_definition"),
        problem_goal=state_data.get("problem_goal"),
        chosen_option=chosen_option_text
    )

    try:
        response = await assistant_service.get_pathways_to_solve_problem_response(
            prompt=prompt,
            context_messages=await message_history_service.get_history(user_telegram_id, context_scope)
        )
        logger.info(f"Generated steps for user {user_telegram_id}: {response.message}")

        await message_history_service.add_message_to_history(
            user_telegram_id, context_scope, ContextMessage(role="assistant", message=response.message)
        )

        response_text = f"{response.message}\n\nЧто думаешь об этих шагах? Какой из них кажется наиболее реальным для начала? (Чтобы закончить, отправь /stop)"
        await send_long_message(query.message, convert_markdown_to_html(response_text), bot)
        await state.set_state(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
    except Exception as e:
        logger.error(f"Error generating steps for user {user_telegram_id}: {e}")
        await query.message.answer(
            "Произошла ошибка при генерации шагов. Попробуйте выбрать другой вариант или начать заново.")
        await state.set_state(SupportStates.METHOD_SELECT)
    finally:
        await query.answer()


@router.message(Command("stop"), SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
async def handle_stop_problem_solving(
        message: Message,
        state: FSMContext,
        **data
):
    user_telegram_id = str(message.from_user.id)
    context_scope = "problem_solving"
    logger.info(f"User {user_telegram_id} stopped problem solving session.")

    container: AsyncContainer = data["dishka_container"]
    history: MessageHistoryService = await container.get(MessageHistoryService)
    await state.clear()
    await history.clear_history(user_telegram_id, context_scope)
    await message.answer("Хорошо, мы закончили. Возвращаю в главное меню.", reply_markup=get_main_keyboard())


@router.message(SupportStates.PROBLEM_S4_STEPS_DISPLAYED)
@inject
async def handle_ps_s4_discussion(
        message: Message,
        state: FSMContext,
        bot: Bot,
        create_user_log: FromDishka[CreateUserLog],
        get_user_schema_interactor: FromDishka[GetUserSchemaById],
        assistant_service: FromDishka[AssistantService],
        message_history_service: FromDishka[MessageHistoryService],
        subscription_service: FromDishka[SubscriptionService],
):
    user_telegram_id = str(message.from_user.id)
    user: UserSchema = await get_user_schema_interactor(telegram_id=user_telegram_id)
    state_data = await state.get_data()
    dialogue_id = state_data["dialogue_id"]
    context_scope = "problem_solving"

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
    message_history = await message_history_service.get_history(user_telegram_id, context_scope)

    try:
        await message.answer(
            "Хорошо, думаю над ответом...\n\n💢Когда захочешь закончить со мной общаться, отправь команду /stop."
        )
        response = await assistant_service.get_speaking_response(
            message=message.text,
            context_messages=message_history
        )
        response_text = response.message

        await message_history_service.add_message_to_history(
            user_telegram_id, context_scope, ContextMessage(role="assistant", message=response_text)
        )

        await send_long_message(message, convert_markdown_to_html(response_text), bot)
        await subscription_service.increment_message_count(user_telegram_id)
    except Exception as e:
        logger.error(f"Error during discussion in problem_solving for user {user_telegram_id}: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте еще раз или завершите сессию командой /stop.")
