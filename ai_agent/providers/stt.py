"""STT Provider factory for Deepgram."""
import os
from pipecat.services.deepgram.stt import DeepgramSTTService
from ..config import get_voice_settings


def get_stt_service() -> DeepgramSTTService:
    """Creates and returns a Deepgram STT service instance configured with Nova-3."""
    settings = get_voice_settings()
    api_key = settings.deepgram_api_key.get_secret_value() if settings.deepgram_api_key else os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not set. Please set it in your .env file.")

    return DeepgramSTTService(
        api_key=api_key,
        settings=DeepgramSTTService.Settings(
            model=settings.deepgram_stt_model,
            language=settings.deepgram_language,
            punctuate=True,
            smart_format=True,
            interim_results=True,
        ),
    )
