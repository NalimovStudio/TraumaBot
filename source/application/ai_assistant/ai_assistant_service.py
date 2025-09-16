from source.application.ai_assistant.AssistantServiceInterface import AssistantServiceInterface
from source.core.lexicon.prompts import GET_CALM_PROMPT, KPT_DIARY_PROMPT, PROBLEMS_SOLVER_PROMPT, SPEAK_OUT_PROMPT, \
    BLACKPILL_EXIT_PROMPT, GET_USER_CHARACTERISTIC
from source.core.schemas.assistant_schemas import ContextMessage, AssistantResponse
from source.core.schemas.user_schema import UserCharacteristicSchema
from source.infrastructure.ai_assistant.ai_assistant import AssistantClient
from source.infrastructure.database.models.base_model import S


class AssistantService(AssistantServiceInterface):
    def __init__(self, client: AssistantClient):
        self.client = client

    async def get_calm_response(
            self,
            message: str,
            context_messages=None,
            prompt: str = GET_CALM_PROMPT,
            temperature=0.3
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_kpt_diary_response(
            self,
            message: str,
            context_messages=None,
            prompt: str = KPT_DIARY_PROMPT
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
        )

    async def get_problems_solver_response(
            self,
            message: str,
            context_messages=None,
            temperature: float = 0.3,
            prompt: str = PROBLEMS_SOLVER_PROMPT
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_speak_out_response(
            self,
            message: str,
            prompt: str = SPEAK_OUT_PROMPT,
            context_messages=None,
            temperature=0.3
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_blackpill_exit_response(
            self,
            message: str,
            prompt: str = BLACKPILL_EXIT_PROMPT,
            context_messages=None,
            temperature=0.3
    ) -> AssistantResponse:
        """Возвращает ответ ассистента в режиме ВЫХОД ИЗ БЛЕКПИЛЛ"""
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_user_characteristic(
            self,
            user_message_history: list[str],  # TODO Влад: брать за последнюю неделю все запросы юзера
            user_mood_history: list[str],  # TODO Влад: тоже
            prompt: str = GET_USER_CHARACTERISTIC,
            response_schema: S = UserCharacteristicSchema
    ):
        query: str = f"user_message_history: {user_message_history}\n\n user_mood_history: {user_mood_history}"
        return await self.client.get_response(
            system_prompt=prompt,
            message=query
        )
