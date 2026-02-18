from dishka import Provider, provide, Scope
from openai import AsyncOpenAI


from source.infrastructure.ai_assistant.ai_assistant import AssistantClient
from source.infrastructure.configs import AssistantConfig


class AssistantProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_openai(self, config: AssistantConfig) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=config.api_key.get_secret_value(), base_url="https://routerai.ru/api/v1/")

    @provide
    def get_assistant(self, client: AsyncOpenAI) -> AssistantClient:
        return AssistantClient(client=client)
