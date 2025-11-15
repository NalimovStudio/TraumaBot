from aiogram.fsm.state import State, StatesGroup


class SupportStates(StatesGroup):
    # Основной поток
    CHECK_IN = State()          # Ожидание ответа на первый вопрос "Как ты?"
    METHOD_SELECT = State()     # Ожидание выбора метода поддержки

    # Потоки поддержки
    # [ отключен ]
    CALMING = State()           # В процессе выполнения техники "Успокоиться"
    CALMING_TALK = State()      # В процессе разговора с ИИ после техники "Успокоиться"

    # [ работают ]
    SPEAKING = State()           # В процессе выполнения техники "Поговорить"
    RELATIONSHIPS = State()
    BLACKPILL_TALK = State()

    # Поток КПТ (Когнитивно-поведенческая терапия)
    CBT_S1_SITUATION = State()          # Шаг 1: Описание ситуации
    CBT_S2_EMOTIONS = State()           # Шаг 2: Эмоции и их интенсивность
    CBT_S3_THOUGHT = State()            # Шаг 3: Автоматическая мысль
    CBT_S4_DISTORTIONS = State()        # Шаг 4: Когнитивные искажения
    CBT_S5_EVIDENCE = State()           # Шаг 5: Доказательства за/против
    CBT_S6_ALTERNATIVE = State()        # Шаг 6: Альтернативная мысль
    CBT_S7_RERATING = State()           # Шаг 7: Повторная оценка эмоций

    # Поток решения проблемы
    PROBLEM_S1_DEFINE = State()         # Шаг 1: Определение проблемы
    PROBLEM_S2_GOAL = State()           # Шаг 2: Определение цели
    PROBLEM_S3_OPTIONS = State()        # Шаг 3: Генерация вариантов
    PROBLEM_S4_STEPS_DISPLAYED = State() # Шаг 4: Отображение шагов и ожидание ответа

    # Протокол безопасности
    RISK_PROTOCOL = State()             # Состояние при обнаружении риска

    # Платежка
    WAITING = State()  # Ожидаем выбор: почта или телефон
