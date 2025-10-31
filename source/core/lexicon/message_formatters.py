from datetime import datetime

from source.core.lexicon.message_templates import PROFILE_CHARACTERISTIC_TEXT
from source.core.schemas.user_schema import UserCharacteristicSchema


# Форматирование даты на русском словами
def format_date_russian(date):
    months = {
        1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля', 5: 'мая', 6: 'июня',
        7: 'июля', 8: 'августа', 9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
    }
    return f"{date.day} {months[date.month]} {date.year} года"


def format_days_russian(days):
    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return f"{days} дня"
    else:
        return f"{days} дней"


# Функция для склонения слова "прошло"
def format_passed_russian(days) -> str:
    if days % 10 == 1 and days % 100 != 11:
        return f"прошёл {days} день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return f"прошло {days} дня"
    else:
        return f"прошло {days} дней"


def format_profile_characteristic(characteristic: UserCharacteristicSchema) -> str:
    """Форматирует характеристику пользователя в красивый текст"""
    characteristic_created_date = characteristic.created_at.date()
    date: str = format_date_russian(characteristic_created_date)

    # Расчет количества прошедших дней с правильным склонением
    days_passed = (datetime.now().date() - characteristic_created_date).days
    days_pass = format_days_russian(days_passed)

    strengths_formatted: str = ''.join([f"└── {strength}\n" for strength in characteristic.strengths])
    weaknesses_formatted: str = ''.join([f"└── {weaknesses}\n" for weaknesses in characteristic.weaknesses])
    recommendations_formatted: str = ''.join(
        [f"└─ {recommendations}\n" for recommendations in characteristic.recommendations])
    personal_insights_formatted: str = ''.join(
        [f"└─ {personal_insights}\n" for personal_insights in characteristic.personal_insights])

    return PROFILE_CHARACTERISTIC_TEXT.format(
        current_mood=characteristic.current_mood or "не указано",
        mood_trend=characteristic.mood_trend or "не указано",
        mood_stability=characteristic.mood_stability or "не указано",
        risk_group=characteristic.risk_group or "не указано",
        stress_level=characteristic.stress_level or "не указано",
        anxiety_level=characteristic.anxiety_level or "не указано",
        communication_style=characteristic.communication_style or "не указано",
        strengths_formatted=strengths_formatted,
        weaknesses_formatted=weaknesses_formatted,
        personal_insights_formatted=personal_insights_formatted,
        recommendations_formatted=recommendations_formatted,
        characteristic_accuracy=characteristic.characteristic_accuracy or "не указано",
        characteristic_when_created=date or "не указано",
        days_pass=days_pass,
        passed_russian_word=format_passed_russian(days_passed)
    )
