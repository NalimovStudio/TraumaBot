from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    Message,
    ReplyKeyboardRemove  # Добавлен импорт для удаления клавиатуры
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from dishka.integrations.aiogram import FromDishka
from source.core.schemas.user_schema import UserSchema
from sqlalchemy import func


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
async def handle_buy_subscription(query: CallbackQuery, callback_data: SubscriptionCallback, user: UserSchema, payment_service: FromDishka[PaymentService], state: FSMContext):
    sub_type = "Стандарт" if callback_data.sub_type == "standard" else "Pro"
    months = callback_data.months
    date = '' 
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

@router.message(StateFilter(SupportStates.WAITING))
async def process_contact(message: Message, state: FSMContext, payment_service: FromDishka[PaymentService]):
    data = await state.get_data()
    customer_contact = None

    if message.contact:
        customer_contact = {'phone': message.contact.phone_number}
    elif message.text:
        if '@' in message.text and '.' in message.text:
            customer_contact = {'email': message.text.strip()}
        else:
            await message.answer("Некорректный email. Попробуйте снова ввести email или поделитесь номером.")
            return
    else:
        await message.answer("Пожалуйста, укажите email текстом или поделитесь номером телефона.")
        return


    payment = await payment_service.create_payment(
        amount=data['price'],
        description=f"Подписка для пользователя {data['username']} {data['sub_type']} на {data['months']} месяцев",
        months_sub=data['months'],
        telegram_id=data['telegram_id'],
        username=data['username'],
        customer_contact=customer_contact 
    )

    payment_url = payment.link

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", url=payment_url)]
    ])

    await message.answer(
        "Нажми на кнопку ниже, чтобы перейти к оплате:",
        reply_markup=keyboard
    )

    await message.answer("Спасибо!", reply_markup=ReplyKeyboardRemove())  # Изменено на ReplyKeyboardRemove для удаления клавиатуры

    await state.clear()