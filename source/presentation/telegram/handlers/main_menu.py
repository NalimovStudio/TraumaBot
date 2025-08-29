import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from source.core.enum import SubscriptionType
from source.core.lexicon.bot import PROFILE_TEXT, HELP_TEXT, SUBSCRIPTION_MENU_TEXT
from source.core.schemas.user_schema import UserSchema
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.keyboards.keyboards import (
    ButtonText,
    get_subscriptions_menu_keyboard,
    get_help_keyboard,
    get_support_methods_keyboard,
    get_main_keyboard
)
from source.presentation.telegram.states.user_states import SupportStates

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(HelpCallback.filter(F.menu == "back"))
async def handle_back_to_help(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} clicked 'Back to help', returning to main menu.")
    await state.clear()
    await query.answer()
    await query.message.answer(
        text="Вы в главном меню.",
        reply_markup=get_main_keyboard()
    )
    await query.message.delete()


@router.callback_query(HelpCallback.filter(F.menu == "start_dialog"))
async def handle_start_dialog_from_help(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} started a new dialog from help menu.")
    await query.answer()
    await state.set_state(SupportStates.CHECK_IN)

    await query.message.delete()

    await query.message.answer(
        text="Как ты себя чувствуешь сейчас?"
             "Оцени по шкале от 1 до 10",
        reply_markup=ReplyKeyboardRemove()
    )


@router.callback_query(HelpCallback.filter(F.menu == "methods"))
async def handle_support_methods(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} requested support methods.")
    await state.set_state(SupportStates.METHOD_SELECT)
    await query.answer()

    await query.message.edit_text(
        text="Какой метод поддержки ты бы хотел использовать?",
        reply_markup=get_support_methods_keyboard(),
    )


@router.message(F.text == "Вернуться в меню")
async def handle_back_to_main_menu(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is returning to the main menu.")
    await state.clear()
    await message.answer(
        text="Вы в главном меню.",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == ButtonText.START_DIALOG)
async def handle_start_dialog(message: Message, state: FSMContext):
    await state.set_state(SupportStates.CHECK_IN)
    text = (
        "Как ты себя чувствуешь сейчас? "
        "Оцени по шкале от 1 до 10"
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
async def handle_profile(message: Message, user: UserSchema | None = None):
    logger.info(f"User {message.from_user.id} requested profile.")

    if user is None:
        await message.answer(
            "Не удалось загрузить ваш профиль. Пожалуйста, попробуйте еще раз позже."
        )
        return

    subscription_info = "Бесплатная"
    if user.subscription != SubscriptionType.FREE and user.subscription_date_end:
        if user.subscription == SubscriptionType.DEFAULT:
            sub_type_str = "Стандарт"
        elif user.subscription == SubscriptionType.PRO:
            sub_type_str = "Pro"
        else:
            sub_type_str = "Неизвестный тип"

        date_end_str = user.subscription_date_end.strftime("%d.%m.%Y")
        subscription_info = f"{sub_type_str} (до {date_end_str})"

    text = PROFILE_TEXT.format(
        user_id=user.telegram_id,
        username=user.username or "не указан",
        subscription_type=subscription_info,
    )
    await message.answer(text=text)


@router.message(F.text, StateFilter(None))
async def handle_unknown_message_no_state(message: Message):
    """Вылавливает сообщение которые не в стейтах и в меню кидает"""
    await message.answer(
        text="Я не совсем понимаю, что ты имеешь в виду. Давай вернемся в главное меню, чтобы ты мог выбрать, что делать дальше.",
        reply_markup=get_main_keyboard()
    )
