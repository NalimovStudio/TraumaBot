from pydantic import BaseModel, Field


class ContextMessage(BaseModel):
    """Схема для запросов нейронке"""
    role: str = Field("user", description="роль пользователя")
    message: str = Field(..., description="сообщение юзера")

    def get_message_to_deepseek(self) -> dict:
        """Получение сообщения нейронке в формате JSON"""
        return {"role": self.role, "content": self.message}


class AssistantResponse(BaseModel):
    """Схема для ответов от нейронки"""
    message: str


class UserCharacteristicAssistantResponse(BaseModel):
    # [ mood_analysis ]
    current_mood: str = Field(..., description="Эмоциональное состояние на момент записи")
    mood_trend: str = Field(..., description="Динамика настроения")
    mood_stability: str = Field(..., description="Эмоциональная стабильность")

    # [ risk_assessment ]
    risk_group: str = Field(..., description="Группа риска")
    stress_level: str = Field(..., description="Уровень стресса")
    anxiety_level: str = Field(..., description="Уровень тревожности")

    # [ personality_traits ]
    strengths: list[str] = Field(default_factory=list, description="Положительные черты характера")
    weaknesses: list[str] = Field(default_factory=list, description="Негативные черты характера")
    communication_style: str = Field(..., description="Стиль коммуникации")

    personal_insights: list[str] = Field(default_factory=list, description="Психологические инсайты и склонности")
    recommendations: list[str] = Field(default_factory=list, description="Рекомендации")

    characteristic_accuracy: str = Field(..., description="Точность оценки ИИ в процентах")

    class Config:
        from_attributes = True
