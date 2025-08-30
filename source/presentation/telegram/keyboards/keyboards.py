from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from source.presentation.telegram.callbacks.method_callbacks import (
    MethodCallback,
    CalmingCallback,
    VentingCallback,
    SubscriptionCallback,
    ProblemSolvingCallback,
    HelpCallback,
)


class ButtonText:
    # Reply Keyboard
    START_DIALOG = "Начать диалог💬"
    HELP = "Помощь 💡"
    SUBSCRIPTION = "Подписка⭐"
    PROFILE = "Профиль 👤"

    # Help Menu
    HELP_START_DIALOG = "Начать диалог 💬"
    HELP_SUPPORT_METHODS = "Методы поддержки 💡"
    BACK_TO_HELP = "Назад к помощи ↩️"

    # Subscription
    BUY_STANDARD = "Купить Стандарт 💎"
    BUY_PRO = "Купить Pro ⭐"

    SUB_STANDART_1_MONTH = "1 месяц/379₽"
    SUB_STANDART_1_MONTH_PRICE = "379.00"
    SUB_STANDART_3_MONTHS = "3 месяца/1099₽"
    SUB_STANDART_3_MONTHS_PRICE = "1099.00"
    SUB_STANDART_6_MONTHS = "6 месяцев/1999₽"
    SUB_STANDART_6_MONTHS_PRICE = "1999.00"
    SUB_STANDART_12_MONTHS = "1 год/4399₽"
    SUB_STANDART_12_MONTHS_PRICE = "4399.00"

    SUB_PRO_1_MONTH = "1 месяц/749₽"
    SUB_PRO_1_MONTH_PRICE = "749.00"
    SUB_PRO_3_MONTHS = "3 месяца/1999₽"
    SUB_PRO_3_MONTHS_PRICE = "1999.00"
    SUB_PRO_6_MONTHS = "6 месяцев/4399₽"
    SUB_PRO_6_MONTHS_PRICE = "4399.00"
    SUB_PRO_12_MONTHS = "1 год/8899₽"
    SUB_PRO_12_MONTHS_PRICE = "8899.00"



    BACK = "Назад ↩️"

    # Inline Keyboard - Methods
    CALM_DOWN = "Успокоиться"
    # TODO: Раскоментировать данный блок что бы вернуть Дневник эмоций
    # CBT_DIARY = "КПТ (Дневник эмоций)"
    PROBLEM_SOLVING = "Потенциальное решение проблемы"
    VENT_OUT = "Высказаться"

    # Inline Keyboard - Calming flow
    ANOTHER_CYCLE = "ещё 1 цикл"
    FEEL_BETTER = "стало чуть легче"
    TO_TALK = "перейти к разговору"

    # Inline Keyboard - Venting summary
    SAVE = "Сохранить"
    DELETE = "Удалить"
    TO_CBT = "Превратить в запись дневника"

    # Inline Keyboard - Subscription
    RENEW_DISCOUNT = "Продлить со скидкой -40%"


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ButtonText.START_DIALOG)],
            [KeyboardButton(text=ButtonText.HELP)],
            [KeyboardButton(text=ButtonText.SUBSCRIPTION)],
            [KeyboardButton(text=ButtonText.PROFILE)],
        ],
        resize_keyboard=True,
    )


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для меню помощи."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.HELP_START_DIALOG,
                    callback_data=HelpCallback(menu="start_dialog").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.HELP_SUPPORT_METHODS,
                    callback_data=HelpCallback(menu="methods").pack(),
                )
            ],
        ]
    )


def get_support_methods_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            #[
            #    InlineKeyboardButton(
            #        text=ButtonText.CALM_DOWN,
            #        callback_data=MethodCallback(name="calm").pack(),
            #    )
            # ],
            # TODO: Раскоментировать данный блок что бы вернуть Дневник эмоций
            # [
            #     InlineKeyboardButton(
            #         text=ButtonText.CBT_DIARY,
            #         callback_data=MethodCallback(name="cbt").pack(),
            #     )
            # ],
            [
                InlineKeyboardButton(
                    text=ButtonText.PROBLEM_SOLVING,
                    callback_data=MethodCallback(name="problem").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.VENT_OUT,
                    callback_data=MethodCallback(name="vent").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.BACK_TO_HELP,
                    callback_data=HelpCallback(menu="back").pack(),
                )
            ],
        ]
    )


def get_calming_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.ANOTHER_CYCLE,
                    callback_data=CalmingCallback(action="another_cycle").pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.FEEL_BETTER,
                    callback_data=CalmingCallback(action="feel_better").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.TO_TALK,
                    callback_data=CalmingCallback(action="to_talk").pack(),
                )
            ],
        ]
    )


def get_venting_summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.SAVE,
                    callback_data=VentingCallback(action="save").pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.DELETE,
                    callback_data=VentingCallback(action="delete").pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.TO_CBT,
                    callback_data=VentingCallback(action="to_cbt").pack(),
                )
            ],
        ]
    )


def get_subscription_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.RENEW_DISCOUNT,
                    callback_data=SubscriptionCallback(menu="renew_discount").pack(),
                )
            ],
        ]
    )


def get_subscriptions_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.BUY_STANDARD,
                    callback_data=SubscriptionCallback(menu="standard").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.BUY_PRO,
                    callback_data=SubscriptionCallback(menu="pro").pack(),
                )
            ],
        ]
    )


def get_standard_subscription_options_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.SUB_STANDART_1_MONTH,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="standard", months=1, price=ButtonText.SUB_STANDART_1_MONTH_PRICE
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.SUB_STANDART_3_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="standard", months=3, price=ButtonText.SUB_STANDART_3_MONTHS_PRICE
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.SUB_STANDART_6_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="standard", months=6, price=ButtonText.SUB_STANDART_6_MONTHS_PRICE
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.SUB_STANDART_12_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="standard", months=12, price=ButtonText.SUB_STANDART_12_MONTHS_PRICE
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.BACK,
                    callback_data=SubscriptionCallback(menu="main").pack(),
                )
            ],
        ]
    )


def get_pro_subscription_options_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ButtonText.SUB_PRO_1_MONTH,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="pro", months=1, price=ButtonText.SUB_PRO_1_MONTH_PRICE
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.SUB_PRO_3_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="pro", months=3, price=ButtonText.SUB_PRO_3_MONTHS_PRICE
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.SUB_PRO_6_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="pro", months=6, price=ButtonText.SUB_PRO_6_MONTHS_PRICE
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text=ButtonText.SUB_PRO_12_MONTHS,
                    callback_data=SubscriptionCallback(
                        menu="buy", sub_type="pro", months=12, price=ButtonText.SUB_PRO_12_MONTHS_PRICE
                    ).pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.BACK,
                    callback_data=SubscriptionCallback(menu="main").pack(),
                )
            ],
        ]
    )


def get_problem_solutions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Вариант 1",
                    callback_data=ProblemSolvingCallback(
                        action="choose_option", option_id=0
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Вариант 2",
                    callback_data=ProblemSolvingCallback(
                        action="choose_option", option_id=1
                    ).pack(),
                ),
                InlineKeyboardButton(
                    text="Вариант 3",
                    callback_data=ProblemSolvingCallback(
                        action="choose_option", option_id=2
                    ).pack(),
                ),
            ]
        ]
    )


def get_back_to_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Вернуться в меню")]],
        resize_keyboard=True,
    )
