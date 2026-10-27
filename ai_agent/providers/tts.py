"""TTS Provider factory supporting Cartesia and Deepgram Aura."""
import os
from pipecat.services.tts_service import TTSService
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.tts import DeepgramTTSService
from ..config import get_voice_settings


def get_tts_service() -> TTSService:
    """Returns CartesiaTTSService if CARTESIA_API_KEY is configured, else falls back to Deepgram Aura."""
    settings = get_voice_settings()

    cartesia_key = settings.cartesia_api_key.get_secret_value() if settings.cartesia_api_key else os.getenv("CARTESIA_API_KEY")
    if cartesia_key and cartesia_key.strip():
        return CartesiaTTSService(
            api_key=cartesia_key,
            settings=CartesiaTTSService.Settings(
                voice=settings.cartesia_voice_id,
            ),
        )

    deepgram_key = settings.deepgram_api_key.get_secret_value() if settings.deepgram_api_key else os.getenv("DEEPGRAM_API_KEY")
    if deepgram_key and deepgram_key.strip():
        return DeepgramTTSService(
            api_key=deepgram_key,
            voice=settings.deepgram_tts_voice,
        )

    raise ValueError(
        "No TTS service configured. Please provide CARTESIA_API_KEY or DEEPGRAM_API_KEY in your .env file."
    )
