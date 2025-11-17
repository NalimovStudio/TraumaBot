from aiogram.filters.callback_data import CallbackData


class MethodCallback(CallbackData, prefix="method"):
    name: str  # calm, cbt, problem, vent, relationships


class CalmingCallback(CallbackData, prefix="calm"):
    action: str  # another_cycle, feel_better, to_talk


class VentingCallback(CallbackData, prefix="vent"):
    action: str  # save, delete, to_cbt


from typing import Optional


class SubscriptionCallback(CallbackData, prefix="sub"):
    menu: str
    sub_type: Optional[str] = None
    months: Optional[int] = None
    price: Optional[str] = ""


class HelpCallback(CallbackData, prefix="help"):
    menu: str


class ProblemSolvingCallback(CallbackData, prefix="problem_solving"):
    action: str  # e.g., 'choose_option'
    option_id: int
