import logging

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from dishka import AsyncContainer
from dishka.integrations.aiogram import inject, FromDishka

from source.application.ai_assistant.ai_assistant_service import AssistantService
from source.application.user.user_characteristic import GetUserCharacteristics, PutGeneratedUserCharacteristic, \
    MayGenerateCharacteristic
from source.application.user.user_logs import GetLastUserLogs, GetAllUserLogs
from source.application.user.user_mood import GetUserMoods
from source.core.enum import SubscriptionType
from source.core.lexicon import message_templates
from source.core.lexicon.ButtonText import ButtonText
from source.core.lexicon.message_formatters import format_profile_characteristic
from source.core.lexicon.message_templates import PROFILE_TEXT
from source.core.lexicon.rules import MIN_MOOD_RECORDS_COUNT, MIN_LOGGING_RECORDS
from source.core.schemas.assistant_schemas import UserCharacteristicAssistantResponse
from source.core.schemas.user_schema import UserSchema, UserCharacteristicSchema, UserMoodSchema, UserLogSchema
from source.presentation.telegram.callbacks.callbacks_data import GenerateUserCharacteristicCallback, \
    UserProfileCallback, GetUserCharacteristicCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_user_characteristics_menu_keyboard, get_user_characteristics_listing_keyboard
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def _show_profile(
        message: Message,
        container: AsyncContainer,
        user: UserSchema | None = None,
        is_callback: bool = False,
):
    logger.info(f"User {message.from_user.id} requested profile.")

    if user is None:
        await message.answer(
            "Не удалось загрузить ваш профиль. Пожалуйста, попробуйте еще раз позже."
        )
        return

    subscription_info = "Без подписки"
    if user.subscription != SubscriptionType.FREE and user.subscription_date_end:
        if user.subscription == SubscriptionType.DEFAULT:
            sub_type_str = "Стандарт 👑"
        elif user.subscription == SubscriptionType.PRO:
            sub_type_str = "Pro 💎"
        else:
            sub_type_str = "Неизвестный тип"

        date_end_str = user.subscription_date_end.strftime("%d.%m.%Y")
        subscription_info = f"{sub_type_str} (до {date_end_str})"

    text = PROFILE_TEXT.format(
        user_id=user.telegram_id,
        username=user.username or "не указан",
        subscription_type=subscription_info,
    )

    get_user_characteristics_interactor: GetUserCharacteristics = await container.get(GetUserCharacteristics)
    user_characteristics: list[UserCharacteristicSchema] | None = await get_user_characteristics_interactor(
        user.telegram_id)
    if not user_characteristics:
        user_characteristics = []

    if is_callback:
        await message.edit_text(
            text=text,
            reply_markup=get_user_characteristics_menu_keyboard(
                pages_count=len(user_characteristics)
            )
        )
    else:
        await message.answer(
            text=text,
            reply_markup=get_user_characteristics_menu_keyboard(
                pages_count=len(user_characteristics)
            )
        )


@router.callback_query(UserProfileCallback.filter())
async def handle_profile(
        callback_query: CallbackQuery,
        user: UserSchema | None = None,
        **data
):
    container: AsyncContainer = data["dishka_container"]
    await _show_profile(
        callback_query.message,
        container=container,
        is_callback=True,
        user=user
    )


@router.message(F.text == ButtonText.PROFILE)
async def handle_profile(
        message: Message,
        user: UserSchema | None = None,
        **data
):
    container: AsyncContainer = data["dishka_container"]
    await _show_profile(message, container=container, user=user)


async def __send_warning_message(
        callback_query: CallbackQuery,
        text: str = message_templates.NEED_MORE_IN_TRAUMA
):
    await callback_query.message.edit_text(
        text=text,
        reply_markup=get_user_characteristics_listing_keyboard(
            user_characteristics=None,
            may_generate=False
        )
    )


