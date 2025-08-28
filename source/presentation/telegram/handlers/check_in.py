import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from source.presentation.telegram.keyboards.keyboards import get_support_methods_keyboard
from source.presentation.telegram.states.user_states import SupportStates

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(SupportStates.CHECK_IN)
async def handle_check_in(message: Message, state: FSMContext):
    """
    Обрабатывает ответ пользователя на вопрос "Как ты?".
    Классифицирует намерение, проверяет риски и предлагает дальнейшие шаги.
    """
    logger.info(f"User {message.from_user.id} in CHECK_IN. Msg: '{message.text[:30]}...'")

    # 1. Классифицируем намерение с помощью заглушки # TODO Решить заглушку
    #classification = await classify_intent(message.text) 
    classification = {
        "intent": "other",
        "risk": "none",
        "emotion_tags": ["тревога", "грусть"],
        "suicide_signals": {"ideation": False, "plan": False, "means": False, "imminent": False}
    }

    # 2. Проверяем на наличие риска
    if classification['risk'] != 'none':
        logger.warning(f"Risk '{classification['risk']}' detected for user {message.from_user.id}")
        await state.set_state(SupportStates.RISK_PROTOCOL)
        await state.update_data(classification=classification)

        # Отправляем первое сообщение из протокола безопасности (согласно ТЗ)
        text = "Мне очень важно понять, в безопасности ли ты. Были ли у тебя мысли причинить себе вред?"
        await message.answer(text=text)
        return

    # 3. Если риска нет, предлагаем выбрать метод
    logger.info(f"No risk for user {message.from_user.id}. Moving to METHOD_SELECT.")
    await state.set_state(SupportStates.METHOD_SELECT)

    text = "Спасибо, что поделился. Хочешь, подберём метод поддержки или просто побудем с этим?"
    await message.answer(text=text, reply_markup=get_support_methods_keyboard())
