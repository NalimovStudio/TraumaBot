import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from source.presentation.telegram.keyboards.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router(name=__name__)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "✨Привет, я готов выслушать тебя. Расскажи мне о чем ты волнуешься или молчишь другим людям. Я могу рассмотреть ситуацию так, чтобы тебе было легче и поддержать тебя в любых трудностях."
    )
    await message.answer(text=text, reply_markup=get_main_keyboard())
    logger.info(f"User {message.from_user.id} started the bot.")