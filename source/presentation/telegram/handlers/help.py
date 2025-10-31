from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from source.core.lexicon.message_templates import HELP_TEXT
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_help_keyboard, get_support_methods_keyboard,
)
from source.presentation.telegram.states.user_states import SupportStates

router = Router(name=__name__)


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