@router.callback_query(GetUserCharacteristicCallback.filter())
@inject
async def user_characteristics_listing(
        callback_query: CallbackQuery,
        callback_data: GetUserCharacteristicCallback,
        get_user_characteristics_interactor: FromDishka[GetUserCharacteristics],
        may_generate_interactor: FromDishka[MayGenerateCharacteristic]
):
    """листинг характеристики"""
    await callback_query.answer()

    page: int = callback_data.page
    user_telegram_id: str = str(callback_query.from_user.id)
    user_characteristics: list[UserCharacteristicSchema] = await get_user_characteristics_interactor(
        telegram_id=user_telegram_id
    )

    may_generate: bool = await may_generate_interactor(telegram_id=user_telegram_id)

    await callback_query.message.edit_text(
        text=format_profile_characteristic(
            user_characteristics[page]
        ),
        reply_markup=get_user_characteristics_listing_keyboard(
            may_generate=may_generate,
            user_characteristics=user_characteristics,
            page=page
        )
    )


@router.callback_query(GenerateUserCharacteristicCallback.filter())
@inject
async def generate_user_characteristic(
        callback_query: CallbackQuery,
        get_user_characteristics_interactor: FromDishka[GetUserCharacteristics],
        get_moods_interactor: FromDishka[GetUserMoods],
        get_last_logs_interactor: FromDishka[GetLastUserLogs],
        get_all_logs_interactor: FromDishka[GetAllUserLogs],
        assistant: FromDishka[AssistantService],
        put_user_characteristic_interactor: FromDishka[PutGeneratedUserCharacteristic],
        user: UserSchema,
):
    """Генерация характеристики юзера в профиле"""
    await callback_query.answer()  # ответ на колбек, чтобы он не "висел"

    user_telegram_id: str = str(callback_query.from_user.id)

    # Получаем существующие характеристики
    user_characteristics: list[UserCharacteristicSchema] = await get_user_characteristics_interactor(
        telegram_id=user_telegram_id
    )

    # [ moods ]
    if not user_characteristics:
        limit_moods_records = 0  # Все записи настроения
    else:
        limit_moods_records = MIN_MOOD_RECORDS_COUNT

    user_moods: list[UserMoodSchema] = await get_moods_interactor(
        telegram_id=user_telegram_id,
        limit=limit_moods_records
    )

    if len(user_moods) < MIN_MOOD_RECORDS_COUNT:
        logger.info(
            f"User Profile: У юзера {callback_query.from_user.username} недостаточно user_moods ({len(user_moods)} < {MIN_MOOD_RECORDS_COUNT}).")

        text = message_templates.NOT_ENOUGH_MOODS_RECORDS

        await __send_warning_message(callback_query, text=text)
        return

    # [ logs ]
    if not user_characteristics:
        # за все дни
        user_logs: list[UserLogSchema] = await get_all_logs_interactor(user_telegram_id)
    else:
        # за последние MIN_DAYS_AFTER_LAST_CHARACTERISTIC_GENERATION дней
        user_logs: list[UserLogSchema] = await get_last_logs_interactor(user_telegram_id, )

    if not user_logs or len(user_logs) < MIN_LOGGING_RECORDS:
        logger.info(
            f"User Profile:: У юзера {callback_query.from_user.username} недостаточно логов ({len(user_logs) if user_logs else 0} < {MIN_LOGGING_RECORDS}).")

        text = message_templates.NOT_ENOUGH_LOGS_RECORDS

        await __send_warning_message(callback_query, text=text)
        return

    # Генерация характеристики
    await callback_query.message.edit_text(
        text="Генерация характеристики.."
    )

    try:
        generated_characteristic: UserCharacteristicAssistantResponse = await assistant.get_user_characteristic(
            user_logs_history=user_logs,
            user_mood_history=user_moods
        )

        # СОХРАНЯЕМ характеристику в БД
        characteristic: UserCharacteristicSchema = await put_user_characteristic_interactor(
            (user.id, generated_characteristic)
        )  # TODO redis, redis invalidate

        # Обновляем список характеристик
        user_characteristics = await get_user_characteristics_interactor(telegram_id=user_telegram_id)

        await callback_query.message.edit_text(
            text=format_profile_characteristic(characteristic),
            reply_markup=get_user_characteristics_listing_keyboard(
                user_characteristics=user_characteristics,
                may_generate=False
            )
        )

    except Exception as e:
        logger.error(f"Ошибка при генерации характеристики: {e}")
        await callback_query.message.edit_text(
            text="Произошла ошибка при генерации характеристики. Попробуйте позже.",
            reply_markup=get_user_characteristics_listing_keyboard(
                user_characteristics=user_characteristics,
                may_generate=True
            )
        )
