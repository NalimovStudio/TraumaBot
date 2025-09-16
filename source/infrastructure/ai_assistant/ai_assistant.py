import logging

from openai import OpenAI

from source.core.exceptions import AssistantResponseException, AssistantException
from source.core.schemas.assistant_schemas import ContextMessage, AssistantResponse
from source.infrastructure.database.models.base_model import S

logger = logging.getLogger(__name__)


class AssistantClient:
    def __init__(self, client: OpenAI):
        self.client = client

    async def get_response(
            self,
            system_prompt: str,
            message: str,
            context_messages: list[ContextMessage] = None,
            temperature: float = 0.7,
            response_schema: S = None  # схема для валидации ответа
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []

        messages = [
            {"role": "system", "content": f"{system_prompt}"}
        ]

        # Добавление контекста
        if context_messages:
            for context_message in context_messages:
                logger.info(context_message.get_message_to_deepseek())
                messages.append(context_message.get_message_to_deepseek())

        # Добавление последнего сообщения 
        messages.append({"role": "user", "content": f"{message}"})

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=temperature
            )
        except:
            logging.ERROR("Ошибка при обращении к DeepseekAPI")
            raise AssistantException

        try:
            if response_schema:
                response_schema.model_validate(response.choices[0].message.content)
            return AssistantResponse.model_validate({"message": response.choices[0].message.content})

        except:
            logging.ERROR("Ошибка валидации ответа от Deepseek")
            raise AssistantResponseException
