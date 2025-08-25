from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from source.presentation.telegram.callbacks.method_callbacks import MethodCallback

from source.core.lexicon.bot import PROFILE_TEXT, HELP_TEXT, SUBSCRIPTION_MENU_TEXT
from source.presentation.telegram.keyboards.keyboards import (
    ButtonText,
    get_subscriptions_menu_keyboard,
    get_help_keyboard,
    get_support_methods_keyboard,
    get_back_to_menu_keyboard,
    get_calming_keyboard
)
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.states.user_states import SupportStates

import logging


router = Router(name=__name__)
logger = logging.getLogger(__name__)

@router.callback_query(MethodCallback.filter(F.name == "calm"))
async def handle_calm_down(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "Успокоиться".
    """
    logger.info(f"User {query.from_user.id} chose 'Calm Down' method.")
    await query.answer()
    await state.set_state(SupportStates.CALMING)

    await query.message.edit_text(
        text="Хорошо, давай сделаем несколько циклов дыхания. Пожалуйста, следуй инструкциям.\n\n"
             "Сделай глубокий вдох, задержи дыхание и медленно выдохни. Повтори 3 раза.",
        reply_markup=get_calming_keyboard()
    )


@router.callback_query(MethodCallback.filter(F.name == "cbt"))
async def handle_cbt_diary(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "КПТ (Дневник эмоций)".
    """
    logger.info(f"User {query.from_user.id} chose 'CBT Diary' method.")
    await query.answer()
    await state.set_state(SupportStates.CBT_S1_SITUATION)

    await query.message.edit_text(
        text="Хорошо, давай заполним дневник эмоций. Опиши ситуацию, в которой ты сейчас находишься.",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(MethodCallback.filter(F.name == "problem"))
async def handle_problem_solving(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "Потенциальное решение проблемы".
    """
    logger.info(f"User {query.from_user.id} chose 'Problem Solving' method.")
    await query.answer()
    await state.set_state(SupportStates.PROBLEM_S1_DEFINE)
    
    await query.message.edit_text(
        text="Отлично, давай попробуем разобраться с твоей проблемой. Начни с ее описания.",
        reply_markup=get_back_to_menu_keyboard()
    )


@router.callback_query(MethodCallback.filter(F.name == "vent"))
async def handle_vent_out(query: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку "Высказаться".
    """
    logger.info(f"User {query.from_user.id} chose 'Vent Out' method.")
    await query.answer()
    await state.set_state(SupportStates.VENTING)
    
    await query.message.edit_text(
        text="Я готов тебя выслушать. Говори, все, что на душе, я здесь для тебя. Можешь начинать.",
        reply_markup=get_back_to_menu_keyboard()
    )

@router.callback_query(HelpCallback.filter(F.menu == "back"))
async def handle_back_to_help(query: CallbackQuery, callback_data: HelpCallback):
    logger.info(f"User {query.from_user.id} returned to help menu.")
    
    await query.answer()
    await query.message.edit_text(
        text="Выберите один из вариантов помощи:",
        reply_markup=get_help_keyboard(),
    )

@router.callback_query(HelpCallback.filter(F.menu == "start_dialog"))
async def handle_start_dialog(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} started a new dialog.")

    await query.answer()

    await state.set_state(SupportStates.CHECK_IN)

    await query.message.edit_text(
        text="Как ты себя чувствуешь? Пожалуйста, опиши свое состояние.",
        reply_markup=get_back_to_menu_keyboard()
    )

@router.callback_query(HelpCallback.filter(F.menu == "methods"))
async def handle_support_methods(query: CallbackQuery):
    logger.info(f"User {query.from_user.id} requested support methods.")

    await query.answer()

    await query.message.edit_text(
        text="Какой метод поддержки ты бы хотел использовать?",
        reply_markup=get_support_methods_keyboard(),
    )

@router.message(F.text == ButtonText.START_DIALOG)
async def handle_start_dialog(message: Message, state: FSMContext):
    await state.set_state(SupportStates.CHECK_IN)
    text = (
        "Я рядом. Как ты себя чувствуешь сейчас? "
        "Если бы это было погодой — какой она была бы?"
    )
    await message.answer(text=text, reply_markup=ReplyKeyboardRemove())


@router.message(F.text == ButtonText.HELP)
async def handle_help(message: Message):
    await message.answer(text=HELP_TEXT, reply_markup=get_help_keyboard())


@router.message(F.text == ButtonText.SUBSCRIPTION)
async def handle_subscription(message: Message):
    await message.answer(
        text=SUBSCRIPTION_MENU_TEXT,
        reply_markup=get_subscriptions_menu_keyboard()
    )


@router.message(F.text == ButtonText.PROFILE)
async def handle_profile(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "не указан"
    subscription_type = "Бесплатная"

    text = PROFILE_TEXT.format(
        user_id=user_id,
        username=username,
        subscription_type=subscription_type,
    )
    await message.answer(text=text)
