from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from source.core.lexicon.bot import HELP_TEXT
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_support_methods_keyboard,
    get_help_keyboard,
)
from source.presentation.telegram.states.user_states import SupportStates

router = Router(name=__name__)


@router.callback_query(HelpCallback.filter(F.menu == "start_dialog"))
async def handle_help_start_dialog(query: CallbackQuery, state: FSMContext):
    # TODO (Влад): если запись за этот день уже есть, пропускать handler и сразу вызывать handle_help_support_methods

    await state.set_state(SupportStates.CHECK_IN)
    text = (
        "Оцени, как ты себя чувствуешь, по шкале от 1 до 10."
    )
    await query.message.answer(text=text, reply_markup=ReplyKeyboardRemove())
    await query.answer()


@router.callback_query(HelpCallback.filter(F.menu == "support_methods"))
async def handle_help_support_methods(query: CallbackQuery, state: FSMContext):
    await state.set_state(SupportStates.METHOD_SELECT)
    text = "Выберите один из методов поддержки:"
    await query.message.edit_text(
        text=text, reply_markup=get_support_methods_keyboard()
    )
    await query.answer()


@router.callback_query(HelpCallback.filter(F.menu == "back"))
async def handle_back_to_help(query: CallbackQuery):
    await query.message.edit_text(text=HELP_TEXT, reply_markup=get_help_keyboard())
    await query.answer()
