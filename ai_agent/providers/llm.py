"""LLM Provider factory using Pipecat's dedicated Groq service."""
import os
from pipecat.services.groq.llm import GroqLLMService
from ..config import get_voice_settings


def get_llm_service() -> GroqLLMService:
    """Creates and returns a dedicated GroqLLMService instance."""
    settings = get_voice_settings()
    api_key = settings.groq_api_key.get_secret_value() if settings.groq_api_key else os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please set it in your .env file.")

    return GroqLLMService(
        api_key=api_key,
        base_url=settings.groq_base_url,
        settings=GroqLLMService.Settings(
            model=settings.groq_model,
        ),
    )
