import logging

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.types import Message

from source.core.lexicon.ButtonText import ButtonText
from source.core.lexicon import message_templates
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_subscriptions_menu_keyboard,
    get_help_keyboard,
    get_support_methods_keyboard,
    get_main_keyboard
)
from source.presentation.telegram.states.user_states import SupportStates

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == "Вернуться в меню")
async def handle_back_to_main_menu(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is returning to the main menu.")
    await state.clear()
    await message.answer(
        text=message_templates.YOU_IN_MAIN_MENU,
        reply_markup=get_main_keyboard()
    )


@router.callback_query(HelpCallback.filter(F.menu == "back"))
async def handle_back_to_help(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} clicked 'Back to help', returning to main menu.")
    await state.clear()
    await query.answer()
    await query.message.answer(
        text=message_templates.YOU_IN_MAIN_MENU,
        reply_markup=get_main_keyboard()
    )
    await query.message.delete()


@router.callback_query(HelpCallback.filter(F.menu == "methods"))
async def handle_support_methods(query: CallbackQuery, state: FSMContext):
    logger.info(f"User {query.from_user.id} requested support methods.")
    await state.set_state(SupportStates.METHOD_SELECT)
    await query.answer()

    await query.message.edit_text(
        text="Какой метод поддержки ты бы хотел использовать?",
        reply_markup=get_support_methods_keyboard(),
    )


@router.message(F.text == ButtonText.HELP)
async def handle_help(message: Message):
    await message.answer(text=message_templates.HELP_TEXT, reply_markup=get_help_keyboard())


@router.message(F.text == ButtonText.SUBSCRIPTION)
async def handle_subscription(message: Message):
    await message.answer(
        text=message_templates.SUBSCRIPTION_MENU_TEXT,
        reply_markup=get_subscriptions_menu_keyboard()
    )


@router.message(F.text, StateFilter(None))
async def handle_unknown_message_no_state(message: Message):
    """Вылавливает сообщение которые не в стейтах и в меню кидает"""
    await message.answer(
        text="Я не совсем понимаю, что ты имеешь в виду. Давай вернемся в главное меню, чтобы ты мог выбрать, что делать дальше.",
        reply_markup=get_main_keyboard()
    )
