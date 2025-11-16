import logging

from aiogram import F, Router
from aiogram import flags
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.types import ReplyKeyboardRemove
from dishka.integrations.aiogram import inject, FromDishka

from source.application.user.user_mood import SetMood
from source.core.lexicon.ButtonText import ButtonText
from source.presentation.telegram.callbacks.method_callbacks import HelpCallback
from source.presentation.telegram.keyboards.keyboards import get_support_methods_keyboard
from source.presentation.telegram.states.user_states import SupportStates

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(HelpCallback.filter(F.menu == "start_dialog"))
@flags.user_mood(True)
async def handle_start_dialog_from_help(
        callback_query: CallbackQuery,
        state: FSMContext,
        is_mood_was_set_today: bool,
):
    logger.info(f"User {callback_query.from_user.id} started a new dialog from help menu.")
    await callback_query.answer()

    # [ запись настроения ]
    if not is_mood_was_set_today:
        await state.set_state(SupportStates.CHECK_IN)

        text = "Как ты сегодня себя чувствуешь?\n\nОцени своё настроение от 0 до 10:"  # TODO in templates
        await callback_query.message.edit_text(
            text=text
        )
        await callback_query.message.edit_reply_markup(
            reply_markup=None
        )

    else:
        # [ юзер выбирает метод поддержки ]
        await _select_support_method(
            message=callback_query.message,
            state=state,
            is_callback=True,
            is_mood_was_set=False
        )


@router.message(F.text == ButtonText.START_DIALOG)
@flags.user_mood(True)
async def handle_start_dialog(
        message: Message,
        state: FSMContext,
        is_mood_was_set_today: bool,
):
    # [ запись настроения ]
    if not is_mood_was_set_today:
        await state.set_state(SupportStates.CHECK_IN)

        text = "Как ты сегодня себя чувствуешь?\n\nОцени своё настроение от 0 до 10:"

        await message.answer(
            text=text,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        # [ юзер выбирает метод поддержки ]
        await _select_support_method(
            message=message,
            state=state,
            is_mood_was_set=False
        )


@router.message(SupportStates.CHECK_IN)
@inject
async def handle_check_in(
        message: Message,
        state: FSMContext,
        set_mood: FromDishka[SetMood],
):
    """
    Обрабатывает ответ пользователя на вопрос "Как ты?".
    """
    logger.info(f"User {message.from_user.id} mood set. Msg: '{message.text[:30]}...'")

    user_telegram_id = str(message.from_user.id)

    # [ запись настроения ]
    try:
        # Проверяем, что введено число
        mood_value = int(message.text)

        # Проверяем диапазон
        if not 0 <= mood_value <= 10:
            text = "❌ Пожалуйста, введите число от 0 до 10 включительно"
            await message.answer(text=text)
            return

        mood: int = int(message.text)

        await set_mood((user_telegram_id, mood))

    except ValueError:
        # Если преобразование в int не удалось
        text = "❌ Пожалуйста, введите целое число от 0 до 10"
        await message.answer(text=text)
        return

    # [ юзер выбирает метод поддержки ]
    await _select_support_method(
        message=message,
        state=state,
        is_mood_was_set=False
    )


async def _select_support_method(
        state: FSMContext,
        message: Message,
        is_callback: bool = False,
        is_mood_was_set: bool = True,
):
    """выбор метода поддержки"""
    await state.set_state(SupportStates.METHOD_SELECT)

    text = "Выбери любой доступный тебе метод поддержки снизу:"
    if is_mood_was_set:
        text = "Спасибо, что поделился.\n\n" + text

    if is_callback:
        await message.edit_text(
            text=text,
            reply_markup=get_support_methods_keyboard()
        )
    else:
        await message.answer(text=text, reply_markup=get_support_methods_keyboard())
