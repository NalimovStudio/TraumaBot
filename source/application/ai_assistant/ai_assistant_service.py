from source.application.ai_assistant.AssistantServiceInterface import AssistantServiceInterface
from source.core.lexicon.prompts import GET_CALM_PROMPT, KPT_DIARY_PROMPT, PROBLEMS_SOLVER_PROMPT, SPEAK_OUT_PROMPT
from source.core.schemas.assistant_schemas import ContextMessage, AssistantResponse
from source.infrastructure.ai_assistant.ai_assistant import AssistantClient


class AssistantService(AssistantServiceInterface):
    def __init__(self, client: AssistantClient):
        self.client = client

    async def get_calm_response(
            self,
            message: str,
            context_messages: list[ContextMessage] = [],
            prompt: str = GET_CALM_PROMPT,
            temperature=0.4
    ) -> AssistantResponse:
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )

    async def get_kpt_diary_response(
            self,
            message: str,
            context_messages: list[ContextMessage] = [],
            prompt: str = KPT_DIARY_PROMPT
    ) -> AssistantResponse:
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
        )

    async def get_problems_solver_response(
            self,
            message: str,
            context_messages: list[ContextMessage] = [],
            temperature: float = 0.65,
            prompt: str = PROBLEMS_SOLVER_PROMPT
    ) -> AssistantResponse:
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
            context_messages: list[ContextMessage] = [],
            temperature = 0.4
    ) -> AssistantResponse:
        return await self.client.get_response(
            system_prompt=prompt,
            message=message,
            context_messages=context_messages,
            temperature=temperature
        )
