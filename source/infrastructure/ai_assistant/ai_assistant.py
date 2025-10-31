import logging

from openai import OpenAI

from source.core.exceptions import AssistantResponseException, AssistantException
from source.core.schemas.assistant_schemas import ContextMessage, AssistantResponse
from source.core.schemas.user_schema import UserCharacteristicSchema
from source.infrastructure.database.models.base_model import S

logger = logging.getLogger(__name__)

ASSISTANT_RESPONSES = (
    AssistantResponse,
    UserCharacteristicSchema,
)


class AssistantClient:
    def __init__(self, client: OpenAI):
        self.client = client

    async def get_response(
            self,
            system_prompt: str,
            message: str,
            context_messages: list[ContextMessage] = None,
            temperature: float = 0.7,
            response_schema: S = None,  # схема для валидации ответа
            need_json: bool = False
    ) -> ASSISTANT_RESPONSES:
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
                temperature=temperature,
                response_format={"type": "json_object"} if need_json else None
            )
        except Exception as e:
            logger.error(f"Ошибка при обращении к DeepseekAPI: {e}")
            raise AssistantException

        try:
            response_content = response.choices[0].message.content
            logger.info(f"Получен ответ от Deepseek: {response_content}")

            if response_schema:
                validated_response = response_schema.model_validate_json(response_content)
                return validated_response
            else:
                return AssistantResponse.model_validate({"message": response_content})

        except Exception as e:
            logger.error(f"Ошибка валидации ответа от Deepseek: {e}")
            logger.error(f"Содержимое ответа: {response.choices[0].message.content}")
            raise AssistantResponseException
