import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from source.core.lexicon import message_templates
from source.materials.get_file import get_file_by_name
from source.presentation.telegram.keyboards.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    try:
        video = get_file_by_name("trauma_preview.mp4")
        await message.answer_animation(
            animation=video,
            caption=message_templates.WELCOME_MESSAGE,
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Гифка отправлена: {video.filename}")

    except Exception as e:
        logger.error(f"Ошибка при отправке гифки: {e}")

    logger.info(f"User {message.from_user.id} started the bot.")
