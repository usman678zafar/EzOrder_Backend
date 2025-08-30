from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig
from config.settings import settings
from tools.registration_tools import validate_name, validate_address, validate_and_save_user
from .prompts import REGISTRATION_AGENT_PROMPT

class RegistrationAgentFactory:
    @staticmethod
    def _create_base_config():
        """Create base configuration for agents"""
        external_client = AsyncOpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url=settings.GEMINI_BASE_URL,
        )

        model = OpenAIChatCompletionsModel(
            model=settings.MODEL_NAME,
            openai_client=external_client
        )

        config = RunConfig(
            model=model,
            model_provider=external_client,
            tracing_disabled=True
        )

        return config, external_client

    @staticmethod
    def create_registration_agent():
        """Create agent for new user registration"""
        config, _ = RegistrationAgentFactory._create_base_config()

        registration_agent = Agent(
            name="Registration Assistant",
            instructions=REGISTRATION_AGENT_PROMPT,
            tools=[
                validate_name,
                validate_address,
                validate_and_save_user
            ]
        )

        return registration_agent, config