import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # MongoDB Configuration
    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("MONGO_URI environment variable is required")
    
    # Gemini Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    
    # WhatsApp Configuration
    WHATSAPP_INSTANCE_ID = os.getenv("WHATSAPP_INSTANCE_ID")
    if not WHATSAPP_INSTANCE_ID:
        raise ValueError("WHATSAPP_INSTANCE_ID environment variable is required")
    
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    if not WHATSAPP_TOKEN:
        raise ValueError("WHATSAPP_TOKEN environment variable is required")
    
    # Model Configuration
    MODEL_NAME = os.getenv("MODEL_NAME")
    
    # Conversation History Settings
    CONVERSATION_HISTORY_LIMIT = int(os.getenv("CONVERSATION_HISTORY_LIMIT"))
    CONVERSATION_HISTORY_HOURS = int(os.getenv("CONVERSATION_HISTORY_HOURS"))
    
    # API Server Configuration
    API_HOST = os.getenv("API_HOST")
    API_PORT = int(os.getenv("API_PORT"))
    
    # Other Settings
    OLD_CONVERSATION_CLEANUP_DAYS = int(os.getenv("OLD_CONVERSATION_CLEANUP_DAYS"))

settings = Settings()
