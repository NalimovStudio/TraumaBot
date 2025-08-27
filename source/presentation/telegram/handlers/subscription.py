from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    Message,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from dishka import AsyncContainer

from source.core.schemas.user_schema import UserSchema
from source.core.enum import SubscriptionType


from source.core.lexicon.bot import (
    SUBSCRIPTION_MENU_TEXT,
    STANDARD_SUB_DETAIL_TEXT,
    PRO_SUB_DETAIL_TEXT,
)
from source.presentation.telegram.callbacks.method_callbacks import SubscriptionCallback
from source.presentation.telegram.keyboards.keyboards import (
    get_subscriptions_menu_keyboard,
    get_standard_subscription_options_keyboard,
    get_pro_subscription_options_keyboard,
)
from source.application.payment.payment_service import PaymentService
from source.presentation.telegram.states.user_states import SupportStates


router = Router(name=__name__)


@router.callback_query(SubscriptionCallback.filter(F.menu == "main"))
async def handle_back_to_main_menu(query: CallbackQuery):
    await query.message.edit_text(
        text=SUBSCRIPTION_MENU_TEXT,
        reply_markup=get_subscriptions_menu_keyboard(),
    )
    await query.answer()


@router.callback_query(SubscriptionCallback.filter(F.menu == "standard"))
async def handle_standard_sub_menu(query: CallbackQuery):
    await query.message.edit_text(
        text=STANDARD_SUB_DETAIL_TEXT,
        reply_markup=get_standard_subscription_options_keyboard(),
    )
    await query.answer()


@router.callback_query(SubscriptionCallback.filter(F.menu == "pro"))
async def handle_pro_sub_menu(query: CallbackQuery):
    await query.message.edit_text(
        text=PRO_SUB_DETAIL_TEXT,
        reply_markup=get_pro_subscription_options_keyboard(),
    )
    await query.answer()

@router.callback_query(SubscriptionCallback.filter(F.menu == "buy"))
async def handle_buy_subscription(query: CallbackQuery, callback_data: SubscriptionCallback, user: UserSchema, state: FSMContext, **data):
    # No changes needed here as PaymentService is not used directly
    sub_type = "Стандарт" if callback_data.sub_type == "standard" else "Pro"
    months = callback_data.months
    price = callback_data.price
    telegram_id = user.telegram_id
    username = user.username

    await state.update_data(
        sub_type=sub_type,
        months=months,
        price=price,
        telegram_id=telegram_id,
        username=username
    )

    await state.set_state(SupportStates.WAITING)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Поделиться номером телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await query.message.answer(
        "Для формирования чека по 54-ФЗ укажите вашу почту (введите текстом) или поделитесь номером телефона:",
        reply_markup=keyboard
    )
    await query.answer()

@router.message(StateFilter(SupportStates.WAITING))
async def process_contact(message: Message, state: FSMContext, **data):
    # Manually get the container and the service
    container: AsyncContainer = data["dishka_container"]
    payment_service: PaymentService = await container.get(PaymentService)
    
    state_data = await state.get_data()
    customer_contact = None

    if message.contact:
        customer_contact = {'phone': message.contact.phone_number}
    elif message.text and '@' in message.text and '.' in message.text:
        customer_contact = {'email': message.text.strip()}
    else:
        await message.answer("Некорректный email. Попробуйте снова ввести email или поделитесь номером.")
        return

    payment = await payment_service.create_payment(
        amount=state_data['price'],
        description=f"Подписка для пользователя {state_data['username']} {state_data['sub_type']} на {state_data['months']} месяцев",
        months_sub=state_data['months'],
        telegram_id=state_data['telegram_id'],
        username=state_data['username'],
        customer_contact=customer_contact,
        subscription=SubscriptionType.PRO if state_data['sub_type'] == "pro" else SubscriptionType.DEFAULT
    )

    payment_url = payment.link

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=payment_url)]
    ])

    await message.answer(
        "Нажми на кнопку ниже, чтобы перейти к оплате:",
        reply_markup=keyboard
    )
    await message.answer("Спасибо!", reply_markup=ReplyKeyboardRemove())
    await state.clear()