import logging

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from source.core.lexicon.ButtonText import ButtonText
from source.core.schemas.user_schema import UserCharacteristicSchema
from source.presentation.telegram.callbacks.callbacks_data import GetUserCharacteristicCallback, \
    GenerateUserCharacteristicCallback, UserProfileCallback
from source.presentation.telegram.callbacks.method_callbacks import (
    MethodCallback,
    CalmingCallback,
    VentingCallback,
    SubscriptionCallback,
    ProblemSolvingCallback,
    HelpCallback
)

logger = logging.getLogger(__name__)


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
            # [
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
                    text=ButtonText.RELATIONSHIPS,
                    callback_data=MethodCallback(name="relationships").pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.PROBLEM_SOLVING,
                    callback_data=MethodCallback(name="problem").pack(),
                )
            ],
            [
                InlineKeyboardButton(
                    text=ButtonText.SPEAKING,
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


def get_user_characteristics_menu_keyboard(
        pages_count: int = 0,
        page: int = 0,
) -> InlineKeyboardMarkup:
    """Меню характеристики юзера"""
    button: InlineKeyboardButton
    if pages_count:
        button = InlineKeyboardButton(
            text=ButtonText.YOUR_CHARACTERISTIC,
            callback_data=GetUserCharacteristicCallback(
                page=page
            ).pack()
        )
    else:
        button = InlineKeyboardButton(
            text=ButtonText.GENERATE_CHARACTERISTIC,
            callback_data=GenerateUserCharacteristicCallback().pack()
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                button
            ]
        ]
    )


def get_user_characteristics_listing_keyboard(
        user_characteristics: list[UserCharacteristicSchema] | None,
        may_generate: bool = False,
        page: int = 0,
) -> InlineKeyboardMarkup:
    """Листинг"""
    logger.info(f"Юзер находится в меню характеристик: page={page}")

    user_characteristics_count: int = 0
    if user_characteristics:
        user_characteristics_count = len(user_characteristics)

    buttons: list[InlineKeyboardButton | list[InlineKeyboardButton]] = []

    pagination_buttons = []
    if user_characteristics_count:
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=ButtonText.LEFT_ARROW,
                    callback_data=GetUserCharacteristicCallback(
                        page=page - 1
                    ).pack()
                )
            )
        if user_characteristics_count - 1 > page:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text=ButtonText.RIGHT_ARROW,
                    callback_data=GetUserCharacteristicCallback(
                        page=page + 1
                    ).pack()
                )
            )

    if pagination_buttons:
        buttons.append(pagination_buttons)

    if may_generate:
        buttons.append([
            InlineKeyboardButton(
                text=ButtonText.GENERATE_CHARACTERISTIC,
                callback_data=GenerateUserCharacteristicCallback().pack()
            )]
        )

    buttons.append([
        InlineKeyboardButton(
            text=ButtonText.BACK_TO_PROFILE,
            callback_data=UserProfileCallback().pack()
        )
    ])

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
