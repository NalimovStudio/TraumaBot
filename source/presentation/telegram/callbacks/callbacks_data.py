from aiogram.filters.callback_data import CallbackData


# [ USER PROFILE ]
class UserProfileCallback(CallbackData, prefix="user_profile"):
    pass


class GetUserCharacteristicCallback(CallbackData, prefix="user_characts"):
    page: int = 0


class GenerateUserCharacteristicCallback(CallbackData, prefix="generate_characts"):
    pass

# [ mailing ]
class MailingConfirmationCallback(CallbackData, prefix="mailing_conf"):
    pass
