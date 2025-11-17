from source.application.ai_assistant.AssistantServiceInterface import AssistantServiceInterface
from source.core.lexicon.prompts import GET_CALM_PROMPT, KPT_DIARY_PROMPT, PROBLEMS_SOLVER_PROMPT, SPEAKING_PROMPT, \
    RELATIONSHIPS_PROMPT, GET_USER_CHARACTERISTIC
from source.core.schemas import UserLogSchema
from source.core.schemas.assistant_schemas import AssistantResponse, UserCharacteristicAssistantResponse
from source.core.schemas.user_schema import UserMoodSchema
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
            temperature=0.75
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_pathways_to_solve_problem_response(
            self,
            prompt: str,
            context_messages=None,
            temperature: float = 0.4,
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message="",  # The prompt contains all info, no new message needed
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

    async def get_speaking_response(
            self,
            message: str,
            prompt: str = SPEAKING_PROMPT,
            context_messages=None,
            temperature=0.7
    ) -> AssistantResponse:
        if context_messages is None:
            context_messages = []
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_relationships_response(
            self,
            message: str,
            prompt: str = RELATIONSHIPS_PROMPT,
            context_messages=None,
            temperature=0.6
    ) -> AssistantResponse:
        """Возвращает ответ ассистента в режиме Отношения"""
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
            user_logs_history: list[UserLogSchema],
            user_mood_history: list[UserMoodSchema],
            prompt: str = GET_USER_CHARACTERISTIC,
            response_schema: S = UserCharacteristicAssistantResponse,
    ) -> UserCharacteristicAssistantResponse:
        """Генерация хар-ки в формате UserCharacteristicSchema"""

        # TODO сделать лимит чтобы не было слишком много сообщений (в отдельном и во всех)
        user_logs_query: str = ", ".join([log.message_text for log in user_logs_history])

        user_moods_query: str = ", ".join([str(mood.mood) for mood in user_mood_history])

        query: str = f"user_message_history: {user_logs_query}\n\n user_mood_history: {user_moods_query}"

        return await self.client.get_response(
            system_prompt=prompt,
            message=query,
            response_schema=response_schema,
            need_json=True
        )
