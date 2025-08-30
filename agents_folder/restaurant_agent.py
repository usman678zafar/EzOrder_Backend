from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig
from config.settings import settings
from tools.menu_tools import show_menu
from tools.order_tools import add_to_order, view_current_order, confirm_order
from tools.registration_tools import validate_name, validate_address, validate_and_save_user
from .prompts import RESTAURANT_AGENT_PROMPT, REGISTRATION_AGENT_PROMPT

class AgentFactory:
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
        config, _ = AgentFactory._create_base_config()

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

    @staticmethod
    def create_restaurant_agent():
        """Create agent for restaurant operations"""
        config, _ = AgentFactory._create_base_config()

        restaurant_agent = Agent(
            name="Restaurant Assistant",
            instructions=RESTAURANT_AGENT_PROMPT,
            tools=[
                show_menu,
                add_to_order,
                view_current_order,
                confirm_order
            ]
        )

        return restaurant_agent, config
